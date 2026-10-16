"""
Realistic Backtesting Engine with Frictions, Sizing, and Risk Metrics.
Reference: Section 25 (Phase 20) & Section 26 (Phase 21) of Implementation Plan.
"""

from src.backtesting.trade import Trade
from src.backtesting.sizing import (
    PositionSizer,
    FixedQuantitySizer,
    PercentCapitalSizer,
    RiskBasedSizer,
    HalfKellySizer,
)
from src.backtesting.metrics import (
    BacktestMetrics,
    MetricsCalculator,
)
from src.backtesting.engine import (
    BacktestEngine,
    BacktestResult,
)

__all__ = [
    "Trade",
    "PositionSizer",
    "FixedQuantitySizer",
    "PercentCapitalSizer",
    "RiskBasedSizer",
    "HalfKellySizer",
    "BacktestMetrics",
    "MetricsCalculator",
    "BacktestEngine",
    "BacktestResult",
]
