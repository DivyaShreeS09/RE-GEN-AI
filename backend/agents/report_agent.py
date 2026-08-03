from datetime import datetime
from core.guardrails import get_disclaimer, get_simulated_notice, sanitize_prompt_input
from core.openai_client import call_openai, openai_status


def _fallback_summary(water, energy, impact, regen, ranked,
                      data_source: str = "Simulated sensor logs, January 15–21, 2024",
                      org_name: str = None) -> str:
    total_loss = round(
        water.get("estimated_cost_inr", 0) + energy.get("estimated_cost_inr", 0), 2
    )
    org_label = f"{org_name} " if org_name else ""
    water_skip = water.get("status") == "skipped"
    energy_skip = energy.get("status") == "skipped"
    water_line = (
        f"Water leakage analysis: {water.get('total_wasted_liters', 0)} L estimated wasted "
        f"(Rs. {water.get('estimated_cost_inr', 0)}/week)."
        if not water_skip else "Water data not provided — water analysis skipped."
    )
    energy_line = (
        f"After-hours energy waste: {energy.get('total_wasted_kwh', 0)} kWh "
        f"(Rs. {energy.get('estimated_cost_inr', 0)}/week)."
        if not energy_skip else "Energy data not provided — energy analysis skipped."
    )
    return (
        f"RE:GEN AI {org_label}Sustainability Analysis — {datetime.now().strftime('%B %d, %Y')}\n\n"
        f"Data source: {data_source}.\n"
        f"{water_line} {energy_line} "
        f"Combined estimated weekly utility loss: Rs. {total_loss}.\n\n"
        f"Top recommended intervention: "
        f"{ranked[0]['recommended_action'] if ranked else 'No critical actions detected'}. "
        f"Recommended timeline: {ranked[0].get('timeline', 'immediately') if ranked else 'as soon as possible'}.\n\n"
        f"Implementing all agent-recommended actions is projected to raise the RE:GEN Score from "
        f"{regen.get('before_score', 'N/A')}/100 to {regen.get('after_score', 'N/A')}/100, "
        f"with an estimated {impact.get('total_co2_saved_kg', 0)} kg CO2 reduction per week — equivalent to "
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
    immediate = [a for a in ranked if a.get("timeline") == "Immediate"]
    week      = [a for a in ranked if "7" in str(a.get("timeline", ""))]

    action_plan = {
        "immediate": [
            {
                "action":               a["recommended_action"],
                "domain":               a["domain"],
                "estimated_saving_inr": a["cost_saving_inr"],
                "priority_score":       a["priority_score"],
                "roi":                  a.get("roi"),
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
        water_result.get("estimated_cost_inr", 0) + energy_result.get("estimated_cost_inr", 0), 2
    )
    level_label  = analysis_metadata.get("overall_label", "Advanced AI Analysis") if analysis_metadata else "Advanced AI Analysis"
    conf_pct     = analysis_metadata.get("confidence_pct", 89) if analysis_metadata else 89
    skipped_mods = ", ".join(m["module"] for m in (analysis_metadata or {}).get("skipped_modules", [])) or "None"
    anomaly_note = (
        f"Note: Anomaly detection was unavailable at this data resolution (analysis level: {level_label}). "
        f"Figures reflect consumption estimates only, not confirmed leakage or waste events. "
        f"Confidence: {conf_pct}%."
        if analysis_metadata and not analysis_metadata.get("anomaly_detection_available", True)
        else ""
    )
    safe_data_source = sanitize_prompt_input(data_source, max_length=300)
    prompt = f"""You are a sustainability analyst. Write a professional 3-paragraph executive summary (max 180 words) for a sustainability officer.

Scan source: {safe_data_source}.
Analysis level: {level_label}. Confidence: {conf_pct}%. Skipped modules: {skipped_mods}.

Key findings:
- Water leakage: {water_result.get('total_wasted_liters', 0)} L wasted (severity: {water_result.get('severity','').upper()}, estimated Rs. {water_result.get('estimated_cost_inr', 0)}/week)
- Energy waste: {energy_result.get('total_wasted_kwh', 0)} kWh after-hours (severity: {energy_result.get('severity','').upper()}, estimated Rs. {energy_result.get('estimated_cost_inr', 0)}/week)
- Combined weekly utility loss: estimated Rs. {total_loss}
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
- Reference the data source accurately: {data_source}
- End with one sentence stating this is a prototype decision-support system"""

    executive_summary, ai_used = call_openai(prompt, fallback)

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
            waste_result.get("estimated_recovery", {}).get("max_inr", 0)
            if waste_result and waste_result.get("estimated_recovery") else 0
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
        "generated_at":       datetime.now().isoformat(),
        "org_name":           org_name or "Demo Organisation",
        "org_type":           org_type or "University",
        "data_source":        data_source,
        "coverage":           coverage or {},
        "analysis_metadata":  analysis_metadata or {},
        "executive_summary":  executive_summary,
        "ai_enhanced":        ai_used,
        "ai_layer":           openai_status(),
        "action_plan":        action_plan,
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
