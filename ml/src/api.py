"""
FastAPI Prediction & Signal Service for Real-Time Inference.
Reference: Section 30 (Phase 25) & Section 31 (Phase 26) of Implementation Plan.

Endpoints:
- GET  /health: System status, active production models, and registry health.
- GET  /models: Discover registered models and lifecycle statuses.
- POST /predict: Production inference returning calibrated probabilities & top factors.
- POST /signal: Multi-confluence trading signal generation (ML + Technical Score + Risk Rules).
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd

from src.training.registry import ModelRegistry, ModelStatus
from src.features.dataset import FeatureDatasetBuilder
from src.inference.service import PredictionService, PredictionOutput
from src.inference.signals import SignalEngine, SignalRuleConfig, TradingSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_service")

app = FastAPI(
    title="AI Trading Prediction & Signal Engine Service",
    version="1.0.0",
    description="Probabilistic trading predictions, technical confluence, and signal generation",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
registry = ModelRegistry()
prediction_service = PredictionService(registry=registry)
signal_engine = SignalEngine(config=SignalRuleConfig())
feature_builder = FeatureDatasetBuilder(k_confirmation=2)


class HealthResponse(BaseModel):
    status: str
    service: str
    active_production_models: List[Dict[str, str]]
    total_registered_models: int


class CandleInput(BaseModel):
    open_time: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: Optional[str] = None


class PredictionRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    candles: List[CandleInput]
    modelVersion: Optional[str] = None


class SignalRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "15m"
    candles: List[CandleInput]
    modelVersion: Optional[str] = None
    minConfidence: Optional[float] = 0.55
    minTechnicalScore: Optional[float] = 60.0
    allowShort: Optional[bool] = False


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Returns service health and active production model metadata."""
    prod_models = registry.list_models(status=ModelStatus.PRODUCTION)
    all_models = registry.list_models()

    active_list = [
        {"symbol": m.symbol, "timeframe": m.timeframe, "version": m.model_version}
        for m in prod_models
    ]

    return HealthResponse(
        status="healthy",
        service="ai-trading-ml",
        active_production_models=active_list,
        total_registered_models=len(all_models),
    )


@app.get("/models")
def list_models(
    symbol: Optional[str] = Query(None, description="Filter by asset symbol (e.g. BTC/USDT)"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe (e.g. 15m)"),
    status: Optional[str] = Query(None, description="Filter by lifecycle status (EXPERIMENTAL, VALIDATED, STAGING, PRODUCTION, RETIRED)"),
):
    """Returns list of registered models matching filter criteria."""
    models = registry.list_models(symbol=symbol, timeframe=timeframe, status=status)
    return [m.to_dict() for m in models]


def _build_features_from_candles(candles: List[CandleInput], symbol: str, timeframe: str) -> pd.DataFrame:
    """Helper to convert CandleInput list into feature DataFrame."""
    if len(candles) < 30:
        raise HTTPException(
            status_code=400,
            detail=f"At least 30 candles are required for technical indicator warmup, received {len(candles)}",
        )

    raw_records = [c.model_dump() for c in candles]
    df = pd.DataFrame(raw_records)
    try:
        df.index = pd.to_datetime(df["open_time"], utc=True)
    except Exception:
        df.index = pd.RangeIndex(len(df))

    ohlcv_sub = pd.DataFrame(df[["open", "high", "low", "close", "volume"]])
    feat_dataset = feature_builder.build(ohlcv_sub, symbol=symbol, timeframe=timeframe)
    return pd.DataFrame(feat_dataset.data)


@app.post("/predict")
def predict_endpoint(request: PredictionRequest):
    """
    Executes real-time probabilistic prediction for the latest candle.
    Section 30 API Contract.
    """
    try:
        features_df = _build_features_from_candles(request.candles, request.symbol, request.timeframe)
        output = prediction_service.predict(
            features_df=features_df,
            symbol=request.symbol,
            timeframe=request.timeframe,
            model_version=request.modelVersion,
        )
        return output.to_dict()
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signal")
def signal_endpoint(request: SignalRequest):
    """
    Generates multi-confluence trading signal combining ML prediction, technical score, and risk filters.
    Section 31 API Contract.
    """
    try:
        features_df = _build_features_from_candles(request.candles, request.symbol, request.timeframe)
        pred_output = prediction_service.predict(
            features_df=features_df,
            symbol=request.symbol,
            timeframe=request.timeframe,
            model_version=request.modelVersion,
        )

        cfg = SignalRuleConfig(
            min_ml_confidence=request.minConfidence or 0.55,
            min_technical_score_buy=request.minTechnicalScore or 60.0,
            allow_short=request.allowShort or False,
        )
        custom_engine = SignalEngine(config=cfg)

        latest_features = features_df.iloc[-1]
        signal = custom_engine.generate_signal(pred_output, latest_features)
        return signal.to_dict()
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Signal generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
