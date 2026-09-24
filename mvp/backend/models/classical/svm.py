"""Support Vector Machine model implementation."""

from dataclasses import dataclass
from typing import Dict, Optional, List

import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from backend.core.logging import logger
from backend.models.classical.logistic_regression import ModelResult
from backend.models.shared_metrics import safe_classification_metrics


class SVMModel:
    """Support Vector Machine wrapper for binary classification."""
    
    def __init__(
        self,
        kernel: str = 'rbf',
        C: float = 1.0,
        random_state: int = 42,
        probability: bool = True
    ):
        """Initialize SVM model.
        
        Args:
            kernel: Kernel type ('linear', 'rbf', 'poly')
            C: Regularization parameter
            random_state: Random seed
            probability: Whether to enable probability estimates
        """
        self.model = SVC(
            kernel=kernel,
            C=C,
            random_state=random_state,
            probability=probability
        )
        self.is_fitted = False
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None
    ) -> ModelResult:
        """Train the model and evaluate.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features (optional, for evaluation)
            y_test: Test labels (optional, for evaluation)
        
        Returns:
            ModelResult with predictions and metrics
        """
        import time
        
        logger.info(f"Training SVM model (kernel={self.model.kernel})")
        
        # Train
        start_time = time.perf_counter()
        self.model.fit(X_train, y_train)
        training_time = time.perf_counter() - start_time
        
        self.is_fitted = True
        
        # Predict
        y_pred_train = self.model.predict(X_train)
        
        y_pred_test = None
        y_pred_proba_test = None
        metrics = {}
        
        if X_test is not None and y_test is not None:
            start_time = time.perf_counter()
            y_pred_test = self.model.predict(X_test)
            y_pred_proba_test = self.model.predict_proba(X_test)[:, 1] if self.model.probability else None
            inference_time = time.perf_counter() - start_time
            
            metrics = self._calculate_metrics(y_test, y_pred_test, y_pred_proba_test)
        else:
            inference_time = 0.0
        
        logger.info(
            f"SVM trained: "
            f"train_acc={accuracy_score(y_train, y_pred_train):.4f}, "
            f"time={training_time:.4f}s"
        )
        
        return ModelResult(
            model_name='svm',
            model_type='classical',
            y_pred_train=y_pred_train,
            y_pred_test=y_pred_test,
            y_pred_proba_test=y_pred_proba_test,
            metrics=metrics,
            training_time=training_time,
            inference_time=inference_time,
            model=self.model
        )
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions on new data."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        if not self.model.probability:
            raise RuntimeError("Probability estimates not enabled")
        return self.model.predict_proba(X)
    
    def _calculate_metrics(self, y_true, y_pred, y_pred_proba=None):
        return safe_classification_metrics(y_true, y_pred, y_pred_proba)
