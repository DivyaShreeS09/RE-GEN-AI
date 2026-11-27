"""Fit one deterministic model per instrumented group; use a disclosed time-of-day threshold for small groups."""
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import timedelta

MIN_SAMPLES_FOR_IF = 24


def _detect(df, grouping, metric, hours, multiplier, default_baseline, count_label):
    result = df.copy()
    fitted = fallback = 0
    groups = result.groupby(grouping) if grouping in result.columns else [(None, result)]
    for _, group in groups:
        in_window = group["hour"].isin(hours)
        if len(group) >= MIN_SAMPLES_FOR_IF:
            predictions = IsolationForest(contamination="auto", random_state=42).fit_predict(group[[metric, "hour"]])
            flags = (predictions == -1) & in_window
            fitted += 1
        else:
            reference = group.loc[in_window, metric]
            baseline = reference.mean() if len(reference) else default_baseline
            flags = in_window & (group[metric] > baseline * multiplier)
            fallback += 1
        result.loc[group.index, "anomaly"] = flags
    method = "mixed" if fitted and fallback else "isolation_forest" if fitted else "threshold"
    return result, {"method": method, f"n_{count_label}_if": fitted, f"n_{count_label}_fallback": fallback,
                    "min_samples_threshold": MIN_SAMPLES_FOR_IF}


def detect_anomalies_water_if(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    return _detect(df, "location", "usage_liters", range(6), 4, 12, "locations")


def detect_anomalies_energy_if(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    return _detect(df, "zone", "usage_kwh", [0, 1, 2, 3, 4, 5, 22, 23], 3.5, 2.5, "zones")


def analyze_resource_observations(frame, metric, zone, unit):
    """Analyze validated observations with chronological, comparable meter baselines."""
    from collections import defaultdict, deque
    from statistics import median

    frame = frame.copy()
    if "timestamp" in frame:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    kind = frame["reading_type"].iat[0]
    chronological = frame["timestamp"].notna().all() if "timestamp" in frame else False
    totals = frame.groupby(zone)[metric].sum()
    dates = pd.to_datetime(frame["date"], errors="coerce")
    daily = frame.groupby("date")[metric].sum().sort_index() if chronological and kind != "monthly" else pd.Series(dtype=float)
    valid_daily = chronological and kind == "daily"
    if chronological and kind in {"counter", "rate", "interval"} and "interval_seconds" in frame:
        durations = frame["interval_seconds"]
        exact_hour = durations.eq(3600).all()
        full_day_hours = frame.groupby(["date", "device_id" if "device_id" in frame else zone])["hour"].nunique()
        valid_daily = bool(exact_hour and full_day_hours.eq(24).all())
    if valid_daily:
        valid_daily = (not frame.get("estimated", pd.Series(False, index=frame.index)).eq(True).any()
                       and frame.groupby("date").size().nunique() == 1)
        if "device_id" in frame:
            valid_daily = valid_daily and frame.groupby("date")["device_id"].agg(frozenset).nunique() == 1
    complete_daily = daily if valid_daily else pd.Series(dtype=float)
    comparable_history = len(complete_daily) > 1 and (
        pd.to_datetime(complete_daily.index).to_series().diff().dropna() == timedelta(days=1)).all()
    forecast = {"status": "insufficient_data", "basis": "At least 21 consecutive documented daily totals are required."}
    if len(complete_daily) >= 21 and comparable_history:
        values = complete_daily.tolist()
        boundaries = range(len(values) - 7, len(values))
        models = {
            "previous_day": lambda past: past[-1],
            "weekly_seasonal": lambda past: past[-7],
        }
        errors = {name: [abs(model(values[:i]) - values[i]) for i in boundaries] for name, model in models.items()}
        mae = {name: round(sum(rows) / len(rows), 4) for name, rows in errors.items()}
        selected = min(models, key=mae.get)
        estimate = models[selected](values)
        spread = max(errors[selected])
        forecast = {"status": "available", "unit": unit, "next_date": (dates.max() + timedelta(days=1)).date().isoformat(),
                    "model": selected, "estimate": round(estimate, 3), "range": [round(max(0, estimate - spread), 3), round(estimate + spread, 3)],
                    "validation_mae": mae, "validation_days": 7, "basis": "Rolling one-day forecasts. Range uses the maximum observed validation error."}

    history = defaultdict(lambda: deque(maxlen=12))
    prior_run = {}
    findings = []
    compared = 0
    precision = 1 if unit == "L" else 2
    if chronological:
        for row in frame.to_dict("records"):
            timestamp = row["timestamp"]
            meter = row.get("device_id") or row[zone]
            instrument = (meter, row[zone])
            value = row[metric]
            estimated = row.get("estimated") == True
            scheduled = row.get("scheduled")
            occupied = row.get("occupied")
            hours = row["hour"]
            if (estimated and kind != "rate") or kind == "monthly" or (kind == "interval" and pd.isna(hours)):
                continue
            seconds = row.get("interval_seconds")
            normalized = value * 3600 / seconds if seconds else value
            key = (instrument, int(hours) if pd.notna(hours) else None, timestamp.tz_convert("Asia/Kolkata").dayofweek >= 5,
                   scheduled if pd.notna(scheduled) else None, occupied if pd.notna(occupied) else None)
            baseline = history[key]
            if len(baseline) >= 3:
                compared += 1
                center = median(baseline)
                deviation = median(abs(sample - center) for sample in baseline)
                if normalized > center + max(4.5 * deviation, 0.3 * center, 0.01):
                    expected = center * seconds / 3600 if seconds else center
                    previous = prior_run.get(instrument)
                    adjacent = previous and (timestamp - previous[0]).total_seconds() == (seconds or 3600)
                    if seconds and seconds > 3600:
                        adjacent = False
                    inactive = scheduled == False and occupied != True
                    run = (previous[1] if adjacent else 0) + 1 if inactive else 0
                    prior_run[instrument] = (timestamp, run)
                    location_key = "location" if zone == "location" else "zone"
                    excess_key = "estimated_waste_liters" if unit == "L" else "wasted_kwh"
                    quantity_key = "total_flow_liters" if unit == "L" else "total_kwh"
                    findings.append({location_key: row[zone], "meter_id": row.get("device_id"), "date": row["date"],
                                     "timestamp": timestamp.isoformat(), "anomaly_hours": [int(hours)] if pd.notna(hours) else [],
                                     "duration_hours": seconds / 3600 if seconds else None, quantity_key: round(value, precision),
                                     "baseline_quantity": round(expected, precision), excess_key: round(value - expected, precision),
                                     "evidence_status": "possible_leakage" if unit == "L" and run >= 3 else
                                         "persistent_off_hours_load" if run >= 3 else "abnormal_consumption",
                                     "schedule_documented": pd.notna(scheduled), "reference_samples": len(baseline),
                                     "estimated_measurement": estimated,
                                     "basis": "Prior observations from same meter/zone, local hour, weekday class and available schedule/occupancy."})
                    continue
            if not row["anomaly"]:
                baseline.append(normalized)

    profile = {"unit": unit, "measurement_type": kind,
               "records": len(frame), "daily_totals": [{"date": date, "amount": round(float(value), 3)}
                                                       for date, value in daily.tail(90).items()],
               "by_zone": [{"zone": name, "amount": round(float(value), 3)} for name, value in totals.items()],
               "average_daily": round(float(complete_daily.mean()), 3) if not complete_daily.empty else None,
               "minimum_daily": round(float(complete_daily.min()), 3) if not complete_daily.empty else None,
               "maximum_daily": round(float(complete_daily.max()), 3) if not complete_daily.empty else None,
               "daily_variability": round(float(complete_daily.std(ddof=0)), 3) if not complete_daily.empty else None,
               "contiguous_complete_daily_coverage": bool(valid_daily and (len(complete_daily) == 1 or comparable_history)),
               "recent_average_daily": round(float(complete_daily.tail(7).mean()), 3) if comparable_history and len(complete_daily) >= 14 else None,
               "previous_average_daily": round(float(complete_daily.iloc[-14:-7].mean()), 3) if comparable_history and len(complete_daily) >= 14 else None,
               "estimated_quantity": round(float(frame.loc[frame.get("estimated", pd.Series(False, index=frame.index)).eq(True), metric].sum()), 3),
               "off_hours_observed": round(float(frame.loc[frame["scheduled"].eq(False), metric].sum()), 3)
                   if "scheduled" in frame and frame["scheduled"].notna().any() else None,
               "observed_days": int(dates.nunique()),
               "median_inter_sample_seconds": round(float(frame["interval_seconds"].dropna().median()), 2)
                   if "interval_seconds" in frame and frame["interval_seconds"].notna().any() else None,
               "baseline_comparisons": compared,
               "window": [frame["timestamp"].min().isoformat(), frame["timestamp"].max().isoformat()] if chronological else None,
               "daily_basis": ("Submitted daily totals" if kind == "daily" else "Complete comparable hourly coverage")
                   if valid_daily else "Observed samples per local date. Daily coverage may be incomplete.",
               "forecast": forecast}
    if "device_id" in frame:
        profile["by_meter"] = [{"meter_id": meter, "amount": round(float(value), 3)}
                               for meter, value in frame.groupby("device_id")[metric].sum().items()]
    if metric == "usage_kwh" and kind == "rate":
        profile["peak_observed_demand_kw"] = frame.attrs.get("validation", {}).get("peak_observed_demand_kw")
    return profile, findings


def uploaded_resource_result(frame, level, *, water, rate, tariff_source):
    from core.guardrails import get_disclaimer

    unit, metric, zone = ("L", "usage_liters", "location") if water else ("kWh", "usage_kwh", "zone")
    profile, findings = analyze_resource_observations(frame, metric, zone, unit)
    available = profile["baseline_comparisons"] > 0
    observed = round(float(frame[metric].sum()), 2)
    excess = round(sum(finding["estimated_waste_liters" if water else "wasted_kwh"] for finding in findings), 2)
    estimate = round(excess * rate, 2) if rate is not None and available else None
    basis = ("Compared against matched prior readings. Excess is an inspection signal; avoidable consumption requires verification."
             if available else "Comparable prior meter observations are insufficient to evaluate an anomaly baseline.")
    if findings:
        recommendation = ("Have authorized facility staff verify scheduled demand and inspect the flagged meter or zone."
                          if water else "Ask qualified facilities staff to compare the flagged load with operating schedules and equipment logs.")
    elif not available:
        recommendation = "Collect comparable timestamped readings and document operating schedules before diagnosing resource loss."
    else:
        recommendation = "Continue monitoring comparable readings and document schedule changes."
    readings = frame.groupby("hour")[metric].mean()
    validation = frame.attrs.get("validation", {})
    return {
        "agent": "Water Leakage Agent" if water else "Energy Optimization Agent",
        "status": "analyzed", "is_uploaded": True, "confidence": None,
        "analysis_level": level["code"], "analysis_level_label": level["label"],
        "anomaly_detection_available": available, "anomaly_detection_reason": None if available else basis,
        "anomaly_events": findings, "total_anomaly_readings": len(findings),
        "total_wasted_liters" if water else "total_wasted_kwh": excess,
        "total_consumption_liters" if water else "total_consumption_kwh": observed,
        "estimated_cost_inr": estimate, "co2_equivalent_kg": None,
        "tariff": {"inr_per_unit": rate, "unit": unit, "basis": tariff_source},
        "severity": "medium" if findings else "none",
        "severity_score": 55 if findings else 95,
        "reporting_days": int(frame.loc[frame["date"].ne("Unknown"), "date"].nunique()) or None,
        "recommendations": [recommendation], "hourly_chart_data": [
            {"hour": int(hour), "avg_usage" if water else "avg_kwh": round(float(value), 3)} for hour, value in readings.items()
        ],
        "reasoning_trace": [f"Summed {len(frame)} validated intervals or aggregates: {observed} {unit}.", basis],
        "war_room_reasoning": basis,
        "war_room_impact": f"Observed consumption: {observed} {unit}. {len(findings)} baseline exceptions.",
        "data_notice": "Uploaded historical observations.",
        "disclaimer": get_disclaimer(),
        "resource_profile": profile,
        "input_quality": {key: validation.get(key) for key in (
            "warnings", "missing_values", "duplicates_removed", "counter_resets", "counter_rollovers", "intervals_excluded")},
        "loss_assessment": {"status": "suspected_excess" if findings else "none_detected" if available else "insufficient_evidence",
                            "estimated_excess": excess if available else None, "potential_savings": None, "verified_savings": None, "unit": unit},
    }
