from core.guardrails import get_disclaimer
from core.openai_client import call_openai

# Estimated one-time install costs (simulated; clearly marked)
_INSTALL_COST = {"W1": 8000, "E1": 5000, "W2": 2000}


def _score_action(urgency: int, cost_saving: float, env_impact: float, feasibility: int) -> float:
    return round(
        urgency      * 0.35
        + min(cost_saving / 1000, 30) * 0.30
        + env_impact * 0.25
        + feasibility * 0.10,
        2,
    )


def _roi(action_id: str, weekly_saving_inr: float) -> dict:
    install = _INSTALL_COST.get(action_id, 5000)
    monthly = round(weekly_saving_inr * 4.33, 2)
    if monthly <= 0:
        return {
            "install_cost_inr": install,
            "monthly_saving_inr": 0,
            "payback_months": None,
            "payback_note": "Insufficient saving data for ROI estimate (simulated).",
        }
    payback = round(install / monthly, 1)
    return {
        "install_cost_inr":   install,
        "monthly_saving_inr": monthly,
        "payback_months":     payback,
        "payback_note":       f"Estimated payback in {payback} months (simulated; actual costs vary).",
    }


def generate_decisions(water_result: dict, energy_result: dict, waste_result: dict = None) -> dict:
    actions = []
    urgency_map = {"critical": 10, "high": 8, "medium": 5, "low": 3, "none": 1}

    # --- Water action ---
    water_severity  = water_result.get("severity", "none")
    water_cost      = water_result.get("estimated_cost_inr", 0)
    water_liters    = water_result.get("total_wasted_liters", 0)
    water_urgency   = urgency_map.get(water_severity, 1)

    water_issue = (
        f"Night-time water leakage detected ({water_liters} L wasted)"
        if water_liters > 0 else
        "Water consumption analysis — no anomalous flow detected at current data resolution"
    )
    actions.append({
        "id": "W1",
        "domain": "Water",
        "issue": water_issue,
        "urgency": water_urgency,
        "urgency_label": water_severity.upper(),
        "cost_saving_inr": water_cost,
        "env_impact_score": min(water_liters / 100, 10),
        "feasibility": 9,
        "priority_score": _score_action(water_urgency, water_cost, min(water_liters / 100, 10), 9),
        "recommended_action": (water_result.get("recommendations") or ["Inspect pipes"])[0],
        "timeline": "Immediate" if water_severity in ("critical", "high") else "Within 7 days",
        "roi": _roi("W1", water_cost),
    })

    # --- Energy action ---
    energy_severity = energy_result.get("severity", "none")
    energy_cost     = energy_result.get("estimated_cost_inr", 0)
    energy_kwh      = energy_result.get("total_wasted_kwh",   0)
    energy_urgency  = urgency_map.get(energy_severity, 1)

    energy_issue = (
        f"After-hours energy waste detected ({energy_kwh} kWh wasted)"
        if energy_kwh > 0 else
        "Energy consumption analysis — no after-hours anomalies detected at current data resolution"
    )
    actions.append({
        "id": "E1",
        "domain": "Energy",
        "issue": energy_issue,
        "urgency": energy_urgency,
        "urgency_label": energy_severity.upper(),
        "cost_saving_inr": energy_cost,
        "env_impact_score": min(energy_kwh / 20, 10),
        "feasibility": 8,
        "priority_score": _score_action(energy_urgency, energy_cost, min(energy_kwh / 20, 10), 8),
        "recommended_action": (energy_result.get("recommendations") or ["Install smart timers"])[0],
        "timeline": "Immediate" if energy_severity in ("critical", "high") else "Within 7 days",
        "roi": _roi("E1", energy_cost),
    })

    # --- Waste action (optional) ---
    if waste_result and waste_result.get("status") == "analyzed":
        hidden_score = waste_result.get("hidden_value_score", 50)
        waste_urgency = 4 if waste_result.get("hazard_warning") else 3
        waste_cost = 0
        if waste_result.get("estimated_recovery"):
            waste_cost = waste_result["estimated_recovery"].get("max_inr", 0)

        actions.append({
            "id": "W2",
            "domain": "Waste",
            "issue": (
                f"Unrecovered waste: {waste_result.get('waste_type','unknown')} "
                f"({waste_result.get('quantity_kg',0)} kg)"
            ),
            "urgency": waste_urgency,
            "urgency_label": "HIGH" if waste_result.get("hazard_warning") else "MEDIUM",
            "cost_saving_inr": waste_cost,
            "env_impact_score": hidden_score / 10,
            "feasibility": 7,
            "priority_score": _score_action(waste_urgency, waste_cost, hidden_score / 10, 7),
            "recommended_action": (
                f"Follow {waste_result.get('recommended_pathway','recycle')} pathway immediately."
            ),
            "timeline": "Within 24 hours" if waste_result.get("hazard_warning") else "Within 7 days",
            "roi": _roi("W2", waste_cost),
        })

    actions.sort(key=lambda x: x["priority_score"], reverse=True)
    for i, a in enumerate(actions):
        a["rank"] = i + 1

    total_potential_saving = sum(a["cost_saving_inr"] for a in actions)

    # --- AI: explain top-priority action in plain language ---
    top_action_explanation = ""
    ai_used = False
    if actions:
        top = actions[0]
        fallback_explanation = (
            f"Prioritised based on composite score {top['priority_score']}: "
            f"urgency {top['urgency']}/10, estimated weekly saving Rs. {top['cost_saving_inr']:.0f}, "
            f"environmental impact {top['env_impact_score']:.1f}/10."
        )
        prompt = f"""You are a sustainability decision analyst. In exactly 2 clear sentences, explain to a sustainability officer WHY this action must be done FIRST.

Action: {top['recommended_action']}
Domain: {top['domain']}
Urgency level: {top['urgency_label']} ({top['urgency']}/10)
Estimated weekly saving: Rs. {top['cost_saving_inr']:.0f}
Environmental impact score: {top['env_impact_score']:.1f}/10
Priority score: {top['priority_score']}
Estimated payback: {top['roi'].get('payback_months','N/A')} months

Rules:
- Say "estimated" for all financial values
- Reference the specific numbers above
- Tell the officer exactly what to do within 24 hours
- Do not use: revolutionary, powerful AI, real-time intelligence, next-generation"""

        top_action_explanation, ai_used = call_openai(prompt, fallback_explanation)
        top["ai_priority_explanation"] = top_action_explanation
        top["ai_powered"]              = ai_used

    reasoning_trace = [
        f"Step 1 — Received results from {len(actions)} domain agents.",
        "Step 2 — Scored each action: urgency (35%), cost saving (30%), env impact (25%), feasibility (10%).",
        f"Step 3 — Ranked {len(actions)} actions by composite priority score.",
        f"Step 4 — Top priority: {actions[0]['issue'] if actions else 'None'}.",
        f"Step 5 — Total estimated savings potential: Rs. {round(total_potential_saving, 2)}.",
        f"Step 6 — ROI payback estimates appended to each action.",
        f"Step 7 — AI reasoning layer: {'AI-enhanced explanation generated.' if ai_used else 'Rule-based fallback used (AI unavailable).'}",
    ]

    return {
        "agent":                       "Decision Engine Agent",
        "status":                      "analyzed",
        "ranked_actions":              actions,
        "total_actions":               len(actions),
        "total_potential_saving_inr":  round(total_potential_saving, 2),
        "top_priority_domain":         actions[0]["domain"] if actions else None,
        "top_action_explanation":      top_action_explanation,
        "ai_enhanced":                 ai_used,
        "reasoning_trace":             reasoning_trace,
        "confidence":                  0.90,
        "disclaimer":                  get_disclaimer(),
    }
