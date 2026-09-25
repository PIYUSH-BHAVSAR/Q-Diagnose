"""Experiment executor for running complete ML pipelines.

Executes the full experiment workflow:
1. Load dataset
2. Profile and validate
3. Preprocess and reduce features
4. Train classical models
5. Train quantum model
6. Compare and benchmark
7. Generate explanations
8. Produce recommendation
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.core.config import config
from backend.core.logging import logger
from backend.data.adapters import AdapterRegistry
from backend.data.loader import DatasetLoader
from backend.data.profiler import DatasetProfiler
from backend.data.validator import DatasetValidator
from backend.features.pipeline import FeaturePipeline, FeaturePipelineResult
from backend.models.classical.logistic_regression import LogisticRegressionModel
from backend.models.classical.svm import SVMModel
from backend.models.classical.random_forest import RandomForestModel
from backend.models.quantum.vqc import VQCModel
from backend.benchmarking.metrics import MetricsCalculator
from backend.benchmarking.comparison import ModelComparison
from backend.experiments.manager import ExperimentManager, ExperimentStatus
from backend.resources.monitor import ResourceMonitor


@dataclass
class ExecutionProgress:
    """Tracks experiment execution progress."""
    stage: str
    progress: float
    message: str
    details: dict = None
    
    def to_dict(self) -> dict:
        return {
            'stage': self.stage,
            'progress': self.progress,
            'message': self.message,
            'details': self.details or {}
        }


class ExperimentExecutor:
    """Executes complete hybrid QML experiments.
    
    This is the core orchestrator that:
    - Loads and validates data
    - Runs preprocessing
    - Trains all models (classical + quantum)
    - Compares results
    - Generates recommendations
    """
    
    def __init__(
        self,
        experiment_manager: Optional[ExperimentManager] = None,
        dataset_loader: Optional[DatasetLoader] = None,
        random_state: int = 42
    ):
        """Initialize experiment executor.
        
        Args:
            experiment_manager: Experiment manager instance
            dataset_loader: Dataset loader instance
            random_state: Random seed for reproducibility
        """
        self.manager = experiment_manager or ExperimentManager()
        self.loader = dataset_loader or DatasetLoader()
        self.random_state = random_state
        
        self.progress: List[ExecutionProgress] = []
        self._current_experiment: Optional[str] = None
    
    def run(
        self,
        dataset_path: str,
        experiment_id: Optional[str] = None,
        target_column: Optional[str] = None,
        n_components: Optional[int] = None,
        quantum_config: Optional[dict] = None
    ) -> dict:
        """Run complete experiment pipeline.
        
        Args:
            dataset_path: Path to CSV dataset
            experiment_id: Existing experiment ID (optional)
            target_column: Target column override
            n_components: PCA components override
            quantum_config: Quantum model configuration
        
        Returns:
            Complete experiment results
        """
        logger.info("=" * 70)
        logger.info("STARTING EXPERIMENT EXECUTION")
        logger.info("=" * 70)
        
        # Get quantum config
        q_config = quantum_config or config.quantum_config
        n_components = n_components or q_config.get('candidate_dimensions', [8])[0]
        
        # Load dataset
        self._update_progress("loading", 0.05, "Loading dataset")
        
        if experiment_id:
            exp = self.manager.get_experiment(experiment_id)
            dataset_id = exp['dataset_id']
            dataset_info = self.loader.get_dataset_info(dataset_id)
            df = pd.read_csv(dataset_info['path'])
        else:
            dataset_id, df = self.loader.load_csv(dataset_path)
            dataset_info = self.loader.get_dataset_info(dataset_id)
        
        self._update_progress("profiling", 0.10, "Profiling dataset")
        
        # Profile dataset
        profiler = DatasetProfiler()
        profile = profiler.profile(df, dataset_id, dataset_info['name'])
        
        # Validate
        self._update_progress("validating", 0.15, "Validating dataset")
        
        validator = DatasetValidator()
        validation = validator.validate(df, profile, target_column)
        
        if not validation.is_valid:
            raise ValueError(f"Dataset validation failed: {validation.issues}")
        
        # Detect and apply adapter
        registry = AdapterRegistry()
        adapter = registry.detect_adapter(df)
        
        if adapter:
            logger.info(f"Using adapter: {adapter.name}")
            X, y, metadata = adapter.adapt(df)
            # subject_ids must be a numpy array for GroupShuffleSplit
            raw_ids = metadata.get('subject_ids')
            subject_ids = np.array(raw_ids) if raw_ids is not None else None
        else:
            # Generic processing
            target_col = target_column or profile.recommended_target
            if not target_col:
                raise ValueError("No target column detected or specified")
            
            y = df[target_col]
            X = df.drop(columns=[target_col])
            subject_ids = None
            
            # Remove non-numeric columns
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            X = X[numeric_cols]
        
        # Create experiment if needed
        if not experiment_id:
            experiment_id = self.manager.create_experiment(
                dataset_id=dataset_id,
                configuration={
                    'target_column': target_column or profile.recommended_target,
                    'n_components': n_components,
                    'quantum_config': q_config,
                    'random_state': self.random_state,
                    'adapter': adapter.name if adapter else None
                }
            )
        
        self._current_experiment = experiment_id
        
        # Start resource monitoring
        resource_monitor = ResourceMonitor()
        resource_monitor.start()
        
        try:
            # Preprocessing
            self._update_progress("preprocessing", 0.20, "Preprocessing data")
            self.manager.update_status(experiment_id, ExperimentStatus.PREPROCESSING)
            
            feature_pipeline = FeaturePipeline(
                test_size=config.experiment['test_size'],
                random_state=self.random_state,
                n_components=n_components,
                max_qubits=q_config.get('max_qubits', 8)
            )
            
            processed = feature_pipeline.fit_transform(X, y, subject_ids)
            
            # Train classical models
            self._update_progress("classical", 0.30, "Training classical models")
            self.manager.update_status(experiment_id, ExperimentStatus.RUNNING_CLASSICAL)
            
            classical_results = self._train_classical_models(
                processed, experiment_id
            )
            
            # Train quantum model
            self._update_progress("quantum", 0.60, "Training quantum model")
            self.manager.update_status(experiment_id, ExperimentStatus.RUNNING_QUANTUM)
            
            quantum_result = self._train_quantum_model(
                processed, n_components, q_config
            )
            
            # Benchmarking
            self._update_progress("benchmarking", 0.80, "Comparing models")
            self.manager.update_status(experiment_id, ExperimentStatus.BENCHMARKING)
            
            comparison = ModelComparison()
            all_results = {
                **classical_results,
                'vqc': quantum_result
            }
            
            comparison_result = comparison.compare(all_results)
            comparison_dict = comparison_result.to_dict()
            
            # Resources
            resource_usage = resource_monitor.stop()
            
            # Compile results
            self._update_progress("finalizing", 0.95, "Finalizing results")
            
            results = {
                'dataset_profile': profile.to_dict(),
                'validation': validation.to_dict(),
                'preprocessing': processed.to_dict(),
                'models': {
                    name: result.to_dict() 
                    for name, result in all_results.items()
                },
                'comparison': comparison_result.to_dict() if hasattr(comparison_result, 'to_dict') else comparison_result,
                'resource_usage': resource_usage.to_dict() if hasattr(resource_usage, 'to_dict') else resource_usage
            }
            
            # Store results
            self.manager.store_results(experiment_id, results)
            self.manager.update_status(experiment_id, ExperimentStatus.COMPLETED)
            
            # Auto-generate report
            from backend.api.reports import _generate_html_report
            from pathlib import Path
            reports_dir = Path("./artifacts/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_id = f"RPT-{experiment_id}"
            report_path = reports_dir / f"{report_id}.html"
            
            html_content = _generate_html_report(experiment_id, self.manager.get_experiment(experiment_id), results)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Auto-generated report: {report_id}")
            
            self._update_progress("completed", 1.0, "Experiment completed")
            
            logger.info("=" * 70)
            logger.info("EXPERIMENT COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            
            return {
                'experiment_id': experiment_id,
                'status': 'completed',
                'results': results
            }
            
        except Exception as e:
            self.manager.update_status(
                experiment_id, 
                ExperimentStatus.FAILED, 
                str(e)
            )
            raise
    
    def _train_classical_models(
        self,
        processed: FeaturePipelineResult,
        experiment_id: str
    ) -> Dict:
        """Train all classical models."""
        results = {}
        
        models = [
            ('logistic_regression', LogisticRegressionModel(random_state=self.random_state)),
            ('svm', SVMModel(random_state=self.random_state)),
            ('random_forest', RandomForestModel(random_state=self.random_state))
        ]
        
        for idx, (name, model) in enumerate(models):
            self._update_progress(
                "classical",
                0.30 + 0.10 * idx,
                f"Training {name}"
            )
            
            logger.info(f"Training {name}...")
            
            result = model.fit(
                processed.X_train,
                processed.y_train,
                processed.X_test,
                processed.y_test,
                processed.reduced_feature_names
            )
            
            results[name] = result
            
            logger.info(
                f"{name} complete: "
                f"accuracy={result.metrics.get('accuracy', 0):.4f}, "
                f"time={result.training_time:.2f}s"
            )
        
        return results
    
    def _train_quantum_model(
        self,
        processed: FeaturePipelineResult,
        n_components: int,
        quantum_config: dict
    ) -> object:
        """Train VQC model."""
        vqc = VQCModel(
            n_qubits=n_components,
            n_layers=quantum_config.get('layers', 2),
            shots=quantum_config.get('shots', 1024),
            epochs=quantum_config.get('epochs', 100),
            batch_size=quantum_config.get('batch_size', 32),
            learning_rate=quantum_config.get('learning_rate', 0.01),
            random_state=self.random_state
        )
        
        result = vqc.fit(
            processed.X_train,
            processed.y_train,
            processed.X_test,
            processed.y_test
        )
        
        logger.info(
            f"VQC complete: "
            f"accuracy={result.metrics.get('accuracy', 0):.4f}, "
            f"time={result.training_time:.2f}s"
        )
        
        return result
    
    def _update_progress(self, stage: str, progress: float, message: str):
        """Update execution progress."""
        progress_item = ExecutionProgress(
            stage=stage,
            progress=progress,
            message=message
        )
        
        self.progress.append(progress_item)
        logger.info(f"[{progress*100:.0f}%] {message}")
    
    def get_progress(self) -> dict:
        """Get current execution progress."""
        if self.progress:
            return self.progress[-1].to_dict()
        return {'stage': 'not_started', 'progress': 0, 'message': 'Not started'}
