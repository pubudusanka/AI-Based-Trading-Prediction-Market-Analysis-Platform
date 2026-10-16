"""
Model Comparison and Benchmark Leaderboard Framework.
Reference: Section 20 (Phase 15) and Section 44 (Phase 39) of Implementation Plan.

Trains and compares:
1. Rule-based Baseline Strategy (Phase 14)
2. Logistic Regression (Phase 15 - Model 1)
3. Random Forest (Phase 15 - Model 2)
4. XGBoost (Phase 15 - Model 3)

Produces a unified comparative leaderboard across:
- Multi-class classification metrics (Accuracy, Balanced Accuracy, Macro F1, ROC-AUC, PR-AUC, Log Loss)
- Trading performance metrics (Directional Win Rate, Signal Frequency, Trade Count)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from src.training.baseline import RuleBasedBaselineStrategy, BaselineStrategy
from src.training.models import (
    BaseTradingModel,
    LogisticRegressionModel,
    RandomForestModel,
    XGBoostModel,
)
from src.evaluation.metrics import ModelEvaluator, ModelEvaluationResult


@dataclass
class BenchmarkComparisonReport:
    """Summary leaderboard comparing ML models and rule-based baselines."""
    split_name: str
    symbol: str
    timeframe: str
    total_eval_samples: int
    results: List[ModelEvaluationResult]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_markdown(self) -> str:
        """Renders comprehensive Markdown leaderboard comparison."""
        md = [
            f"# Baseline Model Benchmark Leaderboard: {self.symbol} ({self.timeframe})",
            "",
            f"**Evaluation Split:** {self.split_name}  ",
            f"**Total Evaluated Samples:** {self.total_eval_samples:,}  ",
            f"**Generated At:** {self.generated_at}  ",
            "",
            "---",
            "",
            "## 1. Model Comparison Leaderboard",
            "",
            "| Rank | Model Name | Balanced Acc | Macro F1 | ROC-AUC | PR-AUC | Log Loss | Win Rate | Trades |",
            "|---|---|---|---|---|---|---|---|---|",
        ]

        # Sort models by Macro F1 descending
        sorted_results = sorted(self.results, key=lambda r: r.macro_f1, reverse=True)

        for rank, res in enumerate(sorted_results, 1):
            roc_str = f"{res.roc_auc_macro:.4f}" if (res.roc_auc_macro is not None and not np.isnan(res.roc_auc_macro)) else "N/A"
            pr_str = f"{res.pr_auc_macro:.4f}" if (res.pr_auc_macro is not None and not np.isnan(res.pr_auc_macro)) else "N/A"
            ll_str = f"{res.log_loss_value:.4f}" if (res.log_loss_value is not None and not np.isnan(res.log_loss_value)) else "N/A"

            md.append(
                f"| {rank} | **{res.model_name}** | {res.balanced_accuracy * 100:.2f}% | "
                f"{res.macro_f1:.4f} | {roc_str} | {pr_str} | {ll_str} | "
                f"{res.directional_win_rate * 100:.2f}% | {res.trade_count:,} |"
            )

        md.extend([
            "",
            "---",
            "",
            "## 2. Detailed Per-Class Breakdown",
            "",
            "| Model Name | Class | Precision | Recall | F1-Score | Support |",
            "|---|---|---|---|---|---|",
        ])

        for res in sorted_results:
            for cls_name in ["DOWN", "NEUTRAL", "UP"]:
                p = res.precision_per_class.get(cls_name, 0.0) * 100.0
                r = res.recall_per_class.get(cls_name, 0.0) * 100.0
                f1 = res.f1_per_class.get(cls_name, 0.0)
                md.append(f"| {res.model_name} | **{cls_name}** | {p:.2f}% | {r:.2f}% | {f1:.4f} | - |")

        return "\n".join(md)

    def save_markdown(self, filepath: str) -> str:
        """Saves benchmark leaderboard to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        content = self.to_markdown()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath


class ModelComparisonRunner:
    """
    Orchestrates training and comparative evaluation across all baseline models.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def run_comparison(
        self,
        train_df: pd.DataFrame,
        eval_df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        split_name: str = "Validation",
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
    ) -> BenchmarkComparisonReport:
        """
        Fits ML models on train_df and evaluates all candidates on eval_df.
        """
        results: List[ModelEvaluationResult] = []

        # 1. Rule-Based Technical Baseline (Phase 14)
        rule_strategy = RuleBasedBaselineStrategy()
        rule_preds = rule_strategy.predict(eval_df)
        rule_proba = rule_strategy.predict_proba(eval_df)
        y_eval = pd.Series(eval_df[target_col], dtype=float)

        rule_res = ModelEvaluator.evaluate(
            y_true=y_eval,
            y_pred=rule_preds,
            y_prob=rule_proba,
            model_name="RuleBasedBaseline",
            split_name=split_name,
            total_samples=len(eval_df),
        )
        results.append(rule_res)

        # 2. ML Models
        ml_models: List[BaseTradingModel] = [
            LogisticRegressionModel(random_state=self.random_state),
            RandomForestModel(random_state=self.random_state),
            XGBoostModel(random_state=self.random_state),
        ]

        for model in ml_models:
            # Fit strictly on train partition
            model.fit(train_df, target_col=target_col, valid_col=valid_col)

            # Evaluate on out-of-sample evaluation partition
            res = model.evaluate(
                eval_df,
                target_col=target_col,
                valid_col=valid_col,
                split_name=split_name,
            )
            results.append(res)

        return BenchmarkComparisonReport(
            split_name=split_name,
            symbol=symbol,
            timeframe=timeframe,
            total_eval_samples=len(eval_df),
            results=results,
        )
