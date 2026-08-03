"""API smoke tests — verifies all public endpoints respond correctly."""
import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

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
