from datetime import datetime
from core.guardrails import get_disclaimer, get_simulated_notice
from core.gemini_client import call_gemini, gemini_status


def _fallback_summary(water, energy, impact, regen, ranked) -> str:
    total_loss = round(
        water.get("estimated_cost_inr", 0) + energy.get("estimated_cost_inr", 0), 2
    )
    return (
        f"RE:GEN AI Campus Sustainability Scan — {datetime.now().strftime('%B %d, %Y')}\n\n"
        f"Simulated sensor logs (Jan 15-21, 2024) reveal significant hidden resource loss. "
        f"Water leakage accounts for {water.get('total_wasted_liters', 0)} L wasted per week "
        f"(estimated Rs. {water.get('estimated_cost_inr', 0)} loss), while after-hours energy waste "
        f"totals {energy.get('total_wasted_kwh', 0)} kWh (estimated Rs. {energy.get('estimated_cost_inr', 0)} loss). "
        f"Combined weekly utility loss is estimated at Rs. {total_loss}.\n\n"
        f"The Decision Engine has ranked the top intervention as: "
        f"{ranked[0]['recommended_action'] if ranked else 'No critical actions detected'}. "
        f"This should be executed {ranked[0].get('timeline', 'immediately') if ranked else 'as a priority'}.\n\n"
        f"Implementing all agent-recommended actions is projected to raise the RE:GEN Score from "
        f"{regen.get('before_score', 'N/A')}/100 to {regen.get('after_score', 'N/A')}/100, "
        f"saving an estimated {impact.get('total_co2_saved_kg', 0)} kg CO2 per week — equivalent to "
        f"{impact.get('trees_equivalent', 0)} trees or {impact.get('vehicle_km_equivalent', 0)} km "
        f"of car travel offset.\n\n"
        "Note: RE:GEN AI is a prototype decision-support system. All data is simulated. "
        "This is not professional regulatory, financial, or engineering advice."
    )


def generate_report(
    water_result:      dict,
    energy_result:     dict,
    impact_result:     dict,
    decision_result:   dict,
    regen_score_result: dict,
    waste_result:      dict = None,
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
            {"action": "Conduct comprehensive energy audit across all campus buildings.", "domain": "Energy"},
            {"action": "Install automated water sub-meters at Block-B, Lab Block, and canteen.", "domain": "Water"},
            {"action": "Set up centralised waste segregation stations with colour-coded bins.", "domain": "Waste"},
        ],
        "long_term": [
            {"action": "Deploy IoT-based smart meters for real-time water and energy monitoring.", "domain": "Infrastructure"},
            {"action": "Establish campus biogas plant to convert wet waste to cooking gas.", "domain": "Waste"},
            {"action": "Partner with certified e-waste and hazardous waste recyclers under EPR agreement.", "domain": "Compliance"},
            {"action": "Target RE:GEN Score > 80 (Excellent) within 12 months.", "domain": "Sustainability"},
        ],
    }

    # --- Gemini executive summary ---
    fallback = _fallback_summary(water_result, energy_result, impact_result, regen_score_result, ranked)
    total_loss = round(
        water_result.get("estimated_cost_inr", 0) + energy_result.get("estimated_cost_inr", 0), 2
    )
    prompt = f"""You are a campus sustainability analyst. Write a professional 3-paragraph executive summary (max 160 words) for a university sustainability officer.

Scan source: Simulated campus sensor logs, January 15-21, 2024.

Key findings:
- Water leakage: {water_result.get('total_wasted_liters', 0)} L wasted (severity: {water_result.get('severity','').upper()}, estimated Rs. {water_result.get('estimated_cost_inr', 0)}/week)
- Energy waste: {energy_result.get('total_wasted_kwh', 0)} kWh after-hours (severity: {energy_result.get('severity','').upper()}, estimated Rs. {energy_result.get('estimated_cost_inr', 0)}/week)
- Combined weekly utility loss: estimated Rs. {total_loss}
- CO2 reduction potential: {impact_result.get('total_co2_saved_kg', 0)} kg/week ({impact_result.get('vehicle_km_equivalent', 0)} km of car travel)
- RE:GEN Score: {regen_score_result.get('before_score','N/A')}/100 now -> {regen_score_result.get('after_score','N/A')}/100 post-action
- Top priority action: {ranked[0]['recommended_action'] if ranked else 'None'}

Paragraph 1: What is the current situation and what is at risk.
Paragraph 2: What the agents recommend doing first and why it matters.
Paragraph 3: Expected impact if all interventions are applied.

Rules:
- Use "estimated" for all financial figures
- Say "simulated campus sensor logs" not "real-time data"
- Do not claim exact profits
- Do not say: revolutionary, powerful AI, real-time intelligence, next-generation solution
- End with one sentence stating this is a prototype decision-support system"""

    executive_summary, gemini_used = call_gemini(prompt, fallback)

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
        "executive_summary":  executive_summary,
        "gemini_enhanced":    gemini_used,
        "ai_layer":           gemini_status(),
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
        "data_notice": get_simulated_notice(),
    }
