"""
Unit tests for MarketStructureEngine.
Validates:
- Swing High and Swing Low detection with K-candle lag
- Higher High (HH), Lower High (LH), Higher Low (HL), Lower Low (LL)
- Trend regime classification (+1, -1, 0)
- Support and Resistance levels and distances
- Breakouts and Break of Structure (BOS)
- Retest logic
- ZERO future lookahead bias
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

from src.features.structure import MarketStructureEngine


def create_base_df(n: int = 50, base_price: float = 100.0) -> pd.DataFrame:
    """Helper to generate dummy OHLC data."""
    dates = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    data = {
        "open": np.full(n, base_price),
        "high": np.full(n, base_price + 1.0),
        "low": np.full(n, base_price - 1.0),
        "close": np.full(n, base_price),
        "volume": np.full(n, 1000.0),
    }
    return pd.DataFrame(data, index=dates)


def test_swing_high_detection():
    """Verify swing high at t is confirmed strictly at index t + k."""
    k = 2
    df = create_base_df(n=20, base_price=100.0)

    # Create a clear peak at t = 5
    # t-2=3, t-1=4, t=5, t+1=6, t+2=7
    df.loc[df.index[5], "high"] = 120.0
    df.loc[df.index[5], "close"] = 118.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    # At t=5, swing high is NOT yet confirmed
    assert res.loc[df.index[5], "is_swing_high"] == 0
    assert res.loc[df.index[6], "is_swing_high"] == 0

    # At t + k = 5 + 2 = 7, candle 7 finishes and confirms the swing high at t=5
    assert res.loc[df.index[7], "is_swing_high"] == 1
    assert res.loc[df.index[7], "active_swing_high_price"] == 120.0
    assert res.loc[df.index[8], "is_swing_high"] == 0
    assert res.loc[df.index[8], "active_swing_high_price"] == 120.0


def test_swing_low_detection():
    """Verify swing low at t is confirmed strictly at index t + k."""
    k = 2
    df = create_base_df(n=20, base_price=100.0)

    # Create a clear trough at t = 6
    df.loc[df.index[6], "low"] = 80.0
    df.loc[df.index[6], "close"] = 82.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    # At t=6, swing low is not yet confirmed
    assert res.loc[df.index[6], "is_swing_low"] == 0
    # At t + k = 6 + 2 = 8, swing low is confirmed
    assert res.loc[df.index[8], "is_swing_low"] == 1
    assert res.loc[df.index[8], "active_swing_low_price"] == 80.0


def test_higher_high_and_lower_high():
    """Verify HH and LH classifications across consecutive confirmed peaks."""
    k = 2
    df = create_base_df(n=30, base_price=100.0)

    # Peak 1 at t = 4: high = 110 (confirmed at t = 6)
    df.loc[df.index[4], "high"] = 110.0
    # Peak 2 at t = 12: high = 120 (confirmed at t = 14) -> Higher High
    df.loc[df.index[12], "high"] = 120.0
    # Peak 3 at t = 20: high = 115 (confirmed at t = 22) -> Lower High
    df.loc[df.index[20], "high"] = 115.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    # Peak 1 confirmed at 6
    assert res.loc[df.index[6], "is_swing_high"] == 1
    assert res.loc[df.index[6], "is_higher_high"] == 0  # No previous peak

    # Peak 2 confirmed at 14: HH
    assert res.loc[df.index[14], "is_swing_high"] == 1
    assert res.loc[df.index[14], "is_higher_high"] == 1
    assert res.loc[df.index[14], "is_lower_high"] == 0

    # Peak 3 confirmed at 22: LH
    assert res.loc[df.index[22], "is_swing_high"] == 1
    assert res.loc[df.index[22], "is_higher_high"] == 0
    assert res.loc[df.index[22], "is_lower_high"] == 1


def test_higher_low_and_lower_low():
    """Verify HL and LL classifications across consecutive confirmed troughs."""
    k = 2
    df = create_base_df(n=30, base_price=100.0)

    # Trough 1 at t = 4: low = 80 (confirmed at t = 6)
    df.loc[df.index[4], "low"] = 80.0
    # Trough 2 at t = 12: low = 85 (confirmed at t = 14) -> Higher Low
    df.loc[df.index[12], "low"] = 85.0
    # Trough 3 at t = 20: low = 75 (confirmed at t = 22) -> Lower Low
    df.loc[df.index[20], "low"] = 75.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    # Trough 2 confirmed at 14: HL
    assert res.loc[df.index[14], "is_swing_low"] == 1
    assert res.loc[df.index[14], "is_higher_low"] == 1
    assert res.loc[df.index[14], "is_lower_low"] == 0

    # Trough 3 confirmed at 22: LL
    assert res.loc[df.index[22], "is_swing_low"] == 1
    assert res.loc[df.index[22], "is_higher_low"] == 0
    assert res.loc[df.index[22], "is_lower_low"] == 1


def test_trend_direction():
    """Verify trend direction reflects latest HH/HL (+1) and LH/LL (-1)."""
    k = 2
    df = create_base_df(n=30, base_price=100.0)

    # Peak 1 at 4 (110), Peak 2 at 12 (120 -> HH -> uptrend at 14)
    df.loc[df.index[4], "high"] = 110.0
    df.loc[df.index[12], "high"] = 120.0

    # Peak 3 at 20 (115 -> LH -> downtrend at 22)
    df.loc[df.index[20], "high"] = 115.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    assert res.loc[df.index[14], "trend_direction"] == 1
    assert res.loc[df.index[20], "trend_direction"] == 1
    assert res.loc[df.index[22], "trend_direction"] == -1


def test_breakout_and_break_of_structure():
    """Verify breakout above confirmed resistance triggers breakout and BOS."""
    k = 2
    df = create_base_df(n=20, base_price=100.0)

    # Swing high at t=4: high=110 (confirmed at t=6)
    df.loc[df.index[4], "high"] = 110.0

    # Candle 10 closes at 115 (breaking above resistance of 110)
    df.loc[df.index[10], "close"] = 115.0
    df.loc[df.index[10], "high"] = 116.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    assert res.loc[df.index[10], "is_breakout_high"] == 1
    assert res.loc[df.index[10], "is_break_of_structure"] == 1
    assert res.loc[df.index[9], "is_breakout_high"] == 0


def test_breakout_low():
    """Verify breakdown below confirmed support triggers breakout low and -1 BOS."""
    k = 2
    df = create_base_df(n=20, base_price=100.0)

    # Swing low at t=4: low=90 (confirmed at t=6)
    df.loc[df.index[4], "low"] = 90.0

    # Candle 10 closes at 85 (breaking below support of 90)
    df.loc[df.index[10], "close"] = 85.0
    df.loc[df.index[10], "low"] = 84.0

    engine = MarketStructureEngine(k_confirmation=k)
    res = engine.compute(df)

    assert res.loc[df.index[10], "is_breakout_low"] == 1
    assert res.loc[df.index[10], "is_break_of_structure"] == -1


def test_retest_support():
    """Verify pullback to broken resistance tests it as new support."""
    k = 2
    df = create_base_df(n=25, base_price=100.0)

    # Resistance established at 110 (confirmed at 6)
    df.loc[df.index[4], "high"] = 110.0

    # Breakout at candle 10 (closes at 115)
    df.loc[df.index[10], "high"] = 116.0
    df.loc[df.index[10], "close"] = 115.0

    # Candle 11 stays above 110
    df.loc[df.index[11], "high"] = 115.0
    df.loc[df.index[11], "low"] = 113.0
    df.loc[df.index[11], "close"] = 114.0

    # Retest at candle 12: low pulls back to 110.1 (within 0.5% of 110) and closes at 112
    df.loc[df.index[12], "high"] = 113.0
    df.loc[df.index[12], "low"] = 110.1
    df.loc[df.index[12], "close"] = 112.0

    engine = MarketStructureEngine(k_confirmation=k, retest_tolerance_pct=0.005)
    res = engine.compute(df)

    assert res.loc[df.index[10], "is_breakout_high"] == 1
    assert res.loc[df.index[12], "is_retest_support"] == 1


def test_retest_resistance():
    """Verify rally to broken support tests it as new resistance."""
    k = 2
    df = create_base_df(n=25, base_price=100.0)

    # Support established at 90 (confirmed at 6)
    df.loc[df.index[4], "low"] = 90.0

    # Breakdown at candle 10 (closes at 85)
    df.loc[df.index[10], "low"] = 84.0
    df.loc[df.index[10], "close"] = 85.0

    # Candle 11 stays below 90
    df.loc[df.index[11], "high"] = 87.0
    df.loc[df.index[11], "low"] = 85.0
    df.loc[df.index[11], "close"] = 86.0

    # Retest at candle 12: high rallies to 89.9 (within 0.5% of 90) and closes at 88
    df.loc[df.index[12], "high"] = 89.9
    df.loc[df.index[12], "low"] = 87.0
    df.loc[df.index[12], "close"] = 88.0

    engine = MarketStructureEngine(k_confirmation=k, retest_tolerance_pct=0.005)
    res = engine.compute(df)

    assert res.loc[df.index[10], "is_breakout_low"] == 1
    assert res.loc[df.index[12], "is_retest_resistance"] == 1


def test_zero_lookahead_bias():
    """
    CRITICAL INVARIANT TEST:
    Appending future candles must NOT alter any previously computed market structure features.
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

    engine = MarketStructureEngine(k_confirmation=k)

    # Compute on first 45 candles
    df_past = df_full.iloc[:45].copy()
    features_past = engine.compute(df_past)

    # Compute on all 60 candles
    features_future = engine.compute(df_full)

    # The first 45 rows of features_future MUST be identical to features_past
    features_future_slice = features_future.iloc[:45]

    for col in MarketStructureEngine.FEATURE_NAMES:
        s_past = pd.Series(features_past[col]).fillna(0.0).to_numpy(dtype=float)
        s_future = pd.Series(features_future_slice[col]).fillna(0.0).to_numpy(dtype=float)
        diff = s_past - s_future
        max_abs_diff = float(np.max(np.abs(diff)))
        assert max_abs_diff == pytest.approx(0.0, abs=1e-9), (
            f"Lookahead leakage detected in column {col}! Max diff: {max_abs_diff}"
        )


def test_empty_dataframe():
    """Verify empty input returns empty DataFrame with correct columns."""
    engine = MarketStructureEngine()
    empty_df = pd.DataFrame(columns=["high", "low", "close"])
    res = engine.compute(empty_df)
    assert len(res) == 0
    assert list(res.columns) == engine.FEATURE_NAMES
