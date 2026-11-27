import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.auth import Member, require_member
from fastapi import Depends, Query, FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional
import io
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

_rate_limit_enabled = os.environ.get("RATELIMIT_ENABLED", "true").lower() != "false"
limiter = Limiter(key_func=get_remote_address, config_filename=os.devnull if os.path.isfile(".env") else None, default_limits=["120/minute"])
# SlowAPI returns the raw environment string for RATELIMIT_ENABLED.
limiter.enabled = _rate_limit_enabled or os.getenv("REGEN_ENV") == "production"

from agents.waste_agent import analyze_waste, analyze_waste_batch, get_kb_materials_list
from agents.water_agent import analyze_water, WATER_COST_PER_LITER
from agents.energy_agent import analyze_energy, ELECTRICITY_COST_PER_KWH
from agents.impact_agent import analyze_impact
from agents.decision_agent import generate_decisions
from agents.regen_score_agent import compute_regen_score
from agents.report_agent import generate_report
from agents.benchmark_agent import compute_benchmark
from core.guardrails import get_disclaimer, get_simulated_notice
from core.database import save_run, get_history, get_run_by_id, log_access, delete_run
from core.audit import build_audit_record, build_pdf
from core.alerting import send_alert
from core.device_control import execute_action
from core.ai_client import ai_status
from core.data_processor import (
    validate_water_df, validate_energy_df, validate_fuel_df,
    build_water_df_from_manual, build_energy_df_from_manual,
    compute_coverage, skipped_water_result, skipped_energy_result,
    detect_analysis_level,
    _parse_bytes, PERIOD_DAYS,
)

app = FastAPI(
    title="RE:GEN AI — Sustainability Intelligence Platform",
    description=(
        "Multi-agent sustainability intelligence system for campuses, offices, hospitals, and industry.\n\n"
        "**Endpoints are grouped by tag:**\n"
        "- **System** — health check\n"
        "- **Waste** — Waste-to-Wealth analysis and material lookup\n"
        "- **Demo** — pre-loaded simulated data analysis (water, energy, dashboard, war room, action plan)\n"
        "- **Upload** — file validation and full multi-agent upload analysis\n"
        "- **Interpret** — dataset pre-analysis intelligence\n"
        "- **Data** — demo CSV downloads"
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

from core.recovery import router as recovery_router, upload_events
from core.telemetry import router as telemetry_router
from core.schema import require_schema, upgrade

if os.getenv("REGEN_ENV") == "production":
    from core.auth import validate_production_identity
    validate_production_identity()
    require_schema()
else:
    upgrade()
app.include_router(recovery_router)
app.include_router(telemetry_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173" if os.getenv("REGEN_ENV") != "production" else ""
).split(",") if origin.strip() and origin.strip() != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-AI-Consent", "X-Alert-Consent", "Idempotency-Key"],
)

from sqlalchemy.exc import OperationalError


@app.exception_handler(OperationalError)
async def database_error(request, exc):
    code = getattr(exc.orig, "sqlite_errorname", "") or getattr(exc.orig, "sqlstate", "")
    if code in ("SQLITE_BUSY", "SQLITE_BUSY_SNAPSHOT", "SQLITE_LOCKED", "40001", "40P01"):
        return JSONResponse({"detail": "Concurrent update. Refresh and retry."}, status_code=409)
    return JSONResponse({"detail": "Storage temporarily unavailable."}, status_code=503)


class RequestSizeLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and os.getenv("REGEN_ENV") == "production" and scope["scheme"] != "https" and not (
                scope["method"] == "GET" and scope["path"] in ("/health", "/ready")):
            return await JSONResponse({"detail": "HTTPS required."}, status_code=400)(scope, receive, send)
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        # Check before multipart parsing. Content-Length is optional and untrusted.
        limits = {"/upload/validate": 21 << 20, "/analyze/upload": 61 << 20, "/recovery/photos": 3 << 20}
        path = scope["path"]
        limit = limits.get(path, 3 << 20 if path.endswith("/import") else 256 << 10)
        if path in limits or path.endswith("/import"):
            try:
                await require_member(Request(scope))
            except HTTPException as exc:
                return await JSONResponse({"detail": exc.detail}, status_code=exc.status_code)(scope, receive, send)
        from tempfile import SpooledTemporaryFile
        with SpooledTemporaryFile(max_size=256 * 1024) as buffer:
            size = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                size += len(chunk)
                if size > limit:
                    return await JSONResponse({"detail":"Request too large."}, status_code=413)(scope, receive, send)
                buffer.write(chunk)
                if not message.get("more_body"):
                    break
            buffer.seek(0)
            delivered = False

            async def replay():
                nonlocal delivered
                if delivered:
                    return await receive()
                chunk = buffer.read(64 * 1024)
                delivered = buffer.tell() >= size
                return {"type":"http.request", "body":chunk, "more_body":not delivered}

            await self.app(scope, replay, send)


app.add_middleware(RequestSizeLimit)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def ai_consent(request, call_next):
    from core.ai_client import (
        _cloud_consent,
        _tenant,
        _usage,
        _last_provider,
    )

    tenant_token = _tenant.set(None)
    usage_token = _usage.set(0)
    provider_token = _last_provider.set(None)

    import re
    manual_step = re.fullmatch(r"/(?:analysis-missions/[^/]+/steps|missions/[^/]+/(?:transitions|clarifications))",
                               request.url.path)
    consent = _cloud_consent.set(
        request.headers.get("X-AI-Consent") == "yes"
        and (manual_step is not None or request.url.path in {
            "/analyze/upload",
            "/interpret/datasets",
            "/analyze/waste",
            "/analyze/waste/inventory",
            "/missions",
        })
    )

    try:
        return await call_next(request)
    finally:
        _cloud_consent.reset(consent)
        _last_provider.reset(provider_token)
        _usage.reset(usage_token)
        _tenant.reset(tenant_token)


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ── Pydantic models ─────────────────────────────────────────────────────────

class WasteRequest(BaseModel):
    service_pin: Optional[str] = Field(default=None, pattern=r"^[1-9][0-9]{5}$")
    condition: str = Field(default="good", min_length=1, max_length=160)
    contaminated: bool = False
    waste_type: str = Field(..., min_length=1, max_length=200, json_schema_extra={"example": "coconut shell"})
    quantity_kg: float = Field(..., gt=0, le=100000, allow_inf_nan=False, json_schema_extra={"example": 50.0})


class ActionPlanRequest(BaseModel):
    include_waste: Optional[bool] = True
    waste_type: Optional[str] = None
    waste_quantity_kg: Optional[float] = None


class DataInterpretRequest(BaseModel):
    org_name: str = "My Organization"
    org_type: str = "University"
    water_records: int = 0
    water_buildings: list[str] = Field(default_factory=list, max_length=256)
    water_date_range: str = ""
    water_warnings: list[str] = Field(default_factory=list, max_length=100)
    energy_records: int = 0
    energy_zones: list[str] = Field(default_factory=list, max_length=256)
    energy_date_range: str = ""
    energy_warnings: list[str] = Field(default_factory=list, max_length=100)
    fuel_records: int = 0
    waste_type: str = ""
    waste_qty_kg: float = 0
    manual_water_liters: float = 0
    manual_water_period: str = ""
    manual_energy_kwh: float = 0
    manual_energy_period: str = ""
    available_datasets: list[str] = Field(default_factory=list, max_length=5)


# ── Existing demo endpoints (unchanged) ─────────────────────────────────────

@app.get("/ready", tags=["System"])
def readiness():
    from sqlalchemy.exc import SQLAlchemyError
    try:
        require_schema()
    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(503, "Database schema unavailable.") from None
    return {"status": "ready"}


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
    Machine-readable disclosure of which agents are deterministic Python vs Gemini-narrated.
    Intended for technical reviewers and judges who want to verify claims without reading source.
    """
    return {
        "architecture_version": "1.0",
        "computation_model": "deterministic_core_with_llm_narration",
        "summary": (
            "All quantitative analysis (anomaly detection, severity classification, cost/CO2 math, "
            "RE:GEN scoring, ROI calculations) is deterministic Python. "
            "Narratives use deterministic fallbacks unless an authorized provider is configured."
        ),
        "deterministic_agents": [
            {"agent": "Water Leakage Agent",       "endpoint": "/analyze/water",        "llm_calls": 0},
            {"agent": "Energy Optimization Agent", "endpoint": "/analyze/energy",       "llm_calls": 0},
            {"agent": "Pollution & Impact Agent",  "endpoint": "/dashboard/summary",       "llm_calls": 0},
            {"agent": "RE:GEN Score Agent",        "endpoint": "/generate/action-plan", "llm_calls": 0},
        ],
        "llm_narrated_agents": [
            {
                "agent": "Waste-to-Wealth Agent",
                "endpoint": "/analyze/waste",
                "llm_calls": 1,
                "llm_fields": ["ai_recommendation"],
                "deterministic_fields": ["hidden_value_score", "estimated_recovery", "hazard_warning", "reasoning_trace"],
            },
            {
                "agent": "Decision Engine Agent",
                "endpoint": "/generate/action-plan",
                "llm_calls": 1,
                "llm_fields": ["top_action_explanation"],
                "deterministic_fields": ["ranked_actions", "priority_score", "roi", "urgency", "feasibility"],
            },
            {
                "agent": "Report Agent",
                "endpoint": "/generate/action-plan",
                "llm_calls": 1,
                "llm_fields": ["executive_summary"],
                "deterministic_fields": ["silent_losses", "campus_health_index", "building_risk_ranking", "action_plan", "sdg_alignment"],
            },
        ],
        "ai_status": ai_status(),
    }


@app.get("/analyze/waste/materials", tags=["Waste"], summary="List waste materials")
def get_waste_materials():
    """
    Return the full list of materials in the Waste-to-Wealth knowledge base.
    Used by the frontend to populate dropdowns dynamically.
    """
    materials = get_kb_materials_list()
    return {
        "materials": materials,
        "count": len(materials),
    }


@app.post("/analyze/waste", tags=["Waste"], summary="Analyze a waste material")
@limiter.limit("10/minute")
def analyze_waste_endpoint(request: Request, body: WasteRequest, member: Member = Depends(require_member)):
    """Analyze a single waste material and return recovery pathways, estimated revenue, and guardrail notices."""
    result = analyze_waste(body.waste_type, body.quantity_kg, narrative=False)
    if body.service_pin and "error" not in result:
        import uuid
        from sqlalchemy.orm import Session
        from core.database import engine
        from core.recovery import Batch, options

        batch = Batch(
            request_id=uuid.uuid4(),
            material=body.waste_type,
            quantity_g=round(body.quantity_kg * 1000),
            service_pin=body.service_pin,
            condition=body.condition,
            contaminated=body.contaminated,
            mixed_inventory=body.condition == "mixed",
            goal="recycling",
        )
        trace = []
        with Session(engine) as db:
            state, matches, reason = options(
                db, member.tenant, batch, trace=trace
            )
        result["recovery_evaluation"] = {
            "state": state,
            "options": matches,
            "reason": reason,
            "events": trace,
        }
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result



class InventoryItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    material: str = Field(min_length=1, max_length=200)
    quantity: float = Field(gt=0, le=100000, allow_inf_nan=False)
    unit: str = Field(pattern=r"^(kg|g|tonnes|pcs|L)$")
    condition: str = Field(default="used", max_length=160)
    contaminated: bool = False
    research_pathways: list[Literal["sell", "donate", "reuse", "repair", "upcycle", "recycle", "compost",
                                    "collective", "professional", "industrial_symbiosis"]] = Field(default_factory=list, max_length=4)


class InventoryRequest(BaseModel):
    evidence_only: bool = False
    items: list[InventoryItem] = Field(min_length=1, max_length=20)
    service_pin: Optional[str] = Field(
        default=None, pattern=r"^[1-9][0-9]{5}$"
    )


INVENTORY_RESEARCH_SECONDS = 8.0


@app.post("/analyze/waste/inventory", tags=["Waste"])
@limiter.limit("20/minute")
def analyze_inventory(
    request: Request,
    body: InventoryRequest,
    member: Member = Depends(require_member)
):
    import asyncio
    from contextvars import copy_context
    from functools import partial
    from time import monotonic

    import anyio
    from starlette.concurrency import run_in_threadpool

    from core.market_evidence import configured_market_feed, inventory_market_rows, public_market_research
    from core.public_discovery import research_deadline
    from core.recovery_discovery import inventory_discovery
    from core.search_research import general_research

    context = copy_context()
    evidence_rows = inventory_market_rows()
    discovery = {"status": "pending"}
    identities = {}
    total = len(body.items)
    started = monotonic()
    timings = {"semantic_ms": 0, "pathway_and_evidence_ms": 0, "evidence_filter_ms": 0.0}

    def evaluate(item, research=False, previous=None, *, enrich_only=False):
        start = monotonic()
        row = context.copy().run(inventory_item, item, body.service_pin, member, research, previous,
                                 body.evidence_only, evidence_rows, discovery, enrich_only=enrich_only,
                                 identity=identities.get(id(item)))
        timings["pathway_and_evidence_ms"] += round((monotonic() - start) * 1000)
        timings["evidence_filter_ms"] += row["intelligence"].pop("service_filter_ms")
        return row

    def prepare_semantics(items):
        from core.material_intelligence import interpret_inventory
        from core.ai_client import _cloud_consent

        start = monotonic()
        consent = _cloud_consent.set(False)
        try:
            interpreted = interpret_inventory([item.model_dump() for item in items])
        finally:
            _cloud_consent.reset(consent)
            timings["semantic_ms"] += round((monotonic() - start) * 1000)

        for item, identity in zip(items, interpreted):
            identities[id(item)] = identity

    async def collect_research(planned):
        start = monotonic()
        absolute = start + INVENTORY_RESEARCH_SECONDS
        deadline = research_deadline.set(absolute)

        async def run(name, function, *args):
            try:
                return await anyio.to_thread.run_sync(partial(function, *args), abandon_on_cancel=True)
            finally:
                timings[name] = round((monotonic() - start) * 1000)

        jobs = {
            "feed_ms": asyncio.create_task(run("feed_ms", configured_market_feed)),
            "specialist_market_ms": asyncio.create_task(run("specialist_market_ms", public_market_research,
                                                            body.items, body.service_pin)),
            "public_discovery_ms": asyncio.create_task(run("public_discovery_ms", inventory_discovery,
                                                           body.service_pin, body.items)),
            "indexed_search_ms": asyncio.create_task(run("indexed_search_ms", general_research,
                                                         body.items, body.service_pin, planned)),
        }
        try:
            done, pending = await asyncio.wait(jobs.values(), timeout=max(0, absolute - monotonic()))
            results = {name: task.result() for name, task in jobs.items() if task in done}
            timings["optional_research_ms"] = round((monotonic() - start) * 1000)
            return results, bool(pending)
        finally:
            for task in jobs.values():
                if not task.done():
                    task.cancel()
            await asyncio.gather(*jobs.values(), return_exceptions=True)
            research_deadline.reset(deadline)

    def use_research(results, expired):
        nonlocal evidence_rows
        specialist = results.get("specialist_market_ms", {})
        indexed = results.get("indexed_search_ms", {})
        local = results.get("public_discovery_ms", {})
        evidence_rows = evidence_rows + results.get("feed_ms", []) + specialist.get("rows", []) + indexed.get("rows", [])
        statuses = {specialist.get("status"), indexed.get("status"), local.get("status")}
        status = (
            "deadline_reached" if expired or "deadline_reached" in statuses else
            "provider_unavailable" if statuses & {"unavailable", "invalid_configuration"} else
            "no_compatible_evidence"
        )
        discovery.update(local, status=status, research_services=specialist.get("services", []) + indexed.get("services", []),
                         material_research_status=specialist.get("status"), general_research_status=indexed.get("status"),
                         general_search_metadata=indexed.get("search_metadata"))

    def snapshot(rows, **progress):
        result = inventory_snapshot(rows, total, context.run(ai_status))
        return {**result, **progress, "research_timings_ms": {
            **timings, "snapshot_elapsed_ms": round((monotonic() - started) * 1000),
        }}

    if "application/x-ndjson" not in request.headers.get("accept", ""):
        if not body.evidence_only:
            context.run(prepare_semantics, body.items)
        planned = [evaluate(item, True) for item in body.items]
        use_research(*anyio.from_thread.run(collect_research, planned))
        return snapshot([evaluate(item, True, row, enrich_only=True)
                         for item, row in zip(body.items, planned)])

    async def stream():
        rows = []
        yield json.dumps(snapshot(rows)) + "\n"
        for item in body.items:
            if await request.is_disconnected():
                return
            rows.append(await run_in_threadpool(evaluate, item))
            yield json.dumps(snapshot(rows)) + "\n"

        research = asyncio.create_task(collect_research(tuple(rows)))
        batch = None

        async def publish_research():
            use_research(*await research)
            for index, item in enumerate(body.items):
                rows[index] = await run_in_threadpool(evaluate, item, True, rows[index], enrich_only=True)
            return json.dumps(snapshot(rows, researched_items=total)) + "\n"

        try:
            if not body.evidence_only:
                for start in range(0, total, 3):
                    if await request.is_disconnected():
                        return
                    batch_items = body.items[start:start + 3]
                    batch = asyncio.create_task(run_in_threadpool(context.copy().run, prepare_semantics, batch_items))
                    if discovery["status"] == "pending":
                        await asyncio.wait((batch, research), return_when=asyncio.FIRST_COMPLETED)
                        if research.done() and not batch.done():
                            yield await publish_research()
                    await batch
                    for index, item in enumerate(batch_items, start):
                        rows[index] = await run_in_threadpool(evaluate, item, True, rows[index])
                        progress = {"planned_items": index + 1}
                        if discovery["status"] != "pending":
                            progress["researched_items"] = total
                        yield json.dumps(snapshot(rows, **progress)) + "\n"
                    if discovery["status"] == "pending" and research.done():
                        yield await publish_research()
            if discovery["status"] == "pending":
                yield await publish_research()
        finally:
            if batch is not None and not batch.done():
                batch.cancel()
            if not research.done():
                research.cancel()
            await asyncio.gather(*(task for task in (batch, research) if task is not None), return_exceptions=True)

    return StreamingResponse(stream(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


def inventory_item(item, pin, member, research, previous, evidence_only, evidence_rows, discovery, *, enrich_only=False, identity=None):
    from uuid import uuid4
    from sqlalchemy.orm import Session
    from core.database import engine
    from core.market_evidence import attach_market_evidence, compatible_market_pathways, normalize, published_references
    from core.market_valuation import convert_quantity, enrich_pathways
    from core.recovery import Batch, PostalArea, options
    from core.recovery_discovery import attach_local_discovery, maps_search_links
    from core.waste_intelligence import investigate_recovery, restricted_material

    item = item.model_copy(update={"contaminated": item.contaminated or
                                   item.condition.casefold() in {"contaminated", "spoiled"}})
    original_material = item.material
    semantic_material = original_material

    if identity and identity.get("certainty") != "unknown":
        candidate = identity.get("canonical_material", "")
        if candidate and not restricted_material(original_material, {}):
            semantic_material = candidate

    semantic_hazard = (
        restricted_material(original_material, {}) or
        restricted_material(semantic_material, {})
    )

    if semantic_hazard:
        semantic_material = original_material

    mass_kg = convert_quantity(item.quantity, item.unit, "kg")
    mass = float(mass_kg) if mass_kg is not None else None
    reference = previous["reference"] if previous else analyze_waste(item.material, mass or 1, narrative=False)
    matches = previous["verified_options"] if previous else []
    reason = previous["locality_note"] if previous else "No verified offer established."
    locality = previous["postal_locality"] if previous else None
    if previous is None and pin:
        with Session(engine) as db:
            area = db.get(PostalArea, pin)
            if area:
                locality = {"name": area.locality, "source": area.provenance.get("source_document")}
            else:
                locality = next((entry for entry in published_references()["postal"] if entry["pin"] == pin), None)
            grams = round(mass_kg * 1000) if mass_kg is not None else 0
            if 1 <= grams <= 100000000 and len(item.material) <= 160:
                batch = Batch(request_id=uuid4(), material=item.material, quantity_g=grams, service_pin=pin,
                              condition=item.condition, contaminated=item.contaminated or
                              restricted_material(item.material, reference), mixed_inventory=item.condition == "mixed")
                _, matches, reason = options(db, member.tenant, batch)

    if semantic_hazard or restricted_material(item.material, reference) or item.contaminated:
        matches = [service for service in matches if service["pathway"] == "authorized_disposal"]
    if item.condition.casefold() not in {"good", "working", "used"}:
        matches = [service for service in matches if service["pathway"] != "donate"]

    if not locality and pin:
        from core.postal_intelligence import lookup_postal
        postal = lookup_postal(pin)
        if postal:
            name = postal.get("locality") or postal.get("district")
            if name:
                locality = {"name": name, "source": "Postal reference"}
    fields = item.model_dump(exclude={"research_pathways"})
    requested = list(item.research_pathways) if evidence_only else []
    requested += compatible_market_pathways(fields, pin, evidence_rows)

    intelligence = investigate_recovery(
        material=semantic_material if not semantic_hazard else original_material,
        quantity=item.quantity,
        unit=item.unit,
        condition=item.condition,
        reference=reference,
        contaminated=item.contaminated or (
            semantic_hazard and not restricted_material(original_material, reference)
        ),
        services=matches,
        allow_ai=(
            research
            and not evidence_only
            and not enrich_only
            and identity is None
        ),
        research_pathways=requested,
        precomputed=(
            identity.get("recovery_plan")
            if identity and not semantic_hazard
            and not evidence_only and not enrich_only
            else None
        )
    )

    if enrich_only and previous and not evidence_only:
        from copy import deepcopy
        evidence_candidates = [route for route in intelligence["pathways"] if route["category"] in requested]
        intelligence = deepcopy(previous["intelligence"])
        retained = {route["category"] for route in intelligence["pathways"]}
        intelligence["pathways"].extend(route for route in evidence_candidates if route["category"] not in retained)
        intelligence["events"] = [event for event in intelligence["events"] if event["action"] not in {
            "public_service_discovery", "rank_evidence_backed_pathways"}]

    intelligence = enrich_pathways(fields, intelligence, matches)
    market_fields = {
        **fields,
        "material_identity": identity or {}
    }
    intelligence = attach_market_evidence(
        market_fields, intelligence, pin, rows=evidence_rows
    )
    discovery_fields = {**fields, "original_material": original_material}

    if identity and not semantic_hazard:
        if identity.get("certainty") != "unknown":
            discovery_fields["material"] = identity.get(
                "search_material", original_material
            )

    from time import monotonic
    filter_started = monotonic()
    intelligence = attach_local_discovery(discovery_fields, intelligence, pin, discovery)
    intelligence["service_filter_ms"] = round((monotonic() - filter_started) * 1000, 2)

    intelligence["material_identity"] = identity or {
        "original_material": original_material,
        "canonical_material": original_material,
        "certainty": "unknown"
    }
    pathways = intelligence["pathways"]
    def priority(route):
        ratings = {"Low": 0, "Medium": 1, "High": 2}
        return (not route.get("conditional_completion"), bool(route.get("verified_services")), route["valuation"]["status"] == "estimated",
                bool(route.get("public_services")), ratings.get(route.get("feasibility"), 0),
                -ratings.get(route.get("risk"), 0), ratings.get(route.get("environmental_impact"), 0))

    pathways.sort(key=priority, reverse=True)
    for route in pathways:
        route["ranking_reason"] = (
                "A verified service matches the submitted lot." if route.get("verified_services") else
                "A compatible published valuation supports comparison." if route["valuation"]["status"] == "estimated" else
                "A published service lead supports further investigation." if route.get("public_services") else
                "Ranked by suitability, estimated feasibility and handling risk."
            )
    del pathways[4:]
    public_names = {normalize(lead["organization"]) for route in pathways for lead in route.get("public_services", [])}
    intelligence["research_status"] = (
        "pending" if discovery["status"] == "pending" else
        "public_leads_found" if public_names else discovery["status"]
    )
    if "local_discovery" in intelligence:
        intelligence["local_discovery"].update(status=intelligence["research_status"], public_lead_count=len(public_names))
    for rank, route in enumerate(pathways, start=1):
        route["rank"] = rank
        route["maps_search_links"] = maps_search_links(
            discovery_fields["material"], route.get("service_pathway", route["category"]), pin,
            locality.get("name") if isinstance(locality, dict) else discovery.get("locality"))
    intelligence["events"].append({"action": "rank_evidence_backed_pathways", "completed": True,
                                   "verified_matches": len(matches)})
    return {
        **fields,
        "material_identity": intelligence["material_identity"],
        "postal_locality": locality,
        "mass_kg": mass,
        "reference": {key: reference.get(key) for key in ("category", "hazard_warning")},
        "intelligence": intelligence,
        "verified_options": matches,
        "locality_note": reason
    }



def inventory_snapshot(results, total, status):
    from core.market_evidence import normalize

    routes = [route for item in results for route in item["intelligence"]["pathways"]]
    public_names = {normalize(lead.get("organization")) for route in routes for lead in route.get("public_services", [])}
    verified = [service for item in results for service in item["verified_options"]]
    verified_names = {normalize(service.get("organization")) for service in verified}
    return {
        "items": results,
        "verified_partner_count": len(verified_names - {""}),
        "public_lead_count": len(public_names - verified_names - {""}),
        "total_items": total,
        "completed_items": len(results),
        "pathway_count": sum(
            len(r["intelligence"]["pathways"]) for r in results
        ),
        "verified_option_count": len({service["service_id"] for service in verified}),
        "ai_enhanced": any(
            r["intelligence"]["ai_enhanced"] for r in results
        ),
        "confirmed_net_inr": None,
        "realized_recovery": None,
        "ai_status": status
    }


@app.post("/demo/waste", tags=["Demo"])
def demo_waste(body: WasteRequest):
    result = analyze_waste(body.waste_type, body.quantity_kg, narrative=False)
    return {**result, "evidence_type": "demo"}


@app.get("/analyze/water", tags=["Demo"], summary="Water leakage analysis (demo data)")
def analyze_water_endpoint():
    """Run the Water Leakage Agent on the built-in simulated campus water dataset."""
    return {**analyze_water(), "evidence_type":"demo"}


@app.get("/analyze/energy", tags=["Demo"], summary="Energy waste analysis (demo data)")
def analyze_energy_endpoint():
    """Run the Energy Optimization Agent on the built-in simulated campus energy dataset."""
    return {**analyze_energy(), "evidence_type":"demo"}


@app.get("/dashboard/summary", tags=["Demo"], summary="Full dashboard summary (demo data)")
def dashboard_summary():
    water  = analyze_water()
    energy = analyze_energy()

    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], 0, weekly_demo=True)
    decision = generate_decisions(water, energy)
    regen    = compute_regen_score(water, energy, impact, decision)
    report   = generate_report(water, energy, impact, decision, regen)

    return {
        "evidence_type": "demo",
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
    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], 0, weekly_demo=True)
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
                "icon":           "ðŸ§ ",
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
                "icon":           "ðŸ†",
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
                "confidence":     None,
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

    impact   = analyze_impact(water["total_wasted_liters"], energy["total_wasted_kwh"], waste_value, weekly_demo=True)
    decision = generate_decisions(water, energy, waste)
    regen    = compute_regen_score(water, energy, impact, decision, waste)
    report   = generate_report(water, energy, impact, decision, regen, waste)

    return {
        "evidence_type":"demo", "water": water, "energy": energy, "waste": waste,
        "impact": impact, "decision": decision,
        "regen_score": regen, "report": report,
    }


# ── Upload: validate a single file ─────────────────────────────────────────

def _validate_preview(validator, frame):
    try:
        return validator(frame)
    except ValueError:
        raise HTTPException(422, "Ambiguous or invalid input. Map the required columns and retry.")


@app.post("/upload/validate", tags=["Upload"], summary="Validate an uploaded file")
@limiter.limit("10/minute")
async def validate_upload(
    request: Request,
    member: Member = Depends(require_member),
    file: UploadFile = File(...),
    column_mapping: str = Form("{}"),
    dataset_type: str = Form(...),   # "water" | "energy" | "fuel"
):
    """
    Validate an uploaded CSV or Excel file.
    Returns detected columns, record count, date range, and any errors/warnings.
    """
    allowed = {"water", "energy", "fuel", "waste", "occupancy"}
    if dataset_type not in allowed:
        raise HTTPException(status_code=400, detail=f"dataset_type must be one of: {allowed}")

    content = await file.read(20 * 1024 * 1024 + 1)
    if len(content) > 20 * 1024 * 1024:  # 20 MB guard
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    try:
        raw_df = _parse_bytes(content, file.filename or "upload.csv", json.loads(column_mapping))
    except Exception:
        raise HTTPException(422, "Invalid or unsupported file.")

    if dataset_type == "water":
        _, info = _validate_preview(validate_water_df, raw_df)
    elif dataset_type == "energy":
        _, info = _validate_preview(validate_energy_df, raw_df)
    elif dataset_type == "fuel":
        _, info = _validate_preview(validate_fuel_df, raw_df)
    else:
        required = {"waste": {"type", "quantity_kg"}, "occupancy": {"occupancy_count"}}[dataset_type]
        valid = required <= set(raw_df.columns)
        if valid:
            try:
                if dataset_type == "waste":
                    if len(raw_df) > 100:
                        raise ValueError()
                    analyze_waste_batch(raw_df.to_dict("records"))
                else:
                    counts = raw_df["occupancy_count"].astype(float)
                    valid = bool((counts.between(1, 10000000) & (counts % 1 == 0)).all())
            except (ValueError, TypeError, KeyError, AttributeError):
                valid = False
        info = {
            "dataset": dataset_type,
            "valid": valid,
            "record_count": len(raw_df),
            "columns_detected": list(raw_df.columns),
            "warnings": [],
            "errors": [] if valid else ["Required valid columns: " + ", ".join(sorted(required))],
        }

    info["filename"]      = file.filename
    info["file_size_kb"]  = round(len(content) / 1024, 1)
    info["raw_columns"]   = list(raw_df.columns)
    return info


# ── Data intelligence interpreter ──────────────────────────────────────────

@app.post("/interpret/datasets", tags=["Interpret"], summary="Interpret uploaded dataset metadata")
@limiter.limit("10/minute")
def interpret_datasets(request: Request, body: DataInterpretRequest, member: Member = Depends(require_member)):
    """
    Produce an intelligent pre-analysis summary of the uploaded datasets.
    Deterministic facts are always returned. Gemini adds a quality note when available.
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
        facts.append("Aggregate water total supplied")

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
        facts.append("Aggregate energy total supplied")

    if body.fuel_records > 0:
        facts.append(f"{body.fuel_records:,} Fuel Records")

    if body.waste_type:
        facts.append(f"Waste: {body.waste_type} ({body.waste_qty_kg} kg)")

    if all_warnings:
        facts.append(f"{len(all_warnings)} Column Warning{'s' if len(all_warnings) > 1 else ''} Handled")

    if not facts:
        facts.append("No datasets detected — manual entries will be used")

    n = len(body.available_datasets)
    facts.append("Avoided emissions require documented applicable factors.")

    # Fallback quality note (deterministic)
    ds_list = ", ".join(body.available_datasets) if body.available_datasets else "no primary datasets"
    fallback = (
        f"{n} dataset{'s' if n != 1 else ''} validated for {body.org_name}. "
        f"Analysis will run on: {ds_list}. "
        "Review outstanding column warnings before analysis."
    )

    return {
        "facts": facts,
        "quality_note": fallback,
        "ai_enhanced": False,
        "ai_status": ai_status(),
        "datasets_count": n,
        "coverage": compute_coverage(body.available_datasets),
    }


# ── Upload: run full analysis on uploaded files ─────────────────────────────

@app.post("/analyze/upload", tags=["Upload"], summary="Run full analysis on uploaded files")
@limiter.limit("10/minute")
async def analyze_upload(
    request: Request,
    member: Member = Depends(require_member),
    progress = Depends(upload_events),
    org_name:           str  = Form("My Organization", min_length=1, max_length=256),
    org_type:           str  = Form("University", min_length=1, max_length=128),
    column_mappings:    str = Form("{}"),
    water_inr_per_litre: Optional[float] = Form(None, ge=0, le=100000, allow_inf_nan=False),
    energy_inr_per_kwh: Optional[float] = Form(None, ge=0, le=100000, allow_inf_nan=False),
    tariff_reference: Optional[str] = Form(None, min_length=1, max_length=160),
    water_file:         Optional[UploadFile] = File(None),
    energy_file:        Optional[UploadFile] = File(None),
    fuel_file:          Optional[UploadFile] = File(None),
    # Manual entry fallbacks
    manual_water_liters:  Optional[float] = Form(None, ge=0, allow_inf_nan=False),
    manual_water_period:  Optional[str]   = Form("weekly"),
    manual_energy_kwh:    Optional[float] = Form(None, ge=0, allow_inf_nan=False),
    manual_energy_period: Optional[str]   = Form("weekly"),
    manual_fuel_type:     Optional[str]   = Form(None),
    manual_fuel_liters:   Optional[float] = Form(None, ge=0, allow_inf_nan=False),
    # Waste — multi-stream JSON array {"type":...,"quantity_kg":...,"unit":...}
    waste_items:          Optional[str]   = Form(None),
    # Legacy single-item fallback (backward compat)
    waste_type:           Optional[str]   = Form(None),
    waste_quantity_kg:    Optional[float] = Form(None, ge=0, allow_inf_nan=False),
    # Occupancy — optional; enables peer benchmarking when provided
    occupancy_count:      Optional[int]   = Form(None, ge=1, le=10000000),
    floor_area_m2: Optional[float] = Form(None, ge=1, le=1e9, allow_inf_nan=False),
):
    """
    Run multi-agent analysis on uploaded organizational data.
    Any combination of datasets is accepted — missing datasets are skipped.
    Utility emissions require documented applicable factors.
    """
    try:
        mappings = json.loads(column_mappings)
        if not isinstance(mappings, dict):
            raise ValueError()
    except ValueError:
        raise HTTPException(422, "Expected column mappings keyed by dataset.")
    if manual_water_period not in PERIOD_DAYS or manual_energy_period not in PERIOD_DAYS:
        raise HTTPException(422, "Unsupported reporting period.")
    rates = {"water":water_inr_per_litre, "energy":energy_inr_per_kwh}
    if any(rate is not None for rate in rates.values()) and not (tariff_reference or "").strip():
        raise HTTPException(422, "Facility tariff requires its invoice or schedule reference.")
    tariffs = {domain:{"rate":rate,"tariff_source":tariff_reference} if rate is not None else {"rate": None, "tariff_source": "No documented tariff supplied."}
               for domain, rate in rates.items()}
    available_datasets = ["occupancy"] if occupancy_count and occupancy_count > 0 else []


    from starlette.concurrency import run_in_threadpool
    from time import monotonic
    timing = {}
    began = monotonic()

    def analyze_resource(content, filename, domain, validate, analyze):
        raw = _parse_bytes(content, filename, mappings.get(domain))
        frame, info = validate(raw)
        if not info["valid"]:
            raise HTTPException(422, f"{domain.title()} file errors: {info['errors']}")
        level = detect_analysis_level(frame, is_manual=False)
        return analyze(df=frame, is_uploaded=True, analysis_level_info=level, **tariffs[domain]), level

    # ── Water ──────────────────────────────────────────
    water_result       = None
    water_level_info   = None

    if water_file and water_file.filename:
        content = await water_file.read(20 * 1024 * 1024 + 1)
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Water file exceeds 20 MB limit.")
        try:
            water_result, water_level_info = await run_in_threadpool(
                analyze_resource, content, water_file.filename, "water", validate_water_df, analyze_water)
            available_datasets.append("water")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(422, "Invalid water file.")

    elif manual_water_liters is not None:
        water_level_info = detect_analysis_level(None, is_manual=True)
        water_df = build_water_df_from_manual(manual_water_liters, period=manual_water_period or "weekly")
        # Do NOT run auto_detect_anomalies — manual entry has no real temporal signal
        water_result = analyze_water(df=water_df, is_uploaded=True, analysis_level_info=water_level_info, **tariffs["water"])
        water_result["reporting_days"] = PERIOD_DAYS[manual_water_period]
        water_result["data_source"] = f"Manual entry ({manual_water_period or 'weekly'})"
        available_datasets.append("water")

    # ── Energy ─────────────────────────────────────────
    timing["water_stage_ms"] = round((monotonic() - began) * 1000)
    await progress("Water Leakage Agent", "analyzed" if water_result else "skipped",
                   records=(water_result or {}).get("resource_profile", {}).get("records"))
    energy_result      = None
    energy_level_info  = None

    if energy_file and energy_file.filename:
        content = await energy_file.read(20 * 1024 * 1024 + 1)
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Energy file exceeds 20 MB limit.")
        try:
            energy_result, energy_level_info = await run_in_threadpool(
                analyze_resource, content, energy_file.filename, "energy", validate_energy_df, analyze_energy)
            available_datasets.append("energy")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(422, "Invalid energy file.")

    elif manual_energy_kwh is not None:
        energy_level_info = detect_analysis_level(None, is_manual=True)
        energy_df = build_energy_df_from_manual(manual_energy_kwh, period=manual_energy_period or "weekly")
        # Do NOT run auto_detect_anomalies — manual entry has no real temporal signal
        energy_result = analyze_energy(df=energy_df, is_uploaded=True, analysis_level_info=energy_level_info, **tariffs["energy"])
        energy_result["reporting_days"] = PERIOD_DAYS[manual_energy_period]
        energy_result["data_source"] = f"Manual entry ({manual_energy_period or 'weekly'})"
        available_datasets.append("energy")

    # ── Fuel (carbon + full summary) ────────────────────
    timing["water_and_energy_ms"] = round((monotonic() - began) * 1000)
    await progress("Energy Optimization Agent", "analyzed" if energy_result else "skipped",
                   records=(energy_result or {}).get("resource_profile", {}).get("records"))
    fuel_co2_kg  = 0.0
    fuel_summary = None
    if fuel_file and fuel_file.filename:
        content = await fuel_file.read(20 * 1024 * 1024 + 1)
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Fuel file exceeds 20 MB limit.")
        try:
            raw_df = _parse_bytes(content, fuel_file.filename, mappings.get("fuel"))
            fuel_summary_raw, finfo = validate_fuel_df(raw_df)
            if finfo["valid"]:
                fuel_co2_kg  = fuel_summary_raw.get("total_co2_kg", 0)
                fuel_summary = fuel_summary_raw
                available_datasets.append("fuel")
            else:
                raise ValueError()
        except Exception:
            raise HTTPException(422, "Invalid fuel file.")

    elif manual_fuel_liters and manual_fuel_type:
        from core.data_processor import FUEL_EMISSION_FACTORS
        factor = FUEL_EMISSION_FACTORS.get(manual_fuel_type.lower())
        if factor is None or manual_fuel_type.lower() in ("coal", "natural gas", "cng"):
            raise HTTPException(422, "Manual fuel input requires a supported liquid fuel measured in litres.")
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
    if waste_items or waste_type:
        try:
            items = json.loads(waste_items) if waste_items else [{"type": waste_type, "quantity_kg": waste_quantity_kg}]
            if not isinstance(items, list) or len(items) > 100 or any(
                not isinstance(item, dict) or not isinstance(item.get("type"), str)
                or not 1 <= len(item["type"].strip()) <= 200 for item in items
            ):
                raise ValueError()
            waste_result = await run_in_threadpool(
                analyze_waste_batch, items, intelligence=True
            )
        except (ValueError, TypeError, KeyError, OverflowError):
            raise HTTPException(422, "Expected up to 100 named waste items with valid quantities and mass units.")
        if waste_result["status"] == "analyzed":
            available_datasets.append("waste")

    if not set(available_datasets) - {"occupancy"}:
        raise HTTPException(422, "Supply at least one supported dataset.")

    # ── Build skipped stubs ─────────────────────────────
    await progress("Waste-to-Wealth Agent","analyzed" if waste_result else "skipped")
    effective_water  = water_result  or skipped_water_result()
    effective_energy = energy_result or skipped_energy_result()

    # ── Carbon is always automatic ──────────────────────
    water_liters = effective_water.get("total_wasted_liters", 0)
    energy_kwh   = effective_energy.get("total_wasted_kwh", 0)
    if waste_result and waste_result.get("status") == "analyzed":
        # Compat: expose single estimated_recovery for agents that expect it
        if waste_result.get("total_recovery_max_inr") is not None:
            waste_result["estimated_recovery"] = {
                "max_inr": waste_result["total_recovery_max_inr"],
                "min_inr": waste_result["total_recovery_min_inr"],
            }

    # ── Run downstream agents ──────────────────────────
    utilities = [result for result in (water_result, energy_result) if result is not None]
    for result, key, unit in ((water_result, "total_consumption_liters", "L"),
                              (energy_result, "total_consumption_kwh", "kWh")):
        if result is None:
            continue
        quantity = result[key]
        result["intensity"] = {
            "unit": unit, "basis": "Observed totals divided by user-supplied denominators for the reporting window.",
            "per_person": round(quantity / occupancy_count, 3) if occupancy_count else None,
            "per_square_metre": round(quantity / floor_area_m2, 3) if floor_area_m2 else None,
            "occupancy": occupancy_count, "floor_area_m2": floor_area_m2,
        }
    windows = [result.get("resource_profile", {}).get("window") for result in utilities]
    costs = [result["estimated_cost_inr"] for result in utilities]
    comparable_costs = bool(costs) and all(cost is not None for cost in costs) and (
        len(costs) == 1 or windows[0] is not None and windows[0] == windows[1])
    impact = analyze_impact(water_liters, energy_kwh,
                            waste_result.get("total_recovery_max_inr") if waste_result else None,
                            fuel_co2_kg=fuel_co2_kg, measured_context=True,
                            utility_exposure_inr=round(sum(costs), 2) if comparable_costs else None)
    await progress(impact["agent"],"analyzed")
    decision_started = monotonic()
    decision = await run_in_threadpool(generate_decisions, effective_water, effective_energy, waste_result)
    timing["decision_stage_ms"] = round((monotonic() - decision_started) * 1000)
    await progress("Decision Engine Agent", "ranked_actions", ai_enhanced=decision["ai_enhanced"],
                   provider=(decision["ai_layer"] or {}).get("provider"), model=(decision["ai_layer"] or {}).get("model"),
                   duration_ms=timing["decision_stage_ms"])
    regen    = compute_regen_score(effective_water, effective_energy, impact, decision, waste_result)

    await progress(regen["agent"],"computed")
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
    anomaly_available = any(result.get("anomaly_detection_available", False)
                            for result in (effective_water, effective_energy))

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

    coverage_pct = coverage["data_coverage_pct"]

    analysis_metadata = {
        "overall_level":            overall_level,
        "overall_code":             overall_code,
        "overall_label":            overall_label,
        "anomaly_detection_available": anomaly_available,
        "confidence_pct":           None,
        "coverage_pct":             coverage_pct,
        "confidence_reasoning": (
            f"Overall analysis level: {overall_label}. "
            f"{len(available_datasets)} dataset(s) provided: {', '.join(available_datasets) or 'none'}. "
            + (
                "Comparable historical observations support deterministic baseline checks."
                if anomaly_available else
                "Anomaly detection is unavailable at the current data resolution. "
                "Confidence is limited to consumption estimates and benchmarks. "
                "Provide hourly operational logs to unlock advanced modules."
            )
        ),
        "skipped_modules":      skipped_modules,
        "data_sufficiency_summary": (
            f"{len(available_datasets)} of 5 possible datasets provided. "
            f"Dataset coverage: {coverage_pct}%. "
            + (
                f"Advanced AI modules ({', '.join(m['module'] for m in skipped_modules)}) "
                "were not executed — see skipped_modules for required data."
                if skipped_modules else
                "The available primary resource data was analyzed."
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
            f"{r.get('total_wasted_liters', 0)} L above comparable baseline; inspection required. "
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
            f"{r.get('total_wasted_kwh', 0)} kWh above comparable baseline; review operating context. "
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
                f"Estimated recovery (INR): {waste_result.get('total_recovery_max_inr') if waste_result.get('total_recovery_max_inr') is not None else 'unavailable'}. "
                f"Circularity score: {waste_result.get('circularity_score', 0)}/100."
                if waste_result and waste_result.get("status") == "analyzed"
                else "Submit waste inventory to compute recovery value."
            ),
            "confidence":  waste_result.get("confidence") if waste_result else None,
            "recommendation": (
                "Authorized facility staff should confirm material condition, service coverage and current acceptance."
                if waste_result and waste_result.get("status") == "analyzed"
                else "No waste inventory submitted — add waste streams in the Upload Center to activate recovery analysis."
            ),
            "severity":    "high" if (waste_result and waste_result.get("hazardous_count", 0) > 0) else "medium" if waste_result and waste_result.get("status") == "analyzed" else "info",
        },
        {
            "agent":      "Pollution & Impact Agent",
            "icon":       "🌿",
            "status":     "active",
            "finding":    "Avoided emissions are unavailable without applicable documented factors.",
            "reasoning":  impact["financial_basis"],
            "impact":     "Estimated exposure and verified outcomes are tracked separately.",
            "confidence": impact["confidence"],
            "recommendation": "Supply facility-specific utility tariffs, emissions factors and verified outcome evidence.",
            "severity":   "low",
        },
        {
            "agent":      "Decision Engine Agent",
            "icon":       "ðŸ§ ",
            "status":     "active",
            "finding":    f"Ranked {decision['total_actions']} proposed actions for staff review.",
            "reasoning":  (
                f"Actions ranked by urgency × estimated impact × implementation cost. "
                f"Top domain: {decision['ranked_actions'][0]['domain'] if decision['ranked_actions'] else 'N/A'}."
            ),
            "impact":     "Benefits require compatible evidence and outcome verification.",
            "confidence": decision["confidence"],
            "recommendation": decision["ranked_actions"][0]["recommended_action"] if decision["ranked_actions"] else "No actions ranked.",
            "severity":   "medium",
        },
        {
            "agent":      "RE:GEN Score Agent",
            "icon":       "ðŸ†",
            "status":     "active",
            "finding":    f"Indicative historical score: {regen['before_score']}/100.",
            "reasoning":  (
                f"Score computed across water, energy, carbon, and waste dimensions. "
                f"Data coverage: {coverage['data_coverage_pct']}%. "
                f"Dataset coverage: {coverage_pct}%."
            ),
            "impact":     "Post-action measurements are required to assess change.",
            "confidence": regen["confidence"],
            "recommendation": "Collect comparable follow-up observations after approved interventions.",
            "severity":   "high" if regen["before_score"] < 40 else "medium",
        },
        {
            "agent":      "Report Agent",
            "icon":       "📋",
            "status":     "active",
            "finding":    f"Report generated for {org_name}. Coverage: {coverage['data_coverage_pct']}%. Analysis level: {overall_label}.",
            "reasoning":  (
                f"Report synthesises findings from {len(available_datasets)} dataset(s). "
                f"Dataset coverage: {coverage_pct}%. "
                + (f"{len(skipped_modules)} module(s) skipped due to data resolution." if skipped_modules else "All modules executed.")
            ),
            "impact":     f"Executive summary and action plan generated. {len(skipped_modules)} advanced module(s) require higher-resolution data.",
            "confidence": None,
            "recommendation": "Download your custom sustainability report.",
            "severity":   "low",
        },
    ]

    # Compare only measured resources with compatible periods.
    periods = {r.get("reporting_days") for r in utilities}
    supported_period = all(r.get("data_source", "").startswith("Manual entry") or
                           r.get("resource_profile", {}).get("contiguous_complete_daily_coverage") for r in utilities)
    _days = next(iter(periods)) if supported_period and len(periods) == 1 and (
        len(utilities) == 1 or windows[0] is not None and windows[0] == windows[1]
    ) else None
    benchmark_result = compute_benchmark(
        org_type=org_type,
        occupancy_count=occupancy_count,
        total_consumption_liters=effective_water.get("total_consumption_liters", 0),
        total_consumption_kwh=effective_energy.get("total_consumption_kwh", 0),
        days_of_data=_days,
    ) if _days else {"available": False, "skip_reason": "Comparable reporting windows required."}

    if benchmark_result.get("available"):
        for domain, resource in (("energy", energy_result), ("water", water_result)):
            if resource is None:
                benchmark_result[domain] = {"available": False, "reason": "No measurements for this domain."}
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
            tenant=member.tenant,
            org_name=org_name,
            org_type=org_type,
            coverage_pct=coverage.get("data_coverage_pct", 0),
            confidence_pct=None,
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
                "waste": waste_result,
            },
        )
        response["analysis_id"] = analysis_id
    except Exception:
        raise HTTPException(503, "Analysis could not be saved.")

    try:
        alert_sent = (os.getenv("REGEN_ALERT_TENANT") == member.tenant and member.role == "admin" and
                      request.headers.get("X-Alert-Consent") == "yes" and
                      send_alert(effective_water, effective_energy, org_name, response.get("analysis_id")))
        response["alert_sent"] = alert_sent
    except Exception:
        response["alert_sent"] = False

    await progress(report["agent"], "analysis_saved", state="completed", analysis_id=analysis_id)
    response["timings_ms"] = {**timing, "analysis_complete_ms": round((monotonic() - began) * 1000)}
    return response


# ── Demo data download ──────────────────────────────────────────────────────

@app.delete("/history/runs/{analysis_id}")
def remove_analysis(analysis_id: int, member: Member = Depends(require_member)):
    if member.role != "admin":
        raise HTTPException(403, "Administrator required.")
    if not delete_run(analysis_id, member.tenant, member.subject):
        raise HTTPException(404, "Run unavailable.")
    return {"deleted": True}


@app.get("/history/{org_name}", tags=["History"], summary="Fetch analysis run history for an org")
def analysis_history(org_name: str, member: Member = Depends(require_member), limit: int = Query(20, ge=1, le=100)):
    """Return the last N analysis runs for the given org_name, newest first."""
    log_access(member.tenant, member.subject, "history")
    return {"org_name": org_name, "runs": get_history(org_name, limit, tenant=member.tenant)}


@app.get("/report/{analysis_id}/audit-record", tags=["Audit"], summary="JSON audit record for an analysis run")
def get_audit_record(analysis_id: int, member: Member = Depends(require_member)):
    log_access(member.tenant, member.subject, "audit_record", analysis_id)
    run = get_run_by_id(analysis_id, tenant=member.tenant)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Analysis run {analysis_id} not found")
    return build_audit_record(run)


@app.get("/report/{analysis_id}/audit-record.pdf", tags=["Audit"], summary="PDF audit record for an analysis run")
def get_audit_record_pdf(analysis_id: int, member: Member = Depends(require_member)):
    log_access(member.tenant, member.subject, "audit_record", analysis_id)
    run = get_run_by_id(analysis_id, tenant=member.tenant)
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


@app.post("/actions/{action_id}/execute", tags=["Device Control"], summary="Simulate executing a device control action")
def execute_device_action(action_id: str):
    """
    Simulates dispatching a device control command for the given action_id.
    All executions are simulated — no real hardware is connected.
    Set DEVICE_CONTROL_LIVE=true to label responses as live mode (still simulated).
    """
    result = execute_action(action_id)
    return result


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
