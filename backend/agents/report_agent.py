from datetime import datetime
from core.guardrails import get_disclaimer, get_simulated_notice


def generate_report(
    water_result: dict,
    energy_result: dict,
    impact_result: dict,
    decision_result: dict,
    regen_score_result: dict,
    waste_result: dict = None,
) -> dict:
    ranked = decision_result.get("ranked_actions", [])

    immediate = [a for a in ranked if a.get("timeline") == "Immediate"]
    week = [a for a in ranked if "7" in str(a.get("timeline", ""))]
    month_30 = []
    long_term = []

    action_plan = {
        "immediate": [
            {
                "action": a["recommended_action"],
                "domain": a["domain"],
                "estimated_saving_inr": a["cost_saving_inr"],
                "priority_score": a["priority_score"],
            }
            for a in immediate
        ],
        "next_7_days": [
            {
                "action": a["recommended_action"],
                "domain": a["domain"],
                "estimated_saving_inr": a["cost_saving_inr"],
                "priority_score": a["priority_score"],
            }
            for a in week
        ],
        "next_30_days": [
            {"action": "Conduct comprehensive energy audit across all campus buildings.", "domain": "Energy"},
            {"action": "Install automated water sub-meters at Block-B, Lab Block, and canteen.", "domain": "Water"},
            {"action": "Set up centralized waste segregation stations with color-coded bins.", "domain": "Waste"},
        ],
        "long_term": [
            {"action": "Deploy IoT-based smart meters for real-time water and energy monitoring.", "domain": "Infrastructure"},
            {"action": "Establish campus biogas plant to convert wet waste to cooking gas.", "domain": "Waste"},
            {"action": "Partner with certified e-waste and hazardous waste recyclers under EPR agreement.", "domain": "Compliance"},
            {"action": "Target RE:GEN Score > 80 (Excellent) within 12 months.", "domain": "Sustainability"},
        ],
    }

    executive_summary = (
        f"RE:GEN AI Campus Sustainability Scan — {datetime.now().strftime('%B %d, %Y')}\n\n"
        f"Current RE:GEN Score: {regen_score_result.get('before_score', 'N/A')}/100 "
        f"({regen_score_result.get('current_rating', 'N/A')})\n"
        f"Projected Score (post-action): {regen_score_result.get('after_score', 'N/A')}/100 "
        f"({regen_score_result.get('target_rating', 'N/A')})\n\n"
        f"Silent Losses Detected:\n"
        f"  • Water leakage: {water_result.get('total_wasted_liters', 0)} liters wasted "
        f"(₹{water_result.get('estimated_cost_inr', 0)} estimated loss)\n"
        f"  • Energy waste: {energy_result.get('total_wasted_kwh', 0)} kWh after-hours "
        f"(₹{energy_result.get('estimated_cost_inr', 0)} estimated loss)\n"
        f"  • Total CO2 savings potential: {impact_result.get('total_co2_saved_kg', 0)} kg\n\n"
        f"Priority action: {ranked[0]['recommended_action'] if ranked else 'No critical actions detected.'}\n"
        f"Total estimated savings potential: ₹{decision_result.get('total_potential_saving_inr', 0)}\n"
    )

    agent_traces = {
        "Water Leakage Agent": water_result.get("reasoning_trace", []),
        "Energy Optimization Agent": energy_result.get("reasoning_trace", []),
        "Pollution & Impact Agent": impact_result.get("reasoning_trace", []),
        "Decision Engine Agent": decision_result.get("reasoning_trace", []),
        "RE:GEN Score Agent": regen_score_result.get("reasoning_trace", []),
    }
    if waste_result and waste_result.get("reasoning_trace"):
        agent_traces["Waste-to-Wealth Agent"] = waste_result["reasoning_trace"]

    silent_losses = {
        "water_leakage_liters": water_result.get("total_wasted_liters", 0),
        "water_cost_inr": water_result.get("estimated_cost_inr", 0),
        "energy_wasted_kwh": energy_result.get("total_wasted_kwh", 0),
        "energy_cost_inr": energy_result.get("estimated_cost_inr", 0),
        "co2_equivalent_kg": impact_result.get("total_co2_saved_kg", 0),
        "total_recoverable_inr": decision_result.get("total_potential_saving_inr", 0),
        "waste_hidden_value_inr": (
            waste_result.get("estimated_recovery", {}).get("max_inr", 0)
            if waste_result and waste_result.get("estimated_recovery")
            else 0
        ),
    }

    return {
        "agent": "Report Agent",
        "status": "generated",
        "generated_at": datetime.now().isoformat(),
        "executive_summary": executive_summary,
        "action_plan": action_plan,
        "silent_losses": silent_losses,
        "agent_reasoning_traces": agent_traces,
        "regen_score": {
            "before": regen_score_result.get("before_score"),
            "after": regen_score_result.get("after_score"),
            "improvement": regen_score_result.get("improvement"),
            "rating": regen_score_result.get("target_rating"),
        },
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }
