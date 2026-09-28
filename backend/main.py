"""
backend/main.py
Owner: Arzaan
Purpose: FastAPI application entry point.

Wires up:
  - Startup event → init_db() + directory creation
  - Routers: backend/api/datasets.py, backend/api/experiments.py
  - GET /api/health   → {"status": "healthy"}
  - GET /api/config   → quantum_config, experiment, classical_models sections
  - GET /api/datasets/{id}/info → DatasetLoader.get_dataset_info() for Jayed

Run:
    python -m uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import dataclasses
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.core.config import config
from backend.core.exceptions import DatasetNotFoundError, StorageError
from backend.core.logging import get_logger, setup_logging
from backend.data.loader import DatasetLoader
from backend.storage.database import get_db, init_db
from backend.storage.repositories import DatasetRepository

logger = get_logger(__name__)
_dataset_repo = DatasetRepository()
_loader = DatasetLoader()


# ---------------------------------------------------------------------------
# Lifespan (startup + shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup:
      1. Configure structured logging
      2. Ensure all required directories exist
      3. Initialise SQLite database (create tables)
    """
    # 1. Logging
    setup_logging(level=config.logging.level, fmt=config.logging.format)
    logger.info(
        "Q-Diagnose starting | version=%s debug=%s",
        config.app.version, config.app.debug,
    )

    # 2. Ensure required directories exist
    dirs = [
        config.storage_base_path / "data" / "uploads",
        config.storage_base_path / "data" / "demo",
        config.storage_base_path / "datasets",
        config.storage_base_path / "artifacts" / "experiments",
        config.storage_base_path / "artifacts" / "models",
        config.storage_base_path / "artifacts" / "reports",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directory structure verified | base=%s", config.storage_base_path)

    # 3. Database
    init_db()
    logger.info("Application ready | port=8000")

    yield

    logger.info("Q-Diagnose shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Q-Diagnose API",
    description="Hybrid Quantum-Classical Disease Detection Platform — Foundation Layer",
    version=config.app.version,
    lifespan=lifespan,
)

# CORS — open during development; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (Shweta, Piyush, Radha)
from backend.api.datasets import router as datasets_router
from backend.api.experiments import router as experiments_router

app.include_router(datasets_router)
app.include_router(experiments_router)

# Serve UI static files (built by `npm run build` in mvp/frontend)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = Path(__file__).parent / "static"
if static_dir.exists() and any(static_dir.iterdir()):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", tags=["system"])
    def read_root():
        return FileResponse(str(static_dir / "index.html"))
else:
    @app.get("/", tags=["system"])
    def read_root():
        return {"status": "healthy", "message": "Q-Diagnose API is running. Frontend runs separately on port 5173."}


# ---------------------------------------------------------------------------
# Helper: JSON serialiser that handles dataclasses and datetimes
# ---------------------------------------------------------------------------

def _jsonable(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable")


# ---------------------------------------------------------------------------
# Health + Config
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["system"])
def health_check():
    """
    Liveness probe.
    Returns: {"status": "healthy"}
    """
    return {"status": "healthy"}


@app.get("/api/config", tags=["system"])
def get_config():
    """
    Return the platform configuration sections needed by Naeem's frontend
    and other teammates.  Excludes storage internals and database URL.
    """
    return {
        "quantum_config": dataclasses.asdict(config.quantum_config),
        "experiment": dataclasses.asdict(config.experiment),
        "classical_models": config.classical_models,
        "app": dataclasses.asdict(config.app),
    }


# Dataset routes are handled by backend/api/datasets.py router (included above).
# The /api/datasets/{dataset_id}/info endpoint below is a Jayed-specific helper
# not covered by that router, so it stays here.

# ---------------------------------------------------------------------------
# Dataset Info for Jayed  (GET /api/datasets/{dataset_id}/info)
# ---------------------------------------------------------------------------

@app.get("/api/datasets/{dataset_id}/info", tags=["datasets"])
def get_dataset_info(dataset_id: str, db: Session = Depends(get_db)):
    """
    Return DatasetLoader.get_dataset_info() dict for Jayed's profiler.
    Shape: {id, name, path, hash, rows, columns, target}
    """
    ds = _dataset_repo.get_by_id(db, dataset_id)
    if ds is None:
        ds = _dataset_repo.get_by_display_id(db, dataset_id)
    if ds is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found.",
        )
    try:
        info = _loader.get_dataset_info(ds.display_id)
        info["id"] = ds.id
        return info
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(StorageError)
async def storage_error_handler(request, exc: StorageError):
    logger.error("StorageError | %s", exc.message)
    return JSONResponse(
        status_code=500,
        content={"error": "STORAGE_ERROR", "detail": exc.message},
    )


@app.exception_handler(DatasetNotFoundError)
async def dataset_not_found_handler(request, exc: DatasetNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "DATASET_NOT_FOUND", "detail": exc.message},
    )
