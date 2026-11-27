"""Post-implementation checks using only isolated local fixtures."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def recovery(token_for):
    tenant = str(uuid4())
    client = TestClient(app, headers={"Authorization": token_for(tenant)})
    admin = {"Authorization": token_for(tenant, "admin", "fixture-reviewer")}
    today = datetime.now(timezone.utc)
    batch = dict(request_id=str(uuid4()), material="cartons", quantity_g=1000, goal="sell",
                 service_pin="600001", condition="dry", contaminated=False,
                 collection_date=(today + timedelta(days=3)).date().isoformat())

    def offer(pathway, **fields):
        service = dict(organization="Synthetic audit fixture", pathway=pathway, material="cardboard",
                       condition="dry", service_pins=["600001"], minimum_g=1, capacity_g=2000,
                       transfer="pickup", expires=(today + timedelta(days=10)).isoformat(),
                       identity_evidence="fixture", acceptance_evidence="fixture", consent_evidence="fixture")
        response = client.post("/recovery/services", json={**service, **fields})
        assert response.status_code == 201
        sid = response.json()["id"]
        assert client.post(f"/recovery/services/{sid}/review", headers=admin,
                           json={"decision":"verified", "confirmation_ref":"fixture"}).status_code == 200
        return sid

    return client, admin, batch, offer


def test_quote_must_cover_collection_day(recovery):
    client, _, batch, offer = recovery
    offer("sell", quote_paise_per_kg=100, quote_expires=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())
    assert client.post("/missions", json=batch).json()["result"]["options"] == []


def test_retry_filters_revoked_service(recovery):
    client, admin, batch, offer = recovery
    sid = offer("reuse")
    first = client.post("/missions", json=batch).json()
    assert first["result"]["options"]
    assert client.post(f"/recovery/services/{sid}/review", headers=admin,
                       json={"decision":"revoked", "confirmation_ref":"fixture"}).status_code == 200
    current = client.get("/missions/"+first["id"]).json()
    assert current["result"]["options"] == []
    assert client.post("/missions", json=batch).json() == current


def test_competing_options_and_rejected_offer(recovery):
    client, admin, batch, offer = recovery
    sale = offer("sell", quote_paise_per_kg=2000, fees_paise=150, transport_paise=50)
    offer("reuse", avoided_purchase_paise=1000)
    offer("donate", effort="low")
    offer("recycling", effort="high")
    mission = client.post("/missions", json={**batch, "preferred_effort":"moderate"}).json()
    matches = mission["result"]["options"]
    assert [m["pathway"] for m in matches] == ["sell", "donate", "reuse"]
    assert matches[0]["net_paise"] == 1800
    path = "/missions/"+mission["id"]+"/transitions"
    assert client.post(path, headers=admin, json={"action":"approve","version":1,"service_id":sale}).status_code == 200
    replanned = client.post(path, headers=admin, json={"action":"reject","version":2}).json()
    assert [m["pathway"] for m in replanned["result"]["options"]] == ["donate", "reuse"]


def test_unseen_and_mixed_inventory(recovery):
    from agents.waste_agent import analyze_waste_batch
    client, _, batch, _ = recovery
    unfamiliar = "quilted foil bonded to woven fibre audit fixture"
    mission = client.post("/missions", json={**batch, "material":unfamiliar}).json()
    assert mission["state"] == "manual_review" and not mission["result"]["options"]
    missing = {k:v for k,v in batch.items() if k != "quantity_g"}
    assert client.post("/missions", json=missing).status_code == 422
    result = analyze_waste_batch([{"type":"cartons","quantity_kg":1},{"type":unfamiliar,"quantity_kg":4}])
    assert (result["total_kg"], result["priced_mass_kg"], result["analyzed_items"]) == (5,1,1)
    assert result["items"][1]["estimated_recovery"] is None


def test_old_meter_file_rejected_in_preview_and_commit(token_for):
    client = TestClient(app, headers={"Authorization": token_for("audit-meter", "admin")})
    t = datetime.now(timezone.utc)
    device = client.post("/devices", json=dict(metric="power", zone_id="fixture-room", interval_seconds=60,
                         calibration_ref="fixture", calibration_due=(t+timedelta(days=1)).isoformat())).json()
    path = "/devices/"+device["id"]
    assert client.get(path+"/observations").json()["findings"] == []
    assert client.get(path+"/balance").json()["available"] is False
    files = {"file":("input.csv", f"timestamp,value,unit\n{(t-timedelta(days=31)).isoformat()},3,kW","text/csv")}
    assert [client.post(path+"/import", data={"preview":flag}, files=files).status_code
            for flag in ("true","false")] == [422,422]


def test_mock_provider_chain_reports_local_success(monkeypatch):
    from core import ai_client as ai
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_AI_PROVIDER", "ollama")
    monkeypatch.setenv("REGEN_OLLAMA_MODEL", "fixture-local")
    monkeypatch.setattr(ai, "cloud_enabled", lambda: False)
    monkeypatch.setattr(ai, "_ollama", lambda prompt, model: "fixture answer")
    token = ai._tenant.set("fixture-local")
    try:
        assert ai.call_ai("fixture local status") == ("fixture answer", True)
        assert ai.ai_status()["provider"] == "Ollama" and ai.ai_status()["available"]
    finally:
        ai._tenant.reset(token)
        ai._last_provider.set(None)

def test_new_offer_needs_replan_before_approval(recovery):
    client, admin, batch, offer = recovery
    offer("reuse")
    mission = client.post("/missions", json=batch).json()
    later = offer("donate")
    path = "/missions/"+mission["id"]+"/transitions"
    assert client.post(path, headers=admin, json={"action":"approve","version":1,"service_id":later}).status_code == 409
    assert client.post(path, headers=admin, json={"action":"replan","version":1}).json()["version"] == 2
    assert client.post(path, headers=admin, json={"action":"approve","version":2,"service_id":later}).status_code == 200


def test_storage_tool_outage_preserves_checkpoint(token_for, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from core import recovery as workflow
    client = TestClient(app, headers={"Authorization":token_for("audit-tool")})
    rid = client.post("/analyze/upload", data={"manual_water_liters":12,"manual_water_period":"daily"}).json()["analysis_id"]
    mission = client.post("/analysis-missions", json={"analysis_id":rid,"goal":"water","request_id":str(uuid4())}).json()
    step = {"version":1,"action":"advance"}
    path = "/analysis-missions/"+mission["id"]+"/steps"

    def unavailable(*args, **kwargs):
        raise OperationalError(None, None, RuntimeError("fixture storage outage"))

    with monkeypatch.context() as scoped:
        scoped.setattr(workflow, "get_run_by_id", unavailable)
        assert client.post(path, json=step).status_code == 503
        assert client.get("/missions/"+mission["id"]).json() == mission
    assert client.post(path, json=step).json()["state"] == "no_feasible_action"


def test_both_mock_providers_unavailable(monkeypatch):
    from core import ai_client as ai
    calls = []

    def failing(name):
        def call(*args):
            calls.append(name)
            raise RuntimeError("fixture provider unavailable")
        return call

    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_AI_PROVIDER", "auto")
    monkeypatch.setenv("REGEN_OLLAMA_MODEL", "fixture-local")
    monkeypatch.setattr(ai, "cloud_enabled", lambda: True)
    monkeypatch.setattr(ai, "_provider", failing("Gemini"))
    monkeypatch.setattr(ai, "_ollama", failing("Ollama"))
    tenant = ai._tenant.set("fixture-unavailable")
    try:
        assert ai.call_ai("two unavailable fixtures", "local rule") == ("local rule", False)
        assert calls == ["Gemini", "Ollama"]
        assert ai.ai_status()["provider"] is None and ai.ai_status()["attempts"] == 2
    finally:
        ai._tenant.reset(tenant)

@pytest.mark.parametrize("filename,content", [("meter.xlsx", b"ordinary text"), ("meter.csv", b'value,unit\n"unfinished')])
def test_invalid_meter_file_returns_client_error(token_for, filename, content):
    client = TestClient(app, headers={"Authorization": token_for("fixture-format","admin")}, raise_server_exceptions=False)
    device = client.post("/devices", json=dict(metric="power", zone_id="fixture", interval_seconds=60,
                         calibration_ref="fixture", calibration_due=datetime.now(timezone.utc).isoformat())).json()
    assert client.post("/devices/"+device["id"]+"/import", files={"file":(filename,content)}).status_code == 422

def test_decline_proposed_quote_before_reservation(recovery, token_for):
    client, admin, batch, offer = recovery
    sale = offer("sell", quote_paise_per_kg=2000)
    donation = offer("donate")
    mission = client.post("/missions", json=batch).json()
    path = "/missions/"+mission["id"]+"/transitions"
    decline = {"action":"reject", "version":1, "service_id":sale}
    assert client.post(path, headers={"Authorization":token_for("outside-fixture","admin")}, json=decline).status_code == 404
    response = client.post(path, headers=admin, json=decline)
    assert response.status_code == 200
    assert [m["service_id"] for m in response.json()["result"]["options"]] == [donation]
    assert client.post(path, headers=admin, json=decline).json()["version"] == 2
    other = client.post("/missions", json={**batch, "request_id":str(uuid4()), "quantity_g":2000}).json()
    option = next(m for m in other["result"]["options"] if m["service_id"] == sale)
    assert option["outcome_count"] == 0


def test_resumable_non_catalogue_classification(recovery, token_for):
    client, admin, batch, offer = recovery
    service = offer("repair", material="fixture moulded insert", preparation="Keep original packing")
    initial = {**batch, "material":"labelled insert bonded to backing"}
    mission = client.post("/missions", json=initial).json()
    assert mission["state"] == "manual_review" and mission["result"]["clarification"]["issue"] == "separation"
    assert "directory_search" not in [e["action"] for e in mission["events"]]
    path = "/missions/"+mission["id"]+"/clarifications"
    lot = dict(material="fixture moulded insert", quantity_g=1000, condition="dry", contaminated=False)
    answer = dict(version=1, disposition="identified", answer="Whole intact insert identified by staff",
                  evidence_ref="fixture supplier record", lots=[lot])
    assert client.post(path, json=answer).status_code == 403
    assert client.post(path, headers={"Authorization":token_for("other","admin")}, json=answer).status_code == 404
    final = client.post(path, headers=admin, json=answer).json()
    assert final["id"] == mission["id"] and final["result"]["options"][0]["service_id"] == service
    assert final["result"]["options"][0]["net_paise"] is None
    assert final["result"]["review"]["question"] == mission["result"]["clarification"]
    assert client.post(path, headers=admin, json=answer).json() == final
    assert client.post("/missions", json=initial).json() == final
    assert client.post("/missions", json={**initial,"request_id":str(uuid4())}).json()["state"] == "manual_review"


def test_weighed_inventory_mass_balance_and_unresolved_review(recovery):
    client, admin, batch, offer = recovery
    offer("reuse")
    mission = client.post("/missions", json={**batch,"mixed_inventory":True}).json()
    path = "/missions/"+mission["id"]+"/clarifications"
    lot = dict(material="cartons", quantity_g=400, condition="dry", contaminated=False)
    body = dict(version=1, disposition="separate_lots", answer="Separated weighed lots",
                evidence_ref="fixture scale record", lots=[lot,{**lot,"material":"paper"}])
    assert client.post(path, headers=admin,json=body).status_code == 422
    body["lots"][1]["quantity_g"] = 600
    grouped = client.post(path, headers=admin,json=body).json()
    assert grouped["state"] == "inventory_split"
    assert client.post(path, headers=admin,json=body).json() == grouped
    children = [client.get("/missions/"+l["id"]).json() for l in grouped["result"]["lots"]]
    assert [c["state"] for c in children] == ["awaiting_approval","needs_evidence"]
    unresolved = client.post("/missions",json={**batch,"request_id":str(uuid4()),"material":"unmarked sheet"}).json()
    result = client.post("/missions/"+unresolved["id"]+"/clarifications", headers=admin,
                         json={**body,"disposition":"unresolved","lots":[]}).json()
    assert result["state"] == "professional_review" and not result["result"]["options"]


def test_publication_requires_separate_current_consent(recovery, token_for, monkeypatch):
    from core import recovery as r
    client, admin, _, offer = recovery
    sid = offer("donate", publication_consent=True, business_email="office@example.invalid")
    path = "/recovery/directory/600001"
    assert client.get(path).json() == []
    review = dict(decision="verified", confirmation_ref="fixture service confirmation",
                  publication_ref="fixture authorized departmental mailbox",
                  verification_expires=(r.now()+timedelta(hours=1)).isoformat())
    client.post(f"/recovery/services/{sid}/review",headers=admin,json=review).raise_for_status()
    assert client.get(path).json()[0]["business_email"] == "office@example.invalid"
    assert client.get(path,headers={"Authorization":token_for("other")}).json() == []
    with monkeypatch.context() as scoped:
        later = r.now()+timedelta(hours=2)
        scoped.setattr(r,"now",lambda:later)
        assert client.get(path).json() == []
    client.delete(f"/recovery/services/{sid}/publication").raise_for_status()
    assert client.get(path).json() == []


def test_schema_validated_provider_fallback_and_offline_gate(monkeypatch):
    from core import ai_client as ai
    from core.recovery import Interpretation
    from unittest.mock import MagicMock
    monkeypatch.setenv("REGEN_AI_PROVIDER","offline")
    monkeypatch.setenv("REGEN_GROQ_MODEL","fixture-alternative")
    monkeypatch.setenv("REGEN_ENV","development")
    monkeypatch.delenv("REGEN_OLLAMA_MODEL",raising=False)
    alternative = MagicMock(return_value='{"issue":"condition","evidence":["tray"]}')
    monkeypatch.setattr(ai,"_alternative",alternative)
    tenant_context = ai._tenant.set("fixture-schema")
    consent = ai._cloud_consent.set(True)
    try:
        assert ai.call_ai("tray","offline",schema=Interpretation) == ("offline",False)
        alternative.assert_not_called()
        monkeypatch.setenv("REGEN_ENV","production")
        monkeypatch.setenv("REGEN_AI_PROVIDER","auto")
        monkeypatch.setenv("GEMINI_API_KEY","fixture-only")
        monkeypatch.setenv("GROQ_API_KEY","fixture-only")
        fake = MagicMock()
        fake.models.generate_content.return_value.text = '{"price":123}'
        fake.models.generate_content.return_value.candidates = []
        monkeypatch.setattr(ai,"_provider",lambda:fake)
        result, used = ai.call_ai("tray","offline",schema=Interpretation)
        assert used and Interpretation.model_validate_json(result).evidence == ["tray"]
        assert ai.ai_status()["provider"] == "Groq"
        alternative.assert_called_once()
    finally:
        ai._cloud_consent.reset(consent)
        ai._tenant.reset(tenant_context)


def test_unavailable_service_replans_without_reservation(recovery):
    client, admin, batch, offer = recovery
    first, second = offer("reuse"), offer("donate")
    mission = client.post("/missions",json=batch).json()
    client.post(f"/recovery/services/{first}/review",headers=admin,
                json={"decision":"revoked","confirmation_ref":"fixture"}).raise_for_status()
    body = dict(version=1,action="approve",service_id=first)
    path = "/missions/"+mission["id"]+"/transitions"
    final = client.post(path,headers=admin,json=body).json()
    assert final["events"][-1]["action"] == "replan"
    assert [m["service_id"] for m in final["result"]["options"]] == [second]
    assert client.post(path,headers=admin,json=body).json()["version"] == 2


def test_meter_equivalent_units_raw_evidence_and_cost(token_for):
    client = TestClient(app, headers={"Authorization":token_for("unit-fixture","admin")})
    current = datetime.now(timezone.utc)
    device = client.post("/devices",json=dict(zone_id="fixture-room",metric="power",calibration_ref="fixture",
                         calibration_due=(current+timedelta(days=1)).isoformat(),interval_seconds=60,
                         tariff_paise_per_unit=600,tariff_source="fixture invoice")).json()
    base = "/devices/"+device["id"]
    sample = dict(timestamp=(current-timedelta(minutes=1)).isoformat(),value=1000,unit="W",equipment_on=True)
    client.post(base+"/manual",json=sample).raise_for_status()
    assert client.post(base+"/manual",json={**sample,"unit":"kW","value":1}).json()["duplicates"] == 1
    client.post(base+"/manual",json={**sample,"timestamp":current.isoformat()}).raise_for_status()
    series = client.get(base+"/observations").json()
    assert series["tariff_source"] == "fixture invoice"
    last = series["readings"][-1]
    assert last["unit"] == "kW" and last["value"] == 1 and last["cost_paise"] == 10
    assert last["context"]["original_unit"] == "W"


def test_evidence_selected_meter_and_retry(token_for, monkeypatch):
    from core import recovery
    from sqlalchemy.exc import OperationalError
    client = TestClient(app, headers={"Authorization":token_for("fixture-plan","admin")})
    run = client.post("/analyze/upload",data={"manual_water_liters":12,"manual_water_period":"daily"}).json()
    device = client.post("/devices",json=dict(zone_id="fixture",metric="water_counter",interval_seconds=60,
                         calibration_ref="fixture",calibration_due=datetime.now(timezone.utc).isoformat())).json()
    goal = dict(analysis_id=run["analysis_id"],device_id=device["id"],request_id=str(uuid4()),goal="water")
    assert client.post("/analysis-missions",json={**goal,"goal":"energy"}).status_code == 422
    mission = client.post("/analysis-missions",json=goal).json()
    assert mission["result"]["pending"] == ["meter","water"]
    path = "/analysis-missions/"+mission["id"]+"/steps"
    first = client.post(path,json={"action":"advance","version":1}).json()
    assert first["result"]["meter_evidence"]["stale"] and not first["result"]["findings"]
    original = recovery.get_run_by_id
    attempts = []
    def recover(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise OperationalError(None,None,RuntimeError("fixture transient read"))
        return original(*args,**kwargs)
    monkeypatch.setattr(recovery,"get_run_by_id",recover)
    step = {"action":"advance","version":2}
    final = client.post(path,json=step).json()
    assert final["state"] == "no_feasible_action" and final["events"][-1]["evidence"]["read_retries"] == 1
    assert client.post(path,json=step).json() == final and len(attempts) == 2


def test_terminal_retention_preserves_open_missions(recovery):
    from core import schema
    from core.recovery import Mission, Session, engine
    client, _, batch, _ = recovery
    closed = client.post("/missions",json=batch).json()["id"]
    opened = client.post("/missions",json={**batch,"request_id":str(uuid4())}).json()["id"]
    client.post("/missions/"+closed+"/transitions",json={"action":"cancel","version":1}).raise_for_status()
    with Session(engine) as db:
        row = db.get(Mission,closed)
        row.events = [{**row.events[-1],"at":(datetime.now(timezone.utc)-timedelta(days=31)).isoformat()}]
        db.commit()
    assert schema.expire_records(30)["terminal_missions"] >= 1
    assert client.get("/missions/"+closed).status_code == 200
    schema.expire_records(30,apply=True)
    assert client.get("/missions/"+closed).status_code == 404 and client.get("/missions/"+opened).status_code == 200


def test_unsafe_review_stays_with_authorized_services(recovery):
    client, admin, batch, offer = recovery
    offer("reuse")
    disposal = offer("authorized_disposal",regulatory_evidence="fixture authorization")
    mission = client.post("/missions",json={**batch,"contaminated":True}).json()
    assert mission["state"] == "manual_review"
    body = dict(version=1,disposition="identified",answer="Facility reviewed contamination",
                evidence_ref="fixture safety review",lots=[dict(material="cartons",quantity_g=1000,
                condition="dry",contaminated=False)])
    final = client.post("/missions/"+mission["id"]+"/clarifications",headers=admin,json=body).json()
    assert final["inputs"]["contaminated"] and [m["service_id"] for m in final["result"]["options"]] == [disposal]


def test_upload_milestones_are_visible_before_report_finishes(token_for, monkeypatch):
    from threading import Event
    from concurrent.futures import ThreadPoolExecutor
    import main
    client = TestClient(app, headers={"Authorization":token_for("upload-progress")})
    mid = str(uuid4())
    marker, release = Event(), Event()
    original = main.generate_report
    def held_report(*args, **kwargs):
        marker.set()
        assert release.wait(8)
        return original(*args,**kwargs)
    monkeypatch.setattr(main,"generate_report",held_report)
    data = {"manual_water_liters":12,"manual_water_period":"daily","upload_mission_id":mid}
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(client.post,"/analyze/upload",data=data)
        try:
            assert marker.wait(8)
            snapshot = client.get("/missions/"+mid).json()
            assert snapshot["state"] == "processing"
            assert any(e["agent"] == "Water Leakage Agent" and e["action"] == "analyzed" for e in snapshot["events"])
            assert not any(e["action"] == "analysis_saved" for e in snapshot["events"])
            assert client.get("/missions/"+mid,headers={"Authorization":token_for("outside")}).status_code == 404
        finally:
            release.set()
        result.result().raise_for_status()
    assert client.get("/missions/"+mid).json()["state"] == "completed"
    assert client.post("/analyze/upload",data=data).status_code == 409
    failed = str(uuid4())
    assert client.post("/analyze/upload",data={"upload_mission_id":failed}).status_code == 422
    assert client.get("/missions/"+failed).json()["state"] == "failed"

def test_changed_quote_requires_new_approval(recovery):
    from sqlalchemy.orm import Session
    from core.recovery import Directory, engine
    client, admin, batch, offer = recovery
    sid = offer("sell", quote_paise_per_kg=500)
    mission = client.post("/missions", json=batch).json()
    with Session(engine) as db:
        row = db.get(Directory, sid)
        row.details = {**row.details, "quote_paise_per_kg": 200}
        db.commit()
    updated = client.post("/missions/" + mission["id"] + "/transitions", headers=admin,
                          json={"action":"approve", "version":1, "service_id":sid}).json()
    assert updated["state"] == "awaiting_approval"
    assert updated["result"]["options"][0]["net_paise"] == 200
    with Session(engine) as db:
        assert db.get(Directory, sid).remaining_g == 2000

def test_collection_window_and_documented_costs(recovery):
    client, _, batch, offer = recovery
    offer("industrial_symbiosis", collection_start=batch["collection_date"], collection_end=batch["collection_date"],
          quote_paise_per_kg=1000, collection_paise=100, fees_paise=10, preparation_paise=20, transport_paise=30)
    match = client.post("/missions", json=batch).json()["result"]["options"][0]
    assert match["gross_paise"] == 1000 and match["net_paise"] == 840
    for day in (None, datetime.now(timezone.utc).date().isoformat()):
        record = client.post("/missions", json={**batch, "request_id":str(uuid4()), "collection_date":day}).json()
        assert record["state"] == "needs_evidence"
