"""
Market Structure Feature Engine.
Reference: Section 13 (Phase 8) of Implementation Plan.

Detects:
- Swing Highs & Swing Lows (with strictly causal K-candle confirmation lag)
- Structural classifications: Higher High (HH), Lower High (LH), Higher Low (HL), Lower Low (LL)
- Real-time Trend Direction (+1 uptrend, -1 downtrend, 0 sideways)
- Dynamic Support and Resistance levels with relative distance metrics
- Break of Structure (BOS) & Breakouts
- Retests of broken key levels

Guarantees:
- ZERO future lookahead bias: A swing high/low occurring at index t is ONLY
  confirmed and available to features at candle t + K.
"""

from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd


class MarketStructureEngine:
    """
    Computes market structure, swing points, trend regime, support/resistance,
    and break-of-structure features from OHLCV candles without lookahead bias.
    """

    FEATURE_NAMES = [
        "is_swing_high",
        "is_swing_low",
        "active_swing_high_price",
        "active_swing_low_price",
        "is_higher_high",
        "is_lower_high",
        "is_higher_low",
        "is_lower_low",
        "trend_direction",
        "support_price",
        "resistance_price",
        "dist_to_support",
        "dist_to_resistance",
        "is_breakout_high",
        "is_breakout_low",
        "is_break_of_structure",
        "is_retest_support",
        "is_retest_resistance",
    ]

    def __init__(self, k_confirmation: int = 3, retest_tolerance_pct: float = 0.003, retest_window: int = 10) -> None:
        """
        Args:
            k_confirmation: Number of confirmation candles required on each side
                to validate a swing point. (A swing at t is confirmed at t + K).
            retest_tolerance_pct: Percentage tolerance around broken level for retest detection (default 0.3%).
            retest_window: Maximum number of candles after breakout to monitor for a retest.
        """
        if k_confirmation < 1:
            raise ValueError("k_confirmation must be at least 1")
        self.k: int = k_confirmation
        self.tolerance: float = retest_tolerance_pct
        self.retest_window: int = retest_window

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates all market structure features for the given DataFrame.
        Expected columns: 'high', 'low', 'close', optionally 'open'.
        """
        req_cols = {"high", "low", "close"}
        if not req_cols.issubset(df.columns):
            missing = req_cols - set(df.columns)
            raise ValueError(f"Input DataFrame missing required columns: {missing}")

        n = len(df)
        if n == 0:
            return pd.DataFrame(columns=self.FEATURE_NAMES, index=df.index)

        h = df["high"].to_numpy(dtype=float)
        l = df["low"].to_numpy(dtype=float)
        c = df["close"].to_numpy(dtype=float)

        # Output feature arrays
        is_swing_high = np.zeros(n, dtype=int)
        is_swing_low = np.zeros(n, dtype=int)
        active_sh_price = np.full(n, np.nan, dtype=float)
        active_sl_price = np.full(n, np.nan, dtype=float)

        is_hh = np.zeros(n, dtype=int)
        is_lh = np.zeros(n, dtype=int)
        is_hl = np.zeros(n, dtype=int)
        is_ll = np.zeros(n, dtype=int)

        trend_dir = np.zeros(n, dtype=int)
        support_price = np.full(n, np.nan, dtype=float)
        resistance_price = np.full(n, np.nan, dtype=float)

        dist_to_support = np.zeros(n, dtype=float)
        dist_to_resistance = np.zeros(n, dtype=float)

        is_breakout_high = np.zeros(n, dtype=int)
        is_breakout_low = np.zeros(n, dtype=int)
        is_bos = np.zeros(n, dtype=int)

        is_retest_sup = np.zeros(n, dtype=int)
        is_retest_res = np.zeros(n, dtype=int)

        k = self.k

        # Tracking state for sequential causal processing
        prev_sh_price: Optional[float] = None
        current_sh_price: Optional[float] = None

        prev_sl_price: Optional[float] = None
        current_sl_price: Optional[float] = None

        last_hh_hl_trend: int = 0  # +1 uptrend, -1 downtrend, 0 neutral

        # Retest tracking states:
        # broken_level, broken_index, type: 'bullish' (resistance broken, now potential support) or 'bearish'
        last_broken_res_level: Optional[float] = None
        last_broken_res_idx: int = -999

        last_broken_sup_level: Optional[float] = None
        last_broken_sup_idx: int = -999

        for i in range(n):
            # 1. Check if a swing high occurred at candle t = i - k and is confirmed at i
            t = i - k
            if t >= k:
                # Candidate index t
                cand_h = h[t]
                # Left check: h[t] >= h[t-k : t]
                left_high_valid = bool(np.all(cand_h >= h[t - k : t]))
                # Right check: h[t] > h[t+1 : t+k+1] (which is h[t+1 : i+1])
                right_high_valid = bool(np.all(cand_h > h[t + 1 : i + 1]))

                if left_high_valid and right_high_valid:
                    is_swing_high[i] = 1
                    if current_sh_price is not None:
                        prev_sh_price = current_sh_price
                        if cand_h > current_sh_price:
                            is_hh[i] = 1
                        elif cand_h < current_sh_price:
                            is_lh[i] = 1
                    current_sh_price = cand_h

                # Candidate index t for swing low
                cand_l = l[t]
                # Left check: l[t] <= l[t-k : t]
                left_low_valid = bool(np.all(cand_l <= l[t - k : t]))
                # Right check: l[t] < l[t+1 : i+1]
                right_low_valid = bool(np.all(cand_l < l[t + 1 : i + 1]))

                if left_low_valid and right_low_valid:
                    is_swing_low[i] = 1
                    if current_sl_price is not None:
                        prev_sl_price = current_sl_price
                        if cand_l > current_sl_price:
                            is_hl[i] = 1
                        elif cand_l < current_sl_price:
                            is_ll[i] = 1
                    current_sl_price = cand_l

            # 2. Update active levels
            if current_sh_price is not None:
                active_sh_price[i] = current_sh_price
                resistance_price[i] = current_sh_price
            if current_sl_price is not None:
                active_sl_price[i] = current_sl_price
                support_price[i] = current_sl_price

            # 3. Update trend direction
            # If we recently made an HH or HL, bias up; if LH or LL, bias down
            if is_hh[i] == 1 or is_hl[i] == 1:
                last_hh_hl_trend = 1
            elif is_lh[i] == 1 or is_ll[i] == 1:
                last_hh_hl_trend = -1
            trend_dir[i] = last_hh_hl_trend

            # 4. Support / Resistance Distances
            curr_c = c[i]
            if current_sl_price is not None and curr_c > 0:
                dist_to_support[i] = (curr_c - current_sl_price) / curr_c
            if current_sh_price is not None and curr_c > 0:
                dist_to_resistance[i] = (current_sh_price - curr_c) / curr_c

            # 5. Breakout / Break of Structure (BOS)
            # Breakout occurs if current candle closes beyond active resistance/support established BEFORE this candle
            # (i.e. if prior candle had an active resistance and current close breaks above it)
            if i > 0:
                prior_res = active_sh_price[i - 1]
                prior_sup = active_sl_price[i - 1]

                if not np.isnan(prior_res) and curr_c > prior_res and c[i - 1] <= prior_res:
                    is_breakout_high[i] = 1
                    is_bos[i] = 1
                    last_broken_res_level = prior_res
                    last_broken_res_idx = i

                if not np.isnan(prior_sup) and curr_c < prior_sup and c[i - 1] >= prior_sup:
                    is_breakout_low[i] = 1
                    is_bos[i] = -1
                    last_broken_sup_level = prior_sup
                    last_broken_sup_idx = i

            # 6. Retest Detection
            # Bullish retest: price broke resistance upwards recently, now pulls back and tests that level as support
            if last_broken_res_level is not None:
                bars_since_break = i - last_broken_res_idx
                if 1 <= bars_since_break <= self.retest_window:
                    curr_l = l[i]
                    # Retest if low comes within tolerance of the broken level and close holds above or near it
                    lower_bound = last_broken_res_level * (1.0 - self.tolerance)
                    upper_bound = last_broken_res_level * (1.0 + self.tolerance)
                    if lower_bound <= curr_l <= upper_bound and curr_c >= lower_bound:
                        is_retest_sup[i] = 1
                        last_broken_res_level = None  # Consume retest to avoid double-counting

            # Bearish retest: price broke support downwards recently, now rallies and tests that level as resistance
            if last_broken_sup_level is not None:
                bars_since_break = i - last_broken_sup_idx
                if 1 <= bars_since_break <= self.retest_window:
                    curr_h = h[i]
                    lower_bound = last_broken_sup_level * (1.0 - self.tolerance)
                    upper_bound = last_broken_sup_level * (1.0 + self.tolerance)
                    if lower_bound <= curr_h <= upper_bound and curr_c <= upper_bound:
                        is_retest_res[i] = 1
                        last_broken_sup_level = None  # Consume retest

        result = pd.DataFrame(
            {
                "is_swing_high": is_swing_high,
                "is_swing_low": is_swing_low,
                "active_swing_high_price": active_sh_price,
                "active_swing_low_price": active_sl_price,
                "is_higher_high": is_hh,
                "is_lower_high": is_lh,
                "is_higher_low": is_hl,
                "is_lower_low": is_ll,
                "trend_direction": trend_dir,
                "support_price": support_price,
                "resistance_price": resistance_price,
                "dist_to_support": dist_to_support,
                "dist_to_resistance": dist_to_resistance,
                "is_breakout_high": is_breakout_high,
                "is_breakout_low": is_breakout_low,
                "is_break_of_structure": is_bos,
                "is_retest_support": is_retest_sup,
                "is_retest_resistance": is_retest_res,
            },
            index=df.index,
        )

        return result
