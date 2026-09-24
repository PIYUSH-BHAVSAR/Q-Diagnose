"""Results API endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.experiments.manager import ExperimentManager


router = APIRouter(prefix="/api", tags=["results"])

manager = ExperimentManager()


class MetricsComparison(BaseModel):
    """Metrics comparison between models."""
    model_name: str
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    training_time: float


class ConfusionMatrixResponse(BaseModel):
    """Confusion matrix for a model."""
    model_name: str
    matrix: List[List[int]]
    labels: List[str]


@router.get("/experiments/{experiment_id}/metrics")
async def get_metrics(experiment_id: str):
    """Get metrics for all models in an experiment.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Metrics for each model
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    results = experiment.get('results', {})
    models = results.get('models', {})
    
    metrics_list = []
    for model_name, model_data in models.items():
        metrics = model_data.get('metrics', {})
        metrics_list.append({
            'model_name': model_name,
            'model_type': model_data.get('model_type', 'unknown'),
            'accuracy': metrics.get('accuracy', 0),
            'precision': metrics.get('precision', 0),
            'recall': metrics.get('recall', 0),
            'f1': metrics.get('f1', 0),
            'roc_auc': metrics.get('roc_auc', 0),
            'training_time': model_data.get('training_time', 0)
        })
    
    return {'metrics': metrics_list}


@router.get("/experiments/{experiment_id}/comparison")
async def get_comparison(experiment_id: str):
    """Get model comparison results.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Detailed comparison between models
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
    
    return comparison


@router.get("/experiments/{experiment_id}/resources")
async def get_resources(experiment_id: str):
    """Get resource usage for an experiment.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Resource usage metrics
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    results = experiment.get('results', {})
    resources = results.get('resource_usage', {})
    
    # Add quantum resources if available
    quantum_resources = None
    models = results.get('models', {})
    if 'vqc' in models:
        vqc_metrics = models['vqc'].get('metrics', {})
        quantum_resources = vqc_metrics.get('quantum_resources')
    
    return {
        'system_resources': resources,
        'quantum_resources': quantum_resources
    }


@router.get("/experiments/{experiment_id}/confusion-matrix/{model_name}")
async def get_confusion_matrix(
    experiment_id: str,
    model_name: str
):
    """Get confusion matrix for a specific model.
    
    Args:
        experiment_id: Experiment identifier
        model_name: Model name
    
    Returns:
        Confusion matrix data
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    results = experiment.get('results', {})
    models = results.get('models', {})
    
    if model_name not in models:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {model_name}"
        )
    
    metrics = models[model_name].get('metrics', {})
    cm = metrics.get('confusion_matrix', [[0, 0], [0, 0]])
    
    return ConfusionMatrixResponse(
        model_name=model_name,
        matrix=cm,
        labels=['Negative', 'Positive']
    )
