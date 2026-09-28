"""
backend/storage/models.py
Owner: Arzaan
Purpose: SQLAlchemy ORM models for all four database tables.

Tables:
  - datasets         → Dataset registration records (Phase 1 output)
  - experiments      → Experiment lifecycle records (Phase 9/10)
  - model_results    → Per-model training results (Phase 10 output)
  - reports          → Generated reports (Phase 15)

Contract compliance:
  - Dataset.is_duplicate + Dataset.duplicate_of  required by ISSUES.md M-11
  - Experiment.progress_data (JSON text) required by experiment_status.json contract
  - All IDs are UUID strings stored as VARCHAR(36)
  - Timestamps stored as DateTime UTC
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.storage.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class Dataset(Base):
    """
    Represents a registered dataset after Phase 1 ingestion.
    One record per upload (including duplicate uploads — duplicate ≠ invalid).

    Field names mirror dataset_upload_response.json contract exactly.
    """
    __tablename__ = "datasets"

    # Primary key — UUID v4 stored as string
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    # Human-readable ID shown in UI: DS-000001
    display_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Original filename from upload (contract field: filename)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # File format container type — CSV | XLSX | ZIP | UNKNOWN (contract enum)
    container_type: Mapped[str] = mapped_column(String(20), nullable=False, default="CSV")

    # File size in bytes
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # SHA-256 hash (64 hex chars) for integrity + duplicate detection
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Relative storage path: datasets/DS-000001/raw/original.csv
    raw_storage_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # UTC timestamp of upload completion (ISO 8601 in API response)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )

    # Registration status — REGISTERED | REJECTED | INVALID_FORMAT | etc.
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="REGISTERED")

    # Audit: who triggered the upload (default "system" for API uploads)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")

    # Duplicate detection fields — required by ISSUES.md M-11
    # Shweta's code uses hasattr(ds, 'is_duplicate') — must be real ORM columns
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_of: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, default=None)

    # Relationship to experiments using this dataset
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment", back_populates="dataset", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Dataset id={self.id!r} display_id={self.display_id!r} "
            f"filename={self.original_filename!r} status={self.status!r}>"
        )

    def to_response_dict(self) -> dict:
        """
        Serialize to dataset_upload_response.json contract shape.
        Field names match the contract exactly.
        """
        return {
            "dataset_id": self.id,
            "display_id": self.display_id,
            "status": self.status,
            "filename": self.original_filename,
            "container_type": self.container_type,
            "upload_timestamp": self.upload_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "file_size_bytes": self.file_size_bytes,
            "sha256": self.sha256,
            "storage_path": self.raw_storage_path,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "validation_warnings": [],
            "rejection_reason": None if self.status == "REGISTERED" else self.status,
        }


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------

class Experiment(Base):
    """
    Represents an ML experiment (classical or quantum).
    Created by Phase 9 planner, updated by Phase 10 executor.

    progress_data stores the experiment_status.json contract fields as JSON text:
      {"current_model": "vqc", "completed_models": [...], "circuit_executions": 8320}
    This is read directly by GET /api/experiments/{id}/status.
    """
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    # Human-readable ID: EXP-A1B2C3D4
    display_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Foreign key to datasets table
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id"), nullable=False, index=True
    )

    # Experiment lifecycle status — contract enum from experiment_status.json:
    # CREATED | VALIDATING | PREPROCESSING | RUNNING_CLASSICAL |
    # RUNNING_QUANTUM | BENCHMARKING | EXPLAINING | COMPLETED | FAILED
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="CREATED")

    # JSON text column storing live progress data (experiment_status.json shape)
    # Updated by executor after each model completes
    progress_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Full immutable experiment config JSON (experiment_config.json shape)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Reproducibility seed (from experiment_config.json reproducibility.seed)
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)

    # Lifecycle timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="experiments")
    model_results: Mapped[list["ModelResult"]] = relationship(
        "ModelResult", back_populates="experiment", lazy="select"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="experiment", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Experiment id={self.id!r} display_id={self.display_id!r} "
            f"dataset_id={self.dataset_id!r} status={self.status!r}>"
        )

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict for API responses."""
        return {
            "id":           self.id,
            "display_id":   self.display_id,
            "dataset_id":   self.dataset_id,
            "status":       self.status,
            "seed":         self.seed,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "started_at":   self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ---------------------------------------------------------------------------
# ModelResult
# ---------------------------------------------------------------------------

class ModelResult(Base):
    """
    Stores the result of a single model run within an experiment.
    Shape mirrors model_result.json contract.

    One experiment produces multiple ModelResult records:
      - logistic_regression (CLASSICAL)
      - svm (CLASSICAL)
      - random_forest (CLASSICAL)
      - vqc (QUANTUM)
    """
    __tablename__ = "model_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    # Foreign key to experiments
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False, index=True
    )

    # Model name: LogisticRegression | SVM | RandomForest | VQC | QuantumKernel
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Model type: CLASSICAL | QUANTUM | HYBRID (contract enum from model_result.json)
    model_type: Mapped[str] = mapped_column(String(20), nullable=False, default="CLASSICAL")

    # Execution status: COMPLETED | FAILED | TIMEOUT | OUT_OF_MEMORY
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETED")

    # Metrics stored as JSON text (accuracy, precision, recall, f1_score, roc_auc, pr_auc …)
    metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Resource usage stored as JSON text (training_time_seconds, memory_peak_mb …)
    resource_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Quantum-specific metrics JSON (qubits, circuit_depth, total_circuit_executions …)
    # null for classical models (nullable per model_result.json contract)
    quantum_metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # Path to serialised model artifact (.pkl or .npy for VQC params)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, default=None)

    # When this result was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )

    # Relationship
    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="model_results"
    )

    def __repr__(self) -> str:
        return (
            f"<ModelResult id={self.id!r} model_name={self.model_name!r} "
            f"model_type={self.model_type!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class Report(Base):
    """
    Stores generated report artifacts (recommendation, cost_report, explanation).
    Report content is stored as JSON text matching the relevant contract shape.
    """
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)

    # Foreign key to experiments
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id"), nullable=False, index=True
    )

    # Report type: recommendation | cost_report | explanation | final_report
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Full report content as JSON text (matches contract shape for the given type)
    content_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    # When the report was generated
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )

    # Relationship
    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="reports"
    )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id!r} experiment_id={self.experiment_id!r} "
            f"report_type={self.report_type!r}>"
        )
