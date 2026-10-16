import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-trading-ml"

def test_predict_endpoint_empty():
    response = client.post("/predict", json={"symbol": "BTC/USDT", "timeframe": "15m", "candles": []})
    assert response.status_code == 400

from unittest.mock import patch
from src.inference.service import PredictionOutput

def test_predict_endpoint_with_candles():
    sample_candles = [
        {
            "open_time": f"2026-01-01T{i//4:02d}:{(i%4)*15:02d}:00Z",
            "open": 50000 + i * 10,
            "high": 50100 + i * 10,
            "low": 49900 + i * 10,
            "close": 50050 + i * 10,
            "volume": 100.0 + i,
        }
        for i in range(35)
    ]
    mock_out = PredictionOutput(
        symbol="BTC/USDT",
        timeframe="15m",
        model_version="BTC_15M_TEST_v1",
        prediction="UP",
        probability_up=0.72,
        probability_down=0.18,
        probability_neutral=0.10,
        candle_time="2026-01-01T08:30:00Z",
        top_factors=[],
        disclaimer="AI-generated trading prediction; not financial advice.",
    )
    with patch("src.api.prediction_service.predict", return_value=mock_out):
        response = client.post(
            "/predict",
            json={"symbol": "BTC/USDT", "timeframe": "15m", "candles": sample_candles}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["prediction"] == "UP"
        assert data["probabilityUp"] == 0.72

def test_predict_endpoint_no_model():
    sample_candles = [
        {
            "open_time": f"2026-01-01T{i//4:02d}:{(i%4)*15:02d}:00Z",
            "open": 50000 + i * 10,
            "high": 50100 + i * 10,
            "low": 49900 + i * 10,
            "close": 50050 + i * 10,
            "volume": 100.0 + i,
        }
        for i in range(35)
    ]
    response = client.post(
        "/predict",
        json={"symbol": "NONEXISTENT/USDT", "timeframe": "15m", "candles": sample_candles}
    )
    assert response.status_code == 404
