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

# Formula constants exposed for auditability
FORMULA_CONSTANTS = {
    "WATER_CO2_KG_PER_LITER": 0.001,
    "ENERGY_CO2_KG_PER_KWH":  0.82,
    "VEHICLE_CO2_KG_PER_KM":  0.167,
    "HOUSEHOLD_CO2_KG_PER_DAY": 2.87,
    "REGEN_SCORE_WEIGHTS": {
        "waste":       0.20,
        "water":       0.20,
        "energy":      0.20,
        "co2":         0.15,
        "urgency":     0.15,
        "feasibility": 0.10,
    },
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
            f"<b>{text}</b>",
            ParagraphStyle("h", parent=styles["Normal"], fontSize=size, spaceAfter=4),
        ))

    def p(text):
        story.append(Paragraph(text, small))

    def sp():
        story.append(Spacer(1, 8))

    h("RE:GEN AI — Analysis Audit Record", 16)
    sp()
    p(f"<b>Analysis ID:</b> {audit_record['analysis_id']}")
    p(f"<b>Organisation:</b> {audit_record['org_name']} ({audit_record['org_type']})")
    p(f"<b>Analysis timestamp:</b> {audit_record['analysis_timestamp']}")
    p(f"<b>Export timestamp:</b> {audit_record['export_timestamp']}")
    sp()

    h("Summary", 12)
    s = audit_record["summary"]
    for label, val in [
        ("Coverage",              f"{s['coverage_pct']}%"),
        ("Confidence",            f"{s['confidence_pct']}%"),
        ("RE:GEN Score (before)", s["regen_score_before"]),
        ("RE:GEN Score (after)",  s["regen_score_after"]),
        ("Water wasted",          f"{s['total_wasted_liters']:,.1f} L"),
        ("Energy wasted",         f"{s['total_wasted_kwh']:,.1f} kWh"),
        ("CO2 saved",             f"{s['total_co2_saved_kg']:,.2f} kg"),
    ]:
        p(f"<b>{label}:</b> {val}")
    sp()

    h("Formula Constants", 12)
    fc = audit_record["formula_constants"]
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
    p("<b>SHA-256 of payload:</b>")
    story.append(Paragraph(audit_record["payload_sha256"], mono))
    sp()
    p(audit_record["tamper_evidence_note"])

    doc.build(story)
    return buf.getvalue()
