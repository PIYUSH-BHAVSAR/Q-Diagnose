# core/exceptions.py
# All custom exceptions for the Dataset API layer.
# HTTP translation (exception → status code) happens in api/datasets.py,
# not here — keeping business logic separate from HTTP concerns.


class DatasetAPIError(Exception):
    """Base exception for all Dataset API errors."""
    pass


# ── Format / validation errors ───────────────────────────────────────────────

class UnsupportedFormatError(DatasetAPIError):
    """
    Raised when the uploaded file extension or MIME type is not allowed.
    Maps to HTTP 400 Bad Request.

    Example:
        raise UnsupportedFormatError("exe")
        # → "Unsupported file format: exe. Allowed: csv, xlsx, zip"
    """
    def __init__(self, detected_format: str, allowed: list[str] | None = None):
        self.detected_format = detected_format
        self.allowed = allowed or ["csv", "xlsx", "zip"]
        super().__init__(
            f"Unsupported file format: {detected_format}. "
            f"Allowed formats: {', '.join(self.allowed)}"
        )


class FileSizeLimitError(DatasetAPIError):
    """
    Raised when the upload exceeds the configured max file size.
    Maps to HTTP 413 Request Entity Too Large.
    """
    def __init__(self, actual_mb: float, limit_mb: int):
        self.actual_mb = actual_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"File size {actual_mb:.1f} MB exceeds the limit of {limit_mb} MB."
        )


class InvalidFileError(DatasetAPIError):
    """
    Raised when a file has the right extension but is corrupt or unreadable.
    Maps to HTTP 400 Bad Request.
    """
    pass


# ── Archive-specific errors ──────────────────────────────────────────────────

class InvalidArchiveError(DatasetAPIError):
    """
    Raised when a ZIP file cannot be opened or is structurally broken.
    Maps to HTTP 400 Bad Request.
    """
    pass


class UnsafeArchiveError(DatasetAPIError):
    """
    Raised when a ZIP contains path-traversal entries (../../) or
    exceeds resource limits (zip bomb protection).
    Maps to HTTP 400 Bad Request.
    """
    pass


# ── Storage errors ───────────────────────────────────────────────────────────

class StorageError(DatasetAPIError):
    """
    Raised when the raw file cannot be written to the storage backend.
    Maps to HTTP 500 Internal Server Error.
    """
    pass


# ── Registry / database errors ───────────────────────────────────────────────

class RegistrationError(DatasetAPIError):
    """
    Raised when dataset metadata cannot be persisted to the registry.
    Maps to HTTP 500 Internal Server Error.
    """
    pass


class DatasetNotFoundError(DatasetAPIError):
    """
    Raised when a dataset_id does not exist in the registry.
    Maps to HTTP 404 Not Found.
    """
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        super().__init__(f"Dataset '{dataset_id}' not found.")


# ── Profiling errors ─────────────────────────────────────────────────────────

class ProfilingError(DatasetAPIError):
    """
    Raised when background profiling fails.
    This is caught silently — upload already returned 201 by this point.
    """
    pass
