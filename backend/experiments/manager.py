"""
backend/experiments/manager.py
Owner: Piyush
Phase: 10 + 12 (MVP)

ExperimentManager — CRUD layer for experiment lifecycle management.
From guide_piyush.md §6 + phase10.md §32-33:

Status transitions (must be exact — Naeem's frontend polls this):
    CREATED → VALIDATING → PREPROCESSING → RUNNING_CLASSICAL
           → RUNNING_QUANTUM → BENCHMARKING → EXPLAINING → COMPLETED / FAILED

Uses Arzaan's storage layer (backend.storage.repositories + database).
Each status update is persisted to SQLite immediately.
Results stored as JSON in artifacts/experiments/{experiment_id}/
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.core.config import config
from backend.core.logging import get_logger

logger = get_logger(__name__)


class ExperimentStatus(str, Enum):
    """
    Experiment lifecycle states.
    These strings are the exact values stored in DB + returned by status API.
    Frontend polls /api/experiments/{id}/status and reads the 'status' field.
    """
    CREATED           = "CREATED"
    VALIDATING        = "VALIDATING"
    PREPROCESSING     = "PREPROCESSING"
    RUNNING_CLASSICAL = "RUNNING_CLASSICAL"
    RUNNING_QUANTUM   = "RUNNING_QUANTUM"
    BENCHMARKING      = "BENCHMARKING"
    EXPLAINING        = "EXPLAINING"
    COMPLETED         = "COMPLETED"
    FAILED            = "FAILED"


class ExperimentManager:
    """
    Creates + tracks experiments in SQLite.
    Stores results + artifacts to disk.

    Usage:
        manager = ExperimentManager(db_session)
        exp_id = manager.create_experiment(dataset_id, config)
        manager.update_status(exp_id, ExperimentStatus.RUNNING_CLASSICAL)
        manager.store_results(exp_id, results_dict)
        status = manager.get_status(exp_id)
    """

    def __init__(self, db: Optional[Session] = None) -> None:
        self._db = db
        self._artifacts_base = config.artifacts_path

    # ── Experiment creation ───────────────────────────────────────────────────

    def create_experiment(
        self,
        dataset_id: str,
        configuration: dict,
        experiment_id: Optional[str] = None,
    ) -> str:
        """
        Create a new experiment record in SQLite.
        Returns experiment_id.

        phase10.md §33: each experiment gets a unique ID.
        """
        exp_id = experiment_id or f"EXP-{uuid.uuid4().hex[:8].upper()}"

        # Attempt DB write (if session available)
        if self._db is not None:
            try:
                from backend.storage.repositories import ExperimentRepository
                repo = ExperimentRepository()
                repo.create(self._db, {
                    "id":          exp_id,
                    "display_id":  exp_id,
                    "dataset_id":  dataset_id,
                    "status":      ExperimentStatus.CREATED.value,
                    "config_json": json.dumps(configuration),
                    "seed":        configuration.get("random_state", 42),
                })
            except Exception as exc:
                logger.warning("DB write failed for %s: %s — continuing without DB.", exp_id, exc)

        # Always write experiment manifest to disk (resilient)
        manifest = {
            "experiment_id":  exp_id,
            "dataset_id":     dataset_id,
            "status":         ExperimentStatus.CREATED.value,
            "configuration":  configuration,
            "created_at":     datetime.now(timezone.utc).isoformat(),
            "completed_at":   None,
            "error_message":  None,
            "progress":       0.0,
            "stage":          "created",
            "completed_models": [],
            "current_model":  None,
        }
        self._write_artifact(exp_id, "manifest.json", manifest)
        logger.info("Experiment created | id=%s | dataset=%s", exp_id, dataset_id)
        return exp_id

    # ── Status management ─────────────────────────────────────────────────────

    def update_status(
        self,
        experiment_id: str,
        status: ExperimentStatus,
        stage: str = "",
        progress: float = 0.0,
        current_model: Optional[str] = None,
        completed_models: Optional[list] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Persist status transition.
        Called by ExperimentExecutor at each phase boundary.
        """
        logger.info("Experiment %s -> %s (stage=%s, progress=%.0f%%)",
                    experiment_id, status.value, stage, progress * 100)

        # Update manifest on disk
        manifest = self._read_artifact(experiment_id, "manifest.json") or {}
        manifest.update({
            "status":           status.value,
            "stage":            stage or status.value.lower(),
            "progress":         round(progress, 4),
            "current_model":    current_model,
            "completed_models": completed_models or manifest.get("completed_models", []),
            "error_message":    error_message,
            "updated_at":       datetime.now(timezone.utc).isoformat(),
        })
        if status == ExperimentStatus.COMPLETED:
            manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._write_artifact(experiment_id, "manifest.json", manifest)

        # Try DB update
        if self._db is not None:
            try:
                from backend.storage.repositories import ExperimentRepository
                repo = ExperimentRepository()
                repo.update_status(self._db, experiment_id, status.value)
            except Exception as exc:
                logger.debug("DB status update failed: %s", exc)

    # ── Status retrieval ──────────────────────────────────────────────────────

    def get_status(self, experiment_id: str) -> dict:
        """
        Returns experiment_status.json contract shape.
        Called by GET /api/experiments/{id}/status
        Frontend polls this every 2 seconds.
        """
        manifest = self._read_artifact(experiment_id, "manifest.json")
        if manifest is None:
            return {
                "experiment_id": experiment_id,
                "status":        "NOT_FOUND",
                "error_message": f"Experiment {experiment_id} not found.",
            }
        return {
            "experiment_id":    experiment_id,
            "status":           manifest.get("status", "UNKNOWN"),
            "stage":            manifest.get("stage", ""),
            "progress":         manifest.get("progress", 0.0),
            "started_at":       manifest.get("created_at"),
            "completed_at":     manifest.get("completed_at"),
            "current_model":    manifest.get("current_model"),
            "completed_models": manifest.get("completed_models", []),
            "error_message":    manifest.get("error_message"),
        }

    def get_experiment(self, experiment_id: str) -> Optional[dict]:
        """Load full experiment manifest."""
        return self._read_artifact(experiment_id, "manifest.json")

    # ── Results storage ───────────────────────────────────────────────────────

    def store_results(self, experiment_id: str, results: Dict[str, Any]) -> None:
        """
        Persist all model results + comparison + recommendation to artifacts dir.
        phase10.md §34: artifacts stored in artifacts/experiments/{experiment_id}/
        """
        self._write_artifact(experiment_id, "results.json", results)
        logger.info("Results stored for experiment %s", experiment_id)

    def get_results(self, experiment_id: str) -> Optional[dict]:
        return self._read_artifact(experiment_id, "results.json")

    def store_recommendation(self, experiment_id: str, recommendation: dict) -> None:
        self._write_artifact(experiment_id, "recommendation.json", recommendation)

    def get_recommendation(self, experiment_id: str) -> Optional[dict]:
        return self._read_artifact(experiment_id, "recommendation.json")

    # ── Artifact helpers ──────────────────────────────────────────────────────

    def _artifact_dir(self, experiment_id: str) -> Path:
        path = self._artifacts_base / "experiments" / experiment_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_artifact(self, experiment_id: str, filename: str, data: dict) -> None:
        target = self._artifact_dir(experiment_id) / filename
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _read_artifact(self, experiment_id: str, filename: str) -> Optional[dict]:
        target = self._artifact_dir(experiment_id) / filename
        if not target.exists():
            return None
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
