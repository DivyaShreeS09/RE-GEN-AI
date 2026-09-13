import os
import logging
from dotenv import load_dotenv

load_dotenv()

AI_AVAILABLE = False
_client = None
_MODEL = "gemini-3.6-flash"


try:
    from google import genai
    from google.genai import types as genai_types

    _api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if _api_key:
        _client = genai.Client(api_key=_api_key)
        AI_AVAILABLE = True
        logging.info(f"Gemini client initialised (model: {_MODEL})")
except Exception as exc:
    logging.warning(f"Gemini client could not initialise: {exc}")


def call_ai(prompt: str, fallback: str = "") -> tuple:
    """Call the Gemini narrative layer and return (text, ai_was_used).
    Returns the deterministic rule-based fallback on any error, missing key,
    or client-library issue — the system works fully without an API key."""
    if not AI_AVAILABLE or _client is None:
        return fallback, False
    try:
        # gemini-3.6-flash performs internal "thinking" before answering, and the
        # amount varies a lot by prompt (observed 100-2000+ thinking tokens on our
        # actual prompts) — a low cap lets thinking alone exhaust the budget and
        # truncates the answer to nothing. 4096 leaves comfortable headroom above
        # the largest thinking usage measured against our longest prompt.
        response = _client.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                max_output_tokens=4096,
                temperature=0.3,
            ),
        )
        candidates = getattr(response, "candidates", None) or []
        finish_reason = candidates[0].finish_reason if candidates else None
        # Never serve a truncated or otherwise abnormal completion as if it were
        # a finished answer — a cut-off sentence is worse than the deterministic
        # fallback, so treat anything other than a clean STOP as a failed call.
        if finish_reason is not None and str(finish_reason).split(".")[-1] != "STOP":
            logging.warning(
                f"Gemini call did not finish cleanly (finish_reason={finish_reason}); "
                "using rule-based fallback to avoid serving truncated text."
            )
            return fallback, False
        text = (response.text or "").strip()
        if not text:
            return fallback, False
        return text, True
    except Exception as exc:
        logging.warning(f"Gemini call failed, using rule-based fallback: {exc}")
        return fallback, False


def ai_status() -> dict:
    return {
        "available": AI_AVAILABLE,
        "provider": "Gemini" if AI_AVAILABLE else None,
        "model": _MODEL if AI_AVAILABLE else None,
        "layer": "AI-enhanced" if AI_AVAILABLE else "Rule-based (deterministic)",
    }
