"""
Baseline Trading Strategies and Benchmark Evaluation.
Reference: Section 19 (Phase 14) of Implementation Plan.

Provides non-ML and heuristic baselines against which all ML models are rigorously evaluated:
1. RuleBasedBaselineStrategy: Classical technical trading rule (RSI oversold/overbought + Trend filter + Candlestick confirmation).
2. MomentumBaselineStrategy: Market structure breakout following confirmed trend direction.
3. MajorityClassBaseline: Always predicts the dominant class (typically NEUTRAL).
4. StratifiedRandomBaseline: Predicts classes proportionally to prior empirical distribution.

Includes BaselineEvaluationResult with comprehensive multi-class classification and directional trading metrics:
- Precision, Recall, F1 for UP (+1.0), DOWN (-1.0), NEUTRAL (0.0)
- Balanced Accuracy, Macro F1, Accuracy
- Directional Win Rate (Precision on active UP/DOWN signals)
- Signal Frequency (% of non-NEUTRAL predictions)
- Confusion Matrix
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union, cast
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


@dataclass
class BaselineEvaluationResult:
    """Summary of benchmark performance against ground-truth triple-barrier labels."""
    strategy_name: str
    total_samples: int
    evaluated_samples: int
    accuracy: float
    balanced_accuracy: float
    macro_f1: float
    precision_per_class: Dict[str, float]
    recall_per_class: Dict[str, float]
    f1_per_class: Dict[str, float]
    directional_win_rate: float
    signal_frequency: float
    confusion_matrix: List[List[int]]
    class_distribution_true: Dict[str, int]
    class_distribution_pred: Dict[str, int]

    def to_markdown(self) -> str:
        """Renders comprehensive markdown summary table."""
        md = [
            f"### Baseline Evaluation: {self.strategy_name}",
            "",
            f"- **Evaluated Samples:** {self.evaluated_samples:,} (of {self.total_samples:,})",
            f"- **Accuracy:** {self.accuracy * 100:.2f}%",
            f"- **Balanced Accuracy:** {self.balanced_accuracy * 100:.2f}%",
            f"- **Macro F1:** {self.macro_f1:.4f}",
            f"- **Directional Win Rate:** {self.directional_win_rate * 100:.2f}%",
            f"- **Signal Frequency:** {self.signal_frequency * 100:.2f}%",
            "",
            "#### Per-Class Performance",
            "",
            "| Class | Support (True) | Predicted | Precision | Recall | F1-Score |",
            "|---|---|---|---|---|---|",
        ]

        for cls_name in ["UP", "DOWN", "NEUTRAL"]:
            s_true = self.class_distribution_true.get(cls_name, 0)
            s_pred = self.class_distribution_pred.get(cls_name, 0)
            p = self.precision_per_class.get(cls_name, 0.0) * 100.0
            r = self.recall_per_class.get(cls_name, 0.0) * 100.0
            f1 = self.f1_per_class.get(cls_name, 0.0)
            md.append(f"| **{cls_name}** | {s_true:,} | {s_pred:,} | {p:.2f}% | {r:.2f}% | {f1:.4f} |")

        md.extend([
            "",
            "#### Confusion Matrix",
            "",
            "| True \\ Pred | Pred DOWN (-1) | Pred NEUTRAL (0) | Pred UP (+1) |",
            "|---|---|---|---|",
        ])

        labels = ["DOWN", "NEUTRAL", "UP"]
        for i, row_label in enumerate(labels):
            if i < len(self.confusion_matrix):
                row = self.confusion_matrix[i]
                c0 = row[0] if len(row) > 0 else 0
                c1 = row[1] if len(row) > 1 else 0
                c2 = row[2] if len(row) > 2 else 0
                md.append(f"| **True {row_label}** | {c0:,} | {c1:,} | {c2:,} |")

        return "\n".join(md)


class BaselineStrategy(ABC):
    """Abstract base class for all baseline and heuristic trading strategies."""

    LABEL_DOWN = -1.0
    LABEL_NEUTRAL = 0.0
    LABEL_UP = 1.0

    CLASS_NAMES = ["DOWN", "NEUTRAL", "UP"]
    LABEL_TO_NAME = {-1.0: "DOWN", 0.0: "NEUTRAL", 1.0: "UP"}
    NAME_TO_LABEL = {"DOWN": -1.0, "NEUTRAL": 0.0, "UP": 1.0}

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates predictions for each candle.
        Returns Series of float: -1.0 (DOWN), 0.0 (NEUTRAL), or +1.0 (UP).
        """
        pass

    @abstractmethod
    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns estimated probabilities for classes [DOWN, NEUTRAL, UP].
        """
        pass

    def evaluate(
        self,
        df: pd.DataFrame,
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
    ) -> BaselineEvaluationResult:
        """
        Evaluates predictions against ground truth labels.
        Excludes invalid boundary tail rows.
        """
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not present in dataframe.")

        # Filter valid evaluation rows
        if valid_col in df.columns:
            valid_mask_series = pd.Series(df[valid_col]) == True
            eval_df: pd.DataFrame = pd.DataFrame(df[valid_mask_series]).copy()
        else:
            eval_df = pd.DataFrame(df).copy()

        # Predict across the evaluation subset
        raw_preds = self.predict(eval_df)
        preds = pd.Series(raw_preds, index=eval_df.index, dtype=float)
        y_true = pd.Series(eval_df[target_col], dtype=float)

        # Drop any remaining NaNs in targets
        valid_mask = ~(y_true.isna() | preds.isna())
        y_true_clean = np.asarray(y_true[valid_mask], dtype=float)
        preds_clean = np.asarray(preds[valid_mask], dtype=float)

        n_eval = len(y_true_clean)
        n_total = len(df)

        if n_eval == 0:
            return BaselineEvaluationResult(
                strategy_name=self.__class__.__name__,
                total_samples=n_total,
                evaluated_samples=0,
                accuracy=0.0,
                balanced_accuracy=0.0,
                macro_f1=0.0,
                precision_per_class={"DOWN": 0.0, "NEUTRAL": 0.0, "UP": 0.0},
                recall_per_class={"DOWN": 0.0, "NEUTRAL": 0.0, "UP": 0.0},
                f1_per_class={"DOWN": 0.0, "NEUTRAL": 0.0, "UP": 0.0},
                directional_win_rate=0.0,
                signal_frequency=0.0,
                confusion_matrix=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                class_distribution_true={"DOWN": 0, "NEUTRAL": 0, "UP": 0},
                class_distribution_pred={"DOWN": 0, "NEUTRAL": 0, "UP": 0},
            )

        # Multi-class mapping: [-1.0, 0.0, 1.0]
        classes = [-1.0, 0.0, 1.0]
        acc = float(accuracy_score(y_true_clean, preds_clean))
        bal_acc = float(balanced_accuracy_score(y_true_clean, preds_clean))
        m_f1 = float(f1_score(y_true_clean, preds_clean, labels=classes, average="macro", zero_division=cast(Any, 0)))

        # Per-class metrics
        prec_raw = precision_score(y_true_clean, preds_clean, labels=classes, average=cast(Any, None), zero_division=cast(Any, 0))
        rec_raw = recall_score(y_true_clean, preds_clean, labels=classes, average=cast(Any, None), zero_division=cast(Any, 0))
        f1_raw = f1_score(y_true_clean, preds_clean, labels=classes, average=cast(Any, None), zero_division=cast(Any, 0))

        prec_arr = np.asarray(prec_raw, dtype=float)
        rec_arr = np.asarray(rec_raw, dtype=float)
        f1_arr = np.asarray(f1_raw, dtype=float)

        prec_dict = {"DOWN": float(prec_arr[0]), "NEUTRAL": float(prec_arr[1]), "UP": float(prec_arr[2])}
        rec_dict = {"DOWN": float(rec_arr[0]), "NEUTRAL": float(rec_arr[1]), "UP": float(rec_arr[2])}
        f1_dict = {"DOWN": float(f1_arr[0]), "NEUTRAL": float(f1_arr[1]), "UP": float(f1_arr[2])}

        # Confusion Matrix (DOWN, NEUTRAL, UP)
        cm = confusion_matrix(y_true_clean, preds_clean, labels=classes)
        cm_list = [[int(cell) for cell in row] for row in cm]

        # Support counts
        true_counts = {
            "DOWN": int(np.sum(y_true_clean == -1.0)),
            "NEUTRAL": int(np.sum(y_true_clean == 0.0)),
            "UP": int(np.sum(y_true_clean == 1.0)),
        }
        pred_counts = {
            "DOWN": int(np.sum(preds_clean == -1.0)),
            "NEUTRAL": int(np.sum(preds_clean == 0.0)),
            "UP": int(np.sum(preds_clean == 1.0)),
        }

        # Directional win rate (UP or DOWN trades only)
        directional_mask = preds_clean != 0.0
        n_directional = int(np.sum(directional_mask))
        if n_directional > 0:
            dir_correct = int(np.sum(y_true_clean[directional_mask] == preds_clean[directional_mask]))
            win_rate = float(dir_correct / n_directional)
            sig_freq = float(n_directional / n_eval)
        else:
            win_rate = 0.0
            sig_freq = 0.0

        return BaselineEvaluationResult(
            strategy_name=self.__class__.__name__,
            total_samples=n_total,
            evaluated_samples=n_eval,
            accuracy=acc,
            balanced_accuracy=bal_acc,
            macro_f1=m_f1,
            precision_per_class=prec_dict,
            recall_per_class=rec_dict,
            f1_per_class=f1_dict,
            directional_win_rate=win_rate,
            signal_frequency=sig_freq,
            confusion_matrix=cm_list,
            class_distribution_true=true_counts,
            class_distribution_pred=pred_counts,
        )


class RuleBasedBaselineStrategy(BaselineStrategy):
    """
    Classical Technical Rule-Based Benchmark.
    Section 19:
      IF RSI < 30 AND price > EMA200 AND bullish_engulfing -> UP
      IF RSI > 70 AND price < EMA200 AND bearish_engulfing -> DOWN
      ELSE -> NEUTRAL
    """

    def __init__(
        self,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        trend_filter_col: str = "sma_200",
        rsi_col: str = "rsi_14",
    ):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.trend_filter_col = trend_filter_col
        self.rsi_col = rsi_col

    def predict(self, df: pd.DataFrame) -> pd.Series:
        n = len(df)
        preds = np.zeros(n, dtype=float)

        # Check required columns
        close = df["close"].to_numpy(dtype=float) if "close" in df.columns else np.zeros(n)
        rsi = df[self.rsi_col].to_numpy(dtype=float) if self.rsi_col in df.columns else np.full(n, 50.0)

        # Trend filter (fallback to sma_50 or ema_21 if 200 is NaN)
        if self.trend_filter_col in df.columns and not bool(pd.Series(df[self.trend_filter_col]).isna().all()):
            trend_val = df[self.trend_filter_col].to_numpy(dtype=float)
        elif "sma_50" in df.columns and not bool(pd.Series(df["sma_50"]).isna().all()):
            trend_val = df["sma_50"].to_numpy(dtype=float)
        elif "ema_21" in df.columns:
            trend_val = df["ema_21"].to_numpy(dtype=float)
        else:
            trend_val = close

        # Candlestick patterns
        bull_pattern = df["pattern_bullish_engulfing"].to_numpy(dtype=float) if "pattern_bullish_engulfing" in df.columns else np.zeros(n)
        bear_pattern = df["pattern_bearish_engulfing"].to_numpy(dtype=float) if "pattern_bearish_engulfing" in df.columns else np.zeros(n)

        # Optional auxiliary patterns (hammer / shooting star)
        hammer = df["pattern_hammer"].to_numpy(dtype=float) if "pattern_hammer" in df.columns else np.zeros(n)
        shooting = df["pattern_shooting_star"].to_numpy(dtype=float) if "pattern_shooting_star" in df.columns else np.zeros(n)

        bullish_trigger = (bull_pattern == 1.0) | (hammer == 1.0)
        bearish_trigger = (bear_pattern == 1.0) | (shooting == 1.0)

        # Bullish signal condition
        bull_mask = np.logical_and(np.logical_and(rsi < self.rsi_oversold, close >= trend_val), bullish_trigger)
        # Bearish signal condition
        bear_mask = np.logical_and(np.logical_and(rsi > self.rsi_overbought, close <= trend_val), bearish_trigger)

        preds[bull_mask] = self.LABEL_UP
        preds[bear_mask] = self.LABEL_DOWN

        return pd.Series(preds, index=df.index)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        preds = self.predict(df)
        n = len(df)
        probas = np.zeros((n, 3), dtype=float)

        # Default distribution when NEUTRAL: [0.15, 0.70, 0.15]
        probas[:, 0] = 0.15  # DOWN
        probas[:, 1] = 0.70  # NEUTRAL
        probas[:, 2] = 0.15  # UP

        # Confident active signals
        up_mask = (preds == self.LABEL_UP).to_numpy()
        probas[up_mask] = [0.10, 0.20, 0.70]

        down_mask = (preds == self.LABEL_DOWN).to_numpy()
        probas[down_mask] = [0.70, 0.20, 0.10]

        return pd.DataFrame(probas, index=df.index, columns=self.CLASS_NAMES)


class MomentumBaselineStrategy(BaselineStrategy):
    """
    Market Structure Momentum Benchmark.
    Buys on Breakout High during confirmed uptrend regime (+1).
    Sells on Breakout Low during confirmed downtrend regime (-1).
    """

    def predict(self, df: pd.DataFrame) -> pd.Series:
        n = len(df)
        preds = np.zeros(n, dtype=float)

        trend = df["trend_direction"].to_numpy(dtype=float) if "trend_direction" in df.columns else np.zeros(n)
        bos_high = df["is_breakout_high"].to_numpy(dtype=float) if "is_breakout_high" in df.columns else np.zeros(n)
        bos_low = df["is_breakout_low"].to_numpy(dtype=float) if "is_breakout_low" in df.columns else np.zeros(n)

        bull_mask = (trend == 1.0) & (bos_high == 1.0)
        bear_mask = (trend == -1.0) & (bos_low == 1.0)

        preds[bull_mask] = self.LABEL_UP
        preds[bear_mask] = self.LABEL_DOWN

        return pd.Series(preds, index=df.index)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        preds = self.predict(df)
        n = len(df)
        probas = np.zeros((n, 3), dtype=float)

        probas[:, 1] = 0.70
        probas[:, 0] = 0.15
        probas[:, 2] = 0.15

        up_mask = (preds == self.LABEL_UP).to_numpy()
        probas[up_mask] = [0.10, 0.25, 0.65]

        down_mask = (preds == self.LABEL_DOWN).to_numpy()
        probas[down_mask] = [0.65, 0.25, 0.10]

        return pd.DataFrame(probas, index=df.index, columns=self.CLASS_NAMES)


class MajorityClassBaseline(BaselineStrategy):
    """
    Predicts constant class (default NEUTRAL / 0.0).
    Represents the simplest zero-intelligence majority baseline.
    """

    def __init__(self, constant_label: float = 0.0):
        self.constant_label = constant_label

    def predict(self, df: pd.DataFrame) -> pd.Series:
        n = len(df)
        return pd.Series(np.full(n, self.constant_label), index=df.index)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        n = len(df)
        probas = np.zeros((n, 3), dtype=float)
        if self.constant_label == -1.0:
            probas[:, 0] = 1.0
        elif self.constant_label == 1.0:
            probas[:, 2] = 1.0
        else:
            probas[:, 1] = 1.0
        return pd.DataFrame(probas, index=df.index, columns=self.CLASS_NAMES)


class StratifiedRandomBaseline(BaselineStrategy):
    """
    Predicts classes randomly matching empirical class probabilities.
    Seedable for reproducible benchmarking.
    """

    def __init__(
        self,
        p_down: float = 0.3333,
        p_neutral: float = 0.3334,
        p_up: float = 0.3333,
        seed: int = 42,
    ):
        total = p_down + p_neutral + p_up
        self.probs = [p_down / total, p_neutral / total, p_up / total]
        self.seed = seed

    def predict(self, df: pd.DataFrame) -> pd.Series:
        rng = np.random.default_rng(self.seed)
        choices = [-1.0, 0.0, 1.0]
        preds = rng.choice(choices, size=len(df), p=self.probs)
        return pd.Series(preds, index=df.index)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        n = len(df)
        probas = np.tile(self.probs, (n, 1))
        return pd.DataFrame(probas, index=df.index, columns=self.CLASS_NAMES)
