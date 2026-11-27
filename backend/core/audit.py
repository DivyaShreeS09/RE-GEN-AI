"""
Build tamper-evident audit records for analysis runs.

SHA-256 hash provides tamper-evidence: if you download this record and later
recompute the hash over the same `payload` field you can confirm nothing was
altered after export. This is NOT a cryptographic signature of authenticity —
it does not prove the record originated from this server or was not replaced
wholesale. A full signature system (e.g. server-side RSA signing) is out of
scope; the hash alone proves the *contents* haven't been silently edited.
"""

import hashlib
import json
from datetime import datetime, timezone

from agents.impact_agent import (WATER_CO2_KG_PER_LITER, ENERGY_CO2_KG_PER_KWH,
                                 VEHICLE_CO2_KG_PER_KM, HOUSEHOLD_CO2_KG_PER_DAY)
from core.scoring import REGEN_SCORE_WEIGHTS

FORMULA_CONSTANTS = {
    "WATER_CO2_KG_PER_LITER": WATER_CO2_KG_PER_LITER, "ENERGY_CO2_KG_PER_KWH": ENERGY_CO2_KG_PER_KWH,
    "VEHICLE_CO2_KG_PER_KM": VEHICLE_CO2_KG_PER_KM, "HOUSEHOLD_CO2_KG_PER_DAY": HOUSEHOLD_CO2_KG_PER_DAY,
    "REGEN_SCORE_WEIGHTS": REGEN_SCORE_WEIGHTS,
}


def _extract_trace(agent_result: dict, agent_name: str) -> dict:
    return {
        "agent":           agent_name,
        "reasoning_trace": agent_result.get("reasoning_trace", []),
    }


def build_audit_record(run: dict) -> dict:
    """
    Assemble the full audit record from a stored analysis run dict
    (as returned by get_run_by_id). Returns the record with a SHA-256
    hash of the payload so the recipient can verify it wasn't tampered with.
    """
    payload = run.get("payload", {})

    agents_traces = []
    for agent_key, label in [
        ("water",       "Water Agent"),
        ("energy",      "Energy Agent"),
        ("impact",      "Impact Agent"),
        ("decision",    "Decision Agent"),
        ("regen_score", "RE:GEN Score Agent"),
    ]:
        if agent_key in payload:
            agents_traces.append(_extract_trace(payload[agent_key], label))

    # Hash is over the canonical payload (sorted keys, no extra whitespace)
    payload_canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_sha256 = hashlib.sha256(payload_canonical.encode()).hexdigest()

    return {
        "schema_version":    "1.0",
        "export_timestamp":  datetime.now(timezone.utc).isoformat(),
        "analysis_id":       run["id"],
        "org_name":          run["org_name"],
        "org_type":          run["org_type"],
        "analysis_timestamp": run["created_at"],
        "summary": {
            "coverage_pct":        run["coverage_pct"],
            "confidence_pct":      run["confidence_pct"],
            "regen_score_before":  run["regen_score_before"],
            "regen_score_after":   run["regen_score_after"],
            "total_wasted_liters": run["total_wasted_liters"],
            "total_wasted_kwh":    run["total_wasted_kwh"],
            "total_co2_saved_kg":  run["total_co2_saved_kg"],
        },
        "formula_constants":  FORMULA_CONSTANTS,
        "agent_reasoning":    agents_traces,
        "payload_sha256":     payload_sha256,
        "payload":            payload,
        "tamper_evidence_note": (
            "SHA-256 hash is computed over the `payload` field of this record "
            "(json.dumps with sort_keys=True, separators=(',',':')). "
            "Recompute to verify contents were not silently edited after export. "
            "This hash does NOT constitute a cryptographic signature of origin."
        ),
    }


def build_pdf(audit_record: dict) -> bytes:
    """Return a minimal PDF of the audit record using reportlab."""
    from xml.sax.saxutils import escape
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from io import BytesIO

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40,
                            topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
    mono  = ParagraphStyle("mono",  parent=styles["Code"],   fontSize=7, leading=9)
    story = []

    def h(text, size=14):
        story.append(Paragraph(
            f"<b>{escape(str(text))}</b>",
            ParagraphStyle("h", parent=styles["Normal"], fontSize=size, spaceAfter=4),
        ))

    def p(text):
        story.append(Paragraph(escape(str(text)), small))

    def sp():
        story.append(Spacer(1, 8))

    h("RE:GEN AI — Analysis Audit Record", 16)
    sp()
    p(f"Analysis ID: {audit_record['analysis_id']}")
    p(f"Organisation: {audit_record['org_name']} ({audit_record['org_type']})")
    p(f"Analysis timestamp: {audit_record['analysis_timestamp']}")
    p(f"Export timestamp: {audit_record['export_timestamp']}")
    sp()

    h("Summary", 12)
    s = audit_record["summary"]
    impact = audit_record["payload"].get("impact", {})
    historical = impact.get("evidence_type") == "historical analysis"

    def metric(key, unit):
        value = s[key]
        return "Unavailable" if value is None else f"{value:,.2f} {unit}"
    for label, val in [
        ("Coverage",              f"{s['coverage_pct']}%"),
        ("Confidence",            "Uncalibrated" if s["confidence_pct"] is None else f"{s['confidence_pct']}% (legacy)"),
        ("RE:GEN Score (before)", s["regen_score_before"]),
        ("RE:GEN Score (after)",  s["regen_score_after"]),
        ("Water baseline excess" if historical else "Water wasted", metric("total_wasted_liters", "L")),
        ("Energy baseline excess" if historical else "Energy wasted", metric("total_wasted_kwh", "kWh")),
        ("Estimated CO2 reduction potential", metric("total_co2_saved_kg", "kg")),
    ]:
        p(f"{label}: {val}")
    sp()

    h("Formula Constants", 12)
    fc = audit_record["formula_constants"]
    if historical:
        p("Historical utility emissions withheld pending applicable documented factors.")
        for resource in ("water", "energy"):
            profile = (audit_record["payload"].get(resource) or {}).get("resource_profile") or {}
            forecast = profile.get("forecast", {})
            if forecast.get("status") == "available":
                p(f"{resource.title()} forecast: {forecast['estimate']} {forecast['unit']} for {forecast['next_date']}.")
    else:
        p(f"WATER_CO2_KG_PER_LITER = {fc['WATER_CO2_KG_PER_LITER']}")
        p(f"ENERGY_CO2_KG_PER_KWH = {fc['ENERGY_CO2_KG_PER_KWH']}")
    weights = fc["REGEN_SCORE_WEIGHTS"]
    p("RE:GEN Score weights: " + ", ".join(f"{k}={v}" for k, v in weights.items()))
    sp()

    h("Agent Reasoning Traces", 12)
    for agent in audit_record["agent_reasoning"]:
        h(agent["agent"], 10)
        for line in agent["reasoning_trace"]:
            p(f"• {line}")
        sp()

    h("Tamper Evidence", 12)
    p("SHA-256 of payload:")
    story.append(Paragraph(audit_record["payload_sha256"], mono))
    sp()
    p(audit_record["tamper_evidence_note"])

    doc.build(story)
    return buf.getvalue()
