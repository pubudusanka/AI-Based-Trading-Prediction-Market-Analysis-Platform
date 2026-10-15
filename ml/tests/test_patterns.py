import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone, timedelta
import pandas as pd
import pytest

from src.features.patterns import CandlestickPatternEngine


def make_df(rows):
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    for i, r in enumerate(rows):
        r["open_time"] = base_time + timedelta(minutes=15 * i)
        if "volume" not in r:
            r["volume"] = 100.0
    df = pd.DataFrame(rows)
    df.set_index("open_time", inplace=True)
    return df


def test_doji_positive_and_negative():
    # Row 0: neutral starter, Row 1: Positive Doji (O=50000, C=50002, H=50100, L=49900), Row 2: Negative (large body)
    df = make_df([
        {"open": 50000, "high": 50100, "low": 49900, "close": 50010},
        {"open": 50000, "high": 50100, "low": 49900, "close": 50002},  # Doji
        {"open": 50000, "high": 50500, "low": 49900, "close": 50480},  # Not Doji
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_doji"].iloc[1] == 1
    assert patterns["pattern_doji"].iloc[2] == 0


def test_hammer_positive_and_negative():
    # Hammer: small body near top, lower wick >= 2 * body, upper wick <= 10%
    df = make_df([
        {"open": 50000, "high": 50100, "low": 49900, "close": 50050},
        {"open": 50450, "high": 50500, "low": 49500, "close": 50480},  # Hammer (body=30, lower_wick=950, upper_wick=20)
        {"open": 50000, "high": 50500, "low": 49900, "close": 50100},  # Inverted (long upper wick, not hammer)
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_hammer"].iloc[1] == 1
    assert patterns["pattern_hammer"].iloc[2] == 0


def test_inverted_hammer_positive_and_negative():
    # Inverted Hammer: small body near bottom, upper wick >= 2 * body, lower wick <= 10%
    df = make_df([
        {"open": 50000, "high": 50100, "low": 49900, "close": 50050},
        {"open": 49550, "high": 50500, "low": 49500, "close": 49580},  # Inverted Hammer (body=30, upper_wick=920, lower_wick=50)
        {"open": 50450, "high": 50500, "low": 49500, "close": 50480},  # Regular Hammer (not inverted)
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_inverted_hammer"].iloc[1] == 1
    assert patterns["pattern_inverted_hammer"].iloc[2] == 0


def test_shooting_star_positive_and_negative():
    # Shooting star: inverted hammer geometry but bearish body (close < open)
    df = make_df([
        {"open": 50000, "high": 50100, "low": 49900, "close": 50050},
        {"open": 49600, "high": 50500, "low": 49500, "close": 49550},  # Shooting star (bearish)
        {"open": 49550, "high": 50500, "low": 49500, "close": 49600},  # Bullish body -> not shooting star
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_shooting_star"].iloc[1] == 1
    assert patterns["pattern_shooting_star"].iloc[2] == 0


def test_hanging_man_positive_and_negative():
    # Hanging man: hammer geometry with bearish body (close < open)
    df = make_df([
        {"open": 50000, "high": 50100, "low": 49900, "close": 50050},
        {"open": 50480, "high": 50500, "low": 49500, "close": 50450},  # Hanging man (bearish body)
        {"open": 50450, "high": 50500, "low": 49500, "close": 50480},  # Bullish body -> hammer, not hanging man
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_hanging_man"].iloc[1] == 1
    assert patterns["pattern_hanging_man"].iloc[2] == 0


def test_bullish_engulfing_positive_and_negative():
    # Candle 0: bearish (O=50000, C=49500)
    # Candle 1: bullish engulfing (O=49400, C=50100) -> completely engulfs Candle 0
    # Candle 2: small bearish (O=50000, C=49900)
    # Candle 3: weak bullish (O=49920, C=49980) -> does not engulf Candle 2
    df = make_df([
        {"open": 50000, "high": 50100, "low": 49400, "close": 49500},
        {"open": 49400, "high": 50200, "low": 49300, "close": 50100},  # Bullish Engulfing
        {"open": 50000, "high": 50100, "low": 49800, "close": 49900},
        {"open": 49920, "high": 50000, "low": 49900, "close": 49980},  # Negative
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_bullish_engulfing"].iloc[1] == 1
    assert patterns["pattern_bullish_engulfing"].iloc[3] == 0


def test_bearish_engulfing_positive_and_negative():
    # Candle 0: bullish (O=49500, C=50000)
    # Candle 1: bearish engulfing (O=50100, C=49400) -> completely engulfs Candle 0
    # Candle 2: weak bearish -> negative
    df = make_df([
        {"open": 49500, "high": 50100, "low": 49400, "close": 50000},
        {"open": 50100, "high": 50200, "low": 49300, "close": 49400},  # Bearish Engulfing
        {"open": 49450, "high": 49500, "low": 49400, "close": 49420},  # Negative
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_bearish_engulfing"].iloc[1] == 1
    assert patterns["pattern_bearish_engulfing"].iloc[2] == 0


def test_morning_star_positive_and_negative():
    # 3-candle: C0 long bearish -> C1 small star -> C2 strong bullish (>50% of C0)
    df = make_df([
        {"open": 51000, "high": 51100, "low": 49900, "close": 50000},  # Long bearish
        {"open": 49800, "high": 49850, "low": 49700, "close": 49750},  # Small star
        {"open": 49800, "high": 50800, "low": 49750, "close": 50700},  # Strong bullish (> 50500 midpoint) -> Morning star
        {"open": 50700, "high": 50800, "low": 50600, "close": 50650},  # Negative
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_morning_star"].iloc[2] == 1
    assert patterns["pattern_morning_star"].iloc[3] == 0


def test_evening_star_positive_and_negative():
    # 3-candle: C0 long bullish -> C1 small star -> C2 strong bearish (<50% of C0)
    df = make_df([
        {"open": 50000, "high": 51100, "low": 49900, "close": 51000},  # Long bullish
        {"open": 51200, "high": 51250, "low": 51150, "close": 51200},  # Small star
        {"open": 51100, "high": 51150, "low": 50200, "close": 50300},  # Strong bearish (< 50500 midpoint) -> Evening star
        {"open": 50300, "high": 50400, "low": 50200, "close": 50350},  # Negative
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_evening_star"].iloc[2] == 1
    assert patterns["pattern_evening_star"].iloc[3] == 0


def test_harami_positive_and_negative():
    # Harami: current body completely inside previous body
    df = make_df([
        {"open": 50000, "high": 51200, "low": 49800, "close": 51000},  # Large body [50000, 51000]
        {"open": 50300, "high": 50800, "low": 50200, "close": 50700},  # Body [50300, 50700] inside -> Harami
        {"open": 50200, "high": 52000, "low": 49000, "close": 51800},  # Body larger -> Not Harami
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_harami"].iloc[1] == 1
    assert patterns["pattern_harami"].iloc[2] == 0


def test_inside_bar_positive_and_negative():
    # Inside bar: current high <= prev high and current low >= prev low
    df = make_df([
        {"open": 50000, "high": 51500, "low": 49500, "close": 51000},
        {"open": 50200, "high": 51000, "low": 50000, "close": 50800},  # Inside bar
        {"open": 50800, "high": 52000, "low": 49900, "close": 51200},  # High exceeds prev high -> Not inside bar
    ])
    patterns = CandlestickPatternEngine.detect_patterns(df)
    assert patterns["pattern_inside_bar"].iloc[1] == 1
    assert patterns["pattern_inside_bar"].iloc[2] == 0
