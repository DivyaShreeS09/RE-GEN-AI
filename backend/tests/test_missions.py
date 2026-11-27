from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from main import app


def test_recovery_lifecycle(token_for):
    client = TestClient(app, headers={"Authorization": token_for("recovery")})
    admin = {"Authorization": token_for("recovery", "admin", "reviewer")}
    batch = dict(request_id=str(uuid4()), material="cartons", quantity_g=2000, condition="dry",
                 service_pin="600001", contaminated=False, goal="sell")
    service = dict(organization="Synthetic fixture", pathway="sell", material="cardboard", condition="dry",
                   service_pins=["600001"], minimum_g=500, capacity_g=3000, transfer="pickup",
                   expires=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat(), fees_paise=50,
                   quote_paise_per_kg=1000, identity_evidence="fixture-identity", consent_evidence="fixture-consent",
                   acceptance_evidence="fixture-acceptance")
    sid = client.post("/recovery/services", json=service).json()["id"]
    mission = client.post("/missions", json=batch).json()
    assert mission["state"] == "needs_evidence"
    mid = mission["id"]
    assert client.post("/missions", json=batch).json()["id"] == mid
    assert client.get(f"/missions/{mid}", headers={"Authorization": token_for("other")}).status_code == 404
    assert client.post(f"/recovery/services/{sid}/review", headers=admin,
                       json={"decision": "verified", "confirmation_ref": "fixture-review"}).status_code == 200
    path = f"/missions/{mid}/transitions"
    mission = client.post(path, json=dict(action="replan", version=1)).json()
    assert mission["result"]["options"][0]["net_paise"] == 1950
    directory = client.get("/recovery/opportunities").json()
    assert [item["id"] for item in directory] == [sid]
    assert directory[0]["quote_expires"] == service["expires"].replace("+00:00", "Z")
    assert "identity_evidence" not in directory[0] and "business_email" not in directory[0]
    assert client.get("/recovery/opportunities", headers={"Authorization": token_for("other")}).json() == []
    approval = dict(action="approve", version=2, service_id=sid)
    assert client.post(path, json=approval).status_code == 403
    assert client.post(path, json=approval, headers=admin).json()["state"] == "approved"
    assert client.post(path, json=approval, headers=admin).json()["version"] == 3
    assert client.post("/missions", json={**batch, "request_id": str(uuid4())}).json()["state"] == "needs_evidence"
    mission = client.post(path, json=dict(action="confirm_handover", version=3, accepted_g=1800,
                          receipt_ref="private-fixture", revenue_paise=1600), headers=admin).json()
    assert client.get("/passports/"+mission["passport"]).json() == {"state": "handover_confirmed", "accepted_g": 1800}
    assert client.post(f"/missions/{mid}/processing-evidence", json={"receipt_ref":"fixture-processor","processed_g":1700}, headers=admin).json()["result"]["processing_evidence"]["processed_g"] == 1700
    assert client.get(f"/missions/{mid}/passport.pdf").content.startswith(b"%PDF")
    assert client.post("/missions", json={**batch, "service_pin":"60000x"}).status_code == 422


def test_meter_ingestion(token_for):
    client = TestClient(app, headers={"Authorization": token_for("meters", "admin")})
    t = datetime.now(timezone.utc)-timedelta(hours=1)
    config = dict(metric="power", zone_id="fixture-floor", calibration_ref="fixture", interval_seconds=900,
                  calibration_due=(t+timedelta(days=1)).isoformat())
    device = client.post("/devices", json=config).json()
    path = "/devices/"+device["id"]
    headers = {"Authorization": "Bearer "+device["device_token"]}
    batch = [dict(timestamp=(t+timedelta(minutes=i*15)).isoformat(), unit="kW", value=v) for i,v in enumerate([2,4])]
    assert client.post(path+"/telemetry", json=batch).status_code == 401
    assert client.post(path+"/telemetry", json=batch, headers=headers).json()["inserted"] == 2
    assert client.post(path+"/telemetry", json=batch, headers=headers).json()["duplicates"] == 2
    assert client.post(path+"/telemetry", json=[{**batch[0],"value":3}], headers=headers).status_code == 409
    data = client.get(path+"/observations").json()
    assert data["zone_id"] == "fixture-floor" and data["readings"][1]["interval_total"] == 0.75
    assert client.get(path+"/observations", headers={"Authorization": token_for("other")}).status_code == 404


def test_collective_consent_volume_date_and_rejection(token_for):
    tenant = "collective-fixture"
    client = TestClient(app, headers={"Authorization": token_for(tenant)})
    admin = {"Authorization": token_for(tenant, "admin", "reviewer")}
    date = datetime.now(timezone.utc)+timedelta(days=2)
    service = dict(organization="Fixture cooperative", pathway="collective_recovery", material="paper", condition="dry",
                   service_pins=["600002"], minimum_g=1000, capacity_g=4000, transfer="pickup",
                   expires=date.isoformat(), identity_evidence="fixture", consent_evidence="fixture", acceptance_evidence="fixture")
    sid = client.post("/recovery/services", json=service).json()["id"]
    review = dict(decision="verified", confirmation_ref="fixture")
    assert client.post(f"/recovery/services/{sid}/review", json=review, headers=admin).status_code == 200
    def batch(material):
        return client.post("/missions", json=dict(request_id=str(uuid4()), material=material, quantity_g=550,
                           condition="dry", service_pin="600002", contaminated=False, collective_consent=True,
                           collection_date=date.date().isoformat())).json()
    first, second, mixed = [batch(x) for x in ("paper", "paper", "steel")]
    inventory = next(m for m in client.get("/missions").json() if m["id"] == first["id"])
    assert inventory["service_pin"] == "600002" and inventory["collective_consent"]
    assert inventory["canonical_material"] == "paper" and inventory["contaminated"] is False
    assert first["state"] == "needs_evidence"
    assert any(e["action"] == "find_collective" and e["candidates"][0]["mission_id"] == first["id"] for e in second["events"])
    def group(a,b):
        return client.post("/recovery/collectives", json={"mission_ids":[a["id"], b["id"]]}, headers=admin)
    assert group(first,mixed).status_code == 409
    collective = group(first,second).json()
    assert collective["inputs"]["quantity_g"] == 1100
    assert group(first,second).json()["id"] == collective["id"]
    assert group(first,batch("paper")).status_code == 409
    path = "/missions/"+collective["id"]+"/transitions"
    assert client.post(path, json=dict(version=1, action="approve", service_id=sid), headers=admin).status_code == 200
    assert client.post(path, json=dict(version=2, action="reject"), headers=admin).json()["state"] == "needs_evidence"
    assert client.post(path, json=dict(version=3, action="cancel"), headers=admin).json()["state"] == "cancelled"
    assert client.get("/missions/"+first["id"]).json()["state"] == "needs_evidence"


def test_symbiosis_and_expired_quote(token_for):
    client = TestClient(app, headers={"Authorization":token_for("symbiosis")})
    admin = {"Authorization":token_for("symbiosis","admin","reviewer")}
    current = datetime.now(timezone.utc)
    common = dict(organization="Fixture demand", material="cardboard", condition="dry", service_pins=["600003"],
                  minimum_g=10, capacity_g=5000, transfer="internal", expires=(current+timedelta(days=1)).isoformat(),
                  identity_evidence="fixture", consent_evidence="fixture", acceptance_evidence="fixture")
    for fields in [dict(pathway="sell", quote_paise_per_kg=100, quote_expires=(current-timedelta(hours=1)).isoformat()),
                   dict(pathway="industrial_symbiosis", avoided_purchase_paise=400)]:
        sid = client.post("/recovery/services", json={**common, **fields}).json()["id"]
        client.post(f"/recovery/services/{sid}/review", json={"decision":"verified","confirmation_ref":"fixture"}, headers=admin)
    result = client.post("/missions", json=dict(request_id=str(uuid4()), material="cartons", quantity_g=1000,
                         condition="dry", service_pin="600003", contaminated=False)).json()
    assert [m["pathway"] for m in result["result"]["options"]] == ["industrial_symbiosis"]
    assert client.get("/postal/600003").json()["status"] == "unmapped"


def test_counter_resets_gaps_and_transactional_batch(token_for):
    client = TestClient(app, headers={"Authorization":token_for("counter","admin")})
    t = datetime.now(timezone.utc)-timedelta(hours=5)
    device = client.post("/devices", json=dict(zone_id="fixture-room", metric="water_counter", interval_seconds=60,
                         calibration_ref="fixture", calibration_due=(t+timedelta(days=1)).isoformat())).json()
    path = "/devices/"+device["id"]
    headers = {"Authorization":"Bearer "+device["device_token"]}
    samples = [dict(timestamp=(t+timedelta(minutes=m)).isoformat(), value=v, unit="L")
               for m,v in [(0,10),(1,12),(2,1),(12,5)]]
    assert client.post(path+"/telemetry", json=[samples[0], {**samples[1],"unit":"kWh"}], headers=headers).status_code == 422
    assert client.get(path+"/observations").json()["readings"] == []
    assert client.post(path+"/telemetry", json=samples, headers=headers).status_code == 200
    readings = client.get(path+"/observations").json()
    assert readings["stale"] and readings["findings"] == []
    assert [r["quality"] for r in readings["readings"]] == ["initial","difference","counter_reset","gap"]


def test_checkpointed_goal_review_resumes_without_repeating_tools(token_for):
    client = TestClient(app, headers={"Authorization":token_for("goals")})
    rid = client.post("/analyze/upload", data={"manual_water_liters":10, "manual_water_period":"daily"}).json()["analysis_id"]
    body = {"goal":"resource_review","request_id":str(uuid4()),"analysis_id":rid}
    mid = client.post("/analysis-missions",json=body).json()["id"]
    step = {"version":1,"action":"advance"}
    path = f"/analysis-missions/{mid}/steps"
    assert client.post(path,json=step).json()["version"] == 2
    resumed = TestClient(app, headers={"Authorization":token_for("goals")})
    assert resumed.get("/missions/"+mid).json()["result"]["pending"] == ["energy"]
    assert resumed.post(path,json=step).json()["version"] == 2
    final = resumed.post(path,json={"version":2,"action":"advance"}).json()
    assert final["state"] == "no_feasible_action" and final["result"]["attempts"] == {"water":1,"energy":1}


def test_synchronized_balance_and_maintenance_evidence(token_for, monkeypatch):
    from core import telemetry
    t = datetime(2026, 2, 7, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(telemetry, "now", lambda:t)
    client = TestClient(app, headers={"Authorization":token_for("maintenance","admin")})
    config = dict(metric="water_counter", zone_id="fixture-building", calibration_ref="fixture", interval_seconds=3600,
                  calibration_due=(t+timedelta(days=10)).isoformat())
    parent = client.post("/devices", json=config).json()
    child = client.post("/devices", json={**config,"parent_device_id":parent["id"],"zone_id":"fixture-floor"}).json()
    start = t-timedelta(hours=99)
    def ingest_series(dev, values, begin):
        samples = [dict(value=v, unit="L", timestamp=(begin+timedelta(hours=i)).isoformat(), occupied=True, scheduled=True)
                   for i,v in enumerate(values)]
        return client.post("/devices/"+dev["id"]+"/telemetry", json=samples, headers={"Authorization":"Bearer "+dev["device_token"]})
    vals = list(range(97))+[106,116,126]
    assert ingest_series(parent,vals,start).status_code == 200
    assert ingest_series(child,[0.5*v for v in vals],start).status_code == 200
    path = "/devices/"+parent["id"]
    balance = client.get(path+"/balance").json()
    assert balance["residual"] == 5 and balance["uncertainty"] == 0.75
    evidence = client.get(path+"/observations").json()
    assert evidence["findings"][0]["zone_id"] == "fixture-building"
    order = client.post(path+"/work-orders").json()["id"]
    later = t+timedelta(days=1)
    monkeypatch.setattr(telemetry,"now",lambda:later)
    assert ingest_series(parent,list(range(127,151)),t+timedelta(hours=1)).status_code == 200
    reviewed = client.post("/work-orders/"+order+"/verify",json={"maintenance_ref":"fixture-inspection",
                           "completed_at":(t+timedelta(hours=1)).isoformat()})
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["measured_difference"] == 27


def test_mapped_device_import_previews_before_commit(token_for):
    client = TestClient(app, headers={"Authorization":token_for("imports","admin")})
    t = datetime.now(timezone.utc)-timedelta(minutes=10)
    device = client.post("/devices", json=dict(zone_id="fictional-zone",metric="energy_counter",
                         interval_seconds=60,calibration_ref="fixture",calibration_due=(t+timedelta(days=1)).isoformat())).json()
    path = "/devices/"+device["id"]
    files = {"file":("meter.csv", f"timestamp,measured,unit\n{t.isoformat()},23,kWh", "text/csv")}
    form = {"mapping":'{"measured":"value"}'}
    assert client.post(path+"/import",data=form,files=files).json()["rows"] == 1
    assert client.get(path+"/observations").json()["readings"] == []
    assert client.post(path+"/import",data={**form,"preview":"false"},files=files).json()["inserted"] == 1
    assert client.get(path+"/observations").json()["source"] == "staff_import"


def test_manual_review_evidence_photo_and_relay(token_for):
    from io import BytesIO
    from PIL import Image
    client = TestClient(app, headers={"Authorization":token_for("review")})
    admin = {"Authorization":token_for("review","admin")}
    picture = BytesIO()
    Image.new("RGB",(2,2)).save(picture,"PNG")
    photo = client.post("/recovery/photos", files={"file":("synthetic.png",picture.getvalue(),"image/png")}).json()["id"]
    assert client.get("/recovery/photos/"+photo, headers={"Authorization":token_for("other")}).status_code == 404
    assert client.get("/recovery/photos/"+photo).headers["content-type"] == "image/jpeg"
    source = dict(material="synthetic composite", source_document="Fixture guidance document",
                  review_question="Can facility staff confirm the supplier material label?",
                  expires=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())
    assert client.post("/recovery/guidance",json=source, headers=admin).status_code == 200
    batch = dict(request_id=str(uuid4()), material=source["material"], photo_id=photo, quantity_g=500, service_pin="600003",
                 condition="unknown", contaminated=False)
    mission = client.post("/missions",json=batch).json()
    assert mission["state"] == "manual_review" and source["source_document"] in mission["events"][-1]["reason"]
    relay = dict(mission_id=mission["id"],purpose="request_onboarding")
    assert client.post("/recovery/relay",json=relay).status_code == 403
    for _ in range(2):
        assert client.post("/recovery/relay",json=relay,headers=admin).json()["status"] == "queued_for_facility_review"
    assert len(client.get("/recovery/relay",headers=admin).json()) == 1


def test_reviewed_postal_import_preserves_provenance(tmp_path, token_for):
    from core.schema import import_postal
    path = tmp_path / "synthetic-postal.csv"
    path.write_text("pin,locality,source_document,reuse_permission,reviewer,publication_date,reviewed_date\n"
                    "600099,Synthetic locality,Fixture document,Test use only,Fixture reviewer,2024-01-01,2024-02-01\n")
    import_postal(path)
    client = TestClient(app, headers={"Authorization":token_for("postal")})
    assert client.get("/postal/600099").json() == {"pin":"600099","locality":"Synthetic locality","status":"reviewed",
                                                  "source_document":"Fixture document","publication_date":"2024-01-01"}


def test_analysis_mission_records_planner_provenance(token_for):
    client = TestClient(
        app,
        headers={"Authorization": token_for("planner-trace")},
    )

    response = client.post(
        "/analyze/upload",
        data={
            "manual_water_liters": 10,
            "manual_water_period": "daily",
        },
    )
    assert response.status_code == 200

    created = client.post(
        "/analysis-missions",
        json={
            "goal": "resource_review",
            "request_id": str(uuid4()),
            "analysis_id": response.json()["analysis_id"],
        },
    )
    assert created.status_code == 200

    identifier = created.json()["id"]
    path = f"/analysis-missions/{identifier}/steps"
    step = {"version": 1, "action": "advance"}

    advanced = client.post(path, json=step)
    assert advanced.status_code == 200

    mission = advanced.json()
    decision = mission["events"][-1]["evidence"]["planner"]

    assert decision["tool"] == "water"
    assert decision["source"] == "deterministic"
    assert decision["reason"]

    persisted = client.get("/missions/" + identifier).json()

    assert (
        persisted["events"][-1]["evidence"]["planner"]
        == decision
    )

    assert client.post(path, json=step).json() == mission
