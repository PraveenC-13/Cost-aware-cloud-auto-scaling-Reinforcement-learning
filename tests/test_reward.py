from app.reward import compute_reward


def test_compute_reward_normal_operation():
    # cpu below threshold (50 <= 80), instance count = 4
    # reward = -(1.0 * 4) - (2.0 * max(0, 50 - 80)) = -4.0
    reward = compute_reward(cpu=50.0, instance_count=4.0, cost_weight=1.0, sla_penalty_weight=2.0, sla_threshold=80.0)
    assert reward == -4.0


def test_compute_reward_sla_breach():
    # cpu above threshold (90 > 80), instance count = 2
    # reward = -(1.0 * 2) - (2.0 * max(0, 90 - 80)) = -2 - 20 = -22.0
    reward = compute_reward(cpu=90.0, instance_count=2.0, cost_weight=1.0, sla_penalty_weight=2.0, sla_threshold=80.0)
    assert reward == -22.0


def test_compute_reward_custom_weights():
    # cost_weight=0.5, sla_penalty_weight=3.0, sla_threshold=70.0
    # cpu = 85 (breach = 15), instance_count = 10
    # reward = -(0.5 * 10) - (3.0 * 15) = -5.0 - 45.0 = -50.0
    reward = compute_reward(
        cpu=85.0,
        instance_count=10.0,
        cost_weight=0.5,
        sla_penalty_weight=3.0,
        sla_threshold=70.0,
    )
    assert reward == -50.0
