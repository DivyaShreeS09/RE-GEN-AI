"""
RE:GEN AI — Gemini Reasoning Layer
Wraps google-generativeai with graceful fallback.
If GEMINI_API_KEY is absent or the call fails, every function returns
the caller-supplied fallback string so all agents remain fully functional.
"""
import os
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_AVAILABLE = False
_model = None

try:
    import google.generativeai as genai
    _api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if _api_key:
        genai.configure(api_key=_api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash")
        GEMINI_AVAILABLE = True
        logging.info("RE:GEN AI — Gemini reasoning layer: ACTIVE (gemini-2.0-flash)")
    else:
        logging.info("RE:GEN AI — Gemini reasoning layer: INACTIVE (set GEMINI_API_KEY to enable)")
except Exception as exc:
    logging.info(f"RE:GEN AI — Gemini reasoning layer: INACTIVE ({exc})")


def call_gemini(prompt: str, fallback: str = "") -> tuple:
    """
    Call Gemini with graceful fallback.
    Returns (text: str, gemini_was_used: bool).
    If Gemini is unavailable or errors, returns (fallback, False).
    """
    if not GEMINI_AVAILABLE or _model is None:
        return fallback, False
    try:
        response = _model.generate_content(prompt)
        return response.text.strip(), True
    except Exception as exc:
        logging.warning(f"Gemini call failed, using rule-based fallback: {exc}")
        return fallback, False


def gemini_status() -> dict:
    return {
        "available": GEMINI_AVAILABLE,
        "model": "gemini-2.0-flash" if GEMINI_AVAILABLE else None,
        "layer": "AI-enhanced" if GEMINI_AVAILABLE else "Rule-based (deterministic)",
    }
