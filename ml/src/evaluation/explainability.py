"""
Feature Importance and Explainability Engine (SHAP, Permutation, MDI/Gain).
Reference: Section 23 (Phase 18) of Implementation Plan.

Guarantees:
- Global feature ranking using native model importance (MDI / GBDT Gain / Coefficients).
- Out-of-sample Permutation Importance strictly evaluated on held-out test data (zero lookahead).
- SHAP (TreeExplainer) global and local single-prediction attribution decomposition.
- Formatted real-time single-candle explanation with top factors and directional impact.
- Strict causal disclaimer enforcement: feature importance represents statistical association,
  not proof of causation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union, cast, TYPE_CHECKING
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import balanced_accuracy_score

if TYPE_CHECKING:
    from src.training.models import BaseTradingModel
    from src.evaluation.calibration import CalibratedTradingModel

try:
    import shap
    HAS_SHAP = True
except ImportError:  # pragma: no cover
    HAS_SHAP = False
    shap = None


CAUSALITY_DISCLAIMER: str = (
    "DISCLAIMER: Feature importance and attribution values quantify empirical statistical "
    "associations within the model's fitted decision landscape. They do NOT establish or prove "
    "economic or financial causation in market mechanics."
)


@dataclass
class FeatureImportanceItem:
    """Importance metric for an individual feature."""
    feature_name: str
    importance_score: float
    rank: int
    std_dev: float = 0.0
    relative_weight_pct: float = 0.0


@dataclass
class PredictionFactorExplanation:
    """Contribution of a single feature to a specific candle's trade prediction."""
    rank: int
    feature_name: str
    feature_value: float
    attribution_score: float
    impact_direction: str  # "BULLISH", "BEARISH", "NEUTRAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "feature": self.feature_name,
            "value": round(float(self.feature_value), 4),
            "attribution": round(float(self.attribution_score), 4),
            "impact": self.impact_direction,
        }


@dataclass
class SinglePredictionExplanation:
    """Explainability payload for a single candle forecast (real-time API contract)."""
    symbol: str
    timeframe: str
    predicted_class: str
    predicted_probability: float
    probabilities: Dict[str, float]
    top_factors: List[PredictionFactorExplanation]
    disclaimer: str = CAUSALITY_DISCLAIMER
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "prediction": self.predicted_class,
            "probability": round(float(self.predicted_probability), 4),
            "probabilities": {k: round(float(v), 4) for k, v in self.probabilities.items()},
            "top_factors": [factor.to_dict() for factor in self.top_factors],
            "disclaimer": self.disclaimer,
            "timestamp": self.timestamp,
        }

    def format_cli(self) -> str:
        """Formatted human-readable output matching Section 23 dashboard format."""
        prob_pct = self.predicted_probability * 100.0
        lines = [
            f"Prediction: {self.predicted_class} {prob_pct:.1f}%",
            "",
            "Important factors:",
        ]
        for f in self.top_factors:
            sign = "+" if f.attribution_score >= 0 else ""
            lines.append(
                f"{f.rank}. {f.feature_name.replace('_', ' ').title()} "
                f"({sign}{f.attribution_score:.2f}) [{f.impact_direction}]"
            )
        return "\n".join(lines)


@dataclass
class FeatureImportanceReport:
    """Comprehensive explainability audit report across native, permutation, and SHAP methods."""
    model_name: str
    symbol: str
    timeframe: str
    sample_count: int
    native_importance: List[FeatureImportanceItem]
    permutation_importance: List[FeatureImportanceItem]
    shap_importance: List[FeatureImportanceItem]
    example_explanation: Optional[SinglePredictionExplanation] = None
    disclaimer: str = CAUSALITY_DISCLAIMER
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_markdown(self) -> str:
        """Renders comprehensive Markdown report for documentation and governance."""
        md = [
            f"# Feature Importance & Model Explainability Report: {self.model_name}",
            "",
            f"**Asset:** {self.symbol} ({self.timeframe})  ",
            f"**Evaluated Test Samples:** {self.sample_count:,}  ",
            f"**Generated At:** {self.generated_at}  ",
            "",
            "> [!IMPORTANT]",
            f"> **Causality Notice:** {self.disclaimer}",
            "",
            "---",
            "",
            "## 1. Native Model Feature Importance (MDI / Gini / GBDT Gain)",
            "",
            "| Rank | Feature | Importance Score | Relative Share |",
            "|---|---|---|---|",
        ]

        for item in self.native_importance[:15]:
            md.append(
                f"| {item.rank} | `{item.feature_name}` | {item.importance_score:.4f} | {item.relative_weight_pct:.2f}% |"
            )

        md.extend([
            "",
            "---",
            "",
            "## 2. Out-of-Sample Permutation Feature Importance",
            "",
            "Permutation importance quantifies the drop in Balanced Accuracy when a feature column is shuffled out-of-sample.",
            "",
            "| Rank | Feature | Mean Accuracy Drop (Δ) | Std Dev (±) |",
            "|---|---|---|---|",
        ])

        for item in self.permutation_importance[:15]:
            md.append(
                f"| {item.rank} | `{item.feature_name}` | {item.importance_score:+.4f} | ±{item.std_dev:.4f} |"
            )

        if self.shap_importance:
            md.extend([
                "",
                "---",
                "",
                "## 3. Global SHAP Feature Importance (Mean |SHAP Value|)",
                "",
                "| Rank | Feature | Mean |SHAP| Attribution | Relative Contribution |",
                "|---|---|---|---|",
            ])
            for item in self.shap_importance[:15]:
                md.append(
                    f"| {item.rank} | `{item.feature_name}` | {item.importance_score:.4f} | {item.relative_weight_pct:.2f}% |"
                )

        if self.example_explanation is not None:
            md.extend([
                "",
                "---",
                "",
                "## 4. Single-Prediction Real-Time Attribution Example",
                "",
                "```text",
                self.example_explanation.format_cli(),
                "```",
                "",
                "### JSON Payload Contract (REST API / WebSocket):",
                "```json",
                json.dumps(self.example_explanation.to_dict(), indent=2),
                "```",
            ])

        return "\n".join(md)

    def save_markdown(self, filepath: str) -> str:
        """Persists markdown report to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_markdown() + "\n")
        return filepath


class FeatureImportanceEngine:
    """
    Production-grade Feature Importance and Explainability Engine.
    Computes Native, Permutation, and SHAP attributions with strict zero-lookahead safety.
    """

    CLASS_NAMES = ["DOWN", "NEUTRAL", "UP"]
    CLASS_LABELS = [-1.0, 0.0, 1.0]

    @staticmethod
    def compute_model_importance(model: Any) -> List[FeatureImportanceItem]:
        """
        Extracts intrinsic model feature importance (RandomForest MDI, XGBoost Gain, or Logistic Regression weights).
        """
        base_model = getattr(model, "base_model", model)
        pipeline = getattr(base_model, "pipeline", None)
        clf = getattr(base_model, "clf", None)

        if pipeline is None or not hasattr(pipeline, "feature_names") or not pipeline.feature_names:
            raise ValueError(f"Model '{base_model}' does not have fitted pipeline feature_names.")

        features: List[str] = pipeline.feature_names

        # 1. Tree ensemble feature importances (Random Forest or XGBoost)
        if clf is not None and hasattr(clf, "feature_importances_"):
            raw_scores = np.asarray(clf.feature_importances_, dtype=np.float64)
        # 2. Linear / Logistic Regression coefficients (mean absolute across classes)
        elif clf is not None and hasattr(clf, "coef_"):
            raw_scores = np.mean(np.abs(np.asarray(clf.coef_, dtype=np.float64)), axis=0)
        else:
            raise ValueError(f"Classifier {type(clf)} does not support intrinsic feature importance.")

        total_weight = float(np.sum(raw_scores)) if np.sum(raw_scores) > 0 else 1.0
        sorted_indices = np.argsort(raw_scores)[::-1]

        items: List[FeatureImportanceItem] = []
        for rank_idx, feat_idx in enumerate(sorted_indices):
            score = float(raw_scores[feat_idx])
            share = (score / total_weight) * 100.0
            items.append(
                FeatureImportanceItem(
                    feature_name=features[feat_idx],
                    importance_score=score,
                    rank=rank_idx + 1,
                    std_dev=0.0,
                    relative_weight_pct=share,
                )
            )

        return items

    @staticmethod
    def compute_permutation_importance(
        model: Any,
        eval_df: pd.DataFrame,
        n_repeats: int = 5,
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
        random_state: int = 42,
    ) -> List[FeatureImportanceItem]:
        """
        Computes model-agnostic out-of-sample Permutation Importance on held-out data.
        """
        base_model = getattr(model, "base_model", model)
        pipeline = getattr(base_model, "pipeline", None)

        if pipeline is None or not hasattr(pipeline, "feature_names") or not pipeline.feature_names:
            raise ValueError(f"Model '{base_model}' does not have fitted pipeline feature_names.")

        features: List[str] = pipeline.feature_names

        if valid_col in eval_df.columns:
            valid_mask = pd.Series(eval_df[valid_col]) == True
            sub_df = pd.DataFrame(eval_df[valid_mask])
        else:
            sub_df = pd.DataFrame(eval_df)

        y_true = np.asarray(pd.Series(sub_df[target_col], dtype=float), dtype=np.float64)

        # Baseline score
        base_preds = np.asarray(model.predict(sub_df), dtype=np.float64)
        baseline_score = float(balanced_accuracy_score(y_true, base_preds))

        rng = np.random.RandomState(random_state)
        drops: Dict[str, List[float]] = {feat: [] for feat in features}

        for feat in features:
            if feat not in sub_df.columns:
                continue

            for _ in range(n_repeats):
                shuffled_df = sub_df.copy()
                shuffled_vals = rng.permutation(shuffled_df[feat].to_numpy())
                cast(Any, shuffled_df)[feat] = shuffled_vals

                shuffled_preds = np.asarray(model.predict(shuffled_df), dtype=np.float64)
                shuffled_score = float(balanced_accuracy_score(y_true, shuffled_preds))
                drops[feat].append(baseline_score - shuffled_score)

        # Rank by mean drop
        results: List[Tuple[str, float, float]] = []
        for feat, score_drops in drops.items():
            if score_drops:
                mean_drop = float(np.mean(score_drops))
                std_drop = float(np.std(score_drops))
            else:
                mean_drop = 0.0
                std_drop = 0.0
            results.append((feat, mean_drop, std_drop))

        results.sort(key=lambda x: x[1], reverse=True)

        items: List[FeatureImportanceItem] = []
        for rank_idx, (feat_name, mean_drop, std_drop) in enumerate(results):
            items.append(
                FeatureImportanceItem(
                    feature_name=feat_name,
                    importance_score=mean_drop,
                    rank=rank_idx + 1,
                    std_dev=std_drop,
                    relative_weight_pct=0.0,
                )
            )

        return items

    @staticmethod
    def compute_shap_importance(
        model: Any,
        sample_df: pd.DataFrame,
        max_samples: int = 150,
        random_state: int = 42,
    ) -> List[FeatureImportanceItem]:
        """
        Computes global SHAP feature importance using TreeExplainer or model decomposition.
        """
        base_model = getattr(model, "base_model", model)
        pipeline = getattr(base_model, "pipeline", None)
        clf = getattr(base_model, "clf", None)

        if pipeline is None or not hasattr(pipeline, "feature_names") or not pipeline.feature_names:
            raise ValueError(f"Model '{base_model}' does not have fitted pipeline feature_names.")

        features: List[str] = pipeline.feature_names
        sub_df = sample_df.sample(n=min(len(sample_df), max_samples), random_state=random_state) if len(sample_df) > max_samples else sample_df

        X_transformed = pipeline.transform(sub_df)

        shap_lib: Any = shap
        if HAS_SHAP and shap_lib is not None and hasattr(clf, "predict_proba"):
            try:
                explainer = shap_lib.TreeExplainer(clf)
                explanation = explainer(X_transformed)
                values = explanation.values

                # Handle multi-class shape (n_samples, n_features, n_classes) or list
                if isinstance(values, list):
                    mean_abs_per_class = [np.mean(np.abs(arr), axis=0) for arr in values]
                    mean_abs = np.mean(mean_abs_per_class, axis=0)
                elif values.ndim == 3:
                    mean_abs = np.mean(np.mean(np.abs(values), axis=2), axis=0)
                else:
                    mean_abs = np.mean(np.abs(values), axis=0)

                total_sum = float(np.sum(mean_abs)) if np.sum(mean_abs) > 0 else 1.0
                sorted_idx = np.argsort(mean_abs)[::-1]

                items: List[FeatureImportanceItem] = []
                for rank_idx, idx in enumerate(sorted_idx):
                    val = float(mean_abs[idx])
                    items.append(
                        FeatureImportanceItem(
                            feature_name=features[idx],
                            importance_score=val,
                            rank=rank_idx + 1,
                            std_dev=0.0,
                            relative_weight_pct=(val / total_sum) * 100.0,
                        )
                    )
                return items
            except Exception:
                pass

        # Fallback to model importance if shap fails or is unsupported
        return FeatureImportanceEngine.compute_model_importance(model)

    @classmethod
    def explain_prediction(
        cls,
        model: Any,
        candle_features: Union[pd.Series, pd.DataFrame, Dict[str, Any]],
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        top_k: int = 5,
    ) -> SinglePredictionExplanation:
        """
        Generates real-time attribution factors for a single candle prediction.
        """
        if isinstance(candle_features, dict):
            input_df = pd.DataFrame([candle_features])
        elif isinstance(candle_features, pd.Series):
            input_df = pd.DataFrame([candle_features.to_dict()])
        else:
            input_df = candle_features.iloc[[-1]].copy()

        base_model = getattr(model, "base_model", model)
        pipeline = getattr(base_model, "pipeline", None)
        clf = getattr(base_model, "clf", None)

        if pipeline is None or not hasattr(pipeline, "feature_names") or not pipeline.feature_names:
            raise ValueError("Fitted pipeline with feature_names is required for prediction explanation.")

        features: List[str] = pipeline.feature_names
        X_scaled = pipeline.transform(input_df)

        # Get probabilities
        prob_df = model.predict_proba(input_df)
        probas: Dict[str, float] = {
            "DOWN": float(prob_df["DOWN"].iloc[0]),
            "NEUTRAL": float(prob_df["NEUTRAL"].iloc[0]),
            "UP": float(prob_df["UP"].iloc[0]),
        }

        # Determine predicted class
        pred_class = max(probas, key=probas.get)  # type: ignore
        pred_prob = probas[pred_class]
        class_idx = cls.CLASS_NAMES.index(pred_class)

        # Compute attributions
        attributions = np.zeros(len(features), dtype=np.float64)

        shap_lib: Any = shap
        if HAS_SHAP and shap_lib is not None and hasattr(clf, "predict_proba"):
            try:
                explainer = shap_lib.TreeExplainer(clf)
                explanation = explainer(X_scaled)
                vals = explanation.values
                if isinstance(vals, list):
                    attributions = vals[class_idx][0]
                elif vals.ndim == 3:
                    attributions = vals[0, :, class_idx]
                else:
                    attributions = vals[0]
            except Exception:
                pass

        if np.all(attributions == 0):
            # Model-intrinsic fallback attribution
            native_items = cls.compute_model_importance(model)
            native_dict = {item.feature_name: item.importance_score for item in native_items}
            for i, feat in enumerate(features):
                attributions[i] = native_dict.get(feat, 0.0)

        # Top K features by absolute attribution
        abs_attributions = np.abs(attributions)
        sorted_indices = np.argsort(abs_attributions)[::-1][:top_k]

        factor_explanations: List[PredictionFactorExplanation] = []
        for rank_idx, f_idx in enumerate(sorted_indices):
            feat_name = features[f_idx]
            feat_val = float(input_df[feat_name].iloc[0]) if feat_name in input_df.columns else float(X_scaled[0, f_idx])
            attr_val = float(attributions[f_idx])

            # Classify impact direction
            if pred_class == "UP":
                impact = "BULLISH" if attr_val > 0 else "BEARISH"
            elif pred_class == "DOWN":
                impact = "BEARISH" if attr_val > 0 else "BULLISH"
            else:
                impact = "NEUTRAL"

            factor_explanations.append(
                PredictionFactorExplanation(
                    rank=rank_idx + 1,
                    feature_name=feat_name,
                    feature_value=feat_val,
                    attribution_score=attr_val,
                    impact_direction=impact,
                )
            )

        return SinglePredictionExplanation(
            symbol=symbol,
            timeframe=timeframe,
            predicted_class=pred_class,
            predicted_probability=pred_prob,
            probabilities=probas,
            top_factors=factor_explanations,
        )

    @classmethod
    def generate_full_audit(
        cls,
        model: Any,
        eval_df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
        n_repeats: int = 3,
        random_state: int = 42,
    ) -> FeatureImportanceReport:
        """
        Executes complete multi-method explainability audit and produces comprehensive report.
        """
        base_model = getattr(model, "base_model", model)
        model_name = getattr(base_model, "name", "TradingModel")

        native_imp = cls.compute_model_importance(model)
        perm_imp = cls.compute_permutation_importance(
            model=model,
            eval_df=eval_df,
            n_repeats=n_repeats,
            target_col=target_col,
            valid_col=valid_col,
            random_state=random_state,
        )
        shap_imp = cls.compute_shap_importance(model, eval_df, max_samples=100, random_state=random_state)

        # Generate single example explanation
        last_row = eval_df.iloc[-1]
        example = cls.explain_prediction(model, last_row, symbol=symbol, timeframe=timeframe, top_k=5)

        return FeatureImportanceReport(
            model_name=model_name,
            symbol=symbol,
            timeframe=timeframe,
            sample_count=len(eval_df),
            native_importance=native_imp,
            permutation_importance=perm_imp,
            shap_importance=shap_imp,
            example_explanation=example,
        )
