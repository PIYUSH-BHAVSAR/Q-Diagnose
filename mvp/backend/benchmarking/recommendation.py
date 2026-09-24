"""Recommendation engine for final model selection.

Analyzes experiment results and provides evidence-based recommendations
for whether to use classical or quantum models.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.core.logging import logger


@dataclass
class Recommendation:
    """Final recommendation result."""
    decision: str  # 'quantum_advantage', 'quantum_parity', 'classical_preferred'
    best_model: str
    reasoning: List[str]
    metrics_summary: Dict
    trade_offs: Dict
    confidence: str  # 'high', 'medium', 'low'
    
    def to_dict(self) -> dict:
        return {
            'decision': self.decision,
            'best_model': self.best_model,
            'reasoning': self.reasoning,
            'metrics_summary': self.metrics_summary,
            'trade_offs': self.trade_offs,
            'confidence': self.confidence
        }


class RecommendationEngine:
    """Generates recommendations based on experiment results.
    
    Decision Framework:
    1. QUANTUM ADVANTAGE: Quantum significantly outperforms classical
    2. QUANTUM PARITY: Comparable performance with trade-offs
    3. CLASSICAL PREFERRED: Classical is better or quantum cost too high
    """
    
    # Thresholds for decision making
    SIGNIFICANT_IMPROVEMENT = 0.02  # 2% improvement
    ACCEPTABLE_RUNTIME_RATIO = 10.0  # 10x slower acceptable for significant gains
    MIN_SAMPLES_FOR_HIGH_CONFIDENCE = 100
    
    def generate(
        self,
        comparison_result: dict,
        dataset_info: Optional[dict] = None
    ) -> Recommendation:
        """Generate recommendation from comparison results.
        
        Args:
            comparison_result: Output from ModelComparison
            dataset_info: Optional dataset metadata
        
        Returns:
            Recommendation with decision and reasoning
        """
        logger.info("Generating recommendation")
        
        quantum_vs_classical = comparison_result.get('quantum_vs_classical', {})
        rankings = comparison_result.get('performance_ranking', [])
        
        if not quantum_vs_classical or 'metrics_diff' not in quantum_vs_classical:
            return self._default_recommendation("Insufficient data for comparison")
        
        metrics_diff = quantum_vs_classical['metrics_diff']
        runtime_diff = quantum_vs_classical['runtime_diff']
        
        # Extract key metrics
        accuracy_diff = metrics_diff.get('accuracy', {}).get('difference', 0)
        recall_diff = metrics_diff.get('recall', {}).get('difference', 0)
        f1_diff = metrics_diff.get('f1', {}).get('difference', 0)
        runtime_ratio = runtime_diff.get('ratio', 1)
        
        quantum_model = quantum_vs_classical.get('quantum_model', 'vqc')
        classical_model = quantum_vs_classical.get('classical_model', 'unknown')
        
        reasoning = []
        trade_offs = {}
        
        # Analyze performance
        if accuracy_diff > self.SIGNIFICANT_IMPROVEMENT:
            reasoning.append(
                f"Quantum model shows significant accuracy improvement: "
                f"+{accuracy_diff*100:.1f}%"
            )
        elif accuracy_diff > 0:
            reasoning.append(
                f"Quantum model shows modest accuracy improvement: "
                f"+{accuracy_diff*100:.1f}%"
            )
        elif accuracy_diff < -self.SIGNIFICANT_IMPROVEMENT:
            reasoning.append(
                f"Classical model shows significant accuracy advantage: "
                f"+{-accuracy_diff*100:.1f}%"
            )
        
        # Analyze recall (critical for disease detection)
        if recall_diff > 0.02:
            reasoning.append(
                f"Quantum model shows higher recall: "
                f"+{recall_diff*100:.1f}% (important for disease screening)"
            )
        
        # Analyze runtime
        if runtime_ratio > 5:
            reasoning.append(
                f"Quantum model has higher computational cost: "
                f"{runtime_ratio:.1f}x runtime"
            )
            trade_offs['runtime'] = {
                'quantum_slower': True,
                'ratio': runtime_ratio
            }
        else:
            reasoning.append(
                f"Computational costs are comparable: "
                f"{runtime_ratio:.1f}x runtime"
            )
        
        # Make decision
        decision, best_model = self._make_decision(
            accuracy_diff=accuracy_diff,
            recall_diff=recall_diff,
            f1_diff=f1_diff,
            runtime_ratio=runtime_ratio,
            quantum_model=quantum_model,
            classical_model=classical_model
        )
        
        # Determine confidence
        confidence = self._assess_confidence(
            dataset_info=dataset_info,
            metrics_diff=metrics_diff
        )
        
        # Build metrics summary
        metrics_summary = {
            'quantum': {
                'accuracy': metrics_diff.get('accuracy', {}).get('quantum'),
                'recall': metrics_diff.get('recall', {}).get('quantum'),
                'runtime': runtime_diff.get('quantum')
            },
            'classical_best': {
                'accuracy': metrics_diff.get('accuracy', {}).get('classical'),
                'recall': metrics_diff.get('recall', {}).get('classical'),
                'runtime': runtime_diff.get('classical')
            }
        }
        
        return Recommendation(
            decision=decision,
            best_model=best_model,
            reasoning=reasoning,
            metrics_summary=metrics_summary,
            trade_offs=trade_offs,
            confidence=confidence
        )
    
    def _make_decision(
        self,
        accuracy_diff: float,
        recall_diff: float,
        f1_diff: float,
        runtime_ratio: float,
        quantum_model: str,
        classical_model: str
    ) -> tuple:
        """Make the final decision."""
        
        # Quantum Advantage: Significant performance gain with acceptable cost
        if accuracy_diff > self.SIGNIFICANT_IMPROVEMENT and runtime_ratio < self.ACCEPTABLE_RUNTIME_RATIO:
            return 'QUANTUM_ADVANTAGE', quantum_model
        
        # Quantum Advantage: Modest gain but high recall improvement
        if accuracy_diff > 0 and recall_diff > 0.03 and runtime_ratio < self.ACCEPTABLE_RUNTIME_RATIO:
            return 'QUANTUM_ADVANTAGE', quantum_model
        
        # Quantum Parity: Comparable performance
        if abs(accuracy_diff) <= 0.01 and runtime_ratio < 20:
            return 'QUANTUM_PARITY', quantum_model if recall_diff >= 0 else classical_model
        
        # Quantum Parity: Slightly worse but good recall
        if -0.02 <= accuracy_diff <= 0 and recall_diff > 0.02:
            return 'QUANTUM_PARITY', quantum_model
        
        # Classical Preferred: Better or much cheaper
        if accuracy_diff < -self.SIGNIFICANT_IMPROVEMENT:
            return 'CLASSICAL_PREFERRED', classical_model
        
        if runtime_ratio > self.ACCEPTABLE_RUNTIME_RATIO and accuracy_diff < 0.01:
            return 'CLASSICAL_PREFERRED', classical_model
        
        # Default: parity
        return 'QUANTUM_PARITY', classical_model
    
    def _assess_confidence(
        self,
        dataset_info: Optional[dict],
        metrics_diff: dict
    ) -> str:
        """Assess confidence in recommendation."""
        
        if not dataset_info:
            return 'medium'
        
        samples = dataset_info.get('rows', 0)
        
        if samples >= self.MIN_SAMPLES_FOR_HIGH_CONFIDENCE:
            return 'high'
        elif samples >= 50:
            return 'medium'
        else:
            return 'low'
    
    def _default_recommendation(self, message: str) -> Recommendation:
        """Create default recommendation when data is insufficient."""
        return Recommendation(
            decision='INCONCLUSIVE',
            best_model='N/A',
            reasoning=[message],
            metrics_summary={},
            trade_offs={},
            confidence='low'
        )
