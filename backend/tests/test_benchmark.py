"""Tests for peer/reference benchmarking agent (prompt 2.6)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.benchmark_agent import compute_benchmark


class TestBenchmarkSkip:
    def test_skip_when_no_occupancy(self):
        result = compute_benchmark(
            org_type="Hospital / Healthcare",
            occupancy_count=None,
            total_consumption_liters=1000.0,
            total_consumption_kwh=500.0,
        )
        assert result["available"] is False
        assert "occupancy" in result["skip_reason"].lower()

    def test_skip_when_occupancy_zero(self):
        result = compute_benchmark(
            org_type="Hospital / Healthcare",
            occupancy_count=0,
            total_consumption_liters=1000.0,
            total_consumption_kwh=500.0,
        )
        assert result["available"] is False


class TestBenchmarkResult:
    def test_hospital_water_efficient_bucket(self):
        # 100 beds, 7 days, 1400 L total -> 2 L/bed/day (well below 250 efficient_upper)
        result = compute_benchmark(
            org_type="Hospital / Healthcare",
            occupancy_count=100,
            total_consumption_liters=1400.0,
            total_consumption_kwh=700.0,
            days_of_data=7,
        )
        assert result["available"] is True
        water = result["water"]
        assert water["available"] is True
        assert water["bucket"] == "top_20pct_efficient"
        assert water["value_per_occupant_per_day"] == round(1400 / 100 / 7, 3)

    def test_hospital_water_high_use_bucket(self):
        # 10 beds, 7 days, 35000 L total -> 500 L/bed/day (above high_use_lower 450)
        result = compute_benchmark(
            org_type="Hospital / Healthcare",
            occupancy_count=10,
            total_consumption_liters=35000.0,
            total_consumption_kwh=100.0,
            days_of_data=7,
        )
        water = result["water"]
        assert water["available"] is True
        assert water["bucket"] == "bottom_20pct_high_use"

    def test_hospital_energy_typical_bucket(self):
        # 100 beds, 7 days, 770 kWh -> 1.1 kWh/bed/day (between 0.96 and 1.37)
        result = compute_benchmark(
            org_type="Hospital / Healthcare",
            occupancy_count=100,
            total_consumption_liters=0.0,
            total_consumption_kwh=770.0,
            days_of_data=7,
        )
        energy = result["energy"]
        assert energy["available"] is True
        assert energy["bucket"] == "typical_range"

    def test_insufficient_reference_disclosed(self):
        # University energy benchmark has insufficient_reference_data
        result = compute_benchmark(
            org_type="University / College",
            occupancy_count=500,
            total_consumption_liters=100000.0,
            total_consumption_kwh=5000.0,
            days_of_data=7,
        )
        energy = result["energy"]
        assert energy["available"] is False
        assert "reason" in energy

    def test_unknown_org_type_uses_other(self):
        result = compute_benchmark(
            org_type="Submarine Base",
            occupancy_count=50,
            total_consumption_liters=1000.0,
            total_consumption_kwh=200.0,
            days_of_data=7,
        )
        assert "available" in result

    def test_reference_source_present(self):
        result = compute_benchmark(
            org_type="Hospital / Healthcare",
            occupancy_count=100,
            total_consumption_liters=1000.0,
            total_consumption_kwh=500.0,
        )
        assert "reference_source" in result
        assert "BEE" in result["reference_source"] or "Bureau" in result["reference_source"]
