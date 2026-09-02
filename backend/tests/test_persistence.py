"""Tests for SQLite persistence: save_run, get_history, and /history endpoint."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.database import save_run, get_history, Base, engine

Base.metadata.create_all(engine)  # idempotent: ensures tables exist

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestSaveAndHistory:
    def test_save_run_returns_int_id(self):
        rid = save_run(
            org_name="TestCorp", org_type="University",
            coverage_pct=80.0, confidence_pct=75.0,
            regen_before=55.0, regen_after=72.0,
            wasted_liters=1200.0, wasted_kwh=340.0, co2_kg=300.0,
            payload_dict={"test": True},
        )
        assert isinstance(rid, int) and rid > 0

    def test_get_history_returns_saved_row(self):
        save_run(
            org_name="HistOrg", org_type="Hospital",
            coverage_pct=60.0, confidence_pct=70.0,
            regen_before=40.0, regen_after=60.0,
            wasted_liters=500.0, wasted_kwh=100.0, co2_kg=90.0,
            payload_dict={},
        )
        runs = get_history("HistOrg")
        assert len(runs) >= 1
        assert runs[0]["org_name"] == "HistOrg"
        assert runs[0]["regen_score_before"] == 40.0

    def test_history_nonexistent_org_returns_empty(self):
        runs = get_history("OrgThatDoesNotExist_xyz123")
        assert runs == []


class TestHistoryEndpoint:
    def test_history_endpoint_empty_org(self):
        r = client.get("/history/NoSuchOrg_abc987")
        assert r.status_code == 200
        data = r.json()
        assert data["runs"] == []
        assert data["org_name"] == "NoSuchOrg_abc987"

    def test_history_endpoint_returns_saved_data(self):
        save_run(
            org_name="EndpointOrg", org_type="Factory",
            coverage_pct=100.0, confidence_pct=90.0,
            regen_before=65.0, regen_after=80.0,
            wasted_liters=800.0, wasted_kwh=200.0, co2_kg=180.0,
            payload_dict={},
        )
        r = client.get("/history/EndpointOrg")
        assert r.status_code == 200
        data = r.json()
        assert len(data["runs"]) >= 1
        assert data["runs"][0]["regen_score_before"] == 65.0
