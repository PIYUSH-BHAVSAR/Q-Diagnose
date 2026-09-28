"""
backend/storage/files.py
Owner: Arzaan
Purpose: LocalFileStorage — the ONLY place that touches the filesystem.
         Business logic (ingestion, loader, etc.) NEVER calls os.path.join directly.
         This abstraction makes future S3/MinIO migration possible without touching
         any ingestion logic (guide_arzaan.md §9, phase1.md §23).

Storage layouts:
  Datasets : {base_path}/datasets/{display_id}/raw/original{ext}
  Profiles : {base_path}/datasets/{display_id}/profile.json
  Artifacts: {base_path}/artifacts/experiments/{experiment_id}/{name}
  Models   : {base_path}/artifacts/experiments/{experiment_id}/models/{filename}
  Data     : {base_path}/artifacts/experiments/{experiment_id}/data/{filename}

Rules (phase1.md §22):
  - Raw dataset file written ONCE and NEVER modified.
  - save_dataset() uses "wb" mode → create. Never "w" or append.
  - read_dataset() returns bytes — caller decides how to interpret.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from backend.core.config import config
from backend.core.exceptions import StorageError
from backend.core.logging import get_logger

logger = get_logger(__name__)


class LocalFileStorage:
    """
    Filesystem storage abstraction.

    All paths returned are *relative* to base_path (matching contract field
    storage_path: "datasets/DS-000001/raw/original.csv").  Callers that need
    an absolute path call .abs(relative_path).
    """

    def __init__(self, base_path: Optional[str | Path] = None) -> None:
        """
        Args:
            base_path: Project root.  Defaults to config.storage_base_path.
        """
        if base_path is None:
            self._base = config.storage_base_path
        else:
            self._base = Path(base_path).resolve()

        # Ensure top-level directories exist on first use
        self._ensure_dirs()

    # ── Public helpers ──────────────────────────────────────────────────────

    def abs(self, relative_path: str) -> Path:
        """Convert a contract relative path to an absolute Path."""
        return (self._base / relative_path).resolve()

    # ── Dataset operations ──────────────────────────────────────────────────

    def save_dataset(self, display_id: str, file_bytes: bytes, filename: str) -> str:
        """
        Save raw uploaded file to immutable storage.

        Storage path: datasets/{display_id}/raw/original{ext}
        Returns the *relative* path string (value of contract field storage_path).

        Raises StorageError on filesystem failure.
        NEVER called twice for the same display_id — immutability guaranteed by
        check-before-write: if path already exists, raises StorageError.
        """
        ext = Path(filename).suffix.lower() or ".csv"
        rel_path = f"datasets/{display_id}/raw/original{ext}"
        abs_path = self._base / rel_path

        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            if abs_path.exists():
                raise StorageError(
                    f"Dataset file already exists at '{rel_path}'. "
                    "Raw dataset files are immutable and cannot be overwritten."
                )
            # Write once, binary, no append
            abs_path.write_bytes(file_bytes)
            logger.info(
                "Dataset saved | display_id=%s rel_path=%s size_bytes=%d",
                display_id, rel_path, len(file_bytes),
            )
            return rel_path
        except StorageError:
            raise
        except OSError as e:
            raise StorageError(f"Failed to save dataset '{filename}': {e}") from e

    def get_dataset_path(self, display_id: str) -> Optional[str]:
        """
        Return relative path for a dataset's raw file, or None if not found.
        Searches for any extension under datasets/{display_id}/raw/.
        """
        raw_dir = self._base / "datasets" / display_id / "raw"
        if not raw_dir.exists():
            return None
        # Find the original file (any extension)
        for p in raw_dir.iterdir():
            if p.stem == "original":
                return str(p.relative_to(self._base))
        return None

    def read_dataset(self, display_id: str) -> bytes:
        """
        Read raw dataset bytes for a registered display_id.
        Used for integrity re-verification after ingestion.

        Raises StorageError if file not found.
        """
        rel_path = self.get_dataset_path(display_id)
        if rel_path is None:
            raise StorageError(f"Dataset file not found for display_id='{display_id}'")
        try:
            return (self._base / rel_path).read_bytes()
        except OSError as e:
            raise StorageError(f"Failed to read dataset for display_id='{display_id}': {e}") from e

    def get_profile_path(self, display_id: str) -> str:
        """
        Return the relative path where the dataset profile JSON should be written.
        Jayed's profiler writes to this path; Shweta reads from it.

        Path: datasets/{display_id}/profile.json
        NOTE: Do NOT derive this from storage_path string manipulation (ISSUES.md M-02).
        """
        return f"datasets/{display_id}/profile.json"

    def save_profile(self, display_id: str, profile_json: str) -> str:
        """
        Write the dataset profile JSON to disk.
        Returns relative path.
        """
        rel_path = self.get_profile_path(display_id)
        abs_path = self._base / rel_path
        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(profile_json, encoding="utf-8")
            logger.info("Profile saved | display_id=%s rel_path=%s", display_id, rel_path)
            return rel_path
        except OSError as e:
            raise StorageError(f"Failed to save profile for display_id='{display_id}': {e}") from e

    # ── Artifact operations ─────────────────────────────────────────────────

    def get_experiment_dir(self, experiment_id: str) -> Path:
        """Absolute path to the experiment artifact directory."""
        return self._base / "artifacts" / "experiments" / experiment_id

    def save_artifact(self, experiment_id: str, name: str, data: bytes) -> str:
        """
        Save a binary artifact for an experiment.
        Returns relative path: artifacts/experiments/{experiment_id}/{name}
        """
        rel_path = f"artifacts/experiments/{experiment_id}/{name}"
        abs_path = self._base / rel_path
        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_bytes(data)
            logger.info(
                "Artifact saved | experiment_id=%s name=%s size=%d",
                experiment_id, name, len(data),
            )
            return rel_path
        except OSError as e:
            raise StorageError(
                f"Failed to save artifact '{name}' for experiment_id='{experiment_id}': {e}"
            ) from e

    def save_text_artifact(self, experiment_id: str, name: str, text: str) -> str:
        """Save a text/JSON artifact. Returns relative path."""
        return self.save_artifact(experiment_id, name, text.encode("utf-8"))

    def read_artifact(self, experiment_id: str, name: str) -> bytes:
        """Read a binary artifact. Raises StorageError if not found."""
        abs_path = self._base / "artifacts" / "experiments" / experiment_id / name
        if not abs_path.exists():
            raise StorageError(
                f"Artifact '{name}' not found for experiment_id='{experiment_id}'"
            )
        try:
            return abs_path.read_bytes()
        except OSError as e:
            raise StorageError(f"Failed to read artifact '{name}': {e}") from e

    def ensure_experiment_dirs(self, experiment_id: str) -> None:
        """Create standard subdirectories for an experiment (data/, models/)."""
        for subdir in ("data", "models"):
            (self._base / "artifacts" / "experiments" / experiment_id / subdir).mkdir(
                parents=True, exist_ok=True
            )

    # ── Internal helpers ────────────────────────────────────────────────────

    def _ensure_dirs(self) -> None:
        """Create all required top-level directories on startup."""
        dirs = [
            self._base / "data" / "uploads",
            self._base / "data" / "demo",
            self._base / "datasets",
            self._base / "artifacts" / "experiments",
            self._base / "artifacts" / "models",
            self._base / "artifacts" / "reports",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Module-level singleton — import this in ingestion service
# ---------------------------------------------------------------------------

file_storage: LocalFileStorage = LocalFileStorage()
