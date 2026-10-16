"""
Unit tests for LabelEngine.
Validates:
- Triple-barrier UP, DOWN, and NEUTRAL labeling
- Intra-candle double-breach conservative resolution
- Auxiliary future return horizons (5, 10, 20)
- Incomplete horizon invalidation on tail candles (is_target_valid == False)
- Binary direction target
"""

import sys
import os
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

from src.features.labels import LabelEngine
from tests.test_structure import create_base_df


def test_take_profit_hit_first_up():
    """Verify candle reaches +1.0% TP before -0.5% SL produces UP (+1) label."""
    df = create_base_df(n=35, base_price=100.0)

    # Bars 1..4 stay safely inside barriers [99.8, 100.2]
    df.loc[df.index[1:5], "high"] = 100.2
    df.loc[df.index[1:10], "low"] = 99.8

    # At step t+5: high spikes to 101.5 (+1.5% > +1.0% TP)
    df.loc[df.index[5], "high"] = 101.5

    engine = LabelEngine(horizon=20, take_profit_pct=0.010, stop_loss_pct=0.005)
    labels = engine.generate_labels(df)

    row_0 = labels.iloc[0]
    assert row_0["is_target_valid"] == True
    assert row_0["target_triple_barrier"] == 1.0
    assert row_0["target_label_name"] == "UP"
    assert row_0["candles_to_target"] == 5.0
    assert np.isnan(row_0["candles_to_stop"])


def test_stop_loss_hit_first_down():
    """Verify candle reaches -0.5% SL before +1.0% TP produces DOWN (-1) label."""
    df = create_base_df(n=35, base_price=100.0)

    # Bars 1..2 stay safely inside barriers [99.8, 100.2]
    df.loc[df.index[1:10], "high"] = 100.2
    df.loc[df.index[1:3], "low"] = 99.8

    # At step t+3: low drops to 99.3 (-0.7% < -0.5% SL)
    df.loc[df.index[3], "low"] = 99.3

    engine = LabelEngine(horizon=20, take_profit_pct=0.010, stop_loss_pct=0.005)
    labels = engine.generate_labels(df)

    row_0 = labels.iloc[0]
    assert row_0["is_target_valid"] == True
    assert row_0["target_triple_barrier"] == -1.0
    assert row_0["target_label_name"] == "DOWN"
    assert row_0["candles_to_stop"] == 3.0
    assert np.isnan(row_0["candles_to_target"])


def test_neither_barrier_hit_neutral():
    """Verify price oscillating between SL and TP over 20 candles produces NEUTRAL (0)."""
    df = create_base_df(n=35, base_price=100.0)

    # Price stays flat in [99.7, 100.4] for all future bars
    df.loc[df.index[1:25], "high"] = 100.4
    df.loc[df.index[1:25], "low"] = 99.7
    df.loc[df.index[1:25], "close"] = 100.1

    engine = LabelEngine(horizon=20, take_profit_pct=0.010, stop_loss_pct=0.005)
    labels = engine.generate_labels(df)

    row_0 = labels.iloc[0]
    assert row_0["is_target_valid"] == True
    assert row_0["target_triple_barrier"] == 0.0
    assert row_0["target_label_name"] == "NEUTRAL"
    assert np.isnan(row_0["candles_to_target"])
    assert np.isnan(row_0["candles_to_stop"])


def test_intra_candle_double_breach_resolution():
    """Verify edge case where both TP and SL are breached in the exact same candle."""
    df = create_base_df(n=35, base_price=100.0)

    # Bars 1..3 stay safe inside barriers [99.8, 100.2]
    df.loc[df.index[1:4], "high"] = 100.2
    df.loc[df.index[1:4], "low"] = 99.8

    # At step t+4: high spikes to 102.0 (+2.0%) and low drops to 98.0 (-2.0%)
    df.loc[df.index[4], "high"] = 102.0
    df.loc[df.index[4], "low"] = 98.0

    # Policy 1: Conservative stop (default)
    engine_cons = LabelEngine(horizon=20, same_candle_resolution="conservative_stop")
    labels_cons = engine_cons.generate_labels(df)
    assert labels_cons.iloc[0]["is_target_valid"] == True
    assert labels_cons.iloc[0]["target_triple_barrier"] == -1.0
    assert labels_cons.iloc[0]["target_label_name"] == "DOWN"
    assert labels_cons.iloc[0]["candles_to_stop"] == 4.0

    # Policy 2: Neutral
    engine_neut = LabelEngine(horizon=20, same_candle_resolution="neutral")
    labels_neut = engine_neut.generate_labels(df)
    assert labels_neut.iloc[0]["is_target_valid"] == True
    assert labels_neut.iloc[0]["target_triple_barrier"] == 0.0
    assert labels_neut.iloc[0]["target_label_name"] == "NEUTRAL"


def test_auxiliary_returns_and_binary_target():
    """Verify auxiliary returns (5, 10, 20), MFE, MAE, and binary direction."""
    df = create_base_df(n=35, base_price=100.0)

    # Entry at index 0 (close = 100.0)
    df.loc[df.index[5], "close"] = 102.0  # +2.0% at t+5
    df.loc[df.index[10], "close"] = 97.0  # -3.0% at t+10
    df.loc[df.index[20], "close"] = 105.0  # +5.0% at t+20
    df.loc[df.index[7], "high"] = 108.0  # Max future high = 108 (+8.0%)
    df.loc[df.index[12], "low"] = 94.0  # Min future low = 94 (-6.0%)

    engine = LabelEngine(horizon=20)
    labels = engine.generate_labels(df)

    row_0 = labels.iloc[0]
    assert row_0["future_return_5"] == pytest.approx(0.02, abs=1e-5)
    assert row_0["future_return_10"] == pytest.approx(-0.03, abs=1e-5)
    assert row_0["future_return_20"] == pytest.approx(0.05, abs=1e-5)
    assert row_0["max_future_return"] == pytest.approx(0.08, abs=1e-5)
    assert row_0["min_future_return"] == pytest.approx(-0.06, abs=1e-5)
    assert row_0["target_binary"] == 1.0


def test_horizon_boundary_tail_candles():
    """Verify that tail candles lacking a full 20-candle horizon are marked invalid."""
    n = 50
    horizon = 20
    df = create_base_df(n=n, base_price=100.0)

    engine = LabelEngine(horizon=horizon)
    labels = engine.generate_labels(df)

    # Valid range: 0 .. (n - horizon - 1) = 0 .. 29 (30 candles)
    valid_slice = labels.iloc[: n - horizon]
    assert bool(valid_slice["is_target_valid"].all())

    # Tail candles: 30 .. 49 (20 candles)
    tail_slice = labels.iloc[n - horizon :]
    assert bool((~tail_slice["is_target_valid"]).all())
    assert bool((tail_slice["target_label_name"] == "UNLABELLED").all())
    assert bool(tail_slice["target_triple_barrier"].isna().all())
