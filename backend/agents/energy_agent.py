from core.simulation import load_energy_data
from core.guardrails import get_disclaimer, get_simulated_notice

AFTER_HOURS = list(range(0, 6)) + [22, 23]
BASELINE_AFTER_HOURS_KWH = 2.5
ELECTRICITY_COST_PER_KWH = 8.0
ANOMALY_THRESHOLD_KWH = 10.0


def analyze_energy() -> dict:
    df = load_energy_data()

    anomaly_rows = df[df["anomaly"] == True].copy()
    normal_after = df[(df["anomaly"] == False) & (df["hour"].isin(AFTER_HOURS))]

    baseline = normal_after["usage_kwh"].mean() if len(normal_after) > 0 else BASELINE_AFTER_HOURS_KWH

    total_anomaly_kwh = float(anomaly_rows["usage_kwh"].sum())
    expected_kwh = baseline * len(anomaly_rows)
    wasted_kwh = round(total_anomaly_kwh - expected_kwh, 2)

    anomaly_events = []
    grouped = anomaly_rows.groupby(["date", "zone"])
    for (date, zone), grp in grouped:
        hours = sorted(grp["hour"].tolist())
        total_kwh = float(grp["usage_kwh"].sum())
        equipment_types = grp["equipment"].unique().tolist()
        anomaly_events.append({
            "date": date,
            "zone": zone,
            "anomaly_hours": hours,
            "duration_hours": len(hours),
            "total_kwh": round(total_kwh, 2),
            "wasted_kwh": round(total_kwh - baseline * len(hours), 2),
            "equipment": equipment_types,
        })

    if wasted_kwh > 200:
        severity = "critical"
        severity_score = 10
    elif wasted_kwh > 100:
        severity = "high"
        severity_score = 28
    elif wasted_kwh > 50:
        severity = "medium"
        severity_score = 52
    elif wasted_kwh > 10:
        severity = "low"
        severity_score = 72
    else:
        severity = "none"
        severity_score = 92

    estimated_cost_inr = round(wasted_kwh * ELECTRICITY_COST_PER_KWH, 2)
    co2_equivalent_kg = round(wasted_kwh * 0.82, 2)

    recommendations = []
    if severity in ("critical", "high"):
        recommendations.append("Immediate shutdown of non-essential AC and lighting in flagged zones.")
        recommendations.append("Install smart occupancy-based auto-shutoff systems.")
        recommendations.append("Audit access controls to prevent after-hours equipment use.")
    elif severity == "medium":
        recommendations.append("Schedule smart switch installation in Seminar Hall and Computer Lab.")
        recommendations.append("Set automated timer shutoffs for AC units after 10 PM.")
    else:
        recommendations.append("Current after-hours usage is within acceptable range.")
        recommendations.append("Continue periodic monitoring.")

    hourly_chart = df.groupby("hour")["usage_kwh"].mean().reset_index()
    hourly_chart_data = [
        {"hour": int(row["hour"]), "avg_kwh": round(float(row["usage_kwh"]), 2)}
        for _, row in hourly_chart.iterrows()
    ]

    reasoning_trace = [
        f"Step 1 — Loaded 7-day energy usage data: {len(df)} hourly records.",
        f"Step 2 — Identified after-hours windows (10 PM–6 AM): {len(AFTER_HOURS)} hours.",
        f"Step 3 — Found {len(anomaly_rows)} anomalous after-hours readings across {len(anomaly_events)} event(s).",
        f"Step 4 — Normal after-hours baseline: {round(baseline, 2)} kWh/hour.",
        f"Step 5 — Estimated wasted kWh: {wasted_kwh} kWh.",
        f"Step 6 — Cost impact: ₹{estimated_cost_inr} at ₹{ELECTRICITY_COST_PER_KWH}/kWh.",
        f"Step 7 — CO2 impact: {co2_equivalent_kg} kg CO2 (India grid emission factor 0.82 kg/kWh).",
        f"Step 8 — Severity assigned: {severity.upper()}.",
    ]

    return {
        "agent": "Energy Optimization Agent",
        "status": "analyzed",
        "anomaly_events": anomaly_events,
        "total_anomaly_readings": len(anomaly_rows),
        "baseline_after_hours_kwh_per_hour": round(baseline, 2),
        "total_wasted_kwh": wasted_kwh,
        "severity": severity,
        "severity_score": severity_score,
        "estimated_cost_inr": estimated_cost_inr,
        "co2_equivalent_kg": co2_equivalent_kg,
        "recommendations": recommendations,
        "hourly_chart_data": hourly_chart_data,
        "reasoning_trace": reasoning_trace,
        "confidence": 0.91,
        "disclaimer": get_disclaimer(),
        "data_notice": get_simulated_notice(),
    }
