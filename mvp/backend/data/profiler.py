"""Dataset profiler for analyzing CSV structure and statistics."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from backend.core.logging import logger


@dataclass
class ColumnProfile:
    """Profile for a single column."""
    name: str
    dtype: str
    missing_count: int
    missing_percentage: float
    unique_count: int
    is_numeric: bool
    is_categorical: bool
    is_target_candidate: bool = False
    target_candidate_score: float = 0.0
    sample_values: List[Any] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


def _convert_numpy(obj):
    if isinstance(obj, dict):
        return {str(k): _convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return _convert_numpy(obj.tolist())
    return obj


@dataclass
class DatasetProfile:
    """Complete profile for a dataset."""
    dataset_id: str
    name: str
    rows: int
    columns: int
    column_profiles: List[ColumnProfile]
    missing_values_total: int
    missing_percentage: float
    duplicate_rows: int
    numerical_columns: List[str]
    categorical_columns: List[str]
    target_candidates: List[str]
    class_distribution: Optional[Dict[str, int]] = None
    recommended_target: Optional[str] = None
    is_binary_classification: bool = False
    class_imbalance_ratio: Optional[float] = None
    subject_column: Optional[str] = None
    profiled_at: str = ""
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary for API response."""
        res = {
            'dataset_id': self.dataset_id,
            'name': self.name,
            'rows': int(self.rows),
            'columns': int(self.columns),
            'missing_values_total': int(self.missing_values_total),
            'missing_percentage': round(float(self.missing_percentage), 2),
            'duplicate_rows': int(self.duplicate_rows),
            'numerical_columns_count': len(self.numerical_columns),
            'categorical_columns_count': len(self.categorical_columns),
            'target_candidates': list(self.target_candidates),
            'recommended_target': self.recommended_target,
            'is_binary_classification': bool(self.is_binary_classification),
            'class_distribution': _convert_numpy(self.class_distribution) if self.class_distribution else None,
            'class_imbalance_ratio': float(self.class_imbalance_ratio) if self.class_imbalance_ratio is not None else None,
            'subject_column': self.subject_column,
            'profiled_at': self.profiled_at,
            'columns': [
                {
                    'name': col.name,
                    'dtype': str(col.dtype),
                    'missing_count': int(col.missing_count),
                    'missing_percentage': round(float(col.missing_percentage), 2),
                    'unique_count': int(col.unique_count),
                    'is_numeric': bool(col.is_numeric),
                    'is_categorical': bool(col.is_categorical),
                    'is_target_candidate': bool(col.is_target_candidate),
                    'sample_values': _convert_numpy(col.sample_values[:5])
                }
                for col in self.column_profiles
            ]
        }
        return _convert_numpy(res)


class DatasetProfiler:
    """Profiles datasets to understand their structure and characteristics."""
    
    # Keywords that suggest target columns
    TARGET_KEYWORDS = {
        'target', 'diagnosis', 'status', 'label', 'class', 'outcome',
        'result', 'prediction', 'disease', 'condition'
    }
    
    # Keywords that suggest subject/patient identifiers
    SUBJECT_KEYWORDS = {
        'subject', 'patient', 'id', 'name', 'identifier', 'subject#'
    }
    
    # Columns to exclude as target candidates
    EXCLUDE_TARGET_PATTERNS = {
        'id', '_id', 'subject', 'name', 'identifier'
    }
    
    def __init__(self, max_categorical_unique: int = 10):
        """Initialize the profiler.
        
        Args:
            max_categorical_unique: Maximum unique values for a column
                to be considered categorical
        """
        self.max_categorical_unique = max_categorical_unique
    
    def profile(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        dataset_name: str
    ) -> DatasetProfile:
        """Generate a complete profile for a DataFrame.
        
        Args:
            df: DataFrame to profile
            dataset_id: Dataset identifier
            dataset_name: Name of the dataset
        
        Returns:
            DatasetProfile object
        """
        from datetime import datetime
        
        logger.info(f"Profiling dataset: {dataset_id}")
        
        # Profile each column
        column_profiles = []
        for col in df.columns:
            profile = self._profile_column(df, col)
            column_profiles.append(profile)
        
        # Detect target candidates
        target_candidates = self._detect_target_candidates(df, column_profiles)
        
        # Detect subject columns
        subject_column = self._detect_subject_column(df, column_profiles)
        
        # Determine if binary classification
        is_binary = False
        class_distribution = None
        class_imbalance = None
        recommended_target = None
        
        if target_candidates:
            recommended_target = target_candidates[0]
            target_col = df[recommended_target]
            
            unique_values = target_col.nunique()
            if unique_values == 2:
                is_binary = True
                class_distribution = target_col.value_counts().to_dict()
                
                # Calculate class imbalance ratio
                counts = list(class_distribution.values())
                if len(counts) == 2:
                    class_imbalance = max(counts) / min(counts)
        
        # Separate numerical and categorical columns
        numerical_cols = [p.name for p in column_profiles if p.is_numeric]
        categorical_cols = [p.name for p in column_profiles if p.is_categorical]
        
        # Calculate overall statistics
        missing_total = df.isnull().sum().sum()
        missing_pct = (missing_total / (len(df) * len(df.columns))) * 100
        duplicates = df.duplicated().sum()
        
        profile = DatasetProfile(
            dataset_id=dataset_id,
            name=dataset_name,
            rows=len(df),
            columns=len(df.columns),
            column_profiles=column_profiles,
            missing_values_total=missing_total,
            missing_percentage=missing_pct,
            duplicate_rows=duplicates,
            numerical_columns=numerical_cols,
            categorical_columns=categorical_cols,
            target_candidates=target_candidates,
            recommended_target=recommended_target,
            is_binary_classification=is_binary,
            class_distribution=class_distribution,
            class_imbalance_ratio=class_imbalance,
            subject_column=subject_column,
            profiled_at=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Profile complete: {profile.rows} rows, {profile.columns} columns, "
            f"target: {profile.recommended_target}, binary: {profile.is_binary_classification}"
        )
        
        return profile
    
    def _profile_column(self, df: pd.DataFrame, col_name: str) -> ColumnProfile:
        """Profile a single column."""
        col = df[col_name]
        
        # Basic stats
        missing_count = col.isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        unique_count = col.nunique()
        
        # Determine type
        is_numeric = pd.api.types.is_numeric_dtype(col)
        
        # Categorical if few unique values or object type
        is_categorical = (
            unique_count <= self.max_categorical_unique or
            pd.api.types.is_object_dtype(col) or
            pd.api.types.is_categorical_dtype(col)
        )
        
        # Sample values
        sample_values = col.dropna().head(5).tolist()
        
        # Statistics for numeric columns
        statistics = {}
        if is_numeric:
            stats = col.describe()
            statistics = {
                'mean': stats.get('mean'),
                'std': stats.get('std'),
                'min': stats.get('min'),
                'max': stats.get('max'),
                'median': col.median()
            }
        
        return ColumnProfile(
            name=col_name,
            dtype=str(col.dtype),
            missing_count=missing_count,
            missing_percentage=missing_pct,
            unique_count=unique_count,
            is_numeric=is_numeric,
            is_categorical=is_categorical,
            sample_values=sample_values,
            statistics=statistics
        )
    
    def _detect_target_candidates(
        self,
        df: pd.DataFrame,
        column_profiles: List[ColumnProfile]
    ) -> List[str]:
        """Detect columns that could be target variables.
        
        Priority:
        1. Columns with target-related names
        2. Columns with exactly 2 unique values (binary)
        3. Categorical columns with few unique values
        """
        candidates = []
        
        for profile in column_profiles:
            score = 0.0
            
            # Check if column name suggests it's a target
            col_lower = profile.name.lower()
            
            # Skip ID/subject columns — use exact name or suffix match,
            # NOT a substring match, to avoid excluding 'radius_mean' etc.
            col_exact = profile.name.lower()
            if col_exact in {'id', 'name', 'subject', 'identifier'} or col_exact.endswith('_id'):
                continue
            
            # Boost score for target keywords
            for keyword in self.TARGET_KEYWORDS:
                if keyword in col_lower:
                    score += 3.0
                    break
            
            # Binary classification is ideal for our MVP
            if profile.unique_count == 2:
                score += 2.0
            
            # Moderate number of unique values (not too many, not too few)
            elif 2 < profile.unique_count <= 10:
                score += 1.0
            
            # Prefer categorical for classification
            if profile.is_categorical and not profile.is_numeric:
                score += 1.0
            
            if score > 0:
                profile.is_target_candidate = True
                profile.target_candidate_score = score
                candidates.append((profile.name, score))
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [c[0] for c in candidates]
    
    def _detect_subject_column(
        self,
        df: pd.DataFrame,
        column_profiles: List[ColumnProfile]
    ) -> Optional[str]:
        """Detect columns that identify subjects/patients.
        
        This is important for group-aware splitting to prevent
        data leakage when the same subject appears multiple times.
        """
        for profile in column_profiles:
            col_lower = profile.name.lower()
            
            for keyword in self.SUBJECT_KEYWORDS:
                if keyword in col_lower:
                    # Verify it has multiple records per subject
                    unique_ratio = profile.unique_count / len(df)
                    if unique_ratio < 0.5:  # Many subjects have multiple records
                        return profile.name
        
        return None
