# Gemini is used ONLY to generate the following narrative field: top_action_explanation.
# All numeric fields (priority_score, roi, urgency, feasibility, cost_saving_inr) are
# computed by deterministic Python above the Gemini call.
from core.guardrails import get_disclaimer
from core.ai_client import ai_status, call_ai
from typing import Literal
from pydantic import BaseModel, ConfigDict


class DecisionFocus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    focus: Literal["compare_baselines", "check_operating_context", "review_shared_observations"]

# Reference base costs per action type. Scaled by consumption size in generate_decisions().
# W1 (leak repair + sensors): base Rs. 8000, +Rs. 10 per 1000 L above 1000 L weekly baseline.
# E1 (smart switches/timers): base Rs. 5000, +Rs. 8 per 1000 kWh above 100 kWh weekly baseline.
# W2 (waste routing/storage): fixed reference — no reliable consumption proxy; disclosed in roi.
_BASE_INSTALL = {"W1": 8000, "E1": 5000, "W2": 2000}


def _score_action(urgency: int, cost_saving: float, env_impact: float, feasibility: int) -> float:
    return round(
        urgency      * 0.35
        + min((cost_saving or 0) / 1000, 10) * 0.30
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


def _roi(install_cost: int, cost_basis: str, period_saving_inr: float, days: float | None) -> dict:
    monthly = round(period_saving_inr * 30 / days, 2) if period_saving_inr is not None and days and days > 0 else None
    if not monthly:
        return {
            "install_cost_inr": install_cost,
            "cost_basis": cost_basis,
            "monthly_saving_inr": monthly,
            "reporting_days": days,
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
        "reporting_days": days,
        "assumption": "A 30-day month with the same average loss and tariff; indicative installation cost.",
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
        f"Flagged water consumption ({water_liters} L estimated above baseline)"
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
        "roi": _roi(w1_install, w1_basis, water_cost, water_result.get("reporting_days")),
    })

    # --- Energy action ---
    energy_severity = energy_result.get("severity", "none")
    energy_cost     = energy_result.get("estimated_cost_inr", 0)
    energy_kwh      = energy_result.get("total_wasted_kwh",   0)
    energy_urgency  = urgency_map.get(energy_severity, 1)
    e1_install, e1_basis = _scale_install_cost("E1", water_total_liters, energy_total_kwh)

    energy_issue = (
        f"Flagged electricity consumption ({energy_kwh} kWh estimated above baseline)"
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
        "roi": _roi(e1_install, e1_basis, energy_cost, energy_result.get("reporting_days")),
    })

    # --- Waste action (optional) ---
    if waste_result and waste_result.get("status") == "analyzed" and waste_result.get("analyzed_items", 1) > 0:
        hidden_score = waste_result.get("hidden_value_score", 50)
        hazard = waste_result.get("hazard_warning") or waste_result.get("hazardous_count", 0) > 0
        waste_urgency = 8 if hazard else 3
        waste_reference = (waste_result.get("estimated_recovery") or {}).get("max_inr")
        w2_install, w2_basis = _scale_install_cost("W2", water_total_liters, energy_total_kwh)

        measured_mass = waste_result.get("total_kg", waste_result.get("quantity_kg"))
        description = waste_result.get("waste_type") or "submitted inventory"
        actions.append({
            "id": "W2",
            "domain": "Waste",
            "issue": (
                f"Recovery assessment for {description}" + (f" ({measured_mass} kg)" if measured_mass is not None else "")
            ),
            "urgency": waste_urgency,
            "urgency_label": "HIGH" if hazard else "MEDIUM",
            "cost_saving_inr": None,
            "indicative_recovery_inr": waste_reference,
            "env_impact_score": hidden_score / 10,
            "feasibility": 7,
            "priority_score": _score_action(waste_urgency, 0, hidden_score / 10, 7),
            "recommended_action": (
                "Request authorized professional handling." if hazard else
                f"Ask facility staff to verify eligibility for {waste_result.get('recommended_pathway') or waste_result.get('top_opportunity_pathway') or 'recovery'}."
            ),
            "timeline": "Within 24 hours" if hazard else "Within 7 days",
            "roi": _roi(w2_install, w2_basis, 0, None),
        })

    recovery_priorities = []

    for item in (waste_result or {}).get("items", []):
        pathways = item.get("recovery_pathways") or []
        if not pathways:
            continue

        route = pathways[0]

        recovery_priorities.append({
            "material": item["waste_type"],
            "quantity_kg": item["quantity_kg"],
            "pathway": route["category"],
            "title": route["title"],
            "action": route["action"],
            "preparation": route.get("preparation"),
            "limitation": route.get("limitation"),
            "valuation": route.get("valuation"),
            "sdg_target": "12.5",
            "status": "proposed",
            "realized_value_inr": None,
        })

    skipped = {domain for domain, result in (("Water", water_result), ("Energy", energy_result))
               if result.get("status") == "skipped"}
    actions = [action for action in actions if action["domain"] not in skipped]
    resources = {"Water": water_result, "Energy": energy_result}
    actions = [action for action in actions if resources.get(action["domain"], {}).get("status") != "skipped"]
    signals = {}
    for domain, resource in resources.items():
        for event in resource.get("anomaly_events", []):
            zone = event.get("location") or event.get("zone")
            if event.get("timestamp") and zone and zone != "Unspecified":
                signals.setdefault((zone, event["date"]), set()).add(domain)
    relationships = [{"zone": zone, "date": date, "status": "co_occurrence",
                      "basis": "Water and electricity baseline exceptions in the same documented zone and date.",
                      "limitation": "Operating records or equipment evidence are needed to establish a common cause."}
                     for (zone, date), domains in sorted(signals.items()) if len(domains) == 2]
    for action in actions:
        if action["domain"] in ("Water", "Energy"):
            resource = water_result if action["domain"] == "Water" else energy_result
            if resource.get("is_uploaded"):
                action["cost_saving_inr"] = None
                action["roi"] = _roi(None, "Facility quotation and verified savings required.", None, None)
                action["env_impact_score"] = None
                action["priority_score"] = _score_action(action["urgency"], None, 0, action["feasibility"])
            action["roi"]["tariff"] = resource.get("tariff")
        resource = resources.get(action["domain"], {})
        action.update(status="proposed", approval_required=True,
                      responsible_role={"Water": "Authorized facilities maintenance", "Energy": "Qualified electrical facilities staff",
                                        "Waste": "Authorized waste coordinator"}[action["domain"]],
                      supporting_evidence=resource.get("anomaly_events", [])[:10],
                      verification_method="Document inspection and compare equivalent pre- and post-intervention observations.",
                      prerequisites=["Review the evidence and obtain facility approval before implementation."])

    if relationships:
        zones = sorted({entry["zone"] for entry in relationships})
        actions.append({
            "id": "R1", "domain": "Facilities", "issue": "Cross-resource baseline exceptions",
            "recommended_action": "Review water and electricity operating records together before selecting separate fixes.",
            "zones": zones, "urgency": 5, "urgency_label": "MEDIUM",
            "cost_saving_inr": None, "env_impact_score": None, "feasibility": 8,
            "priority_score": _score_action(5, None, 0, 8), "timeline": "Within 7 days",
            "roi": _roi(None, "Facility quotation and verified savings required.", None, None),
            "status": "proposed", "approval_required": True, "responsible_role": "Authorized facilities team",
            "supporting_evidence": relationships,
            "prerequisites": ["Compare operating schedules and check for documented shared equipment."],
            "verification_method": "Confirm or rule out a shared cause before any equipment or schedule changes.",
        })
        for action in actions:
            if action["domain"] in resources:
                action["depends_on"] = ["R1"]
                action["prerequisites"].append("Review the coordinated investigation before implementing zone changes.")
    actions.sort(key=lambda x: x["priority_score"], reverse=True)
    for i, a in enumerate(actions):
        a["rank"] = i + 1

    priced = [a["cost_saving_inr"] for a in actions if a["cost_saving_inr"] is not None]
    total_potential_saving = round(sum(priced), 2) if priced else None

    # --- AI: explain top-priority action in plain language ---
    top_action_explanation = ""
    ai_used = False
    ai_layer = None
    if actions:
        top = actions[0]
        environment_label = f"{top['env_impact_score']:.1f}/10" if top["env_impact_score"] is not None else "unquantified"
        cost_label = f"Rs. {top['cost_saving_inr']:.0f}" if top["cost_saving_inr"] is not None else "unavailable"
        fallback_explanation = (
            f"Prioritised based on composite score {top['priority_score']}: "
            f"urgency {top['urgency']}/10, estimated reporting-period saving {cost_label}, "
            f"environmental impact {environment_label}."
        )
        prompt = f"""You are a sustainability decision analyst. In exactly 2 clear sentences, explain to a sustainability officer WHY this action must be done FIRST.

Action: {top['recommended_action']}
Domain: {top['domain']}
Urgency level: {top['urgency_label']} ({top['urgency']}/10)
Estimated reporting-period saving: {cost_label}
Environmental impact: {environment_label}
Priority score: {top['priority_score']}
Estimated payback: {top['roi'].get('payback_months','N/A')} months

Rules:
- Say "estimated" for all financial values
- Reference the specific numbers above
- Keep the action proposed and conditional on authorized staff review. Do not add deadlines or claim savings.
- Do not use: revolutionary, powerful AI, real-time intelligence, next-generation"""

        historical = any(resource.get("is_uploaded") for resource in resources.values())
        if historical:
            approved = {
                "compare_baselines": "Review comparable observations to determine whether the deviation persists.",
                "check_operating_context": "Check the recorded operating conditions with authorized staff before selecting an intervention.",
            }
            if top["domain"] == "Facilities":
                approved["review_shared_observations"] = "Compare both resources with an operating log before attributing the exceptions to a shared cause."
            text, used = call_ai(
                f"Choose one explanation focus for the proposed {top['domain']} investigation. "
                f"Use only one eligible focus: {', '.join(approved)}. Return only JSON.",
                schema=DecisionFocus,
            )
            try:
                selected = DecisionFocus.model_validate_json(text).focus if used else None
            except ValueError:
                selected = None
            ai_used = selected in approved
            top_action_explanation = approved[selected] if ai_used else top["recommended_action"]
        else:
            top_action_explanation, ai_used = call_ai(prompt, fallback_explanation)
        top["ai_priority_explanation"] = top_action_explanation
        top["ai_enhanced"]             = ai_used
        ai_layer = ai_status() if ai_used else {"available": False, "provider": None, "model": None, "layer": "Rule-based (deterministic)"}

    reasoning_trace = [
        f"Step 1 — Received results from {len(actions)} domain agents.",
        "Step 2 — Scored each action: urgency (35%), cost saving (30%), env impact (25%), feasibility (10%).",
        f"Step 3 — Ranked {len(actions)} actions by composite priority score.",
        f"Step 4 — Top priority: {actions[0]['issue'] if actions else 'None'}.",
        f"Step 5 — Total estimated savings potential: Rs. {total_potential_saving}.",
        f"Step 6 — ROI payback estimates appended to each action.",
        f"Step 7 — AI reasoning layer: {'AI-enhanced explanation generated.' if ai_used else 'Rule-based fallback used (AI unavailable).'}",
    ]

    return {
        "agent":                       "Decision Engine Agent",
        "status":                      "analyzed",
        "ranked_actions":              actions,
        "recovery_priorities":         recovery_priorities,
        "cross_resource_relationships": relationships,
        "total_actions":               len(actions),
        "total_potential_saving_inr":  total_potential_saving,
        "top_priority_domain":         actions[0]["domain"] if actions else None,
        "top_action_explanation":      top_action_explanation,
        "ai_enhanced":                 ai_used,
        "ai_layer":                    ai_layer,
        "computation_type":            "deterministic",
        "reasoning_trace":             reasoning_trace,
        "confidence":                  None,
        "disclaimer":                  get_disclaimer(),
    }
