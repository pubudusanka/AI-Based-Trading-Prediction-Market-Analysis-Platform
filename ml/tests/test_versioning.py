"""
Unit tests for DatasetManager, DatasetVersion, and purged chronological splitting.
Validates:
- Chronological time series partitioning with safety purge gaps (embargo)
- Immutability enforcement (preventing accidental overwriting of datasets)
- Complete metadata tracking (hashes, dates, class distributions, split definitions)
- Atomic disk serialization and roundtrip loading
- Multi-dataset discovery
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
from src.features.versioning import DatasetManager, DatasetVersion
from tests.test_structure import create_base_df


def create_sample_feature_and_label_dfs(n: int = 100):
    """Generates synthetic features and labels for testing versioning."""
    df = create_base_df(n=n, base_price=50000.0)
    builder = FeatureDatasetBuilder(k_confirmation=2)
    feat_dataset = builder.build(df, symbol="BTC/USDT", timeframe="15m")

    label_engine = LabelEngine(horizon=10, take_profit_pct=0.01, stop_loss_pct=0.005)
    labels_df = label_engine.generate_labels(df)

    return feat_dataset.data, labels_df


def test_chronological_purged_partition():
    """Verify chronological ordering and safety purge gap between splits."""
    n = 100
    df = create_base_df(n=n, base_price=100.0)
    purge_gap = 5

    splits = DatasetManager.partition_chronological(
        df,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        purge_candles=purge_gap,
    )

    # 1. Train partition: 54 rows (0..53)
    assert len(splits.train) == 54
    assert splits.train.index[-1] == df.index[53]

    # 2. Validation partition starts at 54 + purge_gap = 59
    assert splits.val.index[0] == df.index[59]
    # Check that rows 54..58 are strictly purged (not in train, not in val)
    for p_idx in range(54, 59):
        assert df.index[p_idx] not in splits.train.index
        assert df.index[p_idx] not in splits.val.index

    # 3. Test partition starts at 59 + 18 + 5 = 82
    assert splits.test.index[0] == df.index[82]

    # 4. Strict chronological ordering (last train < first val < last val < first test)
    assert splits.train.index[-1] < splits.val.index[0]
    assert splits.val.index[-1] < splits.test.index[0]


def test_create_and_save_dataset_immutability():
    """Verify dataset creation, atomic saving, and strict immutability checks."""
    features_df, labels_df = create_sample_feature_and_label_dfs(n=80)

    dataset_version = DatasetManager.create_version(
        features_df=features_df,
        labels_df=labels_df,
        dataset_version="btc_15m_v1_test",
        symbol="BTC/USDT",
        timeframe="15m",
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        purge_candles=5,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        # First save succeeds
        saved_dir = DatasetManager.save_dataset(dataset_version, base_dir=tmp_dir)
        assert os.path.exists(os.path.join(saved_dir, "dataset_full.parquet"))
        assert os.path.exists(os.path.join(saved_dir, "train.parquet"))
        assert os.path.exists(os.path.join(saved_dir, "val.parquet"))
        assert os.path.exists(os.path.join(saved_dir, "test.parquet"))
        assert os.path.exists(os.path.join(saved_dir, "metadata.json"))

        # Second save with same version without overwrite MUST fail
        with pytest.raises(FileExistsError):
            DatasetManager.save_dataset(dataset_version, base_dir=tmp_dir, overwrite=False)

        # Second save with overwrite=True succeeds
        DatasetManager.save_dataset(dataset_version, base_dir=tmp_dir, overwrite=True)


def test_load_dataset_roundtrip():
    """Verify loading dataset from disk restores exact data and metadata."""
    features_df, labels_df = create_sample_feature_and_label_dfs(n=80)

    original = DatasetManager.create_version(
        features_df=features_df,
        labels_df=labels_df,
        dataset_version="btc_15m_roundtrip",
        symbol="BTC/USDT",
        timeframe="15m",
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        purge_candles=5,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        DatasetManager.save_dataset(original, base_dir=tmp_dir)
        loaded = DatasetManager.load_dataset("btc_15m_roundtrip", base_dir=tmp_dir)

        # Metadata equivalence
        assert loaded.metadata.dataset_version == original.metadata.dataset_version
        assert loaded.metadata.dataset_hash == original.metadata.dataset_hash
        assert loaded.metadata.total_rows == original.metadata.total_rows
        assert loaded.metadata.valid_rows == original.metadata.valid_rows
        assert loaded.metadata.class_balance == original.metadata.class_balance

        # Data equivalence
        assert loaded.data.shape == original.data.shape
        assert loaded.splits is not None
        assert original.splits is not None
        assert len(loaded.splits.train) == len(original.splits.train)
        assert len(loaded.splits.val) == len(original.splits.val)
        assert len(loaded.splits.test) == len(original.splits.test)


def test_list_datasets_discovery():
    """Verify discovery of all versioned datasets in directory."""
    features_df, labels_df = create_sample_feature_and_label_dfs(n=80)

    d1 = DatasetManager.create_version(features_df, labels_df, dataset_version="btc_v1")
    d2 = DatasetManager.create_version(features_df, labels_df, dataset_version="btc_v2")

    with tempfile.TemporaryDirectory() as tmp_dir:
        DatasetManager.save_dataset(d1, base_dir=tmp_dir)
        DatasetManager.save_dataset(d2, base_dir=tmp_dir)

        discovered = DatasetManager.list_datasets(base_dir=tmp_dir)
        assert len(discovered) == 2
        names = [d["dataset_version"] for d in discovered]
        assert "btc_v1" in names
        assert "btc_v2" in names
