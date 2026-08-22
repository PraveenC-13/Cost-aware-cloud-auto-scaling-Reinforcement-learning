"""
Request/response data shapes for the Workload Prediction Service.
These match the API contract agreed with rl-engine (Pooja Surve) and
backend-api (Praveen C).
"""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class MetricPoint(BaseModel):
    """One raw metric sample coming from monitoring-agent / InfluxDB."""

    timestamp: datetime
    cpu: float = Field(..., ge=0, le=100, description="CPU utilization percent")
    memory: float = Field(..., ge=0, le=100, description="Memory utilization percent")
    requests_per_sec: float = Field(..., ge=0, description="Incoming request rate")


class PredictRequest(BaseModel):
    """Body of POST /predict. Expects the last N (default 60) points."""

    history: List[MetricPoint] = Field(..., min_length=1)


class ForecastPoint(BaseModel):
    """One forecasted future point."""

    timestamp: datetime
    predicted_cpu: float
    predicted_requests_per_sec: float


class PredictResponse(BaseModel):
    """Body returned by POST /predict."""

    forecast: List[ForecastPoint]
    model_used: Literal["lstm", "xgboost", "stub"]
    confidence: float = Field(..., ge=0, le=1)
