"""Leakage-free technical and structural feature engineering"""

from .engine import FeatureEngine
from .patterns import CandlestickPatternEngine
from .structure import MarketStructureEngine
from .fibonacci import FibonacciEngine
from .dataset import FeatureDataset, FeatureDatasetBuilder, FeatureDatasetMetadata
from .labels import LabelEngine
from .versioning import (
    DatasetManager,
    DatasetVersion,
    DatasetVersionMetadata,
    DatasetSplits,
)

__all__ = [
    "FeatureEngine",
    "CandlestickPatternEngine",
    "MarketStructureEngine",
    "FibonacciEngine",
    "FeatureDataset",
    "FeatureDatasetBuilder",
    "FeatureDatasetMetadata",
    "LabelEngine",
    "DatasetManager",
    "DatasetVersion",
    "DatasetVersionMetadata",
    "DatasetSplits",
]


