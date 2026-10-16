"""
Baseline Machine Learning Models for Directional Trading Prediction.
Reference: Section 20 (Phase 15) of Implementation Plan.

Implements the 3 baseline ML models:
1. LogisticRegressionModel: L2 regularized multi-class logistic regression with balanced class weights.
2. RandomForestModel: Non-linear bagged ensemble with sub-sampling and tree depth limits to prevent overfitting.
3. XGBoostModel: Gradient boosted decision trees optimized with multi:softprob objective.

All models incorporate:
- Zero-lookahead feature preprocessing pipeline (fitted strictly on training data).
- Robust 3-class probability alignment (DOWN: -1.0, NEUTRAL: 0.0, UP: +1.0).
- Standardized save/load serialization with joblib.
- Direct evaluation through ModelEvaluator.
"""

from abc import ABC, abstractmethod
import os
from typing import Dict, Any, List, Optional, Tuple, Union, cast
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from src.training.preprocessing import MLFeaturePipeline
from src.evaluation.metrics import ModelEvaluator, ModelEvaluationResult


class BaseTradingModel(ABC):
    """
    Abstract base class for all machine learning trading models.
    """

    CLASS_LABELS = [-1.0, 0.0, 1.0]
    CLASS_NAMES = ["DOWN", "NEUTRAL", "UP"]

    def __init__(self, name: str, pipeline: Optional[MLFeaturePipeline] = None):
        self.name = name
        self.pipeline = pipeline or MLFeaturePipeline()
        self.is_fitted: bool = False

    @abstractmethod
    def _fit_model(self, X: np.ndarray, y: np.ndarray) -> None:
        """Internal model fitting on preprocessed feature matrix."""
        pass

    @abstractmethod
    def _predict_raw(self, X: np.ndarray) -> np.ndarray:
        """Internal prediction producing class labels [-1.0, 0.0, 1.0]."""
        pass

    @abstractmethod
    def _predict_proba_raw(self, X: np.ndarray) -> np.ndarray:
        """Internal probability estimation producing [N, 3] matrix for [DOWN, NEUTRAL, UP]."""
        pass

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
    ) -> "BaseTradingModel":
        """
        Fits preprocessor and ML classifier on training partition.
        """
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not present in training dataframe.")

        # Filter valid rows
        if valid_col in df.columns:
            valid_mask = pd.Series(df[valid_col]) == True
            train_df = pd.DataFrame(df[valid_mask]).copy()
        else:
            train_df = pd.DataFrame(df).copy()

        y_series = pd.Series(train_df[target_col], dtype=float)
        non_nan_mask = ~y_series.isna()
        clean_df = pd.DataFrame(train_df[non_nan_mask])
        y_clean = np.asarray(y_series[non_nan_mask], dtype=np.float64)

        if len(y_clean) == 0:
            raise ValueError("No valid training samples available after filtering.")

        # Fit preprocessor strictly on training features
        X_scaled = self.pipeline.fit_transform(clean_df)

        # Fit classifier
        self._fit_model(X_scaled, y_clean)
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates predictions for each row in the dataframe.
        Returns Series of float: -1.0, 0.0, 1.0.
        """
        if not self.is_fitted:
            raise RuntimeError(f"Model '{self.name}' must be fitted before predict.")

        X_scaled = self.pipeline.transform(df)
        preds = self._predict_raw(X_scaled)
        return pd.Series(cast(Any, preds), index=df.index)

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Estimates class probabilities for [DOWN, NEUTRAL, UP].
        Returns DataFrame with columns ['DOWN', 'NEUTRAL', 'UP'].
        """
        if not self.is_fitted:
            raise RuntimeError(f"Model '{self.name}' must be fitted before predict_proba.")

        X_scaled = self.pipeline.transform(df)
        probas = self._predict_proba_raw(X_scaled)
        return pd.DataFrame(probas, index=df.index, columns=self.CLASS_NAMES)

    def evaluate(
        self,
        df: pd.DataFrame,
        target_col: str = "target_triple_barrier",
        valid_col: str = "is_target_valid",
        split_name: str = "Test",
    ) -> ModelEvaluationResult:
        """
        Evaluates model predictions and probabilities against ground truth labels.
        """
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataframe.")

        if valid_col in df.columns:
            valid_mask = pd.Series(df[valid_col]) == True
            eval_df = pd.DataFrame(df[valid_mask]).copy()
        else:
            eval_df = pd.DataFrame(df).copy()

        y_true = pd.Series(eval_df[target_col], dtype=float)
        y_pred = self.predict(eval_df)
        y_prob = self.predict_proba(eval_df)

        return ModelEvaluator.evaluate(
            y_true=y_true,
            y_pred=y_pred,
            y_prob=y_prob,
            model_name=self.name,
            split_name=split_name,
            total_samples=len(df),
        )

    def save(self, filepath: str) -> str:
        """Persists trained model and pipeline to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump(self, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> "BaseTradingModel":
        """Loads trained model and pipeline from disk."""
        loaded = joblib.load(filepath)
        if not isinstance(loaded, BaseTradingModel):
            raise TypeError(f"Loaded object is not BaseTradingModel: {type(loaded)}")
        return loaded


class LogisticRegressionModel(BaseTradingModel):
    """
    Model 1: Multi-class Logistic Regression with balanced weighting.
    """

    def __init__(
        self,
        name: str = "LogisticRegression",
        pipeline: Optional[MLFeaturePipeline] = None,
        c_param: float = 0.1,
        max_iter: int = 1000,
        random_state: int = 42,
    ):
        super().__init__(name=name, pipeline=pipeline)
        self.c_param = c_param
        self.max_iter = max_iter
        self.random_state = random_state
        self.clf = LogisticRegression(
            C=self.c_param,
            class_weight="balanced",
            max_iter=self.max_iter,
            random_state=self.random_state,
        )

    def _fit_model(self, X: np.ndarray, y: np.ndarray) -> None:
        self.clf.fit(X, y)

    def _predict_raw(self, X: np.ndarray) -> np.ndarray:
        raw = self.clf.predict(X)
        return np.asarray(raw, dtype=np.float64)

    def _predict_proba_raw(self, X: np.ndarray) -> np.ndarray:
        probas = np.asarray(self.clf.predict_proba(X), dtype=np.float64)
        classes = list(self.clf.classes_)

        # Align probabilities to 3 standard columns: [-1.0, 0.0, 1.0]
        n_samples = len(X)
        aligned = np.zeros((n_samples, 3), dtype=np.float64)

        for col_idx, cls_val in enumerate(self.CLASS_LABELS):
            if cls_val in classes:
                src_idx = classes.index(cls_val)
                aligned[:, col_idx] = probas[:, src_idx]

        # Normalize row-wise if any classes were absent
        row_sums = aligned.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return aligned / row_sums


class RandomForestModel(BaseTradingModel):
    """
    Model 2: Random Forest Classifier with depth limits and balanced subsample weighting.
    """

    def __init__(
        self,
        name: str = "RandomForest",
        pipeline: Optional[MLFeaturePipeline] = None,
        n_estimators: int = 100,
        max_depth: int = 6,
        min_samples_split: int = 10,
        min_samples_leaf: int = 5,
        random_state: int = 42,
    ):
        super().__init__(name=name, pipeline=pipeline)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state
        self.clf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            class_weight="balanced_subsample",
            random_state=self.random_state,
            n_jobs=-1,
        )

    def _fit_model(self, X: np.ndarray, y: np.ndarray) -> None:
        self.clf.fit(X, y)

    def _predict_raw(self, X: np.ndarray) -> np.ndarray:
        raw = self.clf.predict(X)
        return np.asarray(raw, dtype=np.float64)

    def _predict_proba_raw(self, X: np.ndarray) -> np.ndarray:
        probas = np.asarray(self.clf.predict_proba(X), dtype=np.float64)
        classes = list(self.clf.classes_)

        n_samples = len(X)
        aligned = np.zeros((n_samples, 3), dtype=np.float64)

        for col_idx, cls_val in enumerate(self.CLASS_LABELS):
            if cls_val in classes:
                src_idx = classes.index(cls_val)
                aligned[:, col_idx] = probas[:, src_idx]

        row_sums = aligned.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return aligned / row_sums


class XGBoostModel(BaseTradingModel):
    """
    Model 3: Gradient Boosted Decision Trees via XGBoost.
    Dynamically aligns to present target classes and guarantees standard 3-class probability alignment.
    """

    def __init__(
        self,
        name: str = "XGBoost",
        pipeline: Optional[MLFeaturePipeline] = None,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
    ):
        super().__init__(name=name, pipeline=pipeline)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state

        self.clf = XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            eval_metric="mlogloss",
            tree_method="hist",
        )
        self.fitted_classes_: List[float] = []

    def _fit_model(self, X: np.ndarray, y: np.ndarray) -> None:
        self.fitted_classes_ = sorted(list(set(y.tolist())))
        label_to_idx = {c: i for i, c in enumerate(self.fitted_classes_)}
        y_int = np.array([label_to_idx[float(val)] for val in y], dtype=np.int32)
        self.clf.fit(X, y_int)

    def _predict_proba_raw(self, X: np.ndarray) -> np.ndarray:
        raw_probas = np.asarray(self.clf.predict_proba(X), dtype=np.float64)
        n_samples = len(X)
        aligned = np.zeros((n_samples, 3), dtype=np.float64)

        for i, c in enumerate(self.fitted_classes_):
            col_idx = self.CLASS_LABELS.index(c)
            aligned[:, col_idx] = raw_probas[:, i]

        row_sums = aligned.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return aligned / row_sums

    def _predict_raw(self, X: np.ndarray) -> np.ndarray:
        probas = self._predict_proba_raw(X)
        pred_idx = np.argmax(probas, axis=1)
        return np.array([self.CLASS_LABELS[i] for i in pred_idx], dtype=np.float64)
