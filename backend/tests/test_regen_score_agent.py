"""Tests proving waste_recovery and feasibility_avg respond to real input."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from agents.regen_score_agent import compute_regen_score


def _base_water():
    return {"total_wasted_liters": 100, "severity_score": 50, "anomaly_events": [], "severity": "medium", "estimated_cost_inr": 500}

def _base_energy():
    return {"total_wasted_kwh": 20, "severity_score": 50, "anomaly_events": [], "severity": "low", "estimated_cost_inr": 200}

def _base_impact():
    return {"sustainability_score": 60, "total_co2_saved_kg": 10, "trees_equivalent": 1, "sustainability_rating": "Good"}

def _base_decision(feasibility_list=None):
    actions = []
    for i, f in enumerate(feasibility_list or [9, 8]):
        actions.append({"id": f"A{i}", "domain": "Water", "urgency": 5, "feasibility": f,
                        "cost_saving_inr": 100, "priority_score": 5.0})
    return {"ranked_actions": actions, "total_potential_saving_inr": 200}

def _waste(circularity: float):
    return {"status": "analyzed", "circularity_score": circularity, "hidden_value_score": circularity}


class TestWasteRecoveryDerived:
    def test_no_waste_uses_neutral_60(self):
        r = compute_regen_score(_base_water(), _base_energy(), _base_impact(), _base_decision())
        assert r["score_breakdown"]["waste_recovery_potential"] == pytest.approx(60.0)

    def test_high_circularity_raises_waste_score(self):
        r_high = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                     _base_decision(), _waste(90))
        r_low  = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                     _base_decision(), _waste(20))
        assert r_high["after_score"] > r_low["after_score"], (
            "Higher circularity_score must produce higher after_score"
        )
        assert r_high["score_breakdown"]["waste_recovery_potential"] == pytest.approx(90.0)
        assert r_low["score_breakdown"]["waste_recovery_potential"]  == pytest.approx(20.0)

    def test_different_circularity_produces_different_before_scores(self):
        r_a = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                  _base_decision(), _waste(10))
        r_b = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                  _base_decision(), _waste(95))
        assert r_a["before_score"] != r_b["before_score"]


class TestFeasibilityDerived:
    def test_feasibility_avg_computed_from_actions(self):
        r = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                _base_decision([9, 7]))
        expected_avg = (9 + 7) / 2
        assert r["score_breakdown"]["feasibility_score"] == pytest.approx(expected_avg, abs=0.1)

    def test_high_vs_low_feasibility_affects_score(self):
        r_high = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                     _base_decision([10, 10]))
        r_low  = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                     _base_decision([1, 1]))
        assert r_high["after_score"] > r_low["after_score"]

    def test_no_actions_fallback_neutral(self):
        decision_no_actions = {"ranked_actions": [], "total_potential_saving_inr": 0}
        r = compute_regen_score(_base_water(), _base_energy(), _base_impact(), decision_no_actions)
        assert r["score_breakdown"]["feasibility_score"] == pytest.approx(80.0)

    def test_single_action_feasibility(self):
        r = compute_regen_score(_base_water(), _base_energy(), _base_impact(),
                                _base_decision([6]))
        assert r["score_breakdown"]["feasibility_score"] == pytest.approx(6.0, abs=0.1)


class TestReturnShapeIntact:
    def test_all_keys_present(self):
        r = compute_regen_score(_base_water(), _base_energy(), _base_impact(), _base_decision())
        for key in ("before_score", "after_score", "improvement", "score_breakdown",
                    "campus_health_index", "building_risk_ranking", "reasoning_trace"):
            assert key in r, f"Missing key: {key}"
