"""
Feature Dataset Creation & Versioning Pipeline.
Reference: Section 15 (Phase 10) of Implementation Plan.

Combines:
1. Raw OHLCV Candles
2. Technical Indicators (Phase 6 FeatureEngine)
3. Candlestick Patterns (Phase 7 CandlestickPatternEngine)
4. Market Structure Features (Phase 8 MarketStructureEngine)
5. Fibonacci Retracement & Proximity Features (Phase 9 FibonacciEngine)

Ensures:
- Unified, leakage-free feature table
- Explicit semantic feature versioning ('v1.0')
- SHA-256 schema & parameter fingerprinting to prevent silent formula changes
- Atomic serialization & deserialization (Parquet / JSON metadata)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from typing import List, Dict, Any, Optional
import pandas as pd

from .engine import FeatureEngine
from .patterns import CandlestickPatternEngine
from .structure import MarketStructureEngine
from .fibonacci import FibonacciEngine


@dataclass(frozen=True)
class FeatureDatasetMetadata:
    feature_version: str
    symbol: str
    timeframe: str
    total_candles: int
    start_time: Optional[str]
    end_time: Optional[str]
    raw_columns: List[str]
    feature_columns: List[str]
    feature_count: int
    feature_hash: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_version": self.feature_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "total_candles": self.total_candles,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "raw_columns": self.raw_columns,
            "feature_columns": self.feature_columns,
            "feature_count": self.feature_count,
            "feature_hash": self.feature_hash,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureDatasetMetadata":
        return cls(
            feature_version=str(data["feature_version"]),
            symbol=str(data["symbol"]),
            timeframe=str(data["timeframe"]),
            total_candles=int(data["total_candles"]),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            raw_columns=list(data["raw_columns"]),
            feature_columns=list(data["feature_columns"]),
            feature_count=int(data["feature_count"]),
            feature_hash=str(data["feature_hash"]),
            created_at=str(data["created_at"]),
        )


@dataclass
class FeatureDataset:
    data: pd.DataFrame
    metadata: FeatureDatasetMetadata

    def save(self, directory_path: str) -> None:
        """Saves feature dataset parquet and metadata.json to disk."""
        os.makedirs(directory_path, exist_ok=True)
        parquet_path = os.path.join(directory_path, "features.parquet")
        meta_path = os.path.join(directory_path, "metadata.json")

        self.data.to_parquet(parquet_path, engine="pyarrow", index=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

    @classmethod
    def load(cls, directory_path: str) -> "FeatureDataset":
        """Loads feature dataset and validates metadata schema."""
        parquet_path = os.path.join(directory_path, "features.parquet")
        meta_path = os.path.join(directory_path, "metadata.json")

        if not os.path.exists(parquet_path) or not os.path.exists(meta_path):
            raise FileNotFoundError(f"Missing features.parquet or metadata.json in {directory_path}")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)
        metadata = FeatureDatasetMetadata.from_dict(meta_dict)

        df = pd.read_parquet(parquet_path, engine="pyarrow")
        return cls(data=df, metadata=metadata)


class FeatureDatasetBuilder:
    """
    Orchestrates the end-to-end feature creation pipeline for market candles.
    """

    CURRENT_VERSION = "v1.0"
    RAW_COLUMNS = ["open", "high", "low", "close", "volume"]

    def __init__(
        self,
        k_confirmation: int = 3,
        near_threshold_pct: float = 0.003,
        retest_tolerance_pct: float = 0.003,
        feature_version: str = CURRENT_VERSION,
    ) -> None:
        self.version = feature_version
        self.k = k_confirmation
        self.near_threshold = near_threshold_pct
        self.retest_tolerance = retest_tolerance_pct

        # Sub-engines
        self.engine_technical = FeatureEngine()
        self.engine_patterns = CandlestickPatternEngine()
        self.engine_structure = MarketStructureEngine(
            k_confirmation=k_confirmation,
            retest_tolerance_pct=retest_tolerance_pct,
        )
        self.engine_fibonacci = FibonacciEngine(
            k_confirmation=k_confirmation,
            near_threshold_pct=near_threshold_pct,
        )

    def _compute_hash(self, feature_columns: List[str]) -> str:
        """Computes deterministic SHA-256 fingerprint for the feature schema."""
        canonical_str = f"{self.version}:{','.join(sorted(feature_columns))}:k={self.k}:near={self.near_threshold}:retest={self.retest_tolerance}"
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def build(
        self,
        df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
    ) -> FeatureDataset:
        """
        Executes all sub-engines and merges their outputs into a single unified dataset.
        """
        req_cols = {"open", "high", "low", "close", "volume"}
        if not req_cols.issubset(df.columns):
            missing = req_cols - set(df.columns)
            raise ValueError(f"Input DataFrame missing required columns: {missing}")

        data = df.copy()
        if not isinstance(data.index, pd.DatetimeIndex):
            if "open_time" in data.columns:
                data["open_time"] = pd.to_datetime(data["open_time"], utc=True)
                data.set_index("open_time", inplace=True)
            else:
                data.index = pd.to_datetime(data.index, utc=True)
        elif data.index.tz is None:
            data.index = data.index.tz_localize("UTC")
        else:
            data.index = data.index.tz_convert("UTC")

        data.sort_index(inplace=True)

        # 1. Technical features (Phase 6)
        tech_df = self.engine_technical.compute_features(data)

        # 2. Candlestick patterns (Phase 7)
        patterns_df = self.engine_patterns.detect_patterns(data)

        # 3. Market structure (Phase 8)
        structure_df = self.engine_structure.compute(data)

        # 4. Fibonacci retracements (Phase 9 - passes precomputed structure)
        fib_df = self.engine_fibonacci.compute(data, structure_df=structure_df)

        # Combine all features with raw OHLCV
        raw_part = data[self.RAW_COLUMNS]
        combined_df = pd.concat([raw_part, tech_df, patterns_df, structure_df, fib_df], axis=1)

        # Remove duplicate column names if any
        combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]

        feature_cols = [c for c in combined_df.columns if c not in self.RAW_COLUMNS]
        feat_hash = self._compute_hash(feature_cols)

        start_time = str(combined_df.index[0]) if len(combined_df) > 0 else None
        end_time = str(combined_df.index[-1]) if len(combined_df) > 0 else None

        metadata = FeatureDatasetMetadata(
            feature_version=self.version,
            symbol=symbol,
            timeframe=timeframe,
            total_candles=len(combined_df),
            start_time=start_time,
            end_time=end_time,
            raw_columns=self.RAW_COLUMNS,
            feature_columns=feature_cols,
            feature_count=len(feature_cols),
            feature_hash=feat_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        return FeatureDataset(data=combined_df, metadata=metadata)
