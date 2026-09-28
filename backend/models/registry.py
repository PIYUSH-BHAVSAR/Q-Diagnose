"""
backend/models/registry.py
Owner: Piyush
Phase: 7 + 8

ModelRegistry — controlled catalogue of all available models (classical + quantum).
From phase7.md §8: "Maintain a controlled registry rather than hard-coding one algorithm."
From phase8.md §7: "Quantum model registry — not just VQC."

Usage:
    registry = ModelRegistry()
    classical = registry.get_classical_models(random_state=42)
    quantum   = registry.get_quantum_models()
"""

from __future__ import annotations

from typing import Dict, List, Optional


# ── Classical model metadata ──────────────────────────────────────────────────

CLASSICAL_REGISTRY: List[Dict] = [
    {
        "model_id":      "C-001",
        "model_name":    "LogisticRegression",
        "display_name":  "Logistic Regression",
        "supported_tasks": ["BINARY_CLASSIFICATION"],
        "strengths":     "Linear relationships, interpretable coefficients",
        "default_hyperparameters": {
            "max_iter": 1000,
            "class_weight": "balanced",
            "C": 1.0,
            "solver": "lbfgs",
        },
        "resource_class": "LOW",       # fast, low memory
    },
    {
        "model_id":      "C-002",
        "model_name":    "RandomForest",
        "display_name":  "Random Forest",
        "supported_tasks": ["BINARY_CLASSIFICATION"],
        "strengths":     "Nonlinear relationships, mixed feature types, feature importance",
        "default_hyperparameters": {
            "n_estimators": 100,
            "max_depth": None,
            "class_weight": "balanced",
        },
        "resource_class": "MEDIUM",
    },
    {
        "model_id":      "C-003",
        "model_name":    "SVM",
        "display_name":  "Support Vector Machine",
        "supported_tasks": ["BINARY_CLASSIFICATION"],
        "strengths":     "High-dimensional feature spaces, smaller datasets",
        "default_hyperparameters": {
            "kernel": "rbf",
            "C": 1.0,
            "gamma": "scale",
            "class_weight": "balanced",
        },
        "resource_class": "MEDIUM",
    },
]

# ── Quantum model metadata ────────────────────────────────────────────────────

QUANTUM_REGISTRY: List[Dict] = [
    {
        "model_id":      "Q-001",
        "model_name":    "VQC",
        "display_name":  "Variational Quantum Classifier",
        "supported_tasks": ["BINARY_CLASSIFICATION"],
        "framework":     "PennyLane",
        "backend":       "default.qubit",
        "encoding":      "angle_encoding",
        "default_hyperparameters": {
            "n_qubits":     8,
            "n_layers":     2,
            "shots":        1024,
            "epochs":       100,
            "batch_size":   32,
            "learning_rate": 0.01,
        },
        "resource_class": "HIGH",
        "max_qubits":    8,
    },
    {
        "model_id":      "Q-002",
        "model_name":    "QuantumSVM",
        "display_name":  "Quantum Support Vector Machine",
        "supported_tasks": ["BINARY_CLASSIFICATION"],
        "framework":     "PennyLane",
        "backend":       "default.qubit",
        "encoding":      "angle_encoding_kernel",
        "default_hyperparameters": {
            "n_qubits":     8,
            "C":            1.0,
        },
        "resource_class": "HIGH",
        "max_qubits":    8,
    },
]


class ModelRegistry:
    """
    Central registry for all available models.

    Provides filtered access based on task type, resource class, etc.
    """

    def __init__(self) -> None:
        self._classical = CLASSICAL_REGISTRY
        self._quantum = QUANTUM_REGISTRY

    # ── Classical ─────────────────────────────────────────────────────────────

    def get_classical_models(
        self,
        random_state: int = 42,
        task: str = "BINARY_CLASSIFICATION",
    ):
        """
        Instantiate all classical models for a given task.
        Returns dict: {model_name: model_instance}
        """
        from backend.models.classical.logistic_regression import LogisticRegressionModel
        from backend.models.classical.svm import SVMModel
        from backend.models.classical.random_forest import RandomForestModel

        models = {}
        for meta in self._classical:
            if task not in meta["supported_tasks"]:
                continue
            name = meta["model_name"]
            if name == "LogisticRegression":
                models[name] = LogisticRegressionModel(random_state=random_state)
            elif name == "RandomForest":
                models[name] = RandomForestModel(random_state=random_state)
            elif name == "SVM":
                models[name] = SVMModel(random_state=random_state)
        return models

    # ── Quantum ──────────────────────────────────────────────────────────────

    def get_quantum_models(
        self,
        n_qubits: int = 8,
        n_layers: int = 2,
        shots: int = 1024,
        epochs: int = 100,
        random_state: int = 42,
        task: str = "BINARY_CLASSIFICATION",
        dev_mode: bool = False,
    ):
        """
        Instantiate quantum models.
        dev_mode=True uses epochs=10, n_qubits=4 for fast testing.
        """
        from backend.models.quantum.vqc import VQCModel
        from backend.models.quantum.qsvm import QuantumSVMModel

        if dev_mode:
            n_qubits = min(n_qubits, 4)
            epochs = 10
            shots = 256

        models = {}
        for meta in self._quantum:
            if task not in meta["supported_tasks"]:
                continue
            name = meta["model_name"]
            if name == "VQC":
                models[name] = VQCModel(
                    n_qubits=n_qubits,
                    n_layers=n_layers,
                    shots=shots,
                    epochs=epochs,
                    random_state=random_state,
                )
            elif name == "QuantumSVM":
                models[name] = QuantumSVMModel(
                    n_qubits=n_qubits,
                    random_state=random_state,
                )
        return models

    def list_classical(self) -> List[Dict]:
        return self._classical

    def list_quantum(self) -> List[Dict]:
        return self._quantum

    def get_metadata(self, model_name: str) -> Optional[Dict]:
        """Look up registry metadata by model name."""
        for m in self._classical + self._quantum:
            if m["model_name"] == model_name:
                return m
        return None
