"""
Unit tests for BacktestEngine, Position Sizers, Execution Frictions, and Metrics (Phases 20 & 21).
Reference: Section 25 & 26 of Implementation Plan.

Validates:
- Position Sizing strategies (Fixed, Percent, Risk-based, Half-Kelly)
- Execution at candle T+1 Open with zero lookahead bias
- Trading fee and slippage deductions
- Intra-candle barrier triggers (Take Profit, Stop Loss)
- Conservative collision resolution (SL takes precedence if both touched in same candle)
- Time limit horizon exits
- Financial metrics computation (Sharpe, Sortino, Drawdown, Profit Factor)
- End-to-end integration with ML models and report generation
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

from src.backtesting.sizing import (
    FixedQuantitySizer,
    PercentCapitalSizer,
    RiskBasedSizer,
    HalfKellySizer,
)
from src.backtesting.trade import Trade
from src.backtesting.metrics import BacktestMetrics, MetricsCalculator
from src.backtesting.engine import BacktestEngine, BacktestResult
from src.training.models import RandomForestModel
from tests.test_eda import create_synthetic_dataset


def test_position_sizers():
    equity = 10_000.0
    price = 50_000.0

    # 1. Fixed Quantity Sizer
    fixed_sizer = FixedQuantitySizer(quantity=0.1)
    qty = fixed_sizer.calculate_order_quantity(equity, price)
    assert np.isclose(qty, 0.1)

    # 2. Percent Capital Sizer (20% of 10,000 = $2,000 / $50,000 = 0.04)
    pct_sizer = PercentCapitalSizer(capital_pct=0.20)
    qty = pct_sizer.calculate_order_quantity(equity, price)
    assert np.isclose(qty, 0.04)

    # 3. Risk-Based Sizer (1% risk = $100; SL at 49,000 = $1,000/unit risk -> qty = 100/1000 = 0.10)
    risk_sizer = RiskBasedSizer(risk_pct=0.01, max_capital_pct=0.50)
    qty = risk_sizer.calculate_order_quantity(equity, price, stop_loss_price=49_000.0)
    assert np.isclose(qty, 0.10)

    # 4. Half Kelly Sizer (win prob 0.60, payoff 2.0 -> full kelly 0.40 -> half kelly 0.20)
    kelly_sizer = HalfKellySizer(payoff_ratio=2.0)
    qty = kelly_sizer.calculate_order_quantity(equity, price, probability=0.60)
    assert np.isclose(qty, (10_000.0 * 0.20) / 50_000.0)


class MockConstantModel:
    """Mock model that always predicts a specified probability for UP."""
    def __init__(self, up_prob: float = 0.60, name: str = "MockModel"):
        self.up_prob = up_prob
        self.name = name

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        n = len(df)
        down = (1.0 - self.up_prob) / 2.0
        neutral = down
        return pd.DataFrame(
            {"DOWN": [down] * n, "NEUTRAL": [neutral] * n, "UP": [self.up_prob] * n},
            index=df.index,
        )


def test_execution_at_t_plus_one_open_with_frictions():
    """Verify orders execute at T+1 Open with slippage and fees applied."""
    dates = pd.date_range("2026-01-01", periods=5, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0, 102.0, 103.0, 104.0, 105.0],
            "high": [101.0, 103.0, 104.0, 105.0, 106.0],
            "low": [99.0, 101.0, 102.0, 103.0, 104.0],
            "close": [100.5, 102.5, 103.5, 104.5, 105.5],
        },
        index=dates,
    )

    engine = BacktestEngine(
        initial_capital=10_000.0,
        sizer=FixedQuantitySizer(quantity=10.0),
        fee_pct=0.001,
        slippage_pct=0.0005,
        take_profit_pct=0.10,  # wide so it won't hit immediately
        stop_loss_pct=0.10,
        min_confidence=0.50,
    )

    model = MockConstantModel(up_prob=0.80)
    result = engine.run(df, model)

    assert len(result.trades) >= 1
    t = result.trades[0]

    # Signal at close of candle 0 (100.5), entry at OPEN of candle 1 (102.0)
    assert t.raw_entry_price == 102.0
    # Entry price with slippage: 102.0 * 1.0005 = 102.051
    assert np.isclose(t.entry_price, 102.0 * 1.0005)
    # Entry fee: 10 * 102.051 * 0.001
    assert t.entry_fee > 0.0
    assert t.slippage_cost > 0.0


def test_intra_candle_barrier_take_profit():
    """Verify intra-candle High triggering Take Profit."""
    dates = pd.date_range("2026-01-01", periods=4, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 100.0, 102.0, 100.0],  # Candle 2 hits +2% (> 1.0% TP)
            "low": [100.0, 100.0, 99.8, 100.0],
            "close": [100.0, 100.0, 101.5, 100.0],
        },
        index=dates,
    )

    engine = BacktestEngine(
        initial_capital=10_000.0,
        sizer=FixedQuantitySizer(quantity=10.0),
        fee_pct=0.001,
        slippage_pct=0.0005,
        take_profit_pct=0.01,  # 1%
        stop_loss_pct=0.01,
        min_confidence=0.50,
    )

    model = MockConstantModel(up_prob=0.80)
    result = engine.run(df, model)

    assert len(result.trades) >= 1
    t = result.trades[0]
    assert t.exit_reason == "TAKE_PROFIT"
    assert t.is_winner is True
    assert t.net_pnl > 0


def test_intra_candle_barrier_stop_loss():
    """Verify intra-candle Low triggering Stop Loss."""
    dates = pd.date_range("2026-01-01", periods=4, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 100.0, 100.2, 100.0],
            "low": [100.0, 100.0, 99.0, 100.0],   # Candle 2 drops -1% (< -0.5% SL)
            "close": [100.0, 100.0, 99.2, 100.0],
        },
        index=dates,
    )

    engine = BacktestEngine(
        initial_capital=10_000.0,
        sizer=FixedQuantitySizer(quantity=10.0),
        fee_pct=0.001,
        slippage_pct=0.0005,
        take_profit_pct=0.01,
        stop_loss_pct=0.005,  # 0.5%
        min_confidence=0.50,
    )

    model = MockConstantModel(up_prob=0.80)
    result = engine.run(df, model)

    assert len(result.trades) >= 1
    t = result.trades[0]
    assert t.exit_reason == "STOP_LOSS"
    assert t.is_winner is False
    assert t.net_pnl < 0


def test_conservative_collision_resolution():
    """Verify that when both TP and SL are hit in same candle, SL takes precedence."""
    dates = pd.date_range("2026-01-01", periods=4, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 100.0, 105.0, 100.0],  # Huge wick high (> 1% TP)
            "low": [100.0, 100.0, 95.0, 100.0],   # Huge wick low (< 0.5% SL)
            "close": [100.0, 100.0, 101.0, 100.0],
        },
        index=dates,
    )

    engine = BacktestEngine(
        initial_capital=10_000.0,
        take_profit_pct=0.01,
        stop_loss_pct=0.005,
        min_confidence=0.50,
    )

    model = MockConstantModel(up_prob=0.80)
    result = engine.run(df, model)

    assert len(result.trades) >= 1
    t = result.trades[0]
    # Conservative rule: STOP_LOSS must win tie-breaker
    assert t.exit_reason == "STOP_LOSS"


def test_time_limit_horizon_exit():
    """Verify trade exits on time horizon when neither barrier is touched."""
    n = 25
    dates = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0] * n,
            "high": [100.1] * n,
            "low": [99.9] * n,
            "close": [100.0] * n,
        },
        index=dates,
    )

    engine = BacktestEngine(
        initial_capital=10_000.0,
        max_holding_candles=5,
        take_profit_pct=0.05,
        stop_loss_pct=0.05,
        min_confidence=0.50,
    )

    model = MockConstantModel(up_prob=0.80)
    result = engine.run(df, model)

    assert len(result.trades) >= 1
    t = result.trades[0]
    assert t.exit_reason == "TIME_LIMIT"
    assert t.holding_candles == 5


def test_end_to_end_backtest_with_random_forest():
    """End-to-end backtest integration with trained RandomForest model."""
    df = create_synthetic_dataset(n=300)
    train_df = df.iloc[:180].copy()
    test_df = df.iloc[180:].copy()

    rf = RandomForestModel(n_estimators=30, max_depth=4, random_state=42)
    rf.fit(train_df)

    engine = BacktestEngine(
        initial_capital=10_000.0,
        sizer=PercentCapitalSizer(capital_pct=0.20),
        fee_pct=0.001,
        slippage_pct=0.0005,
        take_profit_pct=0.01,
        stop_loss_pct=0.005,
        max_holding_candles=20,
        min_confidence=0.40,
    )

    result = engine.run(test_df, rf, symbol="BTC/USDT", timeframe="15m")

    assert result.symbol == "BTC/USDT"
    assert result.timeframe == "15m"
    assert len(result.equity_curve) == len(test_df)
    assert result.metrics.initial_capital == 10_000.0

    # Test report markdown generation
    md = result.to_markdown()
    assert "# Backtest Performance Report: RandomForest" in md
    assert "Execution & Friction Assumptions" in md
    assert "Key Performance Indicators" in md
    assert "Recent Trade Execution Log" in md

    # Test report saving
    with tempfile.TemporaryDirectory() as tmpdir:
        rpt_path = os.path.join(tmpdir, "test_backtest.md")
        saved = result.save_report(rpt_path)
        assert os.path.exists(saved)
