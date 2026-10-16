"""
Position Sizing Strategies for Realistic Backtesting & Execution.
Reference: Section 26 (Phase 21) of Implementation Plan.

Guarantees:
- Fixed quantity sizing (constant coin volume).
- Fixed percentage of capital sizing (fraction of current portfolio equity).
- Risk-based sizing (fixed account equity risk per trade divided by stop-loss distance).
- Half-Kelly criterion sizing based on predictive probability and risk/reward.
- Maximum leverage and allocation caps to prevent over-allocation or negative cash.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PositionSizer(ABC):
    """Abstract base class for position sizing strategies."""

    @abstractmethod
    def calculate_order_quantity(
        self,
        current_equity: float,
        current_price: float,
        stop_loss_price: Optional[float] = None,
        probability: Optional[float] = None,
    ) -> float:
        """
        Calculates the quantity of asset (e.g. BTC) to purchase.
        Returns float quantity (must be >= 0.0).
        """
        pass


class FixedQuantitySizer(PositionSizer):
    """
    Fixed quantity position sizing.
    Always buys a predetermined fixed quantity (e.g. 0.1 BTC), capped by available equity.
    """

    def __init__(self, quantity: float = 0.05):
        if quantity <= 0:
            raise ValueError(f"Quantity must be strictly positive, got {quantity}")
        self.quantity = quantity

    def calculate_order_quantity(
        self,
        current_equity: float,
        current_price: float,
        stop_loss_price: Optional[float] = None,
        probability: Optional[float] = None,
    ) -> float:
        if current_price <= 0 or current_equity <= 0:
            return 0.0
        max_possible = current_equity / current_price
        return min(self.quantity, max_possible)


class PercentCapitalSizer(PositionSizer):
    """
    Fixed percentage of capital position sizing.
    Allocates a fixed fraction of current equity (e.g. 15% of portfolio equity) to each trade.
    """

    def __init__(self, capital_pct: float = 0.10, max_capital_pct: float = 0.95):
        if not (0.0 < capital_pct <= 1.0):
            raise ValueError(f"capital_pct must be in (0, 1], got {capital_pct}")
        if not (0.0 < max_capital_pct <= 1.0):
            raise ValueError(f"max_capital_pct must be in (0, 1], got {max_capital_pct}")
        self.capital_pct = capital_pct
        self.max_capital_pct = max_capital_pct

    def calculate_order_quantity(
        self,
        current_equity: float,
        current_price: float,
        stop_loss_price: Optional[float] = None,
        probability: Optional[float] = None,
    ) -> float:
        if current_price <= 0 or current_equity <= 0:
            return 0.0
        allocated_capital = current_equity * min(self.capital_pct, self.max_capital_pct)
        return float(allocated_capital / current_price)


class RiskBasedSizer(PositionSizer):
    """
    Risk-based position sizing.
    Sizes the position such that if the stop loss is triggered, the loss is limited
    to a fixed percentage of total portfolio equity (e.g. 1.0% risk per trade).
    """

    def __init__(
        self,
        risk_pct: float = 0.01,
        max_capital_pct: float = 0.50,
        default_stop_loss_pct: float = 0.005,
    ):
        if not (0.0 < risk_pct <= 0.10):
            raise ValueError(f"risk_pct must be in (0, 0.10], got {risk_pct}")
        self.risk_pct = risk_pct
        self.max_capital_pct = max_capital_pct
        self.default_stop_loss_pct = default_stop_loss_pct

    def calculate_order_quantity(
        self,
        current_equity: float,
        current_price: float,
        stop_loss_price: Optional[float] = None,
        probability: Optional[float] = None,
    ) -> float:
        if current_price <= 0 or current_equity <= 0:
            return 0.0

        risk_amount = current_equity * self.risk_pct

        if stop_loss_price is not None and stop_loss_price < current_price:
            per_unit_risk = current_price - stop_loss_price
        else:
            per_unit_risk = current_price * self.default_stop_loss_pct

        if per_unit_risk <= 0:
            return 0.0

        desired_quantity = risk_amount / per_unit_risk

        # Cap by maximum portfolio allocation to avoid extreme leverage on tight stops
        max_capital = current_equity * self.max_capital_pct
        max_quantity = max_capital / current_price

        return float(min(desired_quantity, max_quantity))


class HalfKellySizer(PositionSizer):
    """
    Half-Kelly Criterion Position Sizing.
    Uses calibrated win probability and payoff ratio, dampened by 0.5 for financial stability.
    """

    def __init__(
        self,
        payoff_ratio: float = 2.0,  # 1.0% TP / 0.5% SL = 2.0
        max_capital_pct: float = 0.35,
        default_prob: float = 0.55,
    ):
        if payoff_ratio <= 0:
            raise ValueError(f"payoff_ratio must be positive, got {payoff_ratio}")
        self.payoff_ratio = payoff_ratio
        self.max_capital_pct = max_capital_pct
        self.default_prob = default_prob

    def calculate_order_quantity(
        self,
        current_equity: float,
        current_price: float,
        stop_loss_price: Optional[float] = None,
        probability: Optional[float] = None,
    ) -> float:
        if current_price <= 0 or current_equity <= 0:
            return 0.0

        p = probability if probability is not None else self.default_prob
        q = 1.0 - p
        b = self.payoff_ratio

        # Full Kelly = (b * p - q) / b
        full_kelly = (b * p - q) / b
        if full_kelly <= 0:
            return 0.0

        half_kelly = full_kelly * 0.5
        allocation_fraction = min(half_kelly, self.max_capital_pct)

        allocated_capital = current_equity * allocation_fraction
        return float(allocated_capital / current_price)
