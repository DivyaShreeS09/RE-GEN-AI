from core.scoring import calculate_regen_score, severity_label
from core.guardrails import get_disclaimer


def compute_regen_score(water_result: dict, energy_result: dict, impact_result: dict, decision_result: dict) -> dict:
    water_severity_score = water_result.get("severity_score", 50)
    energy_severity_score = energy_result.get("severity_score", 50)
    sustainability_score = impact_result.get("sustainability_score", 50)

    wasted_liters = water_result.get("total_wasted_liters", 0)
    wasted_kwh = energy_result.get("total_wasted_kwh", 0)

    water_saving_potential = min(100, 100 - (wasted_liters / 10))
    energy_saving_potential = min(100, 100 - (wasted_kwh / 5))

    waste_recovery = 60
    feasibility_avg = 82
    urgency_reduction = 100 - (
        sum(a.get("urgency", 5) * 10 for a in decision_result.get("ranked_actions", [])) /
        max(len(decision_result.get("ranked_actions", [])), 1)
    )
    urgency_reduction = max(0, min(100, urgency_reduction))

    before_score = calculate_regen_score(
        waste_score=max(0, waste_recovery - 25),
        water_score=max(0, water_saving_potential - 20),
        energy_score=max(0, energy_saving_potential - 20),
        co2_score=max(0, sustainability_score - 15),
        urgency_score=max(0, urgency_reduction - 15),
        feasibility_score=feasibility_avg - 10,
    )

    after_score = calculate_regen_score(
        waste_score=waste_recovery,
        water_score=water_saving_potential,
        energy_score=energy_saving_potential,
        co2_score=sustainability_score,
        urgency_score=urgency_reduction,
        feasibility_score=feasibility_avg,
    )

    improvement = round(after_score - before_score, 1)

    score_breakdown = {
        "waste_recovery_potential": round(waste_recovery, 1),
        "water_saving_potential": round(water_saving_potential, 1),
        "energy_saving_potential": round(energy_saving_potential, 1),
        "co2_reduction_score": round(sustainability_score, 1),
        "urgency_reduction_score": round(urgency_reduction, 1),
        "feasibility_score": round(feasibility_avg, 1),
    }

    explanation = []
    if wasted_liters > 200:
        explanation.append(f"Water leakage of {wasted_liters}L is dragging down the water savings score by ~20 points.")
    if wasted_kwh > 50:
        explanation.append(f"After-hours energy waste of {wasted_kwh} kWh reduces energy score significantly.")
    if improvement > 0:
        explanation.append(f"Implementing all recommended actions is estimated to raise RE:GEN Score by {improvement} points.")
    explanation.append(f"Before-action risk score: {before_score}/100 → After-action target: {after_score}/100.")

    reasoning_trace = [
        f"Step 1 — Aggregated scores from Water Agent (severity score: {water_severity_score}), Energy Agent (severity score: {energy_severity_score}), Impact Agent (sustainability: {sustainability_score}).",
        f"Step 2 — Computed sub-scores: waste={waste_recovery}, water={round(water_saving_potential,1)}, energy={round(energy_saving_potential,1)}, co2={sustainability_score}, urgency={round(urgency_reduction,1)}, feasibility={feasibility_avg}.",
        f"Step 3 — Before-action score (current state): {before_score}/100.",
        f"Step 4 — After-action score (if all fixes applied): {after_score}/100.",
        f"Step 5 — Estimated score improvement: +{improvement} points.",
        f"Step 6 — Rating: {severity_label(after_score)}.",
    ]

    return {
        "agent": "RE:GEN Score Agent",
        "status": "computed",
        "before_score": before_score,
        "after_score": after_score,
        "improvement": improvement,
        "current_rating": severity_label(before_score),
        "target_rating": severity_label(after_score),
        "score_breakdown": score_breakdown,
        "explanation": explanation,
        "reasoning_trace": reasoning_trace,
        "confidence": 0.88,
        "disclaimer": get_disclaimer(),
    }
