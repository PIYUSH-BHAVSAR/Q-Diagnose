# storage/database.py
#
# DatasetRegistry — a lightweight JSON-file registry for MVP/standalone development.
#
# WHY JSON INSTEAD OF SQLITE/POSTGRES?
#   Arzaan owns the real database layer (storage/database.py in the team repo).
#   Until that exists, we use a local JSON file so you can develop, test, and
#   show Naeem working endpoints without any DB setup.
#
# SWAP PATH:
#   When Arzaan's SQLAlchemy models land, replace this class with one that
#   talks to Session — the ingestion_service.py and api/datasets.py callers
#   never need to change because they only call:
#       registry.save(record)
#       registry.get_by_id(dataset_id)
#       registry.list_all()
#       registry.find_by_sha256(sha256)
#       registry.next_display_id()

import json
import os
import threading
from pathlib import Path
from typing import Optional

from core.config import config
from core.exceptions import DatasetNotFoundError, RegistrationError
from core.logging_config import get_logger

logger = get_logger("storage.database")

# Thread lock so concurrent uploads don't corrupt the JSON file
_lock = threading.Lock()


class DatasetRegistry:
    """
    Persistent dataset metadata store backed by a JSON file.

    File structure:
    {
        "counter": 3,
        "datasets": {
            "<uuid>": { ...record... },
            ...
        }
    }
    """

    def __init__(self):
        self._path = Path(config.database.registry_path)
        self._ensure_file_exists()

    # ── Public interface ──────────────────────────────────────────────────────

    def save(self, record: dict) -> None:
        """
        Persist a new dataset record.
        Raises RegistrationError on any I/O failure.
        """
        with _lock:
            db = self._load()
            dataset_id = record["dataset_id"]
            db["datasets"][dataset_id] = record
            self._write(db)
        logger.info(f"Registered | dataset_id={dataset_id} | display_id={record['display_id']}")

    def get_by_id(self, dataset_id: str) -> dict:
        """
        Return a single record by UUID.
        Raises DatasetNotFoundError if not found.
        """
        db = self._load()
        record = db["datasets"].get(dataset_id)
        if record is None:
            raise DatasetNotFoundError(dataset_id)
        return record

    def list_all(self, offset: int = 0, limit: int = 100) -> tuple[list[dict], int]:
        """
        Return (page, total_count) sorted by upload_timestamp descending.
        Most recently uploaded dataset comes first.
        """
        db = self._load()
        all_records = list(db["datasets"].values())
        # Sort newest-first
        all_records.sort(key=lambda r: r.get("upload_timestamp", ""), reverse=True)
        total = len(all_records)
        page = all_records[offset : offset + limit]
        return page, total

    def find_by_sha256(self, sha256: str) -> Optional[str]:
        """
        Check if a dataset with this exact SHA-256 already exists.
        Returns the existing dataset_id, or None if it's a new file.
        """
        db = self._load()
        for dataset_id, record in db["datasets"].items():
            if record.get("sha256") == sha256:
                return dataset_id
        return None

    def next_display_id(self) -> str:
        """
        Atomically increment the counter and return the next display ID.
        Returns strings like "DS-000001", "DS-000002", etc.
        """
        with _lock:
            db = self._load()
            db["counter"] = db.get("counter", 0) + 1
            counter = db["counter"]
            self._write(db)
        return f"DS-{counter:06d}"

    def profile_exists(self, dataset_id: str) -> bool:
        """
        Check whether a profile JSON file exists for a dataset.
        This is used by the list endpoint to populate has_profile.
        """
        profile_path = (
            Path(config.storage_base_path) / dataset_id / "profile.json"
        )
        return profile_path.exists()

    def save_profile(self, dataset_id: str, profile_data: dict) -> None:
        """
        Save Jayed's profiler output as profile.json next to the raw file.
        Called from the background profiling task in api/datasets.py.
        """
        profile_dir = Path(config.storage_base_path) / dataset_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_path = profile_dir / "profile.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)
        logger.info(f"Profile saved | dataset_id={dataset_id}")

    def load_profile(self, dataset_id: str) -> Optional[dict]:
        """
        Load the profile JSON for a dataset.
        Returns None if the file doesn't exist yet (profiling still in progress).
        """
        profile_path = (
            Path(config.storage_base_path) / dataset_id / "profile.json"
        )
        if not profile_path.exists():
            return None
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_file_exists(self) -> None:
        """Create the registry file with an empty structure if it doesn't exist."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({"counter": 0, "datasets": {}})
            logger.info(f"Registry created | path={self._path}")

    def _load(self) -> dict:
        """Read and parse the JSON registry file."""
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise RegistrationError(f"Cannot read registry file '{self._path}': {e}") from e

    def _write(self, db: dict) -> None:
        """Write the in-memory dict back to the JSON file atomically."""
        try:
            # Write to a temp file first, then rename — prevents corruption on crash
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self._path)   # atomic on all platforms
        except OSError as e:
            raise RegistrationError(f"Cannot write registry file '{self._path}': {e}") from e


# ── FastAPI dependency ────────────────────────────────────────────────────────
# Used with Depends() in route handlers that need a fresh registry instance.
# When swapping to SQLAlchemy, this becomes a real Session factory.

def get_registry() -> DatasetRegistry:
    """FastAPI dependency: yields a DatasetRegistry instance."""
    return DatasetRegistry()
