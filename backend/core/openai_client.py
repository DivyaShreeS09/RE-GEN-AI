import os
import logging
from dotenv import load_dotenv

load_dotenv()

OPENAI_AVAILABLE = False
_client = None
_MODEL = "gpt-4o-mini"

try:
    from openai import OpenAI
    _api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if _api_key:
        _client = OpenAI(api_key=_api_key)
        OPENAI_AVAILABLE = True
        logging.info(f"OpenAI client initialised (model: {_MODEL})")
except Exception as exc:
    logging.warning(f"OpenAI client could not initialise: {exc}")


def call_openai(prompt: str, fallback: str = "") -> tuple:
    """Call OpenAI and return (text, openai_was_used).
    Returns rule-based fallback on any error — system works without an API key."""
    if not OPENAI_AVAILABLE or _client is None:
        return fallback, False
    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=320,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip(), True
    except Exception as exc:
        logging.warning(f"OpenAI call failed, using rule-based fallback: {exc}")
        return fallback, False


def openai_status() -> dict:
    return {
        "available": OPENAI_AVAILABLE,
        "model": _MODEL if OPENAI_AVAILABLE else None,
        "layer": "AI-enhanced" if OPENAI_AVAILABLE else "Rule-based (deterministic)",
    }
