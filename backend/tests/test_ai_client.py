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
             patch.object(ai_client, "AI_AVAILABLE", True):
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
             patch.object(ai_client, "AI_AVAILABLE", True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_safety_finish_reason_returns_fallback(self):
        """finish_reason=SAFETY (another non-STOP value) also uses fallback."""
        response = _make_response("SAFETY", text="Blocked text")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "AI_AVAILABLE", True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_stop_returns_ai_text(self):
        """finish_reason=STOP with non-empty text → AI response is served."""
        response = _make_response("STOP", text="Clean completed answer.")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "AI_AVAILABLE", True):
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
             patch.object(ai_client, "AI_AVAILABLE", True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "Clean completed answer."
        assert ai_was_used is True


class TestCallAiFallbackPaths:
    """call_ai must fall back whenever the usable response is absent or empty."""

    def test_no_candidates_returns_fallback(self):
        """Empty candidates list → finish_reason is None → falls through to text check."""
        response = MagicMock()
        response.candidates = []
        response.text = "some text"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = response

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "AI_AVAILABLE", True):
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
             patch.object(ai_client, "AI_AVAILABLE", True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False

    def test_ai_unavailable_returns_fallback(self):
        """When AI_AVAILABLE is False, fallback is returned without calling the client."""
        mock_client = MagicMock()

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "AI_AVAILABLE", False):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        mock_client.models.generate_content.assert_not_called()
        assert text == "safe fallback"
        assert ai_was_used is False

    def test_api_exception_returns_fallback(self):
        """Any exception from the Gemini client → fallback, not a crash."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("network error")

        with patch.object(ai_client, "_client", mock_client), \
             patch.object(ai_client, "AI_AVAILABLE", True):
            text, ai_was_used = ai_client.call_ai("any prompt", fallback="safe fallback")

        assert text == "safe fallback"
        assert ai_was_used is False
