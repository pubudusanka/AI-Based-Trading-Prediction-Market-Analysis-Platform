"""Walk-forward cross-validation and ML model training pipelines."""

from src.training.baseline import (
    BaselineStrategy,
    BaselineEvaluationResult,
    RuleBasedBaselineStrategy,
    MomentumBaselineStrategy,
    MajorityClassBaseline,
    StratifiedRandomBaseline,
)
from src.training.preprocessing import MLFeaturePipeline
from src.training.models import (
    BaseTradingModel,
    LogisticRegressionModel,
    RandomForestModel,
    XGBoostModel,
)
from src.training.comparison import (
    ModelComparisonRunner,
    BenchmarkComparisonReport,
)
from src.training.validation import (
    PurgedWalkForwardCV,
    WalkForwardFoldResult,
    WalkForwardValidationReport,
    WalkForwardValidator,
)
from src.training.registry import (
    ModelRegistry,
    ModelMetadata,
    ModelStatus,
    ModelIntegrityError,
    PromotionEvent,
)

__all__ = [
    "BaselineStrategy",
    "BaselineEvaluationResult",
    "RuleBasedBaselineStrategy",
    "MomentumBaselineStrategy",
    "MajorityClassBaseline",
    "StratifiedRandomBaseline",
    "MLFeaturePipeline",
    "BaseTradingModel",
    "LogisticRegressionModel",
    "RandomForestModel",
    "XGBoostModel",
    "ModelComparisonRunner",
    "BenchmarkComparisonReport",
    "PurgedWalkForwardCV",
    "WalkForwardFoldResult",
    "WalkForwardValidationReport",
    "WalkForwardValidator",
    "ModelRegistry",
    "ModelMetadata",
    "ModelStatus",
    "ModelIntegrityError",
    "PromotionEvent",
]
