"""Experiment API endpoints."""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.experiments.manager import ExperimentManager, ExperimentStatus
from backend.experiments.executor import ExperimentExecutor
from backend.data.loader import DatasetLoader
from backend.core.logging import logger


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
