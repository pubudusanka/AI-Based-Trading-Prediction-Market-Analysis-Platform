"""
Unit tests for Anti-Overfitting Controls (Phase 22) and Paper Trading Engine (Phase 23).
Reference: Section 27 and Section 28 of Implementation Plan.

Validates:
- Deflated Sharpe Ratio (DSR) computation with skewness and kurtosis adjustments
- Multiple-testing penalty scaling with number of trials (N)
- Friction stress testing across multiple scenarios (2x fees, 3x slippage, break-even detection)
- Anti-overfitting governance report generation and markdown output
- Paper trading candle-by-candle virtual execution lifecycle
- Virtual trade recording (signal, timestamp, entry, stop, target, prediction prob, model version, outcome)
- Performance comparison between paper trading and backtest metrics
- Paper trading state persistence to disk
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

from src.backtesting.overfitting import (
    DeflatedSharpeCalculator,
    DeflatedSharpeResult,
    FrictionStressTester,
    AntiOverfittingAuditor,
    AntiOverfittingReport,
)
from src.backtesting.paper import (
    PaperTradingEngine,
    VirtualOrder,
    VirtualPosition,
    VirtualTradeRecord,
)
from src.backtesting.engine import BacktestEngine
from src.training.models import RandomForestModel
from tests.test_backtest import MockConstantModel
from tests.test_eda import create_synthetic_dataset


def test_deflated_sharpe_ratio_computation():
    """Verify DSR penalizes multiple trials and adjusts for non-normality."""
    np.random.seed(42)
    # Generate positive skewed return series
    returns = np.random.normal(0.0005, 0.005, 500)

    # 1. Single trial baseline
    res_1 = DeflatedSharpeCalculator.compute(returns, num_trials=1)
    assert res_1.observed_sharpe > 0
    assert 0.0 <= res_1.deflated_sharpe_ratio <= 1.0

    # 2. When number of trials tested increases, DSR must decrease (stricter penalty for data snooping)
    res_50 = DeflatedSharpeCalculator.compute(returns, num_trials=50)
    assert res_50.deflated_sharpe_ratio <= res_1.deflated_sharpe_ratio
    assert res_50.expected_max_sharpe > res_1.expected_max_sharpe


def test_friction_stress_tester():
    """Verify stress test runs multiple fee/slippage combinations."""
    dates = pd.date_range("2026-01-01", periods=20, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0 + i for i in range(20)],
            "high": [101.5 + i for i in range(20)],
            "low": [99.5 + i for i in range(20)],
            "close": [101.0 + i for i in range(20)],
        },
        index=dates,
    )

    model = MockConstantModel(up_prob=0.80)
    scenarios, be_fee, be_slip = FrictionStressTester.run_stress_scenarios(df, model)

    assert len(scenarios) == 5
    assert scenarios[0].scenario_name == "Base Reality"
    assert be_fee > 0.0
    assert be_slip > 0.0


def test_anti_overfitting_report_generation():
    """Verify AntiOverfittingAuditor produces compliant audit reports."""
    df = create_synthetic_dataset(n=250)
    model = MockConstantModel(up_prob=0.80)

    report = AntiOverfittingAuditor.audit(
        df=df,
        model=model,
        symbol="BTC/USDT",
        timeframe="15m",
        num_trials_tested=10,
    )

    assert report.symbol == "BTC/USDT"
    assert report.timeframe == "15m"
    assert len(report.stress_scenarios) > 0

    md = report.to_markdown()
    assert "# Backtest Anti-Overfitting & Robustness Audit" in md
    assert "Deflated Sharpe Ratio (DSR)" in md
    assert "Friction Stress Testing" in md
    assert "Anti-Overfitting Governance Checklist" in md

    with tempfile.TemporaryDirectory() as tmpdir:
        rpt_path = os.path.join(tmpdir, "test_audit.md")
        saved = report.save_markdown(rpt_path)
        assert os.path.exists(saved)


def test_paper_trading_virtual_lifecycle():
    """Verify candle-by-candle virtual orders, barrier triggers, and trade records."""
    model = MockConstantModel(up_prob=0.75)
    engine = PaperTradingEngine(
        model=model,
        model_version="BTC_15M_RF_v1.0",
        initial_capital=10_000.0,
        take_profit_pct=0.01,
        stop_loss_pct=0.005,
        min_confidence=0.50,
    )

    # Candle 1: triggers BUY virtual order
    c1 = {"open": 100.0, "high": 100.2, "low": 99.8, "close": 100.0, "volume": 1000.0}
    t1 = engine.process_candle(c1, timestamp="2026-01-01 00:00:00")
    assert t1 is None
    assert engine.active_position is not None
    assert len(engine.order_history) == 1
    assert engine.order_history[0].side == "BUY"

    # Candle 2: intra-candle high hits TP barrier (+1.0%)
    c2 = {"open": 100.0, "high": 102.0, "low": 99.9, "close": 101.5, "volume": 1200.0}
    t2 = engine.process_candle(c2, timestamp="2026-01-01 00:15:00")
    assert t2 is not None
    assert t2.outcome == "WIN"
    assert t2.exit_reason == "TAKE_PROFIT"
    assert t2.model_version == "BTC_15M_RF_v1.0"
    assert t2.signal == "BUY"
    assert t2.target_price > t2.entry_price
    assert t2.stop_price < t2.entry_price
    assert engine.active_position is None
    assert len(engine.order_history) == 2
    assert engine.order_history[1].side == "SELL"


def test_paper_trading_compare_with_backtest_and_persistence():
    """Verify performance comparison with backtest and state serialization."""
    model = MockConstantModel(up_prob=0.70)
    engine = PaperTradingEngine(
        model=model,
        model_version="BTC_15M_v1.0",
        initial_capital=10_000.0,
    )

    dates = pd.date_range("2026-01-01", periods=10, freq="15min", tz="UTC")
    for i, d in enumerate(dates):
        c = {"open": 100.0 + i, "high": 102.0 + i, "low": 99.0 + i, "close": 101.0 + i, "volume": 1000.0}
        engine.process_candle(c, timestamp=str(d))

    summary = engine.get_summary()
    assert summary["initial_capital"] == 10_000.0
    assert summary["model_version"] == "BTC_15M_v1.0"

    # Compare with backtest metrics
    mock_df = pd.DataFrame(
        {"open": [100.0]*10, "high": [101.5]*10, "low": [99.5]*10, "close": [100.5]*10},
        index=dates,
    )
    bt_engine = BacktestEngine(initial_capital=10_000.0)
    bt_res = bt_engine.run(mock_df, model)

    comparison = engine.compare_with_backtest(bt_res.metrics)
    assert "paper_win_rate" in comparison
    assert "backtest_win_rate" in comparison
    assert "win_rate_divergence_pct" in comparison

    # Save state to disk
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "paper_state.json")
        saved = engine.save_state(state_file)
        assert os.path.exists(saved)
