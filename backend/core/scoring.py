def calculate_regen_score(waste_score, water_score, energy_score, co2_score, urgency_score, feasibility_score):
    weights = {
        "waste": 0.20,
        "water": 0.20,
        "energy": 0.20,
        "co2": 0.15,
        "urgency": 0.15,
        "feasibility": 0.10,
    }
    raw = (
        waste_score * weights["waste"]
        + water_score * weights["water"]
        + energy_score * weights["energy"]
        + co2_score * weights["co2"]
        + urgency_score * weights["urgency"]
        + feasibility_score * weights["feasibility"]
    )
    return round(min(max(raw, 0), 100), 1)


def severity_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Moderate"
    elif score >= 20:
        return "Poor"
    return "Critical"


def urgency_from_severity(severity: str) -> str:
    mapping = {
        "critical": "Immediate",
        "high": "Within 24 hours",
        "medium": "Within 7 days",
        "low": "Within 30 days",
        "none": "Routine monitoring",
    }
    return mapping.get(severity.lower(), "Within 7 days")
