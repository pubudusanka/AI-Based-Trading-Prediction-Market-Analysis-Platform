"""
Target / Label Generation Engine.
Reference: Section 16 (Phase 11) of Implementation Plan.

Generates ground-truth labels for machine learning models:
1. Fixed-Horizon Triple-Barrier Labeling:
   - Evaluates price trajectory across future horizon [T+1, T+N].
   - Target Hit First (+1.0% by default) -> 'UP' (+1)
   - Stop Loss Hit First (-0.5% by default) -> 'DOWN' (-1)
   - Neither Barrier Hit within N candles -> 'NEUTRAL' (0)
2. Intra-Candle Ambiguity Resolution:
   - If both barriers are breached within the exact same candle,
     applies a conservative risk-management policy ("conservative_stop"),
     assuming stop-loss triggers before profit target.
3. Auxiliary Targets & Horizons:
   - Continuous returns: future_return_5, future_return_10, future_return_20
   - Maximum favorable excursion (MFE / max_future_return)
   - Maximum adverse excursion (MAE / min_future_return)
   - Time-to-barrier metrics (candles_to_target, candles_to_stop)
   - Binary direction (1 if future_return_20 > 0 else 0)
4. Data Integrity & Lookahead Prevention:
   - Last N candles cannot complete the full horizon and are cleanly marked
     with `is_target_valid = False` and NaNs.
"""

from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import pandas as pd


class LabelEngine:
    """
    Computes triple-barrier classification labels and forward-looking return metrics.
    """

    LABEL_NAMES = ["UP", "DOWN", "NEUTRAL"]

    def __init__(
        self,
        horizon: int = 20,
        take_profit_pct: float = 0.010,
        stop_loss_pct: float = 0.005,
        same_candle_resolution: str = "conservative_stop",
    ) -> None:
        """
        Args:
            horizon: Future candle window to observe (default 20 candles).
            take_profit_pct: Positive price change required to trigger UP label (default +1.0%).
            stop_loss_pct: Negative price change required to trigger DOWN label (default -0.5%).
            same_candle_resolution: Policy when both barriers are touched in the same bar.
                'conservative_stop': Assume stop-loss hit first (-1).
                'neutral': Treat ambiguous outcome as neutral (0).
        """
        if horizon < 1:
            raise ValueError("horizon must be at least 1 candle")
        if take_profit_pct <= 0:
            raise ValueError("take_profit_pct must be strictly positive")
        if stop_loss_pct <= 0:
            raise ValueError("stop_loss_pct must be strictly positive")
        if same_candle_resolution not in ("conservative_stop", "neutral"):
            raise ValueError(f"Unsupported same_candle_resolution: {same_candle_resolution}")

        self.horizon: int = horizon
        self.tp_pct: float = take_profit_pct
        self.sl_pct: float = stop_loss_pct
        self.resolution: str = same_candle_resolution

    def generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates ground-truth labels for each candle in df.
        Expected columns: ['high', 'low', 'close']
        """
        req_cols = {"high", "low", "close"}
        if not req_cols.issubset(df.columns):
            missing = req_cols - set(df.columns)
            raise ValueError(f"Input DataFrame missing required columns: {missing}")

        n = len(df)
        h = df["high"].to_numpy(dtype=float)
        l = df["low"].to_numpy(dtype=float)
        c = df["close"].to_numpy(dtype=float)

        # Output arrays
        target_tb = np.full(n, np.nan, dtype=float)
        target_name = ["UNLABELLED"] * n
        target_binary = np.full(n, np.nan, dtype=float)

        future_ret_5 = np.full(n, np.nan, dtype=float)
        future_ret_10 = np.full(n, np.nan, dtype=float)
        future_ret_20 = np.full(n, np.nan, dtype=float)

        max_future_ret = np.full(n, np.nan, dtype=float)
        min_future_ret = np.full(n, np.nan, dtype=float)

        candles_to_tp = np.full(n, np.nan, dtype=float)
        candles_to_sl = np.full(n, np.nan, dtype=float)
        is_valid = np.zeros(n, dtype=bool)

        hz = self.horizon

        for i in range(n):
            # Only generate labels if we have a full future horizon [i+1, i+hz]
            if i + hz >= n:
                continue

            entry_price = c[i]
            if entry_price <= 0:
                continue

            tp_price = entry_price * (1.0 + self.tp_pct)
            sl_price = entry_price * (1.0 - self.sl_pct)

            # Slices of future window
            fut_highs = h[i + 1 : i + hz + 1]
            fut_lows = l[i + 1 : i + hz + 1]
            fut_closes = c[i + 1 : i + hz + 1]

            # 1. Auxiliary returns
            if len(fut_closes) >= 5:
                future_ret_5[i] = (fut_closes[4] - entry_price) / entry_price
            if len(fut_closes) >= 10:
                future_ret_10[i] = (fut_closes[9] - entry_price) / entry_price
            if len(fut_closes) >= hz:
                future_ret_20[i] = (fut_closes[hz - 1] - entry_price) / entry_price
                target_binary[i] = 1.0 if future_ret_20[i] > 0 else 0.0

            max_future_ret[i] = (float(fut_highs.max()) - entry_price) / entry_price
            min_future_ret[i] = (float(fut_lows.min()) - entry_price) / entry_price

            # 2. Triple Barrier Evaluation
            tp_step: Optional[int] = None
            sl_step: Optional[int] = None

            for step in range(hz):
                candle_h = fut_highs[step]
                candle_l = fut_lows[step]

                hit_tp = candle_h >= tp_price
                hit_sl = candle_l <= sl_price

                if hit_tp and hit_sl:
                    # Edge case: both barriers hit in the same candle
                    if self.resolution == "conservative_stop":
                        sl_step = step + 1
                        candles_to_sl[i] = float(sl_step)
                        target_tb[i] = -1.0
                        target_name[i] = "DOWN"
                    else:
                        target_tb[i] = 0.0
                        target_name[i] = "NEUTRAL"
                    break

                if hit_tp:
                    tp_step = step + 1
                    candles_to_tp[i] = float(tp_step)
                    target_tb[i] = 1.0
                    target_name[i] = "UP"
                    break

                if hit_sl:
                    sl_step = step + 1
                    candles_to_sl[i] = float(sl_step)
                    target_tb[i] = -1.0
                    target_name[i] = "DOWN"
                    break

            if tp_step is None and sl_step is None:
                # Neither barrier hit within horizon
                target_tb[i] = 0.0
                target_name[i] = "NEUTRAL"

            is_valid[i] = True

        result = pd.DataFrame(
            {
                "target_triple_barrier": target_tb,
                "target_label_name": target_name,
                "target_binary": target_binary,
                "future_return_5": future_ret_5,
                "future_return_10": future_ret_10,
                "future_return_20": future_ret_20,
                "max_future_return": max_future_ret,
                "min_future_return": min_future_ret,
                "candles_to_target": candles_to_tp,
                "candles_to_stop": candles_to_sl,
                "is_target_valid": is_valid,
            },
            index=df.index,
        )

        return result
