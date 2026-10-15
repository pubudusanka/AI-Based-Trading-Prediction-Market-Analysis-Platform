from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import pytest

try:
    from src.features.engine import FeatureEngine, FEATURE_CATALOG_V1
except ModuleNotFoundError:
    from features.engine import FeatureEngine, FEATURE_CATALOG_V1


def create_mock_ohlcv(n: int = 250) -> pd.DataFrame:
    np.random.seed(42)
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    times = [base_time + timedelta(minutes=15 * i) for i in range(n)]

    # Generate synthetic geometric random walk
    returns = np.random.normal(0.0005, 0.008, n)
    price = 50000.0 * np.exp(np.cumsum(returns))

    highs = price * (1.0 + np.random.uniform(0.001, 0.005, n))
    lows = price * (1.0 - np.random.uniform(0.001, 0.005, n))
    opens = price * (1.0 + np.random.normal(0, 0.002, n))
    closes = price
    volumes = np.random.uniform(10.0, 500.0, n)

    df = pd.DataFrame({
        "open": np.maximum(lows, np.minimum(highs, opens)),
        "high": highs,
        "low": lows,
        "close": np.maximum(lows, np.minimum(highs, closes)),
        "volume": volumes,
    }, index=times)
    df.index.name = "open_time"
    return df


def test_feature_catalog_completeness():
    assert len(FEATURE_CATALOG_V1) >= 30
    groups = {f.group for f in FEATURE_CATALOG_V1}
    expected_groups = {"Price", "Candle", "Moving Average", "Momentum", "Volatility", "Trend", "Volume"}
    assert expected_groups.issubset(groups)


def test_feature_computation_output():
    df = create_mock_ohlcv(n=250)
    feats = FeatureEngine.compute_features(df, dropna=False)

    # Check all catalog features are present in output
    for f in FEATURE_CATALOG_V1:
        assert f.name in feats.columns, f"Missing feature column: {f.name}"

    # Check boundaries of bounded indicators
    # RSI: [0, 100]
    valid_rsi = feats["rsi_14"].dropna()
    assert (valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all()

    # Stochastic: [0, 100]
    valid_stoch = feats["stoch_k"].dropna()
    assert (valid_stoch >= 0.0).all() and (valid_stoch <= 100.0).all()

    # ADX: [0, 100]
    valid_adx = feats["adx_14"].dropna()
    assert (valid_adx >= 0.0).all() and (valid_adx <= 100.0).all()

    # ATR > 0
    valid_atr = feats["atr_14"].dropna()
    assert (valid_atr >= 0.0).all()

    # Binary flags are 0 or 1
    assert set(feats["bullish_flag"].unique()).issubset({0, 1})
    assert set(feats["bearish_flag"].unique()).issubset({0, 1})
    assert set(feats["ma_cross_20_50"].unique()).issubset({0, 1})
    assert set(feats["ma_cross_50_200"].unique()).issubset({0, 1})


def test_zero_lookahead_bias_leakage():
    """
    CRITICAL INVARIANT TEST:
    Verifies that changing data in future candles (at index T+10 ... T+50)
    has ZERO effect on features calculated at candle index T.
    """
    df1 = create_mock_ohlcv(n=100)
    feats1 = FeatureEngine.compute_features(df1, dropna=False)

    # Clone df1 and alter the future data starting from index 60 onwards
    df2 = df1.copy()
    cutoff_idx = 60
    df2.loc[df2.index[cutoff_idx:], "close"] *= 2.5
    df2.loc[df2.index[cutoff_idx:], "high"] *= 3.0
    df2.loc[df2.index[cutoff_idx:], "volume"] *= 10.0

    feats2 = FeatureEngine.compute_features(df2, dropna=False)

    # At or before cutoff_idx - 1 (time T), all feature values MUST match exactly
    slice1 = feats1.iloc[:cutoff_idx].dropna(how="all")
    slice2 = feats2.iloc[:cutoff_idx].dropna(how="all")

    for col in slice1.columns:
        s1 = slice1[col].dropna()
        s2 = slice2[col].dropna()
        np.testing.assert_allclose(
            np.asarray(s1.to_numpy(), dtype=float),
            np.asarray(s2.to_numpy(), dtype=float),
            rtol=1e-5,
            err_msg=f"Look-ahead bias detected in feature: {col}!"
        )
