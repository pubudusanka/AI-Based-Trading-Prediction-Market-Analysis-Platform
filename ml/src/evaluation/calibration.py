"""
Probability Calibration Engine, Reliability Curves, and Calibrated Model Wrapper.
Reference: Section 22 (Phase 17) of Implementation Plan.

Guarantees:
- Output is always a well-calibrated, normalized multi-class probability distribution:
  {"DOWN": p_down, "NEUTRAL": p_neutral, "UP": p_up} where sum(p) == 1.0.
- Calibration is fitted strictly on out-of-sample / validation data (zero lookahead leakage).
- Supports both Sigmoid (Platt Scaling) and Isotonic Regression calibration.
- Reliability Curves, Expected Calibration Error (ECE), and Maximum Calibration Error (MCE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Dict, Any, List, Optional, Tuple, Union, cast, TYPE_CHECKING
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import label_binarize

from src.evaluation.metrics import ModelEvaluator, ModelEvaluationResult

if TYPE_CHECKING:
    from src.training.models import BaseTradingModel


@dataclass
class ReliabilityBin:
    """Statistics for a single probability bin in a calibration curve."""
    bin_idx: int
    prob_min: float
    prob_max: float
    mean_predicted: float
    empirical_frequency: float
    sample_count: int


@dataclass
class ClassCalibrationMetrics:
    """Calibration assessment metrics for a single target class."""
    class_name: str
    class_label: float
    expected_calibration_error: float
    maximum_calibration_error: float
    brier_score: float
    reliability_bins: List[ReliabilityBin]


@dataclass
class CalibrationAuditReport:
    """Summary report comparing uncalibrated vs calibrated model performance."""
    model_name: str
    calibration_method: str
    symbol: str
    timeframe: str
    evaluated_samples: int
    mean_ece_uncalibrated: float
    mean_ece_calibrated: float
    brier_score_uncalibrated: float
    brier_score_calibrated: float
    class_metrics: Dict[str, ClassCalibrationMetrics]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_markdown(self) -> str:
        """Renders comprehensive Markdown probability calibration audit report."""
        ece_diff = (self.mean_ece_uncalibrated - self.mean_ece_calibrated) * 100.0
        brier_diff = self.brier_score_uncalibrated - self.brier_score_calibrated

        md = [
            f"# Probability Calibration Report: {self.model_name}",
            "",
            f"**Asset:** {self.symbol} ({self.timeframe})  ",
            f"**Calibration Method:** {self.calibration_method.capitalize()} Calibration (Platt / Isotonic)  ",
            f"**Validation Samples:** {self.evaluated_samples:,}  ",
            f"**Generated At:** {self.generated_at}  ",
            "",
            "---",
            "",
            "## 1. Calibration Error Summary",
            "",
            "| Metric | Uncalibrated | Calibrated | Improvement |",
            "|---|---|---|---|",
            f"| **Expected Calibration Error (ECE)** | {self.mean_ece_uncalibrated * 100:.2f}% | {self.mean_ece_calibrated * 100:.2f}% | {ece_diff:+.2f}% |",
            f"| **Multi-Class Brier Score** | {self.brier_score_uncalibrated:.4f} | {self.brier_score_calibrated:.4f} | {brier_diff:+.4f} |",
            "",
            "---",
            "",
            "## 2. Per-Class Calibration Reliability Curves",
            "",
        ]

        for cls_name in ["DOWN", "NEUTRAL", "UP"]:
            if cls_name in self.class_metrics:
                cm = self.class_metrics[cls_name]
                md.extend([
                    f"### Class `{cls_name}` (ECE: {cm.expected_calibration_error * 100:.2f}%, Brier: {cm.brier_score:.4f})",
                    "",
                    "| Bin Range | Mean Forecast Probability | Empirical Win Frequency | Sample Count | Absolute Error |",
                    "|---|---|---|---|---|",
                ])

                for b in cm.reliability_bins:
                    bin_range = f"[{b.prob_min:.2f} - {b.prob_max:.2f}]"
                    abs_err = abs(b.empirical_frequency - b.mean_predicted) * 100.0
                    md.append(
                        f"| {bin_range} | {b.mean_predicted * 100:.1f}% | "
                        f"{b.empirical_frequency * 100:.1f}% | {b.sample_count:,} | {abs_err:.2f}% |"
                    )
                md.append("")

        return "\n".join(md)

    def save_markdown(self, filepath: str) -> str:
        """Saves calibration report to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        content = self.to_markdown()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


class ProbabilityCalibrator:
    """
    Fits and applies multi-class probability calibration using One-vs-Rest calibrators.
    """

    CLASS_LABELS = [-1.0, 0.0, 1.0]
    CLASS_NAMES = ["DOWN", "NEUTRAL", "UP"]

    def __init__(self, method: str = "sigmoid", n_bins: int = 5):
        if method not in ["sigmoid", "isotonic"]:
            raise ValueError(f"method must be 'sigmoid' or 'isotonic', got '{method}'")

        self.method = method
        self.n_bins = n_bins
        self.calibrators: Dict[float, Union[LogisticRegression, IsotonicRegression]] = {}
        self.is_fitted: bool = False

    def fit(self, y_prob: np.ndarray, y_true: np.ndarray) -> "ProbabilityCalibrator":
        """
        Fits 3 binary calibrators (one per class) on uncalibrated out-of-sample probabilities.
        """
        valid_mask = ~(np.isnan(y_true) | np.isnan(y_prob).any(axis=1))
        y_p = y_prob[valid_mask]
        y_t = y_true[valid_mask]

        if len(y_t) < 10:
            raise ValueError(f"Insufficient samples to fit calibrator: {len(y_t)}")

        # One-hot encode targets
        y_bin = np.asarray(label_binarize(y_t, classes=self.CLASS_LABELS), dtype=np.float64)

        for col_idx, cls_label in enumerate(self.CLASS_LABELS):
            prob_col = np.asarray(y_p[:, col_idx], dtype=np.float64)
            target_binary = np.asarray(y_bin[:, col_idx], dtype=np.float64)

            # If a class has zero positive instances, skip or fit dummy
            target_sum = float(np.sum(target_binary))
            if target_sum == 0.0 or target_sum == float(len(target_binary)):
                continue

            if self.method == "sigmoid":
                # Platt scaling via univariate logistic regression on log-odds
                calibrator = LogisticRegression(C=1.0, solver="lbfgs")
                calibrator.fit(prob_col.reshape(-1, 1), target_binary)
                self.calibrators[cls_label] = calibrator
            else:
                # Isotonic regression (monotonically non-decreasing piecewise linear)
                calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                calibrator.fit(prob_col, target_binary)
                self.calibrators[cls_label] = calibrator

        self.is_fitted = True
        return self

    def calibrate(self, y_prob: np.ndarray) -> np.ndarray:
        """
        Applies fitted calibrators to raw probabilities and normalizes row-wise.
        Returns [N, 3] matrix where sum(row) == 1.0.
        """
        if not self.is_fitted:
            raise RuntimeError("ProbabilityCalibrator must be fitted before calibrate.")

        n_samples = len(y_prob)
        calibrated = np.zeros((n_samples, 3), dtype=np.float64)

        for col_idx, cls_label in enumerate(self.CLASS_LABELS):
            raw_p = y_prob[:, col_idx]

            if cls_label in self.calibrators:
                cal = self.calibrators[cls_label]
                if self.method == "sigmoid":
                    p_cal = cast(LogisticRegression, cal).predict_proba(raw_p.reshape(-1, 1))[:, 1]
                else:
                    p_cal = cast(IsotonicRegression, cal).predict(raw_p)
                calibrated[:, col_idx] = p_cal
            else:
                calibrated[:, col_idx] = raw_p

        # Normalize row-wise so probabilities sum to 1.0
        row_sums = calibrated.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return calibrated / row_sums

    @classmethod
    def compute_reliability_curve(
        cls,
        y_prob_col: np.ndarray,
        y_true_binary: np.ndarray,
        n_bins: int = 5,
    ) -> Tuple[float, float, List[ReliabilityBin]]:
        """
        Calculates ECE, MCE, and Reliability Bins for a 1D probability array.
        """
        bins = np.linspace(0.0, 1.0, n_bins + 1)
        bin_records: List[ReliabilityBin] = []

        total_samples = len(y_prob_col)
        ece = 0.0
        mce = 0.0

        for b_idx in range(n_bins):
            b_low = bins[b_idx]
            b_high = bins[b_idx + 1]

            if b_idx == n_bins - 1:
                mask = (y_prob_col >= b_low) & (y_prob_col <= b_high)
            else:
                mask = (y_prob_col >= b_low) & (y_prob_col < b_high)

            count = int(np.sum(mask))
            if count > 0:
                mean_pred = float(np.mean(y_prob_col[mask]))
                emp_freq = float(np.mean(y_true_binary[mask]))
                err = abs(emp_freq - mean_pred)

                ece += (count / total_samples) * err
                mce = max(mce, err)

                bin_records.append(
                    ReliabilityBin(
                        bin_idx=b_idx + 1,
                        prob_min=b_low,
                        prob_max=b_high,
                        mean_predicted=mean_pred,
                        empirical_frequency=emp_freq,
                        sample_count=count,
                    )
                )

        return float(ece), float(mce), bin_records


class CalibratedTradingModel:
    """
    Production-grade model wrapper combining a BaseTradingModel with ProbabilityCalibrator.
    Guarantees properly calibrated probability distributions for real-time predictions.
    """

    CLASS_NAMES = ["DOWN", "NEUTRAL", "UP"]
    CLASS_LABELS = [-1.0, 0.0, 1.0]

    def __init__(
        self,
        base_model: BaseTradingModel,
        method: str = "sigmoid",
        n_bins: int = 5,
    ):
        self.base_model = base_model
        self.calibrator = ProbabilityCalibrator(method=method, n_bins=n_bins)
        self.method = method
        self.is_calibrated: bool = False

    @property
    def name(self) -> str:
        return f"{self.base_model.name}_Calibrated({self.method})"

    def fit_and_calibrate(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
    ) -> "CalibratedTradingModel":
        """
        Fits base model strictly on train_df, then fits probability calibrator strictly on val_df.
        """
        # 1. Fit base model on training split
        self.base_model.fit(train_df, target_col=target_col, valid_col=valid_col)

        # 2. Get uncalibrated validation probabilities
        val_prob_df = self.base_model.predict_proba(val_df)
        val_prob = np.asarray(val_prob_df, dtype=np.float64)

        y_val_series = pd.Series(val_df[target_col], dtype=float)
        y_val = np.asarray(y_val_series, dtype=np.float64)

        # 3. Fit calibrator strictly on validation split
        self.calibrator.fit(val_prob, y_val)
        self.is_calibrated = True
        return self

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns well-calibrated class probability DataFrame.
        """
        raw_prob_df = self.base_model.predict_proba(df)
        raw_probas = np.asarray(raw_prob_df, dtype=np.float64)

        if not self.is_calibrated:
            return raw_prob_df

        cal_probas = self.calibrator.calibrate(raw_probas)
        return pd.DataFrame(cal_probas, index=df.index, columns=self.CLASS_NAMES)

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Predicts class with highest calibrated probability.
        """
        probas = self.predict_proba(df)
        prob_mat = np.asarray(probas, dtype=np.float64)
        pred_idx = np.argmax(prob_mat, axis=1)
        preds = np.array([self.CLASS_LABELS[i] for i in pred_idx], dtype=np.float64)
        return pd.Series(cast(Any, preds), index=df.index)

    def predict_single_dict(self, candle_features: Union[pd.Series, pd.DataFrame, Dict[str, Any]]) -> Dict[str, float]:
        """
        Formats real-time prediction for a single candle into the required platform JSON schema:
        {
            "UP": 0.68,
            "DOWN": 0.17,
            "NEUTRAL": 0.15
        }
        """
        if isinstance(candle_features, dict):
            input_df = pd.DataFrame([candle_features])
        elif isinstance(candle_features, pd.Series):
            input_df = pd.DataFrame([candle_features.to_dict()])
        else:
            input_df = candle_features.iloc[[-1]]

        prob_df = self.predict_proba(input_df)
        row = prob_df.iloc[0]

        return {
            "UP": round(float(row["UP"]), 4),
            "DOWN": round(float(row["DOWN"]), 4),
            "NEUTRAL": round(float(row["NEUTRAL"]), 4),
        }

    def audit_calibration(
        self,
        eval_df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
    ) -> CalibrationAuditReport:
        """
        Compares uncalibrated vs calibrated probabilities and generates reliability curve audit.
        """
        if valid_col in eval_df.columns:
            valid_mask = pd.Series(eval_df[valid_col]) == True
            sub_df = pd.DataFrame(eval_df[valid_mask])
        else:
            sub_df = pd.DataFrame(eval_df)

        y_true_clean = np.asarray(pd.Series(sub_df[target_col], dtype=float), dtype=np.float64)

        # Uncalibrated and Calibrated probabilities
        raw_prob_df = self.base_model.predict_proba(sub_df)
        raw_probs = np.asarray(raw_prob_df, dtype=np.float64)
        cal_prob_df = self.predict_proba(sub_df)
        cal_probs = np.asarray(cal_prob_df, dtype=np.float64)

        y_bin = np.asarray(label_binarize(y_true_clean, classes=self.CLASS_LABELS), dtype=np.float64)

        # Calculate Brier Scores
        brier_uncal = float(np.mean(np.sum((raw_probs - y_bin) ** 2, axis=1)))
        brier_cal = float(np.mean(np.sum((cal_probs - y_bin) ** 2, axis=1)))

        class_metrics: Dict[str, ClassCalibrationMetrics] = {}
        uncal_eces: List[float] = []
        cal_eces: List[float] = []

        for col_idx, cls_name in enumerate(self.CLASS_NAMES):
            cls_val = self.CLASS_LABELS[col_idx]
            y_bin_col = np.asarray(y_bin[:, col_idx], dtype=np.float64)

            raw_col = np.asarray(raw_probs[:, col_idx], dtype=np.float64)
            cal_col = np.asarray(cal_probs[:, col_idx], dtype=np.float64)

            # Uncalibrated ECE
            u_ece, _, _ = ProbabilityCalibrator.compute_reliability_curve(raw_col, y_bin_col, n_bins=self.calibrator.n_bins)
            uncal_eces.append(u_ece)

            # Calibrated ECE & Bins
            c_ece, c_mce, bins = ProbabilityCalibrator.compute_reliability_curve(cal_col, y_bin_col, n_bins=self.calibrator.n_bins)
            cal_eces.append(c_ece)

            cls_brier = float(np.mean((cal_col - y_bin_col) ** 2))
            class_metrics[cls_name] = ClassCalibrationMetrics(
                class_name=cls_name,
                class_label=cls_val,
                expected_calibration_error=c_ece,
                maximum_calibration_error=c_mce,
                brier_score=cls_brier,
                reliability_bins=bins,
            )

        return CalibrationAuditReport(
            model_name=self.base_model.name,
            calibration_method=self.method,
            symbol=symbol,
            timeframe=timeframe,
            evaluated_samples=len(sub_df),
            mean_ece_uncalibrated=float(np.mean(uncal_eces)),
            mean_ece_calibrated=float(np.mean(cal_eces)),
            brier_score_uncalibrated=brier_uncal,
            brier_score_calibrated=brier_cal,
            class_metrics=class_metrics,
        )

    def save(self, filepath: str) -> str:
        """Persists calibrated model and calibrator to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump(self, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> "CalibratedTradingModel":
        """Loads calibrated model from disk."""
        loaded = joblib.load(filepath)
        if not isinstance(loaded, CalibratedTradingModel):
            raise TypeError(f"Loaded object is not CalibratedTradingModel: {type(loaded)}")
        return loaded
