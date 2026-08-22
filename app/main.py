import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas import ScalingDecisionOutput, ScalingStateInput

MODEL_PATH = PROJECT_ROOT / "saved_models" / "ppo_scaling_model.zip"
ACTION_NAMES = {0: "hold", 1: "scale_up", 2: "scale_down"}

model: Optional[Any] = None


def rule_based_fallback(state: ScalingStateInput) -> ScalingDecisionOutput:
    """Fallback rule-based decision logic when trained RL model is unavailable."""
    if state.cpu > 80.0 or state.predicted_cpu_next_15min > 80.0:
        action = 1
        confidence = 0.85
        reasoning = (
            f"Rule-based fallback: High utilization (CPU {state.cpu}% / "
            f"Predicted {state.predicted_cpu_next_15min}%) exceeds SLA threshold (80%)."
        )
    elif state.cpu < 20.0 and state.instance_count > 1:
        action = 2
        confidence = 0.80
        reasoning = f"Rule-based fallback: Low CPU utilization ({state.cpu}%) with {state.instance_count} instances."
    else:
        action = 0
        confidence = 0.90
        reasoning = "Rule-based fallback: Resource utilization within normal operating bounds."

    return ScalingDecisionOutput(
        action=action,
        action_name=ACTION_NAMES[action],
        confidence=confidence,
        reasoning=reasoning,
    )


def load_ppo_model():
    """Attempt to load saved PPO model weights."""
    global model
    if MODEL_PATH.exists():
        try:
            from stable_baselines3 import PPO

            model = PPO.load(str(MODEL_PATH))
            print(f"Successfully loaded PPO model from {MODEL_PATH}")
        except Exception as e:
            print(f"Failed to load PPO model from {MODEL_PATH}: {e}. Defaulting to rule-based fallback.")
            model = None
    else:
        print(f"No trained model found at {MODEL_PATH}. Defaulting to rule-based fallback.")
        model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup and shutdown events lifecycle."""
    load_ppo_model()
    yield


app = FastAPI(
    title="RL Auto-Scaling Engine API",
    description="FastAPI service serving PPO auto-scaling policy with rule-based fallback.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Health check endpoint indicating service and model status."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": str(MODEL_PATH),
    }


@app.post("/decide", response_model=ScalingDecisionOutput)
def decide_scaling_action(state: ScalingStateInput) -> ScalingDecisionOutput:
    """Make scaling decision based on input infrastructure metrics."""
    global model

    # If model is not loaded, use rule-based fallback
    if model is None:
        return rule_based_fallback(state)

    try:
        # Construct state array: [cpu, memory, predicted_cpu, instance_count, cost]
        obs = np.array(
            [
                state.cpu,
                state.memory,
                state.predicted_cpu_next_15min,
                float(state.instance_count),
                state.current_hourly_cost,
            ],
            dtype=np.float32,
        )

        action, _ = model.predict(obs, deterministic=True)
        action_int = int(action)

        reasoning = (
            f"PPO Policy decision '{ACTION_NAMES[action_int]}' based on state: "
            f"CPU={state.cpu}%, Mem={state.memory}%, PredCPU={state.predicted_cpu_next_15min}%, "
            f"Instances={state.instance_count}, Cost=${state.current_hourly_cost}/hr."
        )

        return ScalingDecisionOutput(
            action=action_int,
            action_name=ACTION_NAMES[action_int],
            confidence=0.95,
            reasoning=reasoning,
        )
    except Exception as e:
        print(f"Error evaluating PPO model: {e}. Executing rule-based fallback.")
        return rule_based_fallback(state)
