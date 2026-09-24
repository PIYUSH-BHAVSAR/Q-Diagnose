"""Preprocessing pipeline for dataset preparation.

Implements proper data leakage prevention by fitting transformers
only on training data.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

from backend.core.config import config
from backend.core.logging import logger


@dataclass
class PreprocessedData:
    """Container for preprocessed training and test data."""
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    feature_names: List[str]
    train_indices: np.ndarray
    test_indices: np.ndarray
    preprocessing_info: Dict
    
    def to_dict(self) -> dict:
        return {
            'train_samples': len(self.X_train),
            'test_samples': len(self.X_test),
            'features': len(self.feature_names),
            'feature_names': self.feature_names,
            'split_type': self.preprocessing_info.get('split_type'),
            'preprocessing_steps': self.preprocessing_info.get('steps', [])
        }


class PreprocessingPipeline:
    """Preprocessing pipeline with data leakage prevention.
    
    CRITICAL: All transformers are fit ONLY on training data.
    """
    
    def __init__(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        handle_missing: bool = True,
        scale_features: bool = True
    ):
        """Initialize preprocessing pipeline.
        
        Args:
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility
            handle_missing: Whether to impute missing values
            scale_features: Whether to standardize features
        """
        self.test_size = test_size
        self.random_state = random_state
        self.handle_missing = handle_missing
        self.scale_features = scale_features
        
        # Fitted transformers (fit on train only!)
        self.imputer_: Optional[SimpleImputer] = None
        self.scaler_: Optional[StandardScaler] = None
        self.label_encoder_: Optional[LabelEncoder] = None
        
        self.is_fitted = False
    
    def fit_transform(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        subject_ids: Optional[List[str]] = None,
        target_column: Optional[str] = None
    ) -> PreprocessedData:
        """Fit pipeline on training data and transform.
        
        This is the main entry point that:
        1. Splits data into train/test (with group awareness if needed)
        2. Fits transformers on TRAIN ONLY
        3. Transforms both train and test
        
        Args:
            X: Feature matrix
            y: Target vector
            subject_ids: Optional subject IDs for group-aware splitting
            target_column: Optional target column name for metadata
        
        Returns:
            PreprocessedData with train/test splits
        """
        logger.info("Starting preprocessing pipeline")
        
        # Convert to numpy/pandas if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        else:
            feature_names = list(X.columns)
        
        if isinstance(y, pd.Series):
            y = y.values
        
        preprocessing_info = {
            'steps': [],
            'original_shape': X.shape,
            'split_type': 'stratified'
        }
        
        # Step 1: Train/Test Split (CRITICAL - do this FIRST)
        X_train, X_test, y_train, y_test, train_idx, test_idx = self._split_data(
            X, y, subject_ids
        )
        preprocessing_info['steps'].append('train_test_split')
        # Check if subject_ids is provided (handle both None and empty array)
        has_subject_ids = subject_ids is not None and (not isinstance(subject_ids, np.ndarray) or len(subject_ids) > 0)
        preprocessing_info['split_type'] = 'group_aware' if has_subject_ids else 'stratified'
        
        logger.info(
            f"Split data: train={len(X_train)}, test={len(X_test)}, "
            f"type={preprocessing_info['split_type']}"
        )
        
        # Step 2: Handle missing values (fit on train only)
        if self.handle_missing and X_train.isnull().any().any():
            X_train, X_test = self._handle_missing(X_train, X_test)
            preprocessing_info['steps'].append('missing_value_imputation')
            logger.info("Imputed missing values")
        
        # Step 3: Encode target if needed
        if y_train.dtype == object or y_train.dtype.name == 'category':
            y_train, y_test = self._encode_target(y_train, y_test)
            preprocessing_info['steps'].append('target_encoding')
            logger.info("Encoded target labels")
        
        # Step 4: Scale features (fit on train only)
        if self.scale_features:
            X_train, X_test = self._scale_features(X_train, X_test)
            preprocessing_info['steps'].append('feature_scaling')
            logger.info("Scaled features")
        
        # Convert to numpy
        X_train_np = X_train.values if isinstance(X_train, pd.DataFrame) else X_train
        X_test_np = X_test.values if isinstance(X_test, pd.DataFrame) else X_test
        
        self.is_fitted = True
        preprocessing_info['final_shape'] = {'train': X_train_np.shape, 'test': X_test_np.shape}
        
        logger.info(
            f"Preprocessing complete: {X_train_np.shape[1]} features, "
            f"train={X_train_np.shape[0]}, test={X_test_np.shape[0]}"
        )
        
        return PreprocessedData(
            X_train=X_train_np,
            X_test=X_test_np,
            y_train=y_train,
            y_test=y_test,
            feature_names=feature_names,
            train_indices=train_idx,
            test_indices=test_idx,
            preprocessing_info=preprocessing_info
        )
    
    def _split_data(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        subject_ids: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train/test sets.
        
        Uses group-aware split if subject_ids provided to prevent
        data leakage from same subject appearing in both sets.
        """
        indices = np.arange(len(X))
        
        if subject_ids is not None:
            # Group-aware split for Parkinson's-like datasets
            # where multiple recordings belong to same subject
            gss = GroupShuffleSplit(
                n_splits=1,
                test_size=self.test_size,
                random_state=self.random_state
            )
            train_idx, test_idx = next(gss.split(X, y, groups=subject_ids))
            
            logger.info(
                f"Group-aware split: {len(np.unique(subject_ids))} unique subjects"
            )
        else:
            # Standard stratified split
            train_idx, test_idx = train_test_split(
                indices,
                test_size=self.test_size,
                random_state=self.random_state,
                stratify=y
            )
        
        return (
            X.iloc[train_idx] if isinstance(X, pd.DataFrame) else X[train_idx],
            X.iloc[test_idx] if isinstance(X, pd.DataFrame) else X[test_idx],
            y[train_idx],
            y[test_idx],
            train_idx,
            test_idx
        )
    
    def _handle_missing(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Impute missing values (fit on train only)."""
        # Use median for numerical features
        self.imputer_ = SimpleImputer(strategy='median')
        
        # Fit on train only
        X_train_imputed = self.imputer_.fit_transform(X_train)
        
        # Transform test using train-fitted imputer
        X_test_imputed = self.imputer_.transform(X_test)
        
        return (
            pd.DataFrame(X_train_imputed, columns=X_train.columns, index=X_train.index),
            pd.DataFrame(X_test_imputed, columns=X_test.columns, index=X_test.index)
        )
    
    def _encode_target(
        self,
        y_train: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Encode categorical target labels."""
        self.label_encoder_ = LabelEncoder()
        
        # Fit on train only
        y_train_encoded = self.label_encoder_.fit_transform(y_train)
        
        # Transform test
        y_test_encoded = self.label_encoder_.transform(y_test)
        
        return y_train_encoded, y_test_encoded
    
    def _scale_features(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Standardize features (fit on train only)."""
        self.scaler_ = StandardScaler()
        
        # Fit on train only - CRITICAL
        X_train_scaled = self.scaler_.fit_transform(X_train)
        
        # Transform test using train-fitted scaler
        X_test_scaled = self.scaler_.transform(X_test)
        
        return (
            pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index),
            pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
        )
    
    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Transform new data using fitted pipeline.
        
        Args:
            X: New data to transform
        
        Returns:
            Transformed data
        """
        if not self.is_fitted:
            raise RuntimeError("Pipeline must be fitted before transform")
        
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        if self.imputer_ is not None:
            X = pd.DataFrame(
                self.imputer_.transform(X),
                columns=X.columns
            )
        
        if self.scaler_ is not None:
            X = pd.DataFrame(
                self.scaler_.transform(X),
                columns=X.columns
            )
        
        return X.values
