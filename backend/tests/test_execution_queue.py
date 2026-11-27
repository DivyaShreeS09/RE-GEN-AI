from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core import execution_queue as queue
from core.database import engine
from core.recovery import AnalysisStep, _analysis_step
from main import app


def investigation(token_for):
    tenant = "fixture-" + uuid4().hex
    client = TestClient(app, headers={"Authorization": token_for(tenant)})
    report = client.post("/analyze/upload", data={"manual_water_liters": 10, "manual_water_period": "daily"}).json()
    mission = client.post("/analysis-missions", json={"goal": "resource_review", "request_id": str(uuid4()),
                          "analysis_id": report["analysis_id"]}).json()
    path = "/analysis-missions/" + mission["id"] + "/queue"
    job = client.post(path).json()
    assert client.post(path).json()["id"] == job["id"]
    return tenant, client, mission, job


def test_concurrent_claim_takeover_and_checkpoints(token_for):
    tenant, client, mission, job = investigation(token_for)
    with ThreadPoolExecutor(2) as pool:
        claims = list(pool.map(lambda _: queue.claim_job(tenant, job["id"]), range(2)))
    assert claims.count(None) == 1
    claim = next(c for c in claims if c)
    old = queue.InvestigationLease(tenant, mission["id"], job["id"], claim["claim_token"])
    checkpoint = _analysis_step(mission["id"], AnalysisStep(version=1, action="advance"), old)
    with Session(engine) as db:
        db.get(queue.ExecutionJob, job["id"]).lease_until = "2000-01-01"
        db.commit()
    with pytest.raises(queue.LostLease):
        _analysis_step(mission["id"], AnalysisStep(version=checkpoint["version"], action="advance"), old)
    assert not queue.finish_job(tenant, job["id"], old.token, "completed")
    resumed = client.post("/execution-jobs/" + job["id"] + "/run")
    assert resumed.status_code == 200
    current = resumed.json()["mission"]
    assert current["state"] == "no_feasible_action"
    assert current["events"][:len(checkpoint["events"])] == checkpoint["events"]
    assert client.get("/execution-jobs/" + job["id"]).json()["attempts"] == 2


def test_cancel_fences_worker_and_hides_job_from_other_tenants(token_for):
    tenant, client, mission, job = investigation(token_for)
    path = "/execution-jobs/" + job["id"]
    other = {"Authorization": token_for("unrelated")}
    assert client.get(path, headers=other).status_code == 404
    assert client.post(path + "/run", headers=other).status_code == 409
    assert client.post(path + "/run", headers={"Authorization": token_for(tenant, "viewer")}).status_code == 403
    claim = queue.claim_job(tenant, job["id"])
    assert client.post("/analysis-missions/" + mission["id"] + "/steps",
                       json={"version": 1, "action": "cancel"}).json()["state"] == "cancelled"
    assert client.get(path).json()["status"] == "cancelled"
    assert not queue.finish_job(tenant, job["id"], claim["claim_token"], "completed")


def test_retry_exhaustion_clears_lease():
    with Session(engine) as db:
        job = queue.enqueue(db, "fixture-exhaustion", str(uuid4()), "fixture")
        db.commit()
    for expected in (1, 2, 3):
        claimed = queue.claim_job("fixture-exhaustion", job["id"])
        assert claimed["attempts"] == expected
        assert queue.finish_job("fixture-exhaustion", job["id"], claimed["claim_token"], "retry")
    assert queue.claim_job("fixture-exhaustion", job["id"]) is None
    with Session(engine) as db:
        row = db.get(queue.ExecutionJob, job["id"])
        assert row.status == "failed" and row.claim_token is None and row.lease_until is None


def test_mission_attempts_survive_failure_and_overlap(monkeypatch):
    from core import ai_client as ai
    from core.auth import Member
    from core.recovery import mission_inference

    member = Member("fixture-budget", "fixture", "staff")
    request = uuid4()
    monkeypatch.setattr(ai, "local_enabled", lambda: True)
    monkeypatch.setenv("REGEN_OLLAMA_MODEL", "fixture")
    attempts = []

    def unavailable(*args):
        attempts.append(1)
        raise RuntimeError("fixture outage")

    monkeypatch.setattr(ai, "_ollama", unavailable)
    with mission_inference(member, request_id=request):
        with mission_inference(member, request_id=request):
            assert ai.call_ai("overlapping", "fallback") == ("fallback", False)
        assert not attempts
        ai.call_ai("first")
    for step in range(4):
        token = ai._usage.set(0)
        try:
            with mission_inference(member, request_id=request):
                ai.call_ai(str(step))
        finally:
            ai._usage.reset(token)
    assert len(attempts) == 3

def test_local_identity_cannot_activate_in_production(monkeypatch):
    from fastapi import FastAPI
    from scripts.local_demo import register_session
    monkeypatch.setenv("REGEN_DEV_IDENTITY", "1")
    monkeypatch.setenv("REGEN_ENV", "production")
    with pytest.raises(RuntimeError):
        register_session(FastAPI(), None)
    assert TestClient(app, base_url="https://fixture").post("/dev/session").status_code == 404
