"""Logistic Regression model implementation."""

from dataclasses import dataclass
from typing import Dict, Optional, List

import numpy as np
from sklearn.linear_model import LogisticRegression as SklearnLR
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from backend.core.logging import logger
from backend.models.shared_metrics import safe_classification_metrics
@dataclass
class ModelResult:
    """Result from model training and prediction."""
    model_name: str
    model_type: str
    
    # Predictions
    y_pred_train: np.ndarray
    y_pred_test: np.ndarray
    y_pred_proba_test: Optional[np.ndarray] = None
    
    # Metrics
    metrics: Dict = None
    
    # Timing
    training_time: float = 0.0
    inference_time: float = 0.0
    
    # Model object
    model: Optional[object] = None
    
    def to_dict(self) -> dict:
        # Serialise numpy values inside metrics
        import numpy as np
        def _native(v):
            if isinstance(v, (np.integer,)): return int(v)
            if isinstance(v, (np.floating,)): return float(v)
            if isinstance(v, np.ndarray): return v.tolist()
            return v

        safe_metrics = {k: _native(v) for k, v in (self.metrics or {}).items()
                        if k != 'feature_importance'}

        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'metrics': safe_metrics,
            'training_time': round(self.training_time, 4),
            'inference_time': round(self.inference_time, 4),
        }


class LogisticRegressionModel:
    """Logistic Regression wrapper for binary classification."""
    
    def __init__(
        self,
        max_iter: int = 1000,
        random_state: int = 42,
        C: float = 1.0,
        solver: str = 'lbfgs'
    ):
        """Initialize Logistic Regression model.
        
        Args:
            max_iter: Maximum iterations for optimization
            random_state: Random seed
            C: Regularization parameter (inverse)
            solver: Optimization algorithm
        """
        self.model = SklearnLR(
            max_iter=max_iter,
            random_state=random_state,
            C=C,
            solver=solver
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
        
        logger.info("Training Logistic Regression model")
        
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
            y_pred_proba_test = self.model.predict_proba(X_test)[:, 1]
            inference_time = time.perf_counter() - start_time
            
            metrics = self._calculate_metrics(y_test, y_pred_test, y_pred_proba_test)
        else:
            inference_time = 0.0
        
        logger.info(
            f"Logistic Regression trained: "
            f"train_acc={accuracy_score(y_train, y_pred_train):.4f}, "
            f"time={training_time:.4f}s"
        )
        
        return ModelResult(
            model_name='logistic_regression',
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
        return self.model.predict_proba(X)
    
    def _calculate_metrics(self, y_true, y_pred, y_pred_proba=None):
        return safe_classification_metrics(y_true, y_pred, y_pred_proba)
