"""Explicit provider routing and isolation contracts."""

import pytest
from core import ai_client as ai


@pytest.fixture
def configured(monkeypatch):
    settings = {
        "REGEN_ENV": "production",
        "REGEN_AI_PROVIDER": "offline",
        "GEMINI_MODEL": "fixture-gemini",
        "GEMINI_API_KEY": "fixture-only",
        "REGEN_OLLAMA_MODEL": "fixture-local",
        "REGEN_GROQ_MODEL": "fixture-groq",
        "GROQ_API_KEY": "fixture-only",
    }

    for key, value in settings.items():
        monkeypatch.setenv(key, value)

    tenant = ai._tenant.set("provider-policy-fixture")
    consent = ai._cloud_consent.set(True)

    try:
        yield monkeypatch
    finally:
        ai._tenant.reset(tenant)
        ai._cloud_consent.reset(consent)


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("offline", (False, False, False)),
        ("ollama", (False, True, False)),
        ("gemini", (True, False, False)),
        ("groq", (False, False, True)),
        ("auto", (True, True, True)),
        ("unknown", (False, False, False)),
        ("", (False, False, False)),
    ],
)
def test_provider_mode_isolation(configured, mode, expected):
    configured.setenv("REGEN_AI_PROVIDER", mode)

    assert (
        ai.cloud_enabled(),
        ai.local_enabled(),
        ai.alternative_enabled(),
    ) == expected


def test_cloud_consent_required(configured):
    configured.setenv("REGEN_AI_PROVIDER", "auto")
    token = ai._cloud_consent.set(False)

    try:
        assert not ai.cloud_enabled()
        assert not ai.alternative_enabled()
        assert ai.local_enabled()
    finally:
        ai._cloud_consent.reset(token)


def test_test_environment_blocks_inference(configured):
    configured.setenv("REGEN_ENV", "test")
    configured.setenv("REGEN_AI_PROVIDER", "auto")

    assert not ai.inference_enabled()


def test_cloud_credentials_required(configured):
    configured.setenv("REGEN_AI_PROVIDER", "auto")
    configured.setenv("GEMINI_API_KEY", "")
    configured.setenv("GROQ_API_KEY", "")

    assert not ai.cloud_enabled()
    assert not ai.alternative_enabled()
    assert ai.local_enabled()


def test_offline_never_calls_provider(configured):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline mode invoked an AI provider")

    configured.setattr(ai, "_provider", forbidden)
    configured.setattr(ai, "_ollama", forbidden)
    configured.setattr(ai, "_alternative", forbidden)

    assert ai.call_ai(
        "offline policy fixture", "fallback"
    ) == ("fallback", False)


def test_ollama_failure_returns_fallback(configured):
    configured.setenv("REGEN_AI_PROVIDER", "ollama")

    def unavailable(*args, **kwargs):
        raise RuntimeError("Fixture Ollama unavailable")

    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected cloud provider invocation")

    configured.setattr(ai, "_ollama", unavailable)
    configured.setattr(ai, "_provider", forbidden)
    configured.setattr(ai, "_alternative", forbidden)

    assert ai.call_ai(
        "ollama outage fixture", "fallback"
    ) == ("fallback", False)


def test_local_inference_requires_tenant(configured):
    configured.setenv("REGEN_AI_PROVIDER", "ollama")
    token = ai._tenant.set(None)

    try:
        assert not ai.local_enabled()
    finally:
        ai._tenant.reset(token)
