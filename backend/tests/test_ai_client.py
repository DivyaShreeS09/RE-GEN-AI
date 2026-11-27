"""Tests for core/ai_client.py — call_ai finish_reason guardrail and fallback behaviour."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
import core.ai_client as ai_client


def _make_response(finish_reason, text="Some generated text."):
    """Build a minimal mock that mimics the google-genai response shape."""
    candidate = MagicMock()
    candidate.finish_reason = finish_reason
    response = MagicMock()
    response.candidates = [candidate]
    response.text = text
    return response


class TestCallAiFinishReasonGuardrail:
    """call_ai must discard the response and return (fallback, False) for any
    finish_reason other than STOP, regardless of whether the candidate text
    is non-empty."""

    def test_max_tokens_returns_fallback(self):
        """finish_reason=MAX_TOKENS → truncated response discarded, fallback used."""
        response = _make_response("MAX_TOKENS", text="Truncated sent")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_max_tokens_enum_style_returns_fallback(self):
        """finish_reason as an enum-like object whose str() is 'FinishReason.MAX_TOKENS'."""
        finish_reason_obj = MagicMock()
        finish_reason_obj.__str__ = lambda self: "FinishReason.MAX_TOKENS"
        response = _make_response(finish_reason_obj, text="Truncated sent")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_safety_finish_reason_returns_fallback(self):
        """finish_reason=SAFETY (another non-STOP value) also uses fallback."""
        response = _make_response("SAFETY", text="Blocked text")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_stop_returns_ai_text(self):
        """finish_reason=STOP with non-empty text → AI response is served."""
        response = _make_response("STOP", text="Clean completed answer.")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "Clean completed answer."
        assert ai_was_used is True

    def test_stop_enum_style_returns_ai_text(self):
        """finish_reason as enum-like 'FinishReason.STOP' → AI response served."""
        finish_reason_obj = MagicMock()
        finish_reason_obj.__str__ = lambda self: "FinishReason.STOP"
        response = _make_response(finish_reason_obj, text="Clean completed answer.")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "Clean completed answer."
        assert ai_was_used is True


class TestCallAiFallbackPaths:
    """call_ai must fall back whenever the usable response is absent or empty."""

    def test_nonempty_text_without_candidates_is_accepted(self):
        """Empty candidates list → finish_reason is None → falls through to text check."""
        response = MagicMock()
        response.candidates = []
        response.text = "some text"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        # finish_reason is None → skips the non-STOP check; text is non-empty → serves it
        assert text == "some text"
        assert ai_was_used is True

    def test_empty_text_returns_fallback(self):
        """STOP with empty/whitespace text → fallback used."""
        response = _make_response("STOP", text="   ")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_ai_unavailable_returns_fallback(self):
        """When AI_AVAILABLE is False, fallback is returned without calling the client."""
        mock_client = MagicMock()

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=False):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        mock_client.models.generate_content.assert_not_called()
        assert text == "safe fallback"
        assert ai_was_used is False

    def test_api_exception_returns_fallback(self):
        """Any exception from the Gemini client → fallback, not a crash."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("network error")

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "cloud_enabled", return_value=True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False


def test_offline_even_with_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-fixture")
    with patch.object(ai_client, "_provider") as provider:
        assert ai_client.call_ai("fixture", "offline") == ("offline", False)
        provider.assert_not_called()
    assert ai_client.ai_status()["provider"] is None


def test_cache_scoped_to_tenant_and_provider_budget(monkeypatch):
    monkeypatch.setattr(ai_client, "cloud_enabled", lambda: True)
    fake = MagicMock()
    fake.models.generate_content.return_value = _make_response("STOP", "Fixture narrative")
    monkeypatch.setattr(ai_client, "_provider", lambda: fake)
    original = ai_client._tenant.set("cache-a")
    try:
        assert ai_client.call_ai("cache fixture")[1]
        assert ai_client.call_ai("cache fixture")[1]
        assert fake.models.generate_content.call_count == 1
        ai_client._tenant.set("cache-b")
        assert ai_client.call_ai("cache fixture")[1]
        assert fake.models.generate_content.call_count == 2
        fake.models.generate_content.side_effect = RuntimeError("fixture failure")
        assert ai_client.call_ai("other", "fallback") == ("fallback", False)
        assert ai_client.call_ai("another", "fallback") == ("fallback", False)
        assert fake.models.generate_content.call_count == 3
    finally:
        ai_client._tenant.reset(original)

def test_startup_never_imports_generative_sdk(monkeypatch):
    import subprocess
    from pathlib import Path
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-only")
    # No configuration or SDK is read during startup, even with a synthetic key.
    check = """
import sys
def audit(event, args):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise AssertionError("Network attempt at startup")
sys.addaudithook(audit)
import core.ai_client as ai
assert ai.call_ai("fixture", "offline") == ("offline", False)
assert "google.genai" not in sys.modules
"""
    subprocess.run([sys.executable, "-c", check], cwd=Path(__file__).resolve().parents[1], check=True, timeout=20)
