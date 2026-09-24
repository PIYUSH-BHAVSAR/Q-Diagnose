"""Model comparison for classical vs quantum benchmarking."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.core.logging import logger
from backend.benchmarking.metrics import MetricsCalculator, ClassificationMetrics
from backend.models.classical.logistic_regression import ModelResult


@dataclass
class ComparisonResult:
    """Result of model comparison."""
    best_model: str
    best_classical: str
    best_quantum: str
    performance_ranking: List[dict]
    metrics_comparison: Dict[str, dict]
    runtime_comparison: Dict[str, float]
    quantum_vs_classical: dict
    recommendation: str
    
    def to_dict(self) -> dict:
        return {
            'best_model': self.best_model,
            'best_classical': self.best_classical,
            'best_quantum': self.best_quantum,
            'performance_ranking': self.performance_ranking,
            'metrics_comparison': self.metrics_comparison,
            'runtime_comparison': self.runtime_comparison,
            'quantum_vs_classical': self.quantum_vs_classical,
            'recommendation': self.recommendation
        }


class ModelComparison:
    """Compares classical and quantum models.
    
    Evaluates:
    - Predictive performance (accuracy, recall, AUC)
    - Computational cost (runtime)
    - Quantum-specific metrics
    - Trade-offs
    """
    
    # Metrics to compare
    PRIMARY_METRICS = ['accuracy', 'recall', 'f1', 'roc_auc']
    TRADE_OFF_METRICS = ['training_time', 'inference_time']
    
    def compare(
        self,
        results: Dict[str, ModelResult]
    ) -> ComparisonResult:
        """Compare all model results.
        
        Args:
            results: Dictionary of model name -> ModelResult
        
        Returns:
            ComparisonResult with rankings and analysis
        """
        logger.info(f"Comparing {len(results)} models")
        
        # Separate classical and quantum
        classical_results = {
            k: v for k, v in results.items()
            if v.model_type == 'classical'
        }
        quantum_results = {
            k: v for k, v in results.items()
            if v.model_type == 'quantum'
        }
        
        # Rank by primary metric (accuracy or F1)
        rankings = self._rank_models(results)
        
        # Best models
        best_model = rankings[0]['model']
        best_classical = self._get_best_in_category(classical_results, 'accuracy')
        best_quantum = self._get_best_in_category(quantum_results, 'accuracy') if quantum_results else None
        
        # Metrics comparison
        metrics_comparison = self._compare_metrics(results)
        
        # Runtime comparison
        runtime_comparison = {
            name: result.training_time
            for name, result in results.items()
        }
        
        # Quantum vs Classical comparison
        quantum_vs_classical = self._compare_quantum_classical(
            classical_results, quantum_results
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            results, quantum_vs_classical
        )
        
        return ComparisonResult(
            best_model=best_model,
            best_classical=best_classical,
            best_quantum=best_quantum or 'N/A',
            performance_ranking=rankings,
            metrics_comparison=metrics_comparison,
            runtime_comparison=runtime_comparison,
            quantum_vs_classical=quantum_vs_classical,
            recommendation=recommendation
        )
    
    def _rank_models(
        self,
        results: Dict[str, ModelResult]
    ) -> List[dict]:
        """Rank models by performance."""
        rankings = []
        
        for name, result in results.items():
            metrics = result.metrics or {}
            
            # Use F1 as primary ranking metric for imbalanced data
            # Falls back to accuracy if F1 not available
            score = metrics.get('f1') or metrics.get('accuracy', 0)
            
            rankings.append({
                'model': name,
                'type': result.model_type,
                'score': round(score, 4),
                'accuracy': round(metrics.get('accuracy', 0), 4),
                'recall': round(metrics.get('recall', 0), 4),
                'f1': round(metrics.get('f1', 0), 4),
                'roc_auc': round(metrics.get('roc_auc', 0), 4) if metrics.get('roc_auc') else None,
                'training_time': round(result.training_time, 4)
            })
        
        # Sort by F1 (or accuracy)
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        return rankings
    
    def _get_best_in_category(
        self,
        results: Dict[str, ModelResult],
        metric: str
    ) -> str:
        """Get best model in a category (classical/quantum)."""
        if not results:
            return 'N/A'
        
        best_name = None
        best_score = -1
        
        for name, result in results.items():
            score = (result.metrics or {}).get(metric, 0)
            if score > best_score:
                best_score = score
                best_name = name
        
        return best_name
    
    def _compare_metrics(
        self,
        results: Dict[str, ModelResult]
    ) -> Dict[str, dict]:
        """Compare metrics across all models."""
        comparison = {}
        
        for name, result in results.items():
            if result.metrics:
                comparison[name] = {
                    k: round(v, 4) if isinstance(v, (int, float)) else v
                    for k, v in result.metrics.items()
                    if k != 'quantum_resources'
                }
        
        return comparison
    
    def _compare_quantum_classical(
        self,
        classical_results: Dict[str, ModelResult],
        quantum_results: Dict[str, ModelResult]
    ) -> dict:
        """Compare quantum vs best classical."""
        if not classical_results or not quantum_results:
            return {'status': 'incomplete', 'message': 'Missing results'}
        
        # Get best classical
        best_classical_name = self._get_best_in_category(
            classical_results, 'accuracy'
        )
        best_classical = classical_results[best_classical_name]
        
        # Get quantum result (typically just VQC)
        quantum_name = list(quantum_results.keys())[0]
        quantum = quantum_results[quantum_name]
        
        # Calculate differences
        comparison = {
            'classical_model': best_classical_name,
            'quantum_model': quantum_name,
            'metrics_diff': {},
            'runtime_diff': {}
        }
        
        for metric in ['accuracy', 'recall', 'precision', 'f1', 'roc_auc']:
            classical_val = best_classical.metrics.get(metric)
            quantum_val = quantum.metrics.get(metric)
            
            if classical_val is not None and quantum_val is not None:
                diff = quantum_val - classical_val
                comparison['metrics_diff'][metric] = {
                    'classical': round(classical_val, 4),
                    'quantum': round(quantum_val, 4),
                    'difference': round(diff, 4),
                    'quantum_better': diff > 0
                }
        
        # Runtime comparison
        comparison['runtime_diff'] = {
            'classical': round(best_classical.training_time, 4),
            'quantum': round(quantum.training_time, 4),
            'ratio': round(quantum.training_time / max(best_classical.training_time, 0.001), 2)
        }
        
        # Quantum resources
        if 'quantum_resources' in quantum.metrics:
            comparison['quantum_resources'] = quantum.metrics['quantum_resources']
        
        return comparison
    
    def _generate_recommendation(
        self,
        results: Dict[str, ModelResult],
        quantum_vs_classical: dict
    ) -> str:
        """Generate recommendation based on results."""
        
        if 'metrics_diff' not in quantum_vs_classical:
            return "Unable to generate recommendation: incomplete comparison"
        
        metrics_diff = quantum_vs_classical['metrics_diff']
        runtime_diff = quantum_vs_classical['runtime_diff']
        
        # Analyze performance differences
        quantum_wins = sum(
            1 for diff in metrics_diff.values()
            if diff.get('quantum_better', False)
        )
        total_metrics = len(metrics_diff)
        
        # Check for significant improvement
        accuracy_diff = metrics_diff.get('accuracy', {}).get('difference', 0)
        recall_diff = metrics_diff.get('recall', {}).get('difference', 0)
        f1_diff = metrics_diff.get('f1', {}).get('difference', 0)
        runtime_ratio = runtime_diff.get('ratio', 1)
        
        # Decision logic
        if accuracy_diff > 0.02 and runtime_ratio < 10:
            return (
                "PROMISING QUANTUM ADVANTAGE: "
                f"Quantum model shows +{accuracy_diff*100:.1f}% accuracy improvement "
                f"with {runtime_ratio:.1f}x runtime cost. "
                "Consider for recall-sensitive applications."
            )
        elif accuracy_diff > 0 and runtime_ratio < 5:
            return (
                "QUANTUM PERFORMANCE PARITY: "
                f"Quantum model shows modest +{accuracy_diff*100:.1f}% accuracy improvement "
                f"with {runtime_ratio:.1f}x runtime cost. "
                "Both approaches viable."
            )
        elif accuracy_diff >= -0.02 and recall_diff > 0:
            return (
                "QUANTUM RECALL ADVANTAGE: "
                f"Quantum model shows +{recall_diff*100:.1f}% recall improvement "
                "while maintaining competitive accuracy. "
                "Consider for disease screening where recall is critical."
            )
        elif accuracy_diff < -0.02:
            classical_speedup = round(1 / runtime_ratio, 1) if runtime_ratio > 0 else float('inf')
            return (
                "CLASSICAL MODEL PREFERRED: "
                f"Classical model shows +{-accuracy_diff*100:.1f}% accuracy advantage "
                f"with {classical_speedup}x lower runtime. "
                "Recommended for production use."
            )
        else:
            return (
                "PERFORMANCE PARITY: "
                "Quantum and classical models show comparable performance. "
                "Classical model preferred due to lower computational cost."
            )
