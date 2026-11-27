"""Explicit AI provider routing with consent-controlled cloud inference."""
from collections import OrderedDict
import hashlib
import logging
import os
import time
from contextvars import ContextVar
from threading import Lock

_cloud_consent = ContextVar("cloud_consent", default=False)
_last_provider = ContextVar("last_provider", default=None)
_tenant = ContextVar("ai_tenant", default=None)
_usage = ContextVar("ai_usage", default=0)
_cache = OrderedDict()
_lock = Lock()
_local_inference = Lock()
_retry_after = 0.0
_client = None


# Mutable counter is scoped to one sync mission operation.
_mission_allowance = ContextVar("mission_allowance", default=None)


def provider_mode():
    """Unknown or empty configuration fails closed."""
    mode = os.getenv(
        "REGEN_AI_PROVIDER", ""
    ).strip().lower()

    if mode in {
        "offline", "ollama", "gemini", "groq", "auto"
    }:
        return mode

    return "offline"


def cloud_enabled():
    return (
        provider_mode() in {"gemini", "auto"}
        and os.getenv("REGEN_ENV") == "production"
        and bool(os.getenv("GEMINI_MODEL"))
        and bool(_tenant.get())
        and _cloud_consent.get()
        and bool(os.getenv("GEMINI_API_KEY"))
    )


def local_enabled():
    return (
        provider_mode() in {"ollama", "auto"}
        and os.getenv("REGEN_ENV") != "test"
        and bool(os.getenv("REGEN_OLLAMA_MODEL"))
        and bool(_tenant.get())
    )


def alternative_enabled():
    return (
        provider_mode() in {"groq", "auto"}
        and os.getenv("REGEN_ENV") == "production"
        and bool(os.getenv("REGEN_GROQ_MODEL"))
        and bool(_tenant.get())
        and _cloud_consent.get()
        and bool(os.getenv("GROQ_API_KEY"))
    )


def inference_enabled():
    return (
        cloud_enabled()
        or local_enabled()
        or alternative_enabled()
    )


def _provider():
    global _client
    with _lock:
        if _client is None:
            from google import genai
            _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"timeout": 5000})
        return _client


def _ollama(prompt, model, schema=None):
    import httpx

    timeout = httpx.Timeout(
        connect=3.0,
        read=120.0,
        write=10.0,
        pool=5.0
    )

    with httpx.Client(
        timeout=timeout,
        trust_env=False,
        follow_redirects=False
    ) as http:

        response = http.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                **({"format": schema.model_json_schema()} if schema else {}),
                "think": False,
                "keep_alive": "5m",
                "options": {
                    "num_ctx": 8192,
                    "num_predict": 2048,
                    "temperature": 0.1
                }
            }
        )

        response.raise_for_status()
        payload = response.json()

        if (
            payload.get("done") is True
            and payload.get("done_reason") != "length"
        ):
            return payload.get("response")


def _alternative(prompt, model):
    import httpx
    with httpx.Client(timeout=5, trust_env=False, follow_redirects=False) as http:
        response = http.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024})
        response.raise_for_status()
        choice = response.json()["choices"][0]
        return choice["message"]["content"] if choice["finish_reason"] == "stop" else None


_alternative_retry_after = 0.0


def call_ai(prompt: str, fallback: str = "", *, schema=None) -> tuple[str, bool]:
    global _retry_after, _alternative_retry_after
    _last_provider.set(None)
    if len(prompt) > 12000 or _usage.get() >= 3:
        return fallback, False
    providers = []

    if cloud_enabled() and time.monotonic() >= _retry_after:
        providers.append(("Gemini", os.environ["GEMINI_MODEL"]))

    if local_enabled():
        providers.append(("Ollama", os.environ["REGEN_OLLAMA_MODEL"]))

    if (
        alternative_enabled()
        and time.monotonic() >= _alternative_retry_after
    ):
        providers.append(("Groq", os.environ["REGEN_GROQ_MODEL"]))

    for name, model in providers:
        key = (_tenant.get(), schema.__name__ if schema else "narrative-v1", name, model, hashlib.sha256(prompt.encode()).digest())
        with _lock:
            cached = _cache.get(key) if key[0] else None
        if cached and cached[0] > time.monotonic():
            _last_provider.set(name)
            return cached[1], True
        if _usage.get() >= 3:
            break
        allowance = _mission_allowance.get()
        if allowance is not None:
            if allowance["attempts"] >= allowance["limit"]:
                break
        if name == "Ollama" and not _local_inference.acquire(blocking=False):
            continue
        if allowance is not None:
            allowance["attempts"] += 1
        _usage.set(_usage.get() + 1)
        try:
            if name == "Ollama":
                try:
                    text = _ollama(prompt, model, schema) if schema else _ollama(prompt, model)
                finally:
                    _local_inference.release()
            elif name == "Groq":
                text = _alternative(prompt, model)
            else:
                response = _provider().models.generate_content(
                    model=model, contents=prompt, config={"max_output_tokens": 1024, "temperature": 0.3})
                candidates = getattr(response, "candidates", None) or []
                reason = candidates[0].finish_reason if candidates else None
                if reason is not None and str(reason).split(".")[-1] != "STOP":
                    continue
                text = response.text
            if isinstance(text, str) and 0 < len(text.strip()) <= 16000:
                text = text.strip()
                if schema is not None:
                    try:
                        text = schema.model_validate_json(text).model_dump_json()
                    except ValueError:
                        continue
                if key[0]:
                    with _lock:
                        _cache[key] = (time.monotonic() + 300, text)
                        if len(_cache) > 128:
                            _cache.popitem(last=False)
                _last_provider.set(name)
                return text, True
        except Exception:
            if name == "Gemini":
                _retry_after = time.monotonic() + 60
            elif name == "Groq":
                _alternative_retry_after = time.monotonic() + 60
            logging.warning("Narrative provider unavailable.")
    return fallback, False


def ai_status() -> dict:
    provider = _last_provider.get()
    model = os.getenv({"Gemini":"GEMINI_MODEL", "Ollama":"REGEN_OLLAMA_MODEL", "Groq":"REGEN_GROQ_MODEL"}[provider]) if provider else None
    return {"available": bool(provider), "provider": provider, "model": model, "attempts": _usage.get(),
            "layer": "AI-enhanced" if provider else "Rule-based (deterministic)"}
