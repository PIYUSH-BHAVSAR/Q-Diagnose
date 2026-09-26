# main.py
# FastAPI application entry point for Q-Diagnose Dataset API.
#
# Run locally:
#   pip install fastapi uvicorn[standard] python-multipart pandas openpyxl
#   uvicorn main:app --reload --port 8000
#
# Then open: http://localhost:8000/docs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import datasets
from core.config import config
from core.logging_config import setup_logging

# ── Logging ───────────────────────────────────────────────────────────────────
logger = setup_logging(level="DEBUG" if config.debug else "INFO")
logger.info(f"Starting {config.app_name} v{config.version} [{config.environment}]")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=config.app_name,
    version=config.version,
    description=(
        "Phase 1 Dataset API — upload, register, and profile biomedical datasets "
        "for the Hybrid Quantum-Classical Disease Detection Platform.\n\n"
        "**Owner:** Shweta  |  **Phase:** 1 (Dataset Ingestion & Registration)"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow Naeem's frontend dev servers to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# When Piyush adds experiments.py:
#   from api import experiments
#   app.include_router(experiments.router)
app.include_router(datasets.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health_check():
    """Quick liveness probe — returns 200 when the server is up."""
    return {
        "status":      "ok",
        "app":         config.app_name,
        "version":     config.version,
        "environment": config.environment,
    }


@app.get("/", tags=["system"])
def root():
    """Redirect hint — open /docs for the interactive API explorer."""
    return {
        "message": f"{config.app_name} is running.",
        "docs":    "/docs",
        "health":  "/health",
    }
