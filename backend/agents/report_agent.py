# Gemini is used ONLY to generate the following narrative field: executive_summary.
# All numeric fields (silent_losses, campus_health_index, building_risk_ranking, action_plan
# thresholds, sdg_alignment, data_notice) are computed by deterministic Python above the call.
from datetime import datetime, timezone
from core.guardrails import get_disclaimer, get_simulated_notice
from core.ai_client import call_ai, ai_status


def _fallback_summary(water, energy, impact, regen, ranked,
                      data_source: str = "Simulated sensor logs, January 15–21, 2024",
                      org_name: str = None) -> str:
    if impact.get("evidence_type") == "historical analysis":
        observations = [f"{label}: {result[key]:,.2f} {unit} observed."
                        for label, result, key, unit in (("Water", water, "total_consumption_liters", "L"),
                                                         ("Energy", energy, "total_consumption_kwh", "kWh"))
                        if result.get(key) is not None]
        exposure = impact.get("anomaly_cost_exposure_inr")
        lines = [f"Data source: {data_source}.", *observations,
                 f"Comparable utility anomaly exposure: INR {exposure:,.2f}." if exposure is not None
                 else "Utility anomaly exposure is unquantified.",
                 "Baseline exceptions require inspection. Verified savings and avoided emissions are unavailable.",
                 ranked[0]["recommended_action"] if ranked else "No intervention was prioritized."]
        return "\n\n".join(lines)
    total_loss = round((water.get("estimated_cost_inr") or 0) + (energy.get("estimated_cost_inr") or 0), 2)
    org_label = f"{org_name} " if org_name else ""
    water_skip = water.get("status") == "skipped"
    energy_skip = energy.get("status") == "skipped"
    water_line = (
        f"Water leakage analysis: {water.get('total_wasted_liters', 0)} L estimated wasted "
        f"(Rs. {water.get('estimated_cost_inr', 0)} for this period)."
        if not water_skip else "Water data not provided — water analysis skipped."
    )
    energy_line = (
        f"After-hours energy waste: {energy.get('total_wasted_kwh', 0)} kWh "
        f"(Rs. {energy.get('estimated_cost_inr', 0)} for this period)."
        if not energy_skip else "Energy data not provided — energy analysis skipped."
    )
    return (
        f"RE:GEN AI {org_label}Sustainability Analysis — {datetime.now(timezone.utc).strftime('%B %d, %Y')}\n\n"
        f"Data source: {data_source}.\n"
        f"{water_line} {energy_line} "
        f"Combined estimated reporting-period utility loss: Rs. {total_loss}.\n\n"
        f"Top recommended intervention: "
        f"{ranked[0]['recommended_action'] if ranked else 'No critical actions detected'}. "
        f"Recommended timeline: {ranked[0].get('timeline', 'immediately') if ranked else 'as soon as possible'}.\n\n"
        f"Implementing all agent-recommended actions is projected to raise the RE:GEN Score from "
        f"{regen.get('before_score', 'N/A')}/100 to {regen.get('after_score', 'N/A')}/100, "
        f"with an estimated {impact.get('total_co2_saved_kg', 0)} kg CO2 reduction for the reporting period — equivalent to "
        f"{impact.get('trees_equivalent', 0)} trees or {impact.get('vehicle_km_equivalent', 0)} km "
        f"of car travel offset.\n\n"
        "Note: RE:GEN AI is a prototype decision-support system. "
        "This is not professional regulatory, financial, or engineering advice."
    )


def generate_report(
    water_result:      dict,
    energy_result:     dict,
    impact_result:     dict,
    decision_result:   dict,
    regen_score_result: dict,
    waste_result:      dict = None,
    org_name:          str = None,
    org_type:          str = None,
    data_source:       str = "Simulated sensor logs, January 15–21, 2024",
    coverage:          dict = None,
    analysis_metadata: dict = None,
) -> dict:
    ranked    = decision_result.get("ranked_actions", [])
    immediate = [a for a in ranked if a.get("timeline") in {"Immediate", "Within 24 hours"}]
    week      = [a for a in ranked if "7" in str(a.get("timeline", ""))]

    action_plan = {
        "immediate": [
            {
                "action":               a["recommended_action"],
                "domain":               a["domain"],
                "estimated_saving_inr": a["cost_saving_inr"],
                "priority_score":       a["priority_score"],
                "roi":                  a.get("roi"),
                **{field: a.get(field) for field in ("id", "status", "responsible_role", "supporting_evidence",
                                                     "verification_method", "prerequisites", "approval_required", "zones", "depends_on")},
            }
            for a in immediate
        ],
        "next_7_days": [
            {
                "action":               a["recommended_action"],
                "domain":               a["domain"],
                "estimated_saving_inr": a["cost_saving_inr"],
                "priority_score":       a["priority_score"],
                "roi":                  a.get("roi"),
                **{field: a.get(field) for field in ("id", "status", "responsible_role", "supporting_evidence",
                                                     "verification_method", "prerequisites", "approval_required", "zones", "depends_on")},
            }
            for a in week
        ],
        "next_30_days": [
            {"action": "Conduct a comprehensive energy audit across all buildings and major load centres.", "domain": "Energy", "source": "General Best Practice Recommendation"},
            {"action": "Install automated water sub-meters at high-consumption points and distribution headers.", "domain": "Water", "source": "General Best Practice Recommendation"},
            {"action": "Set up centralised waste segregation stations with colour-coded bins at source points.", "domain": "Waste", "source": "General Best Practice Recommendation"},
        ],
        "long_term": [
            {"action": "Deploy IoT-based smart meters for real-time water and energy monitoring.", "domain": "Infrastructure", "source": "General Best Practice Recommendation"},
            {"action": "Establish on-site biogas plant to convert wet waste to cooking gas.", "domain": "Waste", "source": "General Best Practice Recommendation"},
            {"action": "Partner with certified e-waste and hazardous waste recyclers under EPR agreement.", "domain": "Compliance", "source": "General Best Practice Recommendation"},
            {"action": "Target RE:GEN Score > 80 (Excellent) within 12 months.", "domain": "Sustainability", "source": "General Best Practice Recommendation"},
        ],
    }

    # --- AI executive summary ---
    fallback = _fallback_summary(
        water_result, energy_result, impact_result, regen_score_result, ranked,
        data_source=data_source, org_name=org_name,
    )
    total_loss = round(
        (water_result.get("estimated_cost_inr") or 0) + (energy_result.get("estimated_cost_inr") or 0), 2
    )
    level_label  = analysis_metadata.get("overall_label", "Advanced AI Analysis") if analysis_metadata else "Advanced AI Analysis"
    coverage_pct = coverage.get("data_coverage_pct") if coverage else None
    skipped_mods = ", ".join(m["module"] for m in (analysis_metadata or {}).get("skipped_modules", [])) or "None"
    anomaly_note = (
        f"Note: Anomaly detection was unavailable at this data resolution (analysis level: {level_label}). "
        f"Figures reflect consumption estimates only, not confirmed leakage or waste events. "
        f"Dataset coverage: {coverage_pct}."
        if analysis_metadata and not analysis_metadata.get("anomaly_detection_available", True)
        else ""
    )
    prompt = f"""You are a sustainability analyst. Write a professional 3-paragraph executive summary (max 180 words) for a sustainability officer.

Use the recorded analysis metrics.
Analysis level: {level_label}. Dataset coverage: {coverage_pct}. Skipped modules: {skipped_mods}.

Key findings:
- Water leakage: {water_result.get('total_wasted_liters', 0)} L wasted (severity: {water_result.get('severity','').upper()}, estimated Rs. {water_result.get('estimated_cost_inr', 0)} for this period)
- Energy waste: {energy_result.get('total_wasted_kwh', 0)} kWh after-hours (severity: {energy_result.get('severity','').upper()}, estimated Rs. {energy_result.get('estimated_cost_inr', 0)} for this period)
- Combined reporting-period utility loss: estimated Rs. {total_loss}
- CO2 reduction potential: {impact_result.get('total_co2_saved_kg', 0)} kg/week ({impact_result.get('vehicle_km_equivalent', 0)} km of car travel)
- RE:GEN Score: {regen_score_result.get('before_score','N/A')}/100 now -> {regen_score_result.get('after_score','N/A')}/100 post-action
- Top priority action: {ranked[0]['recommended_action'] if ranked else 'None'}
{anomaly_note}

Paragraph 1: What is the current situation and what is at risk — be honest about data limitations if analysis level is not Level 3.
Paragraph 2: What the agents recommend doing first and why it matters.
Paragraph 3: Expected impact if all interventions are applied.

Rules:
- Use "estimated" for all financial figures
- Do not claim exact profits or guarantee outcomes
- Do not say: revolutionary, powerful AI, real-time intelligence, next-generation solution
- If analysis level is not Level 3, explicitly acknowledge findings are based on consumption estimates, not confirmed anomalies
- Do NOT infer or describe operational behavior (pipe leaks, equipment faults, after-hours usage patterns, zone-specific events) that was not present in the provided data above
- Only describe findings that appear in the Key findings section; do not add additional problems or losses
- End with one sentence stating this is a prototype decision-support system"""

    historical = impact_result.get("evidence_type") == "historical analysis"
    executive_summary, ai_used = (fallback, False) if historical else call_ai(prompt, fallback)
    if historical:
        action_plan.update(next_30_days=[], long_term=[])

    # SDG summary narrative
    sdg_items = impact_result.get("sdg_alignment", [])

    # Campus health index from regen score agent
    campus_health = regen_score_result.get("campus_health_index", {})
    building_ranking = regen_score_result.get("building_risk_ranking", [])

    silent_losses = {
        "water_leakage_liters":   water_result.get("total_wasted_liters", 0),
        "water_cost_inr":         water_result.get("estimated_cost_inr", 0),
        "energy_wasted_kwh":      energy_result.get("total_wasted_kwh", 0),
        "energy_cost_inr":        energy_result.get("estimated_cost_inr", 0),
        "co2_equivalent_kg":      impact_result.get("total_co2_saved_kg", 0),
        "total_recoverable_inr":  decision_result.get("total_potential_saving_inr", 0),
        "waste_hidden_value_inr": (
            waste_result.get("estimated_recovery", {}).get("max_inr")
            if waste_result and waste_result.get("estimated_recovery") else None
        ),
        "vehicle_km_equivalent":      impact_result.get("vehicle_km_equivalent", 0),
        "household_days_equivalent":  impact_result.get("household_days_equivalent", 0),
        "annual_projections":         impact_result.get("annual_projections", {}),
    }

    agent_traces = {
        "Water Leakage Agent":        water_result.get("reasoning_trace", []),
        "Energy Optimization Agent":  energy_result.get("reasoning_trace", []),
        "Pollution & Impact Agent":   impact_result.get("reasoning_trace", []),
        "Decision Engine Agent":      decision_result.get("reasoning_trace", []),
        "RE:GEN Score Agent":         regen_score_result.get("reasoning_trace", []),
    }
    if waste_result and waste_result.get("reasoning_trace"):
        agent_traces["Waste-to-Wealth Agent"] = waste_result["reasoning_trace"]

    return {
        "agent":              "Report Agent",
        "status":             "generated",
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "org_name":           org_name or "Demo Organisation",
        "org_type":           org_type or "University",
        "data_source":        data_source,
        "coverage":           coverage or {},
        "analysis_metadata":  analysis_metadata or {},
        "executive_summary":  executive_summary,
        "ai_enhanced":        ai_used,
        "computation_type":   "deterministic",
        "ai_layer":           ai_status(),
        "action_plan":        action_plan,
        "cross_resource_relationships": decision_result.get("cross_resource_relationships", []),
        "resource_evidence": {domain: {
            "profile": result.get("resource_profile"),
            "intensity": result.get("intensity"),
            "input_quality": result.get("input_quality"),
            "loss_assessment": result.get("loss_assessment"),
            "findings": result.get("anomaly_events", []),
        } for domain, result in (("water", water_result), ("energy", energy_result)) if result.get("status") != "skipped"},
        "silent_losses":      silent_losses,
        "sdg_alignment":      sdg_items,
        "campus_health_index":   campus_health,
        "building_risk_ranking": building_ranking,
        "agent_reasoning_traces": agent_traces,
        "regen_score": {
            "before":      regen_score_result.get("before_score"),
            "after":       regen_score_result.get("after_score"),
            "improvement": regen_score_result.get("improvement"),
            "rating":      regen_score_result.get("target_rating"),
        },
        "disclaimer":  get_disclaimer(),
        "data_notice": (
            f"Analysis based on uploaded organisational data for {org_name or 'your organisation'}."
            if org_name else get_simulated_notice()
        ),
    }
