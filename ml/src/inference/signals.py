"""
Decoupled Trading Signal Engine combining ML Predictions, Technical Confluence, and Risk Rules.
Reference: Section 31 (Phase 26) of Implementation Plan.

Guarantees:
- Strict decoupling: Never hard-codes business or trading logic inside the ML model.
- Multi-dimensional confluence:
  1. ML Calibrated Probability Distribution (UP / DOWN / NEUTRAL).
  2. Technical Analysis Confluence Score (0 - 100) based on RSI, EMAs, MACD, Patterns, and Structure.
  3. Risk filter & trend alignment.
- Configurable signal rules (SignalRuleConfig).
- Standardized signal states: BUY, SELL, HOLD, NO_SIGNAL.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.inference.service import PredictionOutput


class SignalState(str, Enum):
    """Trading signal actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class SignalRuleConfig:
    """Configurable trading parameters for signal generation."""
    min_ml_confidence: float = 0.55
    min_technical_score_buy: float = 60.0
    max_technical_score_sell: float = 40.0
    require_trend_alignment: bool = True
    allow_short: bool = False
    take_profit_pct: float = 0.01   # +1.0%
    stop_loss_pct: float = 0.005    # -0.5%


@dataclass
class TradingSignal:
    """Consolidated trading signal produced by the Signal Engine."""
    symbol: str
    timeframe: str
    timestamp: str
    signal: str  # "BUY", "SELL", "HOLD", "NO_SIGNAL"
    ml_prediction: str
    probability_up: float
    probability_down: float
    probability_neutral: float
    technical_score: float  # 0 to 100
    risk_acceptable: bool
    suggested_entry: float
    suggested_take_profit: float
    suggested_stop_loss: float
    reasoning: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts unknown Series scalar to float with fallback."""
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class TechnicalScoreCalculator:
    """
    Computes a normalized technical confluence score (0 = extreme bear, 50 = neutral, 100 = extreme bull).
    """

    @classmethod
    def calculate_score(cls, features: pd.Series) -> Tuple[float, List[str]]:
        """
        Calculates 0-100 technical score from available technical features.
        Returns (score, list_of_reasons).
        """
        score = 50.0  # start at neutral
        reasons: List[str] = []

        # 1. EMA Trend alignment (up to +/- 15 pts)
        price = _safe_float(features.get("close"), 0.0)
        ema_200 = _safe_float(features.get("ema_200"), 0.0)
        if price > 0 and ema_200 > 0:
            if price > ema_200:
                score += 15.0
                reasons.append("Price above EMA200 (Long-term Bullish)")
            else:
                score -= 15.0
                reasons.append("Price below EMA200 (Long-term Bearish)")

        # 2. Short/medium EMA slope (up to +/- 10 pts)
        ema_21 = _safe_float(features.get("ema_21"), 0.0)
        ema_50 = _safe_float(features.get("ema_50"), 0.0)
        if ema_21 > 0 and ema_50 > 0:
            if ema_21 > ema_50:
                score += 10.0
                reasons.append("EMA21 > EMA50 Golden Cross")
            else:
                score -= 10.0
                reasons.append("EMA21 < EMA50 Death Cross")

        # 3. RSI momentum (up to +/- 10 pts)
        rsi = _safe_float(features.get("rsi_14"), 50.0)
        if rsi < 30.0:
            score += 10.0
            reasons.append(f"RSI Oversold ({rsi:.1f})")
        elif rsi > 70.0:
            score -= 10.0
            reasons.append(f"RSI Overbought ({rsi:.1f})")
        elif 45.0 <= rsi <= 60.0:
            score += 5.0
            reasons.append(f"RSI Healthy Momentum ({rsi:.1f})")

        # 4. MACD Histogram (up to +/- 10 pts)
        macd_hist = _safe_float(features.get("macd_hist"), 0.0)
        if macd_hist > 0:
            score += 8.0
            reasons.append("MACD Histogram Positive")
        elif macd_hist < 0:
            score -= 8.0
            reasons.append("MACD Histogram Negative")

        # 5. Candlestick Patterns (up to +/- 10 pts)
        bullish_patterns = ["is_hammer", "is_bullish_engulfing", "is_morning_star"]
        bearish_patterns = ["is_shooting_star", "is_bearish_engulfing", "is_evening_star", "is_hanging_man"]

        for pat in bullish_patterns:
            if _safe_float(features.get(pat), 0.0) > 0:
                score += 8.0
                reasons.append(f"Bullish Pattern: {pat.replace('is_', '').title()}")
                break

        for pat in bearish_patterns:
            if _safe_float(features.get(pat), 0.0) > 0:
                score -= 8.0
                reasons.append(f"Bearish Pattern: {pat.replace('is_', '').title()}")
                break

        # Bound score in [0.0, 100.0]
        final_score = float(max(0.0, min(100.0, score)))
        return final_score, reasons


class SignalEngine:
    """
    Decoupled Signal Engine applying risk controls and technical confirmation to ML predictions.
    """

    def __init__(self, config: Optional[SignalRuleConfig] = None):
        self.config = config or SignalRuleConfig()

    def generate_signal(
        self,
        prediction: PredictionOutput,
        latest_features: pd.Series,
    ) -> TradingSignal:
        """
        Combines model prediction, technical confirmation score, and risk filters.
        """
        current_price = _safe_float(latest_features.get("close"), 0.0)
        tech_score, reasons = TechnicalScoreCalculator.calculate_score(latest_features)

        p_up = prediction.probability_up
        p_down = prediction.probability_down
        p_neutral = prediction.probability_neutral

        signal_state = SignalState.NO_SIGNAL
        signal_reasons: List[str] = []
        risk_acceptable = True

        # Check Trend Alignment if required
        trend_is_bullish = tech_score >= 50.0

        # BUY Signal Logic
        if p_up >= self.config.min_ml_confidence:
            if tech_score >= self.config.min_technical_score_buy:
                if not self.config.require_trend_alignment or trend_is_bullish:
                    signal_state = SignalState.BUY
                    signal_reasons.append(
                        f"High ML UP probability ({p_up*100:.1f}%) confirmed by Technical Score ({tech_score:.1f}/100)."
                    )
                else:
                    signal_state = SignalState.HOLD
                    risk_acceptable = False
                    signal_reasons.append("ML predicts UP, but counter-trend filter blocked entry.")
            else:
                signal_state = SignalState.HOLD
                signal_reasons.append(
                    f"ML predicts UP ({p_up*100:.1f}%), but Technical Score ({tech_score:.1f}) is below threshold ({self.config.min_technical_score_buy})."
                )

        # SELL / SHORT Signal Logic (if enabled)
        elif p_down >= self.config.min_ml_confidence and self.config.allow_short:
            if tech_score <= self.config.max_technical_score_sell:
                signal_state = SignalState.SELL
                signal_reasons.append(
                    f"High ML DOWN probability ({p_down*100:.1f}%) confirmed by Bearish Technical Score ({tech_score:.1f}/100)."
                )
            else:
                signal_state = SignalState.HOLD
                signal_reasons.append("ML predicts DOWN, but technical confirmation absent.")
        else:
            signal_state = SignalState.NO_SIGNAL
            signal_reasons.append(f"Probabilities within neutral range (UP: {p_up*100:.1f}%, DOWN: {p_down*100:.1f}%).")

        # Barriers
        tp_price = current_price * (1.0 + self.config.take_profit_pct)
        sl_price = current_price * (1.0 - self.config.stop_loss_pct)

        full_reasoning = " ".join(signal_reasons)
        if reasons:
            full_reasoning += " Factors: " + "; ".join(reasons[:3]) + "."

        return TradingSignal(
            symbol=prediction.symbol,
            timeframe=prediction.timeframe,
            timestamp=prediction.candle_time,
            signal=signal_state.value,
            ml_prediction=prediction.prediction,
            probability_up=p_up,
            probability_down=p_down,
            probability_neutral=p_neutral,
            technical_score=tech_score,
            risk_acceptable=risk_acceptable,
            suggested_entry=round(current_price, 2),
            suggested_take_profit=round(tp_price, 2),
            suggested_stop_loss=round(sl_price, 2),
            reasoning=full_reasoning,
        )
