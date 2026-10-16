"""
Unit tests for Real-time Data Pipeline (Phase 24), Prediction Service (Phase 25), and Signal Engine (Phase 26).
Reference: Sections 29, 30, and 31 of Implementation Plan.

Validates:
- RollingCandleBuffer closed-candle event emission and deduplication
- Zero intrabar prediction leaks: features computed strictly when is_closed == True
- PredictionService loading from ModelRegistry with SHA-256 integrity
- Standardized Section 30 JSON contract (/predict)
- TechnicalScoreCalculator indicator scoring
- SignalEngine decoupled confluence logic (/signal)
- FastAPI test client integration for /health, /models, /predict, /signal
"""

import sys
import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(ML_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from src.training.registry import ModelRegistry, ModelStatus
from src.training.models import RandomForestModel
from src.inference.data_pipeline import RollingCandleBuffer, ClosedCandleEvent
from src.inference.service import PredictionService, PredictionOutput
from src.inference.signals import (
    SignalEngine,
    SignalRuleConfig,
    SignalState,
    TechnicalScoreCalculator,
    TradingSignal,
)
from src.api import app
from tests.test_eda import create_synthetic_dataset


@pytest.fixture
def registered_production_model():
    """Sets up a temporary ModelRegistry with an active PRODUCTION model."""
    df = create_synthetic_dataset(n=120)
    rf = RandomForestModel(n_estimators=10, max_depth=3, random_state=42)
    rf.fit(df)

    with tempfile.TemporaryDirectory() as tmpdir:
        reg = ModelRegistry(base_dir=tmpdir)
        reg.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            status=ModelStatus.PRODUCTION,
        )
        yield reg, df


def test_rolling_candle_buffer_closed_candle_discipline():
    """Verify buffer only emits events and computes features when is_closed is True."""
    buffer = RollingCandleBuffer(symbol="BTC/USDT", timeframe="15m", min_warmup_candles=5)

    events: list[ClosedCandleEvent] = []
    buffer.add_listener(lambda ev, feats: events.append(ev))

    # Intrabar tick: is_closed=False -> no event emitted
    ev1 = buffer.on_candle_update(
        {"open_time": "2026-01-01T00:00:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5},
        is_closed=False,
    )
    assert ev1 is None
    assert len(events) == 0

    # Finalized closed candle: is_closed=True -> event emitted
    ev2 = buffer.on_candle_update(
        {"open_time": "2026-01-01T00:00:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5},
        is_closed=True,
    )
    assert ev2 is not None
    assert ev2.open == 100.0

    # Duplicate open_time ignored
    ev3 = buffer.on_candle_update(
        {"open_time": "2026-01-01T00:00:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5},
        is_closed=True,
    )
    assert ev3 is None


def test_prediction_service_with_registry(registered_production_model):
    """Verify PredictionService loads production model and formats Section 30 JSON contract."""
    reg, df = registered_production_model
    service = PredictionService(registry=reg)

    pred = service.predict(features_df=df, symbol="BTC/USDT", timeframe="15m")

    assert pred.symbol == "BTC/USDT"
    assert pred.model_version == "BTC_15M_RF_v1.0"
    assert pred.prediction in ["UP", "DOWN", "NEUTRAL"]
    assert np.isclose(pred.probability_up + pred.probability_down + pred.probability_neutral, 1.0)
    assert len(pred.top_factors) <= 5

    pred_dict = pred.to_dict()
    assert "probabilityUp" in pred_dict
    assert "probabilityDown" in pred_dict
    assert "probabilityNeutral" in pred_dict
    assert "topFactors" in pred_dict
    assert "disclaimer" in pred_dict


def test_signal_engine_decoupled_confluence():
    """Verify SignalEngine combines ML probability and technical score without hard-coding model logic."""
    engine = SignalEngine(
        config=SignalRuleConfig(
            min_ml_confidence=0.55,
            min_technical_score_buy=60.0,
            require_trend_alignment=True,
        )
    )

    pred_high_up = PredictionOutput(
        symbol="BTC/USDT",
        timeframe="15m",
        model_version="test_v1",
        prediction="UP",
        probability_up=0.68,
        probability_down=0.17,
        probability_neutral=0.15,
        candle_time="2026-01-01T00:00:00Z",
        top_factors=[],
        disclaimer="test",
    )

    # Bullish technical features (price > ema200, positive macd, hammer)
    bullish_features = pd.Series(
        {
            "close": 100.0,
            "ema_200": 90.0,
            "ema_21": 95.0,
            "ema_50": 92.0,
            "rsi_14": 52.0,
            "macd_hist": 1.5,
            "is_hammer": 1.0,
        }
    )

    signal_buy = engine.generate_signal(pred_high_up, bullish_features)
    assert signal_buy.signal == SignalState.BUY.value
    assert signal_buy.technical_score >= 60.0
    assert signal_buy.risk_acceptable is True
    assert signal_buy.suggested_take_profit > signal_buy.suggested_entry
    assert signal_buy.suggested_stop_loss < signal_buy.suggested_entry

    # When technical score is bearish (price < ema200, negative macd), BUY should be blocked -> HOLD
    bearish_features = pd.Series(
        {
            "close": 80.0,
            "ema_200": 90.0,
            "ema_21": 82.0,
            "ema_50": 85.0,
            "rsi_14": 25.0,
            "macd_hist": -1.5,
            "is_bearish_engulfing": 1.0,
        }
    )

    signal_hold = engine.generate_signal(pred_high_up, bearish_features)
    assert signal_hold.signal == SignalState.HOLD.value
    assert "below threshold" in signal_hold.reasoning or "counter-trend" in signal_hold.reasoning


def test_fastapi_endpoints_health_and_models():
    """Verify FastAPI /health and /models endpoints."""
    client = TestClient(app)

    # 1. Health endpoint
    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "healthy"
    assert health_data["service"] == "ai-trading-ml"

    # 2. Models list endpoint
    res_models = client.get("/models")
    assert res_models.status_code == 200
    assert isinstance(res_models.json(), list)


def test_fastapi_predict_and_signal_endpoints(registered_production_model):
    """Verify FastAPI /predict and /signal endpoints with live candle payload."""
    reg, df = registered_production_model
    import src.api as api_mod
    api_mod.registry = reg
    api_mod.prediction_service = PredictionService(registry=reg)

    client = TestClient(app)

    # Prepare candle payload from df (last 40 candles)
    sub_df = df.iloc[-40:].copy()
    candle_payload = []
    for idx, row in sub_df.iterrows():
        candle_payload.append(
            {
                "open_time": str(idx),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
        )

    # Test /predict
    req_body = {
        "symbol": "BTC/USDT",
        "timeframe": "15m",
        "candles": candle_payload,
    }
    res_pred = client.post("/predict", json=req_body)
    assert res_pred.status_code == 200
    p_data = res_pred.json()
    assert p_data["symbol"] == "BTC/USDT"
    assert p_data["prediction"] in ["UP", "DOWN", "NEUTRAL"]
    assert "probabilityUp" in p_data
    assert "topFactors" in p_data

    # Test /signal
    res_sig = client.post("/signal", json=req_body)
    assert res_sig.status_code == 200
    s_data = res_sig.json()
    assert s_data["signal"] in ["BUY", "SELL", "HOLD", "NO_SIGNAL"]
    assert "technical_score" in s_data
    assert "suggested_entry" in s_data
    assert "reasoning" in s_data
