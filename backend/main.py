import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from agents.waste_agent import analyze_waste
from agents.water_agent import analyze_water
from agents.energy_agent import analyze_energy
from agents.impact_agent import analyze_impact
from agents.decision_agent import generate_decisions
from agents.regen_score_agent import compute_regen_score
from agents.report_agent import generate_report
from core.guardrails import get_disclaimer, get_simulated_notice

app = FastAPI(
    title="RE:GEN AI — Sustainability Command Center",
    description="Autonomous multi-agent sustainability intelligence system for smart campuses.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WasteRequest(BaseModel):
    waste_type: str = Field(..., example="coconut shell", description="Type of waste material")
    quantity_kg: float = Field(..., gt=0, example=50.0, description="Quantity in kilograms")


class ActionPlanRequest(BaseModel):
    include_waste: Optional[bool] = True
    waste_type: Optional[str] = None
    waste_quantity_kg: Optional[float] = None


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "system": "RE:GEN AI Sustainability Command Center",
        "version": "1.0.0",
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }


@app.post("/analyze/waste")
def analyze_waste_endpoint(request: WasteRequest):
    result = analyze_waste(request.waste_type, request.quantity_kg)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/analyze/water")
def analyze_water_endpoint():
    return analyze_water()


@app.get("/analyze/energy")
def analyze_energy_endpoint():
    return analyze_energy()


@app.get("/dashboard/summary")
def dashboard_summary():
    water = analyze_water()
    energy = analyze_energy()

    impact = analyze_impact(
        water_saved_liters=water["total_wasted_liters"],
        energy_saved_kwh=energy["total_wasted_kwh"],
        waste_value_inr=0,
    )

    decision = generate_decisions(water, energy)
    regen = compute_regen_score(water, energy, impact, decision)
    report = generate_report(water, energy, impact, decision, regen)

    return {
        "regen_score": regen,
        "silent_losses": report["silent_losses"],
        "water_summary": {
            "total_wasted_liters": water["total_wasted_liters"],
            "severity": water["severity"],
            "estimated_cost_inr": water["estimated_cost_inr"],
            "anomaly_events": len(water["anomaly_events"]),
        },
        "energy_summary": {
            "total_wasted_kwh": energy["total_wasted_kwh"],
            "severity": energy["severity"],
            "estimated_cost_inr": energy["estimated_cost_inr"],
            "anomaly_events": len(energy["anomaly_events"]),
        },
        "impact_summary": {
            "total_co2_saved_kg": impact["total_co2_saved_kg"],
            "trees_equivalent": impact["trees_equivalent"],
            "sustainability_score": impact["sustainability_score"],
            "sustainability_rating": impact["sustainability_rating"],
        },
        "top_actions": decision["ranked_actions"][:3],
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }


@app.get("/agent-war-room")
def agent_war_room():
    water = analyze_water()
    energy = analyze_energy()

    impact = analyze_impact(
        water_saved_liters=water["total_wasted_liters"],
        energy_saved_kwh=energy["total_wasted_kwh"],
        waste_value_inr=0,
    )

    decision = generate_decisions(water, energy)
    regen = compute_regen_score(water, energy, impact, decision)
    report = generate_report(water, energy, impact, decision, regen)

    return {
        "war_room": [
            {
                "agent": "Waste-to-Wealth Agent",
                "icon": "♻️",
                "status": "standby",
                "finding": "Submit a waste type using the Waste Analyzer panel to activate this agent.",
                "confidence": None,
                "recommendation": "Use the Waste-to-Wealth Analyzer to identify recovery pathways.",
                "severity": "info",
            },
            {
                "agent": "Water Leakage Agent",
                "icon": "💧",
                "status": "active",
                "finding": f"Detected {len(water['anomaly_events'])} leakage event(s). "
                           f"{water['total_wasted_liters']}L wasted. Severity: {water['severity'].upper()}.",
                "confidence": water["confidence"],
                "recommendation": water["recommendations"][0] if water["recommendations"] else "Monitor water usage.",
                "severity": water["severity"],
                "key_metric": f"{water['total_wasted_liters']} L lost",
            },
            {
                "agent": "Energy Optimization Agent",
                "icon": "⚡",
                "status": "active",
                "finding": f"Detected {len(energy['anomaly_events'])} after-hours waste event(s). "
                           f"{energy['total_wasted_kwh']} kWh wasted. Severity: {energy['severity'].upper()}.",
                "confidence": energy["confidence"],
                "recommendation": energy["recommendations"][0] if energy["recommendations"] else "Monitor energy usage.",
                "severity": energy["severity"],
                "key_metric": f"{energy['total_wasted_kwh']} kWh wasted",
            },
            {
                "agent": "Pollution & Impact Agent",
                "icon": "🌿",
                "status": "active",
                "finding": f"Total CO2 savings potential: {impact['total_co2_saved_kg']} kg. "
                           f"Equivalent to {impact['trees_equivalent']} trees saved.",
                "confidence": impact["confidence"],
                "recommendation": f"Sustainability rating: {impact['sustainability_rating']} ({impact['sustainability_score']}/100).",
                "severity": "low",
                "key_metric": f"{impact['total_co2_saved_kg']} kg CO2",
            },
            {
                "agent": "Decision Engine Agent",
                "icon": "🧠",
                "status": "active",
                "finding": f"Ranked {decision['total_actions']} priority actions. "
                           f"Top priority: {decision['ranked_actions'][0]['domain'] if decision['ranked_actions'] else 'N/A'}.",
                "confidence": decision["confidence"],
                "recommendation": decision["ranked_actions"][0]["recommended_action"] if decision["ranked_actions"] else "No actions ranked.",
                "severity": "medium",
                "key_metric": f"₹{decision['total_potential_saving_inr']} savings potential",
            },
            {
                "agent": "RE:GEN Score Agent",
                "icon": "🏆",
                "status": "active",
                "finding": f"Current score: {regen['before_score']}/100 ({regen['current_rating']}). "
                           f"Post-action target: {regen['after_score']}/100 ({regen['target_rating']}).",
                "confidence": regen["confidence"],
                "recommendation": f"Implementing all actions will improve score by +{regen['improvement']} points.",
                "severity": "high" if regen["before_score"] < 40 else "medium",
                "key_metric": f"{regen['before_score']} → {regen['after_score']}",
            },
            {
                "agent": "Report Agent",
                "icon": "📋",
                "status": "active",
                "finding": f"Executive report generated. {len(report['action_plan']['immediate'])} immediate actions, "
                           f"{len(report['action_plan']['next_7_days'])} 7-day actions.",
                "confidence": 0.95,
                "recommendation": "Download full sustainability action plan for campus administration.",
                "severity": "low",
                "key_metric": f"Generated {report['generated_at'][:10]}",
            },
        ],
        "disclaimer": get_disclaimer(),
    }


@app.post("/generate/action-plan")
def generate_action_plan(request: ActionPlanRequest):
    water = analyze_water()
    energy = analyze_energy()

    waste = None
    if request.include_waste and request.waste_type and request.waste_quantity_kg:
        waste = analyze_waste(request.waste_type, request.waste_quantity_kg)

    waste_value = 0
    if waste and waste.get("estimated_recovery"):
        waste_value = waste["estimated_recovery"].get("max_inr", 0)

    impact = analyze_impact(
        water_saved_liters=water["total_wasted_liters"],
        energy_saved_kwh=energy["total_wasted_kwh"],
        waste_value_inr=waste_value,
    )

    decision = generate_decisions(water, energy, waste)
    regen = compute_regen_score(water, energy, impact, decision)
    report = generate_report(water, energy, impact, decision, regen, waste)

    return {
        "water": water,
        "energy": energy,
        "waste": waste,
        "impact": impact,
        "decision": decision,
        "regen_score": regen,
        "report": report,
    }
