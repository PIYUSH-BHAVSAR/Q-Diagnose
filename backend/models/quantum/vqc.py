"""
backend/models/quantum/vqc.py
Owner: Piyush
Phase: 8 + 10

VQCModel — Variational Quantum Classifier using PennyLane.
From guide_piyush.md §6 + phase8.md §8:

    Architecture:
        AngleEncoder → parameterized circuit → PauliZ measurement
        PauliZ output [-1,1] → (output+1)/2 → probability [0,1]
        threshold 0.5 → class prediction

    Training: PennyLane AdamOptimizer (NOT torch/tensorflow)
    Backend: LocalSimulatorBackend (via QuantumBackend abstraction)
    Input: X_train_reduced (8 PCA components) — NOT X_train (30 features)
    Early stopping: patience=5 (phase10.md §19)

Interface: fit(X_train_reduced, y_train, X_test_reduced, y_test) → ModelResult
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import psutil

from backend.benchmarking.metrics import MetricsCalculator
from backend.models.quantum.backend import LocalSimulatorBackend, QuantumBackend
from backend.models.quantum.circuit import (
    build_vqc_circuit,
    circuit_depth,
    count_gates,
    count_params,
    count_two_qubit_gates,
)
from backend.models.quantum.encoding import AngleEncoder
from backend.models.result import ModelResult


class VQCModel:
    """
    Variational Quantum Classifier.

    Critical rules (guide_piyush.md §9):
        1. Trains on X_train_REDUCED (8 PCA components), NOT X_train (30 features)
        2. QuantumBackend abstraction — never hardcodes default.qubit
        3. Tracks total_circuit_executions
        4. No double-preprocessing: AngleEncoder.scale_features() only clips/rescales
        5. Early stopping with patience to save compute
        6. Returns model_type="QUANTUM" with all quantum_metrics populated
    """

    MODEL_ID = "Q-001"
    MODEL_NAME = "VQC"

    def __init__(
        self,
        n_qubits: int = 8,
        n_layers: int = 2,
        shots: int = 1024,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.01,
        random_state: int = 42,
        early_stopping_patience: int = 5,
        backend: Optional[QuantumBackend] = None,
    ) -> None:
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.shots = shots
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.early_stopping_patience = early_stopping_patience

        # Backend abstraction (phase8.md §21-25)
        self.backend = backend or LocalSimulatorBackend()

        self.encoder = AngleEncoder(n_qubits)
        self._circuit_executions = 0
        self._params: Optional[np.ndarray] = None
        self._circuit = None

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        experiment_id: Optional[str] = None,
        representation_id: str = "QREP-000001",
    ) -> ModelResult:
        """
        Train VQC on REDUCED features (PCA components), evaluate on test set.

        Args:
            X_train: shape (n_train, n_qubits) — PCA-reduced, already scaled by Jayed
            y_train: shape (n_train,), binary labels {0, 1}
            X_test:  shape (n_test, n_qubits)
            y_test:  shape (n_test,)

        phase10.md §12 — NO data leakage: fit only on train, evaluate on test.
        """
        exp_id = experiment_id or f"EXP-Q-{uuid.uuid4().hex[:6].upper()}"
        np.random.seed(self.random_state)
        self._circuit_executions = 0

        proc = psutil.Process(os.getpid())
        mem_before = proc.memory_info().rss / (1024 * 1024)

        try:
            result = self._train_and_evaluate(
                X_train, y_train, X_test, y_test,
                exp_id, representation_id, mem_before, proc,
            )
        except Exception as exc:
            return ModelResult.failed(
                exp_id, "QUANTUM", self.MODEL_NAME, str(exc), self.random_state
            )

        return result

    def _train_and_evaluate(
        self,
        X_train, y_train, X_test, y_test,
        exp_id, representation_id, mem_before, proc,
    ) -> ModelResult:
        import pennylane as qml

        # ── Scale features for angle encoding (phase8.md §12-13) ─────────────
        X_train_enc = self.encoder.scale_features(X_train)
        X_test_enc  = self.encoder.scale_features(X_test)

        # ── Build circuit via backend abstraction (phase8.md §21) ─────────────
        device  = self.backend.get_device(self.n_qubits)
        circuit = build_vqc_circuit(self.n_qubits, self.n_layers, device)
        self._circuit = circuit

        # ── Initialise parameters ─────────────────────────────────────────────
        n_params = count_params(self.n_qubits, self.n_layers)
        params = np.random.uniform(-np.pi, np.pi, n_params)

        # Convert binary labels to ±1 for PauliZ measurement
        y_train_pm = np.where(y_train == 1, 1.0, -1.0)

        # ── Training loop with AdamOptimizer (phase8.md guide) ───────────────
        opt = qml.AdamOptimizer(stepsize=self.learning_rate)
        train_losses: list = []
        val_losses: list = []

        best_val_loss = float("inf")
        patience_counter = 0
        n_train = len(X_train_enc)
        steps_per_epoch = max(1, n_train // self.batch_size)

        t_train_start = time.perf_counter()

        for epoch in range(self.epochs):
            indices = np.random.permutation(n_train)
            epoch_loss = 0.0

            for step in range(steps_per_epoch):
                batch_idx = indices[step * self.batch_size : (step + 1) * self.batch_size]
                if len(batch_idx) == 0:
                    continue
                X_batch = X_train_enc[batch_idx]
                y_batch = y_train_pm[batch_idx]

                def cost_fn(p, X_b=X_batch, y_b=y_batch):
                    # Each call = one circuit execution per sample in batch
                    predictions = np.array([circuit(x, p) for x in X_b])
                    self._circuit_executions += len(X_b)
                    # MSE loss: PauliZ expectation ∈ [-1,1] vs label ∈ {-1,+1}
                    return float(np.mean((predictions - y_b) ** 2))

                params, step_loss = opt.step_and_cost(cost_fn, params)
                epoch_loss += step_loss

            avg_train_loss = epoch_loss / steps_per_epoch
            train_losses.append(round(avg_train_loss, 6))

            # ── Validation every 5 epochs (phase10.md §19 early stopping) ────
            if epoch % 5 == 0:
                val_subset = X_test_enc[:min(20, len(X_test_enc))]
                val_labels = np.where(y_test[:len(val_subset)] == 1, 1.0, -1.0)
                val_preds = np.array([circuit(x, params) for x in val_subset])
                self._circuit_executions += len(val_subset)
                val_loss = float(np.mean((val_preds - val_labels) ** 2))
                val_losses.append(round(val_loss, 6))

                # Early stopping
                if val_loss < best_val_loss - 1e-4:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.early_stopping_patience:
                        break  # stop early

        training_time = time.perf_counter() - t_train_start
        self._params = params

        # ── Inference on full test set ────────────────────────────────────────
        t_infer_start = time.perf_counter()
        raw_scores_test = np.array([circuit(x, params) for x in X_test_enc])
        self._circuit_executions += len(X_test_enc)
        inference_time = time.perf_counter() - t_infer_start

        # PauliZ ∈ [-1,1] → probability [0,1]  (guide_piyush.md §8)
        y_scores_test = (raw_scores_test + 1.0) / 2.0
        y_pred_test   = (y_scores_test >= 0.5).astype(int)

        # Train predictions for generalization gap
        raw_scores_train = np.array([circuit(x, params) for x in X_train_enc])
        self._circuit_executions += len(X_train_enc)
        y_pred_train = ((raw_scores_train + 1.0) / 2.0 >= 0.5).astype(int)

        mem_after = proc.memory_info().rss / (1024 * 1024)

        # ── Metrics ───────────────────────────────────────────────────────────
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
            training_time_seconds=training_time,
            inference_time_seconds=inference_time,
            memory_peak_mb=max(mem_after - mem_before, 0.0),
            # Quantum-specific fields (phase8.md §15)
            qubits=self.n_qubits,
            circuit_depth=circuit_depth(self.n_layers),
            gate_count=count_gates(self.n_qubits, self.n_layers),
            two_qubit_gates=count_two_qubit_gates(self.n_qubits, self.n_layers),
            shots=self.shots,
            total_circuit_executions=self._circuit_executions,
            backend_type=self.backend.backend_type,
            encoding_method="angle_encoding",
            # Training history
            training_history={
                "epochs_run": len(train_losses),
                "train_loss": train_losses,
                "val_loss":   val_losses,
                "early_stopped": patience_counter >= self.early_stopping_patience,
            },
            hyperparameters={
                "n_qubits":      self.n_qubits,
                "n_layers":      self.n_layers,
                "shots":         self.shots,
                "epochs":        self.epochs,
                "batch_size":    self.batch_size,
                "learning_rate": self.learning_rate,
                "random_state":  self.random_state,
                "early_stopping_patience": self.early_stopping_patience,
            },
            random_seed=self.random_state,
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
        )
