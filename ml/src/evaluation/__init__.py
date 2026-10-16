"""Model evaluation, classification metrics, and probability calibration."""

from src.evaluation.metrics import (
    ModelEvaluator,
    ModelEvaluationResult,
)
from src.evaluation.calibration import (
    ProbabilityCalibrator,
    CalibratedTradingModel,
    CalibrationAuditReport,
    ClassCalibrationMetrics,
    ReliabilityBin,
)

from src.evaluation.explainability import (
    FeatureImportanceEngine,
    FeatureImportanceItem,
    PredictionFactorExplanation,
    SinglePredictionExplanation,
    FeatureImportanceReport,
    CAUSALITY_DISCLAIMER,
)

__all__ = [
    "ModelEvaluator",
    "ModelEvaluationResult",
    "ProbabilityCalibrator",
    "CalibratedTradingModel",
    "CalibrationAuditReport",
    "ClassCalibrationMetrics",
    "ReliabilityBin",
    "FeatureImportanceEngine",
    "FeatureImportanceItem",
    "PredictionFactorExplanation",
    "SinglePredictionExplanation",
    "FeatureImportanceReport",
    "CAUSALITY_DISCLAIMER",
]
