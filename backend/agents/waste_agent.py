from core.simulation import load_waste_kb
from core.guardrails import apply_hazard_guardrail, validate_quantity, get_disclaimer

_kb = None


def _get_kb():
    global _kb
    if _kb is None:
        _kb = load_waste_kb()
    return _kb


def analyze_waste(waste_type: str, quantity_kg: float) -> dict:
    kb = _get_kb()
    materials = kb.get("waste_materials", {})

    validation = validate_quantity(quantity_kg)
    if not validation["valid"]:
        return {"error": validation["message"], "agent": "Waste-to-Wealth Agent"}

    key = waste_type.lower().strip()
    material = materials.get(key)

    if material is None:
        close_matches = [k for k in materials if key in k or k in key]
        return {
            "agent": "Waste-to-Wealth Agent",
            "status": "unknown_material",
            "waste_type": waste_type,
            "message": f"Material '{waste_type}' not in knowledge base.",
            "suggestions": close_matches[:3],
            "disclaimer": get_disclaimer(),
        }

    hazard_result = apply_hazard_guardrail(material["hazard_level"])

    min_val = material["estimated_value_range"]["min"]
    max_val = material["estimated_value_range"]["max"]
    unit = material["estimated_value_range"]["unit"]

    if hazard_result["estimated_profit_suppressed"]:
        estimated_recovery = None
        estimated_recovery_note = hazard_result["profit_note"]
    else:
        estimated_recovery = {
            "min_inr": round(min_val * quantity_kg, 2),
            "max_inr": round(max_val * quantity_kg, 2),
            "unit_rate": f"{min_val}–{max_val} {unit}",
            "note": "Estimated only. Actual market prices vary.",
        }
        estimated_recovery_note = None

    hidden_value_score = material["hidden_value_score"]

    reasoning_trace = [
        f"Step 1 — Material identified: '{key}' in knowledge base.",
        f"Step 2 — Category: {material['category']}. Hazard level: {material['hazard_level']}.",
        f"Step 3 — Hazard guardrail applied: {'YES – warning triggered' if hazard_result['warning'] else 'No hazard detected'}.",
        f"Step 4 — Possible products identified: {', '.join(material['possible_products'][:3])}.",
        f"Step 5 — Recommended pathway: {material['recommended_pathway']}.",
        f"Step 6 — Hidden value score computed: {hidden_value_score}/100.",
        f"Step 7 — Estimated recovery calculated for {quantity_kg} kg.",
    ]

    return {
        "agent": "Waste-to-Wealth Agent",
        "status": "analyzed",
        "waste_type": waste_type,
        "quantity_kg": quantity_kg,
        "category": material["category"],
        "composition": material["composition"],
        "hazard_level": material["hazard_level"],
        "hazard_warning": hazard_result["warning"],
        "hazard_message": hazard_result["warning_message"],
        "possible_products": material["possible_products"],
        "buyer_types": material["buyer_types"],
        "recommended_pathway": material["recommended_pathway"],
        "sustainability_notes": material["sustainability_notes"],
        "risks": material["risks"],
        "hidden_value_score": hidden_value_score,
        "estimated_recovery": estimated_recovery,
        "estimated_recovery_note": estimated_recovery_note,
        "reasoning_trace": reasoning_trace,
        "confidence": 0.92,
        "disclaimer": get_disclaimer(),
    }
