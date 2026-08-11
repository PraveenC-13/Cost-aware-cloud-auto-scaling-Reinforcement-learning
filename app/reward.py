from typing import Optional


def compute_reward(
    cpu: float,
    instance_count: float,
    cost_weight: float = 1.0,
    sla_penalty_weight: float = 2.0,
    sla_threshold: float = 80.0,
) -> float:
    """Calculate cost-aware reward penalty.

    Formula:
        reward = -(cost_weight * instance_count) - (sla_penalty_weight * max(0, cpu - sla_threshold))

    Args:
        cpu: Current CPU utilization percentage (0-100).
        instance_count: Active compute instance count.
        cost_weight: Multiplier weight for instance count cost.
        sla_penalty_weight: Multiplier weight for SLA CPU breach.
        sla_threshold: CPU utilization threshold percentage for SLA violation.

    Returns:
        float: Computed reward value.
    """
    sla_breach = max(0.0, float(cpu) - sla_threshold)
    cost_penalty = float(cost_weight) * float(instance_count)
    sla_penalty = float(sla_penalty_weight) * sla_breach

    return -(cost_penalty) - sla_penalty
