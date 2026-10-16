"""
Unit tests for Risk Management Engine (Phase 27 / Section 32).
Verifies:
- Maximum position size constraints
- Maximum daily loss circuit breaker
- Cooldown period after consecutive losses
- Maximum drawdown kill switch
- Risk/Reward ratio validation
- Volatility (ATR) stop distance validation
- Integration with PaperTradingEngine
"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd

from src.risk.manager import RiskConfig, RiskAssessment, RiskManager
from src.backtesting.paper import PaperTradingEngine, VirtualTradeRecord
from src.backtesting.sizing import PercentCapitalSizer


def test_risk_manager_approval_and_sizing():
    """Verify that compliant trade setup is approved and correctly sized."""
    config = RiskConfig(
        initial_capital=10000.0,
        risk_per_trade_pct=0.01,  # 1% risk = 100 USDT
        max_position_size_pct=0.25,  # max 2500 USDT notional
        min_risk_reward_ratio=1.5,
    )
    rm = RiskManager(config=config)

    # Entry = 100, Stop = 95 (risk = 5), Target = 110 (reward = 10) -> R:R = 2.0
    assessment = rm.evaluate_trade(
        symbol="BTC/USDT",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        is_long=True,
        atr=4.0,  # 0.5 * ATR = 2.0 < 5.0 (valid)
        timestamp="2026-01-01T12:00:00Z",
    )

    assert assessment.approved is True
    assert assessment.rejection_reason is None
    assert assessment.risk_reward_ratio == 2.0
    # Expected qty = 100 USDT risk / 5 risk_per_unit = 20 units
    assert np.isclose(assessment.allocated_quantity, 20.0)
    assert np.isclose(assessment.risk_amount, 100.0)


def test_risk_manager_min_rr_rejection():
    """Verify that trade with R:R < 1.5 is rejected."""
    config = RiskConfig(min_risk_reward_ratio=1.5)
    rm = RiskManager(config=config)

    # Entry = 100, Stop = 95 (risk = 5), Target = 105 (reward = 5) -> R:R = 1.0 < 1.5
    assessment = rm.evaluate_trade(
        symbol="BTC/USDT",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=105.0,
        is_long=True,
    )

    assert assessment.approved is False
    assert "below required minimum" in (assessment.rejection_reason or "")
    assert assessment.risk_reward_ratio == 1.0


def test_risk_manager_atr_noise_rejection():
    """Verify that unrealistically tight stop relative to ATR is rejected."""
    config = RiskConfig(use_atr_sizing=True)
    rm = RiskManager(config=config)

    # Stop distance = 1.0, but ATR = 10.0 (0.5 * ATR = 5.0 > 1.0)
    assessment = rm.evaluate_trade(
        symbol="BTC/USDT",
        entry_price=100.0,
        stop_loss=99.0,
        take_profit=110.0,
        is_long=True,
        atr=10.0,
    )

    assert assessment.approved is False
    assert "tighter than 0.5x ATR" in (assessment.rejection_reason or "")


def test_risk_manager_daily_loss_circuit_breaker():
    """Verify daily loss limit halts trading until next day rollover."""
    config = RiskConfig(
        initial_capital=10000.0,
        max_daily_loss_pct=0.03,  # 300 USDT max daily loss
        consecutive_losses_for_cooldown=10,  # Isolate daily loss from cooldown
    )
    rm = RiskManager(config=config)

    # Simulate losing trades on Day 1
    rm.on_trade_closed(realized_pnl=-200.0, close_time="2026-01-01T10:00:00Z")
    assessment_1 = rm.evaluate_trade("BTC/USDT", 100.0, 95.0, 110.0, is_long=True, timestamp="2026-01-01T11:00:00Z")
    assert assessment_1.approved is True

    # Second loss exceeds 300 USDT
    rm.on_trade_closed(realized_pnl=-150.0, close_time="2026-01-01T12:00:00Z")
    assessment_2 = rm.evaluate_trade("BTC/USDT", 100.0, 95.0, 110.0, is_long=True, timestamp="2026-01-01T13:00:00Z")
    assert assessment_2.approved is False
    assert assessment_2.circuit_breaker_active is True
    assert "Daily loss limit breached" in (assessment_2.rejection_reason or "")

    # Day 2 rollover resets daily PnL
    assessment_day2 = rm.evaluate_trade("BTC/USDT", 100.0, 95.0, 110.0, is_long=True, timestamp="2026-01-02T01:00:00Z")
    assert assessment_day2.approved is True


def test_risk_manager_consecutive_losses_cooldown():
    """Verify cooldown period triggers after consecutive losses and decrements per candle."""
    config = RiskConfig(
        consecutive_losses_for_cooldown=2,
        cooldown_duration_candles=3,
    )
    rm = RiskManager(config=config)

    # 1st loss
    rm.on_trade_closed(realized_pnl=-50.0)
    assert rm.consecutive_losses == 1
    assert rm.cooldown_remaining_candles == 0

    # 2nd consecutive loss -> triggers cooldown
    rm.on_trade_closed(realized_pnl=-50.0)
    assert rm.consecutive_losses == 2
    assert rm.cooldown_remaining_candles == 3

    # New trade should be blocked during cooldown
    assessment = rm.evaluate_trade("BTC/USDT", 100.0, 95.0, 110.0, is_long=True)
    assert assessment.approved is False
    assert assessment.cooldown_active is True

    # Decrement candles
    rm.on_candle_close()
    assert rm.cooldown_remaining_candles == 2
    rm.on_candle_close()
    assert rm.cooldown_remaining_candles == 1
    rm.on_candle_close()
    assert rm.cooldown_remaining_candles == 0

    # Now trading resumes
    assessment_resumed = rm.evaluate_trade("BTC/USDT", 100.0, 95.0, 110.0, is_long=True)
    assert assessment_resumed.approved is True


def test_risk_manager_max_drawdown_kill_switch():
    """Verify portfolio kill switch permanently halts when max drawdown threshold breached."""
    config = RiskConfig(
        initial_capital=10000.0,
        max_drawdown_limit_pct=0.10,  # 10% drawdown
    )
    rm = RiskManager(config=config)

    # Capital drops by 11% (from 10,000 to 8,900)
    rm.on_trade_closed(realized_pnl=-1100.0)

    assessment = rm.evaluate_trade("BTC/USDT", 100.0, 95.0, 110.0, is_long=True)
    assert assessment.approved is False
    assert assessment.circuit_breaker_active is True
    assert rm.is_kill_switch_active is True
    assert "Hard drawdown limit breached" in (assessment.rejection_reason or "")


class MockMLModel:
    def __init__(self, p_up: float):
        self.p_up = p_up

    def predict_proba(self, X):
        return pd.DataFrame({"DOWN": [0.1], "NEUTRAL": [0.9 - self.p_up], "UP": [self.p_up]})


def test_paper_trading_with_risk_manager_integration():
    """Verify PaperTradingEngine respects RiskManager constraints during simulation."""
    rm = RiskManager(
        config=RiskConfig(
            initial_capital=10000.0,
            consecutive_losses_for_cooldown=1,
            cooldown_duration_candles=2,
            min_risk_reward_ratio=1.5,
        )
    )

    model = MockMLModel(p_up=0.65)
    engine = PaperTradingEngine(
        model=model,
        initial_capital=10000.0,
        min_confidence=0.50,
        take_profit_pct=0.02,  # R:R = 0.02 / 0.01 = 2.0 (>= 1.5)
        stop_loss_pct=0.01,
        risk_manager=rm,
    )

    # Candle 1: Bullish signal triggers trade entry
    c1 = {"open": 100.0, "high": 100.5, "low": 99.8, "close": 100.2, "volume": 10.0}
    engine.process_candle(c1, timestamp="2026-01-01T00:00:00Z")
    assert engine.active_position is not None
    assert rm.open_positions_count == 1

    # Candle 2: Price crashes, stops out
    c2 = {"open": 100.0, "high": 100.2, "low": 98.0, "close": 98.5, "volume": 20.0}
    closed = engine.process_candle(c2, timestamp="2026-01-01T00:15:00Z")
    assert closed is not None
    assert closed.outcome == "LOSS"
    assert engine.active_position is None
    assert rm.consecutive_losses == 1
    # Cooldown was triggered and decremented once by candle close -> 1 remaining
    assert rm.cooldown_remaining_candles == 1

    # Candle 3: Model tries to signal BUY again, but RiskManager blocks entry due to cooldown
    c3 = {"open": 98.5, "high": 99.0, "low": 98.2, "close": 98.8, "volume": 15.0}
    engine.process_candle(c3, timestamp="2026-01-01T00:30:00Z")
    assert engine.active_position is None  # Blocked by cooldown!

    summary = engine.get_summary()
    assert "risk_status" in summary
    assert summary["risk_status"]["consecutiveLosses"] == 1
