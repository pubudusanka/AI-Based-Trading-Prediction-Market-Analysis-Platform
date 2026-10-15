import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone, timedelta
import pandas as pd
import pytest

from src.preprocessing.quality import DataQualityAuditor

def create_sample_df(count: int = 10, interval_mins: int = 15, drop_indices = None):
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    times = [base_time + timedelta(minutes=i * interval_mins) for i in range(count)]
    
    rows = []
    for t in times:
        rows.append({
            "open_time": t,
            "open": 50000.0,
            "high": 50500.0,
            "low": 49500.0,
            "close": 50200.0,
            "volume": 100.0,
            "quote_volume": 5020000.0,
            "trade_count": 50
        })
    df = pd.DataFrame(rows)
    df.set_index("open_time", inplace=True)
    if drop_indices:
        df = df.drop(df.index[drop_indices])
    return df

def test_quality_audit_clean():
    df = create_sample_df(count=10)
    auditor = DataQualityAuditor()
    report = auditor.audit(df, symbol="BTC/USDT", timeframe="15m")

    assert report.is_clean is True
    assert report.total_candles == 10
    assert report.expected_candles == 10
    assert report.missing_candles == 0
    assert report.duplicate_candles == 0
    assert report.invalid_ohlc_candles == 0
    assert report.coverage_percentage == 100.0
    assert len(report.gaps) == 0

    md = report.generate_markdown()
    assert "CLEAN" in md
    assert "100.00%" in md

def test_quality_audit_with_missing_gaps():
    # Drop 2 candles in the middle (indices 3 and 4)
    df = create_sample_df(count=10, drop_indices=[3, 4])
    auditor = DataQualityAuditor()
    report = auditor.audit(df, symbol="BTC/USDT", timeframe="15m")

    assert report.is_clean is False
    assert report.total_candles == 8
    assert report.expected_candles == 10
    assert report.missing_candles == 2
    assert len(report.gaps) == 1
    assert report.gaps[0].missing_candle_count == 2
    assert report.coverage_percentage == 80.0

def test_quality_audit_with_duplicates():
    df = create_sample_df(count=5)
    # Duplicate first row
    dup_row = df.iloc[[0]]
    df = pd.concat([df, dup_row])
    
    auditor = DataQualityAuditor()
    report = auditor.audit(df, symbol="BTC/USDT", timeframe="15m")

    assert report.duplicate_candles == 1

def test_quality_audit_invalid_ohlc():
    df = create_sample_df(count=5)
    # Corrupt row 1: high lower than close
    df.loc[df.index[1], "high"] = 49000.0

    auditor = DataQualityAuditor()
    report = auditor.audit(df, symbol="BTC/USDT", timeframe="15m")

    assert report.is_clean is False
    assert report.invalid_ohlc_candles == 1

def test_quality_audit_negative_price():
    df = create_sample_df(count=5)
    # Corrupt row 2: negative low
    df.loc[df.index[2], "low"] = -10.0

    auditor = DataQualityAuditor()
    report = auditor.audit(df, symbol="BTC/USDT", timeframe="15m")

    assert report.is_clean is False
    assert report.zero_or_negative_price_candles == 1
