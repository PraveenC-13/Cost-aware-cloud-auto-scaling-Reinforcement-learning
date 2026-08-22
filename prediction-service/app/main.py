"""
main.py
-------
FastAPI entrypoint for the Workload Prediction Service.

Loads the trained model(s) once at startup (if present in saved_models/)
and exposes:
    GET  /health
    POST /predict

If no trained model exists yet (fresh checkout, day 1), /predict falls
back to a stub response so downstream services (rl-engine) can be built
and tested against this API without waiting on training to finish.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException

from app.preprocessing import FEATURE_COLUMNS, scale
from app.schemas import ForecastPoint, PredictRequest, PredictResponse

logger = logging.getLogger("prediction-service")

WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 60))
HORIZON = int(os.getenv("HORIZON", 15))
LSTM_MODEL_PATH = os.getenv("LSTM_MODEL_PATH", "saved_models/lstm_model.h5")
XGB_MODEL_PATH = os.getenv("XGB_MODEL_PATH", "saved_models/xgboost_models.pkl")

# Populated at startup; stays empty (stub mode) if nothing is trained yet.
state: dict = {"lstm_model": None, "xgb_models": None, "scaler": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    try:
        from app.models.lstm_model import load_model as load_lstm

        if os.path.exists(LSTM_MODEL_PATH):
            state["lstm_model"] = load_lstm(LSTM_MODEL_PATH)
            logger.info("Loaded LSTM model from %s", LSTM_MODEL_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load LSTM model: %s", exc)

    try:
        from app.models.xgboost_model import load_models as load_xgb

        if os.path.exists(XGB_MODEL_PATH):
            state["xgb_models"] = load_xgb(XGB_MODEL_PATH)
            logger.info("Loaded XGBoost models from %s", XGB_MODEL_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load XGBoost models: %s", exc)

    yield
    # --- shutdown --- (nothing to clean up yet)


app = FastAPI(title="Workload Prediction Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "lstm_loaded": state["lstm_model"] is not None,
        "xgboost_loaded": state["xgb_models"] is not None,
    }


def _history_to_dataframe(req: PredictRequest) -> pd.DataFrame:
    records = [p.model_dump() for p in req.history]
    df = pd.DataFrame(records).set_index("timestamp").sort_index()
    return df[FEATURE_COLUMNS]


def _build_forecast_timestamps(last_timestamp, horizon: int, freq: str = "1min"):
    return pd.date_range(
        start=last_timestamp + pd.Timedelta(freq), periods=horizon, freq=freq
    )


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    df = _history_to_dataframe(req)

    if len(df) < WINDOW_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Need at least {WINDOW_SIZE} history points, got {len(df)}",
        )

    # Prefer the LSTM model if it's loaded; else XGBoost; else stub.
    if state["lstm_model"] is not None:
        from app.models.lstm_model import predict as lstm_predict

        window = df.iloc[-WINDOW_SIZE:]
        # NOTE: at serving time, reuse the *fitted* scaler saved during
        # training rather than re-fitting on live data. Wire that up once
        # you persist the scaler alongside the model.
        values, _ = scale(window)
        X = values.reshape(1, WINDOW_SIZE, len(FEATURE_COLUMNS))
        raw_preds = lstm_predict(state["lstm_model"], X)[0]  # (horizon, 2) -> cpu, rps
        timestamps = _build_forecast_timestamps(df.index[-1], HORIZON)
        forecast = [
            ForecastPoint(
                timestamp=ts,
                predicted_cpu=float(raw_preds[i, 0]),
                predicted_requests_per_sec=float(raw_preds[i, 1]),
            )
            for i, ts in enumerate(timestamps)
        ]
        return PredictResponse(forecast=forecast, model_used="lstm", confidence=0.87)

    if state["xgb_models"] is not None:
        from app.models.xgboost_model import predict_next

        preds = predict_next(state["xgb_models"], df)
        timestamps = _build_forecast_timestamps(df.index[-1], HORIZON)
        forecast = [
            ForecastPoint(
                timestamp=ts,
                predicted_cpu=float(preds["cpu"][i]),
                predicted_requests_per_sec=float(preds["requests_per_sec"][i]),
            )
            for i, ts in enumerate(timestamps)
        ]
        return PredictResponse(forecast=forecast, model_used="xgboost", confidence=0.8)

    # Stub fallback so rl-engine / backend-api can integrate against this
    # endpoint before a model is trained.
    return PredictResponse(forecast=[], model_used="stub", confidence=0.0)
