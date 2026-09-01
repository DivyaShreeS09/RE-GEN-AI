from core.guardrails import get_disclaimer
from core.openai_client import call_openai

# Reference base costs per action type. Scaled by consumption size in generate_decisions().
# W1 (leak repair + sensors): base Rs. 8000, +Rs. 10 per 1000 L above 1000 L weekly baseline.
# E1 (smart switches/timers): base Rs. 5000, +Rs. 8 per 1000 kWh above 100 kWh weekly baseline.
# W2 (waste routing/storage): fixed reference — no reliable consumption proxy; disclosed in roi.
_BASE_INSTALL = {"W1": 8000, "E1": 5000, "W2": 2000}


def _score_action(urgency: int, cost_saving: float, env_impact: float, feasibility: int) -> float:
    return round(
        urgency      * 0.35
        + min(cost_saving / 1000, 30) * 0.30
        + env_impact * 0.25
        + feasibility * 0.10,
        2,
    )


def _scale_install_cost(action_id: str, water_liters: float, energy_kwh: float) -> tuple:
    """Return (install_cost_inr, cost_basis) scaled from actual consumption where possible."""
    if action_id == "W1":
        extra = max(0.0, water_liters - 1000) / 1000 * 10
        cost = int(round(_BASE_INSTALL["W1"] + extra))
        cost = max(3000, min(cost, 50000))
        return cost, "scaled_from_water_consumption"
    if action_id == "E1":
        extra = max(0.0, energy_kwh - 100) / 1000 * 8
        cost = int(round(_BASE_INSTALL["E1"] + extra))
        cost = max(2000, min(cost, 30000))
        return cost, "scaled_from_energy_consumption"
    return _BASE_INSTALL.get(action_id, 5000), "industry_reference_estimate"


def _roi(install_cost: int, cost_basis: str, weekly_saving_inr: float) -> dict:
    monthly = round(weekly_saving_inr * 4.33, 2)
    if monthly <= 0:
        return {
            "install_cost_inr": install_cost,
            "cost_basis": cost_basis,
            "monthly_saving_inr": 0,
            "payback_months": None,
            "payback_note": "Insufficient saving data for ROI estimate.",
        }
    payback = round(install_cost / monthly, 1)
    basis_note = (
        "Cost estimated from your actual consumption data."
        if cost_basis in ("scaled_from_water_consumption", "scaled_from_energy_consumption")
        else "Cost is an industry reference estimate — not derived from your data."
    )
    return {
        "install_cost_inr":   install_cost,
        "cost_basis":         cost_basis,
        "monthly_saving_inr": monthly,
        "payback_months":     payback,
        "payback_note":       f"Estimated payback in {payback} months. {basis_note}",
    }


def generate_decisions(water_result: dict, energy_result: dict, waste_result: dict = None) -> dict:
    actions = []
    urgency_map = {"critical": 10, "high": 8, "medium": 5, "low": 3, "none": 1}

    water_total_liters = water_result.get("total_consumption_liters", 0)
    energy_total_kwh   = energy_result.get("total_consumption_kwh", 0)

    # --- Water action ---
    water_severity  = water_result.get("severity", "none")
    water_cost      = water_result.get("estimated_cost_inr", 0)
    water_liters    = water_result.get("total_wasted_liters", 0)
    water_urgency   = urgency_map.get(water_severity, 1)
    w1_install, w1_basis = _scale_install_cost("W1", water_total_liters, energy_total_kwh)

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
        "roi": _roi(w1_install, w1_basis, water_cost),
    })

    # --- Energy action ---
    energy_severity = energy_result.get("severity", "none")
    energy_cost     = energy_result.get("estimated_cost_inr", 0)
    energy_kwh      = energy_result.get("total_wasted_kwh",   0)
    energy_urgency  = urgency_map.get(energy_severity, 1)
    e1_install, e1_basis = _scale_install_cost("E1", water_total_liters, energy_total_kwh)

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
        "roi": _roi(e1_install, e1_basis, energy_cost),
    })

    # --- Waste action (optional) ---
    if waste_result and waste_result.get("status") == "analyzed":
        hidden_score = waste_result.get("hidden_value_score", 50)
        waste_urgency = 4 if waste_result.get("hazard_warning") else 3
        waste_cost = 0
        if waste_result.get("estimated_recovery"):
            waste_cost = waste_result["estimated_recovery"].get("max_inr", 0)
        w2_install, w2_basis = _scale_install_cost("W2", water_total_liters, energy_total_kwh)

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
            "roi": _roi(w2_install, w2_basis, waste_cost),
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
