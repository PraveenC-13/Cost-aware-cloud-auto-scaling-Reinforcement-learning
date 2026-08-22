"""
xgboost_model.py
-----------------
Faster baseline to compare against the LSTM. Engineers lag features,
rolling stats, and time-of-day/day-of-week features, then trains one
XGBRegressor per forecast horizon step (via MultiOutputRegressor) for
each target (cpu, requests_per_sec).
"""

from __future__ import annotations

import os
import pickle
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor

LAGS = (1, 5, 15)
ROLLING_WINDOWS = (5, 15)


def engineer_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Build lag / rolling / calendar features for a single target column.
    `df` must be indexed by a DatetimeIndex at a fixed frequency.
    """
    out = pd.DataFrame(index=df.index)
    out[target_col] = df[target_col]

    for lag in LAGS:
        out[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)

    for window in ROLLING_WINDOWS:
        out[f"{target_col}_roll_mean_{window}"] = (
            df[target_col].rolling(window).mean()
        )
        out[f"{target_col}_roll_std_{window}"] = df[target_col].rolling(window).std()

    out["hour_of_day"] = df.index.hour
    out["day_of_week"] = df.index.dayofweek
    out["is_weekend"] = (df.index.dayofweek >= 5).astype(int)

    return out


def make_supervised(
    df: pd.DataFrame, target_col: str, horizon: int = 15
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (X, y) where y has one column per horizon step
    (target_col_t+1 ... target_col_t+horizon).
    """
    features = engineer_features(df, target_col)

    y = pd.DataFrame(index=df.index)
    for step in range(1, horizon + 1):
        y[f"{target_col}_t+{step}"] = df[target_col].shift(-step)

    combined = pd.concat([features, y], axis=1).dropna()
    X = combined[features.columns]
    y = combined[y.columns]
    return X, y


def train_xgb_for_target(
    df: pd.DataFrame,
    target_col: str,
    horizon: int = 15,
    **xgb_kwargs,
) -> tuple[MultiOutputRegressor, list[str]]:
    """Train a MultiOutputRegressor(XGBRegressor) to predict `horizon`
    steps ahead for one target column (e.g. 'cpu' or 'requests_per_sec').
    """
    X, y = make_supervised(df, target_col, horizon=horizon)

    base_params = dict(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
    )
    base_params.update(xgb_kwargs)

    model = MultiOutputRegressor(XGBRegressor(**base_params))
    model.fit(X, y)
    return model, list(X.columns)


def train_all_targets(
    df: pd.DataFrame,
    target_cols: tuple[str, ...] = ("cpu", "requests_per_sec"),
    horizon: int = 15,
) -> Dict[str, tuple[MultiOutputRegressor, list[str]]]:
    """Train one model per target column. Returns {target: (model, feature_names)}."""
    return {
        col: train_xgb_for_target(df, col, horizon=horizon) for col in target_cols
    }


def predict_next(
    models: Dict[str, tuple[MultiOutputRegressor, list[str]]],
    latest_df: pd.DataFrame,
) -> Dict[str, np.ndarray]:
    """Predict the next `horizon` steps for each target from the most
    recent rows of `latest_df` (must contain enough history for the
    largest lag/rolling window used at training time).
    """
    predictions = {}
    for target_col, (model, feature_names) in models.items():
        features = engineer_features(latest_df, target_col)
        latest_row = features[feature_names].iloc[[-1]].dropna()
        if latest_row.empty:
            raise ValueError(
                f"Not enough history to build features for '{target_col}'"
            )
        predictions[target_col] = model.predict(latest_row)[0]
    return predictions


def save_models(models: dict, path: str = "saved_models/xgboost_models.pkl") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(models, f)


def load_models(path: str = "saved_models/xgboost_models.pkl") -> dict:
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    # Smoke test with synthetic data.
    rng = pd.date_range("2026-01-01", periods=500, freq="1min")
    df_dummy = pd.DataFrame(
        {
            "cpu": 50 + 10 * np.sin(np.linspace(0, 20, 500)) + np.random.randn(500),
            "requests_per_sec": 100
            + 20 * np.sin(np.linspace(0, 20, 500))
            + np.random.randn(500) * 5,
        },
        index=rng,
    )
    trained = train_all_targets(df_dummy)
    preds = predict_next(trained, df_dummy)
    print({k: v.shape for k, v in preds.items()})
