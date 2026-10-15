import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest

from src.ingestion.collector import Candle, BinanceMarketDataClient


def test_candle_valid():
    now = datetime.now(timezone.utc)
    c = Candle(
        symbol="BTC/USDT",
        exchange="BINANCE",
        timeframe="15m",
        open_time=now,
        close_time=now + timedelta(minutes=15),
        open=50000.0,
        high=51000.0,
        low=49500.0,
        close=50500.0,
        volume=10.5,
        quote_volume=527000.0,
        trade_count=150
    )
    is_valid, err = c.validate()
    assert is_valid is True
    assert err is None


def test_candle_invalid_high():
    now = datetime.now(timezone.utc)
    # High lower than close
    c = Candle(
        symbol="BTC/USDT",
        exchange="BINANCE",
        timeframe="15m",
        open_time=now,
        close_time=now + timedelta(minutes=15),
        open=50000.0,
        high=50200.0,
        low=49500.0,
        close=50500.0,
        volume=10.5,
        quote_volume=527000.0,
        trade_count=150
    )
    is_valid, err = c.validate()
    assert is_valid is False
    assert err is not None and "high" in err


def test_candle_invalid_low():
    now = datetime.now(timezone.utc)
    # Low higher than open
    c = Candle(
        symbol="BTC/USDT",
        exchange="BINANCE",
        timeframe="15m",
        open_time=now,
        close_time=now + timedelta(minutes=15),
        open=50000.0,
        high=51000.0,
        low=50100.0,
        close=50500.0,
        volume=10.5,
        quote_volume=527000.0,
        trade_count=150
    )
    is_valid, err = c.validate()
    assert is_valid is False
    assert err is not None and "low" in err


def test_candle_invalid_volume():
    now = datetime.now(timezone.utc)
    c = Candle(
        symbol="BTC/USDT",
        exchange="BINANCE",
        timeframe="15m",
        open_time=now,
        close_time=now + timedelta(minutes=15),
        open=50000.0,
        high=51000.0,
        low=49000.0,
        close=50500.0,
        volume=-1.0,
        quote_volume=0.0,
        trade_count=10
    )
    is_valid, err = c.validate()
    assert is_valid is False
    assert err is not None and "volume" in err


def test_binance_client_mock_fetch():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        [1700000000000, "60000.0", "60500.0", "59800.0", "60200.0", "25.5", 1700000899999, "1530000.0", 300]
    ]
    mock_session.get.return_value = mock_response

    client = BinanceMarketDataClient(session=mock_session)
    candles = client.fetch_klines(symbol="BTC/USDT", interval="15m", limit=1)

    assert len(candles) == 1
    assert candles[0].symbol == "BTC/USDT"
    assert candles[0].close == 60200.0
    assert candles[0].trade_count == 300

    df = BinanceMarketDataClient.to_dataframe(candles)
    assert not df.empty
    assert len(df) == 1
    assert "close" in df.columns
