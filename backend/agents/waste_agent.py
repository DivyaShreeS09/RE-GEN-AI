from core.simulation import load_waste_kb
from core.guardrails import apply_hazard_guardrail, validate_quantity, get_disclaimer
from core.openai_client import call_openai

_kb = None


def _get_kb():
    global _kb
    if _kb is None:
        _kb = load_waste_kb()
    return _kb


# ── Multi-stream batch analysis ─────────────────────────────────────────────

_ORGANIC_KEYS  = {
    "food waste", "wet waste", "garden waste", "corn husk", "eggshells",
    "coffee grounds", "sugarcane bagasse", "rice husk", "banana peel",
    "fish waste", "coconut shell", "coconut coir", "dry leaves",
    "organic sludge", "sawdust", "wood waste",
    "kitchen waste", "organic waste", "vegetable waste", "fruit waste",
    "tea waste", "grass clippings", "tree branches", "leaves",
}
_PLASTIC_KEYS  = {
    "plastic bottles", "hdpe", "ldpe", "pet", "pp", "pvc",
    "mixed plastic", "plastic", "plastic waste",
}
_METAL_KEYS    = {
    "aluminium cans", "steel scrap", "copper", "steel", "iron",
    "brass", "aluminium", "scrap metal",
}
_HAZARDOUS_KEYS = {
    "e-waste", "battery waste", "medical waste", "chemical waste",
    "diesel sludge", "oil sludge", "used oil", "leather scraps",
    "fluorescent lamps", "asbestos", "hazardous waste",
    "ups batteries", "lead acid batteries", "lithium batteries",
}
_PAPER_KEYS = {
    "paper waste", "paper", "cardboard", "newspaper", "office paper",
    "mixed paper", "shredded paper",
}
_GLASS_KEYS = {
    "glass bottles", "glass", "clear glass", "colored glass", "broken glass",
}
_CONSTRUCTION_KEYS = {
    "construction debris", "concrete", "bricks", "gypsum", "tiles", "plywood",
}


def analyze_waste_batch(items: list) -> dict:
    """
    Analyze multiple waste streams and return aggregated results.
    items: list of {type: str, quantity_kg: float, unit: str}
    """
    if not items:
        return {
            "agent":   "Waste-to-Wealth Agent",
            "status":  "no_waste",
            "message": "No waste inventory submitted.",
            "total_kg": 0,
            "items":   [],
        }

    results           = []
    total_kg          = 0.0
    total_rec_min     = 0.0
    total_rec_max     = 0.0
    hazardous_count   = 0
    organic_kg        = 0.0
    plastic_kg        = 0.0
    metal_kg          = 0.0
    hazardous_kg      = 0.0
    paper_kg          = 0.0
    glass_kg          = 0.0
    construction_kg   = 0.0

    for item in items:
        raw_type = str(item.get("type", "")).strip()
        unit     = str(item.get("unit", "kg")).lower()

        try:
            raw_qty = float(item.get("quantity_kg", 0) or 0)
        except (ValueError, TypeError):
            continue

        # Unit normalisation → kg
        if unit == "tons":
            qty_kg = raw_qty * 1000.0
        elif unit == "g":
            qty_kg = raw_qty / 1000.0
        else:
            qty_kg = raw_qty

        if not raw_type or qty_kg <= 0:
            continue

        result = analyze_waste(raw_type, qty_kg)
        results.append(result)
        total_kg += qty_kg

        key = raw_type.lower()
        if key in _HAZARDOUS_KEYS:
            hazardous_kg += qty_kg
        elif key in _ORGANIC_KEYS:
            organic_kg += qty_kg
        elif key in _PLASTIC_KEYS:
            plastic_kg += qty_kg
        elif key in _METAL_KEYS:
            metal_kg += qty_kg
        elif key in _PAPER_KEYS:
            paper_kg += qty_kg
        elif key in _GLASS_KEYS:
            glass_kg += qty_kg
        elif key in _CONSTRUCTION_KEYS:
            construction_kg += qty_kg

        if result.get("status") == "analyzed":
            if result.get("hazard_warning"):
                hazardous_count += 1
            rec = result.get("estimated_recovery")
            if rec:
                total_rec_min += rec.get("min_inr", 0)
                total_rec_max += rec.get("max_inr", 0)

    if total_kg == 0:
        return {
            "agent":   "Waste-to-Wealth Agent",
            "status":  "no_waste",
            "message": "No valid waste entries provided.",
            "total_kg": 0,
            "items":   [],
        }

    # Composition percentages
    accounted_kg = organic_kg + plastic_kg + metal_kg + hazardous_kg + paper_kg + glass_kg + construction_kg
    other_kg = max(0, total_kg - accounted_kg)
    composition = {
        "organic_pct":      round(organic_kg      / total_kg * 100, 1),
        "plastic_pct":      round(plastic_kg      / total_kg * 100, 1),
        "metal_pct":        round(metal_kg        / total_kg * 100, 1),
        "hazardous_pct":    round(hazardous_kg    / total_kg * 100, 1),
        "paper_pct":        round(paper_kg        / total_kg * 100, 1),
        "glass_pct":        round(glass_kg        / total_kg * 100, 1),
        "construction_pct": round(construction_kg / total_kg * 100, 1),
        "other_pct":        round(other_kg        / total_kg * 100, 1),
    }

    # Circularity score = mean hidden_value_score of known materials
    known = [r for r in results if r.get("status") == "analyzed"]
    circularity = round(
        sum(r.get("hidden_value_score", 0) for r in known) / len(known), 1
    ) if known else 0

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

    return {
        "agent":                   "Waste-to-Wealth Agent",
        "status":                  "analyzed",
        "total_items":             len(results),
        "analyzed_items":          len(known),
        "total_kg":                round(total_kg, 2),
        "total_recovery_min_inr":  round(total_rec_min, 2),
        "total_recovery_max_inr":  round(total_rec_max, 2),
        "hazardous_count":         hazardous_count,
        "circularity_score":       circularity,
        "composition":             composition,
        "top_opportunity":         top_item.get("waste_type") if top_item else None,
        "top_opportunity_value_max_inr": round(best_max, 2),
        "top_opportunity_pathway": top_item.get("recommended_pathway") if top_item else None,
        "compliance_warnings":     compliance_warnings,
        "items":                   results,
        "confidence":              0.88,
        "disclaimer":              get_disclaimer(),
    }


_ALIASES: dict[str, str] = {
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
    # Direct alias match
    if k in _ALIASES:
        return _ALIASES[k]
    # Partial alias match (e.g. "PET plastic bottles" → "pet")
    for alias, canonical in _ALIASES.items():
        if alias in k:
            return canonical
    return k


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


def analyze_waste(waste_type: str, quantity_kg: float) -> dict:
    kb        = _get_kb()
    materials = kb.get("waste_materials", {})

    validation = validate_quantity(quantity_kg)
    if not validation["valid"]:
        return {"error": validation["message"], "agent": "Waste-to-Wealth Agent"}

    raw_key  = waste_type.lower().strip()
    key      = normalize_waste_key(raw_key)
    material = materials.get(key)
    # If normalization found a match but the original was different, use the canonical name for display
    display_type = waste_type if material else waste_type

    if material is None:
        close_matches = [k for k in materials if key in k or k in key]
        # Infer likely category from keywords
        inferred_category = "Unknown"
        inferred_handling = "Store separately until classified. Do not mix with other waste streams."
        if any(w in key for w in ["plastic", "pet", "pp", "pvc", "poly"]):
            inferred_category = "Likely Plastic Waste"
            inferred_handling = "Keep dry. Do not compact with food waste. Contact local plastic recycler."
        elif any(w in key for w in ["metal", "steel", "iron", "copper", "alum", "brass"]):
            inferred_category = "Likely Metal Waste"
            inferred_handling = "Separate ferrous from non-ferrous. Store dry. Contact scrap dealer."
        elif any(w in key for w in ["paper", "card", "news", "office"]):
            inferred_category = "Likely Paper Waste"
            inferred_handling = "Keep dry. Bundle. Contact paper recycler or kabadiwala."
        elif any(w in key for w in ["food", "organic", "veg", "fruit", "kitchen", "wet"]):
            inferred_category = "Likely Organic Waste"
            inferred_handling = "Process within 24 hours. Compost or route to biogas plant."
        elif any(w in key for w in ["glass", "bottle", "jar"]):
            inferred_category = "Likely Glass Waste"
            inferred_handling = "Handle with gloves. Do not break further. Separate by color."
        elif any(w in key for w in ["hazard", "chemical", "toxic", "acid", "solvent"]):
            inferred_category = "Likely Hazardous Waste"
            inferred_handling = "CRITICAL: Do not mix. Label containers. Contact CPCB-authorised handler."
        elif any(w in key for w in ["wood", "timber", "plank", "log"]):
            inferred_category = "Likely Wood/Biomass Waste"
            inferred_handling = "Store dry. Keep treated wood separate. Contact biomass plant."
        elif any(w in key for w in ["e-waste", "electronic", "computer", "phone", "battery"]):
            inferred_category = "Likely E-waste"
            inferred_handling = "CRITICAL: Do not dismantle. Route to CPCB-authorized e-waste recycler only."
        return {
            "agent":              "Waste-to-Wealth Agent",
            "status":             "unknown_material",
            "waste_type":         waste_type,
            "quantity_kg":        quantity_kg,
            "message":            f"Material '{waste_type}' is not currently in the knowledge base.",
            "inferred_category":  inferred_category,
            "inferred_handling":  inferred_handling,
            "suggestions":        close_matches[:3],
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

    if not hazard_result["estimated_profit_suppressed"]:
        fallback_rec = (
            f"Submit the {quantity_kg} kg of {key} via the {material['recommended_pathway']} pathway "
            f"to maximise estimated recovery. Consider converting into "
            f"{material['possible_products'][0] if material['possible_products'] else 'a value-added product'} "
            "for the highest return."
        )
        prompt = f"""You are a waste management specialist. Write 2 actionable sentences for a sustainability officer.

Material: {waste_type}
Category: {material['category']}
Recommended pathway: {material['recommended_pathway']}
Possible products: {', '.join(material['possible_products'][:3])}
Estimated value: Rs. {min_val}-{max_val} per {unit} (market estimate)
Quantity: {quantity_kg} kg
Hidden value score: {hidden_value_score}/100

Rules:
- Say "estimated" for all financial figures
- Do not claim exact profit
- Name one specific product from the list
- Be actionable: tell the officer exactly what to do this week
- Do not use: revolutionary, powerful AI, next-generation"""

        ai_recommendation, ai_used = call_openai(prompt, fallback_rec)

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
        "possible_products":        material["possible_products"],
        "buyer_types":              material["buyer_types"],
        "recommended_pathway":      material["recommended_pathway"],
        "sustainability_notes":     material["sustainability_notes"],
        "risks":                    material["risks"],
        "hidden_value_score":       hidden_value_score,
        "estimated_recovery":       estimated_recovery,
        "estimated_recovery_note":  estimated_recovery_note,
        "ai_recommendation":        ai_recommendation,
        "ai_powered":               ai_used,
        "reasoning_trace":          reasoning_trace,
        "confidence":               0.92,
        "disclaimer":               get_disclaimer(),
        # Enriched fields — present in expanded knowledge base entries
        "co2_savings_kg_per_tonne": material.get("co2_savings_kg_per_tonne"),
        "compliance_notes":         material.get("compliance_notes"),
        "required_handling":        material.get("required_handling"),
        "knowledge_source":         material.get("knowledge_source"),
        "collection_frequency":     material.get("collection_frequency"),
        "preparation_before_sale":  material.get("preparation_before_sale"),
    }
