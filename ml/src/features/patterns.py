"""
Deterministic Candlestick Pattern Engine (Phase 7).
Reference: Section 12 of Implementation Plan.
Zero future leakage: Patterns detected at index T strictly use candles <= T.
All patterns are represented as binary features (1 = detected, 0 = absent).
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd


class CandlestickPatternEngine:
    """
    Detects 11 core candlestick reversal and continuation patterns deterministically.
    """

    PATTERN_NAMES: List[str] = [
        "pattern_doji",
        "pattern_hammer",
        "pattern_inverted_hammer",
        "pattern_shooting_star",
        "pattern_hanging_man",
        "pattern_bullish_engulfing",
        "pattern_bearish_engulfing",
        "pattern_morning_star",
        "pattern_evening_star",
        "pattern_harami",
        "pattern_inside_bar",
    ]

    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detects all 11 candlestick patterns across the OHLCV timeseries.
        Returns a DataFrame indexed by open_time with integer binary columns (0 or 1).
        """
        if df.empty or len(df) < 3:
            return pd.DataFrame(0, index=df.index, columns=cls.PATTERN_NAMES)

        data = df.copy()
        if not isinstance(data.index, pd.DatetimeIndex) and "open_time" in data.columns:
            data["open_time"] = pd.to_datetime(data["open_time"], utc=True)
            data.set_index("open_time", inplace=True)
        data.sort_index(inplace=True)

        o = data["open"].astype(float)
        h = data["high"].astype(float)
        l = data["low"].astype(float)
        c = data["close"].astype(float)

        # Candle geometric components
        body_size = (c - o).abs()
        candle_range = (h - l).clip(lower=1e-8)
        body_ratio = body_size / candle_range
        body_top = o.where(o >= c, c)
        body_bottom = o.where(o <= c, c)
        upper_wick = h - body_top
        lower_wick = body_bottom - l

        is_bullish = c > o
        is_bearish = c < o

        patterns = pd.DataFrame(0, index=data.index, columns=cls.PATTERN_NAMES, dtype=int)

        # ------------------------------------------------------------------
        # 1. Doji: Very small body (<= 10% of range) with active wicks
        # ------------------------------------------------------------------
        doji_mask = (body_ratio <= 0.10) & (candle_range > 0)
        patterns["pattern_doji"] = doji_mask.astype(int)

        # ------------------------------------------------------------------
        # 2. Hammer: Small body at top (1%-35%), lower wick >= 2 * body, upper wick <= 10% range
        # ------------------------------------------------------------------
        hammer_mask = (
            (body_ratio > 0.01) & (body_ratio <= 0.35) &
            (lower_wick >= 2.0 * body_size) &
            (upper_wick <= 0.10 * candle_range)
        )
        patterns["pattern_hammer"] = hammer_mask.astype(int)

        # ------------------------------------------------------------------
        # 3. Inverted Hammer: Small body near bottom, upper wick >= 2 * body, lower wick <= 10% range
        # ------------------------------------------------------------------
        inv_hammer_mask = (
            (body_ratio > 0.01) & (body_ratio <= 0.35) &
            (upper_wick >= 2.0 * body_size) &
            (lower_wick <= 0.10 * candle_range)
        )
        patterns["pattern_inverted_hammer"] = inv_hammer_mask.astype(int)

        # ------------------------------------------------------------------
        # 4. Shooting Star: Bearish reversal candle (same geometry as inverted hammer with bearish body)
        # ------------------------------------------------------------------
        shooting_star_mask = inv_hammer_mask & is_bearish
        patterns["pattern_shooting_star"] = shooting_star_mask.astype(int)

        # ------------------------------------------------------------------
        # 5. Hanging Man: Bearish reversal candle at top (same geometry as hammer with bearish body)
        # ------------------------------------------------------------------
        hanging_man_mask = hammer_mask & is_bearish
        patterns["pattern_hanging_man"] = hanging_man_mask.astype(int)

        # ------------------------------------------------------------------
        # 6. Bullish Engulfing: Previous candle bearish, current bullish, current body engulfs previous body
        # ------------------------------------------------------------------
        o_prev = o.shift(1)
        c_prev = c.shift(1)
        prev_bearish = c_prev < o_prev
        bull_engulf = (
            prev_bearish & is_bullish &
            (o <= c_prev) & (c >= o_prev)
        )
        patterns["pattern_bullish_engulfing"] = bull_engulf.fillna(False).astype(int)

        # ------------------------------------------------------------------
        # 7. Bearish Engulfing: Previous candle bullish, current bearish, current body engulfs previous body
        # ------------------------------------------------------------------
        prev_bullish = c_prev > o_prev
        bear_engulf = (
            prev_bullish & is_bearish &
            (o >= c_prev) & (c <= o_prev)
        )
        patterns["pattern_bearish_engulfing"] = bear_engulf.fillna(False).astype(int)

        # ------------------------------------------------------------------
        # 8. Morning Star: 3-candle bullish reversal (long bearish -> small body gap down -> strong bullish)
        # ------------------------------------------------------------------
        o_prev2 = o.shift(2)
        c_prev2 = c.shift(2)
        body_prev2 = (c_prev2 - o_prev2).abs()
        range_prev2 = (h.shift(2) - l.shift(2)).clip(lower=1e-8)

        body_prev1 = body_size.shift(1)
        range_prev1 = candle_range.shift(1)

        first_bearish_long = (c_prev2 < o_prev2) & ((body_prev2 / range_prev2) >= 0.50)
        second_small_star = (body_prev1 / range_prev1) <= 0.35
        third_bullish_strong = is_bullish & (c >= (o_prev2 + c_prev2) / 2.0)

        morning_star = first_bearish_long & second_small_star & third_bullish_strong
        patterns["pattern_morning_star"] = morning_star.fillna(False).astype(int)

        # ------------------------------------------------------------------
        # 9. Evening Star: 3-candle bearish reversal (long bullish -> small body gap up -> strong bearish)
        # ------------------------------------------------------------------
        first_bullish_long = (c_prev2 > o_prev2) & ((body_prev2 / range_prev2) >= 0.50)
        third_bearish_strong = is_bearish & (c <= (o_prev2 + c_prev2) / 2.0)

        evening_star = first_bullish_long & second_small_star & third_bearish_strong
        patterns["pattern_evening_star"] = evening_star.fillna(False).astype(int)

        # ------------------------------------------------------------------
        # 10. Harami: Current body completely inside previous body
        # ------------------------------------------------------------------
        body_max_curr = body_top
        body_min_curr = body_bottom
        body_max_prev = o_prev.where(o_prev >= c_prev, c_prev)
        body_min_prev = o_prev.where(o_prev <= c_prev, c_prev)

        harami_mask = (body_max_curr <= body_max_prev) & (body_min_curr >= body_min_prev) & (body_size < body_prev1)
        patterns["pattern_harami"] = harami_mask.fillna(False).astype(int)

        # ------------------------------------------------------------------
        # 11. Inside Bar: Current high <= previous high and current low >= previous low
        # ------------------------------------------------------------------
        inside_bar_mask = (h <= h.shift(1)) & (l >= l.shift(1))
        patterns["pattern_inside_bar"] = inside_bar_mask.fillna(False).astype(int)

        return patterns

    # Alias for convenience
    detect = detect_patterns
