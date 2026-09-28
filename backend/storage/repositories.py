"""
backend/storage/repositories.py
Owner: Arzaan
Purpose: Repository classes providing CRUD operations over ORM models.
         Business logic never queries SQLAlchemy directly — always goes through here.

Repositories:
  - DatasetRepository   → CRUD for datasets table
  - ExperimentRepository → CRUD for experiments table
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.logging import get_logger
from backend.storage.models import Dataset, Experiment, ModelResult, Report

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# DatasetRepository
# ---------------------------------------------------------------------------

class DatasetRepository:
    """
    All database operations for the Dataset model.

    Usage:
        repo = DatasetRepository()
        dataset = repo.create(db, dataset_data)
        found   = repo.get_by_id(db, "a1b2c3d4-...")
    """

    def create(self, db: Session, dataset_data: dict) -> Dataset:
        """
        Insert a new Dataset record.

        dataset_data keys must include (matching Dataset ORM fields):
          id, display_id, original_filename, container_type, file_size_bytes,
          sha256, raw_storage_path, upload_timestamp, status, created_by,
          is_duplicate, duplicate_of
        """
        ds = Dataset(
            id=dataset_data["id"],
            display_id=dataset_data["display_id"],
            original_filename=dataset_data["original_filename"],
            container_type=dataset_data.get("container_type", "CSV"),
            file_size_bytes=dataset_data["file_size_bytes"],
            sha256=dataset_data["sha256"],
            raw_storage_path=dataset_data["raw_storage_path"],
            upload_timestamp=dataset_data.get("upload_timestamp", datetime.now(timezone.utc)),
            status=dataset_data.get("status", "REGISTERED"),
            created_by=dataset_data.get("created_by", "system"),
            is_duplicate=dataset_data.get("is_duplicate", False),
            duplicate_of=dataset_data.get("duplicate_of", None),
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)
        logger.info(
            "Dataset created | dataset_id=%s display_id=%s sha256_prefix=%s",
            ds.id, ds.display_id, ds.sha256[:8],
        )
        return ds

    def get_by_id(self, db: Session, dataset_id: str) -> Optional[Dataset]:
        """Return Dataset by UUID primary key, or None if not found."""
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def get_by_display_id(self, db: Session, display_id: str) -> Optional[Dataset]:
        """Return Dataset by display_id (e.g. DS-000001), or None."""
        return db.query(Dataset).filter(Dataset.display_id == display_id).first()

    def get_by_sha256(self, db: Session, sha256: str) -> Optional[Dataset]:
        """
        Return the first Dataset matching this SHA-256 hash, or None.
        Used for duplicate detection during ingestion.
        """
        return db.query(Dataset).filter(Dataset.sha256 == sha256).first()

    def list_all(self, db: Session) -> list[Dataset]:
        """Return all datasets ordered by upload_timestamp descending."""
        return (
            db.query(Dataset)
            .order_by(Dataset.upload_timestamp.desc())
            .all()
        )

    def update_status(self, db: Session, dataset_id: str, status: str) -> Optional[Dataset]:
        """
        Update status field of a Dataset record.
        Returns updated Dataset, or None if not found.
        """
        ds = self.get_by_id(db, dataset_id)
        if ds is None:
            logger.warning("update_status: dataset_id=%s not found", dataset_id)
            return None
        ds.status = status
        db.commit()
        db.refresh(ds)
        logger.info("Dataset status updated | dataset_id=%s status=%s", dataset_id, status)
        return ds

    def count(self, db: Session) -> int:
        """Return total number of registered datasets. Used for display_id generation."""
        return db.query(func.count(Dataset.id)).scalar() or 0

    def max_display_number(self, db: Session) -> int:
        """
        Return the highest DS-NNNNNN number already in the database.
        Used by generate_display_id to ensure monotonic IDs even after deletions.
        Returns 0 if no datasets exist.
        """
        from sqlalchemy import desc
        latest = (
            db.query(Dataset.display_id)
            .order_by(desc(Dataset.display_id))
            .first()
        )
        if latest is None:
            return 0
        try:
            return int(latest[0].split("-")[1])
        except (IndexError, ValueError):
            return self.count(db)

    def delete(self, db: Session, dataset_id: str) -> bool:
        """
        Delete a dataset record by ID.  Does NOT delete files from disk —
        file deletion is handled by LocalFileStorage separately.
        Returns True if deleted, False if not found.
        """
        ds = self.get_by_id(db, dataset_id)
        if ds is None:
            return False
        db.delete(ds)
        db.commit()
        logger.info("Dataset record deleted | dataset_id=%s", dataset_id)
        return True


# ---------------------------------------------------------------------------
# ExperimentRepository
# ---------------------------------------------------------------------------

class ExperimentRepository:
    """
    All database operations for the Experiment model.

    progress_data is stored as a JSON string in the DB and serialised /
    deserialised transparently by update_progress / get_progress.
    """

    def create(self, db: Session, experiment_data: dict) -> Experiment:
        """
        Insert a new Experiment record.

        experiment_data keys:
          id, display_id, dataset_id, status (optional), config_json (optional),
          seed (optional)
        """
        exp = Experiment(
            id=experiment_data["id"],
            display_id=experiment_data["display_id"],
            dataset_id=experiment_data["dataset_id"],
            status=experiment_data.get("status", "CREATED"),
            config_json=experiment_data.get("config_json"),
            seed=experiment_data.get("seed", 42),
            progress_data=None,
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        logger.info(
            "Experiment created | experiment_id=%s dataset_id=%s",
            exp.id, exp.dataset_id,
        )
        return exp

    def get_by_id(self, db: Session, experiment_id: str) -> Optional[Experiment]:
        """Return Experiment by primary key, or None."""
        return db.query(Experiment).filter(Experiment.id == experiment_id).first()

    def list_by_dataset(self, db: Session, dataset_id: str) -> list[Experiment]:
        """Return all experiments for a given dataset, newest first."""
        return (
            db.query(Experiment)
            .filter(Experiment.dataset_id == dataset_id)
            .order_by(Experiment.created_at.desc())
            .all()
        )

    def list_all(self, db: Session) -> list[Experiment]:
        """Return all experiments ordered by created_at descending."""
        return db.query(Experiment).order_by(Experiment.created_at.desc()).all()

    def update_status(
        self,
        db: Session,
        experiment_id: str,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Experiment]:
        """
        Update experiment status and optional lifecycle timestamps.
        Status values from experiment_status.json contract:
          CREATED | VALIDATING | PREPROCESSING | RUNNING_CLASSICAL |
          RUNNING_QUANTUM | BENCHMARKING | EXPLAINING | COMPLETED | FAILED
        """
        exp = self.get_by_id(db, experiment_id)
        if exp is None:
            logger.warning("update_status: experiment_id=%s not found", experiment_id)
            return None
        exp.status = status
        if started_at is not None:
            exp.started_at = started_at
        if completed_at is not None:
            exp.completed_at = completed_at
        db.commit()
        db.refresh(exp)
        logger.info(
            "Experiment status updated | experiment_id=%s status=%s", experiment_id, status
        )
        return exp

    def update_progress(self, db: Session, experiment_id: str, progress: dict) -> Optional[Experiment]:
        """
        Update the progress_data JSON column.
        progress dict shape (experiment_status.json contract):
          {
            "status":              "RUNNING_QUANTUM",
            "stage":               "quantum_training",
            "progress":            0.67,
            "message":             "Training VQC — Epoch 18/30",
            "current_model":       "vqc",
            "completed_models":    ["logistic_regression", "svm", "random_forest"],
            "circuit_executions":  8320,
            "current_epoch":       18,
            "total_epochs":        30,
            "elapsed_seconds":     412.5,
            "estimated_remaining_seconds": 250.3,
            "error_message":       null
          }
        """
        exp = self.get_by_id(db, experiment_id)
        if exp is None:
            logger.warning("update_progress: experiment_id=%s not found", experiment_id)
            return None
        exp.progress_data = json.dumps(progress)
        # Keep status in sync with progress dict if provided
        if "status" in progress:
            exp.status = progress["status"]
        db.commit()
        db.refresh(exp)
        return exp

    def get_progress(self, db: Session, experiment_id: str) -> Optional[dict]:
        """
        Return the current progress_data dict for an experiment, or None.
        Used by GET /api/experiments/{id}/status endpoint.
        """
        exp = self.get_by_id(db, experiment_id)
        if exp is None or exp.progress_data is None:
            return None
        try:
            return json.loads(exp.progress_data)
        except json.JSONDecodeError:
            logger.error(
                "Corrupt progress_data JSON | experiment_id=%s", experiment_id
            )
            return None

    def count(self, db: Session) -> int:
        """Return total experiment count. Used for display_id generation."""
        return db.query(func.count(Experiment.id)).scalar() or 0
