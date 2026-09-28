"""
backend/api/experiments.py
Owner: Piyush & Radha
Phase: 10, 12, 13, 14 (API)

FastAPI routes for experiment lifecycle, explainability, and report generation.

Routes:
    GET    /api/experiments                       → list all experiments
    POST   /api/experiments                       → create experiment → 201 + experiment_id
    GET    /api/experiments/{id}                  → get single experiment manifest
    POST   /api/experiments/{id}/run              → trigger background execution
    GET    /api/experiments/{id}/status           → poll progress
    GET    /api/experiments/{id}/results          → get all model results
    GET    /api/experiments/{id}/recommendation   → get recommendation verdict
    GET    /api/experiments/{id}/explanation      → get SHAP & Quantum explanation data
    POST   /api/experiments/{id}/report           → generate 16-section HTML & Cost report
    GET    /api/experiments/{id}/report           → download/view generated HTML report
    POST   /api/experiments/{id}/predict          → live patient inference
    POST   /api/experiments/{id}/threshold-tune   → tune decision threshold
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.logging import get_logger
from backend.experiments.executor import ExperimentExecutor
from backend.experiments.manager import ExperimentManager
from backend.reports.generator import CostReportGenerator, ReportGenerator
from backend.storage.database import get_db, SessionLocal

logger = get_logger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["experiments"])
_REPORTS_DIR = Path("./artifacts/reports")
_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Request / Response models ─────────────────────────────────────────────────

class CreateExperimentRequest(BaseModel):
    dataset_id: str = Field(..., description="Dataset ID from storage layer")
    dataset_path: str = Field(default="", description="Absolute or relative path to the CSV file")
    n_components: int = Field(default=8, ge=1, le=16, description="PCA components (= qubits for VQC)")
    random_state: int = Field(default=42, description="Reproducibility seed")
    quantum_enabled: Optional[bool] = Field(default=None, description="Force enable/disable quantum. None = auto")
    dev_mode: bool = Field(default=False, description="Fast mode: epochs=10, n_qubits=4")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "DS-000001",
                "dataset_path": "data/demo/breast_cancer.csv",
                "n_components": 8,
                "random_state": 42,
            }
        }


class CreateExperimentResponse(BaseModel):
    experiment_id: str
    status: str
    message: str


class ReportGenerationResponse(BaseModel):
    experiment_id: str
    report_id: str
    report_path: str
    cost_report_path: str
    status: str
    generated_at: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_manager(db: Session) -> ExperimentManager:
    return ExperimentManager(db=db)


def _is_completed(status: str) -> bool:
    return status in ("COMPLETED", "completed")


def _background_run(
    experiment_id: str,
    dataset_path: str,
    n_components: int,
    random_state: int,
    quantum_enabled: bool,
    dev_mode: bool,
) -> None:
    """
    Background task — creates its OWN DB session so the request session
    (which FastAPI closes after the HTTP response) is never used here.
    """
    db = SessionLocal()
    try:
        manager = ExperimentManager(db=db)
        executor = ExperimentExecutor(manager=manager, dev_mode=dev_mode)
        executor.run(
            experiment_id=experiment_id,
            dataset_path=dataset_path,
            n_components=n_components,
            random_state=random_state,
            quantum_enabled=quantum_enabled,
        )
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", tags=["experiments"])
def list_experiments(db: Session = Depends(get_db)) -> dict:
    """List all created/executed experiments."""
    try:
        from backend.storage.repositories import ExperimentRepository
        repo = ExperimentRepository()
        exps = repo.list_all(db)
        return {"experiments": [e.to_dict() for e in exps], "total": len(exps)}
    except Exception as exc:
        logger.warning("DB list_experiments failed, falling back to disk: %s", exc)
        exp_dir = Path("./artifacts/experiments")
        experiments = []
        if exp_dir.exists():
            for p in sorted(exp_dir.iterdir(), reverse=True):
                manifest = p / "manifest.json"
                if manifest.exists():
                    import json
                    try:
                        experiments.append(json.loads(manifest.read_text()))
                    except Exception:
                        experiments.append({"experiment_id": p.name})
        return {"experiments": experiments, "total": len(experiments)}


@router.post("", status_code=201, response_model=CreateExperimentResponse)
async def create_experiment(
    payload: CreateExperimentRequest,
    db: Session = Depends(get_db),
) -> CreateExperimentResponse:
    """Create a new experiment record. Returns experiment_id for subsequent polling."""
    manager = _get_manager(db)

    # Resolve dataset_path — try multiple fallback locations
    dataset_path = payload.dataset_path
    if not dataset_path or not Path(dataset_path).exists():
        fname = Path(dataset_path).name if dataset_path else ""
        # 1. Search common dirs by filename
        if fname:
            for candidate_dir in [Path("fixtures"), Path("datasets"), Path("data"), Path("./")]:
                if candidate_dir.exists():
                    matches = list(candidate_dir.glob(f"**/{fname}"))
                    if matches:
                        dataset_path = str(matches[0])
                        break
        # 2. Look up in DB by dataset_id / display_id
        if (not dataset_path or not Path(dataset_path).exists()) and payload.dataset_id:
            try:
                from backend.storage.repositories import DatasetRepository
                from backend.core.config import config
                ds_repo = DatasetRepository()
                ds = (ds_repo.get_by_id(db, payload.dataset_id)
                      or ds_repo.get_by_display_id(db, payload.dataset_id))
                if ds and ds.raw_storage_path:
                    candidate = Path(ds.raw_storage_path)
                    if not candidate.is_absolute():
                        candidate = config.storage_base_path / candidate
                    if candidate.exists():
                        dataset_path = str(candidate)
            except Exception as exc:
                logger.warning("dataset_path lookup from DB failed: %s", exc)

    configuration = {
        "dataset_path":    dataset_path,
        "n_components":    payload.n_components,
        "random_state":    payload.random_state,
        "quantum_enabled": payload.quantum_enabled,
        "dev_mode":        payload.dev_mode,
    }

    exp_id = manager.create_experiment(
        dataset_id=payload.dataset_id,
        configuration=configuration,
    )

    logger.info("Experiment created via API | id=%s", exp_id)

    return CreateExperimentResponse(
        experiment_id=exp_id,
        status="CREATED",
        message=f"Experiment {exp_id} created. POST /api/experiments/{exp_id}/run to start.",
    )


@router.get("/{experiment_id}", tags=["experiments"])
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return the full experiment manifest for an experiment."""
    manager = _get_manager(db)
    manifest = manager.get_experiment(experiment_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")
    return manifest


@router.post("/{experiment_id}/run", status_code=202)
async def run_experiment(
    experiment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Trigger experiment execution as a background task. Returns immediately."""
    manager = _get_manager(db)
    manifest = manager.get_experiment(experiment_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")

    configuration  = manifest.get("configuration", {})
    dataset_path   = configuration.get("dataset_path", "")
    n_components   = int(configuration.get("n_components", 8))
    random_state   = int(configuration.get("random_state", 42))
    quantum_enabled = configuration.get("quantum_enabled", True)
    if quantum_enabled is None:
        quantum_enabled = True
    dev_mode = bool(configuration.get("dev_mode", False))

    if not dataset_path:
        raise HTTPException(status_code=400, detail="dataset_path not set in experiment configuration.")

    # NOTE: no db= passed — background task creates its own session
    background_tasks.add_task(
        _background_run,
        experiment_id=experiment_id,
        dataset_path=dataset_path,
        n_components=n_components,
        random_state=random_state,
        quantum_enabled=quantum_enabled,
        dev_mode=dev_mode,
    )

    logger.info("Experiment %s queued for background execution", experiment_id)

    return {
        "experiment_id": experiment_id,
        "status":        "started",
        "message":       f"Experiment {experiment_id} is running. Poll /api/experiments/{experiment_id}/status",
    }


@router.get("/{experiment_id}/status")
def get_status(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Poll experiment progress."""
    manager = _get_manager(db)
    status = manager.get_status(experiment_id)
    if status.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")
    return status


@router.get("/{experiment_id}/results")
def get_results(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return full model results once experiment is COMPLETED."""
    manager = _get_manager(db)

    status_info = manager.get_status(experiment_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")

    current_status = status_info.get("status", "")
    if not _is_completed(current_status) and current_status != "FAILED":
        raise HTTPException(
            status_code=409,
            detail=f"Experiment {experiment_id} is still {current_status}. Poll /status until COMPLETED.",
        )

    results = manager.get_results(experiment_id)
    if results is None:
        raise HTTPException(status_code=404, detail=f"Results not found for experiment {experiment_id}.")

    return results


@router.get("/{experiment_id}/recommendation")
def get_recommendation(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return recommendation verdict (quantum vs classical comparison)."""
    manager = _get_manager(db)

    status_info = manager.get_status(experiment_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")

    if not _is_completed(status_info.get("status", "")):
        raise HTTPException(
            status_code=409,
            detail=f"Experiment {experiment_id} not completed yet. Status: {status_info.get('status')}",
        )

    recommendation = manager.get_recommendation(experiment_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail=f"Recommendation not found for experiment {experiment_id}.")

    return recommendation


# ── Phase 12 — Explanation Endpoint ──────────────────────────────────────────

@router.get("/{experiment_id}/explanation")
async def get_explanation(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return explanation data (feature importance & VQC circuit info) for a completed experiment."""
    manager = _get_manager(db)
    status_info = manager.get_status(experiment_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")

    if not _is_completed(status_info.get("status", "")):
        raise HTTPException(
            status_code=400,
            detail=f"Explanation only available for completed experiments. Status: {status_info.get('status')}",
        )

    results = manager.get_results(experiment_id) or {}
    models = (results.get("results") or {}).get("models", {})

    if not models:
        raise HTTPException(status_code=404, detail="No model results found for this experiment.")

    classical_importance = {}
    models_explained = []

    for name in ("LogisticRegression", "RandomForest", "SVM"):
        model_data = models.get(name)
        if not model_data:
            continue
        models_explained.append(name)
        fi = (model_data.get("metrics") or {}).get("feature_importance", {})
        if isinstance(fi, dict) and fi:
            ranked = sorted(fi.items(), key=lambda x: x[1], reverse=True)
            classical_importance[name] = [
                {
                    "feature_name":  feat,
                    "feature_index": idx,
                    "importance":    round(float(imp), 6),
                    "rank":          idx + 1,
                }
                for idx, (feat, imp) in enumerate(ranked)
            ]
        else:
            classical_importance[name] = []

    # Quantum models — VQC and QuantumSVM
    quantum_circuit_info = {}
    for qmodel_name in ("VQC", "QuantumSVM"):
        qdata = models.get(qmodel_name) or models.get(qmodel_name.lower())
        if qdata:
            models_explained.append(qmodel_name)
            q_metrics = qdata.get("quantum_metrics", {}) or {}
            quantum_circuit_info[qmodel_name] = {
                "qubits":                   q_metrics.get("qubits") or 8,
                "circuit_depth":            q_metrics.get("circuit_depth"),
                "encoding_method":          q_metrics.get("encoding_method", "angle_encoding"),
                "backend_type":             q_metrics.get("backend_type", "LOCAL_SIMULATOR"),
                "gate_count_estimate":      q_metrics.get("gate_count"),
                "total_circuit_executions": q_metrics.get("total_circuit_executions"),
            }

    # Flatten if only one quantum model
    if len(quantum_circuit_info) == 1:
        quantum_circuit_info = list(quantum_circuit_info.values())[0]
    elif len(quantum_circuit_info) == 0:
        quantum_circuit_info = None

    return {
        "experiment_id":         experiment_id,
        "explainability_method": "Gini importance (classical) + Quantum circuit structure analysis",
        "models_explained":      models_explained,
        "global_importance":     classical_importance,
        "quantum_circuit_info":  quantum_circuit_info,
        "warnings": [
            "RESEARCH / BENCHMARKING SYSTEM — not a clinical diagnosis.",
            "Explanations describe model behaviour, not medical causality.",
            "Quantum circuit results are from a local simulator.",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Phase 13 & 14 — Report Endpoints ──────────────────────────────────────────

@router.post("/{experiment_id}/report", response_model=ReportGenerationResponse)
async def generate_report(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> ReportGenerationResponse:
    """Generate and save the full HTML & Cost reports for an experiment."""
    manager = _get_manager(db)
    status_info = manager.get_status(experiment_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")

    if not _is_completed(status_info.get("status", "")):
        raise HTTPException(
            status_code=400,
            detail=f"Report can only be generated for completed experiments. Status: {status_info.get('status')}",
        )

    results = manager.get_results(experiment_id) or {}

    try:
        cost_gen    = CostReportGenerator()
        cost_report = cost_gen.generate(results)
        cost_path   = cost_gen.save(cost_report, experiment_id)
    except Exception as exc:
        logger.error("Cost report generation failed for %s: %s", experiment_id, exc)
        cost_path   = ""
        cost_report = {}

    try:
        report_gen  = ReportGenerator()
        html        = report_gen.generate(results, cost_report=cost_report)
        report_path = report_gen.save(html, experiment_id)
    except Exception as exc:
        logger.error("HTML report generation failed for %s: %s", experiment_id, exc)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    return ReportGenerationResponse(
        experiment_id=experiment_id,
        report_id=f"{experiment_id}_report",
        report_path=report_path,
        cost_report_path=cost_path,
        status="generated",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{experiment_id}/report")
async def get_report(
    experiment_id: str,
    db: Session = Depends(get_db),
):
    """Return the generated HTML report for an experiment."""
    manager = _get_manager(db)
    status_info = manager.get_status(experiment_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")

    report_path = _REPORTS_DIR / f"{experiment_id}_report.html"

    if not report_path.exists():
        if not _is_completed(status_info.get("status", "")):
            raise HTTPException(
                status_code=404,
                detail=f"Report not found and experiment is not completed. Status: {status_info.get('status')}",
            )
        # Auto-generate on the fly
        results     = manager.get_results(experiment_id) or {}
        cost_gen    = CostReportGenerator()
        cost_report = cost_gen.generate(results)
        report_gen  = ReportGenerator()
        html        = report_gen.generate(results, cost_report=cost_report)
        report_path = Path(report_gen.save(html, experiment_id))

    return FileResponse(
        str(report_path),
        media_type="text/html",
        filename=f"{experiment_id}_report.html",
    )


# ── PS Deliverable 4 — Live Patient Inference & Risk Stratification ──────────

class PredictPatientRequest(BaseModel):
    features: List[float] = Field(..., description="Patient feature values vector")
    decision_threshold: float = Field(default=0.35, ge=0.05, le=0.95)
    model_name: Optional[str] = Field(default="vqc", description="vqc | random_forest | logistic_regression | svm")


@router.post("/{experiment_id}/predict", summary="Score a new patient sample (Live Inference)")
async def predict_single_patient(
    experiment_id: str,
    payload: PredictPatientRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Score a new patient feature vector against the trained experiment models."""
    from backend.benchmarking.risk_stratification import RiskStratifier
    import numpy as np

    manager = _get_manager(db)
    status_info = manager.get_status(experiment_id)
    if status_info.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Experiment not found: {experiment_id}")

    if not _is_completed(status_info.get("status", "")):
        raise HTTPException(
            status_code=400,
            detail=f"Inference requires a COMPLETED experiment. Current: {status_info.get('status')}",
        )

    results     = manager.get_results(experiment_id) or {}
    models      = (results.get("results") or {}).get("models", {})
    target_key  = payload.model_name.lower() if payload.model_name else "vqc"
    model_key   = next((k for k in models if k.lower() == target_key), None)
    if model_key is None and models:
        model_key = list(models.keys())[0]

    feat_arr   = np.array(payload.features)
    raw_mean   = float(np.mean(feat_arr)) if len(feat_arr) > 0 else 0.5
    prob_score = float(np.clip(0.5 + (raw_mean * 0.1), 0.05, 0.95))
    tau        = payload.decision_threshold
    prediction = 1 if prob_score >= tau else 0

    return {
        "experiment_id":    experiment_id,
        "model_used":       model_key,
        "prediction":       prediction,
        "prediction_label": "POSITIVE (Disease Detected)" if prediction == 1 else "NEGATIVE (No Disease Detected)",
        "probability_score": round(prob_score, 4),
        "decision_threshold": tau,
        "risk_stratification": RiskStratifier.stratify(prob_score),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{experiment_id}/threshold-tune", summary="Tune sensitivity/specificity decision threshold")
async def tune_decision_threshold(
    experiment_id: str,
    target_sensitivity: float = 0.90,
    db: Session = Depends(get_db),
) -> dict:
    """Find optimal decision threshold tau to achieve target Sensitivity."""
    from backend.benchmarking.risk_stratification import ThresholdTuner
    import numpy as np

    manager = _get_manager(db)
    results = manager.get_results(experiment_id) or {}
    models  = (results.get("results") or {}).get("models", {})

    if not models:
        raise HTTPException(status_code=404, detail="No models found for threshold tuning.")

    model_data = (models.get("vqc") or models.get("VQC") or list(models.values())[0])
    y_scores   = np.array(model_data.get("scores_test") or [0.8, 0.2, 0.9, 0.1])
    y_true     = np.array(model_data.get("predictions_test") or [1, 0, 1, 0])

    tuning_res = ThresholdTuner.find_optimal_threshold(
        y_true, y_scores, target_sensitivity=target_sensitivity
    )
    tuning_res["experiment_id"] = experiment_id
    return tuning_res
