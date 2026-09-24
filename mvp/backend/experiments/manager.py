"""Experiment manager for tracking and storing experiment metadata."""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.config import config
from backend.core.logging import logger


class ExperimentStatus(str, Enum):
    """Experiment status states."""
    CREATED = "created"
    VALIDATING = "validating"
    PREPROCESSING = "preprocessing"
    RUNNING_CLASSICAL = "running_classical"
    RUNNING_QUANTUM = "running_quantum"
    BENCHMARKING = "benchmarking"
    EXPLAINING = "explaining"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentManager:
    """Manages experiment lifecycle and metadata.
    
    Responsibilities:
    - Generate experiment IDs
    - Track experiment status
    - Store experiment configuration
    - Record model results
    - Persist experiment history
    """
    
    def __init__(self, storage_dir: str = "./artifacts/experiments"):
        """Initialize experiment manager.
        
        Args:
            storage_dir: Directory for experiment artifacts
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._experiments: Dict[str, dict] = {}
        
        # Load all experiments from disk on startup
        self._load_all_experiments()
    
    def create_experiment(
        self,
        dataset_id: str,
        configuration: dict,
        name: Optional[str] = None
    ) -> str:
        """Create a new experiment.
        
        Args:
            dataset_id: Dataset to use
            configuration: Experiment configuration
            name: Optional experiment name
        
        Returns:
            Experiment ID
        """
        experiment_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        
        experiment = {
            'id': experiment_id,
            'name': name or f"Experiment {experiment_id}",
            'dataset_id': dataset_id,
            'status': ExperimentStatus.CREATED.value,
            'configuration': configuration,
            'results': {},
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'error': None
        }
        
        self._experiments[experiment_id] = experiment
        
        # Persist
        self._save_experiment(experiment_id)
        
        logger.info(f"Created experiment: {experiment_id}")
        
        return experiment_id
    
    def update_status(
        self,
        experiment_id: str,
        status: ExperimentStatus,
        error: Optional[str] = None
    ):
        """Update experiment status.
        
        Args:
            experiment_id: Experiment identifier
            status: New status
            error: Optional error message
        """
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment = self._experiments[experiment_id]
        experiment['status'] = status.value
        
        if status == ExperimentStatus.RUNNING_CLASSICAL:
            if experiment['started_at'] is None:
                experiment['started_at'] = datetime.utcnow().isoformat()
        
        if status == ExperimentStatus.COMPLETED:
            experiment['completed_at'] = datetime.utcnow().isoformat()
        
        if error:
            experiment['error'] = error
            experiment['status'] = ExperimentStatus.FAILED.value
        
        self._save_experiment(experiment_id)
        
        logger.info(f"Experiment {experiment_id}: {status.value}")
    
    def store_results(
        self,
        experiment_id: str,
        results: dict
    ):
        """Store experiment results.
        
        Args:
            experiment_id: Experiment identifier
            results: Results dictionary
        """
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        self._experiments[experiment_id]['results'] = results
        self._save_experiment(experiment_id)
    
    def get_experiment(self, experiment_id: str) -> dict:
        """Get experiment metadata.
        
        Args:
            experiment_id: Experiment identifier
        
        Returns:
            Experiment metadata dictionary
        """
        if experiment_id not in self._experiments:
            # Try to load from disk
            self._load_experiment(experiment_id)
        
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        return self._experiments[experiment_id].copy()
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        dataset_id: Optional[str] = None
    ) -> List[dict]:
        """List experiments with optional filters.
        
        Args:
            status: Filter by status
            dataset_id: Filter by dataset
        
        Returns:
            List of experiment metadata
        """
        experiments = list(self._experiments.values())
        
        if status:
            experiments = [
                e for e in experiments
                if e['status'] == status.value
            ]
        
        if dataset_id:
            experiments = [
                e for e in experiments
                if e['dataset_id'] == dataset_id
            ]
        
        return experiments
    
    def _save_experiment(self, experiment_id: str):
        """Save experiment to disk."""
        experiment = self._experiments[experiment_id]
        path = self.storage_dir / f"{experiment_id}.json"
        
        with open(path, 'w') as f:
            json.dump(experiment, f, indent=2, default=str)
    
    def _load_experiment(self, experiment_id: str):
        """Load experiment from disk."""
        path = self.storage_dir / f"{experiment_id}.json"
        
        if path.exists():
            with open(path, 'r') as f:
                self._experiments[experiment_id] = json.load(f)
    
    def _load_all_experiments(self):
        """Load all experiments from disk on startup."""
        if self.storage_dir.exists():
            for path in self.storage_dir.glob("EXP-*.json"):
                try:
                    with open(path, 'r') as f:
                        exp = json.load(f)
                        self._experiments[exp['id']] = exp
                        logger.info(f"Loaded experiment from disk: {exp['id']}")
                except Exception as e:
                    logger.warning(f"Failed to load experiment {path}: {str(e)}")
