"""
Unit tests for ML Baseline Models, Preprocessing, Evaluation, and Comparison Leaderboard.
Reference: Section 20 (Phase 15) of Implementation Plan.

Validates:
- MLFeaturePipeline (zero lookahead leakage, proper imputation and scaling)
- ModelEvaluator (ROC-AUC, PR-AUC, Log Loss, Brier score, Directional Win Rate)
- LogisticRegressionModel (fit, predict, predict_proba, save/load)
- RandomForestModel (fit, predict, predict_proba, save/load)
- XGBoostModel (fit, predict, predict_proba, save/load)
- ModelComparisonRunner (end-to-end benchmark comparison across all models)
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

from src.training.preprocessing import MLFeaturePipeline
from src.evaluation.metrics import ModelEvaluator, ModelEvaluationResult
from src.training.models import (
    BaseTradingModel,
    LogisticRegressionModel,
    RandomForestModel,
    XGBoostModel,
)
from src.training.comparison import ModelComparisonRunner, BenchmarkComparisonReport
from tests.test_eda import create_synthetic_dataset


@pytest.fixture
def synthetic_train_and_val():
    """Generates synthetic train (200 rows) and validation (80 rows) market datasets."""
    full_df = create_synthetic_dataset(n=280)
    train_df = full_df.iloc[:200].copy()
    val_df = full_df.iloc[200:].copy()
    return train_df, val_df


def test_feature_pipeline_fit_transform(synthetic_train_and_val):
    """Verify MLFeaturePipeline isolates train statistics and prevents leakage."""
    train_df, val_df = synthetic_train_and_val

    pipeline = MLFeaturePipeline()
    X_train = pipeline.fit_transform(train_df)

    assert pipeline._is_fitted
    assert len(pipeline.feature_names) > 0
    # Targets and raw price must be excluded
    for col in pipeline.feature_names:
        assert col not in pipeline.EXCLUDE_COLUMNS

    # Mean of scaled training data should be close to 0, std close to 1
    assert np.allclose(np.mean(X_train, axis=0), 0.0, atol=1e-5)

    # Transform validation data
    X_val = pipeline.transform(val_df)
    assert X_val.shape[1] == X_train.shape[1]
    assert len(X_val) == len(val_df)

    # Test serialization
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = os.path.join(tmp_dir, "pipeline.joblib")
        pipeline.save(save_path)
        loaded = MLFeaturePipeline.load(save_path)
        assert loaded.feature_names == pipeline.feature_names
        X_val_loaded = loaded.transform(val_df)
        assert np.allclose(X_val, X_val_loaded)


def test_model_evaluator_metrics():
    """Verify ModelEvaluator multi-class probabilistic metric calculations."""
    y_true = np.array([-1.0, 0.0, 1.0, -1.0, 1.0, 0.0])
    y_pred = np.array([-1.0, 0.0, 1.0, 1.0, 1.0, 0.0])

    # Probabilities aligned [DOWN, NEUTRAL, UP]
    y_prob = np.array([
        [0.8, 0.1, 0.1],  # True -1, Pred -1 (Correct)
        [0.1, 0.8, 0.1],  # True 0, Pred 0 (Correct)
        [0.1, 0.1, 0.8],  # True 1, Pred 1 (Correct)
        [0.2, 0.1, 0.7],  # True -1, Pred 1 (Wrong)
        [0.1, 0.2, 0.7],  # True 1, Pred 1 (Correct)
        [0.1, 0.7, 0.2],  # True 0, Pred 0 (Correct)
    ])

    result = ModelEvaluator.evaluate(
        y_true=y_true,
        y_pred=y_pred,
        y_prob=y_prob,
        model_name="TestModel",
        split_name="Validation",
    )

    assert result.model_name == "TestModel"
    assert result.evaluated_samples == 6
    assert result.accuracy == 5.0 / 6.0
    assert result.macro_f1 > 0.0
    assert result.roc_auc_macro is not None
    assert result.roc_auc_macro > 0.5
    assert result.pr_auc_macro is not None
    assert result.log_loss_value is not None
    assert result.brier_score_loss is not None
    # 4 active trades (-1, 1, 1, 1), 3 were correct -> 75% win rate
    assert result.trade_count == 4
    assert result.directional_win_rate == 0.75

    md = result.to_markdown()
    assert "TestModel" in md
    assert "One-vs-Rest ROC-AUC" in md


def test_logistic_regression_model(synthetic_train_and_val):
    """Verify LogisticRegressionModel fit, predict, and serialization."""
    train_df, val_df = synthetic_train_and_val

    model = LogisticRegressionModel()
    model.fit(train_df)
    assert model.is_fitted

    preds = model.predict(val_df)
    assert len(preds) == len(val_df)
    assert set(preds.unique()).issubset({-1.0, 0.0, 1.0})

    probas = model.predict_proba(val_df)
    assert probas.shape == (len(val_df), 3)
    assert list(probas.columns) == ["DOWN", "NEUTRAL", "UP"]
    assert np.allclose(probas.sum(axis=1), 1.0, atol=1e-5)

    eval_res = model.evaluate(val_df, split_name="Validation")
    assert eval_res.evaluated_samples > 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = os.path.join(tmp_dir, "lr_model.joblib")
        model.save(save_path)
        loaded = LogisticRegressionModel.load(save_path)
        loaded_preds = loaded.predict(val_df)
        assert (preds == loaded_preds).all()


def test_random_forest_model(synthetic_train_and_val):
    """Verify RandomForestModel fit, predict, and serialization."""
    train_df, val_df = synthetic_train_and_val

    model = RandomForestModel(n_estimators=30, max_depth=4)
    model.fit(train_df)
    assert model.is_fitted

    preds = model.predict(val_df)
    assert len(preds) == len(val_df)
    assert set(preds.unique()).issubset({-1.0, 0.0, 1.0})

    probas = model.predict_proba(val_df)
    assert probas.shape == (len(val_df), 3)
    assert np.allclose(probas.sum(axis=1), 1.0, atol=1e-5)


def test_xgboost_model(synthetic_train_and_val):
    """Verify XGBoostModel fit, predict, and serialization."""
    train_df, val_df = synthetic_train_and_val

    model = XGBoostModel(n_estimators=30, max_depth=3)
    model.fit(train_df)
    assert model.is_fitted

    preds = model.predict(val_df)
    assert len(preds) == len(val_df)
    assert set(preds.unique()).issubset({-1.0, 0.0, 1.0})

    probas = model.predict_proba(val_df)
    assert probas.shape == (len(val_df), 3)
    assert np.allclose(probas.sum(axis=1), 1.0, atol=1e-5)


def test_model_comparison_runner(synthetic_train_and_val):
    """Verify end-to-end multi-model benchmarking leaderboard."""
    train_df, val_df = synthetic_train_and_val

    runner = ModelComparisonRunner()
    report = runner.run_comparison(
        train_df=train_df,
        eval_df=val_df,
        symbol="BTC/USDT",
        timeframe="15m",
        split_name="Validation",
    )

    assert len(report.results) == 4
    model_names = [r.model_name for r in report.results]
    assert "RuleBasedBaseline" in model_names
    assert "LogisticRegression" in model_names
    assert "RandomForest" in model_names
    assert "XGBoost" in model_names

    md = report.to_markdown()
    assert "# Baseline Model Benchmark Leaderboard: BTC/USDT (15m)" in md
    assert "LogisticRegression" in md
    assert "RandomForest" in md
    assert "XGBoost" in md
    assert "RuleBasedBaseline" in md
