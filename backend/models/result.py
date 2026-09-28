"""
backend/models/result.py
Owner: Piyush
Purpose: Unified ModelResult dataclass — returned by EVERY model (classical + quantum).
         Consumed by benchmarking, API routes, and Radha's explainability engine.

Every field is mandatory except quantum-specific ones (None for classical).
Call to_dict() for JSON-serialisable output — strips all numpy arrays.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np


@dataclass
class ModelResult:
    """
    Unified result object produced by every classical and quantum model.

    Usage:
        result = LogisticRegressionModel().fit(X_train, y_train, X_test, y_test)
        result.to_dict()   # fully JSON-serialisable
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    experiment_id: str
    model_type: str           # "CLASSICAL" or "QUANTUM"
    model_name: str           # "LogisticRegression", "SVM", "RandomForest", "VQC"
    representation_id: str    # "REP-000001" or "QREP-000001"
    status: str               # "COMPLETED", "FAILED", "TIMEOUT", "OUT_OF_MEMORY"

    # ── Predictions (kept as numpy for Phase 11 analysis) ────────────────────
    predictions_train: np.ndarray   # shape (n_train,)
    predictions_test: np.ndarray    # shape (n_test,)
    scores_test: np.ndarray         # probabilities / PauliZ-mapped scores for ROC

    # ── Core metrics ─────────────────────────────────────────────────────────
    accuracy: float
    precision: float
    recall: float
    specificity: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    confusion_matrix: List[List[int]]   # [[TN, FP], [FN, TP]]

    # ── Resource usage ───────────────────────────────────────────────────────
    training_time_seconds: float
    inference_time_seconds: float
    memory_peak_mb: float
    model_size_mb: float = 0.0

    # ── Quantum-specific (None for classical) ─────────────────────────────────
    qubits: Optional[int] = None
    circuit_depth: Optional[int] = None
    gate_count: Optional[int] = None
    two_qubit_gates: Optional[int] = None
    shots: Optional[int] = None
    total_circuit_executions: Optional[int] = None
    backend_type: Optional[str] = None
    encoding_method: Optional[str] = None

    # ── Training history ─────────────────────────────────────────────────────
    training_history: Dict = field(default_factory=dict)

    # ── Reproducibility ──────────────────────────────────────────────────────
    hyperparameters: Dict = field(default_factory=dict)
    random_seed: int = 42
    execution_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error_message: Optional[str] = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def metrics_dict(self) -> dict:
        """Return only the metric fields as a plain dict."""
        return {
            "accuracy":    round(self.accuracy, 6),
            "precision":   round(self.precision, 6),
            "recall":      round(self.recall, 6),
            "specificity": round(self.specificity, 6),
            "f1_score":    round(self.f1_score, 6),
            "roc_auc":     round(self.roc_auc, 6),
            "pr_auc":      round(self.pr_auc, 6),
            "confusion_matrix": self.confusion_matrix,
        }

    def to_dict(self) -> dict:
        """
        Fully JSON-serialisable representation.
        Strips all numpy arrays — converts to Python lists/floats.
        Shape matches contracts/model_result.json.
        """
        d: dict = {
            "experiment_id":      self.experiment_id,
            "model_type":         self.model_type,
            "model_name":         self.model_name,
            "representation_id":  self.representation_id,
            "status":             self.status,
            "metrics":            self.metrics_dict(),
            "resource_usage": {
                "training_time_seconds":  round(self.training_time_seconds, 4),
                "inference_time_seconds": round(self.inference_time_seconds, 6),
                "memory_peak_mb":         round(self.memory_peak_mb, 2),
                "model_size_mb":          round(self.model_size_mb, 4),
            },
            "training_history":   self.training_history,
            "hyperparameters":    self.hyperparameters,
            "random_seed":        self.random_seed,
            "execution_timestamp": self.execution_timestamp,
            "error_message":      self.error_message,
        }

        if self.model_type == "QUANTUM":
            d["quantum_metrics"] = {
                "qubits":                   self.qubits,
                "circuit_depth":            self.circuit_depth,
                "gate_count":               self.gate_count,
                "two_qubit_gates":          self.two_qubit_gates,
                "shots":                    self.shots,
                "total_circuit_executions": self.total_circuit_executions,
                "backend_type":             self.backend_type,
                "encoding_method":          self.encoding_method,
            }
        return d

    @classmethod
    def failed(
        cls,
        experiment_id: str,
        model_type: str,
        model_name: str,
        error: str,
        random_seed: int = 42,
    ) -> "ModelResult":
        """Factory for failed results — avoids boilerplate in error handlers."""
        empty = np.array([], dtype=int)
        return cls(
            experiment_id=experiment_id,
            model_type=model_type,
            model_name=model_name,
            representation_id="REP-FAILED",
            status="FAILED",
            predictions_train=empty,
            predictions_test=empty,
            scores_test=empty,
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            specificity=0.0,
            f1_score=0.0,
            roc_auc=0.0,
            pr_auc=0.0,
            confusion_matrix=[[0, 0], [0, 0]],
            training_time_seconds=0.0,
            inference_time_seconds=0.0,
            memory_peak_mb=0.0,
            random_seed=random_seed,
            error_message=error,
        )
