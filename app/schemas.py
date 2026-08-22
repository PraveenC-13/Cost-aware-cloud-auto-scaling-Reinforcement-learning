from pydantic import BaseModel, Field


class ScalingStateInput(BaseModel):
    """Pydantic schema validating incoming infrastructure state metrics."""

    cpu: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current CPU utilization percentage [0.0 - 100.0]",
        examples=[75.5],
    )
    memory: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current Memory utilization percentage [0.0 - 100.0]",
        examples=[60.0],
    )
    predicted_cpu_next_15min: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Predicted CPU utilization over next 15 minutes [0.0 - 100.0]",
        examples=[85.0],
    )
    instance_count: int = Field(
        ...,
        ge=1,
        description="Current number of active compute instances",
        examples=[4],
    )
    current_hourly_cost: float = Field(
        ...,
        ge=0.0,
        description="Current hourly cost rate in USD",
        examples=[0.20],
    )


class ScalingDecisionOutput(BaseModel):
    """Pydantic schema for scaling decision endpoint response."""

    action: int = Field(
        ...,
        description="Discrete action code: 0=hold, 1=scale_up, 2=scale_down",
        examples=[1],
    )
    action_name: str = Field(
        ...,
        description="Human-readable action description ('hold', 'scale_up', 'scale_down')",
        examples=["scale_up"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the decision [0.0 - 1.0]",
        examples=[0.95],
    )
    reasoning: str = Field(
        ...,
        description="Explanation or rule/model rationale behind the scaling decision",
        examples=["Predicted CPU exceeds SLA threshold (85.0% > 80.0%). Triggering scale_up."],
    )
