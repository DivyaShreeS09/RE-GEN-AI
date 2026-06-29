from core.guardrails import get_disclaimer

WATER_CO2_KG_PER_LITER     = 0.001
ENERGY_CO2_KG_PER_KWH      = 0.82
TREES_SAVED_PER_100KG_CO2  = 4.5
WATER_SCARCITY_INDEX        = 1.8
VEHICLE_CO2_KG_PER_KM      = 0.167   # Average passenger car (India)
HOUSEHOLD_CO2_KG_PER_DAY   = 2.87    # India avg: 3.5 kWh/day x 0.82 kg/kWh
FLIGHT_CO2_KG_PER_PERSON   = 200     # Mumbai-Delhi economy, one-way
WEEKS_PER_YEAR              = 52


def analyze_impact(water_saved_liters: float, energy_saved_kwh: float, waste_value_inr: float) -> dict:
    water_co2_saved       = round(water_saved_liters * WATER_CO2_KG_PER_LITER, 2)
    energy_co2_saved      = round(energy_saved_kwh   * ENERGY_CO2_KG_PER_KWH,  2)
    total_co2_saved_kg    = round(water_co2_saved + energy_co2_saved, 2)
    total_co2_saved_tonnes = round(total_co2_saved_kg / 1000, 4)

    trees_equivalent          = round(total_co2_saved_kg / 100 * TREES_SAVED_PER_100KG_CO2, 1)
    vehicle_km_equivalent     = round(total_co2_saved_kg / VEHICLE_CO2_KG_PER_KM, 1)
    household_days_equivalent = round(total_co2_saved_kg / HOUSEHOLD_CO2_KG_PER_DAY, 1)
    flights_offset_fraction   = round(total_co2_saved_kg / FLIGHT_CO2_KG_PER_PERSON, 3)

    water_scarcity_impact = round(water_saved_liters * WATER_SCARCITY_INDEX / 1000, 2)

    total_financial_benefit = round(
        water_saved_liters * 0.05
        + energy_saved_kwh  * 8.0
        + waste_value_inr   * 0.6,
        2,
    )

    annual_projections = {
        "water_liters":    round(water_saved_liters   * WEEKS_PER_YEAR),
        "energy_kwh":      round(energy_saved_kwh      * WEEKS_PER_YEAR, 1),
        "co2_kg":          round(total_co2_saved_kg    * WEEKS_PER_YEAR, 1),
        "financial_inr":   round(total_financial_benefit * WEEKS_PER_YEAR),
        "trees_equivalent": round(trees_equivalent),
        "vehicle_km":      round(vehicle_km_equivalent  * WEEKS_PER_YEAR, 1),
        "note": "Simulated projection — assumes same weekly loss rate sustained for 52 weeks with no intervention.",
    }

    if total_co2_saved_kg >= 500:
        sustainability_rating = "Outstanding"
        sustainability_score  = 88
    elif total_co2_saved_kg >= 200:
        sustainability_rating = "Excellent"
        sustainability_score  = 75
    elif total_co2_saved_kg >= 100:
        sustainability_rating = "Good"
        sustainability_score  = 62
    elif total_co2_saved_kg >= 30:
        sustainability_rating = "Moderate"
        sustainability_score  = 48
    else:
        sustainability_rating = "Developing"
        sustainability_score  = 35

    sdg_alignment = [
        {
            "goal": "SDG 6", "title": "Clean Water & Sanitation", "relevance": "High",
            "contribution": (
                f"Detecting and fixing {water_saved_liters} L/week of night-flow leakage reduces campus freshwater "
                f"stress. Equivalent to conserving {round(water_saved_liters * WEEKS_PER_YEAR)} L/year — a direct "
                "contribution to safe campus water management targets."
            ),
        },
        {
            "goal": "SDG 7", "title": "Affordable & Clean Energy", "relevance": "High",
            "contribution": (
                f"Eliminating {energy_saved_kwh} kWh of after-hours energy waste/week reduces the campus electricity "
                f"bill by an estimated Rs. {round(energy_saved_kwh * 8)} per week and lowers reliance on grid power "
                "(India emission factor: 0.82 kg CO2/kWh)."
            ),
        },
        {
            "goal": "SDG 12", "title": "Responsible Consumption & Production", "relevance": "High",
            "contribution": (
                "The Waste-to-Wealth pipeline identifies estimated recovery value across 30 material categories, "
                "converting waste streams into economic opportunity and reducing landfill burden — a direct "
                "responsible-consumption outcome."
            ),
        },
        {
            "goal": "SDG 13", "title": "Climate Action", "relevance": "Medium",
            "contribution": (
                f"Estimated {total_co2_saved_kg} kg CO2 reduction per week — equivalent to taking a car off the road "
                f"for {vehicle_km_equivalent} km, or {household_days_equivalent} days of an average Indian household's "
                "electricity use. Directly addresses campus carbon footprint."
            ),
        },
    ]

    reasoning_trace = [
        f"Step 1  — Water CO2: {water_saved_liters} L x {WATER_CO2_KG_PER_LITER} kg/L = {water_co2_saved} kg CO2.",
        f"Step 2  — Energy CO2: {energy_saved_kwh} kWh x {ENERGY_CO2_KG_PER_KWH} kg/kWh = {energy_co2_saved} kg CO2.",
        f"Step 3  — Total CO2 saved: {total_co2_saved_kg} kg ({total_co2_saved_tonnes} tonnes).",
        f"Step 4  — Tree equivalent: {trees_equivalent} trees (1 tree ~ 100 kg CO2/year).",
        f"Step 5  — Vehicle km equivalent: {vehicle_km_equivalent} km (India avg car: {VEHICLE_CO2_KG_PER_KM} kg/km).",
        f"Step 6  — Household electricity: {household_days_equivalent} days (India avg 3.5 kWh/day x 0.82).",
        f"Step 7  — Flights offset fraction: {flights_offset_fraction} Mumbai-Delhi flights ({FLIGHT_CO2_KG_PER_PERSON} kg/person).",
        f"Step 8  — Water scarcity multiplier: x{WATER_SCARCITY_INDEX} applied for campus region.",
        f"Step 9  — Annual projection (simulated): {annual_projections['co2_kg']} kg CO2, Rs. {annual_projections['financial_inr']}.",
        f"Step 10 — SDG alignment mapped: SDG 6, 7, 12, 13.",
        f"Step 11 — Sustainability score: {sustainability_score}/100 ({sustainability_rating}).",
    ]

    return {
        "agent":                      "Pollution & Impact Agent",
        "status":                     "analyzed",
        "water_co2_saved_kg":         water_co2_saved,
        "energy_co2_saved_kg":        energy_co2_saved,
        "total_co2_saved_kg":         total_co2_saved_kg,
        "total_co2_saved_tonnes":     total_co2_saved_tonnes,
        "trees_equivalent":           trees_equivalent,
        "vehicle_km_equivalent":      vehicle_km_equivalent,
        "household_days_equivalent":  household_days_equivalent,
        "flights_offset_fraction":    flights_offset_fraction,
        "water_scarcity_impact_kl":   water_scarcity_impact,
        "total_financial_benefit_inr": total_financial_benefit,
        "sustainability_rating":      sustainability_rating,
        "sustainability_score":       sustainability_score,
        "sdg_alignment":              sdg_alignment,
        "annual_projections":         annual_projections,
        "reasoning_trace":            reasoning_trace,
        "confidence":                 0.87,
        "disclaimer":                 get_disclaimer(),
    }
