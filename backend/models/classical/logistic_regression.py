"""
backend/models/classical/logistic_regression.py
Owner: Piyush
Phase: 7

LogisticRegressionModel — linear baseline for binary classification.
From phase7.md §9: "Good baseline for linear relationships + interpretable coefficients."
From phase7.md §4: class_weight='balanced' mandatory — fair comparison rule.

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
from sklearn.linear_model import LogisticRegression

from backend.benchmarking.metrics import MetricsCalculator
from backend.models.result import ModelResult


class LogisticRegressionModel:
    """
    Logistic Regression classifier wrapper.

    Follows the standard model interface:
        result = model.fit(X_train, y_train, X_test, y_test)

    Key config (phase7.md §4 + guide_piyush.md §6):
        - class_weight='balanced' — compensates for class imbalance
        - max_iter=1000 — enough for convergence on scaled data
        - random_state=42 — reproducibility
    """

    MODEL_ID = "C-001"
    MODEL_NAME = "LogisticRegression"

    def __init__(
        self,
        random_state: int = 42,
        max_iter: int = 1000,
        class_weight: str = "balanced",
        C: float = 1.0,
        solver: str = "lbfgs",
    ) -> None:
        self.random_state = random_state
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.C = C
        self.solver = solver

        self._model = LogisticRegression(
            random_state=random_state,
            max_iter=max_iter,
            class_weight=class_weight,
            C=C,
            solver=solver,
        )

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        experiment_id: Optional[str] = None,
        representation_id: str = "REP-000001",
        feature_names: Optional[List[str]] = None,
    ) -> ModelResult:
        """
        Train on X_train/y_train, evaluate on X_test/y_test.

        phase10.md §12 — NO data leakage:
            fit() is called ONLY on training data.
            X_test is only touched at inference time.
        """
        exp_id = experiment_id or f"EXP-C-{uuid.uuid4().hex[:6].upper()}"
        proc = psutil.Process(os.getpid())

        # ── Memory before training ────────────────────────────────────────────
        mem_before = proc.memory_info().rss / (1024 * 1024)

        # ── Training (phase10.md §16) ─────────────────────────────────────────
        t_train_start = time.perf_counter()
        try:
            self._model.fit(X_train, y_train)
        except Exception as exc:
            return ModelResult.failed(exp_id, "CLASSICAL", self.MODEL_NAME, str(exc), self.random_state)
        training_time = time.perf_counter() - t_train_start

        mem_after = proc.memory_info().rss / (1024 * 1024)
        memory_peak_mb = max(mem_after - mem_before, 0.0)

        # ── Inference (phase10.md §14) ────────────────────────────────────────
        t_infer_start = time.perf_counter()
        y_pred_test = self._model.predict(X_test)
        inference_time = time.perf_counter() - t_infer_start

        # Probability scores for ROC / PR curves
        y_scores_test = self._model.predict_proba(X_test)[:, 1]
        y_pred_train = self._model.predict(X_train)
        y_scores_train = self._model.predict_proba(X_train)[:, 1]

        # ── Metrics (phase7.md §16, phase11.md §9) ───────────────────────────
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
            # unpack all 8 metric fields
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            specificity=metrics["specificity"],
            f1_score=metrics["f1_score"],
            roc_auc=metrics["roc_auc"],
            pr_auc=metrics["pr_auc"],
            confusion_matrix=metrics["confusion_matrix"],
            # resources
            training_time_seconds=training_time,
            inference_time_seconds=inference_time,
            memory_peak_mb=memory_peak_mb,
            # reproducibility
            hyperparameters={
                "max_iter": self.max_iter,
                "class_weight": self.class_weight,
                "C": self.C,
                "solver": self.solver,
                "random_state": self.random_state,
            },
            random_seed=self.random_state,
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @property
    def sklearn_model(self):
        """Expose underlying sklearn model (for Radha's explainability engine)."""
        return self._model
