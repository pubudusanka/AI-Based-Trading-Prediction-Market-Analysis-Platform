"""
Feature Preprocessing Pipeline for Machine Learning Models.
Reference: Section 20 (Phase 15) of Implementation Plan.

Guarantees zero lookahead bias:
- Fitted strictly on the training partition.
- Imputes missing values using training-set medians.
- Standardizes feature distributions using training-set mean and variance.
- Preserves feature column order and metadata across train, val, test, and live inference.
"""

from typing import List, Dict, Any, Optional, Set, Union, cast
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import joblib


class MLFeaturePipeline(BaseEstimator, TransformerMixin):
    """
    Leakage-free feature preprocessor for tabular market features.
    """

    EXCLUDE_COLUMNS: Set[str] = {
        # Raw price and volume
        "open", "high", "low", "close", "volume",
        "open_time", "close_time",
        # Target variables (never used as inputs!)
        "target_triple_barrier", "target_label_name", "target_binary",
        "is_target_valid",
        # Forward auxiliary lookahead returns
        "future_return_5", "future_return_10", "future_return_20",
        "max_future_return", "min_future_return",
        "candles_to_target", "candles_to_stop",
    }

    def __init__(
        self,
        scaler: Optional[StandardScaler] = None,
        imputer: Optional[SimpleImputer] = None,
        feature_names: Optional[List[str]] = None,
    ):
        self.scaler = scaler or StandardScaler()
        self.imputer = imputer or SimpleImputer(strategy="median")
        self.feature_names: List[str] = feature_names or []
        self._is_fitted: bool = False

    def select_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Identifies eligible numeric feature columns excluding targets and raw price columns."""
        cols = []
        for c in df.columns:
            if c not in self.EXCLUDE_COLUMNS and pd.api.types.is_numeric_dtype(df[c]):
                cols.append(c)
        return cols

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None) -> "MLFeaturePipeline":
        """
        Fits the imputer and scaler strictly on the training dataset.
        """
        if not self.feature_names:
            self.feature_names = self.select_feature_columns(X)

        if not self.feature_names:
            raise ValueError("No numeric feature columns found to fit pipeline.")

        sub_df = pd.DataFrame(X[self.feature_names])
        raw_vals = np.asarray(sub_df, dtype=np.float64)

        # 1. Fit Imputer
        imputed_vals = self.imputer.fit_transform(raw_vals)

        # 2. Fit Scaler
        self.scaler.fit(imputed_vals)

        self._is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transforms input features using fitted training statistics.
        """
        if not self._is_fitted:
            raise RuntimeError("MLFeaturePipeline must be fitted before calling transform.")

        # Ensure all required features are present
        missing = [c for c in self.feature_names if c not in X.columns]
        if missing:
            raise ValueError(f"Missing required feature columns in input: {missing}")

        sub_df = pd.DataFrame(X[self.feature_names])
        raw_vals = np.asarray(sub_df, dtype=np.float64)

        # Impute missing values with training medians
        imputed_vals = self.imputer.transform(raw_vals)

        # Scale with training mean and variance
        scaled_vals = self.scaler.transform(imputed_vals)
        return np.asarray(scaled_vals, dtype=np.float64)

    def fit_transform(self, X: pd.DataFrame, y: Optional[Any] = None, **fit_params: Any) -> np.ndarray:
        """Fits on training data and transforms in one atomic step."""
        return self.fit(X, y).transform(X)

    def save(self, filepath: str) -> str:
        """Persists fitted pipeline to disk."""
        import os
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump(self, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> "MLFeaturePipeline":
        """Loads fitted pipeline from disk."""
        loaded = joblib.load(filepath)
        if not isinstance(loaded, MLFeaturePipeline):
            raise TypeError(f"Loaded object is not MLFeaturePipeline: {type(loaded)}")
        return loaded
