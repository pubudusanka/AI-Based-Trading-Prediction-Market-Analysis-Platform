"""
Unit tests for baseline trading strategies and benchmark evaluation.
Reference: Section 19 (Phase 14) of Implementation Plan.

Validates:
- RuleBasedBaselineStrategy (RSI + Trend + Candlestick Pattern)
- MomentumBaselineStrategy (Trend regime + Breakout)
- MajorityClassBaseline
- StratifiedRandomBaseline (reproducibility & distributions)
- Comprehensive multi-class evaluation metric calculations
- Edge case handling (empty subsets, boundary rows)
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

from src.training.baseline import (
    BaselineStrategy,
    BaselineEvaluationResult,
    RuleBasedBaselineStrategy,
    MomentumBaselineStrategy,
    MajorityClassBaseline,
    StratifiedRandomBaseline,
)
from tests.test_eda import create_synthetic_dataset


def test_rule_based_baseline_logic():
    """Verify RSI + Trend + Candlestick rules generate expected signals."""
    dates = pd.date_range("2026-01-01", periods=5, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "close": [105.0, 95.0, 100.0, 100.0, 100.0],
            "rsi_14": [25.0, 75.0, 50.0, 25.0, 75.0],
            "sma_200": [100.0, 100.0, 100.0, 100.0, 100.0],
            "pattern_bullish_engulfing": [1.0, 0.0, 0.0, 0.0, 0.0],
            "pattern_bearish_engulfing": [0.0, 1.0, 0.0, 0.0, 0.0],
            "pattern_hammer": [0.0, 0.0, 0.0, 0.0, 0.0],
            "pattern_shooting_star": [0.0, 0.0, 0.0, 0.0, 0.0],
        },
        index=dates,
    )

    strategy = RuleBasedBaselineStrategy(rsi_oversold=30.0, rsi_overbought=70.0)
    preds = strategy.predict(df)

    # Row 0: RSI=25 (<30), close=105 (>=100), bullish_engulfing=1 -> UP (+1)
    assert preds.iloc[0] == 1.0
    # Row 1: RSI=75 (>70), close=95 (<=100), bearish_engulfing=1 -> DOWN (-1)
    assert preds.iloc[1] == -1.0
    # Row 2: RSI=50 -> NEUTRAL (0)
    assert preds.iloc[2] == 0.0
    # Row 3: RSI=25 but no bullish pattern -> NEUTRAL (0)
    assert preds.iloc[3] == 0.0
    # Row 4: RSI=75 but no bearish pattern -> NEUTRAL (0)
    assert preds.iloc[4] == 0.0

    # Probability shape
    proba = strategy.predict_proba(df)
    assert proba.shape == (5, 3)
    assert list(proba.columns) == ["DOWN", "NEUTRAL", "UP"]
    # Row 0 should have UP as highest prob
    assert proba.iloc[0]["UP"] > proba.iloc[0]["DOWN"]
    # Row 1 should have DOWN as highest prob
    assert proba.iloc[1]["DOWN"] > proba.iloc[1]["UP"]


def test_momentum_baseline_logic():
    """Verify Trend direction + Breakout rules generate expected signals."""
    dates = pd.date_range("2026-01-01", periods=4, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "trend_direction": [1.0, -1.0, 1.0, 0.0],
            "is_breakout_high": [1.0, 0.0, 0.0, 1.0],
            "is_breakout_low": [0.0, 1.0, 0.0, 0.0],
        },
        index=dates,
    )

    strategy = MomentumBaselineStrategy()
    preds = strategy.predict(df)

    # Row 0: Uptrend (+1) and Breakout High -> UP (+1)
    assert preds.iloc[0] == 1.0
    # Row 1: Downtrend (-1) and Breakout Low -> DOWN (-1)
    assert preds.iloc[1] == -1.0
    # Row 2: Uptrend but no breakout -> NEUTRAL (0)
    assert preds.iloc[2] == 0.0
    # Row 3: Sideways (0) even with breakout -> NEUTRAL (0)
    assert preds.iloc[3] == 0.0


def test_majority_class_and_random_baselines():
    """Verify Majority Class and Stratified Random baseline behavior."""
    df = pd.DataFrame({"dummy": np.zeros(50)})

    majority = MajorityClassBaseline(constant_label=0.0)
    preds = majority.predict(df)
    assert (preds == 0.0).all()
    proba = majority.predict_proba(df)
    assert (proba["NEUTRAL"] == 1.0).all()

    # Stratified Random
    random_strat = StratifiedRandomBaseline(p_down=0.2, p_neutral=0.6, p_up=0.2, seed=123)
    rand_preds = random_strat.predict(df)
    assert len(rand_preds) == 50
    assert set(rand_preds.unique()).issubset({-1.0, 0.0, 1.0})

    # Test determinism
    rand_preds_2 = random_strat.predict(df)
    assert (rand_preds == rand_preds_2).all()


def test_baseline_evaluation_metrics_and_markdown():
    """Verify evaluation metric computation against synthetic dataset."""
    df = create_synthetic_dataset(n=120)

    strategy = RuleBasedBaselineStrategy()
    eval_result = strategy.evaluate(df, target_col="target_triple_barrier", valid_col="is_target_valid")

    assert eval_result.strategy_name == "RuleBasedBaselineStrategy"
    assert eval_result.total_samples == 120
    assert eval_result.evaluated_samples > 0
    assert 0.0 <= eval_result.accuracy <= 1.0
    assert 0.0 <= eval_result.balanced_accuracy <= 1.0
    assert 0.0 <= eval_result.macro_f1 <= 1.0
    assert 0.0 <= eval_result.directional_win_rate <= 1.0
    assert 0.0 <= eval_result.signal_frequency <= 1.0

    # Confusion matrix structure
    assert len(eval_result.confusion_matrix) == 3
    assert len(eval_result.confusion_matrix[0]) == 3

    # Markdown export
    md = eval_result.to_markdown()
    assert "### Baseline Evaluation: RuleBasedBaselineStrategy" in md
    assert "Per-Class Performance" in md
    assert "Confusion Matrix" in md


def test_baseline_evaluation_empty_edge_cases():
    """Verify robust handling of empty datasets or missing targets."""
    df_empty = pd.DataFrame({
        "close": [100.0, 101.0],
        "target_triple_barrier": [np.nan, np.nan],
        "is_target_valid": [False, False],
    })

    strategy = RuleBasedBaselineStrategy()
    eval_result = strategy.evaluate(df_empty, target_col="target_triple_barrier", valid_col="is_target_valid")
    assert eval_result.evaluated_samples == 0
    assert eval_result.accuracy == 0.0

    # Missing target column should raise ValueError
    with pytest.raises(ValueError, match="not present in dataframe"):
        strategy.evaluate(df_empty, target_col="non_existent_target")
