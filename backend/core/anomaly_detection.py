"""
IsolationForest-based anomaly detection for Level 3 data resolution (prompt 2.1).

Strategy:
  - Group rows by location (water) or zone (energy).
  - For each group with >= MIN_SAMPLES rows, fit IsolationForest on [usage, hour].
  - For groups too small, fall back to the original threshold approach and disclose this
    in the returned metadata so the reasoning trace stays honest.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MIN_SAMPLES_FOR_IF = 24


def _baseline_flag_water(grp: pd.DataFrame) -> pd.Series:
    night_mask = grp["hour"].isin(range(0, 6))
    night_vals = grp.loc[night_mask, "usage_liters"]
    baseline = float(night_vals.mean()) if len(night_vals) > 0 else 12.0
    return (grp["usage_liters"] > baseline * 4).astype(bool)


def _baseline_flag_energy(grp: pd.DataFrame) -> pd.Series:
    ah_mask = grp["hour"].isin(list(range(0, 6)) + [22, 23])
    ah_vals = grp.loc[ah_mask, "usage_kwh"]
    baseline = float(ah_vals.mean()) if len(ah_vals) > 0 else 2.5
    return (grp["usage_kwh"] > baseline * 3.5).astype(bool)


def _run_if_water(grp: pd.DataFrame, idx) -> tuple[pd.Series, bool]:
    if len(grp) < MIN_SAMPLES_FOR_IF:
        return _baseline_flag_water(grp), False
    X = np.column_stack([grp["usage_liters"].values, grp["hour"].values])
    preds = IsolationForest(contamination="auto", random_state=42).fit_predict(X)
    return pd.Series((preds == -1), index=idx), True


def _run_if_energy(grp: pd.DataFrame, idx) -> tuple[pd.Series, bool]:
    if len(grp) < MIN_SAMPLES_FOR_IF:
        return _baseline_flag_energy(grp), False
    X = np.column_stack([grp["usage_kwh"].values, grp["hour"].values])
    preds = IsolationForest(contamination="auto", random_state=42).fit_predict(X)
    return pd.Series((preds == -1), index=idx), True


def detect_anomalies_water_if(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    IsolationForest anomaly detection per location for water data.
    Returns (updated_df, metadata).
    """
    df = df.copy()
    n_if = n_fallback = 0
    col = "location" if "location" in df.columns else None

    if col is None:
        flags, used = _run_if_water(df, df.index)
        df["anomaly"] = flags
        n_if += int(used); n_fallback += int(not used)
    else:
        for _, grp in df.groupby(col):
            flags, used = _run_if_water(grp, grp.index)
            df.loc[grp.index, "anomaly"] = flags
            n_if += int(used); n_fallback += int(not used)

    return df, {
        "method": "isolation_forest" if n_fallback == 0 else "mixed",
        "n_locations_if": n_if,
        "n_locations_fallback": n_fallback,
        "min_samples_threshold": MIN_SAMPLES_FOR_IF,
    }


def detect_anomalies_energy_if(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    IsolationForest anomaly detection per zone for energy data.
    Returns (updated_df, metadata).
    """
    df = df.copy()
    n_if = n_fallback = 0
    col = "zone" if "zone" in df.columns else None

    if col is None:
        flags, used = _run_if_energy(df, df.index)
        df["anomaly"] = flags
        n_if += int(used); n_fallback += int(not used)
    else:
        for _, grp in df.groupby(col):
            flags, used = _run_if_energy(grp, grp.index)
            df.loc[grp.index, "anomaly"] = flags
            n_if += int(used); n_fallback += int(not used)

    return df, {
        "method": "isolation_forest" if n_fallback == 0 else "mixed",
        "n_zones_if": n_if,
        "n_zones_fallback": n_fallback,
        "min_samples_threshold": MIN_SAMPLES_FOR_IF,
    }
