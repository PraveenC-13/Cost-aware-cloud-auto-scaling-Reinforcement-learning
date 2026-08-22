"""
scripts_train.py
-----------------
End-to-end training script: run this once you have a trace CSV
(Google Cluster Trace / Alibaba Cluster Trace, or an InfluxDB export
with columns: timestamp, cpu, memory, requests_per_sec).

Usage:
    python scripts_train.py --csv data/trace.csv

Produces:
    saved_models/lstm_model.h5
    saved_models/xgboost_models.pkl
    Prints MAPE / RMSE for both models on a held-out test split.
"""

import argparse

import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

from app.models.lstm_model import build_lstm_model, save_model, train
from app.models.xgboost_model import predict_next, save_models, train_all_targets
from app.preprocessing import clean, load_trace_csv, make_windows, resample, scale


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, label: str):
    mape = mean_absolute_percentage_error(y_true.flatten(), y_pred.flatten())
    rmse = mean_squared_error(y_true.flatten(), y_pred.flatten(), squared=False)
    print(f"[{label}] MAPE: {mape:.4f}  RMSE: {rmse:.4f}")
    return mape, rmse


def main(csv_path: str, window_size: int, horizon: int):
    print("Loading + cleaning data...")
    df = load_trace_csv(csv_path)
    df = clean(df)
    df = resample(df, freq="1min")

    # ---- LSTM ----
    print("\n=== Training LSTM ===")
    values, scaler = scale(df)
    X, y = make_windows(values, window_size=window_size, horizon=horizon)

    n = len(X)
    train_end, val_end = int(n * 0.7), int(n * 0.85)
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    lstm = build_lstm_model(
        window_size=window_size,
        n_features=X.shape[-1],
        horizon=horizon,
        n_targets=y.shape[-1],
    )
    train(lstm, X_train, y_train, X_val, y_val, epochs=50)
    lstm_preds = lstm.predict(X_test, verbose=0)
    evaluate(y_test, lstm_preds, "LSTM")
    save_model(lstm)
    print("Saved LSTM -> saved_models/lstm_model.h5")

    # ---- XGBoost ----
    print("\n=== Training XGBoost baseline ===")
    split_idx = int(len(df) * 0.85)
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]

    xgb_models = train_all_targets(train_df, horizon=horizon)
    # Simple rolling-origin style check on the test split's first window.
    if len(test_df) > window_size:
        preds = predict_next(xgb_models, test_df.iloc[:window_size])
        actual_cpu = test_df["cpu"].iloc[window_size : window_size + horizon].values
        actual_rps = test_df["requests_per_sec"].iloc[
            window_size : window_size + horizon
        ].values
        if len(actual_cpu) == horizon:
            evaluate(actual_cpu, preds["cpu"], "XGBoost-cpu")
            evaluate(actual_rps, preds["requests_per_sec"], "XGBoost-rps")

    save_models(xgb_models)
    print("Saved XGBoost -> saved_models/xgboost_models.pkl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to trace CSV")
    parser.add_argument("--window-size", type=int, default=60)
    parser.add_argument("--horizon", type=int, default=15)
    args = parser.parse_args()

    main(args.csv, args.window_size, args.horizon)
