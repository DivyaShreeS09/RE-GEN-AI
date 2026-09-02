from core.simulation import load_water_data
from core.guardrails import get_disclaimer, get_simulated_notice
from core.data_processor import auto_detect_anomalies_water
from core.anomaly_detection import detect_anomalies_water_if

NIGHT_HOURS = list(range(0, 6))
BASELINE_NIGHT_LITERS = 12
WATER_COST_PER_LITER = 0.05

_DEMO_LEVEL = {
    "level": 3, "code": "level3", "label": "Advanced AI Analysis",
    "anomaly_detection_available": True,
    "reasoning": "Simulated smart-campus sensor logs — full hourly resolution.",
}


def analyze_water(df=None, is_uploaded: bool = False, analysis_level_info: dict = None) -> dict:
    _if_meta = None
    if df is None:
        df = load_water_data()
        level_info = _DEMO_LEVEL
        _run_anomaly = True
    else:
        level_info = analysis_level_info or _DEMO_LEVEL
        _run_anomaly = level_info.get("anomaly_detection_available", True)
        if _run_anomaly:
            has_anomalies = bool(df["anomaly"].any())
            if not has_anomalies:
                df, _if_meta = detect_anomalies_water_if(df)
        # If not running anomaly detection, anomaly column stays all False

    anomaly_rows = df[df["anomaly"] == True].copy()
    normal_rows  = df[df["anomaly"] == False].copy()

    night_normal = normal_rows[normal_rows["hour"].isin(NIGHT_HOURS)]
    baseline = night_normal["usage_liters"].mean() if len(night_normal) > 0 else BASELINE_NIGHT_LITERS

    total_anomaly_liters = float(anomaly_rows["usage_liters"].sum())
    expected_for_anomaly_hours = baseline * len(anomaly_rows)
    wasted_liters = max(0.0, round(total_anomaly_liters - expected_for_anomaly_hours, 1))

    anomaly_events = []
    if _run_anomaly:
        grouped = anomaly_rows.groupby(["date", "location"])
        for (date, loc), grp in grouped:
            hours      = sorted(grp["hour"].tolist())
            total_flow = float(grp["usage_liters"].sum())
            anomaly_events.append({
                "date":                   date,
                "location":               loc,
                "anomaly_hours":          hours,
                "duration_hours":         len(hours),
                "total_flow_liters":      total_flow,
                "estimated_waste_liters": round(total_flow - baseline * len(hours), 1),
            })

    if wasted_liters > 1000:
        severity = "critical"; severity_score = 10
    elif wasted_liters > 500:
        severity = "high";     severity_score = 30
    elif wasted_liters > 200:
        severity = "medium";   severity_score = 55
    elif wasted_liters > 50:
        severity = "low";      severity_score = 75
    else:
        severity = "none";     severity_score = 95

    estimated_cost_inr = round(wasted_liters * WATER_COST_PER_LITER, 2)
    co2_equivalent_kg  = round(wasted_liters * 0.001, 2)
    total_liters       = round(float(df["usage_liters"].sum()), 1)

    # Recommendations
    recommendations = []
    if not _run_anomaly:
        recommendations.append(
            "Advanced anomaly detection unavailable. Provide hourly operational logs or "
            "smart-meter exports to enable leak detection and predictive analytics."
        )
        recommendations.append(
            f"Estimated total consumption: {total_liters:,.0f} L. "
            "Compare against utility bills to identify billing anomalies."
        )
        recommendations.append(
            "Install sub-metering at key distribution points for higher-resolution monitoring."
        )
    elif severity in ("critical", "high"):
        recommendations.append("Immediate physical inspection of night-flow pipes at anomalous locations.")
        recommendations.append("Install pressure sensors at identified high-consumption distribution points.")
        recommendations.append("Dispatch maintenance team within 4 hours.")
    elif severity == "medium":
        recommendations.append("Schedule pipe inspection within 48 hours.")
        recommendations.append("Check valve seals and junction points at flagged locations.")
    else:
        recommendations.append("Routine monitoring. No immediate action required.")

    # Hourly chart
    hourly_chart = df.groupby("hour")["usage_liters"].mean().reset_index()
    hourly_chart_data = [
        {"hour": int(row["hour"]), "avg_usage": round(float(row["usage_liters"]), 1)}
        for _, row in hourly_chart.iterrows()
    ]

    # Reasoning trace
    if _run_anomaly:
        _method_note = (
            f"IsolationForest fit on {_if_meta['n_locations_if']} location(s); "
            f"{_if_meta['n_locations_fallback']} location(s) used 4× night-baseline fallback "
            f"(< {_if_meta['min_samples_threshold']} samples). "
            f"Method: {_if_meta['method']}."
            if _if_meta else "Pre-labeled anomalies used (demo / uploaded with anomaly column)."
        )
        reasoning_trace = [
            f"Step 1 — Loaded {level_info['label']} water data: {len(df)} records.",
            f"Step 2 — Anomaly detection: {_method_note}",
            f"Step 3 — Identified {len(anomaly_rows)} anomalous readings across {len(anomaly_events)} event(s).",
            f"Step 4 — Night-hour baseline: {round(baseline, 1)} L/hr.",
            f"Step 5 — Estimated wasted liters: {wasted_liters} L.",
            f"Step 6 — Severity: {severity.upper()}.",
            f"Step 7 — Estimated cost: Rs. {estimated_cost_inr}.",
            f"Step 8 — CO2 equivalent: {co2_equivalent_kg} kg.",
        ]
    else:
        reasoning_trace = [
            f"Step 1 — Loaded {level_info['label']} water data: {len(df)} records.",
            f"Step 2 — Analysis level: {level_info['code'].upper()} — anomaly detection not available at this resolution.",
            f"Step 3 — Total consumption: {total_liters:,.0f} L.",
            "Step 4 — Anomaly detection SKIPPED — requires hourly logs spanning ≥ 3 days.",
            "Step 5 — Recommendations based on consumption benchmarks only.",
        ]

    # War-room level fields
    if _run_anomaly:
        _det_method = (
            f"IsolationForest fit per location (contamination=auto, random_state=42)"
            if _if_meta and _if_meta["method"] == "isolation_forest"
            else "Threshold-based or pre-labeled anomaly detection"
        )
        war_room_reasoning = (
            f"Analyzed {len(anomaly_events)} event(s) from {len(df)} records. "
            f"Detection: {_det_method}. "
            f"Night-hour baseline: {round(baseline, 1)} L/hr. "
            f"Excess above baseline during anomalous periods: {wasted_liters} L."
        )
        war_room_impact = (
            f"Estimated weekly utility loss: Rs. {estimated_cost_inr:.0f}. "
            f"CO2 equivalent: {co2_equivalent_kg} kg."
        )
    else:
        war_room_reasoning = (
            f"Analysis level: {level_info['label']}. "
            f"{level_info.get('reasoning', '')} "
            "Anomaly detection requires hourly logs with ≥ 3 days coverage."
        )
        war_room_impact = (
            f"Total estimated consumption: {total_liters:,.0f} L. "
            "Exact leakage cannot be quantified at this data resolution."
        )

    # Confidence based on level
    confidence = 0.89 if _run_anomaly else (0.42 if level_info["level"] == 1 else 0.65)

    return {
        "agent":                              "Water Leakage Agent",
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
        "baseline_night_usage_liters_per_hour": round(baseline, 1),
        "total_wasted_liters":                wasted_liters,
        "total_consumption_liters":           total_liters,
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
