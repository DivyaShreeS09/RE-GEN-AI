DISCLAIMER = (
    "RE:GEN AI is a prototype decision-support system. "
    "All values are estimated from simulated data for capstone demonstration purposes. "
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
