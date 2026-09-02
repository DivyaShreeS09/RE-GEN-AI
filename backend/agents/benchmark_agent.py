"""
Peer/reference benchmarking agent (prompt 2.6).

Compares an organisation's per-occupant resource consumption against published
reference ranges (BEE India / CPWD norms) from benchmark_reference.json.

Gated on occupancy_count: when absent, returns a skip_reason rather than
fabricating a comparison — consistent with this codebase's skipped-module
pattern in analysis_metadata.
"""

import json
import os

_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_reference.json")
_KB: dict | None = None


def _load_kb() -> dict:
    global _KB
    if _KB is None:
        with open(_KB_PATH, encoding="utf-8") as f:
            _KB = json.load(f)
    return _KB


def _bucket(value_per_occupant: float, ref: dict) -> str:
    if value_per_occupant <= ref["efficient_upper"]:
        return "top_20pct_efficient"
    if value_per_occupant <= ref["typical_upper"]:
        return "typical_range"
    return "bottom_20pct_high_use"


def _bucket_label(bucket: str) -> str:
    return {
        "top_20pct_efficient":   "top 20% most efficient",
        "typical_range":         "typical range",
        "bottom_20pct_high_use": "bottom 20% highest use",
    }.get(bucket, bucket)


def compute_benchmark(
    org_type: str,
    occupancy_count: int | None,
    total_consumption_liters: float,
    total_consumption_kwh: float,
    days_of_data: float = 7,
) -> dict:
    """
    Returns a benchmark_result dict. When occupancy_count is None or 0,
    returns a skip result with a clear reason rather than fabricating a
    comparison — consistent with this codebase's skipped-module pattern.
    """
    if not occupancy_count or occupancy_count <= 0:
        return {
            "available": False,
            "skip_reason": (
                "Occupancy count not provided. Supply 'occupancy_count' to "
                "unlock peer benchmarking against published reference ranges."
            ),
        }

    kb = _load_kb()
    ref = kb.get(org_type) or kb.get("Other")
    meta = kb["_meta"]

    liters_per_occ_day = total_consumption_liters / occupancy_count / max(days_of_data, 1)
    kwh_per_occ_day    = total_consumption_kwh    / occupancy_count / max(days_of_data, 1)

    water_ref  = ref.get("water_liters_per_occupant_per_day",  {})
    energy_ref = ref.get("energy_kwh_per_occupant_per_day", {})

    def _assess(value, ref_dict, unit):
        if ref_dict.get("insufficient_reference_data"):
            return {
                "available": False,
                "reason": ref_dict.get("reason", "Insufficient reference data."),
            }
        bucket = _bucket(value, ref_dict)
        return {
            "available": True,
            "value_per_occupant_per_day": round(value, 3),
            "unit":   unit,
            "bucket": bucket,
            "label":  _bucket_label(bucket),
            "reference_range": {
                "efficient_upper": ref_dict["efficient_upper"],
                "typical_lower":   ref_dict["typical_lower"],
                "typical_upper":   ref_dict["typical_upper"],
                "high_use_lower":  ref_dict["high_use_lower"],
                "unit": unit,
            },
            "source_note": ref_dict.get("source_note", ""),
        }

    return {
        "available": True,
        "org_type":        org_type,
        "occupancy_count": occupancy_count,
        "days_of_data":    days_of_data,
        "water":  _assess(liters_per_occ_day, water_ref,  "L/occupant/day"),
        "energy": _assess(kwh_per_occ_day,    energy_ref, "kWh/occupant/day"),
        "reference_source":        meta["sources"][0]["name"],
        "reference_last_verified": meta["last_verified"],
        "disclaimer":              meta["disclaimer"],
    }
