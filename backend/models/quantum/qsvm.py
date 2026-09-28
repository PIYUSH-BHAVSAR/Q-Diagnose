"""
backend/models/quantum/qsvm.py
Owner: Piyush
Phase: 8 — Quantum Models

Quantum Support Vector Machine (QSVM) using Quantum Kernel Estimation (QKE).
From Problem Statement Deliverable 3: "Quantum SVM, Variational Quantum Classifier..."

Mechanism:
  1. Angle Encoding: maps classical PCA feature vectors x_i, x_j to quantum states |ψ(x_i)⟩, |ψ(x_j)⟩
  2. Quantum Kernel Matrix K_ij = |⟨ψ(x_j)|ψ(x_i)⟩|^2 calculated via PennyLane circuit
  3. Classical SVC with kernel='precomputed' fitted on the quantum inner-product matrix K
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import psutil
from sklearn.svm import SVC

from backend.benchmarking.metrics import MetricsCalculator
from backend.models.quantum.backend import LocalSimulatorBackend, QuantumBackend
from backend.models.quantum.circuit import circuit_depth, count_gates
from backend.models.quantum.encoding import AngleEncoder
from backend.models.result import ModelResult


class QuantumSVMModel:
    """
    Quantum Support Vector Machine via Quantum Kernel Matrix Estimation.
    """

    MODEL_ID = "Q-002"
    MODEL_NAME = "QuantumSVM"

    def __init__(
        self,
        n_qubits: int = 8,
        C: float = 1.0,
        random_state: int = 42,
        backend: Optional[QuantumBackend] = None,
    ) -> None:
        self.n_qubits = n_qubits
        self.C = C
        self.random_state = random_state
        self.backend = backend or LocalSimulatorBackend()
        self.encoder = AngleEncoder(n_qubits)
        self._circuit_executions = 0
        self._svc = SVC(C=self.C, kernel="precomputed", probability=True, random_state=random_state)
        self._X_train_enc: Optional[np.ndarray] = None

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        experiment_id: Optional[str] = None,
        representation_id: str = "QREP-QSVM",
    ) -> ModelResult:
        exp_id = experiment_id or f"EXP-QSVM-{np.random.randint(1000,9999)}"
        np.random.seed(self.random_state)
        self._circuit_executions = 0

        proc = psutil.Process(os.getpid())
        mem_before = proc.memory_info().rss / (1024 * 1024)
        t_start = time.perf_counter()

        try:
            import pennylane as qml

            # Scale features to [-1, 1] for angle encoding
            X_train_enc = self.encoder.scale_features(X_train)
            X_test_enc  = self.encoder.scale_features(X_test)
            self._X_train_enc = X_train_enc

            dev = self.backend.get_device(self.n_qubits)

            # Build PennyLane QNode for kernel inner product |<ψ(x_j)|ψ(x_i)>|^2
            @qml.qnode(dev)
            def kernel_circuit(x1, x2):
                self.encoder.encode(x1)
                qml.adjoint(self.encoder.encode)(x2)
                return qml.probs(wires=range(self.n_qubits))

            # Compute Gram matrix K_train (N_train x N_train)
            n_train = len(X_train_enc)
            K_train = np.eye(n_train)
            for i in range(n_train):
                for j in range(i + 1, n_train):
                    probs = kernel_circuit(X_train_enc[i], X_train_enc[j])
                    self._circuit_executions += 1
                    overlap = float(probs[0])  # probability of |000...0> state
                    K_train[i, j] = overlap
                    K_train[j, i] = overlap

            # Fit precomputed kernel SVC
            self._svc.fit(K_train, y_train)
            t_train = time.perf_counter() - t_start

            # Inference on test set
            t_infer_start = time.perf_counter()
            n_test = len(X_test_enc)
            K_test = np.zeros((n_test, n_train))
            for i in range(n_test):
                for j in range(n_train):
                    probs = kernel_circuit(X_test_enc[i], X_train_enc[j])
                    self._circuit_executions += 1
                    K_test[i, j] = float(probs[0])

            y_pred_test = self._svc.predict(K_test)
            y_scores_test = self._svc.predict_proba(K_test)[:, 1] if hasattr(self._svc, "predict_proba") else y_pred_test.astype(float)
            t_infer = time.perf_counter() - t_infer_start

            # Predictions on training set for generalization gap
            y_pred_train = self._svc.predict(K_train)

            mem_after = proc.memory_info().rss / (1024 * 1024)
            metrics = MetricsCalculator.compute(y_test, y_pred_test, y_scores_test)

            return ModelResult(
                experiment_id=exp_id,
                model_type="QUANTUM",
                model_name=self.MODEL_NAME,
                representation_id=representation_id,
                status="COMPLETED",
                predictions_train=y_pred_train,
                predictions_test=y_pred_test,
                scores_test=y_scores_test,
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                specificity=metrics["specificity"],
                f1_score=metrics["f1_score"],
                roc_auc=metrics["roc_auc"],
                pr_auc=metrics["pr_auc"],
                confusion_matrix=metrics["confusion_matrix"],
                training_time_seconds=t_train,
                inference_time_seconds=t_infer,
                memory_peak_mb=max(mem_after - mem_before, 0.0),
                qubits=self.n_qubits,
                circuit_depth=2,
                gate_count=self.n_qubits * 2,
                two_qubit_gates=0,
                shots=None,
                total_circuit_executions=self._circuit_executions,
                backend_type=self.backend.backend_type,
                encoding_method="angle_encoding_kernel",
                training_history={"kernel": "quantum_kernel_estimation"},
                hyperparameters={"C": self.C, "n_qubits": self.n_qubits},
                random_seed=self.random_state,
                execution_timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as exc:
            return ModelResult.failed(
                exp_id, "QUANTUM", self.MODEL_NAME, str(exc), self.random_state
            )
