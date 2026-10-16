"""
Risk Management Module.
Implements Phase 27 (Section 32) of the AI Trading Prediction Platform.

Provides institutional-grade capital preservation controls:
- Maximum position size
- Maximum daily loss (daily circuit breaker)
- Maximum open positions
- Strict Stop Loss & Take Profit validation
- Risk/Reward ratio gating (minimum R:R threshold)
- Volatility-based sizing (ATR dynamic risk allocation)
- Peak-to-trough Maximum Drawdown circuit breaker / kill switch
- Consecutive loss cooldown mechanism
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("risk_manager")


@dataclass
class RiskConfig:
    """Configuration parameters for portfolio risk management."""
    initial_capital: float = 10000.0
    risk_per_trade_pct: float = 0.01  # 1% risk of current capital per trade
    max_position_size_pct: float = 0.25  # Max 25% of equity in single position notional
    max_daily_loss_pct: float = 0.03  # 3% daily loss limit halts new trades until next day
    max_open_positions: int = 1  # 1 open position for BTC/USDT V1 scope
    min_risk_reward_ratio: float = 1.5  # Reject setups offering < 1.5:1 reward to risk
    max_drawdown_limit_pct: float = 0.10  # 10% peak-to-trough portfolio kill switch
    consecutive_losses_for_cooldown: int = 2  # Cooldown triggered after N straight losses
    cooldown_duration_candles: int = 4  # Number of candles to wait during cooldown
    use_atr_sizing: bool = True  # Use ATR for volatility-adjusted stop and sizing
    atr_multiplier: float = 2.0  # ATR multiplier for dynamic stop buffer


@dataclass
class RiskAssessment:
    """Result of risk evaluation for an incoming trade order/signal."""
    approved: bool
    rejection_reason: Optional[str] = None
    allocated_quantity: float = 0.0
    risk_amount: float = 0.0
    risk_reward_ratio: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    circuit_breaker_active: bool = False
    cooldown_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "rejectionReason": self.rejection_reason,
            "allocatedQuantity": round(self.allocated_quantity, 6),
            "riskAmount": round(self.risk_amount, 2),
            "riskRewardRatio": round(self.risk_reward_ratio, 2),
            "stopLoss": round(self.stop_loss, 4),
            "takeProfit": round(self.take_profit, 4),
            "circuitBreakerActive": self.circuit_breaker_active,
            "cooldownActive": self.cooldown_active,
        }


class RiskManager:
    """
    Dedicated institutional risk manager enforcing strict capital preservation.
    """

    def __init__(self, config: Optional[RiskConfig] = None) -> None:
        self.config = config or RiskConfig()
        self.current_capital: float = self.config.initial_capital
        self.peak_capital: float = self.config.initial_capital
        self.daily_pnl: float = 0.0
        self.current_day: Optional[str] = None
        self.consecutive_losses: int = 0
        self.cooldown_remaining_candles: int = 0
        self.open_positions_count: int = 0
        self.is_kill_switch_active: bool = False

    def update_date_and_check_reset(self, timestamp: Optional[str]) -> None:
        """Resets daily PnL accumulator upon day rollover (UTC)."""
        if not timestamp:
            return
        day_str = timestamp[:10]  # YYYY-MM-DD
        if self.current_day != day_str:
            self.current_day = day_str
            self.daily_pnl = 0.0

    def evaluate_trade(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        is_long: bool = True,
        atr: Optional[float] = None,
        timestamp: Optional[str] = None,
    ) -> RiskAssessment:
        """
        Evaluates a proposed trade signal against all risk management constraints.
        Returns RiskAssessment indicating approval, position sizing, and validated boundaries.
        """
        self.update_date_and_check_reset(timestamp)

        # 1. Check Portfolio Drawdown Kill Switch
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if current_drawdown >= self.config.max_drawdown_limit_pct:
            self.is_kill_switch_active = True
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Hard drawdown limit breached ({current_drawdown:.2%} >= {self.config.max_drawdown_limit_pct:.2%}). Trading halted.",
                circuit_breaker_active=True,
            )

        # 2. Check Daily Loss Limit (Circuit Breaker)
        daily_loss_pct = abs(min(0.0, self.daily_pnl)) / self.config.initial_capital
        if daily_loss_pct >= self.config.max_daily_loss_pct:
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Daily loss limit breached ({daily_loss_pct:.2%} >= {self.config.max_daily_loss_pct:.2%}). Paused for remainder of day.",
                circuit_breaker_active=True,
            )

        # 3. Check Cooldown after Consecutive Losses
        if self.cooldown_remaining_candles > 0:
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Cooldown active after {self.consecutive_losses} consecutive losses. {self.cooldown_remaining_candles} candles remaining.",
                cooldown_active=True,
            )

        # 4. Check Maximum Open Positions
        if self.open_positions_count >= self.config.max_open_positions:
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Max open positions reached ({self.open_positions_count}/{self.config.max_open_positions}).",
            )

        # 5. Price & Boundary Validation
        if entry_price <= 0.0 or stop_loss <= 0.0 or take_profit <= 0.0:
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Invalid pricing: entry={entry_price}, stop={stop_loss}, tp={take_profit}",
            )

        if is_long:
            if not (stop_loss < entry_price < take_profit):
                return RiskAssessment(
                    approved=False,
                    rejection_reason=f"Invalid Long boundaries: stop ({stop_loss}) must be < entry ({entry_price}) < target ({take_profit}).",
                )
            risk_per_unit = entry_price - stop_loss
            reward_per_unit = take_profit - entry_price
        else:
            if not (take_profit < entry_price < stop_loss):
                return RiskAssessment(
                    approved=False,
                    rejection_reason=f"Invalid Short boundaries: target ({take_profit}) must be < entry ({entry_price}) < stop ({stop_loss}).",
                )
            risk_per_unit = stop_loss - entry_price
            reward_per_unit = entry_price - take_profit

        if risk_per_unit <= 0.0:
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Calculated risk per unit must be positive, got {risk_per_unit}.",
            )

        # 6. Risk / Reward Ratio Check
        rr_ratio = reward_per_unit / risk_per_unit
        if rr_ratio < self.config.min_risk_reward_ratio:
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Risk/Reward ratio {rr_ratio:.2f} below required minimum of {self.config.min_risk_reward_ratio:.2f}.",
                risk_reward_ratio=rr_ratio,
            )

        # 7. Volatility-Based Position Sizing (Fixed fractional risk + ATR bounds)
        target_risk_dollars = self.current_capital * self.config.risk_per_trade_pct

        if self.config.use_atr_sizing and atr is not None and atr > 0.0:
            # Volatility-adjusted stop validation
            min_stop_distance = atr * 0.5
            if risk_per_unit < min_stop_distance:
                # Stop is unrealistically tight compared to ATR volatility noise
                return RiskAssessment(
                    approved=False,
                    rejection_reason=f"Stop distance ({risk_per_unit:.2f}) is tighter than 0.5x ATR ({min_stop_distance:.2f}), susceptible to noise whipsaw.",
                    risk_reward_ratio=rr_ratio,
                )

        # Quantity from risk: Q = Risk / (entry - stop)
        allocated_quantity = target_risk_dollars / risk_per_unit

        # Max position notional constraint: Q * Entry <= Capital * MaxPositionPct
        max_notional = self.current_capital * self.config.max_position_size_pct
        if (allocated_quantity * entry_price) > max_notional:
            allocated_quantity = max_notional / entry_price

        # Minimum viable order check
        if allocated_quantity * entry_price < 10.0:  # Minimum 10 USDT notional
            return RiskAssessment(
                approved=False,
                rejection_reason=f"Order size too small ({allocated_quantity * entry_price:.2f} USDT < 10 USDT min).",
                risk_reward_ratio=rr_ratio,
            )

        actual_risk_dollars = allocated_quantity * risk_per_unit

        return RiskAssessment(
            approved=True,
            allocated_quantity=allocated_quantity,
            risk_amount=actual_risk_dollars,
            risk_reward_ratio=rr_ratio,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def on_trade_opened(self) -> None:
        """Called when a trade is executed into an open position."""
        self.open_positions_count += 1

    def on_trade_closed(self, realized_pnl: float, close_time: Optional[str] = None) -> None:
        """
        Called when an open position completes.
        Updates capital, peak equity, daily PnL, and consecutive loss tracking.
        """
        self.update_date_and_check_reset(close_time)
        self.open_positions_count = max(0, self.open_positions_count - 1)
        self.current_capital += realized_pnl
        self.daily_pnl += realized_pnl

        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        if realized_pnl < 0.0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.config.consecutive_losses_for_cooldown:
                self.cooldown_remaining_candles = self.config.cooldown_duration_candles
                logger.info(
                    f"Cooldown triggered: {self.consecutive_losses} straight losses. "
                    f"Pausing for {self.cooldown_remaining_candles} candles."
                )
        else:
            self.consecutive_losses = 0

    def on_candle_close(self) -> None:
        """Called at the close of each candle to decrement cooldown timers."""
        if self.cooldown_remaining_candles > 0:
            self.cooldown_remaining_candles -= 1

    def get_status(self) -> Dict[str, Any]:
        """Returns snapshot of current risk and portfolio health metrics."""
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital if self.peak_capital > 0 else 0.0
        return {
            "currentCapital": round(self.current_capital, 2),
            "peakCapital": round(self.peak_capital, 2),
            "currentDrawdownPct": round(current_drawdown * 100, 2),
            "dailyPnl": round(self.daily_pnl, 2),
            "openPositions": self.open_positions_count,
            "consecutiveLosses": self.consecutive_losses,
            "cooldownRemainingCandles": self.cooldown_remaining_candles,
            "isKillSwitchActive": self.is_kill_switch_active,
        }
