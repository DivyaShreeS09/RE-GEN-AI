"""Tests for SQLite persistence: save_run, get_history, and /history endpoint."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.database import save_run, get_history, Base, engine

Base.metadata.create_all(engine)  # idempotent: ensures tables exist

from fastapi.testclient import TestClient
from main import app

import pytest


@pytest.fixture(autouse=True)
def authenticated_client(token_for, monkeypatch):
    monkeypatch.setitem(client.headers, "Authorization", token_for())


client = TestClient(app)


class TestSaveAndHistory:
    def test_save_run_returns_int_id(self):
        rid = save_run(
            org_name="TestCorp", org_type="University",
            coverage_pct=80.0, confidence_pct=75.0,
            regen_before=55.0, regen_after=72.0,
            wasted_liters=1200.0, wasted_kwh=340.0, co2_kg=300.0,
            tenant="fixture", payload_dict={"test": True},
        )
        assert isinstance(rid, int) and rid > 0

    def test_get_history_returns_saved_row(self):
        save_run(
            org_name="HistOrg", org_type="Hospital",
            coverage_pct=60.0, confidence_pct=70.0,
            regen_before=40.0, regen_after=60.0,
            wasted_liters=500.0, wasted_kwh=100.0, co2_kg=90.0,
            tenant="fixture", payload_dict={},
        )
        runs = get_history("HistOrg", tenant="fixture")
        assert len(runs) >= 1
        assert runs[0]["org_name"] == "HistOrg"
        assert runs[0]["regen_score_before"] == 40.0

    def test_history_nonexistent_org_returns_empty(self):
        runs = get_history("OrgThatDoesNotExist_xyz123", tenant="fixture")
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
            tenant="fixture", payload_dict={},
        )
        r = client.get("/history/EndpointOrg")
        assert r.status_code == 200
        data = r.json()
        assert len(data["runs"]) >= 1
        assert data["runs"][0]["regen_score_before"] == 65.0


def test_revision_one_preserves_unassigned_legacy_analysis():
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from core.database import AnalysisRun, RunOwner
    from core.schema import SchemaRevision, upgrade
    legacy = create_engine("sqlite://")
    AnalysisRun.__table__.create(legacy)
    with Session(legacy) as db:
        old = AnalysisRun(org_name="Synthetic legacy facility", org_type="University", payload="{}")
        db.add(old)
        db.commit()
        identifier = old.id
    upgrade(legacy)
    upgrade(legacy)
    with Session(legacy) as db:
        assert db.get(AnalysisRun, identifier).org_name == "Synthetic legacy facility"
        assert db.get(RunOwner, identifier) is None
        assert db.scalars(select(SchemaRevision.version)).all() == [3]
        from sqlalchemy import inspect
        assert inspect(legacy).has_table("execution_jobs")
    legacy.dispose()

def test_upgrade_revision_one_and_restore_synthetic_backup(tmp_path):
    import sqlite3
    from sqlalchemy import create_engine, inspect
    from core.schema import SchemaRevision, upgrade
    source, restored = (tmp_path / name for name in ("fixture.db", "restored.db"))
    target = create_engine(f"sqlite:///{source}")
    SchemaRevision.__table__.create(target)
    with target.begin() as conn:
        conn.execute(SchemaRevision.__table__.insert().values(version=1))
        conn.exec_driver_sql("CREATE TABLE fixture_marker (id INTEGER PRIMARY KEY)")
        conn.exec_driver_sql("INSERT INTO fixture_marker VALUES (19)")
    upgrade(target)
    target.dispose()
    with sqlite3.connect(source) as src, sqlite3.connect(restored) as dst:
        src.backup(dst)
    target = create_engine(f"sqlite:///{restored}")
    upgrade(target)
    with target.connect() as conn:
        assert conn.exec_driver_sql("SELECT id FROM fixture_marker").scalar_one() == 19
        assert conn.exec_driver_sql("SELECT version FROM regen_schema_revision").scalar_one() == 3
        assert inspect(conn).has_table("execution_jobs")
        assert inspect(conn).has_table("mission_inference_budgets")
    target.dispose()
