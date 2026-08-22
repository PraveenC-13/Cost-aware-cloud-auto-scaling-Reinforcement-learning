from training.evaluate import run_evaluation, rule_based_policy
import numpy as np


def test_rule_based_policy():
    # High CPU (> 70) -> scale_up (1)
    obs_high = np.array([75.0, 50.0, 80.0, 2.0, 0.10], dtype=np.float32)
    assert rule_based_policy(obs_high) == 1

    # Low CPU (< 30) -> scale_down (2)
    obs_low = np.array([25.0, 40.0, 20.0, 5.0, 0.25], dtype=np.float32)
    assert rule_based_policy(obs_low) == 2

    # Medium CPU (30-70) -> hold (0)
    obs_mid = np.array([50.0, 50.0, 50.0, 3.0, 0.15], dtype=np.float32)
    assert rule_based_policy(obs_mid) == 0


def test_run_evaluation():
    baseline_metrics, rl_metrics, comparison = run_evaluation(num_episodes=2)

    assert "total_cost" in baseline_metrics
    assert "sla_violation_pct" in baseline_metrics
    assert "mean_reward" in baseline_metrics

    assert "total_cost" in rl_metrics
    assert "sla_violation_pct" in rl_metrics
    assert "mean_reward" in rl_metrics

    assert "cost_savings_pct" in comparison
    assert isinstance(comparison["cost_savings_pct"], (float, np.floating))
