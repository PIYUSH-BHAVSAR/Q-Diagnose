"""
backend/benchmarking/metrics.py
Owner: Piyush
Phase: 7 + 11

MetricsCalculator — computes all 7 medical-grade metrics + confusion matrix.
Everything else depends on this file — build and test it first.

Key rule from phase7.md §18 + phase11.md §10:
    Sensitivity/Recall is the primary metric for disease detection.
    Specificity = TN / (TN + FP)  ← computed manually, no sklearn built-in.

Usage:
    metrics = MetricsCalculator.compute(y_true, y_pred, y_scores)
    # metrics["recall"], metrics["specificity"], metrics["confusion_matrix"]
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix,
)


class MetricsCalculator:
    """
    All metrics required by the Q-Diagnose platform.

    Static methods only — no state, fully reusable.
    """

    @staticmethod
    def compute(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_scores: np.ndarray,
    ) -> dict:
        """
        Compute full metric suite for binary classification.

        Args:
            y_true:   Ground-truth labels, shape (n,), values {0, 1}
            y_pred:   Hard predictions, shape (n,), values {0, 1}
            y_scores: Continuous scores / probabilities, shape (n,).
                      For classical: predict_proba()[:, 1]
                      For VQC: PauliZ expectation mapped to [0, 1]

        Returns:
            dict with keys:
                accuracy, precision, recall, specificity, f1_score,
                roc_auc, pr_auc, confusion_matrix (as [[TN,FP],[FN,TP]])
        """
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        y_scores = np.asarray(y_scores).ravel()

        # Confusion matrix: sklearn returns [[TN, FP], [FN, TP]] for binary
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
        else:
            # Edge case: only one class predicted
            tn, fp, fn, tp = 0, 0, 0, 0

        # Specificity = TN / (TN + FP)  — manual, phase7.md §18
        specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        # ROC-AUC: requires both classes present in y_true
        try:
            roc_auc = float(roc_auc_score(y_true, y_scores))
        except ValueError:
            roc_auc = 0.0

        # PR-AUC (average precision): important for imbalanced datasets (phase11.md §14)
        try:
            pr_auc = float(average_precision_score(y_true, y_scores))
        except ValueError:
            pr_auc = 0.0

        return {
            "accuracy":    float(accuracy_score(y_true, y_pred)),
            "precision":   float(precision_score(y_true, y_pred, zero_division=0)),
            "recall":      float(recall_score(y_true, y_pred, zero_division=0)),
            "specificity": specificity,
            "f1_score":    float(f1_score(y_true, y_pred, zero_division=0)),
            "roc_auc":     roc_auc,
            "pr_auc":      pr_auc,
            "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        }

    @staticmethod
    def generalization_gap(train_metric: float, test_metric: float) -> float:
        """
        phase11.md §20 — generalization gap.
        Large positive gap = potential overfitting.
        """
        return round(train_metric - test_metric, 6)

    @staticmethod
    def compute_train_and_test(
        y_train: np.ndarray,
        y_pred_train: np.ndarray,
        y_scores_train: np.ndarray,
        y_test: np.ndarray,
        y_pred_test: np.ndarray,
        y_scores_test: np.ndarray,
    ) -> dict:
        """
        Compute metrics on both train and test, and report generalization gaps.
        Used by ExperimentExecutor for phase11.md §19-20 analysis.
        """
        train = MetricsCalculator.compute(y_train, y_pred_train, y_scores_train)
        test = MetricsCalculator.compute(y_test, y_pred_test, y_scores_test)

        gaps = {
            k: MetricsCalculator.generalization_gap(train[k], test[k])
            for k in ["accuracy", "recall", "roc_auc"]
        }

        return {
            "train": train,
            "test": test,
            "generalization_gaps": gaps,
        }
