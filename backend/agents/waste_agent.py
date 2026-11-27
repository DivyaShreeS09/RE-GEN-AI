# Gemini is used ONLY to generate the following narrative field: ai_recommendation.
# All other fields (hidden_value_score, estimated_recovery, hazard_warning, reasoning_trace)
# are computed by deterministic Python above the Gemini call.
from core.simulation import load_waste_kb
from core.guardrails import apply_hazard_guardrail, validate_quantity, get_disclaimer
from core.ai_client import call_ai

_kb = None


def _get_kb():
    global _kb
    if _kb is None:
        _kb = load_waste_kb()
    return _kb


# ── Multi-stream batch analysis ─────────────────────────────────────────────

_CATEGORY_GROUP = {
    "Organic Waste": "organic", "Mixed Organic Waste": "organic",
    "Garden Waste": "organic", "Biomass Waste": "organic", "Agricultural Waste": "organic",
    "Metal Waste": "metal", "Plastic Waste": "plastic", "Construction Waste": "construction",
    "Paper Waste": "paper", "Glass Waste": "glass", "Biomedical Waste": "hazardous",
    "Hazardous Waste": "hazardous", "E-waste": "hazardous",
}
_KG_PER_UNIT = {"kg": 1, "g": 0.001, "t": 1000, "tonne": 1000, "tonnes": 1000, "tons": 1000}


def analyze_waste_batch(items: list, *, intelligence: bool = False) -> dict:
    results = []
    mass = dict.fromkeys((*_CATEGORY_GROUP.values(), "other"), 0.0)
    for item in items:
        unit = item.get("unit", "kg")
        if unit not in _KG_PER_UNIT:
            raise ValueError("Unsupported mass unit.")
        quantity = float(item["quantity_kg"]) * _KG_PER_UNIT[unit]
        result = analyze_waste(item["type"], quantity, narrative=False)
        if "error" in result:
            raise ValueError(result["error"])
        group = "hazardous" if result.get("hazard_warning") else _CATEGORY_GROUP.get(result.get("category"), "other")
        mass[group] += quantity
        results.append(result)
    if intelligence:
        from core.waste_intelligence import investigate_recovery, restricted_material
        from core.material_intelligence import interpret_inventory
        from core.ai_client import _cloud_consent
        from core.market_evidence import inventory_market_rows, attach_market_evidence
        from core.market_valuation import enrich_pathways

        evidence_rows = inventory_market_rows(remote=False)

        inputs = [{"material":result["waste_type"], "quantity":result["quantity_kg"], "unit":"kg",
                   "condition":item.get("condition") or "unspecified", "contaminated":item.get("contaminated") is True}
                  for item, result in zip(items, results)]
        consent = _cloud_consent.set(False)
        try:
            identities = interpret_inventory(inputs)
        finally:
            _cloud_consent.reset(consent)

        for item, result, identity in zip(items, results, identities):
            condition = item.get("condition") or "unspecified"
            if not isinstance(condition, str):
                condition = "unspecified"

            contaminated = (
                item.get("contaminated") is True
                or condition.lower() in {"contaminated", "spoiled"}
            )

            candidate = identity["canonical_material"]
            safe_identity = identity["certainty"] != "unknown" and not (
                restricted_material(result["waste_type"], result) or restricted_material(candidate, {}))
            recovery = investigate_recovery(
                material=candidate if safe_identity else result["waste_type"],
                quantity=result["quantity_kg"],
                unit="kg",
                condition=condition[:160],
                reference=result,
                contaminated=contaminated,
                context="facility maintenance and resource recovery",
                services=[], allow_ai=False,
                precomputed=identity.get("recovery_plan") if safe_identity else None,
            )

            fields = {
                "material": result["waste_type"],
                "quantity": result["quantity_kg"],
                "unit": "kg",
                "condition": condition[:160],
                "contaminated": contaminated,
                "material_identity": identity,
            }

            recovery = enrich_pathways(fields, recovery, [])
            recovery = attach_market_evidence(
                fields, recovery, rows=evidence_rows
            )

            recovery["material_identity"] = identity
            result["recovery_intelligence"] = recovery
            result["recovery_pathways"] = recovery["pathways"]
            result["ai_enhanced"] = recovery["ai_enhanced"]

    total_kg = sum(mass.values())
    if total_kg == 0:
        return {
            "agent":   "Waste-to-Wealth Agent",
            "status":  "no_waste",
            "message": "No valid waste entries provided.",
            "total_kg": 0,
            "items":   [],
        }

    composition = {f"{group}_pct": round(kg * 100 / total_kg, 1) for group, kg in mass.items()}
    known = [r for r in results if r["status"] == "analyzed"]
    known_mass = sum(r["quantity_kg"] for r in known)
    circularity = round(sum(r["hidden_value_score"] * r["quantity_kg"] for r in known) / known_mass, 1) if known_mass else None
    estimates = [r["estimated_recovery"] for r in known if r["estimated_recovery"] is not None]

    if intelligence:
        estimates = []

        for result in results:
            result["estimated_recovery"] = None

            routes = result.get("recovery_pathways", [])
            if not routes:
                continue

            route = routes[0]
            value = route.get("valuation") or {}

            if (
                value.get("status") == "estimated"
                and value.get("value_type") == "gross_reference"
                and value.get("minimum_inr") is not None
                and value.get("maximum_inr") is not None
                and not result.get("hazard_warning")
            ):
                estimate = {
                    "min_inr": value["minimum_inr"],
                    "max_inr": value["maximum_inr"],
                    "note": "Indicative gross recovery; costs and acceptance unconfirmed.",
                }

                result["estimated_recovery"] = estimate

                if result["status"] == "analyzed":
                    estimates.append(estimate)

    # Top opportunity = highest max recovery value
    top_item = None
    best_max = 0.0
    for r in known:
        rec = r.get("estimated_recovery")
        if rec and rec.get("max_inr", 0) > best_max:
            best_max = rec["max_inr"]
            top_item = r

    # Compliance warnings
    compliance_warnings = [
        f"{r['waste_type']} requires CPCB-authorised handling."
        for r in known if r.get("hazard_warning")
    ]

    meta = _kb_meta()
    return {
        "agent":                   "Waste-to-Wealth Agent",
        "status":                  "analyzed",
        "total_items":             len(results),
        "analyzed_items":          len(known),
        "total_kg":                round(total_kg, 2),
        "priced_mass_kg": sum(r["quantity_kg"] for r in known if r["estimated_recovery"] is not None),
        "valuation_basis": (
            "Evidence-supported indicative gross recovery from one selected pathway per material. Not confirmed income or utility savings."
            if intelligence else
            "Partial dated knowledge-base reference, excluding unpriced mass. No confirmed quote."
        ),
        "total_recovery_min_inr":  round(sum(r["min_inr"] for r in estimates), 2) if estimates else None,
        "total_recovery_max_inr":  round(sum(r["max_inr"] for r in estimates), 2) if estimates else None,
        "hazardous_count":         sum(bool(r["hazard_warning"]) for r in known),
        "circularity_score":       circularity,
        "composition":             composition,
        "top_opportunity":         top_item.get("waste_type") if top_item else None,
        "top_opportunity_value_max_inr": round(best_max, 2) if top_item else None,
        "top_opportunity_pathway": top_item.get("recommended_pathway") if top_item else None,
        "compliance_warnings":     compliance_warnings,
        "items":                   results,
        "kb_last_verified":        meta.get("kb_last_verified", "unknown"),
        "kb_source_note":          meta.get("source_note", ""),
        "confidence":              None,
        "disclaimer":              get_disclaimer(),
    }


_ALIASES: dict[str, str] = {
    "காகிதம்": "paper",
    "அட்டை": "cardboard",
    "உணவுக் கழிவு": "food waste",
    "metal / aluminium": "aluminium",
    # Paper aliases
    "paper & cardboard": "cardboard",
    "paper/cardboard": "cardboard",
    "cardboard paper": "cardboard",
    "corrugated cardboard": "cardboard",
    "carton boxes": "cardboard",
    "cartons": "cardboard",
    "shipping cartons": "cardboard",
    "boxes": "cardboard",
    "scrap paper": "paper",
    "magazines": "newspaper",
    "white paper": "office paper",
    "copy paper": "office paper",
    "shredded paper": "mixed paper",
    # Plastic aliases
    "pet bottle": "pet",
    "pet bottles": "pet",
    "plastic bottle": "pet",
    "plastic bottles": "pet",
    "polyethylene terephthalate": "pet",
    "polypropylene": "pp",
    "polyvinyl chloride": "pvc",
    "high density polyethylene": "hdpe",
    "low density polyethylene": "ldpe",
    "plastic packaging": "mixed plastic",
    "soft plastic": "ldpe",
    # Metal aliases
    "aluminum": "aluminium",
    "aluminum cans": "aluminium cans",
    "steel cans": "steel",
    "scrap steel": "steel scrap",
    "ferrous scrap": "steel scrap",
    "iron scrap": "iron",
    "copper wire": "copper",
    "copper pipes": "copper",
    "copper scrap": "copper",
    "brass fittings": "brass",
    "aluminum scrap": "aluminium",
    # Organic aliases
    "food scraps": "food waste",
    "organic waste": "food waste",
    "biowaste": "food waste",
    "food residue": "food waste",
    "compostable waste": "food waste",
    "vegetable peels": "vegetable waste",
    "fruit peels": "fruit waste",
    "kitchen scraps": "kitchen waste",
    "canteen waste": "food waste",
    "cafeteria waste": "food waste",
    # Oil aliases
    "waste cooking oil": "cooking oil",
    "used cooking oil": "cooking oil",
    "frying oil": "cooking oil",
    "used motor oil": "engine oil",
    "waste oil": "used oil",
    # E-waste aliases
    "electronic waste": "e-waste",
    "electronics": "e-waste",
    "ewaste": "e-waste",
    "pcb": "e-waste",
    "circuit boards": "e-waste",
    "computer": "computers",
    "laptop": "laptops",
    "mobile phone": "mobile phones",
    "phone": "mobile phones",
    "smartphone": "mobile phones",
    "monitor": "monitors",
    "printer": "printers",
    # Battery aliases
    "batteries": "battery waste",
    "battery": "battery waste",
    "lead batteries": "lead acid batteries",
    "ups battery": "ups batteries",
    "lithium battery": "lithium batteries",
    "li-ion battery": "lithium batteries",
    # Glass aliases
    "glass waste": "glass",
    "broken glass": "glass",
    "glass jar": "glass",
    "glass jars": "glass",
    "glass containers": "glass",
    "clear glass bottles": "clear glass",
    "colored glass bottles": "colored glass",
    # Textile / Rubber aliases
    "fabric waste": "fabric",
    "textile": "textiles",
    "cloth": "textiles",
    "clothing": "textiles",
    "garments": "textiles",
    "rubber tyre": "tyres",
    "used tyres": "tyres",
    "scrap tyres": "tyres",
    "tires": "tyres",
    "tire": "tyres",
    # Wood aliases
    "timber": "wood",
    "plank": "wood",
    "wooden waste": "wood",
    "wood scraps": "wood",
    "pallet": "pallets",
    "wooden pallet": "pallets",
    # Construction aliases
    "construction waste": "construction debris",
    "demolition waste": "construction debris",
    "c&d waste": "construction debris",
    "building waste": "construction debris",
    "brick": "bricks",
    "rubble": "bricks",
    "cement": "concrete",
    "tile": "tiles",
    "ceramic tiles": "tiles",
    # Hazardous aliases
    "hazardous": "hazardous waste",
    "chemical": "chemical waste",
    "chemicals": "chemical waste",
    "medical": "medical waste",
    "biomedical waste": "medical waste",
    "hospital waste": "medical waste",
    "clinical waste": "medical waste",
    "asbestos waste": "asbestos",
    "fluorescent bulb": "fluorescent lamps",
    "fluorescent tube": "fluorescent lamps",
    "cfl": "fluorescent lamps",
    "tube light": "fluorescent lamps",
    # Other aliases
    "sludge": "organic sludge",
    "mud": "organic sludge",
    "ash waste": "ash",
    "coal ash": "fly ash",
    "industrial ash": "fly ash",
    "mixed waste": "mixed municipal waste",
    "general waste": "mixed municipal waste",
    "msw": "mixed municipal waste",
}


def normalize_waste_key(raw_key: str) -> str:
    """Normalize common variant spellings to their canonical KB key."""
    k = raw_key.lower().strip()
    return _ALIASES.get(k, k)


def _kb_meta() -> dict:
    return _get_kb().get("_meta", {})


def get_kb_materials_list() -> list[dict]:
    """Return sorted, categorized list of all KB materials for the frontend dropdown."""
    kb = _get_kb()
    materials = kb.get("waste_materials", {})
    rows = []
    for name, data in materials.items():
        rows.append({
            "name": name,
            "category": data.get("category", "Other"),
            "hazard_level": data.get("hazard_level", "none"),
        })
    rows.sort(key=lambda r: (r["category"], r["name"]))
    return rows


def _reference_analysis(waste_type: str, quantity_kg: float, *, narrative: bool = True) -> dict:
    kb        = _get_kb()
    materials = kb.get("waste_materials", {})

    validation = validate_quantity(quantity_kg)
    if not validation["valid"]:
        return {"error": validation["message"], "agent": "Waste-to-Wealth Agent"}

    raw_key  = waste_type.lower().strip()
    key      = normalize_waste_key(raw_key)
    material = materials.get(key)
    if material is None:
        return {
            "agent":              "Waste-to-Wealth Agent",
            "status":             "unknown_material",
            "waste_type":         waste_type,
            "quantity_kg":        quantity_kg,
            "message":            f"Material '{waste_type}' is not currently in the knowledge base.",
            "inferred_category":  "Unknown",
            "inferred_handling":  "Request classification from authorized facility staff.",
            "suggestions":        [],
            "clarification": "What does the supplier label say, and is the material mixed or contaminated?",
            "estimated_recovery": None,
            "next_step":          "Submit this material for manual classification. In the interim, store separately and do not dispose in general waste.",
            "disclaimer":         get_disclaimer(),
        }

    hazard_result = apply_hazard_guardrail(material["hazard_level"])

    min_val = material["estimated_value_range"]["min"]
    max_val = material["estimated_value_range"]["max"]
    unit    = material["estimated_value_range"]["unit"]

    if hazard_result["estimated_profit_suppressed"]:
        estimated_recovery      = None
        estimated_recovery_note = hazard_result["profit_note"]
    elif unit != "INR/kg":
        estimated_recovery = None
        estimated_recovery_note = f"Reference rate is per {unit.split('/')[-1]}. Mass alone cannot establish value."
    else:
        estimated_recovery = {
            "min_inr":   round(min_val * quantity_kg, 2),
            "max_inr":   round(max_val * quantity_kg, 2),
            "unit_rate": f"{min_val}-{max_val} {unit}",
            "note":      "Estimated only. Actual market prices vary.",
        }
        estimated_recovery_note = None

    hidden_value_score = material["hidden_value_score"]

    reasoning_trace = [
        f"Step 1 — Material identified: '{key}' found in knowledge base.",
        f"Step 2 — Category: {material['category']}. Hazard level: {material['hazard_level']}.",
        f"Step 3 — Hazard guardrail: {'TRIGGERED — warning active' if hazard_result['warning'] else 'No hazard detected'}.",
        f"Step 4 — Possible products: {', '.join(material['possible_products'][:3])}.",
        f"Step 5 — Recommended pathway: {material['recommended_pathway']}.",
        f"Step 6 — Hidden value score: {hidden_value_score}/100.",
        f"Step 7 — Estimated recovery calculated for {quantity_kg} kg.",
    ]

    # --- AI recommendation (only for non-hazardous materials) ---
    ai_recommendation = None
    ai_used           = False

    if narrative and estimated_recovery is not None:
        fallback_rec = (
            f"The knowledge base identifies {key} as a "
            f"candidate for {material['recommended_pathway']}. "
            "Facility staff should compare verified recovery "
            "options, current acceptance evidence and total "
            "costs before selecting a pathway."
        )

        prompt = f"""You are a waste management specialist. Write 2 actionable sentences for a sustainability officer.

Material: {key}
Category: {material['category']}
Recommended pathway: {material['recommended_pathway']}
Possible products: {', '.join(material['possible_products'][:3])}
Estimated value: Rs. {min_val}-{max_val} per {unit} (market estimate)
Quantity: {quantity_kg} kg
Hidden value score: {hidden_value_score}/100

Rules:
- Say "estimated" for all financial figures
- Do not claim profit, verified buyers, confirmed demand or guaranteed feasibility
- Describe products only as potential applications
- Recommend staff review of verified demand, acceptance and costs
- Do not use: revolutionary, powerful AI, next-generation"""

        ai_recommendation, ai_used = call_ai(prompt, fallback_rec)

    meta = _kb_meta()
    return {
        "agent":                    "Waste-to-Wealth Agent",
        "status":                   "analyzed",
        "waste_type":               waste_type,
        "quantity_kg":              quantity_kg,
        "category":                 material["category"],
        "composition":              material["composition"],
        "hazard_level":             material["hazard_level"],
        "hazard_warning":           hazard_result["warning"],
        "hazard_message":           hazard_result["warning_message"],
        "possible_products":        [] if hazard_result["warning"] else material["possible_products"],
        "buyer_types":              material["buyer_types"],
        "recommended_pathway":      material["recommended_pathway"],
        "sustainability_notes":     material["sustainability_notes"],
        "risks":                    material["risks"],
        "hidden_value_score":       hidden_value_score,
        "estimated_recovery":       estimated_recovery,
        "estimated_recovery_note":  estimated_recovery_note,
        "ai_recommendation":        ai_recommendation,
        "ai_enhanced":              ai_used,
        "computation_type":         "deterministic",
        "reasoning_trace":          reasoning_trace,
        "kb_last_verified":         meta.get("kb_last_verified", "unknown"),
        "kb_source_note":           meta.get("source_note", ""),
        "confidence":               None,
        "disclaimer":               get_disclaimer(),
        # Enriched fields — present in expanded knowledge base entries
        "co2_savings_kg_per_tonne": material.get("co2_savings_kg_per_tonne"),
        "compliance_notes":         material.get("compliance_notes"),
        "required_handling":        material.get("required_handling"),
        "knowledge_source":         material.get("knowledge_source"),
        "collection_frequency":     material.get("collection_frequency"),
        "preparation_before_sale":  None if hazard_result["warning"] else material.get("preparation_before_sale"),
    }


def analyze_waste(
    waste_type: str,
    quantity_kg: float,
    *,
    narrative: bool = True,
    condition: str = "unspecified",
    contaminated: bool = False,
    context: str = "general",
    services=None
) -> dict:
    result = _reference_analysis(
        waste_type, quantity_kg, narrative=False
    )

    if "error" in result or not narrative:
        return result

    from core.waste_intelligence import investigate_recovery

    intelligence = investigate_recovery(
        material=waste_type,
        quantity=quantity_kg,
        unit="kg",
        condition=condition,
        reference=result,
        contaminated=contaminated,
        context=context,
        services=services
    )

    result["recovery_intelligence"] = intelligence
    result["recovery_pathways"] = intelligence["pathways"]
    result["ai_enhanced"] = intelligence["ai_enhanced"]

    if intelligence["pathways"]:
        top = intelligence["pathways"][0]
        result["recommended_pathway"] = top["title"]
        result["ai_recommendation"] = top["action"]
        result["computation_type"] = "hybrid_ai_planning"

    return result
