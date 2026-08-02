from core.simulation import load_energy_data
from core.guardrails import get_disclaimer, get_simulated_notice
from core.data_processor import auto_detect_anomalies_energy

AFTER_HOURS = list(range(0, 6)) + [22, 23]
BASELINE_AFTER_HOURS_KWH = 2.5
ELECTRICITY_COST_PER_KWH = 8.0

_DEMO_LEVEL = {
    "level": 3, "code": "level3", "label": "Advanced AI Analysis",
    "anomaly_detection_available": True,
    "reasoning": "Simulated smart-campus sensor logs — full hourly resolution.",
}


def analyze_energy(df=None, is_uploaded: bool = False, analysis_level_info: dict = None) -> dict:
    if df is None:
        df = load_energy_data()
        level_info = _DEMO_LEVEL
        _run_anomaly = True
    else:
        level_info = analysis_level_info or _DEMO_LEVEL
        _run_anomaly = level_info.get("anomaly_detection_available", True)
        if _run_anomaly:
            has_anomalies = bool(df["anomaly"].any())
            if not has_anomalies:
                df = auto_detect_anomalies_energy(df)
        # If not running anomaly detection, anomaly column stays all False

    anomaly_rows  = df[df["anomaly"] == True].copy()
    normal_after  = df[(df["anomaly"] == False) & (df["hour"].isin(AFTER_HOURS))]

    baseline = normal_after["usage_kwh"].mean() if len(normal_after) > 0 else BASELINE_AFTER_HOURS_KWH

    total_anomaly_kwh = float(anomaly_rows["usage_kwh"].sum())
    expected_kwh      = baseline * len(anomaly_rows)
    wasted_kwh        = max(0.0, round(total_anomaly_kwh - expected_kwh, 2))

    anomaly_events = []
    if _run_anomaly:
        grouped = anomaly_rows.groupby(["date", "zone"])
        for (date, zone), grp in grouped:
            hours           = sorted(grp["hour"].tolist())
            total_kwh       = float(grp["usage_kwh"].sum())
            equipment_types = grp["equipment"].unique().tolist()
            anomaly_events.append({
                "date":            date,
                "zone":            zone,
                "anomaly_hours":   hours,
                "duration_hours":  len(hours),
                "total_kwh":       round(total_kwh, 2),
                "wasted_kwh":      round(total_kwh - baseline * len(hours), 2),
                "equipment":       equipment_types,
            })

    if wasted_kwh > 200:
        severity = "critical"; severity_score = 10
    elif wasted_kwh > 100:
        severity = "high";     severity_score = 28
    elif wasted_kwh > 50:
        severity = "medium";   severity_score = 52
    elif wasted_kwh > 10:
        severity = "low";      severity_score = 72
    else:
        severity = "none";     severity_score = 92

    estimated_cost_inr = round(wasted_kwh * ELECTRICITY_COST_PER_KWH, 2)
    co2_equivalent_kg  = round(wasted_kwh * 0.82, 2)
    total_kwh_consumed = round(float(df["usage_kwh"].sum()), 2)

    # Recommendations
    recommendations = []
    if not _run_anomaly:
        recommendations.append(
            "Advanced anomaly detection unavailable. Provide hourly operational logs or "
            "smart-meter exports to enable after-hours waste analysis and predictive insights."
        )
        recommendations.append(
            f"Estimated total electricity consumption: {total_kwh_consumed:,.1f} kWh. "
            "Compare against utility invoices to validate metering accuracy."
        )
        recommendations.append(
            "Install smart sub-meters and occupancy sensors to capture temporal consumption patterns."
        )
    elif severity in ("critical", "high"):
        recommendations.append("Immediate shutdown of non-essential AC and lighting in flagged zones.")
        recommendations.append("Install smart occupancy-based auto-shutoff systems.")
        recommendations.append("Audit access controls to prevent after-hours equipment use.")
    elif severity == "medium":
        recommendations.append("Schedule smart switch installation in flagged high-consumption zones.")
        recommendations.append("Set automated timer shutoffs for AC units after 10 PM.")
    else:
        recommendations.append("Current after-hours usage is within acceptable range.")
        recommendations.append("Continue periodic monitoring.")

    # Hourly chart
    hourly_chart = df.groupby("hour")["usage_kwh"].mean().reset_index()
    hourly_chart_data = [
        {"hour": int(row["hour"]), "avg_kwh": round(float(row["usage_kwh"]), 2)}
        for _, row in hourly_chart.iterrows()
    ]

    # Reasoning trace
    if _run_anomaly:
        reasoning_trace = [
            f"Step 1 — Loaded {level_info['label']} energy data: {len(df)} records.",
            f"Step 2 — After-hours window (10 PM–6 AM): {len(AFTER_HOURS)} hours.",
            f"Step 3 — Found {len(anomaly_rows)} anomalous readings across {len(anomaly_events)} event(s).",
            f"Step 4 — Normal after-hours baseline: {round(baseline, 2)} kWh/hr.",
            f"Step 5 — Estimated wasted kWh: {wasted_kwh} kWh.",
            f"Step 6 — Cost impact: Rs. {estimated_cost_inr} at Rs. {ELECTRICITY_COST_PER_KWH}/kWh.",
            f"Step 7 — CO2 impact: {co2_equivalent_kg} kg (India grid factor 0.82 kg/kWh).",
            f"Step 8 — Severity: {severity.upper()}.",
        ]
    else:
        reasoning_trace = [
            f"Step 1 — Loaded {level_info['label']} energy data: {len(df)} records.",
            f"Step 2 — Analysis level: {level_info['code'].upper()} — anomaly detection not available at this resolution.",
            f"Step 3 — Total consumption: {total_kwh_consumed:,.1f} kWh.",
            "Step 4 — After-hours waste analysis SKIPPED — requires hourly logs spanning ≥ 3 days.",
            "Step 5 — Recommendations based on consumption benchmarks only.",
        ]

    # War-room level fields
    if _run_anomaly:
        war_room_reasoning = (
            f"Scanned {len(df)} records for after-hours consumption anomalies. "
            f"Normal after-hours baseline: {round(baseline, 2)} kWh/hr. "
            f"Excess above baseline in {len(anomaly_events)} event(s): {wasted_kwh} kWh."
        )
        war_room_impact = (
            f"Estimated weekly electricity loss: Rs. {estimated_cost_inr:.0f}. "
            f"CO2 equivalent: {co2_equivalent_kg} kg."
        )
    else:
        war_room_reasoning = (
            f"Analysis level: {level_info['label']}. "
            f"{level_info.get('reasoning', '')} "
            "After-hours anomaly detection requires hourly logs with ≥ 3 days coverage."
        )
        war_room_impact = (
            f"Total estimated consumption: {total_kwh_consumed:,.1f} kWh. "
            "Exact after-hours waste cannot be quantified at this data resolution."
        )

    confidence = 0.91 if _run_anomaly else (0.42 if level_info["level"] == 1 else 0.65)

    return {
        "agent":                              "Energy Optimization Agent",
        "status":                             "analyzed",
        "analysis_level":                     level_info.get("code", "level3"),
        "analysis_level_label":               level_info.get("label", "Advanced AI Analysis"),
        "anomaly_detection_available":        _run_anomaly,
        "anomaly_detection_reason":           (
            "Advanced anomaly detection unavailable. "
            + level_info.get("reasoning", "")
            if not _run_anomaly else None
        ),
        "anomaly_events":                     anomaly_events,
        "total_anomaly_readings":             len(anomaly_rows),
        "baseline_after_hours_kwh_per_hour":  round(baseline, 2),
        "total_wasted_kwh":                   wasted_kwh,
        "total_consumption_kwh":              total_kwh_consumed,
        "severity":                           severity,
        "severity_score":                     severity_score,
        "estimated_cost_inr":                 estimated_cost_inr,
        "co2_equivalent_kg":                  co2_equivalent_kg,
        "recommendations":                    recommendations,
        "hourly_chart_data":                  hourly_chart_data,
        "reasoning_trace":                    reasoning_trace,
        "war_room_reasoning":                 war_room_reasoning,
        "war_room_impact":                    war_room_impact,
        "is_uploaded":                        is_uploaded,
        "confidence":                         confidence,
        "disclaimer":                         get_disclaimer(),
        "data_notice":                        "Uploaded dataset." if is_uploaded else get_simulated_notice(),
    }
