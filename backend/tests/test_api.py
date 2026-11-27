"""API smoke tests — verifies all public endpoints respond correctly."""
import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app


@pytest.fixture(autouse=True)
def authenticated_client(token_for, monkeypatch):
    monkeypatch.setitem(client.headers, "Authorization", token_for())


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_contains_status(self):
        r = client.get("/health")
        assert r.json()["status"] == "online"

    def test_health_contains_version(self):
        r = client.get("/health")
        assert "version" in r.json()


class TestWasteMaterialsEndpoint:
    def test_returns_200(self):
        r = client.get("/analyze/waste/materials")
        assert r.status_code == 200

    def test_returns_materials_list(self):
        r = client.get("/analyze/waste/materials")
        data = r.json()
        assert "materials" in data
        assert isinstance(data["materials"], list)
        assert len(data["materials"]) > 0

    def test_count_matches_list_length(self):
        r = client.get("/analyze/waste/materials")
        data = r.json()
        assert data["count"] == len(data["materials"])


class TestWasteAnalysisEndpoint:
    def test_valid_request_returns_200(self):
        r = client.post("/analyze/waste", json={"waste_type": "coconut shell", "quantity_kg": 50})
        assert r.status_code == 200

    def test_result_contains_expected_keys(self):
        r = client.post("/analyze/waste", json={"waste_type": "paper waste", "quantity_kg": 100})
        data = r.json()
        assert "waste_type" in data
        assert "recommended_pathway" in data
        assert "status" in data

    def test_zero_quantity_rejected(self):
        # quantity_kg has gt=0 — Pydantic rejects this before the handler runs (422)
        r = client.post("/analyze/waste", json={"waste_type": "plastic bottles", "quantity_kg": 0})
        assert r.status_code == 422

    def test_negative_quantity_rejected(self):
        r = client.post("/analyze/waste", json={"waste_type": "plastic bottles", "quantity_kg": -10})
        assert r.status_code == 422  # pydantic validation (gt=0)


class TestDemoDataEndpoint:
    def test_water_demo_csv(self):
        r = client.get("/demo-data/water")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")

    def test_energy_demo_csv(self):
        r = client.get("/demo-data/energy")
        assert r.status_code == 200

    def test_unknown_type_returns_404(self):
        r = client.get("/demo-data/unknown_type")
        assert r.status_code == 404


class TestUploadValidateEndpoint:
    def test_invalid_dataset_type_rejected(self):
        content = b"timestamp,usage\n2024-01-01,100"
        r = client.post(
            "/upload/validate",
            data={"dataset_type": "invalid_type"},
            files={"file": ("test.csv", content, "text/csv")},
        )
        assert r.status_code == 400

    def test_oversized_file_rejected(self):
        big_content = b"x" * (21 * 1024 * 1024)
        r = client.post(
            "/upload/validate",
            data={"dataset_type": "water"},
            files={"file": ("big.csv", big_content, "text/csv")},
        )
        assert r.status_code == 413

    def test_valid_water_csv_accepted(self):
        csv = b"timestamp,building_id,usage_liters\n2024-01-01 08:00,BldgA,500\n2024-01-01 09:00,BldgA,480"
        r = client.post(
            "/upload/validate",
            data={"dataset_type": "water"},
            files={"file": ("water.csv", csv, "text/csv")},
        )
        assert r.status_code == 200
        assert "record_count" in r.json()


class TestAnalyzeUploadOversizeRejection:
    def test_oversized_water_file_rejected(self):
        big = b"x" * (21 * 1024 * 1024)
        r = client.post(
            "/analyze/upload",
            data={"org_name": "Test Org", "org_type": "University"},
            files={"water_file": ("water.csv", big, "text/csv")},
        )
        assert r.status_code == 413

    def test_oversized_energy_file_rejected(self):
        big = b"x" * (21 * 1024 * 1024)
        r = client.post(
            "/analyze/upload",
            data={"org_name": "Test Org", "org_type": "University"},
            files={"energy_file": ("energy.csv", big, "text/csv")},
        )
        assert r.status_code == 413

@pytest.mark.parametrize("material,status", [("chemical waste", "analyzed"), ("unidentified plastic residue", "unknown_material")])
def test_unpriced_legacy_upload(material, status):
    response = client.post("/analyze/upload", data={"waste_type": material, "waste_quantity_kg": 3})
    assert response.status_code == 200, response.text
    waste = response.json()["waste"]
    assert waste["items"][0]["status"] == status
    assert waste["total_recovery_max_inr"] is None


def test_tenant_boundary(token_for):
    response = client.post("/analyze/upload", data={"waste_type": "paper", "waste_quantity_kg": 1})
    rid = response.json()["analysis_id"]
    other = {"Authorization": token_for("different-facility")}
    for suffix in ["audit-record", "audit-record.pdf"]:
        assert client.get(f"/report/{rid}/{suffix}", headers=other).status_code == 404
    assert client.get("/history/My%20Organization", headers=other).json()["runs"] == []
    assert TestClient(app).get("/history/My%20Organization").status_code == 401


def test_manual_measurement_preserves_period_total():
    response = client.post("/analyze/upload", data={"manual_water_liters": 125, "manual_water_period": "monthly"})
    assert response.status_code == 200, response.text
    water = response.json()["water"]
    assert water["total_consumption_liters"] == 125
    assert water["hourly_chart_data"] == []
    assert water["reporting_days"] == 30


def test_json_preview_mapping_and_invalid_units():
    response = client.post("/upload/validate", data={"dataset_type":"energy", "column_mapping":'{"load":"usage_kwh"}'},
                           files={"file":("values.json", b'[{"load":3}]', "application/json")})
    assert response.json()["total_kwh"] == 3
    response = client.post("/analyze/upload", files={"fuel_file":("fuel.csv", b"fuel_type,quantity_liters\ncng,5", "text/csv")})
    assert response.status_code == 422


def test_explicit_role_and_invalid_token(token_for):
    for token, code in [("Bearer invalid", 401), (token_for(role="viewer"), 403)]:
        response = client.post("/analyze/waste", headers={"Authorization":token}, json={"waste_type":"paper","quantity_kg":1})
        assert response.status_code == code


def test_facility_tariff_requires_source_and_preserves_zero():
    fields = {"manual_water_liters":120,"manual_water_period":"daily","water_inr_per_litre":"0"}
    assert client.post("/analyze/upload",data=fields).status_code == 422
    result = client.post("/analyze/upload",data={**fields,"tariff_reference":"fixture invoice"}).json()
    assert result["water"]["tariff"] == {"inr_per_unit":0,"unit":"L","basis":"fixture invoice"}
    assert result["decision"]["ranked_actions"][0]["roi"]["tariff"] == result["water"]["tariff"]


def test_rate_limit_enforced_when_enabled(monkeypatch):
    from main import limiter
    monkeypatch.setattr(limiter, "enabled", True)
    limiter.reset()
    try:
        codes = [client.post("/analyze/waste",json={"waste_type":"cartons","quantity_kg":1}).status_code for _ in range(11)]
        assert codes == [200]*10 + [429]
    finally:
        limiter.reset()


def test_legacy_interval_adapter_converts_units_and_preserves_hour():
    from core.data_processor import validate_energy_df
    import pandas as pd
    frame = pd.DataFrame([{"date":"2026-01-01","hour":8,"usage_kwh":250,"unit":"Wh"}])
    normalized, info = validate_energy_df(frame)
    assert info["valid"] and normalized.iloc[0]["usage_kwh"] == 0.25
    assert "02:30:00" in normalized.iloc[0]["timestamp"]


def test_unregistered_file_rejects_conflicting_device_instants():
    import pandas as pd
    from core.data_processor import validate_water_df
    sample = {"date":"2026-01-01T08:00:00+05:30","meter_id":"fixture","usage_liters":4}
    _, info = validate_water_df(pd.DataFrame([sample,{**sample,"usage_liters":5}]))
    assert not info["valid"] and "device timestamp" in str(info["errors"])
    _, info = validate_water_df(pd.DataFrame([sample,{**sample,"meter_id":"second-fixture"}]))
    assert info["valid"]

def test_joint_csv_upload_retains_evidence_and_separates_recovery_from_utility_savings(token_for):
    from pathlib import Path
    from agents.decision_agent import generate_decisions

    folder = Path(__file__).resolve().parents[1] / "data"
    tenant = "joint-upload-regression"
    api = TestClient(app, headers={"Authorization":token_for(tenant)})
    with (folder / "water_usage.csv").open("rb") as water, (folder / "energy_usage.csv").open("rb") as energy:
        response = api.post("/analyze/upload", files={
            "water_file": ("water.csv", water, "text/csv"), "energy_file": ("energy.csv", energy, "text/csv")})
    assert response.status_code == 200
    uploaded = response.json()
    assert uploaded["water"]["status"] == uploaded["energy"]["status"] == "analyzed"
    assert uploaded["water"]["total_consumption_liters"] > 0
    assert uploaded["energy"]["total_consumption_kwh"] > 0
    assert uploaded["report"]["silent_losses"]["waste_hidden_value_inr"] is None

    water, energy = uploaded["water"], uploaded["energy"]
    reference = {"status":"analyzed","quantity_kg":5,"estimated_recovery":{"max_inr":100}}
    comparison = generate_decisions(water, energy, reference)
    waste = next(action for action in comparison["ranked_actions"] if action["domain"] == "Waste")
    assert waste["cost_saving_inr"] is None and waste["indicative_recovery_inr"] == 100
    assert comparison["total_potential_saving_inr"] == generate_decisions(water, energy)["total_potential_saving_inr"]
