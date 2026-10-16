"""
Model Evaluation and Metric Calculation Engine.
Reference: Section 20 (Phase 15) of Implementation Plan.

Calculates comprehensive classification and financial performance metrics:
1. Classification Metrics:
   - Accuracy & Balanced Accuracy
   - Macro F1, Precision, Recall
   - Per-class Precision, Recall, and F1 (DOWN, NEUTRAL, UP)
   - Multi-class One-vs-Rest ROC-AUC
   - Multi-class One-vs-Rest PR-AUC (Average Precision)
   - Multi-class Log Loss (Cross-Entropy)
   - Brier Score Loss (Calibration error)
2. Directional Trading Metrics:
   - Directional Win Rate (Precision on active UP/DOWN signals)
   - Signal Frequency (% of non-NEUTRAL predictions)
   - Total Trade Count
3. Confusion Matrix and Summary Markdown Reporting
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union, cast
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.preprocessing import label_binarize


@dataclass
class ModelEvaluationResult:
    """Comprehensive multi-class classification and trading performance result."""
    model_name: str
    split_name: str
    total_samples: int
    evaluated_samples: int
    accuracy: float
    balanced_accuracy: float
    macro_f1: float
    macro_precision: float
    macro_recall: float
    precision_per_class: Dict[str, float]
    recall_per_class: Dict[str, float]
    f1_per_class: Dict[str, float]
    roc_auc_macro: Optional[float]
    pr_auc_macro: Optional[float]
    log_loss_value: Optional[float]
    brier_score_loss: Optional[float]
    directional_win_rate: float
    signal_frequency: float
    trade_count: int
    confusion_matrix: List[List[int]]

    def to_markdown(self) -> str:
        """Renders comprehensive Markdown evaluation report."""
        roc_str = f"{self.roc_auc_macro:.4f}" if self.roc_auc_macro is not None else "N/A"
        pr_str = f"{self.pr_auc_macro:.4f}" if self.pr_auc_macro is not None else "N/A"
        ll_str = f"{self.log_loss_value:.4f}" if self.log_loss_value is not None else "N/A"
        brier_str = f"{self.brier_score_loss:.4f}" if self.brier_score_loss is not None else "N/A"

        md = [
            f"### Model Evaluation: {self.model_name} ({self.split_name} Split)",
            "",
            "#### Overall Metrics",
            "",
            f"- **Evaluated Samples:** {self.evaluated_samples:,} (of {self.total_samples:,})",
            f"- **Accuracy:** {self.accuracy * 100.0:.2f}%",
            f"- **Balanced Accuracy:** {self.balanced_accuracy * 100.0:.2f}%",
            f"- **Macro F1:** {self.macro_f1:.4f}",
            f"- **Macro Precision:** {self.macro_precision:.4f}",
            f"- **Macro Recall:** {self.macro_recall:.4f}",
            f"- **One-vs-Rest ROC-AUC:** {roc_str}",
            f"- **One-vs-Rest PR-AUC:** {pr_str}",
            f"- **Log Loss:** {ll_str}",
            f"- **Brier Score:** {brier_str}",
            f"- **Directional Win Rate:** {self.directional_win_rate * 100.0:.2f}%",
            f"- **Signal Frequency:** {self.signal_frequency * 100.0:.2f}% ({self.trade_count:,} trades)",
            "",
            "#### Per-Class Performance",
            "",
            "| Class | Precision | Recall | F1-Score |",
            "|---|---|---|---|",
        ]

        for cls_name in ["DOWN", "NEUTRAL", "UP"]:
            p = self.precision_per_class.get(cls_name, 0.0) * 100.0
            r = self.recall_per_class.get(cls_name, 0.0) * 100.0
            f1 = self.f1_per_class.get(cls_name, 0.0)
            md.append(f"| **{cls_name}** | {p:.2f}% | {r:.2f}% | {f1:.4f} |")

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


class ModelEvaluator:
    """
    Evaluation engine computing multi-class probabilistic and directional metrics.
    """

    CLASSES = [-1.0, 0.0, 1.0]
    CLASS_NAMES = ["DOWN", "NEUTRAL", "UP"]

    @classmethod
    def evaluate(
        cls,
        y_true: Union[pd.Series, np.ndarray],
        y_pred: Union[pd.Series, np.ndarray],
        y_prob: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        model_name: str = "Model",
        split_name: str = "Test",
        total_samples: Optional[int] = None,
    ) -> ModelEvaluationResult:
        """
        Computes the complete metric suite for multi-class target labels (-1.0, 0.0, +1.0).
        """
        y_t = np.asarray(y_true, dtype=np.float64)
        y_p = np.asarray(y_pred, dtype=np.float64)

        valid_mask = ~(np.isnan(y_t) | np.isnan(y_p))
        y_t_clean = y_t[valid_mask]
        y_p_clean = y_p[valid_mask]

        n_eval = len(y_t_clean)
        n_total = total_samples if total_samples is not None else n_eval

        if n_eval == 0:
            return ModelEvaluationResult(
                model_name=model_name,
                split_name=split_name,
                total_samples=n_total,
                evaluated_samples=0,
                accuracy=0.0,
                balanced_accuracy=0.0,
                macro_f1=0.0,
                macro_precision=0.0,
                macro_recall=0.0,
                precision_per_class={"DOWN": 0.0, "NEUTRAL": 0.0, "UP": 0.0},
                recall_per_class={"DOWN": 0.0, "NEUTRAL": 0.0, "UP": 0.0},
                f1_per_class={"DOWN": 0.0, "NEUTRAL": 0.0, "UP": 0.0},
                roc_auc_macro=None,
                pr_auc_macro=None,
                log_loss_value=None,
                brier_score_loss=None,
                directional_win_rate=0.0,
                signal_frequency=0.0,
                trade_count=0,
                confusion_matrix=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            )

        # Standard Classification Metrics
        acc = float(accuracy_score(y_t_clean, y_p_clean))
        bal_acc = float(balanced_accuracy_score(y_t_clean, y_p_clean))
        m_f1 = float(f1_score(y_t_clean, y_p_clean, labels=cls.CLASSES, average="macro", zero_division=cast(Any, 0)))
        m_prec = float(precision_score(y_t_clean, y_p_clean, labels=cls.CLASSES, average="macro", zero_division=cast(Any, 0)))
        m_rec = float(recall_score(y_t_clean, y_p_clean, labels=cls.CLASSES, average="macro", zero_division=cast(Any, 0)))

        prec_raw = precision_score(y_t_clean, y_p_clean, labels=cls.CLASSES, average=cast(Any, None), zero_division=cast(Any, 0))
        rec_raw = recall_score(y_t_clean, y_p_clean, labels=cls.CLASSES, average=cast(Any, None), zero_division=cast(Any, 0))
        f1_raw = f1_score(y_t_clean, y_p_clean, labels=cls.CLASSES, average=cast(Any, None), zero_division=cast(Any, 0))

        prec_arr = np.asarray(prec_raw, dtype=np.float64)
        rec_arr = np.asarray(rec_raw, dtype=np.float64)
        f1_arr = np.asarray(f1_raw, dtype=np.float64)

        prec_dict = {"DOWN": float(prec_arr[0]), "NEUTRAL": float(prec_arr[1]), "UP": float(prec_arr[2])}
        rec_dict = {"DOWN": float(rec_arr[0]), "NEUTRAL": float(rec_arr[1]), "UP": float(rec_arr[2])}
        f1_dict = {"DOWN": float(f1_arr[0]), "NEUTRAL": float(f1_arr[1]), "UP": float(f1_arr[2])}

        # Confusion Matrix
        cm = confusion_matrix(y_t_clean, y_p_clean, labels=cls.CLASSES)
        cm_list = [[int(cell) for cell in row] for row in cm]

        # Probabilistic Metrics (ROC-AUC, PR-AUC, Log Loss, Brier Score)
        roc_auc: Optional[float] = None
        pr_auc: Optional[float] = None
        ll_val: Optional[float] = None
        brier_val: Optional[float] = None

        if y_prob is not None:
            raw_prob_mat = np.asarray(y_prob, dtype=np.float64)
            prob_mat = raw_prob_mat[valid_mask] if len(raw_prob_mat) == len(y_t) else raw_prob_mat

            if prob_mat.shape[1] == 3 and len(prob_mat) == n_eval:
                # One-hot ground truth encoding
                y_bin = label_binarize(y_t_clean, classes=cls.CLASSES)
                if y_bin.shape[1] == 1:
                    # Handle binary edge case
                    y_bin = np.hstack([1 - y_bin, y_bin])

                # Multi-class Log Loss
                try:
                    ll_val = float(log_loss(y_t_clean, prob_mat, labels=cls.CLASSES))
                except Exception:
                    ll_val = None

                # Brier Score (Mean Squared Probability Error across all classes)
                try:
                    brier_val = float(np.mean(np.sum((prob_mat - y_bin) ** 2, axis=1)))
                except Exception:
                    brier_val = None

                # ROC-AUC (ovr macro)
                try:
                    unique_classes = np.unique(y_t_clean)
                    if len(unique_classes) >= 2:
                        roc_auc = float(roc_auc_score(y_bin, prob_mat, multi_class="ovr", average="macro"))
                except Exception:
                    roc_auc = None

                # PR-AUC (ovr macro average precision)
                try:
                    if len(np.unique(y_t_clean)) >= 2:
                        pr_auc = float(average_precision_score(y_bin, prob_mat, average="macro"))
                except Exception:
                    pr_auc = None

        # Directional Trading Metrics
        active_signals = y_p_clean != 0.0
        n_trades = int(np.sum(active_signals))
        if n_trades > 0:
            dir_correct = int(np.sum(y_t_clean[active_signals] == y_p_clean[active_signals]))
            win_rate = float(dir_correct / n_trades)
            sig_freq = float(n_trades / n_eval)
        else:
            win_rate = 0.0
            sig_freq = 0.0

        return ModelEvaluationResult(
            model_name=model_name,
            split_name=split_name,
            total_samples=n_total,
            evaluated_samples=n_eval,
            accuracy=acc,
            balanced_accuracy=bal_acc,
            macro_f1=m_f1,
            macro_precision=m_prec,
            macro_recall=m_rec,
            precision_per_class=prec_dict,
            recall_per_class=rec_dict,
            f1_per_class=f1_dict,
            roc_auc_macro=roc_auc,
            pr_auc_macro=pr_auc,
            log_loss_value=ll_val,
            brier_score_loss=brier_val,
            directional_win_rate=win_rate,
            signal_frequency=sig_freq,
            trade_count=n_trades,
            confusion_matrix=cm_list,
        )
