"""
backend/core/exceptions.py
Owner: Arzaan
Purpose: All custom exceptions used platform-wide.
         Every teammate imports exception classes from here — never define
         exceptions locally in individual modules.

Hierarchy:
    QMLPlatformError (base)
    ├── DatasetValidationError
    ├── UnsupportedFormatError
    ├── FileSizeLimitError
    ├── UnsafeArchiveError
    ├── StorageError
    ├── ExperimentNotFoundError
    ├── DatasetNotFoundError
    └── DataLeakageError
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class QMLPlatformError(Exception):
    """
    Base exception for all Q-Diagnose platform errors.
    Catch this to handle any platform-level failure generically.
    """
    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# ---------------------------------------------------------------------------
# Dataset / Ingestion errors
# ---------------------------------------------------------------------------

class DatasetValidationError(QMLPlatformError):
    """Raised when an uploaded file fails content or structural validation."""


class UnsupportedFormatError(QMLPlatformError):
    """
    Raised when file extension or detected MIME type is not in supported_formats.
    Maps to status='INVALID_FORMAT' in dataset_upload_response.json.
    """
    def __init__(self, filename: str, detected_ext: str) -> None:
        super().__init__(
            f"Unsupported file format: '{detected_ext}' for file '{filename}'. "
            "Supported formats: .csv, .xlsx, .zip",
            code="INVALID_FORMAT",
        )
        self.filename = filename
        self.detected_ext = detected_ext


class FileSizeLimitError(QMLPlatformError):
    """
    Raised when uploaded file exceeds config.storage.max_file_size_mb.
    Maps to status='SIZE_LIMIT_EXCEEDED' in dataset_upload_response.json.
    """
    def __init__(self, filename: str, size_bytes: int, limit_mb: int) -> None:
        size_mb = size_bytes / (1024 * 1024)
        super().__init__(
            f"File '{filename}' is {size_mb:.2f} MB, exceeds limit of {limit_mb} MB.",
            code="SIZE_LIMIT_EXCEEDED",
        )
        self.filename = filename
        self.size_bytes = size_bytes
        self.limit_mb = limit_mb


class UnsafeArchiveError(QMLPlatformError):
    """
    Raised when a ZIP archive fails security checks (path traversal, bomb, etc.).
    Maps to status='UNSAFE_ARCHIVE' in dataset_upload_response.json.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(f"Unsafe archive detected: {reason}", code="UNSAFE_ARCHIVE")
        self.reason = reason


class InvalidFileError(DatasetValidationError):
    """Raised when file contents are corrupt or unreadable."""


class InvalidArchiveError(DatasetValidationError):
    """Raised when an archive cannot be extracted."""


class DatasetNotFoundError(QMLPlatformError):
    """Raised when a dataset_id is not found in the registry. Maps to HTTP 404."""
    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset not found: '{dataset_id}'", code="DATASET_NOT_FOUND")
        self.dataset_id = dataset_id


class StorageError(QMLPlatformError):
    """
    Raised when filesystem or database storage operations fail.
    Maps to status='STORAGE_ERROR' in dataset_upload_response.json.
    """


class RegistrationError(StorageError):
    """Raised when dataset registration fails in the repository."""


# ---------------------------------------------------------------------------
# Experiment errors
# ---------------------------------------------------------------------------

class ExperimentNotFoundError(QMLPlatformError):
    """Raised when an experiment_id is not found. Maps to HTTP 404."""
    def __init__(self, experiment_id: str) -> None:
        super().__init__(
            f"Experiment not found: '{experiment_id}'",
            code="EXPERIMENT_NOT_FOUND",
        )
        self.experiment_id = experiment_id


# ---------------------------------------------------------------------------
# ML / pipeline errors
# ---------------------------------------------------------------------------

class DataLeakageError(QMLPlatformError):
    """
    Raised when a data leakage risk is detected (e.g. scaler fitted on combined
    train+test data, or target column present in features).
    Hard error — execution must stop.
    """


# ---------------------------------------------------------------------------
# Pipeline errors (used by Jayed's data pipeline phases 2-6)
# These are re-exported here so all teammates import from one place.
# ---------------------------------------------------------------------------

class PipelineError(QMLPlatformError):
    """Base exception for data pipeline errors."""
    pass


class DataLoadError(PipelineError):
    """Raised when data cannot be loaded from the source."""
    pass


class ProfilingError(PipelineError):
    """Raised when dataset profiling fails."""
    pass


class DataValidationError(PipelineError):
    """Raised when dataset fails critical validation checks."""
    pass


class PreprocessingError(PipelineError):
    """Raised when preprocessing fails."""
    pass


class FeatureEngineeringError(PipelineError):
    """Raised when feature engineering fails."""
    pass


class DimensionalityReductionError(PipelineError):
    """Raised when PCA / dimensionality reduction fails."""
    pass
