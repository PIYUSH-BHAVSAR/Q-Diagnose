"""Metrics calculation for model evaluation."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    precision_recall_curve,
    average_precision_score
)


@dataclass
class ClassificationMetrics:
    """Container for classification metrics."""
    accuracy: float
    precision: float
    recall: float
    specificity: float
    sensitivity: float
    f1: float
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    confusion_matrix: List[List[int]]
    
    def to_dict(self) -> dict:
        return {
            'accuracy': round(self.accuracy, 4),
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'specificity': round(self.specificity, 4),
            'sensitivity': round(self.sensitivity, 4),
            'f1': round(self.f1, 4),
            'roc_auc': round(self.roc_auc, 4) if self.roc_auc else None,
            'pr_auc': round(self.pr_auc, 4) if self.pr_auc else None,
            'confusion_matrix': self.confusion_matrix
        }


class MetricsCalculator:
    """Calculates comprehensive classification metrics.
    
    For disease detection, prioritizes:
    - Recall/Sensitivity (avoid missing positive cases)
    - Specificity (avoid false alarms)
    - ROC-AUC (overall discriminative ability)
    """
    
    @staticmethod
    def calculate(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: Optional[np.ndarray] = None
    ) -> ClassificationMetrics:
        """Calculate all classification metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (optional, for AUC)
        
        Returns:
            ClassificationMetrics object
        """
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        # Basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)  # Same as sensitivity
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        # Specificity: TN / (TN + FP)
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        # Sensitivity = Recall
        sensitivity = recall
        
        # ROC-AUC
        roc_auc = None
        if y_pred_proba is not None:
            try:
                roc_auc = roc_auc_score(y_true, y_pred_proba)
            except ValueError:
                pass
        
        # PR-AUC
        pr_auc = None
        if y_pred_proba is not None:
            try:
                pr_auc = average_precision_score(y_true, y_pred_proba)
            except ValueError:
                pass
        
        return ClassificationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            specificity=specificity,
            sensitivity=sensitivity,
            f1=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            confusion_matrix=[[int(tn), int(fp)], [int(fn), int(tp)]]
        )
    
    @staticmethod
    def get_detailed_report(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        target_names: Optional[List[str]] = None
    ) -> str:
        """Get detailed classification report.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            target_names: Class names
        
        Returns:
            Classification report string
        """
        return classification_report(
            y_true, 
            y_pred, 
            target_names=target_names,
            zero_division=0
        )
    
    @staticmethod
    def get_roc_curve_data(
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> Dict:
        """Get ROC curve data for visualization.
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
        
        Returns:
            Dictionary with fpr, tpr, thresholds
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        
        return {
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist(),
            'thresholds': thresholds.tolist()
        }
    
    @staticmethod
    def get_pr_curve_data(
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> Dict:
        """Get Precision-Recall curve data.
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
        
        Returns:
            Dictionary with precision, recall, thresholds
        """
        precision, recall, thresholds = precision_recall_curve(
            y_true, y_pred_proba
        )
        
        return {
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist() if len(thresholds) > 0 else []
        }
