import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import io
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

_rate_limit_enabled = os.environ.get("RATELIMIT_ENABLED", "true").lower() != "false"
limiter = Limiter(key_func=get_remote_address, enabled=_rate_limit_enabled)

from agents.waste_agent import analyze_waste, analyze_waste_batch, get_kb_materials_list
from agents.water_agent import analyze_water
from agents.energy_agent import analyze_energy
from agents.impact_agent import analyze_impact
from agents.decision_agent import generate_decisions
from agents.regen_score_agent import compute_regen_score
from agents.report_agent import generate_report
from agents.benchmark_agent import compute_benchmark
from core.guardrails import get_disclaimer, get_simulated_notice, sanitize_prompt_input
from core.database import save_run, get_history, get_run_by_id
from core.audit import build_audit_record, build_pdf
from core.alerting import send_alert
from core.openai_client import call_openai, openai_status
from core.data_processor import (
    validate_water_df, validate_energy_df, validate_fuel_df,
    build_water_df_from_manual, build_energy_df_from_manual,
    auto_detect_anomalies_water, auto_detect_anomalies_energy,
    compute_coverage, skipped_water_result, skipped_energy_result,
    detect_analysis_level,
    _parse_bytes,
)

app = FastAPI(
    title="RE:GEN AI â€” Sustainability Intelligence Platform",
    description=(
        "Multi-agent sustainability intelligence system for campuses, offices, hospitals, and industry.\n\n"
        "**Endpoints are grouped by tag:**\n"
        "- **System** â€” health check\n"
        "- **Waste** â€” Waste-to-Wealth analysis and material lookup\n"
        "- **Demo** â€” pre-loaded simulated data analysis (water, energy, dashboard, war room, action plan)\n"
        "- **Upload** â€” file validation and full multi-agent upload analysis\n"
        "- **Interpret** â€” dataset pre-analysis intelligence\n"
        "- **Data** â€” demo CSV downloads"
    ),
    version="2.0.0",
    openapi_tags=[
        {"name": "System",    "description": "Health and status checks."},
        {"name": "Waste",     "description": "Waste-to-Wealth pathway analysis."},
        {"name": "Demo",      "description": "Analysis on built-in simulated campus data."},
        {"name": "Upload",    "description": "Upload your own CSV/Excel data for analysis."},
        {"name": "Interpret", "description": "Pre-analysis data quality interpretation."},
        {"name": "Data",      "description": "Download demo CSV files for testing."},
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: restrict to known origins unless ALLOW_ALL_ORIGINS=true (local/demo override).
_DEFAULT_ORIGINS = [
    "https://frontend-two-rho-85.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]
if os.environ.get("ALLOW_ALL_ORIGINS", "").lower() == "true":
    _ALLOWED_ORIGINS = ["*"]
else:
    _env_origins = os.environ.get("ALLOWED_ORIGINS", "")
    _ALLOWED_ORIGINS = (
        [o.strip() for o in _env_origins.split(",") if o.strip()]
        if _env_origins else _DEFAULT_ORIGINS
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# â”€â”€ Pydantic models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class WasteRequest(BaseModel):
    waste_type: str = Field(..., json_schema_extra={"example": "coconut shell"})
    quantity_kg: float = Field(..., gt=0, json_schema_extra={"example": 50.0})


class ActionPlanRequest(BaseModel):
    include_waste: Optional[bool] = True
    waste_type: Optional[str] = None
    waste_quantity_kg: Optional[float] = None


class DataInterpretRequest(BaseModel):
    org_name: str = "My Organization"
    org_type: str = "University"
    water_records: int = 0
    water_buildings: list = []
    water_date_range: str = ""
    water_warnings: list = []
    energy_records: int = 0
    energy_zones: list = []
    energy_date_range: str = ""
    energy_warnings: list = []
    fuel_records: int = 0
    waste_type: str = ""
    waste_qty_kg: float = 0
    manual_water_liters: float = 0
    manual_water_period: str = ""
    manual_energy_kwh: float = 0
    manual_energy_period: str = ""
    available_datasets: list = []


# â”€â”€ Existing demo endpoints (unchanged) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.get("/health", tags=["System"], summary="Health check")
def health_check():
    """Return system status, version, and disclaimer notices."""
    return {
        "status": "online",
        "system": "RE:GEN AI Sustainability Intelligence Platform",
        "version": "2.0.0",
        "modes": ["demo", "upload"],
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }


@app.get("/system/architecture", tags=["System"], summary="System architecture disclosure")
def system_architecture():
    """
    Machine-readable disclosure of which agents are deterministic Python vs OpenAI-narrated.
    Intended for technical reviewers and judges who want to verify claims without reading source.
    """
    from core.openai_client import openai_status
    return {
        "architecture_version": "1.0",
        "computation_model": "deterministic_core_with_llm_narration",
        "summary": (
            "All quantitative analysis (anomaly detection, severity classification, cost/CO2 math, "
            "RE:GEN scoring, ROI calculations) is deterministic Python. "
            "OpenAI (gpt-4o-mini) is used exclusively to generate narrative text in 3 specific call sites."
        ),
        "deterministic_agents": [
            {"agent": "Water Leakage Agent",       "endpoint": "/analyze/water",        "openai_calls": 0},
            {"agent": "Energy Optimization Agent", "endpoint": "/analyze/energy",       "openai_calls": 0},
            {"agent": "Pollution & Impact Agent",  "endpoint": "/analyze/impact",       "openai_calls": 0},
            {"agent": "RE:GEN Score Agent",        "endpoint": "/generate/action-plan", "openai_calls": 0},
        ],
        "llm_narrated_agents": [
            {
                "agent": "Waste-to-Wealth Agent",
                "endpoint": "/analyze/waste",
                "openai_calls": 1,
                "llm_fields": ["ai_recommendation"],
                "deterministic_fields": ["hidden_value_score", "estimated_recovery", "hazard_warning", "reasoning_trace"],
            },
            {
                "agent": "Decision Engine Agent",
                "endpoint": "/generate/action-plan",
                "openai_calls": 1,
                "llm_fields": ["top_action_explanation"],
                "deterministic_fields": ["ranked_actions", "priority_score", "roi", "urgency", "feasibility"],
            },
            {
                "agent": "Report Agent",
                "endpoint": "/generate/action-plan",
                "openai_calls": 1,
                "llm_fields": ["executive_summary"],
                "deterministic_fields": ["silent_losses", "campus_health_index", "building_risk_ranking", "action_plan", "sdg_alignment"],
            },
        ],
        "openai_status": openai_status(),
    }


@app.get("/analyze/waste/materials", tags=["Waste"], summary="List waste materials")
def get_waste_materials():
    """
    Return the full list of materials in the Waste-to-Wealth knowledge base.
    Used by the frontend to populate dropdowns dynamically.
    """
    return {
        "materials": get_kb_materials_list(),
        "count": len(get_kb_materials_list()),
    }


@app.post("/analyze/waste", tags=["Waste"], summary="Analyze a waste material")
@limiter.limit("10/minute")
def analyze_waste_endpoint(request: Request, body: WasteRequest):
    """Analyze a single waste material and return recovery pathways, estimated revenue, and guardrail notices."""
    result = analyze_waste(body.waste_type, body.quantity_kg)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/analyze/water", tags=["Demo"], summary="Water leakage analysis (demo data)")
def analyze_water_endpoint():
    """Run the Water Leakage Agent on the built-in simulated campus water dataset."""
    return analyze_water()


@app.get("/analyze/energy", tags=["Demo"], summary="Energy waste analysis (demo data)")
def analyze_energy_endpoint():
    """Run the Energy Optimization Agent on the built-in simulated campus energy dataset."""
    return analyze_energy()


@app.get("/dashboard/summary", tags=["Demo"], summary="Full dashboard summary (demo data)")
def dashboard_summary():
    water  = analyze_water()
    energy = analyze_energy()

    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], 0)
    decision = generate_decisions(water, energy)
    regen    = compute_regen_score(water, energy, impact, decision)
    report   = generate_report(water, energy, impact, decision, regen)

    return {
        "regen_score":      regen,
        "silent_losses":    report["silent_losses"],
        "water_summary": {
            "total_wasted_liters": water["total_wasted_liters"],
            "severity":            water["severity"],
            "estimated_cost_inr":  water["estimated_cost_inr"],
            "anomaly_events":      len(water["anomaly_events"]),
        },
        "energy_summary": {
            "total_wasted_kwh":   energy["total_wasted_kwh"],
            "severity":           energy["severity"],
            "estimated_cost_inr": energy["estimated_cost_inr"],
            "anomaly_events":     len(energy["anomaly_events"]),
        },
        "impact_summary": {
            "total_co2_saved_kg":   impact["total_co2_saved_kg"],
            "trees_equivalent":     impact["trees_equivalent"],
            "sustainability_score": impact["sustainability_score"],
            "sustainability_rating": impact["sustainability_rating"],
        },
        "top_actions": decision["ranked_actions"][:3],
        "disclaimer":  get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }


@app.get("/agent-war-room", tags=["Demo"], summary="Agent War Room status (demo data)")
@limiter.limit("10/minute")
def agent_war_room(request: Request):
    water  = analyze_water()
    energy = analyze_energy()
    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], 0)
    decision = generate_decisions(water, energy)
    regen    = compute_regen_score(water, energy, impact, decision)
    report   = generate_report(water, energy, impact, decision, regen)

    return {
        "war_room": [
            {
                "agent":          "Waste-to-Wealth Agent",
                "icon":           "â™»ï¸",
                "status":         "standby",
                "finding":        "Submit a waste type using the Waste Analyzer panel to activate this agent.",
                "confidence":     None,
                "recommendation": "Use the Waste-to-Wealth Analyzer to identify recovery pathways.",
                "severity":       "info",
            },
            {
                "agent":          "Water Leakage Agent",
                "icon":           "ðŸ’§",
                "status":         "active",
                "finding":        f"Detected {len(water['anomaly_events'])} leakage event(s). "
                                  f"{water['total_wasted_liters']}L wasted. Severity: {water['severity'].upper()}.",
                "confidence":     water["confidence"],
                "recommendation": water["recommendations"][0] if water["recommendations"] else "Monitor water usage.",
                "severity":       water["severity"],
                "key_metric":     f"{water['total_wasted_liters']} L lost",
            },
            {
                "agent":          "Energy Optimization Agent",
                "icon":           "âš¡",
                "status":         "active",
                "finding":        f"Detected {len(energy['anomaly_events'])} after-hours waste event(s). "
                                  f"{energy['total_wasted_kwh']} kWh wasted. Severity: {energy['severity'].upper()}.",
                "confidence":     energy["confidence"],
                "recommendation": energy["recommendations"][0] if energy["recommendations"] else "Monitor energy usage.",
                "severity":       energy["severity"],
                "key_metric":     f"{energy['total_wasted_kwh']} kWh wasted",
            },
            {
                "agent":          "Pollution & Impact Agent",
                "icon":           "ðŸŒ¿",
                "status":         "active",
                "finding":        f"Total CO2 savings potential: {impact['total_co2_saved_kg']} kg. "
                                  f"Equivalent to {impact['trees_equivalent']} trees saved.",
                "confidence":     impact["confidence"],
                "recommendation": f"Sustainability rating: {impact['sustainability_rating']} ({impact['sustainability_score']}/100).",
                "severity":       "low",
                "key_metric":     f"{impact['total_co2_saved_kg']} kg CO2",
            },
            {
                "agent":          "Decision Engine Agent",
                "icon":           "ðŸ§ ",
                "status":         "active",
                "finding":        f"Ranked {decision['total_actions']} priority actions. "
                                  f"Top priority: {decision['ranked_actions'][0]['domain'] if decision['ranked_actions'] else 'N/A'}.",
                "confidence":     decision["confidence"],
                "recommendation": decision["ranked_actions"][0]["recommended_action"] if decision["ranked_actions"] else "No actions ranked.",
                "severity":       "medium",
                "key_metric":     f"â‚¹{decision['total_potential_saving_inr']} savings potential",
            },
            {
                "agent":          "RE:GEN Score Agent",
                "icon":           "ðŸ†",
                "status":         "active",
                "finding":        f"Current score: {regen['before_score']}/100 ({regen['current_rating']}). "
                                  f"Post-action target: {regen['after_score']}/100 ({regen['target_rating']}).",
                "confidence":     regen["confidence"],
                "recommendation": f"Implementing all actions will improve score by +{regen['improvement']} points.",
                "severity":       "high" if regen["before_score"] < 40 else "medium",
                "key_metric":     f"{regen['before_score']} â†’ {regen['after_score']}",
            },
            {
                "agent":          "Report Agent",
                "icon":           "ðŸ“‹",
                "status":         "active",
                "finding":        f"Executive report generated. {len(report['action_plan']['immediate'])} immediate actions, "
                                  f"{len(report['action_plan']['next_7_days'])} 7-day actions.",
                "confidence":     0.95,
                "recommendation": "Download full sustainability action plan for campus administration.",
                "severity":       "low",
                "key_metric":     f"Generated {report['generated_at'][:10]}",
            },
        ],
        "disclaimer": get_disclaimer(),
    }


@app.post("/generate/action-plan", tags=["Demo"], summary="Generate action plan (demo data)")
@limiter.limit("10/minute")
def generate_action_plan(request: Request, body: ActionPlanRequest):
    """Run all agents on demo data and return the full sustainability action plan and report."""
    water  = analyze_water()
    energy = analyze_energy()

    waste = None
    if body.include_waste and body.waste_type and body.waste_quantity_kg:
        waste = analyze_waste(body.waste_type, body.waste_quantity_kg)

    waste_value = 0
    if waste and waste.get("estimated_recovery"):
        waste_value = waste["estimated_recovery"].get("max_inr", 0)

    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], waste_value)
    decision = generate_decisions(water, energy, waste)
    regen    = compute_regen_score(water, energy, impact, decision, waste)
    report   = generate_report(water, energy, impact, decision, regen, waste)

    return {
        "water": water, "energy": energy, "waste": waste,
        "impact": impact, "decision": decision,
        "regen_score": regen, "report": report,
    }


# â”€â”€ Upload: validate a single file â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.post("/upload/validate", tags=["Upload"], summary="Validate an uploaded file")
@limiter.limit("10/minute")
async def validate_upload(
    request: Request,
    file: UploadFile = File(...),
    dataset_type: str = Form(...),   # "water" | "energy" | "fuel"
):
    """
    Validate an uploaded CSV or Excel file.
    Returns detected columns, record count, date range, and any errors/warnings.
    """
    allowed = {"water", "energy", "fuel", "waste", "occupancy"}
    if dataset_type not in allowed:
        raise HTTPException(status_code=400, detail=f"dataset_type must be one of: {allowed}")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:  # 20 MB guard
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    try:
        raw_df = _parse_bytes(content, file.filename or "upload.csv")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}")

    if dataset_type == "water":
        _, info = validate_water_df(raw_df)
    elif dataset_type == "energy":
        _, info = validate_energy_df(raw_df)
    elif dataset_type == "fuel":
        _, info = validate_fuel_df(raw_df)
    else:
        info = {
            "dataset": dataset_type,
            "valid": True,
            "record_count": len(raw_df),
            "columns_detected": list(raw_df.columns),
            "warnings": ["Generic validation only â€” no schema enforced for this dataset type."],
            "errors": [],
        }

    info["filename"]      = file.filename
    info["file_size_kb"]  = round(len(content) / 1024, 1)
    info["raw_columns"]   = list(raw_df.columns)
    return info


# â”€â”€ Data intelligence interpreter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.post("/interpret/datasets", tags=["Interpret"], summary="Interpret uploaded dataset metadata")
@limiter.limit("10/minute")
def interpret_datasets(request: Request, body: DataInterpretRequest):
    """
    Produce an intelligent pre-analysis summary of the uploaded datasets.
    Deterministic facts are always returned. OpenAI adds a quality note when available.
    """
    facts = []
    all_warnings = []

    if body.water_records > 0:
        facts.append(f"{body.water_records:,} Water Records")
        if body.water_buildings:
            b = len(body.water_buildings)
            facts.append(f"{b} Water Location{'s' if b > 1 else ''} Detected")
        if body.water_date_range:
            facts.append(f"Water Span: {body.water_date_range}")
        all_warnings.extend(body.water_warnings)
    elif body.manual_water_liters > 0:
        period = body.manual_water_period or "weekly"
        facts.append(f"Water: Manual Entry ({body.manual_water_liters:,.0f} L/{period})")
        facts.append("Synthetic Diurnal Profile Generated")

    if body.energy_records > 0:
        facts.append(f"{body.energy_records:,} Energy Records")
        if body.energy_zones:
            z = len(body.energy_zones)
            facts.append(f"{z} Energy Zone{'s' if z > 1 else ''} Detected")
        if body.energy_date_range:
            facts.append(f"Energy Span: {body.energy_date_range}")
        all_warnings.extend(body.energy_warnings)
    elif body.manual_energy_kwh > 0:
        period = body.manual_energy_period or "weekly"
        facts.append(f"Energy: Manual Entry ({body.manual_energy_kwh:,.0f} kWh/{period})")
        facts.append("Synthetic Load Profile Generated")

    if body.fuel_records > 0:
        facts.append(f"{body.fuel_records:,} Fuel Records")

    if body.waste_type:
        facts.append(f"Waste: {body.waste_type} ({body.waste_qty_kg} kg)")

    if all_warnings:
        facts.append(f"{len(all_warnings)} Column Warning{'s' if len(all_warnings) > 1 else ''} Handled")

    if not facts:
        facts.append("No datasets detected â€” manual entries will be used")

    n = len(body.available_datasets)
    facts.append(f"Carbon: Automatic (derived from {n} dataset{'s' if n != 1 else ''})")

    # Fallback quality note (deterministic)
    ds_list = ", ".join(body.available_datasets) if body.available_datasets else "no primary datasets"
    fallback = (
        f"{n} dataset{'s' if n != 1 else ''} validated for {body.org_name}. "
        f"Analysis will run on: {ds_list}. "
        "All data quality issues have been handled automatically."
    )

    # AI quality note
    safe_org_name = sanitize_prompt_input(body.org_name)
    safe_org_type = sanitize_prompt_input(body.org_type)
    facts_str = "\n".join(f"- {f}" for f in facts)
    prompt = f"""You are a data quality analyst reviewing uploaded sustainability data.
Organisation: {safe_org_name} ({safe_org_type})
Datasets available: {', '.join(body.available_datasets) or 'none'}
Data facts:
{facts_str}
Column warnings: {'; '.join(all_warnings) if all_warnings else 'None'}

Write exactly 2 sentences:
1. What the data covers and its quality.
2. What the analysis will be most confident about given this data.

Rules:
- Be specific about the organisation type
- Do not invent numbers not listed above
- Do not use: revolutionary, powerful AI, next-generation
- No bullet points â€” prose only"""

    quality_note, ai_used = call_openai(prompt, fallback)

    return {
        "facts": facts,
        "quality_note": quality_note,
        "ai_enhanced": ai_used,
        "openai_status": openai_status(),
        "datasets_count": n,
    }


# â”€â”€ Upload: run full analysis on uploaded files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.post("/analyze/upload", tags=["Upload"], summary="Run full analysis on uploaded files")
@limiter.limit("10/minute")
async def analyze_upload(
    request: Request,
    org_name:           str  = Form("My Organization"),
    org_type:           str  = Form("University"),
    water_file:         Optional[UploadFile] = File(None),
    energy_file:        Optional[UploadFile] = File(None),
    fuel_file:          Optional[UploadFile] = File(None),
    # Manual entry fallbacks
    manual_water_liters:  Optional[float] = Form(None),
    manual_water_period:  Optional[str]   = Form("weekly"),
    manual_energy_kwh:    Optional[float] = Form(None),
    manual_energy_period: Optional[str]   = Form("weekly"),
    manual_fuel_type:     Optional[str]   = Form(None),
    manual_fuel_liters:   Optional[float] = Form(None),
    # Waste â€” multi-stream JSON array {"type":...,"quantity_kg":...,"unit":...}
    waste_items:          Optional[str]   = Form(None),
    # Legacy single-item fallback (backward compat)
    waste_type:           Optional[str]   = Form(None),
    waste_quantity_kg:    Optional[float] = Form(None),
    # Occupancy — optional; enables peer benchmarking when provided
    occupancy_count:      Optional[int]   = Form(None),
):
    """
    Run multi-agent analysis on uploaded organizational data.
    Any combination of datasets is accepted â€” missing datasets are skipped.
    Carbon is always derived automatically from available resource data.
    """
    available_datasets = []

    # â”€â”€ Water â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    water_result       = None
    water_level_info   = None

    if water_file and water_file.filename:
        content = await water_file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Water file exceeds 20 MB limit.")
        try:
            raw_df = _parse_bytes(content, water_file.filename)
            water_df, winfo = validate_water_df(raw_df)
            if not winfo["valid"]:
                raise HTTPException(status_code=422, detail=f"Water file errors: {winfo['errors']}")
            water_level_info = detect_analysis_level(water_df, is_manual=False)
            water_result = analyze_water(df=water_df, is_uploaded=True, analysis_level_info=water_level_info)
            available_datasets.append("water")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Water file could not be processed: {exc}")

    elif manual_water_liters and manual_water_liters > 0:
        water_level_info = detect_analysis_level(None, is_manual=True)
        water_df = build_water_df_from_manual(manual_water_liters, period=manual_water_period or "weekly")
        # Do NOT run auto_detect_anomalies â€” manual entry has no real temporal signal
        water_result = analyze_water(df=water_df, is_uploaded=True, analysis_level_info=water_level_info)
        water_result["data_source"] = f"Manual entry ({manual_water_period or 'weekly'})"
        available_datasets.append("water")

    # â”€â”€ Energy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    energy_result      = None
    energy_level_info  = None

    if energy_file and energy_file.filename:
        content = await energy_file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Energy file exceeds 20 MB limit.")
        try:
            raw_df = _parse_bytes(content, energy_file.filename)
            energy_df, einfo = validate_energy_df(raw_df)
            if not einfo["valid"]:
                raise HTTPException(status_code=422, detail=f"Energy file errors: {einfo['errors']}")
            energy_level_info = detect_analysis_level(energy_df, is_manual=False)
            energy_result = analyze_energy(df=energy_df, is_uploaded=True, analysis_level_info=energy_level_info)
            available_datasets.append("energy")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Energy file could not be processed: {exc}")

    elif manual_energy_kwh and manual_energy_kwh > 0:
        energy_level_info = detect_analysis_level(None, is_manual=True)
        energy_df = build_energy_df_from_manual(manual_energy_kwh, period=manual_energy_period or "weekly")
        # Do NOT run auto_detect_anomalies â€” manual entry has no real temporal signal
        energy_result = analyze_energy(df=energy_df, is_uploaded=True, analysis_level_info=energy_level_info)
        energy_result["data_source"] = f"Manual entry ({manual_energy_period or 'weekly'})"
        available_datasets.append("energy")

    # â”€â”€ Fuel (carbon + full summary) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fuel_co2_kg  = 0.0
    fuel_summary = None
    if fuel_file and fuel_file.filename:
        content = await fuel_file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Fuel file exceeds 20 MB limit.")
        try:
            raw_df = _parse_bytes(content, fuel_file.filename)
            fuel_summary_raw, finfo = validate_fuel_df(raw_df)
            if finfo["valid"]:
                fuel_co2_kg  = fuel_summary_raw.get("total_co2_kg", 0)
                fuel_summary = fuel_summary_raw
                available_datasets.append("fuel")
        except Exception:
            pass  # non-critical â€” continue without fuel

    elif manual_fuel_liters and manual_fuel_type:
        from core.data_processor import FUEL_EMISSION_FACTORS
        factor = FUEL_EMISSION_FACTORS.get(manual_fuel_type.lower(), 2.5)
        fuel_co2_kg = manual_fuel_liters * factor
        fuel_summary = {
            "source":          "manual_entry",
            "fuel_type":        manual_fuel_type,
            "total_liters":     manual_fuel_liters,
            "total_co2_kg":     round(fuel_co2_kg, 2),
            "emission_factor":  factor,
            "breakdown":        {manual_fuel_type: {"liters": manual_fuel_liters, "co2_kg": round(fuel_co2_kg, 2)}},
        }
        available_datasets.append("fuel")

    # â”€â”€ Waste â€” multi-stream batch or legacy single-item â”€
    waste_result = None
    # Try batch path first (new frontend sends waste_items JSON)
    if waste_items:
        try:
            items_list = json.loads(waste_items)
            if isinstance(items_list, list) and items_list:
                waste_result = analyze_waste_batch(items_list)
                if waste_result.get("status") == "analyzed":
                    available_datasets.append("waste")
        except Exception:
            pass  # malformed JSON â€” fall through to legacy path
    # Legacy single-item fallback
    if waste_result is None and waste_type and waste_quantity_kg and waste_quantity_kg > 0:
        single = analyze_waste(waste_type, waste_quantity_kg)
        if single.get("status") == "analyzed":
            # Wrap as minimal batch-compatible shape
            waste_result = {
                "agent":                  "Waste-to-Wealth Agent",
                "status":                 "analyzed",
                "total_items":            1,
                "analyzed_items":         1,
                "total_kg":               waste_quantity_kg,
                "total_recovery_min_inr": single.get("estimated_recovery", {}).get("min_inr", 0),
                "total_recovery_max_inr": single.get("estimated_recovery", {}).get("max_inr", 0),
                "hazardous_count":        1 if single.get("hazard_warning") else 0,
                "circularity_score":      single.get("hidden_value_score", 0),
                "composition":            {"organic_pct": 0, "plastic_pct": 0, "metal_pct": 0, "hazardous_pct": 0, "other_pct": 100},
                "top_opportunity":        single.get("waste_type"),
                "top_opportunity_value_max_inr": single.get("estimated_recovery", {}).get("max_inr", 0),
                "top_opportunity_pathway": single.get("recommended_pathway"),
                "compliance_warnings":    [f"{single['waste_type']} requires CPCB-authorised handling."] if single.get("hazard_warning") else [],
                "items":                  [single],
                "confidence":             0.88,
                "disclaimer":             single.get("disclaimer", ""),
            }
            available_datasets.append("waste")

    # â”€â”€ Build skipped stubs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    effective_water  = water_result  or skipped_water_result()
    effective_energy = energy_result or skipped_energy_result()

    # â”€â”€ Carbon is always automatic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    water_liters = effective_water.get("total_wasted_liters", 0)
    energy_kwh   = effective_energy.get("total_wasted_kwh", 0)
    waste_value  = 0
    if waste_result and waste_result.get("status") == "analyzed":
        waste_value = waste_result.get("total_recovery_max_inr", 0)
        # Compat: expose single estimated_recovery for agents that expect it
        if not waste_result.get("estimated_recovery") and waste_result.get("total_recovery_max_inr"):
            waste_result["estimated_recovery"] = {
                "max_inr": waste_result["total_recovery_max_inr"],
                "min_inr": waste_result["total_recovery_min_inr"],
            }

    # â”€â”€ Run downstream agents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    impact   = analyze_impact(water_liters, energy_kwh, waste_value, fuel_co2_kg=fuel_co2_kg)
    decision = generate_decisions(effective_water, effective_energy, waste_result)
    regen    = compute_regen_score(effective_water, effective_energy, impact, decision, waste_result)

    coverage = compute_coverage(available_datasets)

    data_source = f"Uploaded data â€” {org_name} ({org_type})"

    # â”€â”€ Analysis metadata â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    all_levels = [
        lv for lv in [water_level_info, energy_level_info]
        if lv is not None
    ]
    overall_level = max((lv["level"] for lv in all_levels), default=1)
    overall_code  = next((lv["code"] for lv in all_levels if lv["level"] == overall_level), "level1")
    overall_label = next((lv["label"] for lv in all_levels if lv["level"] == overall_level), "Basic Sustainability Assessment")
    anomaly_available = any(lv.get("anomaly_detection_available", False) for lv in all_levels)

    skipped_modules = []
    if not anomaly_available:
        skipped_modules.append({
            "module": "Anomaly Detection",
            "reason": "Hourly time-series data required (â‰¥ 3 days, â‰¥ 12 hour slots per day). "
                      "Provide smart-meter exports or IoT logs to enable this module.",
        })
        skipped_modules.append({
            "module": "Leak Detection",
            "reason": "Derived from anomaly detection â€” unavailable at current data resolution.",
        })
        skipped_modules.append({
            "module": "Predictive Maintenance",
            "reason": "Requires temporal pattern analysis across multiple days at hourly resolution.",
        })

    confidence_pct = coverage["analysis_confidence_pct"]
    if not anomaly_available:
        confidence_pct = min(confidence_pct, 55 if overall_level == 1 else 72)

    analysis_metadata = {
        "overall_level":            overall_level,
        "overall_code":             overall_code,
        "overall_label":            overall_label,
        "anomaly_detection_available": anomaly_available,
        "confidence_pct":           confidence_pct,
        "confidence_reasoning": (
            f"Overall analysis level: {overall_label}. "
            f"{len(available_datasets)} dataset(s) provided: {', '.join(available_datasets) or 'none'}. "
            + (
                "Anomaly detection is active â€” full AI analysis available."
                if anomaly_available else
                "Anomaly detection is unavailable at the current data resolution. "
                "Confidence is limited to consumption estimates and benchmarks. "
                "Provide hourly operational logs to unlock advanced modules."
            )
        ),
        "skipped_modules":      skipped_modules,
        "data_sufficiency_summary": (
            f"{len(available_datasets)} of 5 possible datasets provided. "
            f"Analysis confidence: {confidence_pct}%. "
            + (
                f"Advanced AI modules ({', '.join(m['module'] for m in skipped_modules)}) "
                "were not executed â€” see skipped_modules for required data."
                if skipped_modules else
                "All primary analysis modules executed successfully."
            )
        ),
    }

    report = generate_report(
        effective_water, effective_energy, impact, decision, regen,
        waste_result,
        org_name=org_name,
        org_type=org_type,
        data_source=data_source,
        coverage=coverage,
        analysis_metadata=analysis_metadata,
    )

    # â”€â”€ Build war-room agent list (upload-aware) â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _agent_status(result: dict) -> str:
        return "skipped" if result.get("status") == "skipped" else "active"

    def _water_finding(r: dict) -> str:
        if r.get("status") == "skipped":
            return r.get("skip_reason", "No water data provided.")
        if not r.get("anomaly_detection_available", True):
            return (
                f"Consumption estimated: {r.get('total_consumption_liters', 0):,.0f} L. "
                f"Analysis level: {r.get('analysis_level_label', 'Basic')}. "
                "Leak detection unavailable â€” provide hourly logs to enable it."
            )
        return (
            f"{r.get('total_wasted_liters', 0)} L hidden loss detected. "
            f"Severity: {r.get('severity', 'none').upper()}. "
            f"{len(r.get('anomaly_events', []))} event(s) flagged."
        )

    def _energy_finding(r: dict) -> str:
        if r.get("status") == "skipped":
            return r.get("skip_reason", "No energy data provided.")
        if not r.get("anomaly_detection_available", True):
            return (
                f"Consumption estimated: {r.get('total_consumption_kwh', 0):,.1f} kWh. "
                f"Analysis level: {r.get('analysis_level_label', 'Basic')}. "
                "After-hours waste analysis unavailable â€” provide hourly logs to enable it."
            )
        return (
            f"{r.get('total_wasted_kwh', 0)} kWh after-hours waste detected. "
            f"Severity: {r.get('severity', 'none').upper()}. "
            f"{len(r.get('anomaly_events', []))} event(s) flagged."
        )

    war_room_agents = [
        {
            "agent":          "Water Leakage Agent",
            "icon":           "ðŸ’§",
            "status":         _agent_status(effective_water),
            "skip_reason":    effective_water.get("skip_reason"),
            "finding":        _water_finding(effective_water),
            "reasoning":      effective_water.get("war_room_reasoning", ""),
            "impact":         effective_water.get("war_room_impact", ""),
            "analysis_level": effective_water.get("analysis_level", "level1"),
            "anomaly_detection_available": effective_water.get("anomaly_detection_available", False),
            "anomaly_detection_reason": effective_water.get("anomaly_detection_reason"),
            "confidence":     effective_water.get("confidence", 0),
            "recommendation": (effective_water.get("recommendations") or ["No data available."])[0],
            "severity":       effective_water.get("severity", "none"),
            "key_metric":     (
                f"{effective_water.get('total_wasted_liters', 0)} L wasted"
                if effective_water.get("anomaly_detection_available")
                else f"{effective_water.get('total_consumption_liters', 0):,.0f} L consumed"
            ),
        },
        {
            "agent":          "Energy Optimization Agent",
            "icon":           "âš¡",
            "status":         _agent_status(effective_energy),
            "skip_reason":    effective_energy.get("skip_reason"),
            "finding":        _energy_finding(effective_energy),
            "reasoning":      effective_energy.get("war_room_reasoning", ""),
            "impact":         effective_energy.get("war_room_impact", ""),
            "analysis_level": effective_energy.get("analysis_level", "level1"),
            "anomaly_detection_available": effective_energy.get("anomaly_detection_available", False),
            "anomaly_detection_reason": effective_energy.get("anomaly_detection_reason"),
            "confidence":     effective_energy.get("confidence", 0),
            "recommendation": (effective_energy.get("recommendations") or ["No data available."])[0],
            "severity":       effective_energy.get("severity", "none"),
            "key_metric":     (
                f"{effective_energy.get('total_wasted_kwh', 0)} kWh wasted"
                if effective_energy.get("anomaly_detection_available")
                else f"{effective_energy.get('total_consumption_kwh', 0):,.1f} kWh consumed"
            ),
        },
        {
            "agent":       "Waste-to-Wealth Agent",
            "icon":        "â™»ï¸",
            "status":      "active" if waste_result and waste_result.get("status") == "analyzed" else "standby",
            "finding":     (
                f"{waste_result.get('analyzed_items', waste_result.get('total_items', 1))} waste stream(s) analysed. "
                f"Total: {waste_result.get('total_kg', 0):.1f} kg. "
                f"Top opportunity: {waste_result.get('top_opportunity', 'N/A')}."
                if waste_result and waste_result.get("status") == "analyzed"
                else "No waste inventory submitted."
            ),
            "reasoning":   (
                f"Batch analysis of {waste_result.get('total_items', 0)} stream(s) ({waste_result.get('total_kg', 0):.1f} kg total). "
                f"Top recovery pathway: {waste_result.get('top_opportunity_pathway', 'N/A')} "
                f"for {waste_result.get('top_opportunity', 'N/A')}."
                if waste_result and waste_result.get("status") == "analyzed"
                else "No waste material submitted â€” agent in standby."
            ),
            "impact":      (
                f"Estimated recovery value: Rs. {waste_result.get('total_recovery_max_inr', 0):,.0f}. "
                f"Circularity score: {waste_result.get('circularity_score', 0)}/100."
                if waste_result and waste_result.get("status") == "analyzed"
                else "Submit waste inventory to compute recovery value."
            ),
            "confidence":  waste_result.get("confidence") if waste_result else None,
            "recommendation": (
                next(
                    (r.get("ai_recommendation") for r in (waste_result.get("items") or [])
                     if r.get("status") == "analyzed"
                     and r.get("waste_type") == waste_result.get("top_opportunity")
                     and r.get("ai_recommendation")),
                    (
                        f"Segregate {waste_result.get('top_opportunity', 'waste streams')} and route via "
                        f"{(waste_result.get('top_opportunity_pathway') or 'authorized_recycler').replace('_', ' ')} "
                        f"for an estimated recovery of up to â‚¹{waste_result.get('top_opportunity_value_max_inr', 0):,.0f}. "
                        + (f"Route {waste_result.get('hazardous_count', 0)} hazardous stream(s) to CPCB-authorised handlers immediately."
                           if waste_result.get("hazardous_count", 0) > 0 else
                           f"Engage a local kabadiwala or certified recycler this week.")
                    )
                )
                if waste_result and waste_result.get("status") == "analyzed"
                else "No waste inventory submitted â€” add waste streams in the Upload Center to activate recovery analysis."
            ),
            "severity":    "high" if (waste_result and waste_result.get("hazardous_count", 0) > 0) else "medium" if waste_result and waste_result.get("status") == "analyzed" else "info",
        },
        {
            "agent":      "Pollution & Impact Agent",
            "icon":       "ðŸŒ¿",
            "status":     "active",
            "finding":    f"CO2 reduction potential: {impact['total_co2_saved_kg']} kg. Sustainability rating: {impact['sustainability_rating']}.",
            "reasoning":  (
                f"CO2 derived from: electricity ({effective_energy.get('co2_equivalent_kg',0)} kg), "
                f"water treatment ({effective_water.get('co2_equivalent_kg',0)} kg), "
                f"fuel combustion ({round(fuel_co2_kg,2)} kg). "
                f"India grid emission factor 0.82 kg/kWh applied."
            ),
            "impact":     f"Sustainability score: {impact['sustainability_score']}/100 ({impact['sustainability_rating']}). Trees equivalent: {impact['trees_equivalent']}.",
            "confidence": impact["confidence"],
            "recommendation": f"Sustainability rating: {impact['sustainability_rating']} ({impact['sustainability_score']}/100).",
            "severity":   "low",
        },
        {
            "agent":      "Decision Engine Agent",
            "icon":       "ðŸ§ ",
            "status":     "active",
            "finding":    f"Ranked {decision['total_actions']} priority actions. Total savings potential: Rs. {decision['total_potential_saving_inr']:,}.",
            "reasoning":  (
                f"Actions ranked by urgency Ã— estimated impact Ã— implementation cost. "
                f"Top domain: {decision['ranked_actions'][0]['domain'] if decision['ranked_actions'] else 'N/A'}."
            ),
            "impact":     f"Implementing all actions: Rs. {decision['total_potential_saving_inr']:,} potential savings.",
            "confidence": decision["confidence"],
            "recommendation": decision["ranked_actions"][0]["recommended_action"] if decision["ranked_actions"] else "No actions ranked.",
            "severity":   "medium",
        },
        {
            "agent":      "RE:GEN Score Agent",
            "icon":       "ðŸ†",
            "status":     "active",
            "finding":    f"Score: {regen['before_score']}/100 ({regen['current_rating']}) â†’ {regen['after_score']}/100 post-action.",
            "reasoning":  (
                f"Score computed across water, energy, carbon, and waste dimensions. "
                f"Data coverage: {coverage['data_coverage_pct']}%. "
                f"Analysis confidence: {confidence_pct}%."
            ),
            "impact":     f"+{regen['improvement']} point improvement achievable with full intervention stack.",
            "confidence": regen["confidence"],
            "recommendation": f"Implementing all recommendations will raise score by +{regen['improvement']} points to {regen['after_score']}/100.",
            "severity":   "high" if regen["before_score"] < 40 else "medium",
        },
        {
            "agent":      "Report Agent",
            "icon":       "ðŸ“‹",
            "status":     "active",
            "finding":    f"Report generated for {org_name}. Coverage: {coverage['data_coverage_pct']}%. Analysis level: {overall_label}.",
            "reasoning":  (
                f"Report synthesises findings from {len(available_datasets)} dataset(s). "
                f"Analysis confidence: {confidence_pct}%. "
                + (f"{len(skipped_modules)} module(s) skipped due to data resolution." if skipped_modules else "All modules executed.")
            ),
            "impact":     f"Executive summary and action plan generated. {len(skipped_modules)} advanced module(s) require higher-resolution data.",
            "confidence": 0.95,
            "recommendation": "Download your custom sustainability report.",
            "severity":   "low",
        },
    ]

    # Infer days of data from whichever agent processed the most rows
    _days = (
        effective_water.get("days_of_data")
        or effective_energy.get("days_of_data")
        or 7
    )
    benchmark_result = compute_benchmark(
        org_type=org_type,
        occupancy_count=occupancy_count,
        total_consumption_liters=effective_water.get("total_consumption_liters", 0),
        total_consumption_kwh=effective_energy.get("total_consumption_kwh", 0),
        days_of_data=_days,
    )

    response = {
        "mode":              "upload",
        "org_name":          org_name,
        "org_type":          org_type,
        "coverage":          coverage,
        "analysis_metadata": analysis_metadata,
        "water":             effective_water,
        "energy":            effective_energy,
        "waste":             waste_result,
        "fuel_co2_kg":       fuel_co2_kg,
        "fuel_summary":      fuel_summary,
        "impact":            impact,
        "decision":          decision,
        "regen_score":       regen,
        "report":            report,
        "war_room":          war_room_agents,
        "benchmark":         benchmark_result,
        "disclaimer":        get_disclaimer(),
    }

    try:
        analysis_id = save_run(
            org_name=org_name,
            org_type=org_type,
            coverage_pct=coverage.get("data_coverage_pct", 0),
            confidence_pct=confidence_pct,
            regen_before=regen.get("before_score", 0),
            regen_after=regen.get("after_score", 0),
            wasted_liters=effective_water.get("total_wasted_liters", 0),
            wasted_kwh=effective_energy.get("total_wasted_kwh", 0),
            co2_kg=impact.get("total_co2_saved_kg", 0),
            payload_dict={
                "water":      effective_water,
                "energy":     effective_energy,
                "impact":     impact,
                "decision":   decision,
                "regen_score": regen,
            },
        )
        response["analysis_id"] = analysis_id
    except Exception:
        pass  # persistence is non-critical — never break the analysis response

    try:
        alert_sent = send_alert(effective_water, effective_energy, org_name, response.get("analysis_id"))
        response["alert_sent"] = alert_sent
    except Exception:
        response["alert_sent"] = False

    return response


# â”€â”€ Demo data download â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.get("/history/{org_name}", tags=["History"], summary="Fetch analysis run history for an org")
def analysis_history(org_name: str, limit: int = 20):
    """Return the last N analysis runs for the given org_name, newest first."""
    return {"org_name": org_name, "runs": get_history(org_name, limit=min(limit, 100))}


@app.get("/report/{analysis_id}/audit-record", tags=["Audit"], summary="JSON audit record for an analysis run")
def get_audit_record(analysis_id: int):
    run = get_run_by_id(analysis_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Analysis run {analysis_id} not found")
    return build_audit_record(run)


@app.get("/report/{analysis_id}/audit-record.pdf", tags=["Audit"], summary="PDF audit record for an analysis run")
def get_audit_record_pdf(analysis_id: int):
    run = get_run_by_id(analysis_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Analysis run {analysis_id} not found")
    record = build_audit_record(run)
    pdf_bytes = build_pdf(record)
    filename = f"regen-audit-{analysis_id}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/demo-data/{dataset_type}", tags=["Data"], summary="Download a demo dataset CSV")
def download_demo_data(dataset_type: str):
    """
    Download the bundled demo CSV for a given dataset type.
    Supported: water, energy, waste_kb (JSON), fuel, occupancy.
    """
    file_map = {
        "water":     ("water_usage.csv",        "text/csv"),
        "energy":    ("energy_usage.csv",        "text/csv"),
        "fuel":      ("fuel_usage.csv",          "text/csv"),
        "occupancy": ("occupancy.csv",           "text/csv"),
    }
    if dataset_type not in file_map:
        raise HTTPException(status_code=404, detail=f"No demo data for '{dataset_type}'. Available: {list(file_map)}")

    filename, media = file_map[dataset_type]
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Demo file '{filename}' not found on server.")

    with open(filepath, "rb") as f:
        content = f.read()

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
