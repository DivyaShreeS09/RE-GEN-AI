"""
Domain-correctness tests: prove the math, not just the keys.
Each test constructs synthetic data with known planted values and asserts
the agent recovers expected outputs within documented tolerances.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd

from agents.water_agent import analyze_water, NIGHT_HOURS, WATER_COST_PER_LITER
from agents.energy_agent import analyze_energy, AFTER_HOURS, ELECTRICITY_COST_PER_KWH
from agents.impact_agent import (
    analyze_impact,
    WATER_CO2_KG_PER_LITER,
    ENERGY_CO2_KG_PER_KWH,
)

_LEVEL3 = {
    "level": 3, "code": "level3", "label": "Advanced AI Analysis",
    "anomaly_detection_available": True,
    "reasoning": "test",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_water_df(n_days=3, baseline_night=10.0, baseline_day=30.0, planted_row=None):
    rows = []
    for d in range(n_days):
        date = f"2024-01-{d+1:02d}"
        for h in range(24):
            usage = baseline_night if h in NIGHT_HOURS else baseline_day
            rows.append({"date": date, "hour": h, "usage_liters": usage,
                         "location": "TestBuilding", "anomaly": False})
    df = pd.DataFrame(rows)
    if planted_row:
        mask = (df["date"] == planted_row["date"]) & (df["hour"] == planted_row["hour"])
        df.loc[mask, "usage_liters"] = planted_row["usage"]
        df.loc[mask, "anomaly"] = planted_row.get("anomaly", True)
    return df


def _make_energy_df(n_days=3, baseline_after=2.5, baseline_normal=10.0, planted_row=None):
    rows = []
    for d in range(n_days):
        date = f"2024-01-{d+1:02d}"
        for h in range(24):
            usage = baseline_after if h in AFTER_HOURS else baseline_normal
            rows.append({"date": date, "hour": h, "usage_kwh": usage,
                         "zone": "TestZone", "equipment": "HVAC", "anomaly": False})
    df = pd.DataFrame(rows)
    if planted_row:
        mask = (df["date"] == planted_row["date"]) & (df["hour"] == planted_row["hour"])
        df.loc[mask, "usage_kwh"] = planted_row["usage"]
        df.loc[mask, "anomaly"] = planted_row.get("anomaly", True)
    return df


# ─── Water domain correctness ─────────────────────────────────────────────────

class TestWaterAgent:
    def test_planted_anomaly_recovered_within_tolerance(self):
        # Baseline night = 10 L, plant 100 L → wasted ≈ 90 L
        planted = {"date": "2024-01-02", "hour": 2, "usage": 100.0, "anomaly": True}
        df = _make_water_df(n_days=3, baseline_night=10.0, planted_row=planted)
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_liters"] == pytest.approx(90.0, abs=20.0)

    def test_planted_severity_classified_correctly(self):
        # 90 L wasted → 'low' (50–200 L threshold)
        planted = {"date": "2024-01-02", "hour": 2, "usage": 100.0, "anomaly": True}
        df = _make_water_df(n_days=3, baseline_night=10.0, planted_row=planted)
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["severity"] == "low"

    def test_large_anomaly_triggers_critical(self):
        # 2000 L in one slot → > 1000 L wasted → critical
        planted = {"date": "2024-01-02", "hour": 3, "usage": 2000.0, "anomaly": True}
        df = _make_water_df(n_days=3, baseline_night=10.0, planted_row=planted)
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["severity"] == "critical"
        assert result["total_wasted_liters"] > 1000

    def test_wasted_liters_never_negative(self):
        df = _make_water_df(n_days=3)
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_liters"] >= 0.0

    def test_all_zero_usage_no_crash(self):
        df = _make_water_df(n_days=3)
        df["usage_liters"] = 0.0
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_liters"] >= 0.0

    def test_duplicate_timestamps_no_crash(self):
        df = _make_water_df(n_days=2)
        df = pd.concat([df, df], ignore_index=True)
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_liters"] >= 0.0

    def test_single_row_no_crash(self):
        df = pd.DataFrame([{
            "date": "2024-01-01", "hour": 2, "usage_liters": 15.0,
            "location": "Main", "anomaly": True,
        }])
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_liters"] >= 0.0

    def test_auto_detect_finds_obvious_anomaly(self):
        # No pre-labeled anomalies; 200 L >> baseline(10) * 4 = 40 → auto-detected
        df = _make_water_df(n_days=4, baseline_night=10.0)
        mask = (df["date"] == "2024-01-02") & (df["hour"] == 1)
        df.loc[mask, "usage_liters"] = 200.0
        result = analyze_water(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_liters"] > 0.0
        assert len(result["anomaly_events"]) > 0


# ─── Energy domain correctness ────────────────────────────────────────────────

class TestEnergyAgent:
    def test_planted_anomaly_recovered_within_tolerance(self):
        # Baseline after-hours = 2.5 kWh, plant 50 kWh → wasted ≈ 47.5 kWh
        planted = {"date": "2024-01-02", "hour": 2, "usage": 50.0, "anomaly": True}
        df = _make_energy_df(n_days=3, baseline_after=2.5, planted_row=planted)
        result = analyze_energy(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_kwh"] == pytest.approx(47.5, abs=10.0)

    def test_planted_severity_low(self):
        # ~47.5 kWh → 'low' (10–50 kWh threshold)
        planted = {"date": "2024-01-02", "hour": 2, "usage": 50.0, "anomaly": True}
        df = _make_energy_df(n_days=3, baseline_after=2.5, planted_row=planted)
        result = analyze_energy(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["severity"] == "low"

    def test_large_energy_anomaly_triggers_critical(self):
        # 500 kWh after hours → > 200 kWh wasted → critical
        planted = {"date": "2024-01-02", "hour": 3, "usage": 500.0, "anomaly": True}
        df = _make_energy_df(n_days=3, baseline_after=2.5, planted_row=planted)
        result = analyze_energy(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["severity"] == "critical"
        assert result["total_wasted_kwh"] > 200

    def test_wasted_kwh_never_negative(self):
        df = _make_energy_df(n_days=3)
        result = analyze_energy(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_kwh"] >= 0.0

    def test_all_zero_energy_no_crash(self):
        df = _make_energy_df(n_days=3)
        df["usage_kwh"] = 0.0
        result = analyze_energy(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_kwh"] >= 0.0

    def test_single_row_no_crash(self):
        df = pd.DataFrame([{
            "date": "2024-01-01", "hour": 2, "usage_kwh": 50.0,
            "zone": "TestZone", "equipment": "HVAC", "anomaly": True,
        }])
        result = analyze_energy(df, is_uploaded=True, analysis_level_info=_LEVEL3)
        assert result["total_wasted_kwh"] >= 0.0


# ─── Impact agent correctness ─────────────────────────────────────────────────

class TestImpactAgent:
    def test_co2_water_hand_computed(self):
        # 100 L × 0.001 kg/L = 0.1 kg CO2 exactly
        result = analyze_impact(100.0, 0.0, 0.0)
        assert result["water_co2_saved_kg"] == pytest.approx(
            100.0 * WATER_CO2_KG_PER_LITER, abs=0.001
        )

    def test_co2_energy_hand_computed(self):
        # 100 kWh × 0.82 kg/kWh = 82.0 kg CO2 exactly
        result = analyze_impact(0.0, 100.0, 0.0)
        assert result["energy_co2_saved_kg"] == pytest.approx(
            100.0 * ENERGY_CO2_KG_PER_KWH, abs=0.01
        )

    def test_total_co2_is_sum_of_components(self):
        result = analyze_impact(200.0, 50.0, 0.0)
        expected = round(200.0 * WATER_CO2_KG_PER_LITER + 50.0 * ENERGY_CO2_KG_PER_KWH, 2)
        assert result["total_co2_saved_kg"] == pytest.approx(expected, abs=0.01)

    def test_doubling_water_does_not_decrease_co2(self):
        r1 = analyze_impact(100.0, 50.0, 0.0)
        r2 = analyze_impact(200.0, 50.0, 0.0)
        assert r2["total_co2_saved_kg"] >= r1["total_co2_saved_kg"]

    def test_doubling_energy_does_not_decrease_co2(self):
        r1 = analyze_impact(100.0, 50.0, 0.0)
        r2 = analyze_impact(100.0, 100.0, 0.0)
        assert r2["total_co2_saved_kg"] >= r1["total_co2_saved_kg"]

    def test_zero_inputs_give_zero_co2(self):
        result = analyze_impact(0.0, 0.0, 0.0)
        assert result["total_co2_saved_kg"] == 0.0
        assert result["trees_equivalent"] == 0.0

    def test_high_co2_gives_outstanding_rating(self):
        # 700 kWh × 0.82 = 574 kg CO2 → Outstanding (≥ 500)
        result = analyze_impact(0.0, 700.0, 0.0)
        assert result["sustainability_rating"] == "Outstanding"
        assert result["sustainability_score"] == 88

    def test_co2_monotone_over_sweep(self):
        prev = -1.0
        for liters in [0, 100, 500, 1000, 5000, 10000]:
            r = analyze_impact(float(liters), 0.0, 0.0)
            assert r["total_co2_saved_kg"] >= prev
            prev = r["total_co2_saved_kg"]

    def test_regen_score_responds_to_severity(self):  # noqa: E301
        """Confirm (from test_regen_score_agent) that regen score changes across severities."""
        from agents.regen_score_agent import compute_regen_score
        def _decision():
            return {"ranked_actions": [{"id": "W1", "domain": "Water", "urgency": 5,
                                        "feasibility": 8, "cost_saving_inr": 100, "priority_score": 5.0}],
                    "total_potential_saving_inr": 100}
        water_high  = {"total_wasted_liters": 2000, "severity_score": 10, "anomaly_events": [], "severity": "critical", "estimated_cost_inr": 100}
        water_low   = {"total_wasted_liters": 10,   "severity_score": 95, "anomaly_events": [], "severity": "none",     "estimated_cost_inr": 1}
        energy_base = {"total_wasted_kwh": 0, "severity_score": 92, "anomaly_events": [], "severity": "none", "estimated_cost_inr": 0}
        impact_base = {"sustainability_score": 50, "total_co2_saved_kg": 0, "trees_equivalent": 0, "sustainability_rating": "Developing"}
        r_high = compute_regen_score(water_high, energy_base, impact_base, _decision())
        r_low  = compute_regen_score(water_low,  energy_base, impact_base, _decision())
        assert r_high["before_score"] < r_low["before_score"], (
            "Critical water severity must produce lower before_score than none"
        )


# ─── Decision Engine install-cost correctness ─────────────────────────────────

class TestDecisionAgentInstallCosts:
    def _water(self, liters):
        return {"total_wasted_liters": 100, "total_consumption_liters": liters,
                "severity": "low", "estimated_cost_inr": 500,
                "anomaly_events": [], "recommendations": ["Inspect"]}

    def _energy(self, kwh):
        return {"total_wasted_kwh": 20, "total_consumption_kwh": kwh,
                "severity": "low", "estimated_cost_inr": 200,
                "anomaly_events": [], "recommendations": ["Timer"]}

    def test_larger_facility_has_higher_w1_cost(self):
        from agents.decision_agent import generate_decisions
        small = generate_decisions(self._water(500),  self._energy(50))
        large = generate_decisions(self._water(5000), self._energy(50))
        small_cost = small["ranked_actions"][0]["roi"]["install_cost_inr"]
        large_cost = large["ranked_actions"][0]["roi"]["install_cost_inr"]
        # W1 is always present; for water-dominant: larger consumption → higher cost
        w1_small = next(a for a in small["ranked_actions"] if a["id"] == "W1")
        w1_large = next(a for a in large["ranked_actions"] if a["id"] == "W1")
        assert w1_large["roi"]["install_cost_inr"] >= w1_small["roi"]["install_cost_inr"]

    def test_w1_cost_basis_is_scaled(self):
        from agents.decision_agent import generate_decisions
        result = generate_decisions(self._water(2000), self._energy(100))
        w1 = next(a for a in result["ranked_actions"] if a["id"] == "W1")
        assert w1["roi"]["cost_basis"] == "scaled_from_water_consumption"

    def test_e1_cost_basis_is_scaled(self):
        from agents.decision_agent import generate_decisions
        result = generate_decisions(self._water(500), self._energy(500))
        e1 = next(a for a in result["ranked_actions"] if a["id"] == "E1")
        assert e1["roi"]["cost_basis"] == "scaled_from_energy_consumption"

    def test_w2_cost_basis_is_reference(self):
        from agents.decision_agent import generate_decisions
        waste = {"status": "analyzed", "waste_type": "pet", "quantity_kg": 10,
                 "hidden_value_score": 60, "hazard_warning": False,
                 "estimated_recovery": {"max_inr": 500},
                 "recommended_pathway": "recycle"}
        result = generate_decisions(self._water(500), self._energy(50), waste)
        w2 = next(a for a in result["ranked_actions"] if a["id"] == "W2")
        assert w2["roi"]["cost_basis"] == "industry_reference_estimate"

    def test_cost_clamped_within_range(self):
        from agents.decision_agent import _scale_install_cost
        cost, basis = _scale_install_cost("W1", 0, 0)
        assert 3000 <= cost <= 50000
        cost2, _ = _scale_install_cost("W1", 1_000_000, 0)
        assert cost2 <= 50000  # upper clamp


# ─── IsolationForest anomaly detection (prompt 2.1) ──────────────────────────

class TestIsolationForestAnomalyDetection:
    def _make_water_df(self, n_days=7, spike=True):
        rows = []
        for d in range(n_days):
            for h in range(24):
                usage = 10.0 if h < 6 else 30.0
                rows.append({"date": f"2024-01-{d+1:02d}", "hour": h,
                             "usage_liters": usage, "location": "Hostel A", "anomaly": False})
        if spike:
            for h in range(1, 4):
                rows[4 * 24 + h]["usage_liters"] = 250.0
        return pd.DataFrame(rows)

    def _make_energy_df(self, n_days=7, spike=True):
        rows = []
        for d in range(n_days):
            for h in range(24):
                usage = 2.0 if h in list(range(0, 6)) + [22, 23] else 15.0
                rows.append({"date": f"2024-01-{d+1:02d}", "hour": h,
                             "usage_kwh": usage, "zone": "Lab Block", "anomaly": False,
                             "equipment": "Mixed"})
        if spike:
            for h in range(0, 4):
                rows[3 * 24 + h]["usage_kwh"] = 80.0
        return pd.DataFrame(rows)

    def test_if_detects_planted_water_spike(self):
        from core.anomaly_detection import detect_anomalies_water_if
        df, meta = detect_anomalies_water_if(self._make_water_df())
        assert df["anomaly"].any()
        assert meta["n_locations_if"] >= 1

    def test_water_fallback_for_small_dataset(self):
        from core.anomaly_detection import detect_anomalies_water_if, MIN_SAMPLES_FOR_IF
        # Only 12 rows — below the 24-sample threshold
        rows = [{"date": "2024-01-01", "hour": h, "usage_liters": 10.0,
                 "location": "Hostel A", "anomaly": False} for h in range(12)]
        small = pd.DataFrame(rows)
        assert len(small) < MIN_SAMPLES_FOR_IF
        _, meta = detect_anomalies_water_if(small)
        assert meta["n_locations_fallback"] >= 1

    def test_if_detects_planted_energy_spike(self):
        from core.anomaly_detection import detect_anomalies_energy_if
        df, meta = detect_anomalies_energy_if(self._make_energy_df())
        assert df["anomaly"].any()
        assert meta["n_zones_if"] >= 1

    def test_energy_fallback_for_small_dataset(self):
        from core.anomaly_detection import detect_anomalies_energy_if, MIN_SAMPLES_FOR_IF
        rows = [{"date": "2024-01-01", "hour": h, "usage_kwh": 2.0,
                 "zone": "Lab Block", "anomaly": False, "equipment": "Mixed"}
                for h in range(12)]
        small = pd.DataFrame(rows)
        assert len(small) < MIN_SAMPLES_FOR_IF
        _, meta = detect_anomalies_energy_if(small)
        assert meta["n_zones_fallback"] >= 1

    def test_water_agent_reasoning_trace_mentions_detection(self):
        result = analyze_water(df=self._make_water_df(), is_uploaded=True, analysis_level_info=_LEVEL3)
        trace = " ".join(result["reasoning_trace"])
        assert "IsolationForest" in trace or "detection" in trace.lower()

    def test_energy_agent_reasoning_trace_mentions_detection(self):
        result = analyze_energy(df=self._make_energy_df(), is_uploaded=True, analysis_level_info=_LEVEL3)
        trace = " ".join(result["reasoning_trace"])
        assert "IsolationForest" in trace or "detection" in trace.lower()


def test_reporting_window_roi_and_unpriced_inventory():
    from agents.decision_agent import _roi
    assert _roi(600, "reference", 100, 10)["payback_months"] == 2
    assert _roi(600, "reference", 100, None)["monthly_saving_inr"] is None


def test_canonical_weighted_mass():
    from agents.waste_agent import analyze_waste_batch
    result = analyze_waste_batch([{"type": "cartons", "quantity_kg": 9000, "unit": "g"},
                                  {"type": "PET bottles", "quantity_kg": 1}])
    assert result["composition"]["paper_pct"] == 90
    scores = [r["hidden_value_score"] for r in result["items"]]
    assert result["circularity_score"] == round((9*scores[0]+scores[1])/10, 1)


def test_fuel_is_emitted_carbon():
    result = analyze_impact(0, 0, 0, fuel_co2_kg=120)
    assert result["fuel_emissions_kg"] == 120
    assert result["total_co2_saved_kg"] == 0


def test_mass_cannot_price_count_or_volume_rates():
    from agents.waste_agent import analyze_waste, _get_kb
    samples = [name for name, record in _get_kb()["waste_materials"].items()
               if record["estimated_value_range"]["unit"] != "INR/kg"]
    assert samples
    for name in samples:
        assert analyze_waste(name, 10, narrative=False)["estimated_recovery"] is None


def test_normalize_counter_by_meter_and_skip_reset_missing_and_duplicates():
    from core.data_processor import validate_water_df

    columns = ["timestamp", "meter_id", "cumulative_m3", "zone"]
    rows = [
        ("2026-11-01T03:00:00+05:30", "W1", 1.8, "Annex"),
        ("2026-11-01T00:00:00+05:30", "W1", 5, "Annex"),
        ("2026-11-01T01:00:00+05:30", "W1", 6, "Annex"),
        ("2026-11-01T02:00:00+05:30", "W1", 1, "Annex"),
        ("2026-11-01T04:00:00+05:30", "W1", None, "Annex"),
        ("2026-11-01T05:00:00+05:30", "W1", 2, "Annex"),
        ("2026-10-31T18:30:00Z", "W2", 20, "Annex"),
        ("2026-11-01T01:00:00+05:30", "W2", 22, "Annex"),
    ]
    frame, quality = validate_water_df(pd.DataFrame(rows + [rows[2]], columns=columns))
    assert quality["valid"] and quality["duplicates_removed"] == quality["counter_resets"] == quality["missing_values"] == 1
    assert quality["intervals_excluded"] == 3
    assert frame.groupby("device_id")["usage_liters"].sum().to_dict() == {"W1": 1800.0, "W2": 2000.0}


def test_mixed_resource_rates_need_endpoints_and_use_elapsed_time():
    from core.data_processor import validate_energy_df, validate_water_df

    raw = pd.DataFrame([
        ["water", "2026-11-01 00:00", "instantaneous", "L/min", 10],
        ["water", "2026-11-01 00:10", "instantaneous", "L/min", 10],
        ["energy", "2026-11-01 00:00", "power", "W", 2000],
        ["energy", "2026-11-01 00:30", "power", "W", 2000],
        ["energy", "2026-11-01 01:15", "power", "W", 4000],
        ["energy", "2026-11-02 12:00", "power", "W", 2000],
    ], columns=["resource", "timestamp", "reading_type", "unit", "value"])
    water, wq = validate_water_df(raw)
    energy, eq = validate_energy_df(raw)
    assert wq["valid"] and eq["valid"]
    assert water["usage_liters"].sum() == 100
    assert energy["usage_kwh"].sum() == pytest.approx(3.25)
    assert eq["intervals_excluded"] == 1 and eq["peak_observed_demand_kw"] == 4
    result = analyze_energy(energy, is_uploaded=True, rate=None)
    assert result["resource_profile"]["estimated_quantity"] == pytest.approx(3.25)
    assert result["estimated_cost_inr"] is None and result["co2_equivalent_kg"] is None
    _, invalid = validate_energy_df(pd.DataFrame({"date": ["2026-11-01"], "power_kw": [4]}))
    assert not invalid["valid"]
    _, ambiguous = validate_water_df(pd.DataFrame({"date": ["01/02/2026"], "meter_reading": [5], "unit": ["L"]}))
    assert not ambiguous["valid"] and "reading_type" in ambiguous["errors"][0]


def test_daily_forecast_uses_only_prior_values_and_rejects_missing_coverage():
    from core.data_processor import validate_water_df
    dates = pd.date_range("2026-10-01", periods=21)
    raw = pd.DataFrame({"date": dates, "usage_liters": [10 + i % 7 for i in range(21)], "reading_type": "daily"})
    frame, info = validate_water_df(raw)
    assert info["valid"]
    result = analyze_water(frame, is_uploaded=True, rate=None)
    forecast = result["resource_profile"]["forecast"]
    assert forecast["model"] == "weekly_seasonal" and forecast["estimate"] == 10
    assert forecast["validation_mae"]["weekly_seasonal"] == 0 < forecast["validation_mae"]["previous_day"]
    assert result["resource_profile"]["average_daily"] == 13
    short, _ = validate_water_df(raw.drop(index=10))
    assert analyze_water(short, is_uploaded=True, rate=None)["resource_profile"]["forecast"]["status"] == "insufficient_data"


def test_upload_integrates_flags_tariff_provenance_and_shared_zone_without_confirming_cause(token_for):
    from fastapi.testclient import TestClient
    from main import app

    def file(metric):
        rows = [f"timestamp,meter_id,zone,{metric},scheduled,occupied"]
        for day in (2, 3, 4, 5, 6):
            for hour in range(6):
                value = 30 if day == 6 and hour < 3 else 10
                rows.append(f"2026-11-{day:02}T{hour:02}:00:00+05:30,{metric},North Annex,{value},no,no")
        return "\n".join(rows)

    client = TestClient(app, headers={"Authorization": token_for("integrated-resource-regression")})
    response = client.post("/analyze/upload",
                           files={"water_file": ("water.csv", file("usage_liters")), "energy_file": ("electricity.csv", file("usage_kwh"))},
                           data={"water_inr_per_litre": "0.1", "tariff_reference": "fixture invoice",
                                 "waste_type": "paper", "waste_quantity_kg": "5"})
    assert response.status_code == 200, response.text
    result = response.json()
    water = result["water"]
    assert water["total_consumption_liters"] == result["energy"]["total_consumption_kwh"] == 360
    assert water["anomaly_events"][-1]["evidence_status"] == "possible_leakage"
    assert result["energy"]["anomaly_events"][-1]["evidence_status"] == "persistent_off_hours_load"
    assert water["estimated_cost_inr"] == 6 and result["energy"]["estimated_cost_inr"] is None
    assert water["loss_assessment"]["verified_savings"] is None
    assert result["impact"]["total_co2_saved_kg"] is None and result["impact"]["total_financial_benefit_inr"] is None
    assert result["decision"]["cross_resource_relationships"][0]["status"] == "co_occurrence"
    assert result["report"]["resource_evidence"]["water"]["findings"] == water["anomaly_events"]
    assert result["report"]["silent_losses"]["water_cost_inr"] == 6
    planned = result["decision"]["ranked_actions"]
    assert all(item["approval_required"] for item in planned)
    assert next(item for item in planned if item["id"] == "R1")["zones"] == ["North Annex"]
    assert all(item["depends_on"] == ["R1"] for item in planned if item["domain"] in ("Water", "Energy"))
    from core.database import get_run_by_id
    stored = get_run_by_id(result["analysis_id"], tenant="integrated-resource-regression")
    assert result["regen_score"]["after_score"] is None and stored["regen_score_after"] is None
    assert stored["total_co2_saved_kg"] is None
    pdf = client.get(f"/report/{result['analysis_id']}/audit-record.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_documented_meter_rollover_reconciles_only_near_the_boundary():
    from core.data_processor import validate_energy_df

    raw = pd.DataFrame({
        "timestamp": pd.date_range("2026-10-01", periods=4, freq="h"),
        "cumulative_kwh": [990, 10, 300, 20],
        "rollover_value": [1000] * 4,
        "rollover_reference": ["fixture meter manual"] * 4,
    })
    result, info = validate_energy_df(raw)
    assert info["valid"] and info["counter_rollovers"] == 1 and info["counter_resets"] == 1
    assert result["usage_kwh"].sum() == 310
    _, missing = validate_energy_df(raw.drop(columns="rollover_reference"))
    assert not missing["valid"]


def test_historical_decision_rejects_unstructured_or_ineligible_narrative(monkeypatch):
    from agents import decision_agent

    water = {"status": "analyzed", "is_uploaded": True, "severity": "medium",
             "total_wasted_liters": 20, "estimated_cost_inr": None,
             "recommendations": ["Inspect with authorized staff."]}
    for response in ("Confirmed water leak. Implement immediately.", '{"focus":"review_shared_observations"}'):
        monkeypatch.setattr(decision_agent, "call_ai", lambda *args, **kwargs: (response, True))
        result = decision_agent.generate_decisions(water, {"status": "skipped"})
        assert not result["ai_enhanced"]
        assert result["top_action_explanation"] == "Inspect with authorized staff."
    monkeypatch.setattr(decision_agent, "call_ai", lambda *args, **kwargs: ('{"focus":"check_operating_context"}', True))
    result = decision_agent.generate_decisions(water, {"status": "skipped"})
    assert result["ai_enhanced"]
    assert "before selecting" in result["top_action_explanation"]
