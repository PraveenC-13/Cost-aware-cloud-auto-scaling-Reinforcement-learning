"""
lstm_model.py
-------------
Small Keras LSTM forecaster: 1-2 LSTM layers + Dense output layer sized
to (horizon * n_target_features), reshaped back to (horizon, n_target_features).
"""

from __future__ import annotations

import os

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def build_lstm_model(
    window_size: int,
    n_features: int,
    horizon: int,
    n_targets: int,
    lstm_units: tuple[int, ...] = (64, 32),
    dropout: float = 0.2,
) -> keras.Model:
    """Build an uncompiled-then-compiled Keras Sequential LSTM model.

    Input shape:  (window_size, n_features)
    Output shape: (horizon, n_targets)  -- e.g. horizon=15, n_targets=2 (cpu, rps)
    """
    model = keras.Sequential(name="workload_lstm")
    model.add(layers.Input(shape=(window_size, n_features)))

    for i, units in enumerate(lstm_units):
        return_sequences = i < len(lstm_units) - 1
        model.add(layers.LSTM(units, return_sequences=return_sequences))
        model.add(layers.Dropout(dropout))

    model.add(layers.Dense(horizon * n_targets))
    model.add(layers.Reshape((horizon, n_targets)))

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def train(
    model: keras.Model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 50,
    batch_size: int = 32,
    patience: int = 5,
) -> keras.callbacks.History:
    """Train with early stopping on validation loss."""
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=patience, restore_best_weights=True
    )
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=2,
    )
    return history


def save_model(model: keras.Model, path: str = "saved_models/lstm_model.h5") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    model.save(path)


def load_model(path: str = "saved_models/lstm_model.h5") -> keras.Model:
    return keras.models.load_model(path)


def predict(model: keras.Model, X: np.ndarray) -> np.ndarray:
    """X shape: (n_samples, window_size, n_features) -> (n_samples, horizon, n_targets)."""
    return model.predict(X, verbose=0)


if __name__ == "__main__":
    # Smoke test with random data so you can sanity-check shapes on day one.
    WINDOW, FEATURES, HORIZON, TARGETS = 60, 3, 15, 2
    m = build_lstm_model(WINDOW, FEATURES, HORIZON, TARGETS)
    m.summary()

    X_dummy = np.random.rand(200, WINDOW, FEATURES)
    y_dummy = np.random.rand(200, HORIZON, TARGETS)
    X_tr, X_v = X_dummy[:160], X_dummy[160:]
    y_tr, y_v = y_dummy[:160], y_dummy[160:]

    train(m, X_tr, y_tr, X_v, y_v, epochs=2)
    preds = predict(m, X_v[:1])
    print("Prediction shape:", preds.shape)
