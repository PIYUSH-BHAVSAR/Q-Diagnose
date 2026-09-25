"""Main FastAPI application entry point.

QuantWarriors Hybrid Quantum Machine Learning Disease Detection Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.core.config import config
from backend.core.logging import logger
from backend.api import datasets, experiments, results, reports


# Create FastAPI app
app = FastAPI(
    title="QuantWarriors QML Platform",
    description="Hybrid Quantum Machine Learning Disease Detection Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(datasets.router)
app.include_router(experiments.router)
app.include_router(results.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "QuantWarriors QML Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/config")
async def get_config():
    """Get platform configuration."""
    return {
        "quantum": config.quantum_config,
        "experiment": config.experiment,
        "classical_models": config.classical_models
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("=" * 60)
    logger.info("QuantWarriors QML Platform Starting")
    logger.info("=" * 60)
    logger.info(f"Quantum config: {config.quantum_config}")
    logger.info(f"Classical models: {config.classical_models}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("QuantWarriors QML Platform Shutting Down")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
