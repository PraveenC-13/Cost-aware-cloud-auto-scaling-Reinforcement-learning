import sys
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
from stable_baselines3 import PPO

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.env.scaling_env import ScalingEnv

MODEL_PATH = PROJECT_ROOT / "saved_models" / "ppo_scaling_model.zip"


def rule_based_policy(obs: np.ndarray) -> int:
    """Baseline policy: Scale up if CPU > 70%, Scale down if CPU < 30%."""
    cpu = obs[0]
    if cpu > 70.0:
        return 1  # scale_up
    elif cpu < 30.0:
        return 2  # scale_down
    return 0  # hold


def evaluate_policy(env: ScalingEnv, policy_type: str, model: PPO = None, num_episodes: int = 20) -> Dict[str, float]:
    """Evaluate a policy on ScalingEnv over num_episodes."""
    total_cost = 0.0
    sla_violations = 0
    total_steps = 0
    total_reward = 0.0
    instance_counts = []

    for episode in range(num_episodes):
        # Use a deterministic seed sequence for fair comparison across policies
        obs, _ = env.reset(seed=1000 + episode)
        terminated = False
        truncated = False

        while not (terminated or truncated):
            if policy_type == "rl":
                action, _ = model.predict(obs, deterministic=True)
                action = int(action)
            else:
                action = rule_based_policy(obs)

            obs, reward, terminated, truncated, info = env.step(action)
            cpu, _, _, instance_count, cost = obs

            total_cost += cost
            total_reward += reward
            total_steps += 1
            instance_counts.append(instance_count)

            if cpu > env.sla_threshold:
                sla_violations += 1

    mean_reward = total_reward / num_episodes
    sla_violation_pct = (sla_violations / total_steps) * 100.0 if total_steps > 0 else 0.0
    avg_instances = float(np.mean(instance_counts)) if instance_counts else 0.0

    return {
        "total_cost": total_cost,
        "sla_violations": sla_violations,
        "sla_violation_pct": sla_violation_pct,
        "total_reward": total_reward,
        "mean_reward": mean_reward,
        "total_steps": total_steps,
        "avg_instances": avg_instances,
    }


def run_evaluation(num_episodes: int = 20) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Run head-to-head evaluation between RL PPO policy and Rule-Based baseline."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Please run training/train.py first.")

    print(f"Loading trained PPO model from {MODEL_PATH}...")
    model = PPO.load(str(MODEL_PATH))

    env = ScalingEnv()

    print(f"Evaluating Rule-Based Baseline over {num_episodes} episodes...")
    baseline_metrics = evaluate_policy(env, policy_type="baseline", num_episodes=num_episodes)

    print(f"Evaluating Trained PPO RL Agent over {num_episodes} episodes...")
    rl_metrics = evaluate_policy(env, policy_type="rl", model=model, num_episodes=num_episodes)

    # Calculate comparative savings
    cost_savings_pct = (
        float(((baseline_metrics["total_cost"] - rl_metrics["total_cost"]) / baseline_metrics["total_cost"]) * 100.0)
        if baseline_metrics["total_cost"] > 0
        else 0.0
    )

    comparison = {
        "cost_savings_pct": cost_savings_pct,
        "sla_diff_pct": float(rl_metrics["sla_violation_pct"] - baseline_metrics["sla_violation_pct"]),
        "reward_improvement": float(rl_metrics["mean_reward"] - baseline_metrics["mean_reward"]),
    }

    # Log summary table
    print("\n" + "=" * 65)
    print("        RL AGENT VS RULE-BASED BASELINE EVALUATION REPORT        ")
    print("=" * 65)
    print(f"{'Metric':<30} | {'Rule Baseline':<14} | {'RL Agent (PPO)':<14}")
    print("-" * 65)
    print(f"{'Total Cost ($)':<30} | ${baseline_metrics['total_cost']:<13.2f} | ${rl_metrics['total_cost']:<13.2f}")
    print(f"{'Cost Savings (%)':<30} | {'0.0%':<14} | {cost_savings_pct:<+13.2f}%")
    print(f"{'SLA Violations (%)':<30} | {baseline_metrics['sla_violation_pct']:<13.2f}% | {rl_metrics['sla_violation_pct']:<13.2f}%")
    print(f"{'Mean Reward / Episode':<30} | {baseline_metrics['mean_reward']:<14.2f} | {rl_metrics['mean_reward']:<14.2f}")
    print(f"{'Avg Instance Count':<30} | {baseline_metrics['avg_instances']:<14.2f} | {rl_metrics['avg_instances']:<14.2f}")
    print("=" * 65 + "\n")

    return baseline_metrics, rl_metrics, comparison


if __name__ == "__main__":
    run_evaluation(num_episodes=20)
