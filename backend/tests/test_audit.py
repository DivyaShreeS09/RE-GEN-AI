"""Tests for the audit record endpoint (prompt 2.5)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.database import save_run, get_run_by_id, Base, engine
from core.audit import build_audit_record, build_pdf

Base.metadata.create_all(engine)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_PAYLOAD = {
    "water":  {"reasoning_trace": ["w-step1", "w-step2"], "total_wasted_liters": 100.0},
    "energy": {"reasoning_trace": ["e-step1"],             "total_wasted_kwh":    20.0},
    "impact": {"reasoning_trace": ["i-step1"],             "total_co2_saved_kg":  0.1},
    "decision":    {"reasoning_trace": ["d-step1"]},
    "regen_score": {"reasoning_trace": ["r-step1"], "before_score": 50, "after_score": 65},
}


def _make_run() -> int:
    return save_run(
        org_name="AuditOrg", org_type="University",
        coverage_pct=90.0, confidence_pct=85.0,
        regen_before=50.0, regen_after=65.0,
        wasted_liters=100.0, wasted_kwh=20.0, co2_kg=0.1,
        payload_dict=_PAYLOAD,
    )


class TestBuildAuditRecord:
    def test_contains_all_agent_traces(self):
        rid = _make_run()
        run = get_run_by_id(rid)
        record = build_audit_record(run)
        agent_names = {a["agent"] for a in record["agent_reasoning"]}
        assert "Water Agent" in agent_names
        assert "Energy Agent" in agent_names
        assert "Decision Agent" in agent_names
        assert "RE:GEN Score Agent" in agent_names

    def test_reasoning_trace_content(self):
        rid = _make_run()
        run = get_run_by_id(rid)
        record = build_audit_record(run)
        water_traces = next(a for a in record["agent_reasoning"] if a["agent"] == "Water Agent")
        assert "w-step1" in water_traces["reasoning_trace"]

    def test_hash_is_deterministic(self):
        rid = _make_run()
        run = get_run_by_id(rid)
        h1 = build_audit_record(run)["payload_sha256"]
        h2 = build_audit_record(run)["payload_sha256"]
        assert h1 == h2

    def test_hash_changes_when_payload_changes(self):
        rid1 = _make_run()
        rid2 = save_run(
            org_name="AuditOrg2", org_type="Hospital",
            coverage_pct=70.0, confidence_pct=75.0,
            regen_before=40.0, regen_after=55.0,
            wasted_liters=200.0, wasted_kwh=50.0, co2_kg=1.0,
            payload_dict={"water": {"reasoning_trace": ["different"], "total_wasted_liters": 200.0}},
        )
        h1 = build_audit_record(get_run_by_id(rid1))["payload_sha256"]
        h2 = build_audit_record(get_run_by_id(rid2))["payload_sha256"]
        assert h1 != h2

    def test_formula_constants_present(self):
        rid = _make_run()
        record = build_audit_record(get_run_by_id(rid))
        fc = record["formula_constants"]
        assert fc["WATER_CO2_KG_PER_LITER"] == 0.001
        assert fc["ENERGY_CO2_KG_PER_KWH"] == 0.82
        assert "REGEN_SCORE_WEIGHTS" in fc


class TestAuditEndpoint:
    def test_404_for_missing_id(self):
        r = client.get("/report/999999/audit-record")
        assert r.status_code == 404

    def test_json_audit_record_returned(self):
        rid = _make_run()
        r = client.get(f"/report/{rid}/audit-record")
        assert r.status_code == 200
        data = r.json()
        assert data["analysis_id"] == rid
        assert data["org_name"] == "AuditOrg"
        assert "payload_sha256" in data
        assert "agent_reasoning" in data

    def test_pdf_endpoint_returns_pdf(self):
        rid = _make_run()
        r = client.get(f"/report/{rid}/audit-record.pdf")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"
