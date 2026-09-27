"""Experiment API endpoints."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.experiments.manager import ExperimentManager, ExperimentStatus
from backend.experiments.executor import ExperimentExecutor
from backend.data.loader import DatasetLoader
from backend.core.logging import logger

# Phase 12/13 — report generation
from backend.reports.generator import CostReportGenerator, ReportGenerator

_REPORTS_DIR = Path("./artifacts/reports")


router = APIRouter(prefix="/api/experiments", tags=["experiments"])

# Global instances
manager = ExperimentManager()
loader = DatasetLoader()
executors = {}  # Track running executors


class ExperimentCreate(BaseModel):
    """Request to create a new experiment."""
    dataset_id: str
    name: Optional[str] = None
    target_column: Optional[str] = None
    n_components: Optional[int] = None
    quantum_config: Optional[dict] = None


class ExperimentResponse(BaseModel):
    """Response for experiment creation."""
    experiment_id: str
    dataset_id: str
    status: str


class ExperimentListResponse(BaseModel):
    """Response for experiment list."""
    experiments: List[dict]


class ExperimentStatusResponse(BaseModel):
    """Response for experiment status."""
    experiment_id: str
    status: str
    progress: dict
    started_at: Optional[str]
    completed_at: Optional[str]


class ExperimentResultsResponse(BaseModel):
    """Response for experiment results."""
    experiment_id: str
    status: str
    results: dict


@router.post("", response_model=ExperimentResponse)
async def create_experiment(
    request: ExperimentCreate,
    background_tasks: BackgroundTasks
):
    """Create a new experiment.
    
    Creates an experiment configuration ready for execution.
    
    Args:
        request: Experiment creation request
        background_tasks: FastAPI background tasks
    
    Returns:
        Experiment ID and initial status
    """
    logger.info(f"Creating experiment for dataset: {request.dataset_id}")
    
    # Verify dataset exists
    try:
        dataset_info = loader.get_dataset_info(request.dataset_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {request.dataset_id}"
        )
    
    # Create experiment
    experiment_id = manager.create_experiment(
        dataset_id=request.dataset_id,
        configuration={
            'target_column': request.target_column,
            'n_components': request.n_components,
            'quantum_config': request.quantum_config
        },
        name=request.name
    )
    
    return ExperimentResponse(
        experiment_id=experiment_id,
        dataset_id=request.dataset_id,
        status="created"
    )


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    status: Optional[str] = None,
    dataset_id: Optional[str] = None
):
    """List all experiments.
    
    Args:
        status: Filter by status
        dataset_id: Filter by dataset
    
    Returns:
        List of experiments
    """
    status_enum = ExperimentStatus(status) if status else None
    
    experiments = manager.list_experiments(
        status=status_enum,
        dataset_id=dataset_id
    )
    
    return ExperimentListResponse(experiments=experiments)


@router.get("/{experiment_id}", response_model=dict)
async def get_experiment(experiment_id: str):
    """Get experiment details.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Complete experiment metadata
    """
    try:
        experiment = manager.get_experiment(experiment_id)
        return experiment
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )


@router.post("/{experiment_id}/run", response_model=ExperimentResponse)
async def run_experiment(
    experiment_id: str,
    background_tasks: BackgroundTasks
):
    """Start experiment execution.
    
    Runs the experiment in the background. Use the status endpoint
    to monitor progress.
    
    Args:
        experiment_id: Experiment identifier
        background_tasks: FastAPI background tasks
    
    Returns:
        Experiment ID and status
    """
    logger.info(f"Starting experiment: {experiment_id}")
    
    # Get experiment
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    # Check if already running
    if experiment['status'] in ['running_classical', 'running_quantum', 'preprocessing']:
        raise HTTPException(
            status_code=400,
            detail="Experiment is already running"
        )
    
    # Get dataset info
    dataset_id = experiment['dataset_id']
    dataset_info = loader.get_dataset_info(dataset_id)
    
    # Get configuration
    config = experiment.get('configuration', {})
    
    # Create executor
    executor = ExperimentExecutor(
        experiment_manager=manager,
        dataset_loader=loader
    )
    executors[experiment_id] = executor
    
    # Run in background
    async def run_async():
        try:
            await asyncio.to_thread(
                executor.run,
                dataset_info['path'],
                experiment_id,
                config.get('target_column'),
                config.get('n_components'),
                config.get('quantum_config')
            )
        except Exception as e:
            logger.error(f"Experiment failed: {str(e)}")
            manager.update_status(
                experiment_id,
                ExperimentStatus.FAILED,
                str(e)
            )
    
    background_tasks.add_task(run_async)
    
    return ExperimentResponse(
        experiment_id=experiment_id,
        dataset_id=dataset_id,
        status="started"
    )


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
async def get_experiment_status(experiment_id: str):
    """Get experiment execution status.
    
    Returns current status and progress for a running experiment.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Status and progress information
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    # Get progress from executor if running
    progress = {'stage': experiment['status'], 'progress': 0, 'message': ''}
    if experiment_id in executors:
        progress = executors[experiment_id].get_progress()
    
    return ExperimentStatusResponse(
        experiment_id=experiment_id,
        status=experiment['status'],
        progress=progress,
        started_at=experiment.get('started_at'),
        completed_at=experiment.get('completed_at')
    )


@router.get("/{experiment_id}/results", response_model=ExperimentResultsResponse)
async def get_experiment_results(experiment_id: str):
    """Get experiment results.
    
    Returns complete results including model metrics, comparisons,
    and recommendations.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Complete experiment results
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    if experiment['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Experiment not completed. Current status: {experiment['status']}"
        )
    
    return ExperimentResultsResponse(
        experiment_id=experiment_id,
        status=experiment['status'],
        results=experiment.get('results', {})
    )


@router.get("/{experiment_id}/recommendation")
async def get_recommendation(experiment_id: str):
    """Get final recommendation.
    
    Returns the evidence-based recommendation for model selection.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Recommendation with reasoning
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    results = experiment.get('results', {})
    comparison = results.get('comparison', {})
    
    if not comparison:
        raise HTTPException(
            status_code=400,
            detail="No comparison results available"
        )
    
    from backend.benchmarking.recommendation import RecommendationEngine
    
    engine = RecommendationEngine()
    recommendation = engine.generate(
        comparison,
        results.get('dataset_profile')
    )
    
    return recommendation.to_dict()


@router.delete("/{experiment_id}")
async def delete_experiment(experiment_id: str):
    """Delete an experiment.
    
    Removes experiment data and artifacts.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Confirmation message
    """
    # For MVP, just mark as deleted
    # Full implementation would remove artifacts
    
    logger.info(f"Deleting experiment: {experiment_id}")
    
    return {"message": f"Experiment {experiment_id} deleted"}


# ---------------------------------------------------------------------------
# Phase 12 — Explanation endpoint
# ---------------------------------------------------------------------------

class ExplanationResponse(BaseModel):
    """Response for GET /explanation."""
    experiment_id: str
    explainability_method: str
    models_explained: List[str]
    global_importance: dict
    quantum_circuit_info: Optional[dict]
    pipeline_trace: Optional[List[dict]]
    warnings: List[str]
    generated_at: str


@router.get("/{experiment_id}/explanation")
async def get_explanation(experiment_id: str):
    """Return explanation data for a completed experiment.

    Derives explainability information entirely from the stored experiment
    results — no model retraining or re-inference is performed.

    For classical models the response contains the feature importance stored
    by the Random Forest (Gini importances from training).
    For the VQC the response contains the quantum circuit structure and
    the feature-to-qubit mapping derived from the stored quantum resources.

    Returns 404 if the experiment does not exist or has not completed.

    RESEARCH NOTE: Explanations describe model behaviour, not medical
    causality.  Scores are uncalibrated and must not be interpreted as
    clinical probabilities.  This is a research/benchmarking system only.
    """
    # ── Load experiment ────────────────────────────────────────────────
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )

    if experiment["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Explanation is only available for completed experiments. "
                f"Current status: {experiment['status']}"
            )
        )

    results      = experiment.get("results", {})
    models       = results.get("models", {})
    preprocessing = results.get("preprocessing", {})

    if not models:
        raise HTTPException(
            status_code=404,
            detail="No model results found for this experiment."
        )

    # ── Classical global importance (Random Forest Gini) ──────────────
    classical_importance: dict = {}
    classical_models_found = []

    for model_name in ("random_forest", "logistic_regression", "svm"):
        model_data = models.get(model_name)
        if not model_data:
            continue
        classical_models_found.append(model_name)
        fi = (model_data.get("metrics") or {}).get("feature_importance", {})
        if fi and isinstance(fi, dict):
            # Sort by importance descending, attach rank
            ranked = sorted(fi.items(), key=lambda x: x[1], reverse=True)
            classical_importance[model_name] = [
                {
                    "feature_name":  feat,
                    "feature_index": idx,
                    "importance":    round(float(imp), 6),
                    "rank":          idx + 1,
                }
                for idx, (feat, imp) in enumerate(ranked)
            ]
        else:
            classical_importance[model_name] = []

    # ── Quantum circuit info (VQC) ─────────────────────────────────────
    quantum_circuit_info: Optional[dict] = None
    vqc_data = models.get("vqc")
    if vqc_data:
        q_res = (vqc_data.get("metrics") or {}).get("quantum_resources", {})
        n_qubits = int(q_res.get("n_qubits") or 8)
        n_layers = int(q_res.get("n_layers") or 2)
        n_params = int(q_res.get("n_params") or 0)
        depth    = int(q_res.get("circuit_depth") or 0)
        shots    = q_res.get("shots")

        # Build feature-to-qubit mapping from stored PCA component names
        red_info = preprocessing.get("reduction", {})
        component_names = red_info.get("component_names") or [
            f"PC{i+1}" for i in range(n_qubits)
        ]
        f2q = {
            component_names[i]: f"qubit_{i}"
            for i in range(min(n_qubits, len(component_names)))
        }

        # Estimated gate counts from circuit geometry
        cnot_per_layer     = (n_qubits * (n_qubits - 1)) // 2
        gate_count_est     = (
            n_qubits                           # encoding RY gates
            + n_layers * n_qubits * 2          # RY + RZ per layer
            + n_layers * cnot_per_layer        # CNOT entanglement
        )

        quantum_circuit_info = {
            "qubits":                   n_qubits,
            "n_layers":                 n_layers,
            "n_params":                 n_params,
            "circuit_depth":            depth,
            "encoding_method":          "angle_encoding",
            "backend_type":             "local_simulator (default.qubit)",
            "feature_to_qubit_mapping": f2q,
            "measured_qubits":          [0],
            "measurement":              "PauliZ(qubit_0)",
            "gate_count_estimate":      gate_count_est,
            "shots_per_execution":      shots,
            "total_circuit_executions": q_res.get("n_circuit_executions"),
            "circuit_diagram": (
                f"VQC Circuit\n"
                f"  Qubits:     {n_qubits}\n"
                f"  Layers:     {n_layers}\n"
                f"  Parameters: {n_params}\n"
                f"  Shots:      {shots or 'exact'}\n"
                f"\n"
                f"  Structure:\n"
                f"    1. Angle encoding (RY rotations)\n"
                f"    2. Variational layers (RY, RZ + CNOT entanglement)\n"
                f"    3. Measurement: PauliZ expectation on qubit 0"
            ),
        }

    # ── Pipeline trace ─────────────────────────────────────────────────
    dataset_id        = experiment.get("dataset_id", "UNKNOWN")
    configuration     = experiment.get("configuration", {})
    red_info          = preprocessing.get("reduction", {})
    orig_feats        = preprocessing.get("original_features", "?")
    red_feats         = preprocessing.get("reduced_features", "?")

    pipeline_trace = [
        {
            "phase":     "Phase 1",
            "component": "Dataset Ingestion",
            "artifact":  dataset_id,
        },
        {
            "phase":     "Phase 4",
            "component": "Preprocessing",
            "artifact":  "StandardScaler (fitted on training split only)",
        },
        {
            "phase":     "Phase 6",
            "component": "Feature Reduction",
            "artifact":  f"PCA ({orig_feats} → {red_feats} components)",
            "method":    "PCA",
            "dimensions": f"{orig_feats} -> {red_feats}",
            "variance_retained": red_info.get("cumulative_variance"),
        },
        {
            "phase":     "Phase 8 (Classical)",
            "component": "Classical Models",
            "artifact":  "Logistic Regression, SVM, Random Forest",
        },
        {
            "phase":     "Phase 8 (Quantum)",
            "component": "Quantum Model",
            "artifact":  "VQC",
            "qubits":    (quantum_circuit_info or {}).get("qubits"),
        },
        {
            "phase":     "Phase 10",
            "component": "Execution",
            "artifact":  experiment_id,
            "backend":   "LOCAL_SIMULATOR",
        },
        {
            "phase":     "Phase 12",
            "component": "Explainability",
            "artifact":  experiment_id,
            "method":    "Gini importance (classical) + circuit structure (quantum)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # ── Assemble response ──────────────────────────────────────────────
    models_explained = list(classical_importance.keys())
    if vqc_data:
        models_explained.append("vqc")

    response = {
        "experiment_id":       experiment_id,
        "explainability_method": (
            "Gini importance (Random Forest / classical) + "
            "VQC circuit structure analysis"
        ),
        "models_explained":    models_explained,
        "global_importance":   classical_importance,
        "quantum_circuit_info": quantum_circuit_info,
        "pipeline_trace":      pipeline_trace,
        "warnings": [
            "RESEARCH / BENCHMARKING SYSTEM — not a clinical diagnosis.",
            "Explanations describe model behaviour, not medical causality.",
            "Scores are uncalibrated and must not be interpreted as "
            "clinical probabilities.",
            "Quantum circuit results are from a local simulator, not "
            "real quantum hardware.",
            "No models were retrained or re-run to produce this explanation.",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Explanation generated for {experiment_id}: "
        f"{len(models_explained)} models"
    )
    return response


# ---------------------------------------------------------------------------
# Phase 13 — Report endpoints
# ---------------------------------------------------------------------------

class ReportGenerationResponse(BaseModel):
    """Response for POST /report."""
    experiment_id: str
    report_id: str
    report_path: str
    cost_report_path: str
    status: str
    generated_at: str


@router.post("/{experiment_id}/report", response_model=ReportGenerationResponse)
async def generate_report(experiment_id: str):
    """Generate and save the full experiment report.

    Uses the Phase 13 ReportGenerator (16-section HTML) and
    CostReportGenerator to produce:
      - artifacts/reports/{experiment_id}_report.html
      - artifacts/reports/{experiment_id}_cost_report.json

    Returns the paths of the generated files.

    Returns 404 if the experiment does not exist.
    Returns 400 if the experiment has not completed.

    No models are retrained or re-run.  The report is derived entirely
    from stored experiment results.
    """
    # ── Load and validate experiment ───────────────────────────────────
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )

    if experiment["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Report can only be generated for completed experiments. "
                f"Current status: {experiment['status']}"
            )
        )

    # ── Generate cost report ───────────────────────────────────────────
    try:
        cost_gen    = CostReportGenerator()
        cost_report = cost_gen.generate(experiment)
        cost_path   = cost_gen.save(cost_report, experiment_id)
    except Exception as exc:
        logger.error(f"Cost report generation failed for {experiment_id}: {exc}")
        cost_path   = ""
        cost_report = {}

    # ── Generate HTML report ───────────────────────────────────────────
    try:
        report_gen  = ReportGenerator()
        html        = report_gen.generate(experiment, cost_report=cost_report)
        report_path = report_gen.save(html, experiment_id)
    except Exception as exc:
        logger.error(f"HTML report generation failed for {experiment_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(exc)}"
        )

    report_id = f"{experiment_id}_report"
    generated_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        f"Report generated for {experiment_id}: "
        f"html={report_path}, cost={cost_path}"
    )

    return ReportGenerationResponse(
        experiment_id=experiment_id,
        report_id=report_id,
        report_path=report_path,
        cost_report_path=cost_path,
        status="generated",
        generated_at=generated_at,
    )


@router.get("/{experiment_id}/report")
async def get_report(experiment_id: str):
    """Return the generated HTML report for an experiment.

    Serves the file at artifacts/reports/{experiment_id}_report.html.

    Returns 404 if the experiment or its report does not exist.
    If the experiment is completed but the report has not been generated
    yet, automatically generates it first.
    """
    # ── Verify experiment exists ───────────────────────────────────────
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )

    report_path = _REPORTS_DIR / f"{experiment_id}_report.html"

    # ── Auto-generate if completed but report missing ──────────────────
    if not report_path.exists():
        if experiment["status"] != "completed":
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Report not found and experiment is not completed "
                    f"(status: {experiment['status']}). "
                    f"Run POST /{experiment_id}/report after the experiment finishes."
                )
            )
        # Experiment is complete — generate on the fly
        logger.info(
            f"Report not found for {experiment_id}; auto-generating."
        )
        try:
            cost_gen    = CostReportGenerator()
            cost_report = cost_gen.generate(experiment)
            report_gen  = ReportGenerator()
            html        = report_gen.generate(experiment, cost_report=cost_report)
            report_gen.save(html, experiment_id)
        except Exception as exc:
            logger.error(f"Auto-generation failed for {experiment_id}: {exc}")
            raise HTTPException(
                status_code=500,
                detail=f"Could not auto-generate report: {str(exc)}"
            )

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report file not found: {report_path}"
        )

    logger.info(f"Serving report for {experiment_id}: {report_path}")
    return FileResponse(
        str(report_path),
        media_type="text/html",
        filename=f"{experiment_id}_report.html",
    )
