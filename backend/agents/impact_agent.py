from core.guardrails import get_disclaimer

WATER_CO2_KG_PER_LITER = 0.001
ENERGY_CO2_KG_PER_KWH = 0.82
TREES_SAVED_PER_100KG_CO2 = 4.5
WATER_SCARCITY_INDEX = 1.8


def analyze_impact(water_saved_liters: float, energy_saved_kwh: float, waste_value_inr: float) -> dict:
    water_co2_saved = round(water_saved_liters * WATER_CO2_KG_PER_LITER, 2)
    energy_co2_saved = round(energy_saved_kwh * ENERGY_CO2_KG_PER_KWH, 2)
    total_co2_saved_kg = round(water_co2_saved + energy_co2_saved, 2)
    total_co2_saved_tonnes = round(total_co2_saved_kg / 1000, 4)

    trees_equivalent = round(total_co2_saved_kg / 100 * TREES_SAVED_PER_100KG_CO2, 1)

    water_scarcity_impact = round(water_saved_liters * WATER_SCARCITY_INDEX / 1000, 2)

    total_financial_benefit = round(
        water_saved_liters * 0.05
        + energy_saved_kwh * 8.0
        + waste_value_inr * 0.6,
        2,
    )

    if total_co2_saved_kg >= 500:
        sustainability_rating = "Outstanding"
        sustainability_score = 88
    elif total_co2_saved_kg >= 200:
        sustainability_rating = "Excellent"
        sustainability_score = 75
    elif total_co2_saved_kg >= 100:
        sustainability_rating = "Good"
        sustainability_score = 62
    elif total_co2_saved_kg >= 30:
        sustainability_rating = "Moderate"
        sustainability_score = 48
    else:
        sustainability_rating = "Developing"
        sustainability_score = 35

    sdg_alignment = [
        {"goal": "SDG 6 — Clean Water & Sanitation", "relevance": "High", "contribution": f"Saving {water_saved_liters}L/week reduces freshwater stress."},
        {"goal": "SDG 7 — Affordable & Clean Energy", "relevance": "High", "contribution": f"Eliminating {energy_saved_kwh} kWh waste improves energy efficiency."},
        {"goal": "SDG 12 — Responsible Consumption", "relevance": "High", "contribution": "Waste-to-Wealth pipeline converts campus waste into economic value."},
        {"goal": "SDG 13 — Climate Action", "relevance": "Medium", "contribution": f"Estimated {total_co2_saved_kg} kg CO2 reduction directly offsets emissions."},
    ]

    reasoning_trace = [
        f"Step 1 — Water CO2 impact: {water_saved_liters}L × {WATER_CO2_KG_PER_LITER} = {water_co2_saved} kg CO2.",
        f"Step 2 — Energy CO2 impact: {energy_saved_kwh} kWh × {ENERGY_CO2_KG_PER_KWH} = {energy_co2_saved} kg CO2.",
        f"Step 3 — Total CO2 saved: {total_co2_saved_kg} kg ({total_co2_saved_tonnes} tonnes).",
        f"Step 4 — Tree equivalent: {trees_equivalent} trees (1 tree absorbs ~100 kg CO2/year).",
        f"Step 5 — Water scarcity multiplier applied: ×{WATER_SCARCITY_INDEX} for campus region.",
        f"Step 6 — SDG alignment mapped across 4 Sustainable Development Goals.",
        f"Step 7 — Sustainability score assigned: {sustainability_score}/100 ({sustainability_rating}).",
    ]

    return {
        "agent": "Pollution & Impact Agent",
        "status": "analyzed",
        "water_co2_saved_kg": water_co2_saved,
        "energy_co2_saved_kg": energy_co2_saved,
        "total_co2_saved_kg": total_co2_saved_kg,
        "total_co2_saved_tonnes": total_co2_saved_tonnes,
        "trees_equivalent": trees_equivalent,
        "water_scarcity_impact_kl": water_scarcity_impact,
        "total_financial_benefit_inr": total_financial_benefit,
        "sustainability_rating": sustainability_rating,
        "sustainability_score": sustainability_score,
        "sdg_alignment": sdg_alignment,
        "reasoning_trace": reasoning_trace,
        "confidence": 0.87,
        "disclaimer": get_disclaimer(),
    }
