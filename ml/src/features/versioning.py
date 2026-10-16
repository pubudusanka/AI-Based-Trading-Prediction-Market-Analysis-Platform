"""
Dataset Versioning & Chronological Partitioning Pipeline.
Reference: Section 17 (Phase 12) & Section 4.3 of Implementation Plan.

Guarantees:
1. Immutability: Versioned datasets are written once and cannot be silently overwritten.
2. Complete Provenance & Metadata:
   - symbol, timeframe, provider, date range, row counts
   - feature_version and label_version
   - SHA-256 raw data and full dataset hashes
   - Class balance distributions (counts and percentages)
   - Train, Validation, and Test boundary definitions
3. Purged Chronological Splitting:
   - Random train/test shuffling is strictly forbidden.
   - Chronological partitions with safety purge gaps (embargo) equal to
     the prediction horizon (N candles) to prevent target leakage across boundaries.
4. Storage Format:
   - Columnar Parquet for high-speed I/O and lossless schema preservation.
   - Structured JSON metadata sidecar.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DatasetVersionMetadata:
    dataset_version: str
    symbol: str
    timeframe: str
    data_provider: str
    feature_version: str
    label_version: str
    start_date: str
    end_date: str
    total_rows: int
    valid_rows: int
    raw_data_hash: str
    dataset_hash: str
    class_balance: Dict[str, int]
    class_distribution_pct: Dict[str, float]
    split_definitions: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_version": self.dataset_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "data_provider": self.data_provider,
            "feature_version": self.feature_version,
            "label_version": self.label_version,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "raw_data_hash": self.raw_data_hash,
            "dataset_hash": self.dataset_hash,
            "class_balance": self.class_balance,
            "class_distribution_pct": self.class_distribution_pct,
            "split_definitions": self.split_definitions,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DatasetVersionMetadata":
        return cls(
            dataset_version=str(d["dataset_version"]),
            symbol=str(d["symbol"]),
            timeframe=str(d["timeframe"]),
            data_provider=str(d["data_provider"]),
            feature_version=str(d["feature_version"]),
            label_version=str(d["label_version"]),
            start_date=str(d["start_date"]),
            end_date=str(d["end_date"]),
            total_rows=int(d["total_rows"]),
            valid_rows=int(d["valid_rows"]),
            raw_data_hash=str(d["raw_data_hash"]),
            dataset_hash=str(d["dataset_hash"]),
            class_balance=dict(d["class_balance"]),
            class_distribution_pct=dict(d["class_distribution_pct"]),
            split_definitions=dict(d["split_definitions"]),
            created_at=str(d["created_at"]),
        )


@dataclass
class DatasetSplits:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    purge_candles: int

    def summary(self) -> Dict[str, Any]:
        return {
            "train_rows": len(self.train),
            "train_range": (str(self.train.index[0]), str(self.train.index[-1])) if len(self.train) > 0 else None,
            "val_rows": len(self.val),
            "val_range": (str(self.val.index[0]), str(self.val.index[-1])) if len(self.val) > 0 else None,
            "test_rows": len(self.test),
            "test_range": (str(self.test.index[0]), str(self.test.index[-1])) if len(self.test) > 0 else None,
            "purge_gap_candles": self.purge_candles,
        }


@dataclass
class DatasetVersion:
    data: pd.DataFrame
    metadata: DatasetVersionMetadata
    splits: Optional[DatasetSplits] = None


class DatasetManager:
    """
    Manages creation, chronological purged partitioning, metadata auditing,
    and immutable storage of ML datasets.
    """

    DEFAULT_DATASET_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "datasets"
    )

    @classmethod
    def compute_sha256(cls, df: pd.DataFrame) -> str:
        """Computes deterministic SHA-256 hash for a DataFrame."""
        return hashlib.sha256(df.to_csv().encode("utf-8")).hexdigest()

    @classmethod
    def partition_chronological(
        cls,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        purge_candles: int = 20,
    ) -> DatasetSplits:
        """
        Partitions time series chronologically with safety purge gaps.
        
        Leakage Prevention Rule:
        A model predicting 20 candles into the future cannot have training labels
        that overlap with validation features. A purge gap of `purge_candles`
        is excised between Train and Validation, and between Validation and Test.
        """
        if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0, atol=1e-5):
            raise ValueError("train_ratio + val_ratio + test_ratio must sum to 1.0")

        n = len(df)
        total_purge = 2 * purge_candles
        min_required = total_purge + 10
        if n < min_required:
            raise ValueError(f"Dataset too small ({n} rows) for purged splitting with gap={purge_candles}. Minimum required: {min_required}")

        n_effective = n - total_purge
        n_train = max(int(n_effective * train_ratio), 1)
        n_val = max(int(n_effective * val_ratio), 1)

        # 1. Train partition: [0, n_train)
        train_df = df.iloc[:n_train].copy()

        # 2. Validation partition: [n_train + purge_candles, n_train + purge_candles + n_val)
        val_start = n_train + purge_candles
        val_end = val_start + n_val
        val_df = df.iloc[val_start:val_end].copy()

        # 3. Test partition: [val_end + purge_candles, n)
        test_start = val_end + purge_candles
        test_df = df.iloc[test_start:].copy()

        return DatasetSplits(
            train=train_df,
            val=val_df,
            test=test_df,
            purge_candles=purge_candles,
        )

    @classmethod
    def create_version(
        cls,
        features_df: pd.DataFrame,
        labels_df: pd.DataFrame,
        dataset_version: str = "btc_15m_v1",
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        data_provider: str = "Binance Spot",
        feature_version: str = "v1.0",
        label_version: str = "tb_20_10_05",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        purge_candles: int = 20,
    ) -> DatasetVersion:
        """
        Assembles, validates, and partitions a versioned dataset.
        """
        # Ensure common UTC index
        if not features_df.index.equals(labels_df.index):
            raise ValueError("features_df and labels_df must have identical index")

        # Combine features and labels
        combined = pd.concat([features_df, labels_df], axis=1)
        combined = combined.loc[:, ~combined.columns.duplicated()]

        # Compute raw data hash using standard OHLCV if present
        raw_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in combined.columns]
        raw_hash = cls.compute_sha256(combined[raw_cols]) if raw_cols else "unknown"
        dataset_hash = cls.compute_sha256(combined)

        # Class balance computation on valid targets
        if "target_label_name" in combined.columns:
            valid_mask = combined["is_target_valid"] == True if "is_target_valid" in combined.columns else pd.Series(True, index=combined.index)
            valid_targets = combined.loc[valid_mask, "target_label_name"]
            counts = valid_targets.value_counts().to_dict()
            total_valid = len(valid_targets)
            pcts = {k: round(v / total_valid * 100.0, 2) for k, v in counts.items()} if total_valid > 0 else {}
        else:
            counts = {}
            pcts = {}
            total_valid = len(combined)

        # Perform chronological purged partition
        splits = cls.partition_chronological(
            combined,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            purge_candles=purge_candles,
        )

        metadata = DatasetVersionMetadata(
            dataset_version=dataset_version,
            symbol=symbol,
            timeframe=timeframe,
            data_provider=data_provider,
            feature_version=feature_version,
            label_version=label_version,
            start_date=str(combined.index[0]),
            end_date=str(combined.index[-1]),
            total_rows=len(combined),
            valid_rows=int(total_valid),
            raw_data_hash=raw_hash,
            dataset_hash=dataset_hash,
            class_balance=counts,
            class_distribution_pct=pcts,
            split_definitions=splits.summary(),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        return DatasetVersion(data=combined, metadata=metadata, splits=splits)

    @classmethod
    def save_dataset(
        cls,
        dataset: DatasetVersion,
        base_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> str:
        """
        Saves dataset parquet files and metadata.json to disk.
        Enforces immutability: fails if target directory exists unless overwrite=True.
        """
        target_root = base_dir or cls.DEFAULT_DATASET_DIR
        version_dir = os.path.join(target_root, dataset.metadata.dataset_version)

        if os.path.exists(version_dir) and not overwrite:
            raise FileExistsError(
                f"Dataset version '{dataset.metadata.dataset_version}' already exists at {version_dir}. "
                "Versioned datasets are immutable. Increment the version to save new data."
            )

        os.makedirs(version_dir, exist_ok=True)

        # 1. Save full dataset
        dataset.data.to_parquet(os.path.join(version_dir, "dataset_full.parquet"), engine="pyarrow", index=True)

        # 2. Save split partitions
        if dataset.splits is not None:
            dataset.splits.train.to_parquet(os.path.join(version_dir, "train.parquet"), engine="pyarrow", index=True)
            dataset.splits.val.to_parquet(os.path.join(version_dir, "val.parquet"), engine="pyarrow", index=True)
            dataset.splits.test.to_parquet(os.path.join(version_dir, "test.parquet"), engine="pyarrow", index=True)

        # 3. Save metadata JSON
        meta_path = os.path.join(version_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(dataset.metadata.to_dict(), f, indent=2)

        return version_dir

    @classmethod
    def load_dataset(
        cls,
        dataset_version: str,
        base_dir: Optional[str] = None,
    ) -> DatasetVersion:
        """
        Loads a versioned dataset and its chronological partitions from disk.
        """
        target_root = base_dir or cls.DEFAULT_DATASET_DIR
        version_dir = os.path.join(target_root, dataset_version)

        if not os.path.exists(version_dir):
            raise FileNotFoundError(f"Dataset version '{dataset_version}' not found at {version_dir}")

        meta_path = os.path.join(version_dir, "metadata.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)
        metadata = DatasetVersionMetadata.from_dict(meta_dict)

        full_df = pd.read_parquet(os.path.join(version_dir, "dataset_full.parquet"), engine="pyarrow")

        # Load splits if available
        train_path = os.path.join(version_dir, "train.parquet")
        val_path = os.path.join(version_dir, "val.parquet")
        test_path = os.path.join(version_dir, "test.parquet")

        splits: Optional[DatasetSplits] = None
        if os.path.exists(train_path) and os.path.exists(val_path) and os.path.exists(test_path):
            train_df = pd.read_parquet(train_path, engine="pyarrow")
            val_df = pd.read_parquet(val_path, engine="pyarrow")
            test_df = pd.read_parquet(test_path, engine="pyarrow")
            purge_k = int(metadata.split_definitions.get("purge_gap_candles", 20))
            splits = DatasetSplits(train=train_df, val=val_df, test=test_df, purge_candles=purge_k)

        return DatasetVersion(data=full_df, metadata=metadata, splits=splits)

    @classmethod
    def list_datasets(cls, base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all versioned datasets available in the repository."""
        target_root = base_dir or cls.DEFAULT_DATASET_DIR
        if not os.path.exists(target_root):
            return []

        results = []
        for entry in sorted(os.listdir(target_root)):
            entry_path = os.path.join(target_root, entry)
            meta_path = os.path.join(entry_path, "metadata.json")
            if os.path.isdir(entry_path) and os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    results.append(meta)
                except Exception:
                    continue
        return results
