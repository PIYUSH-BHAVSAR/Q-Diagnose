"""
backend/models/classical/random_forest.py
Owner: Piyush
Phase: 7

RandomForestModel — tree ensemble for binary classification.
From phase7.md §9: "Useful for nonlinear relationships + mixed feature types."
From guide_piyush.md §9 Common Failures: Use n_estimators=100, NOT n_estimators=1.
From phase7.md §4: class_weight='balanced' mandatory.

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
from sklearn.ensemble import RandomForestClassifier

from backend.benchmarking.metrics import MetricsCalculator
from backend.models.result import ModelResult


class RandomForestModel:
    """
    Random Forest classifier wrapper.

    Follows the standard model interface:
        result = model.fit(X_train, y_train, X_test, y_test)

    Key config:
        - n_estimators=100 — guide says don't use 1
        - class_weight='balanced' — mandatory (phase7.md §4)
        - random_state=42 — reproducibility
        - n_jobs=-1 — use all cores for training speed
    """

    MODEL_ID = "C-002"
    MODEL_NAME = "RandomForest"

    def __init__(
        self,
        random_state: int = 42,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        class_weight: str = "balanced",
        n_jobs: int = -1,
    ) -> None:
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.class_weight = class_weight
        self.n_jobs = n_jobs

        self._model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            class_weight=class_weight,
            random_state=random_state,
            n_jobs=n_jobs,
        )

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        experiment_id: Optional[str] = None,
        representation_id: str = "REP-000003",
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
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "min_samples_split": self.min_samples_split,
                "class_weight": self.class_weight,
                "random_state": self.random_state,
            },
            random_seed=self.random_state,
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @property
    def sklearn_model(self):
        return self._model

    @property
    def feature_importances_(self) -> Optional[np.ndarray]:
        """Feature importances — available for Radha's explainability engine."""
        return getattr(self._model, "feature_importances_", None)
