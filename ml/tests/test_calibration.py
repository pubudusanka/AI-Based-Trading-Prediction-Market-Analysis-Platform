"""
Unit tests for ProbabilityCalibrator, CalibratedTradingModel, and Reliability Curves.
Reference: Section 22 (Phase 17) of Implementation Plan.

Validates:
- Sigmoid (Platt) and Isotonic calibration algorithms
- Expected Calibration Error (ECE), MCE, and Brier Score calculations
- Row-wise probability normalization (sum to 1.0)
- Single-candle prediction dictionary schema: {"UP": float, "DOWN": float, "NEUTRAL": float}
- End-to-end fit_and_calibrate workflow on train and validation datasets
- Serialization and persistence roundtrip
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

from src.evaluation.calibration import (
    ProbabilityCalibrator,
    CalibratedTradingModel,
    CalibrationAuditReport,
)
from src.training.models import LogisticRegressionModel, RandomForestModel
from tests.test_eda import create_synthetic_dataset


@pytest.fixture
def train_and_val_data():
    """Generates synthetic dataset and splits into train (200) and val (100)."""
    full_df = create_synthetic_dataset(n=300)
    train_df = full_df.iloc[:200].copy()
    val_df = full_df.iloc[200:].copy()
    return train_df, val_df


def test_probability_calibrator_sigmoid():
    """Verify ProbabilityCalibrator with Platt sigmoid scaling."""
    np.random.seed(42)
    n = 100
    # Synthetic uncalibrated overconfident probabilities
    raw_p = np.random.dirichlet([1, 1, 1], size=n)
    y_true = np.random.choice([-1.0, 0.0, 1.0], size=n)

    calibrator = ProbabilityCalibrator(method="sigmoid", n_bins=5)
    calibrator.fit(raw_p, y_true)
    assert calibrator.is_fitted

    calibrated = calibrator.calibrate(raw_p)
    assert calibrated.shape == (n, 3)
    # Check row-wise normalization
    assert np.allclose(calibrated.sum(axis=1), 1.0, atol=1e-5)
    assert (calibrated >= 0.0).all() and (calibrated <= 1.0).all()


def test_probability_calibrator_isotonic():
    """Verify ProbabilityCalibrator with Isotonic regression."""
    np.random.seed(42)
    n = 100
    raw_p = np.random.dirichlet([1, 1, 1], size=n)
    y_true = np.random.choice([-1.0, 0.0, 1.0], size=n)

    calibrator = ProbabilityCalibrator(method="isotonic", n_bins=5)
    calibrator.fit(raw_p, y_true)
    assert calibrator.is_fitted

    calibrated = calibrator.calibrate(raw_p)
    assert calibrated.shape == (n, 3)
    assert np.allclose(calibrated.sum(axis=1), 1.0, atol=1e-5)


def test_reliability_curve_and_ece():
    """Verify calculation of Expected Calibration Error and reliability bins."""
    y_prob_col = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    y_true_binary = np.array([0, 0, 1, 1, 1, 1])

    ece, mce, bins = ProbabilityCalibrator.compute_reliability_curve(y_prob_col, y_true_binary, n_bins=5)

    assert 0.0 <= ece <= 1.0
    assert 0.0 <= mce <= 1.0
    assert len(bins) > 0
    for b in bins:
        assert 0.0 <= b.mean_predicted <= 1.0
        assert 0.0 <= b.empirical_frequency <= 1.0
        assert b.sample_count > 0


def test_calibrated_trading_model_end_to_end(train_and_val_data):
    """Verify CalibratedTradingModel fit, calibration, and prediction dictionary format."""
    train_df, val_df = train_and_val_data

    base_model = LogisticRegressionModel(random_state=42)
    cal_model = CalibratedTradingModel(base_model=base_model, method="sigmoid")

    cal_model.fit_and_calibrate(train_df, val_df)
    assert cal_model.is_calibrated

    # Test predict_proba
    probas = cal_model.predict_proba(val_df)
    assert probas.shape == (len(val_df), 3)
    assert list(probas.columns) == ["DOWN", "NEUTRAL", "UP"]
    assert np.allclose(probas.sum(axis=1), 1.0, atol=1e-5)

    # Test predict
    preds = cal_model.predict(val_df)
    assert len(preds) == len(val_df)
    assert set(preds.unique()).issubset({-1.0, 0.0, 1.0})

    # Test single candle prediction dictionary schema
    single_candle = val_df.iloc[-1]
    prob_dict = cal_model.predict_single_dict(single_candle)

    assert "UP" in prob_dict
    assert "DOWN" in prob_dict
    assert "NEUTRAL" in prob_dict
    assert isinstance(prob_dict["UP"], float)
    assert isinstance(prob_dict["DOWN"], float)
    assert isinstance(prob_dict["NEUTRAL"], float)
    # Sum should be very close to 1.0 (with 4-decimal round tolerance)
    assert abs(sum(prob_dict.values()) - 1.0) < 0.01

    # Test calibration audit report
    audit_report = cal_model.audit_calibration(val_df, symbol="BTC/USDT", timeframe="15m")
    assert audit_report.evaluated_samples > 0
    assert 0.0 <= audit_report.mean_ece_calibrated <= 1.0
    assert 0.0 <= audit_report.brier_score_calibrated <= 1.0

    md = audit_report.to_markdown()
    assert "# Probability Calibration Report: LogisticRegression" in md
    assert "Expected Calibration Error (ECE)" in md


def test_calibrated_trading_model_serialization(train_and_val_data):
    """Verify saving and loading of calibrated model."""
    train_df, val_df = train_and_val_data

    base_model = RandomForestModel(n_estimators=30, max_depth=3, random_state=42)
    cal_model = CalibratedTradingModel(base_model=base_model, method="sigmoid")
    cal_model.fit_and_calibrate(train_df, val_df)

    preds_orig = cal_model.predict(val_df)

    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = os.path.join(tmp_dir, "calibrated_model.joblib")
        cal_model.save(save_path)
        loaded = CalibratedTradingModel.load(save_path)
        assert loaded.is_calibrated
        preds_loaded = loaded.predict(val_df)
        assert (preds_orig == preds_loaded).all()
