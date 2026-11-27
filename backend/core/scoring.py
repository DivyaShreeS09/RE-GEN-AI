REGEN_SCORE_WEIGHTS = {
    "waste": 0.20,
    "water": 0.20,
    "energy": 0.20,
    "co2": 0.15,
    "urgency": 0.15,
    "feasibility": 0.10,
}


def calculate_regen_score(waste_score, water_score, energy_score, co2_score, urgency_score, feasibility_score):
    raw = (
        waste_score * REGEN_SCORE_WEIGHTS["waste"]
        + water_score * REGEN_SCORE_WEIGHTS["water"]
        + energy_score * REGEN_SCORE_WEIGHTS["energy"]
        + co2_score * REGEN_SCORE_WEIGHTS["co2"]
        + urgency_score * REGEN_SCORE_WEIGHTS["urgency"]
        + feasibility_score * REGEN_SCORE_WEIGHTS["feasibility"]
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


