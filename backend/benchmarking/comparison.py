"""
backend/benchmarking/comparison.py
Owner: Piyush
Phase: 11

ModelComparison — side-by-side comparison of all model results.
From phase11.md §8-9:
    Supports three comparison types:
        A. Same representation (strongest controlled comparison)
        B. Best classical vs best quantum
        C. Full benchmark table (all models)

    Best classical = highest ROC-AUC (phase11.md §9, guide §6)
    Best quantum   = highest ROC-AUC
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.models.result import ModelResult


@dataclass
class ComparisonResult:
    """
    Output of ModelComparison.compare().
    Consumed by RecommendationEngine and the API.
    """
    classical_results: Dict[str, ModelResult]          # all classical results
    quantum_results:   Dict[str, ModelResult]          # all quantum results
    best_classical:    Optional[ModelResult]           # highest ROC-AUC classical
    best_quantum:      Optional[ModelResult]           # highest ROC-AUC quantum
    all_results:       Dict[str, ModelResult] = field(default_factory=dict)

    def to_table(self) -> List[Dict]:
        """
        Phase 11 §9 — standardized performance table.
        Returns list of dicts, one per model, sorted by ROC-AUC descending.
        """
        rows = []
        for name, result in self.all_results.items():
            rows.append({
                "model_name":  result.model_name,
                "model_type":  result.model_type,
                "status":      result.status,
                "accuracy":    round(result.accuracy,    4),
                "precision":   round(result.precision,   4),
                "recall":      round(result.recall,      4),
                "specificity": round(result.specificity, 4),
                "f1_score":    round(result.f1_score,    4),
                "roc_auc":     round(result.roc_auc,     4),
                "pr_auc":      round(result.pr_auc,      4),
                "training_time_seconds": round(result.training_time_seconds, 3),
                "inference_time_seconds": round(result.inference_time_seconds, 6),
                "memory_peak_mb": round(result.memory_peak_mb, 2),
                "confusion_matrix": result.confusion_matrix,
            })
        return sorted(rows, key=lambda r: r["roc_auc"], reverse=True)

    def to_dict(self) -> dict:
        """JSON-serialisable summary."""
        return {
            "performance_table": self.to_table(),
            "best_classical": {
                "model_name": self.best_classical.model_name,
                "roc_auc":    round(self.best_classical.roc_auc, 4),
                "recall":     round(self.best_classical.recall, 4),
            } if self.best_classical else None,
            "best_quantum": {
                "model_name": self.best_quantum.model_name,
                "roc_auc":    round(self.best_quantum.roc_auc, 4),
                "recall":     round(self.best_quantum.recall, 4),
                "qubits":     self.best_quantum.qubits,
                "total_circuit_executions": self.best_quantum.total_circuit_executions,
            } if self.best_quantum else None,
        }


class ModelComparison:
    """
    Builds side-by-side comparisons of model results.

    Usage:
        comparison = ModelComparison().compare(results_dict)
        comparison.to_table()   # all models ranked
    """

    def compare(self, results: Dict[str, ModelResult]) -> ComparisonResult:
        """
        Phase 11 §8-9 — compare all model results.

        Args:
            results: dict mapping model_name → ModelResult
                     e.g. {"LogisticRegression": ..., "SVM": ..., "VQC": ...}

        Returns:
            ComparisonResult with best_classical, best_quantum, full table.
        """
        classical = {
            k: v for k, v in results.items()
            if v.model_type == "CLASSICAL" and v.status == "COMPLETED"
        }
        quantum = {
            k: v for k, v in results.items()
            if v.model_type == "QUANTUM" and v.status == "COMPLETED"
        }

        # Best by ROC-AUC (phase11.md §9 + guide §6)
        best_classical = (
            max(classical.values(), key=lambda r: r.roc_auc)
            if classical else None
        )
        best_quantum = (
            max(quantum.values(), key=lambda r: r.roc_auc)
            if quantum else None
        )

        return ComparisonResult(
            classical_results=classical,
            quantum_results=quantum,
            best_classical=best_classical,
            best_quantum=best_quantum,
            all_results=results,
        )

    def generalization_report(
        self,
        results: Dict[str, ModelResult],
        train_results: Optional[Dict[str, ModelResult]] = None,
    ) -> Dict:
        """
        Phase 11 §19-20 — generalization gap analysis.
        Compares train vs test ROC-AUC per model.
        Large gap → potential overfitting.
        """
        report = {}
        if train_results is None:
            return report

        for name, test_result in results.items():
            train_result = train_results.get(name)
            if train_result is None:
                continue
            gap = round(train_result.roc_auc - test_result.roc_auc, 4)
            report[name] = {
                "train_roc_auc": round(train_result.roc_auc, 4),
                "test_roc_auc":  round(test_result.roc_auc, 4),
                "generalization_gap": gap,
                "overfit_risk": "HIGH" if gap > 0.05 else ("MEDIUM" if gap > 0.02 else "LOW"),
            }
        return report
