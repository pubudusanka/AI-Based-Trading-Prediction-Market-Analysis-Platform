"""
Unit tests for PurgedWalkForwardCV, WalkForwardValidator, and WalkForwardValidationReport.
Reference: Section 21 (Phase 16) of Implementation Plan.

Validates:
- Strict chronological walk-forward splitting
- Purge gap / safety embargo invariant between train and test windows
- Expanding vs Rolling window modes
- Multi-fold out-of-sample validation execution with ML models
- Aggregate metrics and stability reporting
- Edge cases and error handling (insufficient data length)
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

from src.training.validation import (
    PurgedWalkForwardCV,
    WalkForwardValidator,
    WalkForwardValidationReport,
)
from src.training.models import LogisticRegressionModel
from tests.test_eda import create_synthetic_dataset


def test_purged_walk_forward_cv_expanding_leakage_invariants():
    """Verify expanding walk-forward splits enforce chronological ordering and safety purge gap."""
    n = 200
    df = pd.DataFrame({"dummy": np.zeros(n)})
    purge_gap = 10
    n_splits = 4

    cv = PurgedWalkForwardCV(
        n_splits=n_splits,
        purge_candles=purge_gap,
        expanding=True,
        min_train_ratio=0.40,
    )

    splits = list(cv.split(df))
    assert len(splits) == n_splits

    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        assert len(train_idx) > 0
        assert len(test_idx) > 0

        # Expanding window: train always starts at index 0
        assert train_idx[0] == 0

        # Monotonically increasing indices
        assert np.all(np.diff(train_idx) == 1)
        assert np.all(np.diff(test_idx) == 1)

        # STRICT SAFETY INVARIANT: purge gap between train and test
        max_train = train_idx[-1]
        min_test = test_idx[0]
        assert min_test - max_train >= purge_gap

        # Training window must grow in expanding mode
        if fold_idx > 0:
            prev_train_idx, _ = splits[fold_idx - 1]
            assert len(train_idx) > len(prev_train_idx)


def test_purged_walk_forward_cv_rolling():
    """Verify rolling (sliding) window moves train start forward."""
    n = 200
    df = pd.DataFrame({"dummy": np.zeros(n)})
    purge_gap = 8
    n_splits = 3

    cv = PurgedWalkForwardCV(
        n_splits=n_splits,
        purge_candles=purge_gap,
        expanding=False,
        min_train_ratio=0.40,
    )

    splits = list(cv.split(df))
    assert len(splits) == n_splits

    # Later folds should slide train_start forward
    train_starts = [t[0][0] for t in splits]
    assert train_starts[-1] > train_starts[0]

    for train_idx, test_idx in splits:
        assert test_idx[0] - train_idx[-1] >= purge_gap


def test_purged_walk_forward_cv_insufficient_data():
    """Verify ValueError is raised if dataset cannot accommodate splits and purge gap."""
    df = pd.DataFrame({"dummy": np.zeros(30)})
    cv = PurgedWalkForwardCV(n_splits=5, purge_candles=20, min_train_ratio=0.50)

    with pytest.raises(ValueError, match="insufficient"):
        list(cv.split(df))


def test_walk_forward_validator_execution():
    """Verify end-to-end walk-forward execution on synthetic market dataset."""
    df = create_synthetic_dataset(n=250)

    cv = PurgedWalkForwardCV(n_splits=3, purge_candles=15, expanding=True, min_train_ratio=0.40)
    validator = WalkForwardValidator(cv=cv)

    model = LogisticRegressionModel(random_state=42)
    report = validator.validate(model, df, symbol="BTC/USDT", timeframe="15m")

    assert report.model_name == "LogisticRegression"
    assert report.symbol == "BTC/USDT"
    assert report.timeframe == "15m"
    assert len(report.fold_results) == 3
    assert report.n_splits == 3
    assert report.purge_candles == 15

    # Check aggregate statistics
    assert 0.0 <= report.mean_accuracy <= 1.0
    assert 0.0 <= report.mean_balanced_accuracy <= 1.0
    assert 0.0 <= report.mean_macro_f1 <= 1.0

    # Check per-fold evaluation integrity
    for fr in report.fold_results:
        assert fr.train_count > 0
        assert fr.test_count > 0
        assert fr.evaluation.evaluated_samples > 0

    # Test Markdown generation and persistence
    md = report.to_markdown()
    assert "# Walk-Forward Validation Report: LogisticRegression" in md
    assert "Aggregate Out-of-Sample Performance" in md
    assert "Per-Fold Out-of-Sample Leaderboard" in md

    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = os.path.join(tmp_dir, "wf_report.md")
        report.save_markdown(save_path)
        assert os.path.exists(save_path)
        with open(save_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 100
        assert "BTC/USDT" in content
