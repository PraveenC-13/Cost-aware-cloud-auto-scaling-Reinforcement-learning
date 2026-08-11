import numpy as np
from app.env.scaling_env import ScalingEnv
from app.reward import compute_reward


def test_env_initialization():
    env = ScalingEnv(cost_weight=1.5, sla_penalty_weight=3.0, sla_threshold=75.0)
    assert env.action_space.n == 3
    assert env.observation_space.shape == (5,)
    assert env.cost_weight == 1.5
    assert env.sla_penalty_weight == 3.0
    assert env.sla_threshold == 75.0


def test_env_reset():
    env = ScalingEnv()
    obs, info = env.reset(seed=42)
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (5,)
    assert isinstance(info, dict)


def test_env_step_and_dynamic_reward():
    env = ScalingEnv(cost_weight=1.0, sla_penalty_weight=2.0, sla_threshold=80.0)
    env.reset(seed=42)
    for action in [0, 1, 2]:
        obs, reward, terminated, truncated, info = env.step(action)
        cpu, _, _, instance_count, _ = obs

        expected_reward = compute_reward(
            cpu=cpu,
            instance_count=instance_count,
            cost_weight=env.cost_weight,
            sla_penalty_weight=env.sla_penalty_weight,
            sla_threshold=env.sla_threshold,
        )

        assert obs.shape == (5,)
        assert isinstance(reward, float)
        assert np.isclose(reward, expected_reward)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
