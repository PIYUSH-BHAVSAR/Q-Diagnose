# api/datasets.py
#
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Q-Diagnose — Dataset API                                               ║
# ║  Owner: Shweta                                                          ║
# ║  Phase: 1 (phase1.md §28-30)                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# ENDPOINTS (4 real + 1 mock for Naeem):
#
#   POST   /api/datasets/upload          → upload a CSV/XLSX/ZIP dataset
#   GET    /api/datasets                 → list all registered datasets
#   GET    /api/datasets/{dataset_id}    → get single dataset metadata
#   GET    /api/datasets/{dataset_id}/profile  → get profiling results
#   GET    /api/datasets/demo/breast-cancer    → hardcoded mock (Naeem dev helper)
#
# RULES followed (from guide_shweta.md §9):
#   • UploadFile read once — stored in file_bytes, never re-read
#   • Background profiling uses its OWN registry (not the request-scoped one)
#   • Duplicate uploads return 201 + is_duplicate=true  (NOT 409)
#   • Profile not ready → 202  (NOT 404)
#   • All errors are HTTPException — no raw Python tracebacks to client
#   • Never log file content or biomedical data

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.config import config
from core.exceptions import (
    DatasetNotFoundError,
    FileSizeLimitError,
    InvalidArchiveError,
    InvalidFileError,
    RegistrationError,
    StorageError,
    UnsafeArchiveError,
    UnsupportedFormatError,
)
from core.logging_config import get_logger
from ingestion.ingestion_service import DatasetIngestionService
from storage.database import DatasetRegistry, get_registry

logger = get_logger("api.datasets")

# ── Router ────────────────────────────────────────────────────────────────────
# Registered in main.py with: app.include_router(datasets.router)
router = APIRouter(prefix="/api/datasets", tags=["datasets"])


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC RESPONSE MODELS
# Define ALL shapes before writing any route logic.
# These drive FastAPI's /docs page and give type-safe returns.
# ══════════════════════════════════════════════════════════════════════════════

class DatasetUploadResponse(BaseModel):
    """
    Returned on successful POST /api/datasets/upload.
    Shape matches contracts/dataset_upload_response.json exactly.
    HTTP 201 Created.
    """
    dataset_id:          str
    display_id:          str
    status:              str                   # "REGISTERED" | "REJECTED"
    filename:            str
    container_type:      str                   # "CSV" | "XLSX" | "ZIP"
    upload_timestamp:    str                   # ISO 8601
    file_size_bytes:     int
    sha256:              str
    storage_path:        str
    is_duplicate:        bool
    duplicate_of:        Optional[str]         # dataset_id of the original, or null
    validation_warnings: List[str]
    rejection_reason:    Optional[str]

    model_config = {"json_schema_extra": {
        "example": {
            "dataset_id":          "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
            "display_id":          "DS-000001",
            "status":              "REGISTERED",
            "filename":            "breast_cancer.csv",
            "container_type":      "CSV",
            "upload_timestamp":    "2026-09-10T14:23:45.123Z",
            "file_size_bytes":     125847,
            "sha256":              "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
            "storage_path":        "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7/raw/original.csv",
            "is_duplicate":        False,
            "duplicate_of":        None,
            "validation_warnings": [],
            "rejection_reason":    None,
        }
    }}


class DatasetSummary(BaseModel):
    """One item in the list response."""
    dataset_id:       str
    display_id:       str
    filename:         str
    container_type:   str
    file_size_bytes:  int
    status:           str
    upload_timestamp: str
    has_profile:      bool                     # True once background profiling is done


class DatasetListResponse(BaseModel):
    """
    Returned by GET /api/datasets.
    HTTP 200 OK.
    """
    datasets: List[DatasetSummary]
    total:    int

    model_config = {"json_schema_extra": {
        "example": {
            "datasets": [{
                "dataset_id":       "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
                "display_id":       "DS-000001",
                "filename":         "breast_cancer.csv",
                "container_type":   "CSV",
                "file_size_bytes":  125847,
                "status":           "REGISTERED",
                "upload_timestamp": "2026-09-10T14:23:45.123Z",
                "has_profile":      True,
            }],
            "total": 1,
        }
    }}


class DatasetDetailResponse(BaseModel):
    """
    Returned by GET /api/datasets/{dataset_id}.
    HTTP 200 OK.
    """
    dataset_id:       str
    display_id:       str
    filename:         str
    container_type:   str
    file_size_bytes:  int
    sha256:           str
    status:           str
    upload_timestamp: str
    storage_path:     str
    is_duplicate:     bool
    duplicate_of:     Optional[str]

    model_config = {"json_schema_extra": {
        "example": {
            "dataset_id":       "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
            "display_id":       "DS-000001",
            "filename":         "breast_cancer.csv",
            "container_type":   "CSV",
            "file_size_bytes":  125847,
            "sha256":           "a1b2c3d4e5f67890abcdef1234567890",
            "status":           "REGISTERED",
            "upload_timestamp": "2026-09-10T14:23:45.123Z",
            "storage_path":     "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7/raw/original.csv",
            "is_duplicate":     False,
            "duplicate_of":     None,
        }
    }}


class DatasetProfileResponse(BaseModel):
    """
    Returned by GET /api/datasets/{dataset_id}/profile when profiling is done.
    HTTP 200 OK.
    Shape matches contracts/dataset_profile.json exactly.
    """
    dataset_id:          str
    profile_id:          str
    modality:            str                   # "TABULAR" | "IMAGE" | "MULTIMODAL"
    dimensions:          dict                  # {"rows": 569, "columns": 32}
    features:            dict                  # {"numerical": 30, "categorical": 1}
    target:              dict                  # {"candidate": "diagnosis", "confidence": "HIGH"}
    task:                dict                  # {"candidate": "BINARY_CLASSIFICATION", ...}
    class_distribution:  dict
    missing_values:      dict
    duplicates:          dict
    warnings:            List[str]
    status:              str                   # "PROFILED"
    profiled_at:         str                   # ISO 8601

    model_config = {"json_schema_extra": {
        "example": {
            "dataset_id":   "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
            "profile_id":   "PROFILE-000001",
            "modality":     "TABULAR",
            "dimensions":   {"rows": 569, "columns": 32},
            "features":     {"numerical": 30, "categorical": 1},
            "target":       {"candidate": "diagnosis", "confidence": "HIGH"},
            "task":         {"candidate": "BINARY_CLASSIFICATION", "confidence": "HIGH"},
            "class_distribution": {"0": 357, "1": 212},
            "missing_values": {"total": 0, "percentage": 0.0, "by_column": {}},
            "duplicates":   {"candidate_count": 0},
            "warnings":     ["Class imbalance detected: 62.7% vs 37.3%"],
            "status":       "PROFILED",
            "profiled_at":  "2026-09-10T14:25:12.456Z",
        }
    }}


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 1 — Upload Dataset
# POST /api/datasets/upload
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=201,
    summary="Upload a biomedical dataset",
    description=(
        "Accepts a CSV, XLSX, or ZIP file. Validates format, checks security, "
        "computes SHA-256, stores the immutable original, registers metadata, "
        "and triggers profiling in the background. Returns 201 immediately."
    ),
)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="The dataset file (CSV, XLSX, or ZIP)"),
    registry: DatasetRegistry = Depends(get_registry),
) -> DatasetUploadResponse:
    """
    Upload a biomedical dataset.

    Error codes:
    - 400  Unsupported format, corrupt file, or unsafe ZIP
    - 413  File exceeds the configured size limit
    - 500  Storage or registration failure
    """
    # Guard: file field present
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    # Read file bytes ONCE — file pointer is consumed after this call
    # (guide_shweta.md §9: "UploadFile gotcha")
    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(
        f"Upload request | file={file.filename!r} | "
        f"size={len(file_bytes)} bytes | content_type={file.content_type!r}"
    )

    # Run full ingestion pipeline
    try:
        service = DatasetIngestionService()
        result  = service.ingest(
            filename=file.filename,
            content_type=file.content_type or "",
            file_bytes=file_bytes,
        )
    except FileSizeLimitError as exc:
        logger.warning(f"Upload rejected (size limit) | file={file.filename!r} | {exc}")
        raise HTTPException(status_code=413, detail=str(exc))
    except (UnsupportedFormatError, InvalidFileError) as exc:
        logger.warning(f"Upload rejected (format) | file={file.filename!r} | {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except (InvalidArchiveError, UnsafeArchiveError) as exc:
        logger.warning(f"Upload rejected (archive) | file={file.filename!r} | {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except StorageError as exc:
        logger.error(f"Storage failure | file={file.filename!r} | {exc}")
        raise HTTPException(status_code=500, detail=f"Storage error: {exc}")
    except RegistrationError as exc:
        logger.error(f"Registration failure | file={file.filename!r} | {exc}")
        raise HTTPException(status_code=500, detail=f"Registration error: {exc}")
    except Exception as exc:
        # Catch-all: never expose tracebacks to the client
        logger.exception(f"Unexpected ingestion error | file={file.filename!r}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")

    # Kick off profiling in background — upload returns 201 immediately
    # Background task creates its OWN registry/session (guide_shweta.md §9)
    dataset_id   = result["dataset_id"]
    storage_path = result["storage_path"]
    container    = result["container_type"]

    background_tasks.add_task(
        _run_profiling_background,
        dataset_id=dataset_id,
        storage_path=storage_path,
        container_type=container,
    )

    logger.info(
        f"Upload complete | dataset_id={dataset_id} | "
        f"display_id={result['display_id']} | is_duplicate={result['is_duplicate']}"
    )
    return DatasetUploadResponse(**result)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 2 — List Datasets
# GET /api/datasets
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=DatasetListResponse,
    status_code=200,
    summary="List all registered datasets",
    description="Returns all datasets, newest first. Supports pagination via limit/offset.",
)
def list_datasets(
    limit:  int = 50,
    offset: int = 0,
    registry: DatasetRegistry = Depends(get_registry),
) -> DatasetListResponse:
    """
    List all registered datasets, newest first.
    """
    try:
        records, total = registry.list_all(offset=offset, limit=limit)
    except Exception as exc:
        logger.exception("Error reading dataset list")
        raise HTTPException(status_code=500, detail="Could not retrieve dataset list.")

    summaries = []
    for r in records:
        summaries.append(DatasetSummary(
            dataset_id=r["dataset_id"],
            display_id=r["display_id"],
            filename=r["original_filename"],
            container_type=r["container_type"],
            file_size_bytes=r["file_size_bytes"],
            status=r["status"],
            upload_timestamp=r["upload_timestamp"],
            has_profile=registry.profile_exists(r["dataset_id"]),
        ))

    return DatasetListResponse(datasets=summaries, total=total)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 3 — Get Single Dataset
# GET /api/datasets/{dataset_id}
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    status_code=200,
    summary="Get dataset metadata",
    description="Returns full registration metadata for a single dataset by its UUID.",
)
def get_dataset(
    dataset_id: str,
    registry: DatasetRegistry = Depends(get_registry),
) -> DatasetDetailResponse:
    """
    Get registration metadata for a single dataset.
    Returns 404 if dataset_id is not found.
    """
    try:
        r = registry.get_by_id(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found.",
        )
    except Exception as exc:
        logger.exception(f"Error retrieving dataset | dataset_id={dataset_id}")
        raise HTTPException(status_code=500, detail="Could not retrieve dataset.")

    return DatasetDetailResponse(
        dataset_id=r["dataset_id"],
        display_id=r["display_id"],
        filename=r["original_filename"],
        container_type=r["container_type"],
        file_size_bytes=r["file_size_bytes"],
        sha256=r["sha256"],
        status=r["status"],
        upload_timestamp=r["upload_timestamp"],
        storage_path=r["raw_storage_path"],
        is_duplicate=r.get("is_duplicate", False),
        duplicate_of=r.get("duplicate_of"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 4 — Get Dataset Profile
# GET /api/datasets/{dataset_id}/profile
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{dataset_id}/profile",
    summary="Get dataset profiling results",
    description=(
        "Returns profiling results (modality, features, target, task, statistics). "
        "Returns 202 if profiling is still running. Returns 404 if dataset not found."
    ),
)
def get_dataset_profile(
    dataset_id: str,
    registry: DatasetRegistry = Depends(get_registry),
):
    """
    Get profiling results for a dataset.

    Response codes:
    - 200  Profile ready — returns DatasetProfileResponse
    - 202  Profiling still in progress — returns {"status": "profiling_in_progress"}
    - 404  Dataset not found
    """
    # First confirm the dataset itself exists
    try:
        registry.get_by_id(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    # Try to load the profile
    profile_data = registry.load_profile(dataset_id)

    if profile_data is None:
        # Profiling hasn't finished yet — return 202 Accepted
        # Frontend should poll until it gets 200
        return JSONResponse(
            status_code=202,
            content={
                "status":     "profiling_in_progress",
                "dataset_id": dataset_id,
                "message":    "Profiling is running in the background. Poll this endpoint again shortly.",
            },
        )

    return DatasetProfileResponse(**profile_data)


# ══════════════════════════════════════════════════════════════════════════════
# MOCK ENDPOINT — for Naeem (frontend developer)
# GET /api/datasets/demo/breast-cancer
#
# Returns hardcoded data so Naeem can build UI immediately without
# waiting for a real upload. Remove or gate behind a feature flag in production.
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/demo/breast-cancer",
    response_model=DatasetDetailResponse,
    status_code=200,
    summary="[MOCK] Breast cancer dataset metadata",
    description=(
        "Development-only mock endpoint. Returns hardcoded breast cancer "
        "metadata so the frontend can build without running a real upload. "
        "Remove before production deployment."
    ),
    tags=["mock"],
)
def get_demo_breast_cancer() -> DatasetDetailResponse:
    """Hardcoded mock — Breast Cancer Wisconsin dataset."""
    return DatasetDetailResponse(
        dataset_id="a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
        display_id="DS-000001",
        filename="breast_cancer.csv",
        container_type="CSV",
        file_size_bytes=125847,
        sha256="a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        status="REGISTERED",
        upload_timestamp="2026-09-10T14:23:45.123Z",
        storage_path="a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7/raw/original.csv",
        is_duplicate=False,
        duplicate_of=None,
    )


@router.get(
    "/demo/breast-cancer/profile",
    response_model=DatasetProfileResponse,
    status_code=200,
    summary="[MOCK] Breast cancer dataset profile",
    description="Development-only mock. Returns hardcoded profiling results.",
    tags=["mock"],
)
def get_demo_breast_cancer_profile() -> DatasetProfileResponse:
    """Hardcoded mock — Breast Cancer Wisconsin profiling result."""
    return DatasetProfileResponse(
        dataset_id="a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
        profile_id="PROFILE-000001",
        modality="TABULAR",
        dimensions={"rows": 569, "columns": 32},
        features={"numerical": 30, "categorical": 1},
        target={"candidate": "diagnosis", "confidence": "HIGH"},
        task={"candidate": "BINARY_CLASSIFICATION", "confidence": "HIGH"},
        class_distribution={"0": 357, "1": 212},
        missing_values={"total": 0, "percentage": 0.0, "by_column": {}},
        duplicates={"candidate_count": 0},
        warnings=["Class imbalance detected: 62.7% vs 37.3%"],
        status="PROFILED",
        profiled_at="2026-09-10T14:25:12.456Z",
    )


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND TASK — Profile after upload
# Runs AFTER the 201 response is already sent to the client.
# ══════════════════════════════════════════════════════════════════════════════

def _run_profiling_background(
    dataset_id:     str,
    storage_path:   str,
    container_type: str,
) -> None:
    """
    Background task: run Jayed's DatasetProfiler and save results.

    IMPORTANT NOTES (guide_shweta.md §9):
    1. This function runs AFTER the HTTP response is sent — never raise here.
    2. Create a FRESH DatasetRegistry — the request-scoped one is already closed.
    3. Only CSV/XLSX can be profiled by pandas; ZIP profiling is deferred.
    4. Never log file content — only metadata (dataset_id, row/col counts).
    """
    # Create an independent registry (no shared state with request)
    registry = DatasetRegistry()

    logger.info(f"Background profiling started | dataset_id={dataset_id}")

    try:
        # Only tabular files can be profiled with pandas right now
        if container_type.upper() == "ZIP":
            logger.info(
                f"Skipping auto-profile for ZIP | dataset_id={dataset_id} | "
                "ZIP profiling belongs to Phase 2"
            )
            return

        # Build the absolute path to the stored raw file
        abs_path = Path(config.storage_base_path) / storage_path

        if not abs_path.exists():
            logger.error(f"Profiling failed — raw file not found | path={abs_path}")
            return

        # Try to use Jayed's real profiler if it exists
        # Falls back to a minimal built-in profiler if Jayed's isn't integrated yet
        profile_data = _build_profile(dataset_id, abs_path, container_type)

        # Save the profile alongside the raw file
        registry.save_profile(dataset_id, profile_data)
        logger.info(
            f"Background profiling complete | dataset_id={dataset_id} | "
            f"rows={profile_data['dimensions']['rows']} | "
            f"cols={profile_data['dimensions']['columns']}"
        )

    except Exception as exc:
        # Background failures must NEVER crash — just log
        # The upload already returned 201 successfully
        logger.error(f"Background profiling failed | dataset_id={dataset_id} | error={exc}")


def _build_profile(dataset_id: str, abs_path: Path, container_type: str) -> dict:
    """
    Build a profile dict from the raw file.

    Priority:
    1. Try Jayed's DatasetProfiler (when his code is integrated)
    2. Fall back to a minimal built-in pandas profile

    Returns a dict matching contracts/dataset_profile.json.
    """
    # ── Attempt to use Jayed's profiler ──────────────────────────────────────
    try:
        # This import will succeed once Jayed's module is integrated
        from data.profiler import DatasetProfiler  # type: ignore
        import pandas as pd

        if container_type.upper() == "CSV":
            df = pd.read_csv(abs_path)
        elif container_type.upper() == "XLSX":
            df = pd.read_excel(abs_path)
        else:
            raise ValueError(f"Cannot profile container type: {container_type}")

        profiler = DatasetProfiler()
        profile  = profiler.profile(df, dataset_id)

        # Jayed's profiler returns an object with .to_dict() or is already a dict
        if hasattr(profile, "to_dict"):
            return profile.to_dict()
        return dict(profile)

    except ImportError:
        # Jayed's profiler not yet integrated — use built-in minimal profiler
        logger.info(
            f"Jayed's profiler not found — using minimal built-in profile | "
            f"dataset_id={dataset_id}"
        )
        return _minimal_profile(dataset_id, abs_path, container_type)


def _minimal_profile(dataset_id: str, abs_path: Path, container_type: str) -> dict:
    """
    Minimal built-in profiler using pandas.
    Produces a profile that satisfies the dataset_profile.json contract shape
    so the GET /profile endpoint returns 200 immediately after upload.

    This is intentionally basic — Phase 2 (Jayed) does the deep profiling.
    We're only ensuring the contract shape is filled so the frontend can proceed.
    """
    import pandas as pd

    if container_type.upper() == "CSV":
        df = pd.read_csv(abs_path)
    elif container_type.upper() == "XLSX":
        df = pd.read_excel(abs_path)
    else:
        raise ValueError(f"Cannot profile: {container_type}")

    rows, cols       = df.shape
    numerical_cols   = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    # Missing values summary
    total_missing = int(df.isnull().sum().sum())
    total_cells   = rows * cols
    missing_pct   = round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0.0
    missing_by_col = {
        col: int(df[col].isnull().sum())
        for col in df.columns
        if df[col].isnull().sum() > 0
    }

    # Duplicate rows
    duplicate_count = int(df.duplicated().sum())

    # Warnings
    warnings = []
    if total_missing > 0:
        warnings.append(f"Dataset contains {total_missing} missing values ({missing_pct}%).")
    if duplicate_count > 0:
        warnings.append(f"Dataset contains {duplicate_count} duplicate rows.")

    # Simple target candidate heuristic — last column or column named 'target'/'label'
    candidate_target = None
    for name in ["target", "label", "diagnosis", "outcome", "status", "class"]:
        if name in [c.lower() for c in df.columns]:
            idx = [c.lower() for c in df.columns].index(name)
            candidate_target = df.columns[idx]
            break
    if candidate_target is None and len(df.columns) > 0:
        candidate_target = df.columns[-1]

    # Class distribution (only if target looks binary/categorical)
    class_dist: dict = {}
    task_candidate = "UNKNOWN"
    task_confidence = "LOW"
    target_confidence = "LOW"

    if candidate_target and candidate_target in df.columns:
        unique_vals = df[candidate_target].nunique()
        target_confidence = "HIGH" if unique_vals <= 10 else "LOW"
        if unique_vals == 2:
            task_candidate  = "BINARY_CLASSIFICATION"
            task_confidence = "HIGH"
            class_dist = {
                str(k): int(v)
                for k, v in df[candidate_target].value_counts().items()
            }
        elif 2 < unique_vals <= 10:
            task_candidate  = "MULTICLASS_CLASSIFICATION"
            task_confidence = "MEDIUM"
        elif unique_vals > 10 and df[candidate_target].dtype in ["float64", "int64"]:
            task_candidate  = "REGRESSION"
            task_confidence = "LOW"

    profile_id = f"PROFILE-{dataset_id[:8].upper()}"

    return {
        "dataset_id":   dataset_id,
        "profile_id":   profile_id,
        "modality":     "TABULAR",
        "dimensions":   {"rows": rows, "columns": cols},
        "features":     {
            "numerical":   len(numerical_cols),
            "categorical": len(categorical_cols),
        },
        "target": {
            "candidate":  candidate_target,
            "confidence": target_confidence,
        },
        "task": {
            "candidate":  task_candidate,
            "confidence": task_confidence,
        },
        "class_distribution": class_dist,
        "missing_values": {
            "total":      total_missing,
            "percentage": missing_pct,
            "by_column":  missing_by_col,
        },
        "duplicates": {
            "candidate_count": duplicate_count,
        },
        "warnings":   warnings,
        "status":     "PROFILED",
        "profiled_at": datetime.now(timezone.utc).isoformat(),
    }
