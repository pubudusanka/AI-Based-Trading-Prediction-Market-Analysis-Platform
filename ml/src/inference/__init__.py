"""
Real-time inference, candle buffers, model serving, and signal generation.
Reference: Section 29 (Phase 24), Section 30 (Phase 25), Section 31 (Phase 26).
"""

from src.inference.data_pipeline import (
    RollingCandleBuffer,
    ClosedCandleEvent,
)
from src.inference.service import (
    PredictionService,
    PredictionOutput,
)
from src.inference.signals import (
    SignalEngine,
    SignalRuleConfig,
    TradingSignal,
    SignalState,
    TechnicalScoreCalculator,
)

__all__ = [
    "RollingCandleBuffer",
    "ClosedCandleEvent",
    "PredictionService",
    "PredictionOutput",
    "SignalEngine",
    "SignalRuleConfig",
    "TradingSignal",
    "SignalState",
    "TechnicalScoreCalculator",
]
