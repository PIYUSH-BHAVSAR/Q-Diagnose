"""Complete feature engineering pipeline combining preprocessing and reduction."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from backend.core.logging import logger
from backend.data.preprocessing import PreprocessingPipeline, PreprocessedData
from backend.features.reducer import FeatureReducer, ReductionResult


@dataclass
class FeaturePipelineResult:
    """Result of complete feature pipeline."""
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    original_feature_names: List[str]
    reduced_feature_names: List[str]
    preprocessing_info: Dict
    reduction_info: Dict
    train_indices: np.ndarray
    test_indices: np.ndarray
    
    def to_dict(self) -> dict:
        return {
            'train_samples': self.X_train.shape[0],
            'test_samples': self.X_test.shape[0],
            'original_features': len(self.original_feature_names),
            'reduced_features': len(self.reduced_feature_names),
            'preprocessing': self.preprocessing_info,
            'reduction': self.reduction_info
        }


class FeaturePipeline:
    """Complete feature engineering pipeline.
    
    Combines:
    1. Preprocessing (split, impute, scale)
    2. Feature reduction (PCA)
    
    Ensures data leakage prevention at all stages.
    """
    
    def __init__(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        n_components: Optional[int] = None,
        variance_threshold: float = 0.95,
        max_qubits: int = 8
    ):
        """Initialize feature pipeline.
        
        Args:
            test_size: Test set fraction
            random_state: Random seed
            n_components: Target PCA components
            variance_threshold: Minimum variance to preserve
            max_qubits: Maximum quantum qubits
        """
        self.test_size = test_size
        self.random_state = random_state
        self.n_components = n_components
        self.variance_threshold = variance_threshold
        self.max_qubits = max_qubits
        
        self.preprocessing_: Optional[PreprocessingPipeline] = None
        self.reduction_: Optional[FeatureReducer] = None
        self.is_fitted = False
    
    def fit_transform(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        subject_ids: Optional[List[str]] = None
    ) -> FeaturePipelineResult:
        """Run complete feature pipeline.
        
        Steps:
        1. Preprocess (split, impute, scale)
        2. Reduce dimensions (PCA)
        
        Args:
            X: Features
            y: Target
            subject_ids: Optional subject IDs for group-aware splitting
        
        Returns:
            FeaturePipelineResult with processed data
        """
        logger.info("=" * 60)
        logger.info("Starting Feature Pipeline")
        logger.info("=" * 60)
        
        # Step 1: Preprocessing
        logger.info("Step 1: Preprocessing (split, impute, scale)")
        self.preprocessing_ = PreprocessingPipeline(
            test_size=self.test_size,
            random_state=self.random_state
        )
        
        preprocessed = self.preprocessing_.fit_transform(
            X, y, subject_ids
        )
        
        # Step 2: Feature Reduction
        logger.info("Step 2: Feature Reduction (PCA)")
        self.reduction_ = FeatureReducer(
            n_components=self.n_components,
            variance_threshold=self.variance_threshold,
            max_qubits=self.max_qubits
        )
        
        reduced = self.reduction_.fit_transform(
            preprocessed.X_train,
            preprocessed.X_test,
            preprocessed.feature_names
        )
        
        self.is_fitted = True
        
        logger.info("=" * 60)
        logger.info(
            f"Feature Pipeline Complete: "
            f"{preprocessed.X_train.shape[1]} -> {reduced.X_train_reduced.shape[1]} features"
        )
        logger.info("=" * 60)
        
        return FeaturePipelineResult(
            X_train=reduced.X_train_reduced,
            X_test=reduced.X_test_reduced,
            y_train=preprocessed.y_train,
            y_test=preprocessed.y_test,
            original_feature_names=preprocessed.feature_names,
            reduced_feature_names=reduced.component_names,
            preprocessing_info=preprocessed.preprocessing_info,
            reduction_info=reduced.to_dict(),
            train_indices=preprocessed.train_indices,
            test_indices=preprocessed.test_indices
        )
    
    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Transform new data through fitted pipeline.
        
        Args:
            X: New data to transform
        
        Returns:
            Transformed and reduced features
        """
        if not self.is_fitted:
            raise RuntimeError("Pipeline must be fitted before transform")
        
        # Preprocess
        X_preprocessed = self.preprocessing_.transform(X)
        
        # Reduce
        X_reduced = self.reduction_.transform(X_preprocessed)
        
        return X_reduced
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance information.
        
        Returns:
            Dictionary with component importance
        """
        if not self.is_fitted:
            raise RuntimeError("Pipeline must be fitted first")
        
        return {
            'pca_components': self.reduction_.get_component_importance(),
            'explained_variance': self.reduction_.pca_.explained_variance_ratio_.tolist()
        }
