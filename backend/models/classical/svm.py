"""
backend/models/classical/svm.py
Owner: Piyush
Phase: 7

SVMModel — support vector machine for binary classification.
From phase7.md §9: "Potentially useful for high-dimensional feature spaces + smaller datasets."
From phase7.md §4: class_weight='balanced' mandatory.
Uses SVC(probability=True) to produce calibrated probability scores for ROC/PR curves.

Interface: fit(X_train, y_train, X_test, y_test) → ModelResult
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
import psutil
from sklearn.svm import SVC

from backend.benchmarking.metrics import MetricsCalculator
from backend.models.result import ModelResult


class SVMModel:
    """
    SVM classifier wrapper.

    Follows the standard model interface:
        result = model.fit(X_train, y_train, X_test, y_test)

    Key config:
        - kernel='rbf' — works well on scaled tabular features
        - class_weight='balanced' — mandatory from phase7.md §4
        - probability=True — required for predict_proba() → ROC/PR curves
        - random_state=42 — reproducibility (used by probability calibration)
    """

    MODEL_ID = "C-003"
    MODEL_NAME = "SVM"

    def __init__(
        self,
        random_state: int = 42,
        class_weight: str = "balanced",
        kernel: str = "rbf",
        C: float = 1.0,
        gamma: str = "scale",
    ) -> None:
        self.random_state = random_state
        self.class_weight = class_weight
        self.kernel = kernel
        self.C = C
        self.gamma = gamma

        self._model = SVC(
            kernel=kernel,
            C=C,
            gamma=gamma,
            class_weight=class_weight,
            probability=True,      # needed for predict_proba → ROC-AUC
            random_state=random_state,
        )

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        experiment_id: Optional[str] = None,
        representation_id: str = "REP-000002",
        feature_names: Optional[List[str]] = None,
    ) -> ModelResult:
        """
        Train on X_train/y_train, evaluate on X_test/y_test.

        phase10.md §12 — NO data leakage.
        """
        exp_id = experiment_id or f"EXP-C-{uuid.uuid4().hex[:6].upper()}"
        proc = psutil.Process(os.getpid())

        mem_before = proc.memory_info().rss / (1024 * 1024)

        # ── Training ──────────────────────────────────────────────────────────
        t_train_start = time.perf_counter()
        try:
            self._model.fit(X_train, y_train)
        except Exception as exc:
            return ModelResult.failed(exp_id, "CLASSICAL", self.MODEL_NAME, str(exc), self.random_state)
        training_time = time.perf_counter() - t_train_start

        mem_after = proc.memory_info().rss / (1024 * 1024)
        memory_peak_mb = max(mem_after - mem_before, 0.0)

        # ── Inference ─────────────────────────────────────────────────────────
        t_infer_start = time.perf_counter()
        y_pred_test = self._model.predict(X_test)
        inference_time = time.perf_counter() - t_infer_start

        y_scores_test = self._model.predict_proba(X_test)[:, 1]
        y_pred_train = self._model.predict(X_train)

        # ── Metrics ───────────────────────────────────────────────────────────
        metrics = MetricsCalculator.compute(y_test, y_pred_test, y_scores_test)

        return ModelResult(
            experiment_id=exp_id,
            model_type="CLASSICAL",
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
            memory_peak_mb=memory_peak_mb,
            hyperparameters={
                "kernel": self.kernel,
                "C": self.C,
                "gamma": self.gamma,
                "class_weight": self.class_weight,
                "probability": True,
                "random_state": self.random_state,
            },
            random_seed=self.random_state,
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @property
    def sklearn_model(self):
        return self._model
