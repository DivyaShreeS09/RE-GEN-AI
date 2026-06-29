from core.simulation import load_water_data
from core.guardrails import get_disclaimer, get_simulated_notice

NIGHT_HOURS = list(range(0, 6))
BASELINE_NIGHT_LITERS = 12
ANOMALY_THRESHOLD_MULTIPLIER = 4.0
WATER_COST_PER_LITER = 0.05


def analyze_water() -> dict:
    df = load_water_data()

    anomaly_rows = df[df["anomaly"] == True].copy()
    normal_rows = df[df["anomaly"] == False].copy()

    night_normal = normal_rows[normal_rows["hour"].isin(NIGHT_HOURS)]
    baseline = night_normal["usage_liters"].mean() if len(night_normal) > 0 else BASELINE_NIGHT_LITERS

    total_anomaly_liters = float(anomaly_rows["usage_liters"].sum())
    expected_for_anomaly_hours = baseline * len(anomaly_rows)
    wasted_liters = round(total_anomaly_liters - expected_for_anomaly_hours, 1)

    anomaly_events = []
    grouped = anomaly_rows.groupby(["date", "location"])
    for (date, loc), grp in grouped:
        hours = sorted(grp["hour"].tolist())
        total_flow = float(grp["usage_liters"].sum())
        anomaly_events.append({
            "date": date,
            "location": loc,
            "anomaly_hours": hours,
            "duration_hours": len(hours),
            "total_flow_liters": total_flow,
            "estimated_waste_liters": round(total_flow - baseline * len(hours), 1),
        })

    if wasted_liters > 1000:
        severity = "critical"
        severity_score = 10
    elif wasted_liters > 500:
        severity = "high"
        severity_score = 30
    elif wasted_liters > 200:
        severity = "medium"
        severity_score = 55
    elif wasted_liters > 50:
        severity = "low"
        severity_score = 75
    else:
        severity = "none"
        severity_score = 95

    estimated_cost_inr = round(wasted_liters * WATER_COST_PER_LITER, 2)
    co2_equivalent_kg = round(wasted_liters * 0.001, 2)

    recommendations = []
    if severity in ("critical", "high"):
        recommendations.append("Immediate physical inspection of night-flow pipes at anomalous locations.")
        recommendations.append("Install pressure sensors at Block-B Hostel and Lab Block distribution points.")
        recommendations.append("Dispatch maintenance team within 4 hours.")
    elif severity == "medium":
        recommendations.append("Schedule pipe inspection within 48 hours.")
        recommendations.append("Check valve seals and junction points at flagged locations.")
    else:
        recommendations.append("Routine monitoring. No immediate action required.")

    hourly_chart = df.groupby("hour")["usage_liters"].mean().reset_index()
    hourly_chart_data = [
        {"hour": int(row["hour"]), "avg_usage": round(float(row["usage_liters"]), 1)}
        for _, row in hourly_chart.iterrows()
    ]

    reasoning_trace = [
        f"Step 1 — Loaded 7-day water usage data: {len(df)} hourly records.",
        f"Step 2 — Identified {len(anomaly_rows)} anomalous readings across {len(anomaly_events)} event(s).",
        f"Step 3 — Computed night-hour baseline: {round(baseline, 1)} liters/hour.",
        f"Step 4 — Estimated wasted liters: {wasted_liters} L (anomaly flow minus baseline).",
        f"Step 5 — Assigned severity: {severity.upper()} based on threshold analysis.",
        f"Step 6 — Estimated cost impact: ₹{estimated_cost_inr}.",
        f"Step 7 — CO2 equivalent computed: {co2_equivalent_kg} kg.",
    ]

    return {
        "agent": "Water Leakage Agent",
        "status": "analyzed",
        "anomaly_events": anomaly_events,
        "total_anomaly_readings": len(anomaly_rows),
        "baseline_night_usage_liters_per_hour": round(baseline, 1),
        "total_wasted_liters": wasted_liters,
        "severity": severity,
        "severity_score": severity_score,
        "estimated_cost_inr": estimated_cost_inr,
        "co2_equivalent_kg": co2_equivalent_kg,
        "recommendations": recommendations,
        "hourly_chart_data": hourly_chart_data,
        "reasoning_trace": reasoning_trace,
        "confidence": 0.89,
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }
