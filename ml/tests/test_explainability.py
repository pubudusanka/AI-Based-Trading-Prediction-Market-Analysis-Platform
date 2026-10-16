"""
Unit tests for FeatureImportanceEngine and Explainability Reporting (Phase 18).
Reference: Section 23 of Implementation Plan.

Validates:
- Native tree/model feature importance ranking (RandomForest, XGBoost, LogisticRegression)
- Out-of-sample permutation importance with zero lookahead
- SHAP TreeExplainer feature importance and sample explanations
- Single-candle prediction explanation formatting (CLI and JSON contracts)
- Comprehensive Markdown report generation and causality disclaimer enforcement
"""

import sys
import os
import tempfile
import numpy as np
import pandas as pd
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(ML_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from src.training.models import RandomForestModel, XGBoostModel, LogisticRegressionModel
from src.evaluation.explainability import (
    FeatureImportanceEngine,
    FeatureImportanceItem,
    PredictionFactorExplanation,
    SinglePredictionExplanation,
    FeatureImportanceReport,
    CAUSALITY_DISCLAIMER,
)
from tests.test_eda import create_synthetic_dataset


@pytest.fixture
def dataset_splits():
    df = create_synthetic_dataset(n=250)
    train_df = df.iloc[:160].copy()
    test_df = df.iloc[160:].copy()
    return train_df, test_df


def test_native_model_importance(dataset_splits):
    train_df, _ = dataset_splits

    # 1. Random Forest
    rf = RandomForestModel(n_estimators=20, max_depth=4, random_state=42)
    rf.fit(train_df)
    rf_items = FeatureImportanceEngine.compute_model_importance(rf)
    assert len(rf_items) > 0
    assert rf_items[0].rank == 1
    assert rf_items[0].importance_score >= rf_items[-1].importance_score
    total_pct = sum(item.relative_weight_pct for item in rf_items)
    assert np.isclose(total_pct, 100.0, atol=1e-2)

    # 2. XGBoost
    xgb = XGBoostModel(n_estimators=20, max_depth=3, random_state=42)
    xgb.fit(train_df)
    xgb_items = FeatureImportanceEngine.compute_model_importance(xgb)
    assert len(xgb_items) > 0
    assert xgb_items[0].rank == 1

    # 3. Logistic Regression
    lr = LogisticRegressionModel(c_param=0.1, random_state=42)
    lr.fit(train_df)
    lr_items = FeatureImportanceEngine.compute_model_importance(lr)
    assert len(lr_items) > 0
    assert lr_items[0].importance_score >= lr_items[-1].importance_score


def test_permutation_importance_out_of_sample(dataset_splits):
    train_df, test_df = dataset_splits

    rf = RandomForestModel(n_estimators=30, max_depth=4, random_state=42)
    rf.fit(train_df)

    # Evaluated strictly on test partition
    perm_items = FeatureImportanceEngine.compute_permutation_importance(
        model=rf,
        eval_df=test_df,
        n_repeats=3,
        random_state=42,
    )

    assert len(perm_items) > 0
    assert perm_items[0].rank == 1
    # Check ranking order (descending by drop)
    for i in range(len(perm_items) - 1):
        assert perm_items[i].importance_score >= perm_items[i + 1].importance_score


def test_shap_importance_and_global_ranking(dataset_splits):
    train_df, test_df = dataset_splits

    rf = RandomForestModel(n_estimators=20, max_depth=4, random_state=42)
    rf.fit(train_df)

    shap_items = FeatureImportanceEngine.compute_shap_importance(
        model=rf,
        sample_df=test_df,
        max_samples=50,
        random_state=42,
    )

    assert len(shap_items) > 0
    assert shap_items[0].rank == 1
    assert shap_items[0].importance_score >= 0.0


def test_single_prediction_explanation_cli_and_json(dataset_splits):
    train_df, test_df = dataset_splits

    rf = RandomForestModel(n_estimators=20, max_depth=4, random_state=42)
    rf.fit(train_df)

    # Test with single candle series
    sample_candle = test_df.iloc[-1]
    explanation = FeatureImportanceEngine.explain_prediction(
        model=rf,
        candle_features=sample_candle,
        symbol="BTC/USDT",
        timeframe="15m",
        top_k=5,
    )

    assert explanation.symbol == "BTC/USDT"
    assert explanation.timeframe == "15m"
    assert explanation.predicted_class in ["UP", "DOWN", "NEUTRAL"]
    assert 0.0 <= explanation.predicted_probability <= 1.0
    assert len(explanation.top_factors) <= 5
    assert explanation.disclaimer == CAUSALITY_DISCLAIMER

    # Test CLI output formatting matching Section 23
    cli_text = explanation.format_cli()
    assert f"Prediction: {explanation.predicted_class}" in cli_text
    assert "Important factors:" in cli_text
    assert "1. " in cli_text

    # Test JSON dictionary schema
    json_data = explanation.to_dict()
    assert json_data["prediction"] == explanation.predicted_class
    assert "top_factors" in json_data
    assert len(json_data["top_factors"]) > 0
    assert "impact" in json_data["top_factors"][0]


def test_feature_importance_report_markdown_and_persistence(dataset_splits):
    train_df, test_df = dataset_splits

    rf = RandomForestModel(n_estimators=20, max_depth=4, random_state=42)
    rf.fit(train_df)

    report = FeatureImportanceEngine.generate_full_audit(
        model=rf,
        eval_df=test_df,
        symbol="BTC/USDT",
        timeframe="15m",
        n_repeats=2,
        random_state=42,
    )

    assert report.model_name == "RandomForest"
    assert len(report.native_importance) > 0
    assert len(report.permutation_importance) > 0
    assert report.example_explanation is not None

    md = report.to_markdown()
    assert "# Feature Importance & Model Explainability Report: RandomForest" in md
    assert "Causality Notice:" in md
    assert "Native Model Feature Importance" in md
    assert "Out-of-Sample Permutation Feature Importance" in md
    assert "Single-Prediction Real-Time Attribution Example" in md

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "test_report.md")
        saved = report.save_markdown(report_path)
        assert os.path.exists(saved)
        with open(saved, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 500
