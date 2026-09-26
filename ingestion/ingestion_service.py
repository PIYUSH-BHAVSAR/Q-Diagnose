# ingestion/ingestion_service.py
#
# DatasetIngestionService — the single function Shweta calls from the upload route.
#
# It orchestrates all Phase 1 sub-steps in the correct order:
#
#   1. Receive bytes in memory (done in the route, passed here)
#   2. Validate format  (Module 2 from phase1.md §10)
#   3. Validate archive (Module 3 — ZIP only, phase1.md §13)
#   4. Hash the content (Module 4, phase1.md §16)
#   5. Check duplicates (phase1.md §18)
#   6. Generate dataset ID (Module 5, phase1.md §19)
#   7. Store raw file   (Module 6, phase1.md §21)
#   8. Register metadata (Module 7, phase1.md §24)
#
# What this file does NOT do:
#   - Profile the dataset  → that's Jayed's DatasetProfiler
#   - Decide ML task/target → that's Phase 2
#   - Modify the uploaded bytes in any way

import hashlib
import io
import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from core.config import config
from core.exceptions import (
    FileSizeLimitError,
    InvalidArchiveError,
    InvalidFileError,
    RegistrationError,
    StorageError,
    UnsafeArchiveError,
    UnsupportedFormatError,
)
from core.logging_config import get_logger
from storage.database import DatasetRegistry

logger = get_logger("ingestion")

# ── Magic-byte signatures for format validation (phase1.md §11) ──────────────
# Never trust file extension alone — check actual file bytes.
_MAGIC_BYTES: dict[str, list[bytes]] = {
    "csv":  [],                          # CSV has no magic bytes; validated by readability
    "xlsx": [b"PK\x03\x04"],            # XLSX is a ZIP-based format (Office Open XML)
    "zip":  [b"PK\x03\x04"],            # Standard ZIP local file header
}

# MIME types accepted for each format
_ALLOWED_MIME: dict[str, list[str]] = {
    "csv":  ["text/csv", "text/plain", "application/csv", "application/octet-stream"],
    "xlsx": [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream",
    ],
    "zip":  ["application/zip", "application/x-zip-compressed", "application/octet-stream"],
}


class DatasetIngestionService:
    """
    Orchestrates all Phase 1 ingestion steps.

    Usage (in the upload route):
        service = DatasetIngestionService()
        result  = service.ingest(filename, content_type, file_bytes)
        # result is a dict matching the dataset_upload_response.json contract
    """

    def __init__(self):
        self._registry = DatasetRegistry()

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest(
        self,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> dict:
        """
        Full ingestion pipeline. Returns the upload response contract dict.
        Raises specific exceptions that the route maps to HTTP status codes.
        """
        logger.info(f"Ingestion started | file={filename!r} | size={len(file_bytes)} bytes")

        # Step 1 — size check (fast, do it before anything else)
        self._check_size(filename, file_bytes)

        # Step 2 — format validation
        fmt = self._validate_format(filename, content_type, file_bytes)
        logger.info(f"Format validated | format={fmt}")

        # Step 3 — ZIP-specific security validation
        zip_meta: dict | None = None
        if fmt == "zip":
            zip_meta = self._validate_archive(file_bytes)
            logger.info(f"Archive validated | entries={zip_meta['entry_count']}")

        # Step 4 — SHA-256 hash
        sha256 = self._hash(file_bytes)
        logger.info(f"Hash computed | sha256={sha256[:16]}...")

        # Step 5 — duplicate detection
        existing_id = self._registry.find_by_sha256(sha256)
        is_duplicate = existing_id is not None
        if is_duplicate:
            logger.info(f"Duplicate detected | existing_id={existing_id}")

        # Step 6 — generate unique dataset ID
        dataset_id  = str(uuid.uuid4())
        display_id  = self._registry.next_display_id()          # "DS-000001", "DS-000002", …
        logger.info(f"Dataset ID generated | dataset_id={dataset_id} | display_id={display_id}")

        # Step 7 — store raw file (immutable original, never modified)
        storage_path = self._store_raw(dataset_id, display_id, fmt, file_bytes)
        logger.info(f"Raw file stored | path={storage_path}")

        # Step 8 — register metadata
        timestamp = datetime.now(timezone.utc).isoformat()
        record = {
            "dataset_id":       dataset_id,
            "display_id":       display_id,
            "original_filename": filename,
            "container_type":   fmt.upper(),
            "file_size_bytes":  len(file_bytes),
            "sha256":           sha256,
            "raw_storage_path": storage_path,
            "upload_timestamp": timestamp,
            "status":           "REGISTERED",
            "is_duplicate":     is_duplicate,
            "duplicate_of":     existing_id if is_duplicate else None,
            "zip_meta":         zip_meta,
        }
        self._registry.save(record)
        logger.info(f"Dataset registered | display_id={display_id} | status=REGISTERED")

        # Build the upload response contract shape (matches dataset_upload_response.json)
        return {
            "dataset_id":          dataset_id,
            "display_id":          display_id,
            "status":              "REGISTERED",
            "filename":            filename,
            "container_type":      fmt.upper(),
            "upload_timestamp":    timestamp,
            "file_size_bytes":     len(file_bytes),
            "sha256":              sha256,
            "storage_path":        storage_path,
            "is_duplicate":        is_duplicate,
            "duplicate_of":        existing_id if is_duplicate else None,
            "validation_warnings": [],
            "rejection_reason":    None,
        }

    # ── Step 1: Size check ────────────────────────────────────────────────────

    def _check_size(self, filename: str, file_bytes: bytes) -> None:
        size_mb = len(file_bytes) / (1024 * 1024)
        limit   = config.max_file_size_mb
        if size_mb > limit:
            logger.warning(f"Size limit exceeded | file={filename!r} | size={size_mb:.1f}MB | limit={limit}MB")
            raise FileSizeLimitError(actual_mb=size_mb, limit_mb=limit)

    # ── Step 2: Format validation ─────────────────────────────────────────────

    def _validate_format(self, filename: str, content_type: str, file_bytes: bytes) -> str:
        """
        Returns the detected format string ("csv" | "xlsx" | "zip").
        Raises UnsupportedFormatError if not allowed.

        Does NOT trust extension alone — also checks magic bytes for xlsx/zip.
        """
        ext = Path(filename).suffix.lstrip(".").lower()

        if ext not in config.supported_formats:
            raise UnsupportedFormatError(
                detected_format=ext or "(no extension)",
                allowed=config.supported_formats,
            )

        # Magic-byte check for binary formats
        if ext in ("xlsx", "zip"):
            magic = _MAGIC_BYTES[ext]
            if magic and not any(file_bytes.startswith(m) for m in magic):
                raise InvalidFileError(
                    f"File '{filename}' has extension .{ext} but does not match "
                    f"the expected file signature. It may be corrupt or mislabeled."
                )

        # CSV: attempt minimal readability check (first 4KB)
        if ext == "csv":
            try:
                sample = file_bytes[:4096].decode("utf-8", errors="replace")
                if len(sample.strip()) == 0:
                    raise InvalidFileError(f"CSV file '{filename}' appears to be empty.")
            except Exception as e:
                raise InvalidFileError(f"Cannot read CSV file '{filename}': {e}") from e

        return ext

    # ── Step 3: ZIP security validation ──────────────────────────────────────

    def _validate_archive(self, file_bytes: bytes) -> dict:
        """
        Validates the ZIP archive for safety.
        Returns metadata dict (entry count, sizes, etc.) — does NOT extract files.
        Raises InvalidArchiveError or UnsafeArchiveError.
        """
        try:
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
        except zipfile.BadZipFile as e:
            raise InvalidArchiveError(f"Cannot open ZIP file: {e}") from e

        entries        = zf.infolist()
        entry_count    = len(entries)
        compressed_sz  = len(file_bytes)
        uncomp_sz      = sum(e.file_size for e in entries)

        # ── Resource limits (phase1.md §13) ──────────────────────────────────
        max_entries = config.archive.max_entries
        if entry_count > max_entries:
            raise UnsafeArchiveError(
                f"Archive has {entry_count:,} entries, exceeding limit of {max_entries:,}."
            )

        max_uncomp_bytes = config.archive.max_uncompressed_size_gb * 1024 ** 3
        if uncomp_sz > max_uncomp_bytes:
            raise UnsafeArchiveError(
                f"Archive uncompressed size {uncomp_sz / 1024**3:.1f} GB "
                f"exceeds limit of {config.archive.max_uncompressed_size_gb} GB."
            )

        # ── Path traversal check (phase1.md §13 point 5) ─────────────────────
        for entry in entries:
            name = entry.filename
            # Reject absolute paths and parent-directory traversal
            if name.startswith("/") or ".." in name.split("/"):
                raise UnsafeArchiveError(
                    f"Unsafe path in archive entry: '{name}'. "
                    "Path traversal detected."
                )

        zf.close()

        return {
            "archive_valid":                    True,
            "entry_count":                      entry_count,
            "compressed_size_bytes":            compressed_sz,
            "estimated_uncompressed_size_bytes": uncomp_sz,
            "security_status":                  "SAFE_FOR_REGISTRATION",
        }

    # ── Step 4: Hash ──────────────────────────────────────────────────────────

    def _hash(self, file_bytes: bytes) -> str:
        """Returns hex-encoded SHA-256 of the raw file bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    # ── Step 7: Store raw file ────────────────────────────────────────────────

    def _store_raw(
        self,
        dataset_id: str,
        display_id: str,
        fmt: str,
        file_bytes: bytes,
    ) -> str:
        """
        Saves the immutable original file to:
            <base_path>/<dataset_id>/raw/original.<ext>

        Returns the relative storage path (suitable for the DB record).
        Raises StorageError on any I/O problem.
        """
        # Use UUID folder so no two datasets ever collide
        raw_dir = Path(config.storage_base_path) / dataset_id / "raw"
        try:
            raw_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Cannot create storage directory '{raw_dir}': {e}") from e

        dest_file = raw_dir / f"original.{fmt}"
        try:
            dest_file.write_bytes(file_bytes)
        except OSError as e:
            raise StorageError(f"Cannot write dataset to '{dest_file}': {e}") from e

        # Return a relative path — no absolute paths stored in registry
        relative = f"{dataset_id}/raw/original.{fmt}"
        return relative
