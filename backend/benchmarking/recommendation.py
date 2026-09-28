"""
backend/benchmarking/recommendation.py
Owner: Piyush
Phase: 11

RecommendationEngine — produces the final verdict on quantum vs classical.
From phase11.md §25-34 + guide_piyush.md §6:

CRITICAL RULE (phase11.md §3 + guide §9):
    "Never manipulate the experiment to force quantum to win."
    "Never say 'Quantum accuracy > classical therefore quantum is better.'"

    Recommendation is based ONLY on measured deltas:
        QUANTUM_ADVANTAGE:    recall_delta > 3pp AND auc_delta > 1pp
        TRADEOFF:             recall_delta > 2pp AND auc_delta >= -1pp
        PERFORMANCE_PARITY:   |recall_delta| <= 2pp AND |auc_delta| <= 2pp
        CLASSICAL_ADVANTAGE:  otherwise

    Always show resource cost alongside performance verdict.
    Never claim universal advantage — use "on this evaluated dataset."
"""

from __future__ import annotations

import uuid
from typing import Optional

from backend.benchmarking.comparison import ComparisonResult
from backend.models.result import ModelResult


class RecommendationEngine:
    """
    Produces honest recommendation based on measured evidence only.

    Thresholds (guide_piyush.md §6):
        QUANTUM_ADVANTAGE   → recall_delta > 0.03 AND auc_delta > 0.01
        TRADEOFF            → recall_delta > 0.02 AND auc_delta >= -0.01
        PERFORMANCE_PARITY  → |recall_delta| <= 0.02 AND |auc_delta| <= 0.02
        CLASSICAL_ADVANTAGE → otherwise
    """

    def recommend(self, comparison: ComparisonResult) -> dict:
        """
        Phase 11 §34 — produce recommendation.json contract shape.

        Args:
            comparison: output of ModelComparison.compare()

        Returns:
            dict matching contracts/recommendation.json shape.
        """
        bc: Optional[ModelResult] = comparison.best_classical
        bq: Optional[ModelResult] = comparison.best_quantum

        # ── Handle missing results ─────────────────────────────────────────────
        if bc is None and bq is None:
            return self._inconclusive("No models completed successfully.")
        if bc is None:
            return self._inconclusive("No classical models completed — cannot compare.")
        if bq is None:
            return {
                "benchmark_id":   f"BENCH-{uuid.uuid4().hex[:6].upper()}",
                "classification": "CLASSICAL_ONLY",
                "observations":   ["Quantum model did not run — quantum was disabled for this dataset."],
                "recommendation_text": (
                    f"Only classical models were evaluated on this dataset. "
                    f"Best classical: {bc.model_name} with ROC-AUC={bc.roc_auc:.3f}, "
                    f"Recall={bc.recall:.3f}."
                ),
                "classical_best": self._result_summary(bc),
                "quantum_best":   None,
                "performance_differences": None,
                "resource_comparison": None,
            }

        # ── Compute deltas ────────────────────────────────────────────────────
        recall_delta = bq.recall  - bc.recall     # positive = quantum has higher recall
        auc_delta    = bq.roc_auc - bc.roc_auc   # positive = quantum has higher AUC
        acc_delta    = bq.accuracy - bc.accuracy
        time_ratio   = (
            bq.training_time_seconds / max(bc.training_time_seconds, 0.001)
        )
        infer_ratio  = (
            bq.inference_time_seconds / max(bc.inference_time_seconds, 0.0001)
        )

        # ── Classification logic (phase11.md + guide) ─────────────────────────
        classification = self._classify(recall_delta, auc_delta)

        # ── Observations (phase11.md §34) ─────────────────────────────────────
        observations = self._build_observations(
            bc, bq, recall_delta, auc_delta, acc_delta, time_ratio
        )

        # ── Recommendation text ───────────────────────────────────────────────
        recommendation_text = self._generate_text(classification, bc, bq, recall_delta, auc_delta, time_ratio)

        return {
            "benchmark_id":    f"BENCH-{uuid.uuid4().hex[:6].upper()}",
            "classical_best":  self._result_summary(bc),
            "quantum_best":    self._result_summary(bq),
            "performance_differences": {
                "accuracy_delta": round(acc_delta,    4),
                "recall_delta":   round(recall_delta, 4),
                "auc_delta":      round(auc_delta,    4),
                "f1_delta":       round(bq.f1_score - bc.f1_score, 4),
            },
            "resource_comparison": {
                "training_time_ratio":  round(time_ratio,  2),
                "inference_time_ratio": round(infer_ratio, 2),
                "quantum_circuit_executions": bq.total_circuit_executions,
                "quantum_qubits":             bq.qubits,
                "quantum_circuit_depth":      bq.circuit_depth,
            },
            "classification":      classification,
            "observations":        observations,
            "recommendation_text": recommendation_text,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _classify(self, recall_delta: float, auc_delta: float) -> str:
        """
        Pure threshold logic. No hardcoding of outcomes.
        Thresholds from guide_piyush.md §6 + phase11.md §25-26.
        """
        if recall_delta > 0.03 and auc_delta > 0.01:
            return "QUANTUM_ADVANTAGE"
        elif recall_delta > 0.02 and auc_delta >= -0.01:
            return "TRADEOFF"
        elif abs(recall_delta) <= 0.02 and abs(auc_delta) <= 0.02:
            return "PERFORMANCE_PARITY"
        else:
            return "CLASSICAL_ADVANTAGE"

    def _build_observations(
        self, bc, bq, recall_delta, auc_delta, acc_delta, time_ratio
    ):
        """Build factual observation bullet points from measured numbers."""
        obs = []
        qname = bq.model_name  # e.g. "VQC", "QuantumSVM"

        # Recall comparison
        if recall_delta > 0:
            obs.append(
                f"{qname} achieved {recall_delta:+.1%} higher recall than {bc.model_name} "
                f"({bq.recall:.1%} vs {bc.recall:.1%}) on this evaluated dataset."
            )
        else:
            obs.append(
                f"{bc.model_name} achieved {-recall_delta:+.1%} higher recall than {qname} "
                f"({bc.recall:.1%} vs {bq.recall:.1%}) on this evaluated dataset."
            )

        # AUC comparison
        if auc_delta > 0:
            obs.append(
                f"{qname} achieved {auc_delta:+.3f} higher ROC-AUC than {bc.model_name} "
                f"({bq.roc_auc:.3f} vs {bc.roc_auc:.3f})."
            )
        else:
            obs.append(
                f"{bc.model_name} achieved {-auc_delta:+.3f} higher ROC-AUC than {qname} "
                f"({bc.roc_auc:.3f} vs {bq.roc_auc:.3f})."
            )

        # Resource cost (always shown — phase11.md §21)
        obs.append(
            f"{qname} required {time_ratio:.1f}x more training time "
            f"({bq.training_time_seconds:.1f}s vs {bc.training_time_seconds:.1f}s)."
        )
        if bq.total_circuit_executions:
            obs.append(
                f"{qname} performed {bq.total_circuit_executions:,} circuit executions "
                f"using {bq.qubits} qubits with circuit depth {bq.circuit_depth}."
            )

        return obs

    def _generate_text(self, classification, bc, bq, recall_delta, auc_delta, time_ratio) -> str:
        """
        Honest recommendation text — never claims universal advantage.
        Uses "observed" and "on this evaluated dataset" (guide_piyush.md §9).
        """
        qname = bq.model_name  # e.g. "VQC", "QuantumSVM"
        if classification == "QUANTUM_ADVANTAGE":
            return (
                f"On this evaluated dataset, {qname} demonstrated a meaningful advantage over "
                f"{bc.model_name}: recall was {recall_delta:+.1%} higher "
                f"and ROC-AUC was {auc_delta:+.3f} higher. "
                f"This observed advantage came at a computational cost of {time_ratio:.1f}x "
                f"more training time. Whether this tradeoff is worthwhile depends on the "
                f"clinical cost of false negatives vs computational resources available."
            )
        elif classification == "TRADEOFF":
            return (
                f"On this evaluated dataset, {qname} showed a sensitivity advantage "
                f"({recall_delta:+.1%} recall) over {bc.model_name}, "
                f"with comparable ROC-AUC (delta: {auc_delta:+.3f}). "
                f"However, this came at {time_ratio:.1f}x the training time. "
                f"This is a tradeoff: higher recall with substantially greater compute cost."
            )
        elif classification == "PERFORMANCE_PARITY":
            return (
                f"On this evaluated dataset, {qname} and {bc.model_name} performed comparably "
                f"(recall delta: {recall_delta:+.1%}, AUC delta: {auc_delta:+.3f}). "
                f"{qname} required {time_ratio:.1f}x more training time for equivalent results. "
                f"Classical approach is more computationally efficient for this dataset."
            )
        else:  # CLASSICAL_ADVANTAGE
            return (
                f"On this evaluated dataset, {bc.model_name} outperformed {qname} "
                f"(recall delta: {recall_delta:+.1%}, AUC delta: {auc_delta:+.3f}). "
                f"Classical approach achieved better results with {time_ratio:.1f}x less "
                f"training time. This is a clear classical advantage on this dataset."
            )

    def _result_summary(self, result: ModelResult) -> dict:
        """Compact result dict for recommendation output."""
        summary = {
            "model_name":             result.model_name,
            "model_type":             result.model_type,
            "status":                 result.status,
            "metrics": {
                "accuracy":    round(result.accuracy,    4),
                "recall":      round(result.recall,      4),
                "specificity": round(result.specificity, 4),
                "f1_score":    round(result.f1_score,    4),
                "roc_auc":     round(result.roc_auc,     4),
                "pr_auc":      round(result.pr_auc,      4),
            },
            "training_time_seconds": round(result.training_time_seconds, 3),
        }
        if result.model_type == "QUANTUM":
            summary["quantum_metrics"] = {
                "qubits":                   result.qubits,
                "circuit_depth":            result.circuit_depth,
                "gate_count":               result.gate_count,
                "two_qubit_gates":          result.two_qubit_gates,
                "shots":                    result.shots,
                "total_circuit_executions": result.total_circuit_executions,
                "backend_type":             result.backend_type,
                "encoding_method":          result.encoding_method,
            }
        return summary

    def _inconclusive(self, reason: str) -> dict:
        return {
            "benchmark_id":   f"BENCH-{uuid.uuid4().hex[:6].upper()}",
            "classification": "INCONCLUSIVE",
            "observations":   [reason],
            "recommendation_text": reason,
            "classical_best": None,
            "quantum_best":   None,
            "performance_differences": None,
            "resource_comparison": None,
        }
