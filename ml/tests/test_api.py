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

def test_predict_endpoint_with_candles():
    sample_candles = [
        {
            "open_time": "2026-01-01T00:00:00Z",
            "open": 50000,
            "high": 50500,
            "low": 49800,
            "close": 50200,
            "volume": 120.5
        }
    ]
    response = client.post(
        "/predict",
        json={"symbol": "BTC/USDT", "timeframe": "15m", "candles": sample_candles}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["predicted_class"] in ["UP", "DOWN", "NEUTRAL"]
