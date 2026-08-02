import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import io
import json

from agents.waste_agent import analyze_waste, analyze_waste_batch, get_kb_materials_list
from agents.water_agent import analyze_water
from agents.energy_agent import analyze_energy
from agents.impact_agent import analyze_impact
from agents.decision_agent import generate_decisions
from agents.regen_score_agent import compute_regen_score
from agents.report_agent import generate_report
from core.guardrails import get_disclaimer, get_simulated_notice
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
    title="RE:GEN AI — Sustainability Intelligence Platform",
    description="Multi-agent sustainability intelligence system for campuses, offices, hospitals, and industry.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ── Pydantic models ─────────────────────────────────────────────────────────

class WasteRequest(BaseModel):
    waste_type: str = Field(..., example="coconut shell")
    quantity_kg: float = Field(..., gt=0, example=50.0)


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


# ── Existing demo endpoints (unchanged) ─────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "system": "RE:GEN AI Sustainability Intelligence Platform",
        "version": "2.0.0",
        "modes": ["demo", "upload"],
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }


@app.get("/analyze/waste/materials")
def get_waste_materials():
    """
    Return the full list of materials in the Waste-to-Wealth knowledge base.
    Used by the frontend to populate dropdowns dynamically.
    """
    return {
        "materials": get_kb_materials_list(),
        "count": len(get_kb_materials_list()),
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


@app.get("/agent-war-room")
def agent_war_room():
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
                "icon":           "♻️",
                "status":         "standby",
                "finding":        "Submit a waste type using the Waste Analyzer panel to activate this agent.",
                "confidence":     None,
                "recommendation": "Use the Waste-to-Wealth Analyzer to identify recovery pathways.",
                "severity":       "info",
            },
            {
                "agent":          "Water Leakage Agent",
                "icon":           "💧",
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
                "icon":           "⚡",
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
                "icon":           "🌿",
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
                "icon":           "🧠",
                "status":         "active",
                "finding":        f"Ranked {decision['total_actions']} priority actions. "
                                  f"Top priority: {decision['ranked_actions'][0]['domain'] if decision['ranked_actions'] else 'N/A'}.",
                "confidence":     decision["confidence"],
                "recommendation": decision["ranked_actions"][0]["recommended_action"] if decision["ranked_actions"] else "No actions ranked.",
                "severity":       "medium",
                "key_metric":     f"₹{decision['total_potential_saving_inr']} savings potential",
            },
            {
                "agent":          "RE:GEN Score Agent",
                "icon":           "🏆",
                "status":         "active",
                "finding":        f"Current score: {regen['before_score']}/100 ({regen['current_rating']}). "
                                  f"Post-action target: {regen['after_score']}/100 ({regen['target_rating']}).",
                "confidence":     regen["confidence"],
                "recommendation": f"Implementing all actions will improve score by +{regen['improvement']} points.",
                "severity":       "high" if regen["before_score"] < 40 else "medium",
                "key_metric":     f"{regen['before_score']} → {regen['after_score']}",
            },
            {
                "agent":          "Report Agent",
                "icon":           "📋",
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


@app.post("/generate/action-plan")
def generate_action_plan(request: ActionPlanRequest):
    water  = analyze_water()
    energy = analyze_energy()

    waste = None
    if request.include_waste and request.waste_type and request.waste_quantity_kg:
        waste = analyze_waste(request.waste_type, request.waste_quantity_kg)

    waste_value = 0
    if waste and waste.get("estimated_recovery"):
        waste_value = waste["estimated_recovery"].get("max_inr", 0)

    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], waste_value)
    decision = generate_decisions(water, energy, waste)
    regen    = compute_regen_score(water, energy, impact, decision)
    report   = generate_report(water, energy, impact, decision, regen, waste)

    return {
        "water": water, "energy": energy, "waste": waste,
        "impact": impact, "decision": decision,
        "regen_score": regen, "report": report,
    }


# ── Upload: validate a single file ─────────────────────────────────────────

@app.post("/upload/validate")
async def validate_upload(
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
            "warnings": ["Generic validation only — no schema enforced for this dataset type."],
            "errors": [],
        }

    info["filename"]      = file.filename
    info["file_size_kb"]  = round(len(content) / 1024, 1)
    info["raw_columns"]   = list(raw_df.columns)
    return info


# ── Data intelligence interpreter ──────────────────────────────────────────

@app.post("/interpret/datasets")
def interpret_datasets(request: DataInterpretRequest):
    """
    Produce an intelligent pre-analysis summary of the uploaded datasets.
    Deterministic facts are always returned. OpenAI adds a quality note when available.
    """
    facts = []
    all_warnings = []

    if request.water_records > 0:
        facts.append(f"{request.water_records:,} Water Records")
        if request.water_buildings:
            b = len(request.water_buildings)
            facts.append(f"{b} Water Location{'s' if b > 1 else ''} Detected")
        if request.water_date_range:
            facts.append(f"Water Span: {request.water_date_range}")
        all_warnings.extend(request.water_warnings)
    elif request.manual_water_liters > 0:
        period = request.manual_water_period or "weekly"
        facts.append(f"Water: Manual Entry ({request.manual_water_liters:,.0f} L/{period})")
        facts.append("Synthetic Diurnal Profile Generated")

    if request.energy_records > 0:
        facts.append(f"{request.energy_records:,} Energy Records")
        if request.energy_zones:
            z = len(request.energy_zones)
            facts.append(f"{z} Energy Zone{'s' if z > 1 else ''} Detected")
        if request.energy_date_range:
            facts.append(f"Energy Span: {request.energy_date_range}")
        all_warnings.extend(request.energy_warnings)
    elif request.manual_energy_kwh > 0:
        period = request.manual_energy_period or "weekly"
        facts.append(f"Energy: Manual Entry ({request.manual_energy_kwh:,.0f} kWh/{period})")
        facts.append("Synthetic Load Profile Generated")

    if request.fuel_records > 0:
        facts.append(f"{request.fuel_records:,} Fuel Records")

    if request.waste_type:
        facts.append(f"Waste: {request.waste_type} ({request.waste_qty_kg} kg)")

    if all_warnings:
        facts.append(f"{len(all_warnings)} Column Warning{'s' if len(all_warnings) > 1 else ''} Handled")

    if not facts:
        facts.append("No datasets detected — manual entries will be used")

    n = len(request.available_datasets)
    facts.append(f"Carbon: Automatic (derived from {n} dataset{'s' if n != 1 else ''})")

    # Fallback quality note (deterministic)
    ds_list = ", ".join(request.available_datasets) if request.available_datasets else "no primary datasets"
    fallback = (
        f"{n} dataset{'s' if n != 1 else ''} validated for {request.org_name}. "
        f"Analysis will run on: {ds_list}. "
        "All data quality issues have been handled automatically."
    )

    # AI quality note
    facts_str = "\n".join(f"- {f}" for f in facts)
    prompt = f"""You are a data quality analyst reviewing uploaded sustainability data.
Organisation: {request.org_name} ({request.org_type})
Datasets available: {', '.join(request.available_datasets) or 'none'}
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
- No bullet points — prose only"""

    quality_note, ai_used = call_openai(prompt, fallback)

    return {
        "facts": facts,
        "quality_note": quality_note,
        "ai_enhanced": ai_used,
        "openai_status": openai_status(),
        "datasets_count": n,
    }


# ── Upload: run full analysis on uploaded files ─────────────────────────────

@app.post("/analyze/upload")
async def analyze_upload(
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
    # Waste — multi-stream JSON array {"type":...,"quantity_kg":...,"unit":...}
    waste_items:          Optional[str]   = Form(None),
    # Legacy single-item fallback (backward compat)
    waste_type:           Optional[str]   = Form(None),
    waste_quantity_kg:    Optional[float] = Form(None),
):
    """
    Run multi-agent analysis on uploaded organizational data.
    Any combination of datasets is accepted — missing datasets are skipped.
    Carbon is always derived automatically from available resource data.
    """
    available_datasets = []

    # ── Water ──────────────────────────────────────────
    water_result       = None
    water_level_info   = None

    if water_file and water_file.filename:
        content = await water_file.read()
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
        # Do NOT run auto_detect_anomalies — manual entry has no real temporal signal
        water_result = analyze_water(df=water_df, is_uploaded=True, analysis_level_info=water_level_info)
        water_result["data_source"] = f"Manual entry ({manual_water_period or 'weekly'})"
        available_datasets.append("water")

    # ── Energy ─────────────────────────────────────────
    energy_result      = None
    energy_level_info  = None

    if energy_file and energy_file.filename:
        content = await energy_file.read()
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
        # Do NOT run auto_detect_anomalies — manual entry has no real temporal signal
        energy_result = analyze_energy(df=energy_df, is_uploaded=True, analysis_level_info=energy_level_info)
        energy_result["data_source"] = f"Manual entry ({manual_energy_period or 'weekly'})"
        available_datasets.append("energy")

    # ── Fuel (carbon + full summary) ────────────────────
    fuel_co2_kg  = 0.0
    fuel_summary = None
    if fuel_file and fuel_file.filename:
        content = await fuel_file.read()
        try:
            raw_df = _parse_bytes(content, fuel_file.filename)
            fuel_summary_raw, finfo = validate_fuel_df(raw_df)
            if finfo["valid"]:
                fuel_co2_kg  = fuel_summary_raw.get("total_co2_kg", 0)
                fuel_summary = fuel_summary_raw
                available_datasets.append("fuel")
        except Exception:
            pass  # non-critical — continue without fuel

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

    # ── Waste — multi-stream batch or legacy single-item ─
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
            pass  # malformed JSON — fall through to legacy path
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

    # ── Build skipped stubs ─────────────────────────────
    effective_water  = water_result  or skipped_water_result()
    effective_energy = energy_result or skipped_energy_result()

    # ── Carbon is always automatic ──────────────────────
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

    # ── Run downstream agents ──────────────────────────
    impact   = analyze_impact(water_liters, energy_kwh, waste_value, fuel_co2_kg=fuel_co2_kg)
    decision = generate_decisions(effective_water, effective_energy, waste_result)
    regen    = compute_regen_score(effective_water, effective_energy, impact, decision)

    coverage = compute_coverage(available_datasets)

    data_source = f"Uploaded data — {org_name} ({org_type})"

    # ── Analysis metadata ───────────────────────────────
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
            "reason": "Hourly time-series data required (≥ 3 days, ≥ 12 hour slots per day). "
                      "Provide smart-meter exports or IoT logs to enable this module.",
        })
        skipped_modules.append({
            "module": "Leak Detection",
            "reason": "Derived from anomaly detection — unavailable at current data resolution.",
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
                "Anomaly detection is active — full AI analysis available."
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
                "were not executed — see skipped_modules for required data."
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

    # ── Build war-room agent list (upload-aware) ─────────
    def _agent_status(result: dict) -> str:
        return "skipped" if result.get("status") == "skipped" else "active"

    def _water_finding(r: dict) -> str:
        if r.get("status") == "skipped":
            return r.get("skip_reason", "No water data provided.")
        if not r.get("anomaly_detection_available", True):
            return (
                f"Consumption estimated: {r.get('total_consumption_liters', 0):,.0f} L. "
                f"Analysis level: {r.get('analysis_level_label', 'Basic')}. "
                "Leak detection unavailable — provide hourly logs to enable it."
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
                "After-hours waste analysis unavailable — provide hourly logs to enable it."
            )
        return (
            f"{r.get('total_wasted_kwh', 0)} kWh after-hours waste detected. "
            f"Severity: {r.get('severity', 'none').upper()}. "
            f"{len(r.get('anomaly_events', []))} event(s) flagged."
        )

    war_room_agents = [
        {
            "agent":          "Water Leakage Agent",
            "icon":           "💧",
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
            "icon":           "⚡",
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
            "icon":        "♻️",
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
                else "No waste material submitted — agent in standby."
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
                        f"for an estimated recovery of up to ₹{waste_result.get('top_opportunity_value_max_inr', 0):,.0f}. "
                        + (f"Route {waste_result.get('hazardous_count', 0)} hazardous stream(s) to CPCB-authorised handlers immediately."
                           if waste_result.get("hazardous_count", 0) > 0 else
                           f"Engage a local kabadiwala or certified recycler this week.")
                    )
                )
                if waste_result and waste_result.get("status") == "analyzed"
                else "No waste inventory submitted — add waste streams in the Upload Center to activate recovery analysis."
            ),
            "severity":    "high" if (waste_result and waste_result.get("hazardous_count", 0) > 0) else "medium" if waste_result and waste_result.get("status") == "analyzed" else "info",
        },
        {
            "agent":      "Pollution & Impact Agent",
            "icon":       "🌿",
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
            "icon":       "🧠",
            "status":     "active",
            "finding":    f"Ranked {decision['total_actions']} priority actions. Total savings potential: Rs. {decision['total_potential_saving_inr']:,}.",
            "reasoning":  (
                f"Actions ranked by urgency × estimated impact × implementation cost. "
                f"Top domain: {decision['ranked_actions'][0]['domain'] if decision['ranked_actions'] else 'N/A'}."
            ),
            "impact":     f"Implementing all actions: Rs. {decision['total_potential_saving_inr']:,} potential savings.",
            "confidence": decision["confidence"],
            "recommendation": decision["ranked_actions"][0]["recommended_action"] if decision["ranked_actions"] else "No actions ranked.",
            "severity":   "medium",
        },
        {
            "agent":      "RE:GEN Score Agent",
            "icon":       "🏆",
            "status":     "active",
            "finding":    f"Score: {regen['before_score']}/100 ({regen['current_rating']}) → {regen['after_score']}/100 post-action.",
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
            "icon":       "📋",
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

    return {
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
        "disclaimer":        get_disclaimer(),
    }


# ── Demo data download ──────────────────────────────────────────────────────

@app.get("/demo-data/{dataset_type}")
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
