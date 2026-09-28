"""
backend/data/loader.py
Owner: Arzaan
Purpose: DatasetLoader + DatasetIngestionService — the full Phase 1 pipeline.

DatasetLoader:
  - load_csv(file_path) → (dataset_id, DataFrame)   — dynamic, no hardcoded columns
  - get_dataset_info(dataset_id) → dict              — metadata dict for Jayed's profiler

DatasetIngestionService:
  - Class-based (required by Shweta, ISSUES.md B-08)
  - ingest(filename, content_type, file_bytes, db) → dict  (dataset_upload_response.json shape)
  - ingest_from_path(file_path, db) → dict           — convenience for testing

Pipeline steps (guide_arzaan.md §6 step 8):
  1. validate_format        — extension + magic bytes check
  2. check_file_size        — raises FileSizeLimitError
  3. calculate_sha256       — 64-char hex
  4. check_duplicate        — query by sha256
  5. generate_display_id    — DS-{n:06d}
  6. uuid4()                — dataset_id
  7. LocalFileStorage.save_dataset()
  8. DatasetRepository.create()
  9. return contract dict

Contract (dataset_upload_response.json):
  status enum: REGISTERED | REJECTED | INVALID_FORMAT | UNSAFE_ARCHIVE
               | SIZE_LIMIT_EXCEEDED | STORAGE_ERROR
  container_type enum: CSV | XLSX | ZIP | UNKNOWN

Rules:
  - NEVER trust file extensions alone — check actual bytes (phase1.md §11)
  - NEVER overwrite original file (phase1.md §22)
  - NEVER hardcode dataset-specific values (implementation_plan.md §11)
  - NEVER log raw biomedical data (phase1.md §39)
  - Duplicate ≠ Invalid — is_duplicate=true still REGISTERED (phase1.md §18)
"""

from __future__ import annotations

import hashlib
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.core.config import config
from backend.core.exceptions import (
    FileSizeLimitError,
    StorageError,
    UnsafeArchiveError,
    UnsupportedFormatError,
)
from backend.core.logging import get_logger
from backend.storage.files import file_storage
from backend.storage.repositories import DatasetRepository

logger = get_logger(__name__)

# Lazy pandas import — avoids hard dependency at module import time
try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

_dataset_repo = DatasetRepository()

# ---------------------------------------------------------------------------
# Known binary magic-byte signatures to REJECT (phase1.md §11)
# ---------------------------------------------------------------------------

_BINARY_MAGIC_BYTES: list[bytes] = [
    b"\x4d\x5a",          # MZ — Windows PE/EXE
    b"\x7f\x45\x4c\x46",  # ELF — Linux executable
    b"\x25\x50\x44\x46",  # %PDF
    b"\xd0\xcf\x11\xe0",  # MS-CFB (old Office .doc/.xls)
    b"\xff\xd8\xff",       # JPEG
    b"\x89\x50\x4e\x47",  # PNG
    b"\x47\x49\x46",       # GIF
    b"\x42\x4d",           # BMP
    b"\x1f\x8b",           # GZIP
    b"\x42\x5a\x68",       # BZIP2
]

# ZIP magic — special: allowed as container but needs security check
_ZIP_MAGIC = b"\x50\x4b\x03\x04"


# ---------------------------------------------------------------------------
# Format validation helpers
# ---------------------------------------------------------------------------

def _detect_extension(filename: str) -> str:
    """Return lower-case extension including dot, e.g. '.csv'."""
    return Path(filename).suffix.lower()


def _detect_container_type(filename: str, file_bytes: bytes) -> str:
    """
    Determine container type from extension AND first bytes.
    Returns: CSV | XLSX | ZIP | UNKNOWN
    """
    ext = _detect_extension(filename)
    head = file_bytes[:8] if len(file_bytes) >= 8 else file_bytes

    if head[:4] == _ZIP_MAGIC:
        # Could be ZIP or XLSX (XLSX is a ZIP internally)
        if ext in (".xlsx", ".xls"):
            return "XLSX"
        return "ZIP"

    if ext == ".csv":
        return "CSV"
    if ext in (".xlsx", ".xls"):
        return "XLSX"
    if ext == ".zip":
        return "ZIP"

    return "UNKNOWN"


def validate_format(filename: str, file_bytes: bytes) -> Tuple[str, list[str]]:
    """
    Validate file format using BOTH extension and file content.
    Returns (container_type, validation_warnings).
    Raises UnsupportedFormatError if format is not allowed.

    Rules:
      - Reject known binary magic bytes even if extension says .csv
      - Accept only extensions in config.storage.supported_formats
    """
    ext = _detect_extension(filename)
    warnings: list[str] = []
    head = file_bytes[:16] if len(file_bytes) >= 16 else file_bytes

    # 1. Check against binary magic bytes (reject executables, images, etc.)
    for magic in _BINARY_MAGIC_BYTES:
        if head[:len(magic)] == magic:
            raise UnsupportedFormatError(
                filename=filename,
                detected_ext=ext,
            )

    # 2. Extension must be in supported list
    if ext not in config.storage.supported_formats:
        raise UnsupportedFormatError(filename=filename, detected_ext=ext)

    # 3. Determine container type
    container_type = _detect_container_type(filename, file_bytes)

    # 4. Warn if extension says CSV but bytes look non-printable
    if ext == ".csv" and container_type == "UNKNOWN":
        warnings.append(
            f"File '{filename}' has .csv extension but content appears non-standard."
        )

    return container_type, warnings


def validate_zip(file_bytes: bytes) -> None:
    """
    Security check for ZIP archives (phase1.md §14).
    Only inspects metadata — does NOT parse CSV contents inside.

    Raises UnsafeArchiveError on:
      - Invalid ZIP structure
      - Path traversal entries (../)
      - Entry count > 100,000
      - Estimated uncompressed size > config.storage.max_uncompressed_size_gb GB
    """
    max_uncompressed = config.storage.max_uncompressed_size_gb * 1024 * 1024 * 1024

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            entries = zf.infolist()

            # Check entry count
            if len(entries) > 100_000:
                raise UnsafeArchiveError(
                    f"Archive contains {len(entries):,} entries (limit: 100,000)."
                )

            total_uncompressed = 0
            for entry in entries:
                # Path traversal check
                if ".." in entry.filename or entry.filename.startswith("/"):
                    raise UnsafeArchiveError(
                        f"Archive contains unsafe path: '{entry.filename}'"
                    )
                total_uncompressed += entry.file_size

                # Incremental size check (zip bomb detection)
                if total_uncompressed > max_uncompressed:
                    raise UnsafeArchiveError(
                        f"Archive uncompressed size exceeds "
                        f"{config.storage.max_uncompressed_size_gb} GB limit."
                    )
    except zipfile.BadZipFile as e:
        raise UnsafeArchiveError(f"Invalid ZIP archive: {e}") from e


def calculate_sha256(file_bytes: bytes) -> str:
    """Return SHA-256 hex digest (64 lowercase hex chars)."""
    return hashlib.sha256(file_bytes).hexdigest()


# ---------------------------------------------------------------------------
# DatasetLoader
# ---------------------------------------------------------------------------

class DatasetLoader:
    """
    Utility for loading registered datasets back into memory.
    Used by Jayed's profiler and preprocessing pipeline.

    All loading is dynamic — never hardcodes column names or row counts.
    """

    def load_csv(self, file_path: str) -> Tuple[str, "pd.DataFrame"]:
        """
        Load a CSV file from an absolute or relative path.
        Returns (dataset_id_placeholder, DataFrame).

        The dataset_id returned here is a placeholder — the real UUID is
        assigned during ingestion and stored in the DB.  Callers that need
        the real ID should use get_dataset_info() after querying the DB.

        Raises ImportError if pandas is not installed.
        Raises FileNotFoundError if file does not exist.
        """
        if not _PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for DatasetLoader.load_csv(). "
                "Install it: pip install pandas"
            )

        path = Path(file_path)
        if not path.is_absolute():
            path = config.storage_base_path / path

        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: '{path}'")

        df = pd.read_csv(str(path), low_memory=False)
        # Placeholder ID derived from filename — real UUID is in the DB
        placeholder_id = path.stem
        return placeholder_id, df

    def get_dataset_info(self, display_id: str) -> dict:
        """
        Return metadata dict for a registered dataset.
        This is the shape Jayed's DatasetProfiler expects:
          {
            "id":      "<UUID>",
            "name":    "breast_cancer.csv",
            "path":    "datasets/DS-000001/raw/original.csv",
            "hash":    "<sha256>",
            "rows":    None,     ← Jayed fills by reading file
            "columns": None,
            "target":  None
          }

        Raises FileNotFoundError if display_id not registered.
        """
        rel_path = file_storage.get_dataset_path(display_id)
        if rel_path is None:
            raise FileNotFoundError(
                f"No raw dataset file found for display_id='{display_id}'"
            )

        abs_path = file_storage.abs(rel_path)
        filename = abs_path.name

        # Recompute hash from stored file to allow Jayed to verify integrity
        try:
            file_bytes = abs_path.read_bytes()
            sha256 = calculate_sha256(file_bytes)
        except OSError:
            sha256 = None

        return {
            "id": display_id,       # Jayed queries DB for real UUID; this is display_id
            "name": filename,
            "path": rel_path,       # relative path — Jayed resolves against base_path
            "hash": sha256,
            "rows": None,           # Jayed calculates dynamically
            "columns": None,        # Jayed calculates dynamically
            "target": None,         # Jayed detects via adapter
        }


# ---------------------------------------------------------------------------
# DatasetIngestionService
# ---------------------------------------------------------------------------

class DatasetIngestionService:
    """
    Full Phase 1 ingestion pipeline as a class.
    Class-based interface required by Shweta's route handler (ISSUES.md B-08).

    Usage (in Shweta's api/datasets.py):
        service = DatasetIngestionService(db=db)
        result  = await service.ingest(filename, content_type, file_bytes)

    Usage (standalone / testing):
        result = DatasetIngestionService.ingest_from_path("data/demo/breast_cancer.csv", db)
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = DatasetRepository()
        self._storage = file_storage

    # ── Public API ──────────────────────────────────────────────────────────

    def ingest(
        self,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> dict:
        """
        Run the full ingestion pipeline.

        Returns a dict matching contracts/dataset_upload_response.json exactly.
        On validation failure, returns a dict with the appropriate error status
        rather than raising (so Shweta can return a 200/422 response to frontend).

        Raises:
            StorageError  — filesystem failure (unrecoverable)
        """
        upload_timestamp = datetime.now(timezone.utc)

        # ── Step 1: Format validation ────────────────────────────────────────
        try:
            container_type, warnings = validate_format(filename, file_bytes)
        except UnsupportedFormatError as e:
            logger.warning(
                "Format validation failed | filename=%s ext=%s",
                filename, e.detected_ext,
            )
            return self._error_response(
                filename=filename,
                status="INVALID_FORMAT",
                rejection_reason=str(e),
                upload_timestamp=upload_timestamp,
                file_size_bytes=len(file_bytes),
            )

        # ── Step 2: ZIP security check ───────────────────────────────────────
        if container_type == "ZIP":
            try:
                validate_zip(file_bytes)
            except UnsafeArchiveError as e:
                logger.warning(
                    "ZIP security check failed | filename=%s reason=%s",
                    filename, e.reason,
                )
                return self._error_response(
                    filename=filename,
                    status="UNSAFE_ARCHIVE",
                    rejection_reason=str(e),
                    upload_timestamp=upload_timestamp,
                    file_size_bytes=len(file_bytes),
                    container_type=container_type,
                )

        # ── Step 3: File size check ──────────────────────────────────────────
        try:
            self._check_size(filename, file_bytes)
        except FileSizeLimitError as e:
            logger.warning(
                "File size exceeded | filename=%s size_bytes=%d limit_mb=%d",
                filename, e.size_bytes, e.limit_mb,
            )
            return self._error_response(
                filename=filename,
                status="SIZE_LIMIT_EXCEEDED",
                rejection_reason=str(e),
                upload_timestamp=upload_timestamp,
                file_size_bytes=len(file_bytes),
                container_type=container_type,
            )

        # ── Step 4: SHA-256 hash ─────────────────────────────────────────────
        sha256 = calculate_sha256(file_bytes)
        logger.info(
            "File hashed | filename=%s sha256_prefix=%s size=%d",
            filename, sha256[:8], len(file_bytes),
        )

        # ── Step 5: Duplicate detection ──────────────────────────────────────
        is_duplicate = False
        duplicate_of: Optional[str] = None
        existing = self._repo.get_by_sha256(self._db, sha256)
        if existing is not None:
            is_duplicate = True
            duplicate_of = existing.id
            logger.info(
                "Duplicate detected | sha256_prefix=%s duplicate_of=%s",
                sha256[:8], duplicate_of,
            )
            # Duplicate is NOT a rejection — still register (phase1.md §18)

        # ── Step 6: Generate display_id ──────────────────────────────────────
        display_id = self._generate_display_id()

        # ── Step 7: Generate UUID ────────────────────────────────────────────
        dataset_id = str(uuid4())

        # ── Step 8: Save file to storage ─────────────────────────────────────
        try:
            storage_path = self._storage.save_dataset(display_id, file_bytes, filename)
        except StorageError as e:
            logger.error(
                "Storage failure | filename=%s display_id=%s error=%s",
                filename, display_id, str(e),
            )
            return self._error_response(
                filename=filename,
                status="STORAGE_ERROR",
                rejection_reason=str(e),
                upload_timestamp=upload_timestamp,
                file_size_bytes=len(file_bytes),
                container_type=container_type,
            )

        # ── Step 9: Persist to DB ─────────────────────────────────────────────
        dataset_data = {
            "id": dataset_id,
            "display_id": display_id,
            "original_filename": filename,
            "container_type": container_type,
            "file_size_bytes": len(file_bytes),
            "sha256": sha256,
            "raw_storage_path": storage_path,
            "upload_timestamp": upload_timestamp,
            "status": "REGISTERED",
            "created_by": "system",
            "is_duplicate": is_duplicate,
            "duplicate_of": duplicate_of,
        }
        dataset = self._repo.create(self._db, dataset_data)

        # ── Step 10: Build and return contract response ───────────────────────
        response = {
            "dataset_id": dataset.id,
            "display_id": dataset.display_id,
            "status": "REGISTERED",
            "filename": dataset.original_filename,
            "container_type": dataset.container_type,
            "upload_timestamp": upload_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "file_size_bytes": dataset.file_size_bytes,
            "sha256": dataset.sha256,
            "storage_path": dataset.raw_storage_path,
            "is_duplicate": dataset.is_duplicate,
            "duplicate_of": dataset.duplicate_of,
            "validation_warnings": warnings,
            "rejection_reason": None,
        }

        logger.info(
            "Dataset registered | dataset_id=%s display_id=%s filename=%s "
            "is_duplicate=%s sha256_prefix=%s",
            dataset.id, dataset.display_id, filename,
            is_duplicate, sha256[:8],
        )
        return response

    @classmethod
    def ingest_from_path(cls, file_path: str, db: Session) -> dict:
        """
        Convenience method for testing — ingest a file directly from disk path.
        Resolves path relative to config.storage_base_path if not absolute.
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = config.storage_base_path / path

        if not path.exists():
            raise FileNotFoundError(f"File not found: '{path}'")

        file_bytes = path.read_bytes()
        filename = path.name
        # Determine MIME content_type hint from extension
        ext = path.suffix.lower()
        content_type_map = {
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".zip": "application/zip",
        }
        content_type = content_type_map.get(ext, "application/octet-stream")

        service = cls(db=db)
        return service.ingest(filename, content_type, file_bytes)

    # ── Private helpers ─────────────────────────────────────────────────────

    def _check_size(self, filename: str, file_bytes: bytes) -> None:
        """Raise FileSizeLimitError if file exceeds configured limit."""
        limit_bytes = config.get_max_file_size_bytes()
        if len(file_bytes) > limit_bytes:
            raise FileSizeLimitError(
                filename=filename,
                size_bytes=len(file_bytes),
                limit_mb=config.storage.max_file_size_mb,
            )

    def _generate_display_id(self) -> str:
        """
        Generate next sequential display_id: DS-000001, DS-000002, ...
        Uses max existing number from DB (not count) so IDs are monotonically
        increasing even after deletions or DB resets with existing files on disk.
        Thread-safe within a single process (DB commit serialises it).
        """
        max_n = self._repo.max_display_number(self._db)
        return f"DS-{max_n + 1:06d}"

    @staticmethod
    def _error_response(
        filename: str,
        status: str,
        rejection_reason: str,
        upload_timestamp: datetime,
        file_size_bytes: int,
        container_type: str = "UNKNOWN",
    ) -> dict:
        """Build a contract-compliant error response dict (no DB record created)."""
        return {
            "dataset_id": None,
            "display_id": None,
            "status": status,
            "filename": filename,
            "container_type": container_type,
            "upload_timestamp": upload_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "file_size_bytes": file_size_bytes,
            "sha256": None,
            "storage_path": None,
            "is_duplicate": False,
            "duplicate_of": None,
            "validation_warnings": [],
            "rejection_reason": rejection_reason,
        }
