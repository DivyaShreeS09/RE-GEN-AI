import os
import logging
from dotenv import load_dotenv

load_dotenv()

GEMINI_AVAILABLE = False
_client = None
_MODEL = "gemini-2.5-flash-lite"

try:
    from google import genai

    _api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if _api_key:
        _client = genai.Client(api_key=_api_key)
        GEMINI_AVAILABLE = True
        logging.info(f"Gemini client initialised (model: {_MODEL})")
except Exception as exc:
    logging.warning(f"Gemini client could not initialise: {exc}")


def call_gemini(prompt: str, fallback: str = "") -> tuple:
    """Call Gemini and return (text, gemini_was_used).
    Returns rule-based fallback on any error -- system always works without Gemini."""
    if not GEMINI_AVAILABLE or _client is None:
        return fallback, False
    try:
        response = _client.models.generate_content(model=_MODEL, contents=prompt)
        return response.text.strip(), True
    except Exception as exc:
        logging.warning(f"Gemini call failed, using rule-based fallback: {exc}")
        return fallback, False


def gemini_status() -> dict:
    return {
        "available": GEMINI_AVAILABLE,
        "model": _MODEL if GEMINI_AVAILABLE else None,
        "layer": "AI-enhanced" if GEMINI_AVAILABLE else "Rule-based (deterministic)",
    }
