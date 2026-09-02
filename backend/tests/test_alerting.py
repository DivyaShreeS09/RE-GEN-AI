"""Tests for Slack alerting module (prompt 2.3)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


def _water(severity):
    return {"severity": severity, "total_wasted_liters": 1200.0, "total_anomaly_readings": 5}


def _energy(severity):
    return {"severity": severity, "total_wasted_kwh": 250.0, "estimated_cost_inr": 2000.0}


class TestAlerting:
    def test_no_webhook_returns_false(self, monkeypatch):
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        from core.alerting import send_alert
        assert send_alert(_water("critical"), _energy("none"), "TestOrg", 1) is False

    def test_non_critical_returns_false(self, monkeypatch):
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        from core.alerting import send_alert
        assert send_alert(_water("low"), _energy("medium"), "TestOrg", 2) is False

    def test_critical_water_posts_to_webhook(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/fake")
        import urllib.request, json
        captured = {}
        class FakeResp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): pass
        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=5: (captured.__setitem__("body", json.loads(req.data.decode())), FakeResp())[1])
        from core import alerting
        monkeypatch.setattr(alerting, "_get_webhook", lambda: "https://hooks.slack.com/fake")
        result = alerting.send_alert(_water("critical"), _energy("none"), "TestOrg", 42)
        assert result is True
        assert "TestOrg" in captured["body"]["text"]
        assert "CRITICAL" in captured["body"]["text"]

    def test_high_energy_alert_included(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/fake")
        import urllib.request, json
        captured = {}
        class FakeResp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): pass
        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=5: (captured.__setitem__("body", json.loads(req.data.decode())), FakeResp())[1])
        from core import alerting
        monkeypatch.setattr(alerting, "_get_webhook", lambda: "https://hooks.slack.com/fake")
        result = alerting.send_alert(_water("none"), _energy("high"), "TestOrg", 7)
        assert result is True
        assert "Energy" in captured["body"]["text"]
        assert "HIGH" in captured["body"]["text"]

    def test_url_error_returns_false(self, monkeypatch):
        import urllib.request, urllib.error
        monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=5: (_ for _ in ()).throw(urllib.error.URLError("refused")))
        from core import alerting
        monkeypatch.setattr(alerting, "_get_webhook", lambda: "https://hooks.slack.com/fake")
        assert alerting.send_alert(_water("critical"), _energy("critical"), "TestOrg", 3) is False
