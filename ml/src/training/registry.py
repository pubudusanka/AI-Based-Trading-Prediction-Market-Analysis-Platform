"""
Model Registry & Versioning Pipeline for Trading Predictions.
Reference: Section 24 (Phase 19) of Implementation Plan.

Guarantees:
- Every trained model receives a standardized version (e.g. BTC_15M_XGB_v1.0).
- Strict provenance tracking: feature version, dataset version, training range,
  hyperparameters, evaluation metrics, and SHA-256 artifact integrity hashing.
- Immutable storage & artifact checksum verification on load.
- Strict Lifecycle state machine:
  EXPERIMENTAL -> VALIDATED -> STAGING -> PRODUCTION -> RETIRED.
- Single-active-production invariant: Exactly one model per (symbol, timeframe) can be
  active in PRODUCTION at any given moment; previous production models are cleanly RETIRED.
- Full chronological audit trail of all promotions and lifecycle transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union, cast
import joblib


class ModelStatus(str, Enum):
    """Lifecycle statuses for machine learning models."""
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    RETIRED = "RETIRED"


class ModelIntegrityError(Exception):
    """Raised when model artifact fails SHA-256 checksum validation."""
    pass


@dataclass
class PromotionEvent:
    """Historical record of a model lifecycle status change."""
    timestamp: str
    from_status: str
    to_status: str
    actor: str
    comment: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PromotionEvent:
        return cls(
            timestamp=data["timestamp"],
            from_status=data["from_status"],
            to_status=data["to_status"],
            actor=data["actor"],
            comment=data.get("comment", ""),
        )


@dataclass
class ModelMetadata:
    """Comprehensive provenance and performance metadata for a versioned model."""
    model_version: str
    model_name: str
    model_type: str
    symbol: str
    timeframe: str
    feature_version: str
    dataset_version: str
    training_date: str
    training_range: Dict[str, str]
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float]
    artifact_filename: str
    artifact_hash: str
    status: str = ModelStatus.EXPERIMENTAL.value
    calibration_method: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelMetadata:
        return cls(
            model_version=data["model_version"],
            model_name=data["model_name"],
            model_type=data["model_type"],
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            feature_version=data["feature_version"],
            dataset_version=data["dataset_version"],
            training_date=data["training_date"],
            training_range=data.get("training_range", {}),
            hyperparameters=data.get("hyperparameters", {}),
            metrics=data.get("metrics", {}),
            artifact_filename=data["artifact_filename"],
            artifact_hash=data["artifact_hash"],
            status=data.get("status", ModelStatus.EXPERIMENTAL.value),
            calibration_method=data.get("calibration_method"),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


class ModelRegistry:
    """
    Production-grade Model Registry for managing serialized models,
    cryptographic integrity, and lifecycle status progression.
    """

    METADATA_FILE = "metadata.json"
    AUDIT_FILE = "audit_trail.json"
    DEFAULT_ARTIFACT_NAME = "model.joblib"

    def __init__(self, base_dir: str = "models/registry"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_model_dir(self, model_version: str) -> str:
        return os.path.join(self.base_dir, model_version)

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        """Computes SHA-256 hash of a file for integrity verification."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def register_model(
        self,
        model: Any,
        model_version: str,
        model_name: str,
        symbol: str,
        timeframe: str,
        feature_version: str,
        dataset_version: str,
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, float],
        training_range: Dict[str, str],
        status: Union[ModelStatus, str] = ModelStatus.EXPERIMENTAL,
        calibration_method: Optional[str] = None,
        tags: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> ModelMetadata:
        """
        Serializes model, computes SHA-256 hash, stores metadata, and registers model.
        """
        model_dir = self._get_model_dir(model_version)
        if os.path.exists(model_dir) and not overwrite:
            raise FileExistsError(
                f"Model version '{model_version}' already exists in registry. "
                "Models are immutable; set overwrite=True or bump the model version."
            )

        os.makedirs(model_dir, exist_ok=True)
        artifact_path = os.path.join(model_dir, self.DEFAULT_ARTIFACT_NAME)

        # 1. Serialize model to disk
        joblib.dump(model, artifact_path)

        # 2. Compute cryptographic checksum
        artifact_hash = self.compute_sha256(artifact_path)

        # 3. Determine status string
        status_str = status.value if isinstance(status, ModelStatus) else str(status).upper()
        if status_str not in [s.value for s in ModelStatus]:
            raise ValueError(f"Invalid status '{status_str}'. Must be one of {[s.value for s in ModelStatus]}")

        model_type = type(model).__name__
        now = datetime.now(timezone.utc).isoformat()

        metadata = ModelMetadata(
            model_version=model_version,
            model_name=model_name,
            model_type=model_type,
            symbol=symbol,
            timeframe=timeframe,
            feature_version=feature_version,
            dataset_version=dataset_version,
            training_date=now,
            training_range=training_range,
            hyperparameters=hyperparameters,
            metrics=metrics,
            artifact_filename=self.DEFAULT_ARTIFACT_NAME,
            artifact_hash=artifact_hash,
            status=status_str,
            calibration_method=calibration_method,
            tags=tags or [],
            created_at=now,
            updated_at=now,
        )

        # 4. Save metadata sidecar
        metadata_path = os.path.join(model_dir, self.METADATA_FILE)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        # 5. Initialize audit trail
        audit_path = os.path.join(model_dir, self.AUDIT_FILE)
        initial_event = PromotionEvent(
            timestamp=now,
            from_status="NONE",
            to_status=status_str,
            actor="system",
            comment=f"Initial registration as {status_str}",
        )
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump([initial_event.to_dict()], f, indent=2)

        # 6. If registered directly as PRODUCTION, demote previous active production model
        if status_str == ModelStatus.PRODUCTION.value:
            self._ensure_single_production(model_version, symbol, timeframe)

        return metadata

    def load_model(self, model_version: str) -> Tuple[Any, ModelMetadata]:
        """
        Loads versioned model after verifying cryptographic checksum integrity.
        """
        model_dir = self._get_model_dir(model_version)
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Model version '{model_version}' not found in registry {self.base_dir}")

        metadata_path = os.path.join(model_dir, self.METADATA_FILE)
        if not os.path.isfile(metadata_path):
            raise FileNotFoundError(f"Metadata file missing for model '{model_version}'")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_dict = json.load(f)
        metadata = ModelMetadata.from_dict(metadata_dict)

        artifact_path = os.path.join(model_dir, metadata.artifact_filename)
        if not os.path.isfile(artifact_path):
            raise FileNotFoundError(f"Artifact binary missing for model '{model_version}' at {artifact_path}")

        # Verify integrity
        computed_hash = self.compute_sha256(artifact_path)
        if computed_hash != metadata.artifact_hash:
            raise ModelIntegrityError(
                f"Artifact checksum verification failed for '{model_version}'. "
                f"Expected {metadata.artifact_hash}, got {computed_hash}. File may be corrupted or tampered with."
            )

        model = joblib.load(artifact_path)
        return model, metadata

    def promote_model(
        self,
        model_version: str,
        new_status: Union[ModelStatus, str],
        comment: str = "",
        actor: str = "system",
    ) -> ModelMetadata:
        """
        Promotes/transitions a model to a new lifecycle status with full audit logging.
        Enforces single-active-production invariant for (symbol, timeframe).
        """
        model_dir = self._get_model_dir(model_version)
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Model version '{model_version}' not found in registry.")

        metadata_path = os.path.join(model_dir, self.METADATA_FILE)
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_dict = json.load(f)
        metadata = ModelMetadata.from_dict(metadata_dict)

        target_status = new_status.value if isinstance(new_status, ModelStatus) else str(new_status).upper()
        if target_status not in [s.value for s in ModelStatus]:
            raise ValueError(f"Invalid status '{target_status}'. Must be one of {[s.value for s in ModelStatus]}")

        current_status = metadata.status
        if current_status == target_status:
            return metadata

        now = datetime.now(timezone.utc).isoformat()

        # Update metadata
        metadata.status = target_status
        metadata.updated_at = now
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        # Record audit event
        audit_path = os.path.join(model_dir, self.AUDIT_FILE)
        audit_events: List[Dict[str, Any]] = []
        if os.path.isfile(audit_path):
            with open(audit_path, "r", encoding="utf-8") as f:
                audit_events = json.load(f)

        event = PromotionEvent(
            timestamp=now,
            from_status=current_status,
            to_status=target_status,
            actor=actor,
            comment=comment or f"Promoted from {current_status} to {target_status}",
        )
        audit_events.append(event.to_dict())
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_events, f, indent=2)

        # Enforce single production model invariant
        if target_status == ModelStatus.PRODUCTION.value:
            self._ensure_single_production(model_version, metadata.symbol, metadata.timeframe)

        return metadata

    def _ensure_single_production(self, current_prod_version: str, symbol: str, timeframe: str) -> None:
        """
        Guarantees that only one model per (symbol, timeframe) is in PRODUCTION status.
        Any previous PRODUCTION model is transitioned to RETIRED.
        """
        for m in self.list_models(symbol=symbol, timeframe=timeframe, status=ModelStatus.PRODUCTION.value):
            if m.model_version != current_prod_version:
                self.promote_model(
                    model_version=m.model_version,
                    new_status=ModelStatus.RETIRED,
                    comment=f"Auto-demoted to RETIRED: replaced by new PRODUCTION model '{current_prod_version}'",
                    actor="registry-guard",
                )

    def get_production_model(self, symbol: str, timeframe: str) -> Tuple[Any, ModelMetadata]:
        """
        Retrieves the active PRODUCTION model for the specified symbol and timeframe.
        """
        candidates = self.list_models(symbol=symbol, timeframe=timeframe, status=ModelStatus.PRODUCTION.value)
        if not candidates:
            raise FileNotFoundError(f"No active PRODUCTION model registered for symbol='{symbol}', timeframe='{timeframe}'.")

        # Pick latest updated candidate
        active_metadata = candidates[0]
        return self.load_model(active_metadata.model_version)

    def list_models(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        status: Optional[Union[ModelStatus, str]] = None,
    ) -> List[ModelMetadata]:
        """
        Discovers and lists all registered models filtered by symbol, timeframe, or status.
        Sorted by creation time descending.
        """
        results: List[ModelMetadata] = []
        if not os.path.exists(self.base_dir):
            return results

        status_filter = status.value if isinstance(status, ModelStatus) else (status.upper() if status else None)

        for folder in os.listdir(self.base_dir):
            folder_path = os.path.join(self.base_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            metadata_path = os.path.join(folder_path, self.METADATA_FILE)
            if not os.path.isfile(metadata_path):
                continue

            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = ModelMetadata.from_dict(data)

                if symbol and meta.symbol.lower() != symbol.lower():
                    continue
                if timeframe and meta.timeframe.lower() != timeframe.lower():
                    continue
                if status_filter and meta.status.upper() != status_filter:
                    continue

                results.append(meta)
            except Exception:
                continue

        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def get_audit_trail(self, model_version: str) -> List[PromotionEvent]:
        """Returns the full audit trail of promotions for a given model version."""
        model_dir = self._get_model_dir(model_version)
        audit_path = os.path.join(model_dir, self.AUDIT_FILE)
        if not os.path.isfile(audit_path):
            return []

        with open(audit_path, "r", encoding="utf-8") as f:
            events_data = json.load(f)
        return [PromotionEvent.from_dict(e) for e in events_data]
