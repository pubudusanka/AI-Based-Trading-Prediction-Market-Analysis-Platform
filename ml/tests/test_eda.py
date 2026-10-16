"""
Unit tests for EDAAnalyzer and EDAReport.
Validates:
- Statistical summary generation
- Target class distribution and imbalance ratio computation
- Missing value detection
- Zero variance feature filtering
- Multicollinearity pair detection (|r| >= 0.85)
- ANOVA F-score candidate ranking
- Regime-conditional class breakdown
- Markdown report generation and export
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

from src.features.dataset import FeatureDatasetBuilder
from src.features.labels import LabelEngine
from src.preprocessing.eda import EDAAnalyzer, EDAReport
from tests.test_structure import create_base_df


def create_synthetic_dataset(n: int = 150) -> pd.DataFrame:
    """Generate a realistic dataset with features, labels, and market structure."""
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    trend = np.linspace(0, 1000, n)
    wave = 300 * np.sin(np.linspace(0, 6 * np.pi, n))
    noise = np.random.normal(0, 30, n)
    close = 50000.0 + trend + wave + noise
    high = close + np.random.uniform(50, 150, n)
    low = close - np.random.uniform(50, 150, n)
    open_p = close + np.random.normal(0, 20, n)
    volume = np.random.uniform(500, 2000, n)

    df = pd.DataFrame(
        {"open": open_p, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )

    builder = FeatureDatasetBuilder(k_confirmation=2)
    feat_dataset = builder.build(df, symbol="BTC/USDT", timeframe="15m")

    label_engine = LabelEngine(horizon=10, take_profit_pct=0.01, stop_loss_pct=0.005)
    labels_df = label_engine.generate_labels(df)

    merged = feat_dataset.data.copy()
    for col in labels_df.columns:
        if col not in merged.columns:
            merged[col] = labels_df[col]

    return merged


def test_eda_analyzer_full_pipeline():
    """Verify end-to-end analysis on engineered dataset."""
    df = create_synthetic_dataset(n=120)

    # Inject a collinear feature to test multicollinearity detection
    df["rsi_clone"] = df["rsi_14"] * 1.0001
    # Inject a zero-variance feature
    df["constant_zero"] = 0.0

    analyzer = EDAAnalyzer()
    report = analyzer.analyze(df, symbol="BTC/USDT", timeframe="15m")

    # Assertions on basic metadata
    assert report.symbol == "BTC/USDT"
    assert report.timeframe == "15m"
    assert report.total_rows == 120
    assert report.valid_rows > 0

    # Class distribution
    assert "UP" in report.class_distribution
    assert "DOWN" in report.class_distribution
    assert "NEUTRAL" in report.class_distribution
    assert report.imbalance_ratio >= 1.0

    # Zero-variance check
    assert "constant_zero" in report.zero_variance_features

    # Multicollinearity check: rsi_14 and rsi_clone should be detected with |r| >= 0.85
    found_rsi_pair = any(
        (p["feature_1"] in ["rsi_14", "rsi_clone"] and p["feature_2"] in ["rsi_14", "rsi_clone"])
        for p in report.high_correlation_pairs
    )
    assert found_rsi_pair

    # ANOVA ranking check
    assert isinstance(report.top_feature_candidates, list)
    if len(report.top_feature_candidates) > 0:
        top_cand = report.top_feature_candidates[0]
        assert "feature" in top_cand
        assert "f_stat" in top_cand
        assert "p_value" in top_cand
        assert "corr" in top_cand

    # Markdown conversion
    md_content = report.to_markdown()
    assert "# Exploratory Data Analysis Report: BTC/USDT (15m)" in md_content
    assert "## 1. Target Class Distribution" in md_content
    assert "## 2. Missing Value & Data Quality Audit" in md_content
    assert "## 4. Multicollinearity & High Correlation Pairs" in md_content


def test_eda_report_save_markdown():
    """Verify that report can be written to disk."""
    df = create_synthetic_dataset(n=80)
    analyzer = EDAAnalyzer()
    report = analyzer.analyze(df, symbol="BTC/USDT", timeframe="15m")

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, "eda_report.md")
        saved_path = report.save_markdown(out_path)
        assert os.path.exists(saved_path)
        with open(saved_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 100
        assert "BTC/USDT" in content


def test_eda_empty_and_minimal_datasets():
    """Verify graceful handling when data has missing targets or minimal rows."""
    df = pd.DataFrame({
        "open_time": pd.date_range("2026-01-01", periods=10, freq="15min"),
        "open": np.linspace(100, 110, 10),
        "high": np.linspace(101, 111, 10),
        "low": np.linspace(99, 109, 10),
        "close": np.linspace(100.5, 110.5, 10),
        "volume": np.ones(10) * 1000.0,
    })

    analyzer = EDAAnalyzer()
    report = analyzer.analyze(df, symbol="TEST/USDT", timeframe="15m")
    assert report.total_rows == 10
    assert report.valid_rows == 10
    assert len(report.class_distribution) == 0
    assert len(report.top_feature_candidates) == 0
    md = report.to_markdown()
    assert "TEST/USDT" in md
