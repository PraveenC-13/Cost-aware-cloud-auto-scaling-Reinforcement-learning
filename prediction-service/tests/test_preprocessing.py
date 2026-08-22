import numpy as np
import pandas as pd
import pytest

from app.preprocessing import clean, make_windows, resample, scale


def _sample_df(n=200):
    idx = pd.date_range("2026-01-01", periods=n, freq="1min")
    return pd.DataFrame(
        {
            "cpu": np.random.uniform(0, 100, n),
            "memory": np.random.uniform(0, 100, n),
            "requests_per_sec": np.random.uniform(0, 500, n),
        },
        index=idx,
    )


def test_clean_fills_missing_values():
    df = _sample_df()
    df.iloc[5, 0] = np.nan
    cleaned = clean(df)
    assert cleaned["cpu"].isna().sum() == 0


def test_clean_clips_out_of_range():
    df = _sample_df()
    df.iloc[0, 0] = 150  # cpu > 100
    cleaned = clean(df)
    assert cleaned["cpu"].max() <= 100


def test_resample_fixed_interval():
    df = _sample_df()
    resampled = resample(df, freq="1min")
    assert resampled.index.freq is not None
    assert resampled.isna().sum().sum() == 0


def test_scale_range():
    df = _sample_df()
    values, scaler = scale(clean(df))
    assert values.min() >= -1e-9
    assert values.max() <= 1.0 + 1e-9


def test_make_windows_shapes():
    values = np.random.rand(100, 3)
    X, y = make_windows(values, window_size=60, horizon=15, target_columns=(0, 2))
    assert X.shape == (100 - 60 - 15 + 1, 60, 3)
    assert y.shape == (100 - 60 - 15 + 1, 15, 2)


def test_make_windows_raises_when_too_little_data():
    values = np.random.rand(10, 3)
    with pytest.raises(ValueError):
        make_windows(values, window_size=60, horizon=15)
