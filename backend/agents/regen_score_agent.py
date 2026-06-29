from core.scoring import calculate_regen_score, severity_label
from core.guardrails import get_disclaimer


def _campus_health_grade(score: float) -> dict:
    if score >= 90:
        return {"grade": "A+", "label": "Carbon-Neutral Ready",           "color": "green"}
    if score >= 80:
        return {"grade": "A",  "label": "Excellent Sustainability",        "color": "green"}
    if score >= 70:
        return {"grade": "B+", "label": "Good — Minor Gaps",               "color": "cyan"}
    if score >= 60:
        return {"grade": "B",  "label": "Good — Improvements Needed",      "color": "cyan"}
    if score >= 50:
        return {"grade": "C+", "label": "Moderate Risk",                   "color": "yellow"}
    if score >= 40:
        return {"grade": "C",  "label": "Moderate — Action Required",      "color": "yellow"}
    if score >= 30:
        return {"grade": "D",  "label": "Poor — Immediate Action Needed",  "color": "orange"}
    return    {"grade": "F",  "label": "Critical — Urgent Intervention",  "color": "red"}


def _rank_buildings(water_events: list, energy_events: list) -> list:
    buildings: dict = {}

    for ev in water_events:
        loc = ev.get("location", "Unknown Building")
        b = buildings.setdefault(loc, {"water_loss_liters": 0.0, "energy_loss_kwh": 0.0,
                                       "water_events": 0, "energy_events": 0})
        b["water_loss_liters"] += float(ev.get("estimated_waste_liters", 0))
        b["water_events"] += 1

    for ev in energy_events:
        zone = ev.get("zone", "Unknown Zone")
        b = buildings.setdefault(zone, {"water_loss_liters": 0.0, "energy_loss_kwh": 0.0,
                                        "water_events": 0, "energy_events": 0})
        b["energy_loss_kwh"] += float(ev.get("wasted_kwh", 0))
        b["energy_events"] += 1

    ranked = []
    for name, data in buildings.items():
        risk_score = min(100.0, data["water_loss_liters"] / 15 + data["energy_loss_kwh"] * 1.5)
        wl = data["water_loss_liters"]
        el = data["energy_loss_kwh"]
        water_sev = ("critical" if wl > 500 else "high" if wl > 200 else
                     "medium"   if wl > 50  else "low"  if wl > 0   else "none")
        energy_sev = ("high"   if el > 100 else "medium" if el > 50 else
                      "low"    if el > 0   else "none")
        ranked.append({
            "building":           name,
            "water_loss_liters":  round(wl, 1),
            "energy_loss_kwh":    round(el, 1),
            "total_events":       data["water_events"] + data["energy_events"],
            "risk_score":         round(risk_score, 1),
            "water_severity":     water_sev,
            "energy_severity":    energy_sev,
        })

    ranked.sort(key=lambda x: x["risk_score"], reverse=True)
    for i, b in enumerate(ranked):
        b["rank"] = i + 1
    return ranked


def compute_regen_score(water_result: dict, energy_result: dict,
                         impact_result: dict, decision_result: dict) -> dict:
    water_severity_score  = water_result.get("severity_score", 50)
    energy_severity_score = energy_result.get("severity_score", 50)
    sustainability_score  = impact_result.get("sustainability_score", 50)

    wasted_liters = water_result.get("total_wasted_liters", 0)
    wasted_kwh    = energy_result.get("total_wasted_kwh",   0)

    water_saving_potential  = min(100, 100 - (wasted_liters / 10))
    energy_saving_potential = min(100, 100 - (wasted_kwh    / 5))

    waste_recovery   = 60
    feasibility_avg  = 82
    urgency_reduction = 100 - (
        sum(a.get("urgency", 5) * 10 for a in decision_result.get("ranked_actions", []))
        / max(len(decision_result.get("ranked_actions", [])), 1)
    )
    urgency_reduction = max(0, min(100, urgency_reduction))

    before_score = calculate_regen_score(
        waste_score=max(0, waste_recovery          - 25),
        water_score=max(0, water_saving_potential  - 20),
        energy_score=max(0, energy_saving_potential - 20),
        co2_score=max(0, sustainability_score      - 15),
        urgency_score=max(0, urgency_reduction     - 15),
        feasibility_score=feasibility_avg          - 10,
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
        "waste_recovery_potential":  round(waste_recovery,          1),
        "water_saving_potential":    round(water_saving_potential,  1),
        "energy_saving_potential":   round(energy_saving_potential, 1),
        "co2_reduction_score":       round(sustainability_score,    1),
        "urgency_reduction_score":   round(urgency_reduction,       1),
        "feasibility_score":         round(feasibility_avg,         1),
    }

    # Campus Health Index
    before_health = _campus_health_grade(before_score)
    after_health  = _campus_health_grade(after_score)
    campus_health_index = {
        "current_grade":  before_health["grade"],
        "current_label":  before_health["label"],
        "current_color":  before_health["color"],
        "target_grade":   after_health["grade"],
        "target_label":   after_health["label"],
        "target_color":   after_health["color"],
        "interpretation": (
            f"Current campus sustainability posture is {before_health['label']} "
            f"(Grade {before_health['grade']}). Implementing all agent-recommended "
            f"interventions is projected to lift this to {after_health['label']} "
            f"(Grade {after_health['grade']}) — a +{improvement}-point improvement."
        ),
    }

    # Building risk ranking
    building_risk_ranking = _rank_buildings(
        water_result.get("anomaly_events", []),
        energy_result.get("anomaly_events", []),
    )

    explanation = []
    if wasted_liters > 200:
        explanation.append(
            f"Water leakage of {wasted_liters} L is dragging down the water savings score by ~20 points.")
    if wasted_kwh > 50:
        explanation.append(
            f"After-hours energy waste of {wasted_kwh} kWh reduces energy score significantly.")
    if improvement > 0:
        explanation.append(
            f"Implementing all recommended actions is estimated to raise RE:GEN Score by {improvement} points.")
    explanation.append(
        f"Before-action risk score: {before_score}/100 — After-action target: {after_score}/100.")

    reasoning_trace = [
        f"Step 1 — Aggregated scores: Water={water_severity_score}, Energy={energy_severity_score}, Sustainability={sustainability_score}.",
        f"Step 2 — Sub-scores: waste={waste_recovery}, water={round(water_saving_potential,1)}, "
        f"energy={round(energy_saving_potential,1)}, co2={sustainability_score}, "
        f"urgency={round(urgency_reduction,1)}, feasibility={feasibility_avg}.",
        f"Step 3 — Before-action score (current state): {before_score}/100.",
        f"Step 4 — After-action score (all fixes applied): {after_score}/100.",
        f"Step 5 — Score improvement: +{improvement} points.",
        f"Step 6 — Campus Health Grade: {before_health['grade']} -> {after_health['grade']}.",
        f"Step 7 — Building risk ranking computed across {len(building_risk_ranking)} location(s).",
    ]

    return {
        "agent":                  "RE:GEN Score Agent",
        "status":                 "computed",
        "before_score":           before_score,
        "after_score":            after_score,
        "improvement":            improvement,
        "current_rating":         severity_label(before_score),
        "target_rating":          severity_label(after_score),
        "score_breakdown":        score_breakdown,
        "campus_health_index":    campus_health_index,
        "building_risk_ranking":  building_risk_ranking,
        "explanation":            explanation,
        "reasoning_trace":        reasoning_trace,
        "confidence":             0.88,
        "disclaimer":             get_disclaimer(),
    }
