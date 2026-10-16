"""
Realistic Backtesting Engine with Frictions, Sizing, Risk Metrics, Anti-Overfitting, and Paper Trading.
Reference: Section 25 (Phase 20), Section 26 (Phase 21), Section 27 (Phase 22), Section 28 (Phase 23).
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
from src.backtesting.overfitting import (
    DeflatedSharpeCalculator,
    DeflatedSharpeResult,
    FrictionStressTester,
    StressTestScenario,
    AntiOverfittingAuditor,
    AntiOverfittingReport,
)
from src.backtesting.paper import (
    PaperTradingEngine,
    VirtualOrder,
    VirtualPosition,
    VirtualTradeRecord,
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
    "DeflatedSharpeCalculator",
    "DeflatedSharpeResult",
    "FrictionStressTester",
    "StressTestScenario",
    "AntiOverfittingAuditor",
    "AntiOverfittingReport",
    "PaperTradingEngine",
    "VirtualOrder",
    "VirtualPosition",
    "VirtualTradeRecord",
]
