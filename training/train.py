import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stable_baselines3 import PPO
from app.env.scaling_env import ScalingEnv

MODEL_DIR = PROJECT_ROOT / "saved_models"
MODEL_PATH = MODEL_DIR / "ppo_scaling_model.zip"


def train_model(total_timesteps: int = 10000) -> Path:
    """Train PPO agent on ScalingEnv and save trained weights."""
    print("Initializing ScalingEnv...")
    env = ScalingEnv()

    print("Creating PPO model with MlpPolicy...")
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        seed=42,
    )

    print(f"Training PPO for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    save_target = str(MODEL_PATH).replace(".zip", "")
    model.save(save_target)
    print(f"Model saved successfully to {MODEL_PATH}")
    return MODEL_PATH


if __name__ == "__main__":
    train_model(total_timesteps=10000)
