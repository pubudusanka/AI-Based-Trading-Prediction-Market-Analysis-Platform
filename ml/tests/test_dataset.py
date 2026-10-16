"""
Unit tests for FeatureDatasetBuilder & FeatureDataset.
Validates:
- Comprehensive multi-engine feature combination (raw, technical, patterns, structure, fibonacci)
- Feature metadata tracking & SHA-256 fingerprinting
- Parquet + JSON metadata disk persistence and loading
- Strict zero lookahead leakage invariant
"""

import sys
import os
import tempfile
import numpy as np
import pandas as pd
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(ML_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from src.features.dataset import FeatureDatasetBuilder, FeatureDataset
from tests.test_structure import create_base_df


def test_feature_dataset_build():
    """Verify builder produces unified dataset with all sub-engine features and metadata."""
    df = create_base_df(n=50, base_price=50000.0)
    builder = FeatureDatasetBuilder(k_confirmation=2)
    dataset = builder.build(df, symbol="BTC/USDT", timeframe="15m")

    # 1. Raw columns must be present and match
    for col in ["open", "high", "low", "close", "volume"]:
        assert col in dataset.data.columns
        pd.testing.assert_series_equal(dataset.data[col], df[col])

    # 2. Check representative features from each phase
    # Technical (Phase 6)
    assert "rsi_14" in dataset.data.columns
    assert "ema_21" in dataset.data.columns
    assert "macd" in dataset.data.columns

    # Candlestick patterns (Phase 7)
    assert "pattern_doji" in dataset.data.columns
    assert "pattern_bullish_engulfing" in dataset.data.columns

    # Market structure (Phase 8)
    assert "is_swing_high" in dataset.data.columns
    assert "trend_direction" in dataset.data.columns
    assert "is_break_of_structure" in dataset.data.columns

    # Fibonacci (Phase 9)
    assert "fib_level_618" in dataset.data.columns
    assert "distance_to_618" in dataset.data.columns
    assert "near_618" in dataset.data.columns

    # 3. Check metadata
    meta = dataset.metadata
    assert meta.feature_version == "v1.0"
    assert meta.symbol == "BTC/USDT"
    assert meta.timeframe == "15m"
    assert meta.total_candles == 50
    assert meta.feature_count >= 70
    assert len(meta.feature_hash) == 64  # SHA-256


def test_feature_dataset_persistence():
    """Verify atomic serialization to Parquet + JSON metadata and roundtrip loading."""
    df = create_base_df(n=40, base_price=50000.0)
    builder = FeatureDatasetBuilder(k_confirmation=2)
    dataset = builder.build(df, symbol="BTC/USDT", timeframe="15m")

    with tempfile.TemporaryDirectory() as tmp_dir:
        dataset.save(tmp_dir)

        assert os.path.exists(os.path.join(tmp_dir, "features.parquet"))
        assert os.path.exists(os.path.join(tmp_dir, "metadata.json"))

        loaded = FeatureDataset.load(tmp_dir)

        # Check metadata equality
        assert loaded.metadata.feature_version == dataset.metadata.feature_version
        assert loaded.metadata.feature_hash == dataset.metadata.feature_hash
        assert loaded.metadata.total_candles == dataset.metadata.total_candles

        # Check data equality
        assert loaded.data.shape == dataset.data.shape
        assert list(loaded.data.columns) == list(dataset.data.columns)


def test_schema_hash_sensitivity():
    """Verify modifying parameters alters the feature hash to detect silent formula changes."""
    b1 = FeatureDatasetBuilder(k_confirmation=2, near_threshold_pct=0.003)
    b2 = FeatureDatasetBuilder(k_confirmation=3, near_threshold_pct=0.003)
    b3 = FeatureDatasetBuilder(k_confirmation=2, near_threshold_pct=0.005)
    b4 = FeatureDatasetBuilder(feature_version="v1.1")

    dummy_cols = ["f1", "f2", "f3"]
    h1 = b1._compute_hash(dummy_cols)
    h2 = b2._compute_hash(dummy_cols)
    h3 = b3._compute_hash(dummy_cols)
    h4 = b4._compute_hash(dummy_cols)

    assert h1 != h2
    assert h1 != h3
    assert h1 != h4
    # Determinism: same builder produces identical hash
    assert h1 == b1._compute_hash(dummy_cols)


def test_zero_lookahead_dataset():
    """
    CRITICAL INVARIANT TEST:
    Adding future bars must NOT change any previously calculated features in the unified dataset.
    """
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

    builder = FeatureDatasetBuilder(k_confirmation=3)

    # Compute on first 45 candles
    df_past = df_full.iloc[:45].copy()
    dataset_past = builder.build(df_past)

    # Compute on all 60 candles
    dataset_future = builder.build(df_full)

    past_data = dataset_past.data
    future_slice = dataset_future.data.iloc[:45]

    for col in dataset_past.metadata.feature_columns:
        s_past = pd.Series(past_data[col]).fillna(0.0).to_numpy(dtype=float)
        s_future = pd.Series(future_slice[col]).fillna(0.0).to_numpy(dtype=float)
        diff = s_past - s_future
        max_abs_diff = float(np.max(np.abs(diff)))
        assert max_abs_diff == pytest.approx(0.0, abs=1e-9), (
            f"Lookahead leakage detected in column {col}! Max diff: {max_abs_diff}"
        )
