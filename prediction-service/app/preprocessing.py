"""
preprocessing.py
-----------------
Turns a raw metrics time series (from InfluxDB, or a Google/Alibaba cluster
trace CSV while you're bootstrapping) into clean, windowed (X, y) sequences
that lstm_model.py and xgboost_model.py can train on.

Pipeline: load -> clean -> resample -> scale -> window.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Columns the rest of the service assumes exist after cleaning.
FEATURE_COLUMNS = ["cpu", "memory", "requests_per_sec"]


def load_trace_csv(path: str, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Load a raw trace CSV (Google Cluster Trace / Alibaba Cluster Trace style)
    or a metrics export and return a DataFrame indexed by datetime.
    """
    df = pd.read_csv(path)
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.set_index(timestamp_col).sort_index()
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and obviously bad rows.

    - Drop exact duplicate timestamps.
    - Forward-fill short gaps, then back-fill any remaining leading NaNs.
    - Clip out-of-range values (defensive against sensor glitches).
    """
    df = df[~df.index.duplicated(keep="first")]
    df = df[FEATURE_COLUMNS].copy()

    df = df.ffill().bfill()

    df["cpu"] = df["cpu"].clip(0, 100)
    df["memory"] = df["memory"].clip(0, 100)
    df["requests_per_sec"] = df["requests_per_sec"].clip(lower=0)

    return df


def resample(df: pd.DataFrame, freq: str = "1min") -> pd.DataFrame:
    """Resample to a fixed interval (default: every 1 minute), averaging
    any points that fall inside the same bucket, then re-fill any gaps
    the resampling introduces.
    """
    resampled = df.resample(freq).mean()
    resampled = resampled.interpolate(method="time").ffill().bfill()
    return resampled


def scale(
    df: pd.DataFrame, scaler: MinMaxScaler | None = None
) -> Tuple[np.ndarray, MinMaxScaler]:
    """Scale features to [0, 1]. Pass a fitted scaler in to reuse it at
    inference time (never re-fit on live/serving data).
    """
    if scaler is None:
        scaler = MinMaxScaler()
        values = scaler.fit_transform(df[FEATURE_COLUMNS])
    else:
        values = scaler.transform(df[FEATURE_COLUMNS])
    return values, scaler


def make_windows(
    values: np.ndarray,
    window_size: int = 60,
    horizon: int = 15,
    target_columns: tuple[int, ...] = (0, 2),  # cpu, requests_per_sec
) -> Tuple[np.ndarray, np.ndarray]:
    """Turn a flat (T, n_features) array into sliding-window sequences.

    Given the last `window_size` points, predict the next `horizon` points
    for `target_columns` (by default: cpu and requests_per_sec, matching
    the API contract's forecast fields).

    Returns:
        X: shape (n_samples, window_size, n_features)
        y: shape (n_samples, horizon, len(target_columns))
    """
    n_samples = len(values) - window_size - horizon + 1
    if n_samples <= 0:
        raise ValueError(
            f"Not enough data: need at least {window_size + horizon} points, "
            f"got {len(values)}"
        )

    n_features = values.shape[1]
    X = np.zeros((n_samples, window_size, n_features))
    y = np.zeros((n_samples, horizon, len(target_columns)))

    for i in range(n_samples):
        X[i] = values[i : i + window_size]
        future = values[i + window_size : i + window_size + horizon]
        y[i] = future[:, target_columns]

    return X, y


def prepare_dataset(
    csv_path: str,
    window_size: int = 60,
    horizon: int = 15,
    freq: str = "1min",
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
    """Convenience end-to-end call used by training scripts / notebooks."""
    df = load_trace_csv(csv_path)
    df = clean(df)
    df = resample(df, freq=freq)
    values, scaler = scale(df)
    X, y = make_windows(values, window_size=window_size, horizon=horizon)
    return X, y, scaler
