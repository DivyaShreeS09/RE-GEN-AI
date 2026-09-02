"""Tests for device control simulation module (prompt 2.4)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient


class TestDeviceControlUnit:
    def test_known_action_returns_executed(self):
        from core.device_control import execute_action
        result = execute_action("W1")
        assert result["status"] == "executed"
        assert result["action_id"] == "W1"
        assert result["mode"] == "mock"
        assert "simulation_note" in result

    def test_unknown_action_returns_unknown(self):
        from core.device_control import execute_action
        result = execute_action("UNKNOWN_XYZ")
        assert result["status"] == "unknown_action"
        assert result["mode"] == "mock"

    def test_all_known_actions_execute(self):
        from core.device_control import execute_action, _KNOWN_ACTIONS
        for action_id in _KNOWN_ACTIONS:
            result = execute_action(action_id)
            assert result["status"] == "executed"
            assert result["action_id"] == action_id
            assert result["mode"] == "mock"


class TestDeviceControlEndpoint:
    @pytest.fixture
    def client(self):
        os.environ["RATELIMIT_ENABLED"] = "false"
        os.environ["DATABASE_URL"] = "sqlite:///./test_device.db"
        from main import app
        return TestClient(app)

    def test_execute_known_action(self, client, monkeypatch):
        monkeypatch.delenv("DEVICE_CONTROL_LIVE", raising=False)
        resp = client.post("/actions/W1/execute")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "executed"
        assert data["action_id"] == "W1"
        assert data["mode"] == "mock"

    def test_execute_unknown_action(self, client):
        resp = client.post("/actions/BOGUS/execute")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unknown_action"
