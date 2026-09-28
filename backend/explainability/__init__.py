"""Explainability package for the Q-Diagnose platform.

Exports
-------
ClassicalExplainer
    SHAP-based explainer for classical scikit-learn models
    (RandomForest → TreeExplainer, LogisticRegression → LinearExplainer,
     SVM/other → KernelExplainer with background capped at 50 samples).

QuantumExplainer
    Perturbation-based explainer for the fitted VQCModel.
    Does not retrain or modify the model.
"""

from backend.explainability.classical import ClassicalExplainer
from backend.explainability.quantum import QuantumExplainer

__all__ = [
    "ClassicalExplainer",
    "QuantumExplainer",
]
