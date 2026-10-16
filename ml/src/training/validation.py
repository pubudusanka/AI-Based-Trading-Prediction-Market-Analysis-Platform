"""
Purged Walk-Forward Cross-Validation and Time-Series Validation Framework.
Reference: Section 21 (Phase 16) of Implementation Plan.

Strict Financial Machine Learning Requirements:
- Chronological ordering: Future candles never appear in training splits.
- Purging & Embargo: A safety buffer of N candles (matching label horizon) is enforced
  between train and test splits to prevent overlapping forward label information.
- Supports both Expanding Window (anchored walk-forward) and Rolling Window (fixed-size sliding window).
- Computes per-fold and aggregate out-of-sample performance stability across market regimes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Dict, Any, List, Optional, Tuple, Iterator, Generator, Union, cast
import numpy as np
import pandas as pd

from src.training.models import BaseTradingModel
from src.evaluation.metrics import ModelEvaluator, ModelEvaluationResult


class PurgedWalkForwardCV:
    """
    Purged chronological time-series cross-validator with embargo safety gaps.
    """

    def __init__(
        self,
        n_splits: int = 5,
        purge_candles: int = 20,
        expanding: bool = True,
        min_train_ratio: float = 0.40,
    ):
        if n_splits < 2:
            raise ValueError(f"n_splits must be at least 2, got {n_splits}")
        if purge_candles < 0:
            raise ValueError(f"purge_candles cannot be negative, got {purge_candles}")

        self.n_splits = n_splits
        self.purge_candles = purge_candles
        self.expanding = expanding
        self.min_train_ratio = min_train_ratio

    def split(self, df: pd.DataFrame) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generates (train_indices, test_indices) integer arrays for each fold.
        Strictly enforces train_end + purge_candles <= test_start.
        """
        n = len(df)
        min_train = int(n * self.min_train_ratio)
        usable_test = n - min_train - (self.n_splits * self.purge_candles)

        if usable_test <= 0:
            raise ValueError(
                f"Dataset length {n} is insufficient for {self.n_splits} splits "
                f"with {self.purge_candles} purge candles and {self.min_train_ratio:.0%} min train ratio."
            )

        test_fold_size = max(usable_test // self.n_splits, 1)

        for fold in range(self.n_splits):
            test_start = min_train + (fold * (test_fold_size + self.purge_candles)) + self.purge_candles
            test_end = test_start + test_fold_size if fold < self.n_splits - 1 else n

            if test_start >= n:
                break

            train_end = test_start - self.purge_candles

            if self.expanding:
                train_start = 0
            else:
                train_start = max(0, train_end - min_train)

            train_indices = np.arange(train_start, train_end, dtype=np.int64)
            test_indices = np.arange(test_start, test_end, dtype=np.int64)

            if len(train_indices) > 0 and len(test_indices) > 0:
                yield train_indices, test_indices


@dataclass
class WalkForwardFoldResult:
    """Performance evaluation for a single out-of-sample walk-forward fold."""
    fold_idx: int
    train_start: str
    train_end: str
    train_count: int
    test_start: str
    test_end: str
    test_count: int
    evaluation: ModelEvaluationResult


@dataclass
class WalkForwardValidationReport:
    """Multi-fold walk-forward cross-validation summary report."""
    model_name: str
    symbol: str
    timeframe: str
    n_splits: int
    purge_candles: int
    expanding: bool
    fold_results: List[WalkForwardFoldResult]
    mean_accuracy: float
    std_accuracy: float
    mean_balanced_accuracy: float
    std_balanced_accuracy: float
    mean_macro_f1: float
    std_macro_f1: float
    mean_win_rate: float
    std_win_rate: float
    total_trades: int
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_markdown(self) -> str:
        """Renders comprehensive Markdown walk-forward analysis report."""
        mode_str = "Expanding Window" if self.expanding else "Rolling Window"
        md = [
            f"# Walk-Forward Validation Report: {self.model_name}",
            "",
            f"**Asset:** {self.symbol} ({self.timeframe})  ",
            f"**Validation Scheme:** {self.n_splits}-Fold Purged Walk-Forward ({mode_str})  ",
            f"**Safety Embargo (Purge Gap):** {self.purge_candles} candles  ",
            f"**Generated At:** {self.generated_at}  ",
            "",
            "---",
            "",
            "## 1. Aggregate Out-of-Sample Performance",
            "",
            f"- **Mean Balanced Accuracy:** {self.mean_balanced_accuracy * 100:.2f}% (± {self.std_balanced_accuracy * 100:.2f}%)",
            f"- **Mean Macro F1:** {self.mean_macro_f1:.4f} (± {self.std_macro_f1:.4f})",
            f"- **Mean Accuracy:** {self.mean_accuracy * 100:.2f}% (± {self.std_accuracy * 100:.2f}%)",
            f"- **Directional Win Rate:** {self.mean_win_rate * 100:.2f}% (± {self.std_win_rate * 100:.2f}%)",
            f"- **Total Out-of-Sample Trades:** {self.total_trades:,}",
            "",
            "---",
            "",
            "## 2. Per-Fold Out-of-Sample Leaderboard",
            "",
            "| Fold | Train Window | Test Window | Test Samples | Balanced Acc | Macro F1 | Win Rate | Trades |",
            "|---|---|---|---|---|---|---|---|",
        ]

        for fr in self.fold_results:
            e = fr.evaluation
            train_span = f"`{fr.train_start[:10]}`..`{fr.train_end[:10]}`"
            test_span = f"`{fr.test_start[:10]}`..`{fr.test_end[:10]}`"
            md.append(
                f"| {fr.fold_idx} | {train_span} | {test_span} | {fr.test_count:,} | "
                f"{e.balanced_accuracy * 100:.2f}% | {e.macro_f1:.4f} | "
                f"{e.directional_win_rate * 100:.2f}% | {e.trade_count:,} |"
            )

        return "\n".join(md)

    def save_markdown(self, filepath: str) -> str:
        """Saves walk-forward report to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        content = self.to_markdown()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


class WalkForwardValidator:
    """
    Orchestrates out-of-sample walk-forward cross-validation for a trading model.
    """

    def __init__(
        self,
        cv: Optional[PurgedWalkForwardCV] = None,
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
    ):
        self.cv = cv or PurgedWalkForwardCV()
        self.target_col = target_col
        self.valid_col = valid_col

    def validate(
        self,
        model: BaseTradingModel,
        df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
    ) -> WalkForwardValidationReport:
        """
        Executes purged walk-forward cross-validation across all folds.
        Ensures model is refitted cleanly per fold with zero leakage.
        """
        fold_results: List[WalkForwardFoldResult] = []

        acc_list: List[float] = []
        bal_acc_list: List[float] = []
        f1_list: List[float] = []
        win_rate_list: List[float] = []
        total_trades = 0

        for fold_idx, (train_idx, test_idx) in enumerate(self.cv.split(df), 1):
            train_sub = pd.DataFrame(df.iloc[cast(Any, train_idx)])
            test_sub = pd.DataFrame(df.iloc[cast(Any, test_idx)])

            # Refit model cleanly on this fold's training slice
            model.fit(train_sub, target_col=self.target_col, valid_col=self.valid_col)

            # Evaluate out-of-sample on test fold
            eval_res = model.evaluate(
                test_sub,
                target_col=self.target_col,
                valid_col=self.valid_col,
                split_name=f"Fold_{fold_idx}",
            )

            train_start_str = str(train_sub.index[0])
            train_end_str = str(train_sub.index[-1])
            test_start_str = str(test_sub.index[0])
            test_end_str = str(test_sub.index[-1])

            fold_result = WalkForwardFoldResult(
                fold_idx=fold_idx,
                train_start=train_start_str,
                train_end=train_end_str,
                train_count=len(train_sub),
                test_start=test_start_str,
                test_end=test_end_str,
                test_count=len(test_sub),
                evaluation=eval_res,
            )
            fold_results.append(fold_result)

            acc_list.append(eval_res.accuracy)
            bal_acc_list.append(eval_res.balanced_accuracy)
            f1_list.append(eval_res.macro_f1)
            win_rate_list.append(eval_res.directional_win_rate)
            total_trades += eval_res.trade_count

        mean_acc = float(np.mean(acc_list)) if acc_list else 0.0
        std_acc = float(np.std(acc_list)) if acc_list else 0.0

        mean_bal = float(np.mean(bal_acc_list)) if bal_acc_list else 0.0
        std_bal = float(np.std(bal_acc_list)) if bal_acc_list else 0.0

        mean_f1 = float(np.mean(f1_list)) if f1_list else 0.0
        std_f1 = float(np.std(f1_list)) if f1_list else 0.0

        mean_wr = float(np.mean(win_rate_list)) if win_rate_list else 0.0
        std_wr = float(np.std(win_rate_list)) if win_rate_list else 0.0

        return WalkForwardValidationReport(
            model_name=model.name,
            symbol=symbol,
            timeframe=timeframe,
            n_splits=self.cv.n_splits,
            purge_candles=self.cv.purge_candles,
            expanding=self.cv.expanding,
            fold_results=fold_results,
            mean_accuracy=mean_acc,
            std_accuracy=std_acc,
            mean_balanced_accuracy=mean_bal,
            std_balanced_accuracy=std_bal,
            mean_macro_f1=mean_f1,
            std_macro_f1=std_f1,
            mean_win_rate=mean_wr,
            std_win_rate=std_wr,
            total_trades=total_trades,
        )
