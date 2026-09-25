"""Random Forest model implementation."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier as SklearnRF
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from backend.core.logging import logger
from backend.models.classical.logistic_regression import ModelResult
from backend.models.shared_metrics import safe_classification_metrics


class RandomForestModel:
    """Random Forest wrapper for binary classification."""
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = 10,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        random_state: int = 42
    ):
        """Initialize Random Forest model.
        
        Args:
            n_estimators: Number of trees
            max_depth: Maximum depth of trees
            min_samples_split: Minimum samples to split a node
            min_samples_leaf: Minimum samples at a leaf node
            random_state: Random seed
        """
        self.model = SklearnRF(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state
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
            feature_names: Feature names for importance
        
        Returns:
            ModelResult with predictions and metrics
        """
        import time
        
        logger.info(
            f"Training Random Forest model "
            f"(n_estimators={self.model.n_estimators}, max_depth={self.model.max_depth})"
        )
        
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
            
            # Feature importance
            if feature_names:
                metrics['feature_importance'] = dict(zip(
                    feature_names,
                    self.model.feature_importances_.tolist()
                ))
        else:
            inference_time = 0.0
        
        logger.info(
            f"Random Forest trained: "
            f"train_acc={accuracy_score(y_train, y_pred_train):.4f}, "
            f"time={training_time:.4f}s"
        )
        
        return ModelResult(
            model_name='random_forest',
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
    
    def get_feature_importance(self) -> np.ndarray:
        """Get feature importances."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted first")
        return self.model.feature_importances_
    
    def _calculate_metrics(self, y_true, y_pred, y_pred_proba=None):
        metrics = safe_classification_metrics(y_true, y_pred, y_pred_proba)
        return metrics
