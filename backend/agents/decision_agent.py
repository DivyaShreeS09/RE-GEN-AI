from core.guardrails import get_disclaimer


def _score_action(urgency: int, cost_saving: float, env_impact: float, feasibility: int) -> float:
    return round(
        urgency * 0.35
        + min(cost_saving / 1000, 30) * 0.30
        + env_impact * 0.25
        + feasibility * 0.10,
        2,
    )


def generate_decisions(water_result: dict, energy_result: dict, waste_result: dict = None) -> dict:
    actions = []

    water_severity = water_result.get("severity", "none")
    water_cost = water_result.get("estimated_cost_inr", 0)
    water_liters = water_result.get("total_wasted_liters", 0)

    urgency_map = {"critical": 10, "high": 8, "medium": 5, "low": 3, "none": 1}
    water_urgency = urgency_map.get(water_severity, 1)

    actions.append({
        "id": "W1",
        "domain": "Water",
        "issue": f"Night-time water leakage detected ({water_liters} L wasted)",
        "urgency": water_urgency,
        "urgency_label": water_severity.upper(),
        "cost_saving_inr": water_cost,
        "env_impact_score": min(water_liters / 100, 10),
        "feasibility": 9,
        "priority_score": _score_action(water_urgency, water_cost, min(water_liters / 100, 10), 9),
        "recommended_action": water_result.get("recommendations", ["Inspect pipes"])[0],
        "timeline": "Immediate" if water_severity in ("critical", "high") else "Within 7 days",
    })

    energy_severity = energy_result.get("severity", "none")
    energy_cost = energy_result.get("estimated_cost_inr", 0)
    energy_kwh = energy_result.get("total_wasted_kwh", 0)
    energy_urgency = urgency_map.get(energy_severity, 1)

    actions.append({
        "id": "E1",
        "domain": "Energy",
        "issue": f"After-hours energy waste detected ({energy_kwh} kWh wasted)",
        "urgency": energy_urgency,
        "urgency_label": energy_severity.upper(),
        "cost_saving_inr": energy_cost,
        "env_impact_score": min(energy_kwh / 20, 10),
        "feasibility": 8,
        "priority_score": _score_action(energy_urgency, energy_cost, min(energy_kwh / 20, 10), 8),
        "recommended_action": energy_result.get("recommendations", ["Install smart timers"])[0],
        "timeline": "Immediate" if energy_severity in ("critical", "high") else "Within 7 days",
    })

    if waste_result and waste_result.get("status") == "analyzed":
        hidden_score = waste_result.get("hidden_value_score", 50)
        waste_urgency = 4 if waste_result.get("hazard_warning") else 3
        waste_cost = 0
        if waste_result.get("estimated_recovery"):
            waste_cost = waste_result["estimated_recovery"].get("max_inr", 0)

        actions.append({
            "id": "W2",
            "domain": "Waste",
            "issue": f"Unrecovered waste: {waste_result.get('waste_type', 'unknown')} ({waste_result.get('quantity_kg', 0)} kg)",
            "urgency": waste_urgency,
            "urgency_label": "HIGH" if waste_result.get("hazard_warning") else "MEDIUM",
            "cost_saving_inr": waste_cost,
            "env_impact_score": hidden_score / 10,
            "feasibility": 7,
            "priority_score": _score_action(waste_urgency, waste_cost, hidden_score / 10, 7),
            "recommended_action": f"Follow {waste_result.get('recommended_pathway', 'recycle')} pathway immediately.",
            "timeline": "Within 24 hours" if waste_result.get("hazard_warning") else "Within 7 days",
        })

    actions.sort(key=lambda x: x["priority_score"], reverse=True)
    for i, action in enumerate(actions):
        action["rank"] = i + 1

    total_potential_saving = sum(a["cost_saving_inr"] for a in actions)

    reasoning_trace = [
        f"Step 1 — Received results from {len(actions)} domain agents.",
        f"Step 2 — Scored each action on: urgency (35%), cost saving (30%), environmental impact (25%), feasibility (10%).",
        f"Step 3 — Ranked {len(actions)} actions by composite priority score.",
        f"Step 4 — Top priority: {actions[0]['issue'] if actions else 'None'}.",
        f"Step 5 — Total estimated savings potential: ₹{round(total_potential_saving, 2)}.",
    ]

    return {
        "agent": "Decision Engine Agent",
        "status": "analyzed",
        "ranked_actions": actions,
        "total_actions": len(actions),
        "total_potential_saving_inr": round(total_potential_saving, 2),
        "top_priority_domain": actions[0]["domain"] if actions else None,
        "reasoning_trace": reasoning_trace,
        "confidence": 0.90,
        "disclaimer": get_disclaimer(),
    }
