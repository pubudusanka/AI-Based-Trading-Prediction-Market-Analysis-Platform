"""
Fibonacci Feature Engine.
Reference: Section 14 (Phase 9) of Implementation Plan.

Calculates Fibonacci retracement and proximity features anchored to active,
confirmed swing points without lookahead bias.

Swing Selection Algorithm:
1. Anchored dynamically to the most recent confirmed swing high and swing low from MarketStructureEngine.
2. Impulse Direction:
   - If the confirmed swing high occurred after the confirmed swing low, the impulse move was Low -> High.
     Retracement is calculated downward from High towards Low.
   - If the confirmed swing low occurred after the confirmed swing high, the impulse move was High -> Low.
     Retracement is calculated upward from Low towards High.
3. Fibonacci Levels:
   - 0.236, 0.382, 0.500, 0.618, 0.786, 1.000
4. Distance & Proximity Metrics:
   - distance_to_X: Normalized relative distance `(close - fib_X) / close`
   - near_618: Binary flag indicating close is within `near_threshold_pct` (default 0.3%) of 0.618 level
   - near_382: Binary flag indicating close is within `near_threshold_pct` of 0.382 level
"""

from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

from .structure import MarketStructureEngine


class FibonacciEngine:
    """
    Computes strictly causal Fibonacci retracement levels and proximity features.
    """

    FEATURE_NAMES = [
        "fib_level_236",
        "fib_level_382",
        "fib_level_500",
        "fib_level_618",
        "fib_level_786",
        "fib_level_1000",
        "distance_to_236",
        "distance_to_382",
        "distance_to_500",
        "distance_to_618",
        "distance_to_786",
        "near_618",
        "near_382",
        "fib_swing_range",
        "fib_impulse_direction",
    ]

    FIB_RATIOS = [0.236, 0.382, 0.500, 0.618, 0.786, 1.000]

    def __init__(
        self,
        k_confirmation: int = 3,
        near_threshold_pct: float = 0.003,
    ) -> None:
        """
        Args:
            k_confirmation: Confirmation window for underlying swing points.
            near_threshold_pct: Percentage buffer to trigger near_618 / near_382 flags (default 0.3%).
        """
        self.k: int = k_confirmation
        self.near_threshold: float = near_threshold_pct
        self.structure_engine = MarketStructureEngine(k_confirmation=k_confirmation)

    def compute(
        self,
        df: pd.DataFrame,
        structure_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Computes Fibonacci features for the given market candles.
        
        Args:
            df: OHLCV DataFrame with at least ['high', 'low', 'close'].
            structure_df: Optional pre-computed market structure DataFrame.
        """
        req_cols = {"high", "low", "close"}
        if not req_cols.issubset(df.columns):
            missing = req_cols - set(df.columns)
            raise ValueError(f"Input DataFrame missing required columns: {missing}")

        n = len(df)
        if n == 0:
            return pd.DataFrame(columns=self.FEATURE_NAMES, index=df.index)

        if structure_df is None:
            structure_df = self.structure_engine.compute(df)

        close = df["close"].to_numpy(dtype=float)

        is_sh = structure_df["is_swing_high"].to_numpy(dtype=int)
        is_sl = structure_df["is_swing_low"].to_numpy(dtype=int)
        active_sh = structure_df["active_swing_high_price"].to_numpy(dtype=float)
        active_sl = structure_df["active_swing_low_price"].to_numpy(dtype=float)

        # Output feature arrays
        fib_236 = np.full(n, np.nan, dtype=float)
        fib_382 = np.full(n, np.nan, dtype=float)
        fib_500 = np.full(n, np.nan, dtype=float)
        fib_618 = np.full(n, np.nan, dtype=float)
        fib_786 = np.full(n, np.nan, dtype=float)
        fib_1000 = np.full(n, np.nan, dtype=float)

        dist_236 = np.zeros(n, dtype=float)
        dist_382 = np.zeros(n, dtype=float)
        dist_500 = np.zeros(n, dtype=float)
        dist_618 = np.zeros(n, dtype=float)
        dist_786 = np.zeros(n, dtype=float)

        near_618 = np.zeros(n, dtype=int)
        near_382 = np.zeros(n, dtype=int)

        fib_range = np.zeros(n, dtype=float)
        fib_impulse = np.zeros(n, dtype=int)

        last_sh_idx: int = -1
        last_sl_idx: int = -1

        for i in range(n):
            if is_sh[i] == 1:
                last_sh_idx = i
            if is_sl[i] == 1:
                last_sl_idx = i

            sh_price = active_sh[i]
            sl_price = active_sl[i]

            # We need both an active confirmed swing high and an active confirmed swing low
            if not np.isnan(sh_price) and not np.isnan(sl_price) and sh_price > sl_price:
                swing_diff = sh_price - sl_price
                fib_range[i] = swing_diff
                curr_c = close[i]

                # Determine impulse direction:
                # If swing high was confirmed more recently or at same time -> Low-to-High impulse (+1)
                # If swing low was confirmed more recently -> High-to-Low impulse (-1)
                if last_sh_idx >= last_sl_idx:
                    # Upward impulse: Low -> High
                    # Retracement falls from sh_price downward
                    impulse_dir = 1
                    f236 = sh_price - 0.236 * swing_diff
                    f382 = sh_price - 0.382 * swing_diff
                    f500 = sh_price - 0.500 * swing_diff
                    f618 = sh_price - 0.618 * swing_diff
                    f786 = sh_price - 0.786 * swing_diff
                    f1000 = sl_price
                else:
                    # Downward impulse: High -> Low
                    # Retracement bounces from sl_price upward
                    impulse_dir = -1
                    f236 = sl_price + 0.236 * swing_diff
                    f382 = sl_price + 0.382 * swing_diff
                    f500 = sl_price + 0.500 * swing_diff
                    f618 = sl_price + 0.618 * swing_diff
                    f786 = sl_price + 0.786 * swing_diff
                    f1000 = sh_price

                fib_impulse[i] = impulse_dir
                fib_236[i] = f236
                fib_382[i] = f382
                fib_500[i] = f500
                fib_618[i] = f618
                fib_786[i] = f786
                fib_1000[i] = f1000

                if curr_c > 0:
                    d236 = (curr_c - f236) / curr_c
                    d382 = (curr_c - f382) / curr_c
                    d500 = (curr_c - f500) / curr_c
                    d618 = (curr_c - f618) / curr_c
                    d786 = (curr_c - f786) / curr_c

                    dist_236[i] = d236
                    dist_382[i] = d382
                    dist_500[i] = d500
                    dist_618[i] = d618
                    dist_786[i] = d786

                    if abs(d618) <= self.near_threshold:
                        near_618[i] = 1
                    if abs(d382) <= self.near_threshold:
                        near_382[i] = 1

        result = pd.DataFrame(
            {
                "fib_level_236": fib_236,
                "fib_level_382": fib_382,
                "fib_level_500": fib_500,
                "fib_level_618": fib_618,
                "fib_level_786": fib_786,
                "fib_level_1000": fib_1000,
                "distance_to_236": dist_236,
                "distance_to_382": dist_382,
                "distance_to_500": dist_500,
                "distance_to_618": dist_618,
                "distance_to_786": dist_786,
                "near_618": near_618,
                "near_382": near_382,
                "fib_swing_range": fib_range,
                "fib_impulse_direction": fib_impulse,
            },
            index=df.index,
        )

        return result
