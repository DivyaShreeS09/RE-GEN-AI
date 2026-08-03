DISCLAIMER = (
    "RE:GEN AI is a prototype decision-support system. "
    "All values are estimated from simulated or uploaded data for demonstration purposes. "
    "This is not professional regulatory, financial, or engineering advice. "
    "Always consult certified waste management, engineering, and environmental professionals before taking action."
)

HAZARD_WARNING = (
    "⚠️ HAZARDOUS WASTE DETECTED: This material requires handling by certified, licensed processors only. "
    "Unauthorized disposal may violate environmental laws and cause serious health and environmental harm. "
    "Contact a CPCB/PCB authorized facility immediately."
)

SIMULATED_DATA_NOTICE = (
    "Data shown is simulated for demonstration. No real IoT sensors or live systems are connected."
)


def apply_hazard_guardrail(hazard_level: str) -> dict:
    critical_levels = {"critical", "high"}
    if hazard_level.lower() in critical_levels:
        return {
            "warning": True,
            "warning_message": HAZARD_WARNING,
            "estimated_profit_suppressed": True,
            "profit_note": "Estimated financial values are not shown for hazardous waste. Compliance costs must be assessed by a certified professional.",
        }
    return {"warning": False, "warning_message": None, "estimated_profit_suppressed": False, "profit_note": None}


def validate_quantity(quantity_kg: float) -> dict:
    if quantity_kg <= 0:
        return {"valid": False, "message": "Quantity must be greater than 0 kg."}
    if quantity_kg > 100000:
        return {"valid": False, "message": "Quantity exceeds 100,000 kg. Break into smaller batches for analysis."}
    return {"valid": True, "message": None}


def get_disclaimer() -> str:
    return DISCLAIMER


def get_simulated_notice() -> str:
    return SIMULATED_DATA_NOTICE


def sanitize_prompt_input(value: str, max_length: int = 200) -> str:
    """Strip characters and patterns commonly used in prompt-injection attempts.

    Applied to all user-supplied strings before they are interpolated into
    LLM prompts.  The goal is defence-in-depth: the model's system prompt and
    low-temperature setting already constrain output, but we also strip the
    most obvious attack vectors so they are never sent to the model at all.
    """
    if not isinstance(value, str):
        return str(value)[:max_length]
    # Truncate to a safe length first
    value = value[:max_length]
    # Remove common injection markers
    import re
    value = re.sub(r'(?i)(ignore\s+(all\s+)?(previous|prior|above|preceding)\s+instructions?)', '', value)
    value = re.sub(r'(?i)(system\s*prompt|you\s+are\s+now|act\s+as\s+)', '', value)
    value = re.sub(r'(?i)(###\s*(system|user|assistant)\s*###)', '', value)
    # Remove null bytes and ASCII control characters (except newline/tab)
    value = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', value)
    return value.strip()
