"""
Unit tests for FibonacciEngine.
Validates:
- Upward impulse retracement calculations (0.236, 0.382, 0.500, 0.618, 0.786, 1.000)
- Downward impulse retracement calculations
- Distance and near proximity binary flags (near_618, near_382)
- Zero lookahead bias invariance
- Empty DataFrame handling
"""

import sys
import os
import numpy as np
import pandas as pd
import pytest

# Ensure ml and ml/src are on path for direct test execution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(ML_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from src.features.fibonacci import FibonacciEngine
from tests.test_structure import create_base_df


def test_fibonacci_upward_impulse():
    """
    Test Low -> High impulse.
    Low at 80 (confirmed first), High at 120 (confirmed second).
    Range = 40.
    """
    k = 2
    df = create_base_df(n=25, base_price=100.0)

    # Trough at index 4 (low=80.0, confirmed at index 6)
    df.loc[df.index[4], "low"] = 80.0
    df.loc[df.index[4], "close"] = 82.0

    # Peak at index 10 (high=120.0, confirmed at index 12)
    df.loc[df.index[10], "high"] = 120.0
    df.loc[df.index[10], "close"] = 118.0

    engine = FibonacciEngine(k_confirmation=k)
    res = engine.compute(df)

    # Before both swings confirmed (< 12), fib levels are NaN
    assert np.isnan(res.loc[df.index[6], "fib_level_500"])

    # At index 12, both swings confirmed, impulse direction is +1 (Low -> High)
    idx_12 = df.index[12]
    assert res.loc[idx_12, "fib_impulse_direction"] == 1
    assert res.loc[idx_12, "fib_swing_range"] == pytest.approx(40.0, abs=1e-5)

    # Upward retracement levels: high - ratio * range
    expected_500 = 120.0 - 0.500 * 40.0  # 100.0
    expected_618 = 120.0 - 0.618 * 40.0  # 95.28
    expected_382 = 120.0 - 0.382 * 40.0  # 104.72
    expected_236 = 120.0 - 0.236 * 40.0  # 110.56
    expected_786 = 120.0 - 0.786 * 40.0  # 88.56
    expected_1000 = 80.0

    assert res.loc[idx_12, "fib_level_500"] == pytest.approx(expected_500, abs=1e-4)
    assert res.loc[idx_12, "fib_level_618"] == pytest.approx(expected_618, abs=1e-4)
    assert res.loc[idx_12, "fib_level_382"] == pytest.approx(expected_382, abs=1e-4)
    assert res.loc[idx_12, "fib_level_236"] == pytest.approx(expected_236, abs=1e-4)
    assert res.loc[idx_12, "fib_level_786"] == pytest.approx(expected_786, abs=1e-4)
    assert res.loc[idx_12, "fib_level_1000"] == pytest.approx(expected_1000, abs=1e-4)


def test_fibonacci_downward_impulse():
    """
    Test High -> Low impulse.
    High at 120 (confirmed first), Low at 80 (confirmed second).
    Range = 40.
    """
    k = 2
    df = create_base_df(n=25, base_price=100.0)

    # Peak at index 4 (high=120.0, confirmed at index 6)
    df.loc[df.index[4], "high"] = 120.0
    df.loc[df.index[4], "close"] = 118.0

    # Trough at index 10 (low=80.0, confirmed at index 12)
    df.loc[df.index[10], "low"] = 80.0
    df.loc[df.index[10], "close"] = 82.0

    engine = FibonacciEngine(k_confirmation=k)
    res = engine.compute(df)

    idx_12 = df.index[12]
    assert res.loc[idx_12, "fib_impulse_direction"] == -1
    assert res.loc[idx_12, "fib_swing_range"] == pytest.approx(40.0, abs=1e-5)

    # Downward retracement levels: low + ratio * range
    expected_500 = 80.0 + 0.500 * 40.0  # 100.0
    expected_618 = 80.0 + 0.618 * 40.0  # 104.72
    expected_382 = 80.0 + 0.382 * 40.0  # 95.28

    assert res.loc[idx_12, "fib_level_500"] == pytest.approx(expected_500, abs=1e-4)
    assert res.loc[idx_12, "fib_level_618"] == pytest.approx(expected_618, abs=1e-4)
    assert res.loc[idx_12, "fib_level_382"] == pytest.approx(expected_382, abs=1e-4)


def test_near_fib_flags_and_distances():
    """Verify near_618 and near_382 flags and signed relative distances."""
    k = 2
    df = create_base_df(n=25, base_price=100.0)

    # Trough at 4 (low=80), Peak at 10 (high=120) -> Upward impulse
    df.loc[df.index[4], "low"] = 80.0
    df.loc[df.index[10], "high"] = 120.0

    # Expected 618 level = 95.28.
    # At index 15, let close = 95.30 (within 0.3% of 95.28)
    df.loc[df.index[15], "close"] = 95.30
    df.loc[df.index[15], "high"] = 96.0
    df.loc[df.index[15], "low"] = 95.0

    # At index 16, let close = 104.75 (near 382 level = 104.72)
    df.loc[df.index[16], "close"] = 104.75
    df.loc[df.index[16], "high"] = 105.0
    df.loc[df.index[16], "low"] = 104.0

    engine = FibonacciEngine(k_confirmation=k, near_threshold_pct=0.003)
    res = engine.compute(df)

    # Index 15: near 0.618
    assert res.loc[df.index[15], "near_618"] == 1
    assert res.loc[df.index[15], "near_382"] == 0
    expected_d618 = (95.30 - (120.0 - 0.618 * 40.0)) / 95.30
    assert res.loc[df.index[15], "distance_to_618"] == pytest.approx(expected_d618, abs=1e-5)

    # Index 16: near 0.382
    assert res.loc[df.index[16], "near_382"] == 1
    assert res.loc[df.index[16], "near_618"] == 0


def test_zero_lookahead_bias():
    """
    CRITICAL INVARIANT TEST:
    Adding future bars must NOT change any previously calculated Fibonacci features.
    """
    k = 3
    np.random.seed(42)
    n = 60
    dates = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    close = 50000.0 + np.cumsum(np.random.normal(0, 100, n))
    high = close + np.random.uniform(10, 50, n)
    low = close - np.random.uniform(10, 50, n)
    open_p = close + np.random.uniform(-20, 20, n)

    df_full = pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": 1000.0},
        index=dates,
    )

    engine = FibonacciEngine(k_confirmation=k)

    # Compute on first 45 candles
    df_past = df_full.iloc[:45].copy()
    features_past = engine.compute(df_past)

    # Compute on all 60 candles
    features_future = engine.compute(df_full)

    # Sliced rows 0..44 must match exactly
    features_future_slice = features_future.iloc[:45]

    for col in FibonacciEngine.FEATURE_NAMES:
        s_past = pd.Series(features_past[col]).fillna(0.0).to_numpy(dtype=float)
        s_future = pd.Series(features_future_slice[col]).fillna(0.0).to_numpy(dtype=float)
        diff = s_past - s_future
        max_abs_diff = float(np.max(np.abs(diff)))
        assert max_abs_diff == pytest.approx(0.0, abs=1e-9), (
            f"Lookahead leakage detected in column {col}! Max diff: {max_abs_diff}"
        )


def test_empty_dataframe():
    """Verify empty input returns empty DataFrame with correct columns."""
    engine = FibonacciEngine()
    empty_df = pd.DataFrame(columns=["high", "low", "close"])
    res = engine.compute(empty_df)
    assert len(res) == 0
    assert list(res.columns) == engine.FEATURE_NAMES
