"""Shared metric helper used by all model implementations.

Centralises confusion-matrix unpacking so a model that collapses to a
single predicted class doesn't crash with 'too many values to unpack'.
"""

from typing import Dict, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def safe_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: Optional[np.ndarray] = None,
) -> Dict:
    """Calculate classification metrics safely.

    Handles the edge case where a model predicts only one class (e.g.
    an undertrained VQC that always outputs 1), which causes
    ``confusion_matrix(...).ravel()`` to return only one or two values
    instead of four, crashing with ``ValueError: too many values to unpack``.
    """
    metrics: Dict = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }

    # Safe confusion-matrix unpacking
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    elif cm.shape == (1, 1):
        # Model predicts only one class — determine which
        unique_pred = np.unique(y_pred)
        if unique_pred[0] == 0:
            tn, fp, fn, tp = int(cm[0, 0]), 0, 0, 0
        else:
            tn, fp, fn, tp = 0, 0, 0, int(cm[0, 0])
    else:
        tn, fp, fn, tp = 0, 0, 0, 0

    metrics["specificity"] = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    metrics["sensitivity"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    metrics["confusion_matrix"] = [[int(tn), int(fp)], [int(fn), int(tp)]]

    if y_pred_proba is not None:
        try:
            metrics["roc_auc"] = roc_auc_score(y_true, y_pred_proba)
        except ValueError:
            # Only one class present in y_true / y_pred_proba
            metrics["roc_auc"] = None

    return metrics
