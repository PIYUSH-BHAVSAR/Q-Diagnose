"""Dataset validator for ensuring data quality."""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from backend.core.exceptions import DatasetValidationError
from backend.core.logging import logger
from backend.data.profiler import DatasetProfile, _convert_numpy


@dataclass
class ValidationResult:
    """Result of dataset validation."""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    ready_for_ml: bool
    needs_target_selection: bool
    details: dict
    
    def to_dict(self) -> dict:
        return _convert_numpy({
            'is_valid': bool(self.is_valid),
            'issues': [str(i) for i in self.issues],
            'warnings': [str(w) for w in self.warnings],
            'ready_for_ml': bool(self.ready_for_ml),
            'needs_target_selection': bool(self.needs_target_selection),
            'details': self.details
        })


class DatasetValidator:
    """Validates datasets for ML pipeline compatibility."""
    
    MIN_SAMPLES = 50
    MIN_FEATURES = 2
    MAX_MISSING_PERCENTAGE = 50.0
    MIN_CLASS_SAMPLES = 10
    
    def validate(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        target_column: Optional[str] = None
    ) -> ValidationResult:
        """Validate a dataset for the ML pipeline.
        
        Args:
            df: DataFrame to validate
            profile: Dataset profile from profiler
            target_column: Optional target column (auto-detected if None)
        
        Returns:
            ValidationResult with validation status and issues
        """
        issues = []
        warnings = []
        details = {}
        
        logger.info(f"Validating dataset: {profile.dataset_id}")
        
        # Check if DataFrame is empty
        if len(df) == 0:
            issues.append("Dataset is empty (0 rows)")
            return ValidationResult(
                is_valid=False,
                issues=issues,
                warnings=warnings,
                ready_for_ml=False,
                needs_target_selection=False,
                details=details
            )
        
        # Check minimum samples
        if len(df) < self.MIN_SAMPLES:
            issues.append(
                f"Dataset has only {len(df)} rows. "
                f"Minimum recommended: {self.MIN_SAMPLES}"
            )
        
        # Check minimum features
        feature_count = len(profile.numerical_columns) + len(profile.categorical_columns)
        if feature_count < self.MIN_FEATURES:
            issues.append(
                f"Dataset has only {feature_count} features. "
                f"Minimum required: {self.MIN_FEATURES}"
            )
        
        # Check for completely empty columns
        empty_columns = df.columns[df.isnull().all()].tolist()
        if empty_columns:
            issues.append(
                f"Columns with all missing values: {empty_columns}"
            )
        
        # Check for high missing value percentage
        high_missing_cols = []
        for col in df.columns:
            missing_pct = (df[col].isnull().sum() / len(df)) * 100
            if missing_pct > self.MAX_MISSING_PERCENTAGE:
                high_missing_cols.append((col, missing_pct))
        
        if high_missing_cols:
            warnings.append(
                f"Columns with >{self.MAX_MISSING_PERCENTAGE}% missing: "
                f"{[(c, f'{p:.1f}%') for c, p in high_missing_cols]}"
            )
        
        # Check for infinite values in numeric columns
        inf_cols = []
        for col in profile.numerical_columns:
            if np.isinf(df[col]).any():
                inf_cols.append(col)
        
        if inf_cols:
            issues.append(f"Infinite values found in columns: {inf_cols}")
        
        # Validate target column
        needs_target_selection = False
        if not target_column:
            if profile.recommended_target:
                target_column = profile.recommended_target
                details['auto_detected_target'] = target_column
            else:
                needs_target_selection = True
                warnings.append(
                    "Could not automatically detect target column. "
                    "Please select a target column."
                )
        
        if target_column:
            target_validation = self._validate_target(df, profile, target_column)
            issues.extend(target_validation['issues'])
            warnings.extend(target_validation['warnings'])
            details.update(target_validation['details'])
        
        # Check class imbalance
        if profile.class_imbalance_ratio and profile.class_imbalance_ratio > 5:
            warnings.append(
                f"Significant class imbalance detected (ratio: {profile.class_imbalance_ratio:.2f}). "
                f"Consider using stratified splitting."
            )
        
        # Check for subject column (Parkinson's case)
        if profile.subject_column:
            details['subject_column'] = profile.subject_column
            details['split_recommendation'] = 'group_aware'
            warnings.append(
                f"Subject column detected: '{profile.subject_column}'. "
                f"Group-aware splitting will be used to prevent data leakage."
            )
        
        # Overall validation status
        is_valid = len(issues) == 0
        ready_for_ml = is_valid and not needs_target_selection
        
        result = ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            ready_for_ml=ready_for_ml,
            needs_target_selection=needs_target_selection,
            details=details
        )
        
        logger.info(
            f"Validation complete: valid={is_valid}, "
            f"ready_for_ml={ready_for_ml}, issues={len(issues)}"
        )
        
        return result
    
    def _validate_target(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        target_column: str
    ) -> dict:
        """Validate the target column."""
        issues = []
        warnings = []
        details = {}
        
        if target_column not in df.columns:
            issues.append(f"Target column '{target_column}' not found in dataset")
            return {'issues': issues, 'warnings': warnings, 'details': details}
        
        target = df[target_column]
        
        # Check target has valid values
        if target.isnull().all():
            issues.append(f"Target column '{target_column}' contains only missing values")
            return {'issues': issues, 'warnings': warnings, 'details': details}
        
        # Check for binary classification
        unique_values = target.dropna().nunique()
        details['target_unique_values'] = int(unique_values)
        details['target_classes'] = target.dropna().unique().tolist()[:10]  # First 10
        
        if unique_values != 2:
            if unique_values == 1:
                issues.append(
                    f"Target column has only 1 unique value. "
                    f"Cannot perform binary classification."
                )
            elif unique_values > 10:
                warnings.append(
                    f"Target column has {unique_values} unique values. "
                    f"This may be a regression task rather than classification."
                )
            else:
                details['task_type'] = 'multiclass_classification'
        else:
            details['task_type'] = 'binary_classification'
        
        # Check minimum samples per class
        class_counts = target.value_counts()
        small_classes = class_counts[class_counts < self.MIN_CLASS_SAMPLES]
        if len(small_classes) > 0:
            warnings.append(
                f"Some classes have fewer than {self.MIN_CLASS_SAMPLES} samples: "
                f"{small_classes.to_dict()}"
            )
        
        # Check for missing values in target
        target_missing = target.isnull().sum()
        if target_missing > 0:
            warnings.append(
                f"Target column has {target_missing} missing values. "
                f"These rows will be removed during preprocessing."
            )
        
        return {'issues': issues, 'warnings': warnings, 'details': details}
