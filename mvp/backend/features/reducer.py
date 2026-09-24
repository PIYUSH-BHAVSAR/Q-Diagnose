"""Feature reduction using PCA.

Implements dimensionality reduction for quantum encoding.
CRITICAL: PCA is fit ONLY on training data to prevent data leakage.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

from backend.core.config import config
from backend.core.logging import logger


@dataclass
class ReductionResult:
    """Result of feature reduction."""
    X_train_reduced: np.ndarray
    X_test_reduced: np.ndarray
    n_components: int
    explained_variance_ratio: np.ndarray
    cumulative_variance: float
    component_names: List[str]
    reduction_info: Dict
    
    def to_dict(self) -> dict:
        return {
            'n_components': self.n_components,
            'cumulative_variance': round(self.cumulative_variance, 4),
            'explained_variance_ratio': [round(v, 4) for v in self.explained_variance_ratio],
            'component_names': self.component_names,
            'original_features': self.reduction_info.get('original_features'),
            'reduction_method': self.reduction_info.get('method')
        }


class FeatureReducer:
    """Feature reduction using PCA.
    
    Reduces features to a compact representation suitable for
    quantum encoding (typically 4-8 dimensions).
    """
    
    def __init__(
        self,
        n_components: Optional[int] = None,
        variance_threshold: float = 0.95,
        max_qubits: int = 8
    ):
        """Initialize feature reducer.
        
        Args:
            n_components: Target number of components (auto-selected if None)
            variance_threshold: Minimum variance to preserve
            max_qubits: Maximum quantum qubits (limits components)
        """
        self.n_components = n_components
        self.variance_threshold = variance_threshold
        self.max_qubits = max_qubits
        self.pca_: Optional[PCA] = None
        self.is_fitted = False
    
    def fit_transform(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> ReductionResult:
        """Fit PCA on training data and transform both sets.
        
        CRITICAL: PCA is fit ONLY on training data.
        
        Args:
            X_train: Training features
            X_test: Test features
            feature_names: Original feature names
        
        Returns:
            ReductionResult with reduced features
        """
        logger.info(
            f"Starting feature reduction: {X_train.shape[1]} features -> "
            f"target={self.n_components or 'auto'}"
        )
        
        # Determine number of components
        n_components = self._determine_components(X_train)
        
        reduction_info = {
            'method': 'pca',
            'original_features': X_train.shape[1],
            'target_components': n_components
        }
        
        # Fit PCA on TRAIN ONLY
        self.pca_ = PCA(n_components=n_components, random_state=42)
        X_train_reduced = self.pca_.fit_transform(X_train)
        
        # Transform test using train-fitted PCA
        X_test_reduced = self.pca_.transform(X_test)
        
        self.is_fitted = True
        
        # Calculate variance explained
        explained_variance = self.pca_.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)[-1]
        
        # Component names
        component_names = [f"PC{i+1}" for i in range(n_components)]
        
        reduction_info.update({
            'actual_components': n_components,
            'cumulative_variance': cumulative_variance,
            'singular_values': self.pca_.singular_values_.tolist()
        })
        
        logger.info(
            f"PCA complete: {n_components} components, "
            f"variance explained: {cumulative_variance:.4f}"
        )
        
        return ReductionResult(
            X_train_reduced=X_train_reduced,
            X_test_reduced=X_test_reduced,
            n_components=n_components,
            explained_variance_ratio=explained_variance,
            cumulative_variance=cumulative_variance,
            component_names=component_names,
            reduction_info=reduction_info
        )
    
    def _determine_components(self, X: np.ndarray) -> int:
        """Determine optimal number of components.
        
        Uses the minimum of:
        - Specified n_components
        - max_qubits (quantum limit)
        - Number of features
        - Components needed for variance threshold
        """
        n_features = X.shape[1]
        safe_max = max(2, min(n_features, self.max_qubits))
        
        if self.n_components is not None:
            n_components = min(self.n_components, n_features, self.max_qubits)
        else:
            temp_pca = PCA(n_components=safe_max)
            temp_pca.fit(X)
            
            cumulative_variance = np.cumsum(temp_pca.explained_variance_ratio_)
            
            # Find minimum components for variance threshold
            n_for_variance = np.argmax(
                cumulative_variance >= self.variance_threshold
            ) + 1 if cumulative_variance[-1] >= self.variance_threshold else len(cumulative_variance)
            
            # Use candidate dimensions from config if available
            candidate_dims = config.quantum_config.get('candidate_dimensions', [4, 8])
            
            # Select from candidates
            n_components = candidate_dims[0]  # Default to smallest
            for dim in sorted(candidate_dims):
                if dim <= self.max_qubits and dim <= n_features:
                    if dim >= n_for_variance or dim == candidate_dims[-1]:
                        n_components = dim
                        break
            
            n_components = min(n_components, n_features, self.max_qubits)
        
        return max(2, n_components)  # Minimum 2 components
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform new data using fitted PCA.
        
        Args:
            X: Data to transform
        
        Returns:
            Reduced features
        """
        if not self.is_fitted:
            raise RuntimeError("Reducer must be fitted before transform")
        
        return self.pca_.transform(X)
    
    def get_component_importance(self) -> Dict:
        """Get importance of original features in principal components.
        
        Returns:
            Dictionary mapping component names to feature weights
        """
        if not self.is_fitted:
            raise RuntimeError("Reducer must be fitted first")
        
        return {
            f"PC{i+1}": self.pca_.components_[i].tolist()
            for i in range(self.pca_.n_components_)
        }
