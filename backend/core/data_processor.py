"""
data_processor.py — Upload pipeline: parse, validate, normalise, auto-detect anomalies.

All computations are deterministic (no LLM). Handles CSV and Excel (.xlsx).
Column detection is flexible: tries canonical names, then common synonyms.
"""

import io
import logging
from typing import Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Column synonym maps
# ---------------------------------------------------------------------------

_DATE_COLS   = {"date", "Date", "timestamp", "Timestamp", "datetime", "Datetime", "time", "Time", "day"}
_HOUR_COLS   = {"hour", "Hour", "hr", "Hr", "time_hour"}
_W_USAGE     = {"usage_liters", "usage_l", "liters", "litres", "usage", "consumption",
                "flow", "flow_liters", "water_usage", "volume", "quantity_liters", "amount_liters"}
_W_LOCATION  = {"location", "Location", "building", "Building", "site", "zone", "Zone", "area", "Area", "block"}
_W_ANOMALY   = {"anomaly", "Anomaly", "is_anomaly", "flag", "Flag", "leak", "Leak", "alert"}

_E_USAGE     = {"usage_kwh", "kwh", "kWh", "KWH", "energy", "Energy", "consumption",
                "electricity", "power", "usage", "amount_kwh"}
_E_ZONE      = {"zone", "Zone", "area", "Area", "building", "Building", "location", "department", "Department"}
_E_EQUIPMENT = {"equipment", "Equipment", "device", "Device", "type", "Type", "appliance"}
_E_ANOMALY   = _W_ANOMALY

_FUEL_TYPE   = {"fuel_type", "fuel", "Fuel", "type", "Type"}
_FUEL_QTY    = {"quantity", "quantity_liters", "liters", "litres", "volume", "amount", "consumption", "usage"}
_FUEL_UNIT   = {"unit", "Unit", "units"}

# ---------------------------------------------------------------------------
# Emission factors (deterministic — never use AI)
# ---------------------------------------------------------------------------

FUEL_EMISSION_FACTORS = {
    "diesel":       2.68,   # kg CO2 / liter
    "petrol":       2.31,
    "gasoline":     2.31,
    "cng":          1.96,   # kg CO2 / kg
    "lpg":          1.51,   # kg CO2 / liter
    "natural gas":  2.02,   # kg CO2 / m3
    "lng":          2.76,   # kg CO2 / liter
    "coal":         2.42,   # kg CO2 / kg
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_col(df_cols: list, candidates: set) -> Optional[str]:
    """Return the first df column that matches any candidate name (case-insensitive)."""
    lower_map = {c.lower(): c for c in df_cols}
    for cand in candidates:
        if cand in df_cols:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def _parse_bytes(content: bytes, filename: str) -> pd.DataFrame:
    """Parse CSV or Excel bytes into a DataFrame."""
    fname = filename.lower()
    if fname.endswith(".xlsx") or fname.endswith(".xls"):
        return pd.read_excel(io.BytesIO(content))
    # Default: CSV
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(io.StringIO(content.decode(enc)))
        except Exception:
            continue
    raise ValueError("Could not parse file as CSV or Excel.")


def _truthy(val) -> bool:
    """Convert various truth representations to bool."""
    if isinstance(val, bool):
        return val
    s = str(val).lower().strip()
    return s in ("true", "1", "yes", "y")


# ---------------------------------------------------------------------------
# Water data
# ---------------------------------------------------------------------------

def validate_water_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Validate and normalise an uploaded water DataFrame.
    Returns (normalised_df, validation_info).
    """
    cols = list(df.columns)
    info = {"dataset": "water", "valid": True, "errors": [], "warnings": [], "detected_columns": {}}

    date_col  = _find_col(cols, _DATE_COLS)
    hour_col  = _find_col(cols, _HOUR_COLS)
    usage_col = _find_col(cols, _W_USAGE)
    loc_col   = _find_col(cols, _W_LOCATION)
    anom_col  = _find_col(cols, _W_ANOMALY)

    if not usage_col:
        info["valid"] = False
        info["errors"].append(
            "No water usage column found. Expected one of: usage_liters, liters, consumption, flow, volume."
        )
        return df, info

    info["detected_columns"] = {
        "date": date_col, "hour": hour_col, "usage": usage_col,
        "location": loc_col, "anomaly": anom_col,
    }

    # Build normalised frame
    out = pd.DataFrame()
    out["usage_liters"] = pd.to_numeric(df[usage_col], errors="coerce").fillna(0)

    # Date column
    if date_col:
        out["date"] = df[date_col].astype(str)
    else:
        out["date"] = "2024-01-15"
        info["warnings"].append("No date column found — using placeholder date.")

    # Hour column — derive from datetime if absent
    if hour_col:
        out["hour"] = pd.to_numeric(df[hour_col], errors="coerce").fillna(0).astype(int)
    elif date_col:
        try:
            parsed = pd.to_datetime(df[date_col], errors="coerce")
            out["hour"] = parsed.dt.hour.fillna(0).astype(int)
            info["warnings"].append("Hour derived from datetime column.")
        except Exception:
            out["hour"] = 0
            info["warnings"].append("Could not derive hour — using 0.")
    else:
        out["hour"] = 0
        info["warnings"].append("No hour column — using 0.")

    out["location"] = df[loc_col].astype(str) if loc_col else "Main Building"

    if anom_col:
        out["anomaly"] = df[anom_col].apply(_truthy)
    else:
        out["anomaly"] = False  # will be auto-detected later
        info["warnings"].append("No anomaly column — anomalies will be auto-detected.")

    # Stats
    info["record_count"]       = len(out)
    info["date_range"]         = f"{out['date'].min()} to {out['date'].max()}"
    info["buildings_detected"] = out["location"].unique().tolist()
    info["avg_usage_liters"]   = round(float(out["usage_liters"].mean()), 1)
    info["total_liters"]       = round(float(out["usage_liters"].sum()), 1)
    info["anomaly_pre_labeled"] = bool(anom_col)

    return out, info


def auto_detect_anomalies_water(df: pd.DataFrame) -> pd.DataFrame:
    """Set anomaly=True for night-hour readings > 4× baseline, if not pre-labeled."""
    night_hours = list(range(0, 6))
    night_mask  = df["hour"].isin(night_hours)
    night_vals  = df.loc[night_mask & ~df["anomaly"], "usage_liters"]
    baseline    = float(night_vals.mean()) if len(night_vals) > 0 else 12.0
    df = df.copy()
    df.loc[night_mask, "anomaly"] = df.loc[night_mask, "usage_liters"] > baseline * 4
    return df


# ---------------------------------------------------------------------------
# Energy data
# ---------------------------------------------------------------------------

def validate_energy_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    cols = list(df.columns)
    info = {"dataset": "energy", "valid": True, "errors": [], "warnings": [], "detected_columns": {}}

    date_col  = _find_col(cols, _DATE_COLS)
    hour_col  = _find_col(cols, _HOUR_COLS)
    usage_col = _find_col(cols, _E_USAGE)
    zone_col  = _find_col(cols, _E_ZONE)
    equip_col = _find_col(cols, _E_EQUIPMENT)
    anom_col  = _find_col(cols, _E_ANOMALY)

    if not usage_col:
        info["valid"] = False
        info["errors"].append(
            "No energy usage column found. Expected one of: usage_kwh, kwh, energy, electricity, consumption."
        )
        return df, info

    info["detected_columns"] = {
        "date": date_col, "hour": hour_col, "usage": usage_col,
        "zone": zone_col, "equipment": equip_col, "anomaly": anom_col,
    }

    out = pd.DataFrame()
    out["usage_kwh"] = pd.to_numeric(df[usage_col], errors="coerce").fillna(0)

    if date_col:
        out["date"] = df[date_col].astype(str)
    else:
        out["date"] = "2024-01-15"
        info["warnings"].append("No date column — using placeholder.")

    if hour_col:
        out["hour"] = pd.to_numeric(df[hour_col], errors="coerce").fillna(0).astype(int)
    elif date_col:
        try:
            parsed = pd.to_datetime(df[date_col], errors="coerce")
            out["hour"] = parsed.dt.hour.fillna(0).astype(int)
            info["warnings"].append("Hour derived from datetime column.")
        except Exception:
            out["hour"] = 0
    else:
        out["hour"] = 0

    out["zone"]      = df[zone_col].astype(str)  if zone_col  else "Main Zone"
    out["equipment"] = df[equip_col].astype(str) if equip_col else "Mixed"

    if anom_col:
        out["anomaly"] = df[anom_col].apply(_truthy)
    else:
        out["anomaly"] = False
        info["warnings"].append("No anomaly column — anomalies will be auto-detected.")

    info["record_count"]      = len(out)
    info["date_range"]        = f"{out['date'].min()} to {out['date'].max()}"
    info["zones_detected"]    = out["zone"].unique().tolist()
    info["avg_usage_kwh"]     = round(float(out["usage_kwh"].mean()), 2)
    info["total_kwh"]         = round(float(out["usage_kwh"].sum()), 2)
    info["anomaly_pre_labeled"] = bool(anom_col)

    return out, info


def auto_detect_anomalies_energy(df: pd.DataFrame) -> pd.DataFrame:
    """Flag after-hours readings > threshold as anomalies, if not pre-labeled."""
    after_hours = list(range(0, 6)) + [22, 23]
    ah_mask     = df["hour"].isin(after_hours)
    ah_vals     = df.loc[ah_mask & ~df["anomaly"], "usage_kwh"]
    baseline    = float(ah_vals.mean()) if len(ah_vals) > 0 else 2.5
    df = df.copy()
    df.loc[ah_mask, "anomaly"] = df.loc[ah_mask, "usage_kwh"] > baseline * 3.5
    return df


# ---------------------------------------------------------------------------
# Fuel data
# ---------------------------------------------------------------------------

def validate_fuel_df(df: pd.DataFrame) -> Tuple[dict, dict]:
    """
    Parse a fuel consumption CSV/Excel.
    Returns (fuel_summary, validation_info).
    """
    cols = list(df.columns)
    info = {"dataset": "fuel", "valid": True, "errors": [], "warnings": []}

    type_col = _find_col(cols, _FUEL_TYPE)
    qty_col  = _find_col(cols, _FUEL_QTY)

    if not qty_col:
        info["valid"] = False
        info["errors"].append("No fuel quantity column found. Expected: quantity, liters, consumption, usage.")
        return {}, info

    total_co2   = 0.0
    total_liters = 0.0
    # breakdown: { ftype: { liters, co2_kg, emission_factor } }
    breakdown   = {}

    if type_col:
        for _, row in df.iterrows():
            ftype  = str(row[type_col]).strip().lower()
            qty    = float(str(row[qty_col]).replace(",", "")) if pd.notna(row[qty_col]) else 0
            factor = FUEL_EMISSION_FACTORS.get(ftype, 2.5)
            co2    = qty * factor
            total_co2    += co2
            total_liters += qty
            if ftype not in breakdown:
                breakdown[ftype] = {"liters": 0.0, "co2_kg": 0.0, "emission_factor": factor}
            breakdown[ftype]["liters"] += qty
            breakdown[ftype]["co2_kg"] += co2

        # Round all values
        for k in breakdown:
            breakdown[k]["liters"] = round(breakdown[k]["liters"], 2)
            breakdown[k]["co2_kg"] = round(breakdown[k]["co2_kg"], 2)
    else:
        total_qty   = pd.to_numeric(df[qty_col], errors="coerce").fillna(0).sum()
        total_liters = float(total_qty)
        total_co2   = total_liters * 2.5
        info["warnings"].append("No fuel type column found — using generic emission factor (2.5 kg CO₂/unit).")
        breakdown["unknown"] = {"liters": round(total_liters, 2), "co2_kg": round(total_co2, 2), "emission_factor": 2.5}

    info["record_count"] = len(df)

    return {
        "source":          "uploaded_file",
        "total_co2_kg":    round(total_co2, 2),
        "total_liters":    round(total_liters, 2),
        "breakdown":       breakdown,
        "emission_method": "Deterministic emission factors (IPCC 2006 / BEE India)",
    }, info


# ---------------------------------------------------------------------------
# Coverage and confidence
# ---------------------------------------------------------------------------

_DATASET_WEIGHTS = {
    "water":     0.30,
    "energy":    0.30,
    "waste":     0.15,
    "fuel":      0.15,
    "occupancy": 0.10,
}

_CONFIDENCE_PENALTIES = {
    "water":   0.20,
    "energy":  0.20,
    "waste":   0.08,
    "fuel":    0.08,
    "occupancy": 0.04,
}


def compute_coverage(available_datasets: list) -> dict:
    """
    Given a list of available dataset names, compute coverage %, confidence %,
    and mission readiness %.
    """
    weighted_coverage = sum(
        _DATASET_WEIGHTS.get(d, 0) for d in available_datasets
    )
    coverage_pct = round(weighted_coverage * 100, 1)

    # Confidence starts at 100% and drops for each missing high-value dataset
    confidence = 1.0
    for ds, penalty in _CONFIDENCE_PENALTIES.items():
        if ds not in available_datasets:
            confidence -= penalty
    confidence_pct = round(max(0, confidence) * 100, 1)

    # Mission readiness: blend of coverage and confidence
    readiness_pct = round((coverage_pct * 0.6 + confidence_pct * 0.4), 1)

    missing = [ds for ds in _DATASET_WEIGHTS if ds not in available_datasets]

    return {
        "available_datasets":  available_datasets,
        "missing_datasets":    missing,
        "data_coverage_pct":   coverage_pct,
        "analysis_confidence_pct": confidence_pct,
        "mission_readiness_pct":   readiness_pct,
        "carbon_source":       "Automatic — derived from uploaded resource data",
        "note": (
            "Analysis confidence decreases when high-value datasets (water, energy) are absent. "
            "All present datasets are analysed fully. Missing datasets are skipped and documented."
        ),
    }


# ---------------------------------------------------------------------------
# Manual entry helpers
# ---------------------------------------------------------------------------

_PERIOD_TO_WEEKLY_WATER = {
    "hourly":  24 * 7,       # 1 L/hr  → 168 L/week
    "daily":   7,            # 1 L/day → 7 L/week
    "weekly":  1,            # direct
    "monthly": 12 / 52,      # 1 L/mo  → 12/52 L/week ≈ 0.231
}

_PERIOD_TO_WEEKLY_ENERGY = _PERIOD_TO_WEEKLY_WATER


def _deterministic_jitter(day: int, hour: int, scale: float = 0.08) -> float:
    """Return a small deterministic variation based on day+hour seed (no random)."""
    # Simple deterministic hash — avoids randomness while adding realistic variation
    seed = (day * 31 + hour * 7 + day * hour) % 100
    return 1.0 + (seed / 100.0 - 0.5) * scale * 2


def build_water_df_from_manual(
    value: float,
    period: str = "weekly",
    location: str = "Main Building",
) -> pd.DataFrame:
    """
    Build a synthetic 7-day hourly water DataFrame from an aggregate value.
    Applies realistic weekday/weekend demand curves with morning, lunch, and
    evening peaks. All values are deterministic — no random numbers used.
    `period` can be 'hourly', 'daily', 'weekly', or 'monthly'.
    """
    multiplier = _PERIOD_TO_WEEKLY_WATER.get(period, 1)
    weekly_liters = value * multiplier

    # Weekday diurnal profile — morning peak (7–9), lunch (12–13), evening (17–19)
    _WEEKDAY_WATER = [
        0.40, 0.35, 0.28, 0.25, 0.30, 0.55,   # 0–5  AM: very low night flow
        1.20, 3.20, 3.80, 3.40, 3.10, 2.70,   # 6–11 AM: morning peak
        3.00, 3.50, 2.80, 2.60, 2.50, 3.20,   # 12–17: lunch peak + afternoon
        2.80, 2.20, 1.60, 1.20, 0.90, 0.65,   # 18–23: evening wind-down
    ]
    # Weekend profile — flatter, slightly later start, lower overall
    _WEEKEND_WATER = [
        0.35, 0.30, 0.25, 0.22, 0.28, 0.50,
        0.90, 2.10, 2.80, 3.00, 2.90, 2.60,
        2.80, 3.10, 2.70, 2.50, 2.40, 2.60,
        2.30, 1.90, 1.40, 1.10, 0.85, 0.60,
    ]

    # Weekday total weight / weekend total weight — for balanced weekly total
    wd_sum = sum(_WEEKDAY_WATER) * 5
    we_sum = sum(_WEEKEND_WATER) * 2
    total_weight = wd_sum + we_sum

    rows = []
    for day in range(7):
        date_str = f"2024-01-{15 + day:02d}"
        is_weekend = day >= 5  # day 5=Sat, 6=Sun
        profile    = _WEEKEND_WATER if is_weekend else _WEEKDAY_WATER

        for hour, weight in enumerate(profile):
            # Scale to weekly total; apply small deterministic jitter
            jitter = _deterministic_jitter(day, hour, 0.06)
            liters = (weight / total_weight) * weekly_liters * jitter
            rows.append({
                "date":         date_str,
                "hour":         hour,
                "usage_liters": round(max(0.0, liters), 1),
                "location":     location,
                "anomaly":      False,
            })
    return pd.DataFrame(rows)


def build_energy_df_from_manual(
    value: float,
    period: str = "weekly",
    zone: str = "Main Zone",
) -> pd.DataFrame:
    """
    Build a synthetic 7-day hourly energy DataFrame from an aggregate value.
    Applies realistic weekday/weekend demand curves with morning ramp, midday
    plateau, and after-hours base load. All values are deterministic.
    `period` can be 'hourly', 'daily', 'weekly', or 'monthly'.
    """
    multiplier = _PERIOD_TO_WEEKLY_ENERGY.get(period, 1)
    weekly_kwh = value * multiplier

    # Weekday energy profile — ramps up at 7, plateau 9–17, drops after 18
    _WEEKDAY_ENERGY = [
        1.0, 0.9, 0.8, 0.8, 0.9, 1.2,    # 0–5  AM: base load / standby
        2.0, 5.5, 9.0, 10.0, 10.0, 9.5,  # 6–11 AM: morning ramp + peak
        9.0, 9.0, 8.5, 8.5, 8.0, 6.5,    # 12–17: peak + afternoon
        5.0, 3.8, 2.8, 2.2, 1.7, 1.3,    # 18–23: wind-down
    ]
    # Weekend profile — lower peak, later start, higher night base (HVAC continues)
    _WEEKEND_ENERGY = [
        1.2, 1.0, 0.9, 0.8, 0.9, 1.1,
        1.5, 3.2, 5.5, 6.5, 6.5, 6.0,
        6.0, 6.0, 5.5, 5.5, 5.0, 4.2,
        3.5, 2.8, 2.2, 1.8, 1.5, 1.3,
    ]

    wd_sum = sum(_WEEKDAY_ENERGY) * 5
    we_sum = sum(_WEEKEND_ENERGY) * 2
    total_weight = wd_sum + we_sum

    rows = []
    for day in range(7):
        date_str   = f"2024-01-{15 + day:02d}"
        is_weekend = day >= 5
        profile    = _WEEKEND_ENERGY if is_weekend else _WEEKDAY_ENERGY

        for hour, weight in enumerate(profile):
            jitter = _deterministic_jitter(day, hour, 0.05)
            kwh    = (weight / total_weight) * weekly_kwh * jitter
            rows.append({
                "date":      date_str,
                "hour":      hour,
                "usage_kwh": round(max(0.0, kwh), 2),
                "zone":      zone,
                "equipment": "Mixed",
                "anomaly":   False,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Skipped agent result stubs
# ---------------------------------------------------------------------------

def detect_analysis_level(df=None, is_manual: bool = False) -> dict:
    """
    Classify uploaded data into one of three analysis levels.

    Level 1 — Basic Sustainability Assessment
        Manual entry or < 3 days of data.  No anomaly detection.
    Level 2 — Operational Analysis
        Daily/weekly file with ≥ 3 distinct dates.  Trend analysis only.
    Level 3 — Advanced AI Analysis
        Hourly file, ≥ 12 unique hour slots, ≥ 3 days, ≥ 48 records.
        Full anomaly detection enabled.
    """
    if is_manual or df is None:
        return {
            "level": 1,
            "code": "level1",
            "label": "Basic Sustainability Assessment",
            "confidence_range": "Low–Medium",
            "anomaly_detection_available": False,
            "reasoning": (
                "Manual entry — a synthetic consumption profile is generated for "
                "estimation purposes only. Anomaly detection, leak detection, and "
                "predictive maintenance require actual operational logs with "
                "time-series resolution."
            ),
        }

    n_records    = len(df)
    unique_hours = int(df["hour"].nunique()) if "hour" in df.columns else 1
    unique_dates = int(df["date"].nunique()) if "date" in df.columns else 1

    if unique_hours >= 12 and unique_dates >= 3 and n_records >= 48:
        return {
            "level": 3,
            "code": "level3",
            "label": "Advanced AI Analysis",
            "confidence_range": "High–Very High",
            "anomaly_detection_available": True,
            "reasoning": (
                f"Hourly operational logs — {n_records:,} records across "
                f"{unique_dates} days with {unique_hours} distinct hour slots. "
                "Full anomaly detection, night-flow analysis, and pattern recognition available."
            ),
        }
    elif unique_dates >= 3 and n_records >= 3:
        return {
            "level": 2,
            "code": "level2",
            "label": "Operational Analysis",
            "confidence_range": "Medium–High",
            "anomaly_detection_available": False,
            "reasoning": (
                f"Daily/weekly operational data — {n_records} records across {unique_dates} days. "
                "Trend analysis and consumption benchmarking available. "
                "Hourly logs (≥ 3 days, ≥ 12 hour slots) are required for anomaly detection."
            ),
        }
    else:
        return {
            "level": 1,
            "code": "level1",
            "label": "Basic Sustainability Assessment",
            "confidence_range": "Low–Medium",
            "anomaly_detection_available": False,
            "reasoning": (
                f"Limited data — {n_records} record(s) across {unique_dates} day(s). "
                "Provide daily or hourly logs covering ≥ 3 days for operational trend analysis."
            ),
        }


def skipped_water_result(reason: str = "No water data provided") -> dict:
    return {
        "agent": "Water Leakage Agent",
        "status": "skipped",
        "skip_reason": reason,
        "total_wasted_liters": 0,
        "severity": "none",
        "severity_score": 50,
        "estimated_cost_inr": 0,
        "co2_equivalent_kg": 0,
        "anomaly_events": [],
        "recommendations": ["Upload water usage data to enable water leakage analysis."],
        "hourly_chart_data": [],
        "reasoning_trace": [f"Skipped — {reason}"],
        "confidence": 0,
    }


def skipped_energy_result(reason: str = "No energy data provided") -> dict:
    return {
        "agent": "Energy Optimization Agent",
        "status": "skipped",
        "skip_reason": reason,
        "total_wasted_kwh": 0,
        "severity": "none",
        "severity_score": 50,
        "estimated_cost_inr": 0,
        "co2_equivalent_kg": 0,
        "anomaly_events": [],
        "recommendations": ["Upload energy usage data to enable after-hours waste analysis."],
        "hourly_chart_data": [],
        "reasoning_trace": [f"Skipped — {reason}"],
        "confidence": 0,
    }
