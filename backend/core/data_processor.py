"""
data_processor.py — Upload pipeline: parse, validate, normalise, auto-detect anomalies.

All computations are deterministic (no LLM). Handles CSV and Excel (.xlsx).
Column detection is flexible: tries canonical names, then common synonyms.
"""

import io
import json
import csv
import re
import logging
from typing import Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Column synonym maps
# ---------------------------------------------------------------------------

_DATE_COLS   = {"date", "Date", "timestamp", "Timestamp", "reading_timestamp", "reading_date", "datetime", "Datetime", "time", "Time", "day"}
_HOUR_COLS   = {"hour", "Hour", "hr", "Hr", "time_hour"}
_W_USAGE     = {"usage_liters", "usage_l", "liters", "litres", "usage", "consumption",
                "flow_liters", "water_usage", "volume", "quantity_liters", "amount_liters", "water_consumption", "consumption_liters", "consumption_kl", "consumption_m3", "cumulative_liters", "cumulative_m3", "water_counter", "flow_lpm", "flow_lps", "flow_m3_h", "reading", "meter_reading", "value"}
_W_LOCATION  = {"location", "Location", "building", "building_id", "Building", "site", "facility", "department", "zone", "Zone", "area", "Area", "block"}
_W_ANOMALY   = {"anomaly", "Anomaly", "is_anomaly", "flag", "Flag", "leak", "Leak", "alert"}

_E_USAGE     = {"usage_kwh", "kwh", "kWh", "KWH", "energy", "Energy", "consumption",
                "electricity", "usage", "amount_kwh", "energy_consumption", "consumption_kwh", "cumulative_kwh", "energy_counter", "power_kw", "power_w", "reading", "meter_reading", "value"}
_E_ZONE      = {"zone", "Zone", "area", "Area", "building", "building_id", "Building", "location", "department", "Department"}
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
    names = {c.casefold() for c in candidates}
    matches = [column for column in df_cols if str(column).casefold() in names]
    if len(matches) > 1:
        raise ValueError("Ambiguous columns. Map or rename columns before analysis.")
    return matches[0] if matches else None


def _parse_bytes(content: bytes, filename: str, mapping: dict | None = None) -> pd.DataFrame:
    import zipfile

    if len(content) > 20 * 1024 * 1024:
        raise ValueError("File exceeds 20 MB.")
    limit = 50000
    if filename.lower().endswith(".xlsx"):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            members = archive.infolist()
            if len(members) > 512 or sum(m.file_size for m in members) > 32 * 1024 * 1024:
                raise ValueError("Workbook exceeds processing limits.")
            from defusedxml.ElementTree import iterparse
            from openpyxl.utils.cell import column_index_from_string
            for member in members:
                if not re.fullmatch(r"xl/worksheets/[^/]+\.xml", member.filename):
                    continue
                with archive.open(member) as sheet:
                    for _, element in iterparse(sheet, events=("end",)):
                        tag = element.tag.rsplit("}", 1)[-1]
                        if tag in ("c", "dimension"):
                            ref = element.get("r" if tag == "c" else "ref", "").split(":")[-1]
                            coord = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,6})", ref)
                            if not coord or column_index_from_string(coord[1]) > 128 or int(coord[2]) > limit+1:
                                raise ValueError("Worksheet dimensions exceed processing limits.")
                        element.clear()
        frame = pd.read_excel(io.BytesIO(content), nrows=limit + 1, engine="openpyxl")
    elif filename.lower().endswith(".csv"):
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded = content.decode("latin-1")
        reader = csv.reader(io.StringIO(decoded, newline=""), strict=True)
        columns = next(reader, [])
        if not 1 <= len(columns) <= 128 or len(set(columns)) != len(columns):
            raise ValueError("Invalid or duplicate CSV columns.")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(columns) or len(rows) >= limit or (len(rows)+1)*len(columns) > 1000000:
                raise ValueError("Inconsistent rows or CSV processing limit exceeded.")
            rows.append(row)
        frame = pd.DataFrame(rows, columns=columns)
    elif filename.lower().endswith(".json"):
        if len(content) > 2 * 1024 * 1024:
            raise ValueError("JSON exceeds 2 MB.")
        records = json.loads(content)
        if (not isinstance(records, list) or len(records) > limit or any(
                not isinstance(r, dict) or len(r) > 128 or any(isinstance(v, (dict, list)) for v in r.values()) for r in records)):
            raise ValueError("Expected an array of flat observation records.")
        frame = pd.DataFrame(records)
    else:
        raise ValueError("Expected CSV, XLSX or JSON.")
    if frame.empty or len(frame) > limit or len(frame.columns) > 128:
        raise ValueError("Expected 1–50000 data rows and at most 128 columns.")
    if mapping:
        if not isinstance(mapping, dict) or not set(mapping) <= set(frame.columns) or any(
                not isinstance(v, str) or not 1 <= len(v) <= 100 for v in mapping.values()):
            raise ValueError("Invalid column mapping.")
        frame = frame.rename(columns=mapping)
        if not frame.columns.is_unique:
            raise ValueError("Column mapping has duplicate destinations.")
    return frame


def _truthy(val) -> bool:
    """Convert various truth representations to bool."""
    if isinstance(val, bool):
        return val
    s = str(val).lower().strip()
    return s in ("true", "1", "yes", "y")


# ---------------------------------------------------------------------------
# Water data
# ---------------------------------------------------------------------------

UNIT_CONVERSION = {"L":("L",1), "mL":("L",0.001), "kL":("L",1000), "m3":("L",1000),
                  "kWh":("kWh",1), "Wh":("kWh",0.001), "kW":("kW",1), "W":("kW",0.001)}


_MEASUREMENT_TYPES = {
    "interval": "interval", "interval_consumption": "interval", "consumption": "interval",
    "cumulative": "counter", "counter": "counter", "cumulative_meter": "counter",
    "water_counter": "counter", "energy_counter": "counter",
    "instantaneous": "rate", "flow": "rate", "power": "rate",
    "daily": "daily", "daily_total": "daily", "monthly": "monthly", "monthly_total": "monthly",
}


def _resource_rows(frame, names):
    column = _find_col(list(frame.columns), {"resource", "resource_type"})
    return frame[frame[column].astype(str).str.strip().str.casefold().isin(names)].copy() if column else frame.copy()


def _observation_fields(frame, out, info, date_col, hour_col, usage_col, metric, units):
    cols = list(frame.columns)
    header = str(usage_col).casefold()
    identified = "counter" if "cumulative" in header or header.endswith("_counter") else (
        "rate" if header.startswith(("power_", "flow_lp", "flow_m3_")) else None)
    kind_col = _find_col(cols, {"reading_type", "measurement_type"})
    kinds = set(frame[kind_col].astype(str).str.strip().str.casefold().map(_MEASUREMENT_TYPES)) if kind_col else set()
    if (kind_col and (len(kinds) != 1 or None in kinds or any(pd.isna(value) for value in kinds))) or (
            identified and kinds and identified not in kinds):
        info["errors"].append("Use one consistent measurement type per resource file.")
    kind = next(iter(kinds), identified or "interval")
    if not kind_col and header in {"reading", "meter_reading", "value"}:
        info["errors"].append("Specify reading_type: interval, cumulative, instantaneous, daily or monthly.")
    if info["errors"]:
        info["valid"] = False
        return
    info["measurement_type"] = kind
    if not kind_col and not identified:
        info["warnings"].append("Usage columns are treated as interval quantities. Supply a reading type for cumulative, instantaneous or billing records.")
    canonical = "L" if metric == "usage_liters" else "kWh"
    scales = {key.casefold(): factor for key, (target, factor) in UNIT_CONVERSION.items() if target == canonical}
    scales.update({alias: 1 for alias in units})
    scales.update({"m³": 1000, "kilolitres": 1000, "kiloliters": 1000} if canonical == "L" else {})
    if kind == "rate":
        scales = {"l/min": 60, "lpm": 60, "l/s": 3600, "lps": 3600, "m3/h": 1000, "m³/h": 1000,
                  "l/h": 1} if canonical == "L" else {"kw": 1, "w": 0.001}
    hinted = {"flow_lpm":"lpm", "flow_lps":"lps", "flow_m3_h":"m3/h", "power_kw":"kw", "power_w":"w",
              "consumption_m3":"m3", "cumulative_m3":"m3", "consumption_kl":"kl", "cumulative_liters":"l",
              "cumulative_kwh":"kwh"}
    unit_col = _find_col(cols, {"unit", "units", "measurement_unit"})
    supplied = frame[unit_col].astype(str).str.casefold().str.strip() if unit_col else hinted.get(header, canonical.casefold())
    factors = supplied.map(scales) if unit_col else scales.get(supplied)
    if factors is None or unit_col and factors.isna().any():
        info["errors"].append("Measurement unit is incompatible or missing for this reading type.")
        info["valid"] = False
        return
    raw = frame[usage_col]
    present = raw.notna() & raw.astype(str).str.strip().ne("")
    numeric = pd.to_numeric(raw, errors="coerce")
    if not numeric[present].between(0, 1e12).all() or not present.any():
        info["errors"].append("Provide at least one finite, nonnegative measurement. Leave unavailable cells blank.")
        info["valid"] = False
        return
    info["missing_values"] = int((~present).sum())
    if info["missing_values"]:
        info["warnings"].append("Blank measurements were excluded. No values were filled.")
    out[metric] = numeric * factors
    if not out[metric][present].between(0, 1e12).all():
        info["errors"].append("Normalized measurement exceeds the supported range.")
    if date_col:
        def local_time(raw_value):
            if isinstance(raw_value, (int, float)):
                raise ValueError("Use a calendar timestamp")
            if isinstance(raw_value, str):
                ambiguous = re.match(r"^([0-9]{1,2})[/-]([0-9]{1,2})[/-][0-9]{4}(?:\D|$)", raw_value.strip())
                if ambiguous and all(1 <= int(part) <= 12 for part in ambiguous.groups()):
                    raise ValueError("Ambiguous calendar date")
            value = pd.to_datetime(raw_value, errors="raise")
            if pd.isna(value):
                raise ValueError("Missing timestamp")
            return value.tz_localize("Asia/Kolkata") if value.tzinfo is None else value.tz_convert("Asia/Kolkata")
        try:
            parsed = frame[date_col].map(local_time)
        except (ValueError, TypeError, OverflowError):
            info["errors"].append("Provide valid observation timestamps; use ISO dates for unambiguous day/month order.")
            info["valid"] = False
            return
        has_time = frame[date_col].astype(str).str.contains(r"\d:\d")
        out["date"] = parsed.dt.strftime("%Y-%m-%d")
        out["hour"] = parsed.dt.hour.where(has_time) if kind not in {"daily", "monthly"} else None
        info["timezone"] = "Asia/Kolkata"
    else:
        has_time = pd.Series(False, index=frame.index)
        out["date"], out["hour"] = "Unknown", None
        info["warnings"].append("Reporting dates unavailable.")
    if hour_col:
        hours = pd.to_numeric(frame[hour_col], errors="coerce")
        if not (hours.between(0, 23) & (hours % 1 == 0)).all() or kind in {"daily", "monthly"}:
            info["errors"].append("Use a valid 0–23 hour only for interval observations.")
        else:
            out["hour"] = hours.astype(int)
            if date_col:
                if not (parsed.dt.hour[has_time] == hours[has_time]).all():
                    info["errors"].append("Hour conflicts with the timestamp.")
                parsed = parsed + pd.to_timedelta(hours.where(~has_time, 0), unit="h")
    if date_col:
        out["timestamp"] = parsed.dt.tz_convert("UTC")
    device_col = _find_col(cols, {"device_id", "meter_id", "meter", "meter_identifier", "sensor_id"})
    if device_col:
        out["device_id"] = frame[device_col].fillna("").astype(str).str.strip()
        if out["device_id"].eq("").any():
            info["errors"].append("Provide a meter identifier on every row when a meter column is supplied.")
    for context in ("scheduled", "occupied", "estimated"):
        source = _find_col(cols, {context, f"is_{context}"})
        if source:
            labels = frame[source].astype(str).str.strip().str.casefold()
            out[context] = labels.map({"true":True, "1":True, "yes":True, "false":False, "0":False, "no":False})
            if (frame[source].notna() & labels.ne("") & out[context].isna()).any():
                info["errors"].append(f"Use yes or no for {context} when known.")
    interval_col = _find_col(cols, {"interval_seconds", "duration_seconds"})
    if interval_col and kind == "interval":
        duration = pd.to_numeric(frame[interval_col], errors="coerce")
        if not duration.between(1, 86400).all():
            info["errors"].append("Interval duration must be 1 to 86400 seconds.")
        out["interval_seconds"] = duration
    rollover_col = _find_col(cols, {"counter_rollover", "rollover_value"})
    rollover_ref = _find_col(cols, {"rollover_reference"})
    if rollover_col or rollover_ref:
        if kind != "counter" or not rollover_col or not rollover_ref:
            info["errors"].append("Document counter rollover with its limit and reference.")
        else:
            out["counter_rollover"] = pd.to_numeric(frame[rollover_col], errors="coerce") * factors
            out["rollover_reference"] = frame[rollover_ref].fillna("").astype(str).str.strip()
            if not (out["counter_rollover"].between(1, 1e12).all() and out["rollover_reference"].ne("").all()
                    and (out["counter_rollover"][present] > out[metric][present]).all()):
                info["errors"].append("Rollover limits must exceed observed readings and have a documented reference.")
    out["reading_type"] = kind
    if kind in {"daily", "monthly"} and not date_col:
        info["errors"].append("Provide the observation date for daily or monthly measurements.")
    if kind in {"counter", "rate"} and (not date_col or not (has_time.all() or hour_col)):
        info["errors"].append("Counter and instantaneous readings require timestamped endpoints for each meter.")
    info["valid"] = not info["errors"]


def _normalize_intervals(frame, out, info, metric, zone):
    if out.empty:
        info["valid"] = False
        info["errors"].append("No rows match the requested resource.")
        return out
    kind = info["measurement_type"]
    grouping = ["device_id"] if "device_id" in out else [zone]
    if "device_id" in out and (out.groupby("device_id")[zone].nunique() > 1).any():
        info["errors"].append("A meter appears in multiple zones. Split the observations by meter assignment.")
    dedupe = [*grouping, "timestamp"]
    if "timestamp" in out:
        raw_duplicate = frame.duplicated()
        info["duplicates_removed"] = int(raw_duplicate.sum())
        out = out.loc[~raw_duplicate].sort_values("timestamp", kind="stable").copy()
        if out.duplicated(dedupe).any():
            info["errors"].append("Conflicting readings share a device timestamp. Supply distinct meter IDs or resolve conflicts.")
        if info["duplicates_removed"]:
            info["warnings"].append("Identical source rows were counted once.")
    if kind in {"daily", "monthly"} and "timestamp" in out:
        dates = out["date"].str.slice(stop=7) if kind == "monthly" else out["date"]
        if out.assign(period_key=dates).duplicated([*grouping, "period_key"]).any():
            info["errors"].append("Multiple observations for the same meter and reporting period.")
    if kind in {"counter", "rate"} and not info["errors"]:
        groups = out.groupby(grouping, dropna=False)
        elapsed = groups["timestamp"].diff().dt.total_seconds()
        nominal = elapsed.groupby(out[grouping[0]]).transform("median")
        estimated = out.get("estimated", pd.Series(False, index=out.index)).eq(True)
        earlier_estimated = estimated.groupby(out[grouping[0]]).shift().eq(True)
        previous = groups[metric].shift()
        delta = out[metric] - previous
        maximum_gap = nominal.mul(2).clip(upper=86400)
        valid = elapsed.gt(0) & elapsed.le(maximum_gap) & previous.notna() & out[metric].notna()
        resets = valid & delta.lt(0) if kind == "counter" else pd.Series(False, index=out.index)
        if "counter_rollover" in out:
            modulus = out["counter_rollover"]
            rollover = (resets & modulus.eq(groups["counter_rollover"].shift())
                        & out["rollover_reference"].eq(groups["rollover_reference"].shift())
                        & previous.ge(modulus * 0.9) & out[metric].le(modulus * 0.1))
            delta = delta.where(~rollover, delta + modulus)
            resets = resets & ~rollover
            info["counter_rollovers"] = int(rollover.sum())
            if info["counter_rollovers"]:
                info["warnings"].append("Boundary crossings used the documented meter rollover value.")
        if kind == "rate" and metric == "usage_kwh":
            measured = out.loc[~estimated, metric].dropna()
            info["peak_observed_demand_kw"] = float(measured.max()) if not measured.empty and len(groups) == 1 else None
        for context in ("scheduled", "occupied"):
            if context in out:
                out[context] = out[context].where(out[context].eq(groups[context].shift()))
        out["sample_value"] = out[metric]
        out["interval_seconds"] = elapsed
        out["estimated"] = estimated | earlier_estimated | (kind == "rate")
        out[metric] = ((out[metric] + previous) / 2 * elapsed / 3600 if kind == "rate" else delta).where(valid & ~resets)
        info["counter_resets"] = int(resets.sum())
        info["intervals_excluded"] = int((elapsed.notna() & (~valid | resets)).sum())
        if kind == "rate":
            info["warnings"].append("Totals use trapezoidal integration between observed endpoints and are estimates.")
        if info["intervals_excluded"]:
            info["warnings"].append("Unsupported gaps, missing endpoints and counter resets were excluded from totals.")
    out = out.dropna(subset=[metric])
    if not out[metric].between(0, 1e12).all():
        info["errors"].append("Computed intervals exceed the supported range.")
    if out.empty:
        info["errors"].append("No defensible consumption intervals. Provide additional comparable readings.")
    info["valid"] = not info["errors"]
    return out


def validate_water_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Validate and normalise an uploaded water DataFrame.
    Returns (normalised_df, validation_info).
    """
    df = _resource_rows(df, {"water"})
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
    _observation_fields(df, out, info, date_col, hour_col, usage_col, "usage_liters", {"l", "liter", "litre", "liters", "litres"})
    if not info["valid"]:
        return df, info

    out["location"] = df[loc_col].fillna("Unspecified").astype(str) if loc_col else "Unspecified"

    if anom_col:
        out["anomaly"] = df[anom_col].apply(_truthy)
    else:
        out["anomaly"] = False  # will be auto-detected later
        info["warnings"].append("No anomaly column — anomalies will be auto-detected.")

    # Stats
    out = _normalize_intervals(df, out, info, "usage_liters", "location")
    if not info["valid"]:
        return df, info
    if "timestamp" in out:
        out["timestamp"] = out["timestamp"].astype(str)
    out.attrs["validation"] = info

    info["record_count"]       = len(out)
    info["date_range"]         = f"{out['date'].min()} to {out['date'].max()}"
    info["buildings_detected"] = out["location"].unique().tolist()
    info["avg_usage_liters"]   = round(float(out["usage_liters"].mean()), 1)
    info["total_liters"]       = round(float(out["usage_liters"].sum()), 1)
    info["anomaly_pre_labeled"] = bool(anom_col)

    return out, info


# ---------------------------------------------------------------------------
# Energy data
# ---------------------------------------------------------------------------

def validate_energy_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    df = _resource_rows(df, {"energy", "electricity"})
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
    _observation_fields(df, out, info, date_col, hour_col, usage_col, "usage_kwh", {"kwh"})
    if not info["valid"]:
        return df, info

    out["zone"]      = df[zone_col].fillna("Unspecified").astype(str) if zone_col else "Unspecified"
    out["equipment"] = df[equip_col].fillna("Unspecified").astype(str) if equip_col else "Unspecified"

    if anom_col:
        out["anomaly"] = df[anom_col].apply(_truthy)
    else:
        out["anomaly"] = False
        info["warnings"].append("No anomaly column — anomalies will be auto-detected.")

    out = _normalize_intervals(df, out, info, "usage_kwh", "zone")
    if not info["valid"]:
        return df, info
    if "timestamp" in out:
        out["timestamp"] = out["timestamp"].astype(str)
    out.attrs["validation"] = info

    info["record_count"]      = len(out)
    info["date_range"]        = f"{out['date'].min()} to {out['date'].max()}"
    info["zones_detected"]    = out["zone"].unique().tolist()
    info["avg_usage_kwh"]     = round(float(out["usage_kwh"].mean()), 2)
    info["total_kwh"]         = round(float(out["usage_kwh"].sum()), 2)
    info["anomaly_pre_labeled"] = bool(anom_col)

    return out, info


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

    if not type_col:
        info.update(valid=False, errors=["Fuel type and compatible units are required."])
        return {}, info
    unit_col = _find_col(cols, _FUEL_UNIT)
    breakdown = {}
    total_co2 = 0.0
    total_liters = 0.0
    for _, row in df.iterrows():
        fuel = str(row[type_col]).strip().lower()
        factor = FUEL_EMISSION_FACTORS.get(fuel)
        unit = {"coal": "kg", "cng": "kg", "natural gas": "m3"}.get(fuel, "l")
        supplied = str(row[unit_col]).strip().lower() if unit_col else (
            "l" if str(qty_col).lower() in ("liters", "litres", "quantity_liters") else "")
        supplied = {"liters": "l", "litres": "l", "m³": "m3"}.get(supplied, supplied)
        qty = pd.to_numeric(row[qty_col], errors="coerce")
        if factor is None or supplied != unit or not 0 <= qty < float("inf"):
            info.update(valid=False, errors=["Unknown fuel, incompatible unit or invalid fuel quantity."])
            return {}, info
        entry = breakdown.setdefault(fuel, {"quantity": 0.0, "unit": unit, "co2_kg": 0.0, "emission_factor": factor})
        entry["quantity"] += float(qty)
        entry["co2_kg"] += float(qty) * factor
        total_co2 += float(qty) * factor
        if unit == "l":
            total_liters += float(qty)
            entry["liters"] = entry["quantity"]

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

def compute_coverage(available_datasets: list) -> dict:
    coverage_pct = round(100 * sum(_DATASET_WEIGHTS.get(d, 0) for d in set(available_datasets)), 1)
    missing = [ds for ds in _DATASET_WEIGHTS if ds not in available_datasets]

    return {
        "available_datasets":  available_datasets,
        "missing_datasets":    missing,
        "data_coverage_pct":   coverage_pct,
        "analysis_confidence_pct": None,
        "mission_readiness_pct": coverage_pct,
        "weights": _DATASET_WEIGHTS,
        "carbon_source":       "Automatic — derived from uploaded resource data",
        "note": (
            "Coverage is the weighted share of supplied datasets. "
            "All present datasets are analysed fully. Missing datasets are skipped and documented."
        ),
    }


# ---------------------------------------------------------------------------
# Manual entry helpers
# ---------------------------------------------------------------------------

PERIOD_DAYS = {"hourly": 1 / 24, "daily": 1, "weekly": 7, "monthly": 30}


def build_water_df_from_manual(value: float, period: str = "weekly", location: str = "Unspecified"):
    return pd.DataFrame([{"usage_liters": value, "location": location, "anomaly": False,
                          "hour": None, "date": None}])


def build_energy_df_from_manual(value: float, period: str = "weekly", zone: str = "Unspecified"):
    return pd.DataFrame([{"usage_kwh": value, "zone": zone, "equipment": "Unspecified",
                          "anomaly": False, "hour": None, "date": None}])


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
            "confidence_range": None,
            "anomaly_detection_available": False,
            "reasoning": (
                "Manual entry provides a single aggregate. Anomaly detection, leak detection, and "
                "predictive maintenance require actual operational logs with "
                "time-series resolution."
            ),
        }

    n_records    = len(df)
    unique_hours = int(df["hour"].nunique()) if "hour" in df.columns else 1
    dates = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.normalize() if "date" in df else None
    unique_dates = int(dates.nunique()) if dates is not None else 0
    hourly_days = df.groupby(dates)["hour"].nunique() if dates is not None and "hour" in df else pd.Series(dtype=int)

    if (hourly_days >= 12).sum() >= 3 and n_records >= 48:
        return {
            "level": 3,
            "code": "level3",
            "label": "Advanced AI Analysis",
            "confidence_range": None,
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
            "confidence_range": None,
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
            "confidence_range": None,
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
