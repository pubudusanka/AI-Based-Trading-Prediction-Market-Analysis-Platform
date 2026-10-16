"""
Prediction & Inference Service leveraging ModelRegistry and Calibrated Models.
Reference: Section 30 (Phase 25) of Implementation Plan.

Guarantees:
- Strictly loads verified model versions from ModelRegistry with SHA-256 integrity verification.
- Defaults to currently active PRODUCTION model for (symbol, timeframe).
- In-memory model caching to minimize disk I/O latency during real-time inference.
- Multi-class calibrated probabilities strictly summing to 1.0000.
- Inline factor explainability attribution for real-time trader interpretability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.training.registry import ModelRegistry, ModelMetadata
from src.evaluation.explainability import FeatureImportanceEngine, SinglePredictionExplanation


@dataclass
class PredictionOutput:
    """Standardized prediction output payload matching Section 30 API specification."""
    symbol: str
    timeframe: str
    model_version: str
    prediction: str  # "UP", "DOWN", "NEUTRAL"
    probability_up: float
    probability_down: float
    probability_neutral: float
    candle_time: str
    top_factors: List[Dict[str, Any]]
    disclaimer: str
    inferred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "modelVersion": self.model_version,
            "prediction": self.prediction,
            "probabilityUp": round(self.probability_up, 4),
            "probabilityDown": round(self.probability_down, 4),
            "probabilityNeutral": round(self.probability_neutral, 4),
            "candleTime": self.candle_time,
            "topFactors": self.top_factors,
            "disclaimer": self.disclaimer,
            "inferredAt": self.inferred_at,
        }


class PredictionService:
    """
    Production inference engine serving real-time model forecasts.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()
        self._cache: Dict[str, Tuple[Any, ModelMetadata]] = {}

    def get_or_load_model(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        model_version: Optional[str] = None,
    ) -> Tuple[Any, ModelMetadata]:
        """
        Retrieves model from cache or loads from registry with SHA-256 integrity check.
        """
        cache_key = f"{symbol}:{timeframe}:{model_version or 'PRODUCTION'}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if model_version:
            model, metadata = self.registry.load_model(model_version)
        else:
            model, metadata = self.registry.get_production_model(symbol=symbol, timeframe=timeframe)

        self._cache[cache_key] = (model, metadata)
        return model, metadata

    def predict(
        self,
        features_df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        model_version: Optional[str] = None,
        candle_time: Optional[str] = None,
    ) -> PredictionOutput:
        """
        Executes prediction on the latest row of features_df.
        """
        if features_df.empty:
            raise ValueError("features_df cannot be empty for prediction.")

        model, meta = self.get_or_load_model(symbol=symbol, timeframe=timeframe, model_version=model_version)
        latest_row = features_df.iloc[[-1]]

        # Generate probabilities
        prob_df = model.predict_proba(latest_row)
        p_up = float(prob_df["UP"].iloc[0])
        p_down = float(prob_df["DOWN"].iloc[0])
        p_neutral = float(prob_df["NEUTRAL"].iloc[0])

        # Normalize to strictly 1.0000
        total = p_up + p_down + p_neutral
        if total > 0:
            p_up /= total
            p_down /= total
            p_neutral /= total

        # Predicted class
        probs = {"UP": p_up, "DOWN": p_down, "NEUTRAL": p_neutral}
        pred_class = max(probs, key=probs.get)  # type: ignore

        # Inline feature attribution
        try:
            explanation = FeatureImportanceEngine.explain_prediction(
                model=model,
                candle_features=latest_row,
                symbol=symbol,
                timeframe=timeframe,
                top_k=5,
            )
            top_factors = [f.to_dict() for f in explanation.top_factors]
            disclaimer = explanation.disclaimer
        except Exception:
            top_factors = []
            disclaimer = "Statistical association within fitted model."

        time_val = candle_time or str(latest_row.index[-1])

        return PredictionOutput(
            symbol=symbol,
            timeframe=timeframe,
            model_version=meta.model_version,
            prediction=pred_class,
            probability_up=p_up,
            probability_down=p_down,
            probability_neutral=p_neutral,
            candle_time=time_val,
            top_factors=top_factors,
            disclaimer=disclaimer,
        )
