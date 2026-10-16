"""
Unit tests for ModelRegistry, ModelMetadata, and Lifecycle Promotions (Phase 19).
Reference: Section 24 of Implementation Plan.

Validates:
- Model registration, artifact serialization, and SHA-256 integrity hashing
- Immutability and overwrite protection
- Cryptographic tampering detection (ModelIntegrityError)
- Lifecycle transitions (EXPERIMENTAL -> VALIDATED -> STAGING -> PRODUCTION -> RETIRED)
- Audit trail provenance tracking
- Single-active-production invariant per (symbol, timeframe)
- Production model retrieval and filtering
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

from src.training.models import RandomForestModel, XGBoostModel
from src.training.registry import (
    ModelRegistry,
    ModelMetadata,
    ModelStatus,
    ModelIntegrityError,
    PromotionEvent,
)
from tests.test_eda import create_synthetic_dataset


@pytest.fixture
def trained_models():
    df = create_synthetic_dataset(n=150)
    rf = RandomForestModel(n_estimators=10, max_depth=3, random_state=42)
    rf.fit(df)

    xgb = XGBoostModel(n_estimators=10, max_depth=3, random_state=42)
    xgb.fit(df)

    return rf, xgb, df


def test_register_and_load_model_with_integrity(trained_models):
    rf, _, df = trained_models

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ModelRegistry(base_dir=tmpdir)

        meta = registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={"n_estimators": 10, "max_depth": 3},
            metrics={"balanced_accuracy": 0.58, "macro_f1": 0.35},
            training_range={"start": "2026-01-01", "end": "2026-01-05"},
            status=ModelStatus.EXPERIMENTAL,
            tags=["baseline", "rf"],
        )

        assert meta.model_version == "BTC_15M_RF_v1.0"
        assert meta.status == "EXPERIMENTAL"
        assert len(meta.artifact_hash) == 64

        # Load back
        loaded_model, loaded_meta = registry.load_model("BTC_15M_RF_v1.0")
        assert loaded_meta.model_version == "BTC_15M_RF_v1.0"
        assert loaded_meta.artifact_hash == meta.artifact_hash

        # Verify predictions match perfectly
        orig_preds = rf.predict_proba(df)
        loaded_preds = loaded_model.predict_proba(df)
        pd.testing.assert_frame_equal(orig_preds, loaded_preds)


def test_model_immutability(trained_models):
    rf, _, _ = trained_models

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ModelRegistry(base_dir=tmpdir)

        registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
        )

        # Attempting duplicate registration without overwrite must fail
        with pytest.raises(FileExistsError):
            registry.register_model(
                model=rf,
                model_version="BTC_15M_RF_v1.0",
                model_name="RandomForest",
                symbol="BTC/USDT",
                timeframe="15m",
                feature_version="v1.0",
                dataset_version="btc_15m_v1",
                hyperparameters={},
                metrics={},
                training_range={},
                overwrite=False,
            )

        # With overwrite=True, it succeeds
        meta = registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            overwrite=True,
        )
        assert meta.model_version == "BTC_15M_RF_v1.0"


def test_tampered_artifact_integrity_failure(trained_models):
    rf, _, _ = trained_models

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ModelRegistry(base_dir=tmpdir)

        registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
        )

        # Tamper with the artifact binary
        artifact_path = os.path.join(tmpdir, "BTC_15M_RF_v1.0", "model.joblib")
        with open(artifact_path, "ab") as f:
            f.write(b"CORRUPTED_BYTES")

        # Load must detect hash mismatch and raise ModelIntegrityError
        with pytest.raises(ModelIntegrityError):
            registry.load_model("BTC_15M_RF_v1.0")


def test_lifecycle_promotion_and_audit_trail(trained_models):
    rf, _, _ = trained_models

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ModelRegistry(base_dir=tmpdir)

        registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            status=ModelStatus.EXPERIMENTAL,
        )

        # Promote through lifecycle stages
        registry.promote_model("BTC_15M_RF_v1.0", ModelStatus.VALIDATED, comment="OOS validation passed", actor="lead_quant")
        registry.promote_model("BTC_15M_RF_v1.0", ModelStatus.STAGING, comment="Staged for shadow trading", actor="ops")
        updated_meta = registry.promote_model("BTC_15M_RF_v1.0", ModelStatus.PRODUCTION, comment="Live trading approved", actor="risk_committee")

        assert updated_meta.status == "PRODUCTION"

        # Check audit trail
        trail = registry.get_audit_trail("BTC_15M_RF_v1.0")
        assert len(trail) == 4
        assert trail[0].to_status == "EXPERIMENTAL"
        assert trail[1].to_status == "VALIDATED"
        assert trail[1].actor == "lead_quant"
        assert trail[2].to_status == "STAGING"
        assert trail[3].to_status == "PRODUCTION"
        assert trail[3].actor == "risk_committee"


def test_single_active_production_invariant(trained_models):
    rf, xgb, _ = trained_models

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ModelRegistry(base_dir=tmpdir)

        # 1. Register Model A and promote to PRODUCTION
        registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            status=ModelStatus.PRODUCTION,
        )

        prod_model_1, prod_meta_1 = registry.get_production_model("BTC/USDT", "15m")
        assert prod_meta_1.model_version == "BTC_15M_RF_v1.0"
        assert prod_meta_1.status == "PRODUCTION"

        # 2. Register Model B as STAGING
        registry.register_model(
            model=xgb,
            model_version="BTC_15M_XGB_v1.0",
            model_name="XGBoost",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            status=ModelStatus.STAGING,
        )

        # 3. Promote Model B to PRODUCTION -> Model A must automatically become RETIRED!
        registry.promote_model("BTC_15M_XGB_v1.0", ModelStatus.PRODUCTION, comment="Replacing RF with XGB")

        prod_model_2, prod_meta_2 = registry.get_production_model("BTC/USDT", "15m")
        assert prod_meta_2.model_version == "BTC_15M_XGB_v1.0"
        assert prod_meta_2.status == "PRODUCTION"

        # Verify Model A is now RETIRED
        _, model_a_meta = registry.load_model("BTC_15M_RF_v1.0")
        assert model_a_meta.status == "RETIRED"


def test_list_models_filtering(trained_models):
    rf, xgb, _ = trained_models

    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ModelRegistry(base_dir=tmpdir)

        registry.register_model(
            model=rf,
            model_version="BTC_15M_RF_v1.0",
            model_name="RandomForest",
            symbol="BTC/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="btc_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            status=ModelStatus.EXPERIMENTAL,
        )

        registry.register_model(
            model=xgb,
            model_version="ETH_15M_XGB_v1.0",
            model_name="XGBoost",
            symbol="ETH/USDT",
            timeframe="15m",
            feature_version="v1.0",
            dataset_version="eth_15m_v1",
            hyperparameters={},
            metrics={},
            training_range={},
            status=ModelStatus.VALIDATED,
        )

        # Filter by symbol
        btc_models = registry.list_models(symbol="BTC/USDT")
        assert len(btc_models) == 1
        assert btc_models[0].model_version == "BTC_15M_RF_v1.0"

        # Filter by status
        val_models = registry.list_models(status=ModelStatus.VALIDATED)
        assert len(val_models) == 1
        assert val_models[0].model_version == "ETH_15M_XGB_v1.0"
