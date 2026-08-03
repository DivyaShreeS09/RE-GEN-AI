"""Tests for core/scoring.py — deterministic score calculations."""
import pytest
from core.scoring import calculate_regen_score, severity_label


class TestCalculateRegenScore:
    def test_perfect_scores_return_100(self):
        result = calculate_regen_score(100, 100, 100, 100, 100, 100)
        assert result == 100.0

    def test_zero_scores_return_zero(self):
        result = calculate_regen_score(0, 0, 0, 0, 0, 0)
        assert result == 0.0

    def test_score_clamped_at_100(self):
        result = calculate_regen_score(200, 200, 200, 200, 200, 200)
        assert result == 100.0

    def test_score_clamped_at_zero(self):
        result = calculate_regen_score(-50, -50, -50, -50, -50, -50)
        assert result == 0.0

    def test_weights_sum_to_one(self):
        # With all inputs = 1, result should equal 1 * sum_of_weights = 1.0
        result = calculate_regen_score(1, 1, 1, 1, 1, 1)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_partial_scores(self):
        # Only waste and water at 100; rest 0 → 0.20+0.20 = 0.40 → 40.0
        result = calculate_regen_score(100, 100, 0, 0, 0, 0)
        assert result == pytest.approx(40.0, abs=0.1)


class TestSeverityLabel:
    def test_excellent(self):
        assert severity_label(90) == "Excellent"

    def test_good(self):
        assert severity_label(65) == "Good"

    def test_moderate(self):
        assert severity_label(50) == "Moderate"

    def test_poor(self):
        assert severity_label(25) == "Poor"

    def test_critical(self):
        assert severity_label(10) == "Critical"

    def test_boundary_80_excellent(self):
        assert severity_label(80) == "Excellent"

    def test_boundary_60_good(self):
        assert severity_label(60) == "Good"

    def test_boundary_40_moderate(self):
        assert severity_label(40) == "Moderate"

    def test_boundary_20_poor(self):
        assert severity_label(20) == "Poor"
