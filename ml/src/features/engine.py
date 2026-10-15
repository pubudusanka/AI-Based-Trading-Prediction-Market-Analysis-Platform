"""
Versioned Feature Engineering Engine (V1.0).
Reference: Section 11 (Phase 6) of Implementation Plan.
Strict zero-lookahead bias guarantee: features at time T strictly depend only on observations <= T.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    group: str
    formula: str
    window: int
    input_columns: List[str]
    output_type: str
    missing_value_behavior: str
    leakage_risk: str = "Zero: strictly backwards-looking (<= T)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "group": self.group,
            "formula": self.formula,
            "window": self.window,
            "input_columns": self.input_columns,
            "output_type": self.output_type,
            "missing_value_behavior": self.missing_value_behavior,
            "leakage_risk": self.leakage_risk,
        }


FEATURE_CATALOG_V1: List[FeatureDefinition] = [
    # A. Price Features
    FeatureDefinition("returns", "Price", "(C_t - C_{t-1}) / C_{t-1}", 1, ["close"], "float", "NaN for first row"),
    FeatureDefinition("log_returns", "Price", "ln(C_t / C_{t-1})", 1, ["close"], "float", "NaN for first row"),
    FeatureDefinition("percentage_change", "Price", "returns * 100", 1, ["close"], "float", "NaN for first row"),

    # B. Candle Features
    FeatureDefinition("body_size", "Candle", "|C_t - O_t|", 1, ["open", "close"], "float", "Always valid"),
    FeatureDefinition("body_percentage", "Candle", "body_size / (H_t - L_t)", 1, ["open", "high", "low", "close"], "float", "0.0 if H == L"),
    FeatureDefinition("upper_wick", "Candle", "H_t - max(O_t, C_t)", 1, ["open", "high", "close"], "float", "Always valid"),
    FeatureDefinition("lower_wick", "Candle", "min(O_t, C_t) - L_t", 1, ["open", "low", "close"], "float", "Always valid"),
    FeatureDefinition("candle_range", "Candle", "H_t - L_t", 1, ["high", "low"], "float", "Always valid"),
    FeatureDefinition("body_to_range_ratio", "Candle", "body_size / candle_range", 1, ["open", "high", "low", "close"], "float", "0.0 if range == 0"),
    FeatureDefinition("bullish_flag", "Candle", "1 if C_t > O_t else 0", 1, ["open", "close"], "int", "Binary indicator"),
    FeatureDefinition("bearish_flag", "Candle", "1 if C_t < O_t else 0", 1, ["open", "close"], "int", "Binary indicator"),

    # C. Moving Averages
    FeatureDefinition("sma_20", "Moving Average", "SMA(close, 20)", 20, ["close"], "float", "NaN for t < 20"),
    FeatureDefinition("sma_50", "Moving Average", "SMA(close, 50)", 50, ["close"], "float", "NaN for t < 50"),
    FeatureDefinition("sma_200", "Moving Average", "SMA(close, 200)", 200, ["close"], "float", "NaN for t < 200"),
    FeatureDefinition("ema_9", "Moving Average", "EMA(close, 9)", 9, ["close"], "float", "Standard exponential smoothing"),
    FeatureDefinition("ema_21", "Moving Average", "EMA(close, 21)", 21, ["close"], "float", "Standard exponential smoothing"),
    FeatureDefinition("ema_50", "Moving Average", "EMA(close, 50)", 50, ["close"], "float", "Standard exponential smoothing"),
    FeatureDefinition("ema_200", "Moving Average", "EMA(close, 200)", 200, ["close"], "float", "Standard exponential smoothing"),

    # D. Momentum
    FeatureDefinition("rsi_14", "Momentum", "RSI(close, 14) via Wilder smoothing", 14, ["close"], "float", "NaN for t < 14"),
    FeatureDefinition("macd", "Momentum", "EMA_12 - EMA_26", 26, ["close"], "float", "NaN for t < 26"),
    FeatureDefinition("macd_signal", "Momentum", "EMA_9(MACD)", 34, ["close"], "float", "NaN for t < 34"),
    FeatureDefinition("macd_hist", "Momentum", "MACD - MACD_signal", 34, ["close"], "float", "NaN for t < 34"),
    FeatureDefinition("stoch_k", "Momentum", "((C - L_14) / (H_14 - L_14)) * 100", 14, ["high", "low", "close"], "float", "NaN for t < 14"),
    FeatureDefinition("stoch_d", "Momentum", "SMA_3(stoch_k)", 16, ["high", "low", "close"], "float", "NaN for t < 16"),
    FeatureDefinition("roc_10", "Momentum", "((C_t - C_{t-10}) / C_{t-10}) * 100", 10, ["close"], "float", "NaN for t < 10"),

    # E. Volatility
    FeatureDefinition("atr_14", "Volatility", "Wilder average of True Range", 14, ["high", "low", "close"], "float", "NaN for t < 14"),
    FeatureDefinition("bb_width_20", "Volatility", "(BB_upper - BB_lower) / BB_mid", 20, ["close"], "float", "NaN for t < 20"),
    FeatureDefinition("rolling_std_20", "Volatility", "Rolling 20-period standard deviation of returns", 20, ["close"], "float", "NaN for t < 20"),

    # F. Trend
    FeatureDefinition("adx_14", "Trend", "Average Directional Index (14 periods)", 28, ["high", "low", "close"], "float", "NaN for t < 28"),
    FeatureDefinition("ema_slope_21", "Trend", "(EMA_21_t - EMA_21_{t-5}) / EMA_21_{t-5}", 26, ["close"], "float", "NaN for t < 26"),
    FeatureDefinition("price_vs_ema_21", "Trend", "(C_t - EMA_21) / EMA_21", 21, ["close"], "float", "Normalized distance"),
    FeatureDefinition("price_vs_ema_50", "Trend", "(C_t - EMA_50) / EMA_50", 50, ["close"], "float", "Normalized distance"),
    FeatureDefinition("price_vs_ema_200", "Trend", "(C_t - EMA_200) / EMA_200", 200, ["close"], "float", "Normalized distance"),
    FeatureDefinition("ma_cross_20_50", "Trend", "1 if SMA_20 > SMA_50 else 0", 50, ["close"], "int", "State indicator"),
    FeatureDefinition("ma_cross_50_200", "Trend", "1 if SMA_50 > SMA_200 else 0", 200, ["close"], "int", "Golden cross regime"),

    # G. Volume
    FeatureDefinition("volume_ma_20", "Volume", "SMA(volume, 20)", 20, ["volume"], "float", "NaN for t < 20"),
    FeatureDefinition("volume_ratio_20", "Volume", "volume / volume_ma_20", 20, ["volume"], "float", "1.0 default if 0"),
    FeatureDefinition("volume_change", "Volume", "(V_t - V_{t-1}) / V_{t-1}", 1, ["volume"], "float", "NaN for first row"),
    FeatureDefinition("obv", "Volume", "Cumulative On-Balance Volume", 1, ["close", "volume"], "float", "Continuous cumulative"),
]


class FeatureEngine:
    """
    Computes all Group A-G technical and structural market features with
    guaranteed zero future data leakage.
    """

    VERSION = "v1.0.0"

    @classmethod
    def compute_features(cls, df: pd.DataFrame, dropna: bool = False) -> pd.DataFrame:
        if df.empty or len(df) < 2:
            return pd.DataFrame()

        data = df.copy()
        if not isinstance(data.index, pd.DatetimeIndex) and "open_time" in data.columns:
            data["open_time"] = pd.to_datetime(data["open_time"], utc=True)
            data.set_index("open_time", inplace=True)
        data.sort_index(inplace=True)

        o = data["open"].astype(float)
        h = data["high"].astype(float)
        l = data["low"].astype(float)
        c = data["close"].astype(float)
        v = data["volume"].astype(float)

        feats = pd.DataFrame(index=data.index)

        # ------------------------------------------------------------------
        # Group A: Price Features
        # ------------------------------------------------------------------
        feats["returns"] = c.pct_change()
        feats["log_returns"] = np.log(c / c.shift(1))
        feats["percentage_change"] = feats["returns"] * 100.0

        # ------------------------------------------------------------------
        # Group B: Candle Features
        # ------------------------------------------------------------------
        candle_range = h - l
        # Safe range divisor to prevent division by zero in zero-range candles
        safe_range = candle_range.clip(lower=1e-8)

        feats["body_size"] = (c - o).abs()
        feats["body_percentage"] = feats["body_size"] / safe_range
        feats["upper_wick"] = h - np.maximum(o.to_numpy(), c.to_numpy())
        feats["lower_wick"] = np.minimum(o.to_numpy(), c.to_numpy()) - l
        feats["candle_range"] = candle_range
        feats["body_to_range_ratio"] = feats["body_size"] / safe_range
        feats["bullish_flag"] = (c > o).astype(int)
        feats["bearish_flag"] = (c < o).astype(int)

        # ------------------------------------------------------------------
        # Group C: Moving Averages
        # ------------------------------------------------------------------
        feats["sma_20"] = c.rolling(window=20).mean()
        feats["sma_50"] = c.rolling(window=50).mean()
        feats["sma_200"] = c.rolling(window=200).mean()

        feats["ema_9"] = c.ewm(span=9, adjust=False).mean()
        feats["ema_21"] = c.ewm(span=21, adjust=False).mean()
        feats["ema_50"] = c.ewm(span=50, adjust=False).mean()
        feats["ema_200"] = c.ewm(span=200, adjust=False).mean()

        # ------------------------------------------------------------------
        # Group D: Momentum
        # ------------------------------------------------------------------
        # RSI(14) with Wilder's smoothing
        delta = c.diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)
        roll_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        roll_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = roll_gain / roll_loss.clip(lower=1e-8)
        feats["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))

        # MACD (12, 26, 9)
        ema_12 = c.ewm(span=12, adjust=False).mean()
        ema_26 = c.ewm(span=26, adjust=False).mean()
        feats["macd"] = ema_12 - ema_26
        feats["macd_signal"] = feats["macd"].ewm(span=9, adjust=False).mean()
        feats["macd_hist"] = feats["macd"] - feats["macd_signal"]

        # Stochastic (14, 3)
        low_14 = l.rolling(window=14).min()
        high_14 = h.rolling(window=14).max()
        stoch_denom = (high_14 - low_14).clip(lower=1e-8)
        feats["stoch_k"] = ((c - low_14) / stoch_denom) * 100.0
        feats["stoch_d"] = feats["stoch_k"].rolling(window=3).mean()

        # Rate of Change (10)
        feats["roc_10"] = c.pct_change(periods=10) * 100.0

        # ------------------------------------------------------------------
        # Group E: Volatility
        # ------------------------------------------------------------------
        # True Range & ATR(14)
        prev_close = c.shift(1)
        tr1 = h - l
        tr2 = (h - prev_close).abs()
        tr3 = (l - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        feats["atr_14"] = true_range.ewm(alpha=1/14, adjust=False).mean()

        # Bollinger Bands (20, 2)
        rolling_std = c.rolling(window=20).std()
        bb_upper = feats["sma_20"] + (2.0 * rolling_std)
        bb_lower = feats["sma_20"] - (2.0 * rolling_std)
        sma20_safe = feats["sma_20"].replace(0, 1e-8)
        feats["bb_width_20"] = (bb_upper - bb_lower) / sma20_safe
        feats["rolling_std_20"] = feats["returns"].rolling(window=20).std()

        # ------------------------------------------------------------------
        # Group F: Trend
        # ------------------------------------------------------------------
        # Directional Movement (+DM, -DM) and ADX(14)
        up_move = h - h.shift(1)
        down_move = l.shift(1) - l
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

        tr_smooth = true_range.ewm(alpha=1/14, adjust=False).mean()
        tr_smooth_safe = tr_smooth.clip(lower=1e-8)
        plus_di = 100.0 * (plus_dm.ewm(alpha=1/14, adjust=False).mean() / tr_smooth_safe)
        minus_di = 100.0 * (minus_dm.ewm(alpha=1/14, adjust=False).mean() / tr_smooth_safe)
        dx_denom = (plus_di + minus_di).clip(lower=1e-8)
        dx = 100.0 * ((plus_di - minus_di).abs() / dx_denom)
        feats["adx_14"] = dx.ewm(alpha=1/14, adjust=False).mean()

        # EMA slopes & distance ratios
        ema21_shift5_safe = feats["ema_21"].shift(5).replace(0, 1e-8)
        feats["ema_slope_21"] = (feats["ema_21"] - feats["ema_21"].shift(5)) / ema21_shift5_safe
        feats["price_vs_ema_21"] = (c - feats["ema_21"]) / feats["ema_21"].replace(0, 1e-8)
        feats["price_vs_ema_50"] = (c - feats["ema_50"]) / feats["ema_50"].replace(0, 1e-8)
        feats["price_vs_ema_200"] = (c - feats["ema_200"]) / feats["ema_200"].replace(0, 1e-8)

        feats["ma_cross_20_50"] = (feats["sma_20"] > feats["sma_50"]).astype(int)
        feats["ma_cross_50_200"] = (feats["sma_50"] > feats["sma_200"]).astype(int)

        # ------------------------------------------------------------------
        # Group G: Volume
        # ------------------------------------------------------------------
        feats["volume_ma_20"] = v.rolling(window=20).mean()
        feats["volume_ratio_20"] = v / feats["volume_ma_20"].replace(0, 1e-8)
        feats["volume_change"] = v.pct_change()

        # On-Balance Volume (OBV)
        price_diff = c.diff().fillna(0)
        obv_direction = np.sign(price_diff.to_numpy())
        feats["obv"] = (v * obv_direction).cumsum()

        if dropna:
            feats.dropna(inplace=True)

        return feats

    @classmethod
    def generate_documentation_markdown(cls) -> str:
        """Generates comprehensive documentation catalog for FEATURE_CATALOG_V1."""
        lines = [
            f"# Feature Catalog ({cls.VERSION})",
            "",
            "**Document Version:** 1.0  ",
            "**Reference:** Implementation Plan Section 11 (Phase 6)  ",
            "**Guaranteed Invariant:** Zero future information leakage. All features at candle index $T$ use only data $\\le T$.  ",
            "",
            "## Summary Table",
            "",
            "| Feature Name | Group | Formula / Definition | Window | Inputs | Output Type | Missing Value Handling | Leakage Risk |",
            "|---|---|---|---|---|---|---|---|",
        ]

        for f in FEATURE_CATALOG_V1:
            inputs_str = ", ".join(f.input_columns)
            lines.append(
                f"| `{f.name}` | {f.group} | `{f.formula}` | {f.window} | {inputs_str} | `{f.output_type}` | {f.missing_value_behavior} | {f.leakage_risk} |"
            )

        return "\n".join(lines)
