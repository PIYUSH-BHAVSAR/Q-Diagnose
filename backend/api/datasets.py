"""
backend/api/datasets.py
Owner: Shweta
Phase: 1 (phase1.md §28-30)

ENDPOINTS:
  POST   /api/datasets/upload                  → upload a CSV/XLSX/ZIP dataset
  GET    /api/datasets                         → list all registered datasets
  GET    /api/datasets/{dataset_id}            → get single dataset metadata
  GET    /api/datasets/{dataset_id}/profile    → get profiling results
  GET    /api/datasets/demo/breast-cancer      → hardcoded mock (Naeem dev helper)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.config import config
from backend.core.exceptions import (
    DatasetNotFoundError,
    FileSizeLimitError,
    InvalidArchiveError,
    InvalidFileError,
    RegistrationError,
    StorageError,
    UnsafeArchiveError,
    UnsupportedFormatError,
)
from backend.core.logging import get_logger
from backend.data.loader import DatasetIngestionService, DatasetLoader
from backend.storage.database import get_db
from backend.storage.repositories import DatasetRepository

logger = get_logger("api.datasets")
_dataset_repo = DatasetRepository()
_loader = DatasetLoader()

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════════

class DatasetUploadResponse(BaseModel):
    dataset_id:          str
    display_id:          str
    status:              str
    filename:            str
    container_type:      str
    upload_timestamp:    str
    file_size_bytes:     int
    sha256:              str
    storage_path:        str
    is_duplicate:        bool
    duplicate_of:        Optional[str]
    validation_warnings: List[str]
    rejection_reason:    Optional[str]


class DatasetSummary(BaseModel):
    dataset_id:       str
    display_id:       str
    filename:         str
    container_type:   str
    file_size_bytes:  int
    status:           str
    upload_timestamp: str
    has_profile:      bool


class DatasetListResponse(BaseModel):
    datasets: List[DatasetSummary]
    total:    int


class DatasetDetailResponse(BaseModel):
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


class DatasetProfileResponse(BaseModel):
    dataset_id:          str
    profile_id:          str
    modality:            str
    dimensions:          dict
    features:            dict
    target:              dict
    task:                dict
    class_distribution:  dict
    missing_values:      dict
    duplicates:          dict
    warnings:            List[str]
    status:              str
    profiled_at:         str


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 1 — Upload Dataset (POST /api/datasets/upload)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=201,
    summary="Upload a biomedical dataset",
)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="The dataset file (CSV, XLSX, or ZIP)"),
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(
        f"Upload request | file={file.filename!r} | "
        f"size={len(file_bytes)} bytes | content_type={file.content_type!r}"
    )

    try:
        service = DatasetIngestionService(db=db)
        result  = service.ingest(
            filename=file.filename,
            content_type=file.content_type or "",
            file_bytes=file_bytes,
        )
    except FileSizeLimitError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except (UnsupportedFormatError, InvalidFileError, InvalidArchiveError, UnsafeArchiveError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (StorageError, RegistrationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Unexpected ingestion error | file={file.filename!r}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")

    dataset_id   = result["dataset_id"]
    storage_path = result["storage_path"]
    container    = result["container_type"]

    background_tasks.add_task(
        _run_profiling_background,
        dataset_id=dataset_id,
        storage_path=storage_path,
        container_type=container,
    )

    return DatasetUploadResponse(**result)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 2 — List Datasets (GET /api/datasets)
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=DatasetListResponse,
    status_code=200,
    summary="List all registered datasets",
)
def list_datasets(
    db: Session = Depends(get_db),
) -> DatasetListResponse:
    datasets = _dataset_repo.list_all(db)
    summaries = []
    for ds in datasets:
        d = ds.to_response_dict()
        summaries.append(DatasetSummary(
            dataset_id=d["dataset_id"],
            display_id=d["display_id"],
            filename=d["filename"],
            container_type=d["container_type"],
            file_size_bytes=d["file_size_bytes"],
            status=d["status"],
            upload_timestamp=d["upload_timestamp"],
            has_profile=True,
        ))
    return DatasetListResponse(datasets=summaries, total=len(datasets))


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 3 — Get Single Dataset (GET /api/datasets/{dataset_id})
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    status_code=200,
    summary="Get dataset metadata",
)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
) -> DatasetDetailResponse:
    ds = _dataset_repo.get_by_id(db, dataset_id)
    if ds is None:
        ds = _dataset_repo.get_by_display_id(db, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    d = ds.to_response_dict()
    return DatasetDetailResponse(
        dataset_id=d["dataset_id"],
        display_id=d["display_id"],
        filename=d["filename"],
        container_type=d["container_type"],
        file_size_bytes=d["file_size_bytes"],
        sha256=d["sha256"],
        status=d["status"],
        upload_timestamp=d["upload_timestamp"],
        storage_path=d["storage_path"],
        is_duplicate=d.get("is_duplicate", False),
        duplicate_of=d.get("duplicate_of"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 4 — Get Dataset Profile (GET /api/datasets/{dataset_id}/profile)
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{dataset_id}/profile",
    summary="Get dataset profiling results",
)
def get_dataset_profile(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    ds = _dataset_repo.get_by_id(db, dataset_id)
    if ds is None:
        ds = _dataset_repo.get_by_display_id(db, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    profile_path = Path(config.storage_base_path) / "datasets" / ds.id / "profile.json"
    if not profile_path.exists():
        return JSONResponse(
            status_code=202,
            content={
                "status":     "profiling_in_progress",
                "dataset_id": dataset_id,
                "message":    "Profiling is running in the background. Poll this endpoint again shortly.",
            },
        )

    with open(profile_path, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    return DatasetProfileResponse(**profile_data)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 5 — Validate Dataset for ML Pipeline (POST /api/datasets/{dataset_id}/validate)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{dataset_id}/validate",
    status_code=200,
    summary="Validate a dataset for ML pipeline compatibility",
)
def validate_dataset(
    dataset_id: str,
    target_column: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Check whether a registered dataset is ready for the ML pipeline.
    Reads the stored profile (if available) and applies heuristic checks.
    Returns { ready_for_ml, issues, warnings, recommended_target, task_type }.
    """
    ds = _dataset_repo.get_by_id(db, dataset_id)
    if ds is None:
        ds = _dataset_repo.get_by_display_id(db, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    issues: List[str] = []
    warnings: List[str] = []
    recommended_target: Optional[str] = None
    task_type: Optional[str] = None

    # Try to load profile from disk
    profile_path = Path(config.storage_base_path) / "datasets" / ds.id / "profile.json"
    if profile_path.exists():
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        dims = profile_data.get("dimensions", {})
        rows = dims.get("rows", 0)
        cols = dims.get("columns", 0)
        missing = profile_data.get("missing_values", {})
        task = profile_data.get("task", {})
        target = profile_data.get("target", {})

        if rows < 50:
            issues.append(f"Dataset has only {rows} rows — minimum 50 required for reliable ML.")
        if cols < 2:
            issues.append("Dataset must have at least 2 columns (features + target).")
        if missing.get("percentage", 0) > 50:
            issues.append(f"Too many missing values: {missing.get('percentage', 0):.1f}% — clean before use.")
        elif missing.get("percentage", 0) > 20:
            warnings.append(f"High missing values: {missing.get('percentage', 0):.1f}%. Consider imputation.")

        task_candidate = task.get("candidate", "UNKNOWN")
        if task_candidate not in ("BINARY_CLASSIFICATION", "MULTICLASS_CLASSIFICATION", "REGRESSION"):
            warnings.append(f"Task type '{task_candidate}' detected — pipeline optimised for BINARY_CLASSIFICATION.")
        if task_candidate == "UNKNOWN":
            issues.append("Could not detect ML task type from dataset. Ensure a clear target column exists.")

        task_type = task_candidate
        recommended_target = target_column or target.get("candidate")

        for w in profile_data.get("warnings", []):
            if w not in warnings:
                warnings.append(w)

    else:
        # Profile not yet ready — basic check on file metadata only
        if ds.file_size_bytes < 100:
            issues.append("File appears empty or too small for ML.")
        warnings.append("Dataset profiling is still in progress. Validation is incomplete.")
        task_type = "UNKNOWN"

    ready_for_ml = len(issues) == 0

    return {
        "dataset_id":          ds.id,
        "display_id":          ds.display_id,
        "ready_for_ml":        ready_for_ml,
        "issues":              issues,
        "warnings":            warnings,
        "recommended_target":  recommended_target,
        "task_type":           task_type,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MOCK ENDPOINT — for Naeem (frontend developer)
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/demo/breast-cancer",
    response_model=DatasetDetailResponse,
    status_code=200,
    tags=["mock"],
)
def get_demo_breast_cancer() -> DatasetDetailResponse:
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
    tags=["mock"],
)
def get_demo_breast_cancer_profile() -> DatasetProfileResponse:
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
# ══════════════════════════════════════════════════════════════════════════════

def _run_profiling_background(
    dataset_id:     str,
    storage_path:   str,
    container_type: str,
) -> None:
    logger.info(f"Background profiling started | dataset_id={dataset_id}")

    try:
        if container_type.upper() == "ZIP":
            return

        abs_path = Path(config.storage_base_path) / storage_path
        if not abs_path.exists():
            return

        profile_data = _minimal_profile(dataset_id, abs_path, container_type)

        out_dir = Path(config.storage_base_path) / "datasets" / dataset_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "profile.json"

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        logger.info(f"Background profiling complete | dataset_id={dataset_id}")

    except Exception as exc:
        logger.error(f"Background profiling failed | dataset_id={dataset_id} | error={exc}")


def _minimal_profile(dataset_id: str, abs_path: Path, container_type: str) -> dict:
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

    total_missing = int(df.isnull().sum().sum())
    total_cells   = rows * cols
    missing_pct   = round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0.0
    missing_by_col = {
        col: int(df[col].isnull().sum())
        for col in df.columns
        if df[col].isnull().sum() > 0
    }

    duplicate_count = int(df.duplicated().sum())

    warnings = []
    if total_missing > 0:
        warnings.append(f"Dataset contains {total_missing} missing values ({missing_pct}%).")
    if duplicate_count > 0:
        warnings.append(f"Dataset contains {duplicate_count} duplicate rows.")

    candidate_target = None
    for name in ["target", "label", "diagnosis", "outcome", "status", "class"]:
        if name in [c.lower() for c in df.columns]:
            idx = [c.lower() for c in df.columns].index(name)
            candidate_target = df.columns[idx]
            break
    if candidate_target is None and len(df.columns) > 0:
        candidate_target = df.columns[-1]

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
