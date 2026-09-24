"""Dataset adapters for handling known dataset formats.

Each adapter knows the specifics of a particular dataset format,
including target column, columns to drop, and any special preprocessing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import pandas as pd


class DatasetAdapter(ABC):
    """Base adapter for handling specific dataset formats."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Dataset name."""
        pass
    
    @property
    @abstractmethod
    def target_column(self) -> str:
        """Target column name."""
        pass
    
    @property
    def drop_columns(self) -> List[str]:
        """Columns to drop from the dataset."""
        return []
    
    @property
    def subject_column(self) -> Optional[str]:
        """Subject/patient identifier column (for group-aware splitting)."""
        return None
    
    @property
    def positive_class(self) -> Optional[str]:
        """Value representing positive class (for binary classification)."""
        return None
    
    @abstractmethod
    def detect(self, df: pd.DataFrame) -> bool:
        """Check if this adapter matches the given DataFrame.
        
        Args:
            df: DataFrame to check
        
        Returns:
            True if this adapter can handle the dataset
        """
        pass
    
    def adapt(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        """Adapt the dataset for the ML pipeline.
        
        Args:
            df: Original DataFrame
        
        Returns:
            Tuple of (features_df, target_series, metadata)
        """
        metadata = {
            'adapter': self.name,
            'target_column': self.target_column,
            'dropped_columns': [],
            'subject_column': self.subject_column
        }
        
        # Make a copy
        df = df.copy()
        
        # Store subject column if present
        subject_ids = None
        if self.subject_column and self.subject_column in df.columns:
            subject_ids = df[self.subject_column]
        
        # Drop specified columns
        for col in self.drop_columns:
            if col in df.columns:
                df = df.drop(columns=[col])
                metadata['dropped_columns'].append(col)
        
        # Extract target
        if self.target_column not in df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found")
        
        y = df[self.target_column]
        X = df.drop(columns=[self.target_column])
        
        # Encode target for binary classification
        if self.positive_class:
            y = self._encode_target(y, self.positive_class)
        
        metadata['features'] = list(X.columns)
        metadata['samples'] = len(X)
        
        return X, y, metadata
    
    def _encode_target(self, y: pd.Series, positive_class: str) -> pd.Series:
        """Encode target to 0/1 for binary classification.
        
        Args:
            y: Target series
            positive_class: Value representing positive class
        
        Returns:
            Encoded target series (0/1)
        """
        return (y == positive_class).astype(int)


class BreastCancerAdapter(DatasetAdapter):
    """Adapter for Breast Cancer Wisconsin Diagnostic dataset."""
    
    @property
    def name(self) -> str:
        return "breast_cancer_wisconsin"
    
    @property
    def target_column(self) -> str:
        return "diagnosis"
    
    @property
    def drop_columns(self) -> List[str]:
        return ["id"]
    
    @property
    def positive_class(self) -> str:
        return "M"  # Malignant is positive class
    
    def detect(self, df: pd.DataFrame) -> bool:
        """Detect Breast Cancer dataset by column names."""
        required_cols = {'id', 'diagnosis', 'radius_mean', 'texture_mean'}
        return required_cols.issubset(set(df.columns))


class HeartDiseaseAdapter(DatasetAdapter):
    """Adapter for Heart Disease UCI dataset."""
    
    @property
    def name(self) -> str:
        return "heart_disease_uci"
    
    @property
    def target_column(self) -> str:
        return "target"
    
    @property
    def drop_columns(self) -> List[str]:
        return []  # No columns to drop
    
    @property
    def positive_class(self) -> Optional[str]:
        return None  # Already encoded as 0/1
    
    def detect(self, df: pd.DataFrame) -> bool:
        """Detect Heart Disease dataset by column names."""
        required_cols = {'age', 'sex', 'cp', 'trestbps', 'chol', 'target'}
        return required_cols.issubset(set(df.columns))


class ParkinsonsAdapter(DatasetAdapter):
    """Adapter for Parkinson's Disease dataset (Oxford)."""
    
    @property
    def name(self) -> str:
        return "parkinsons_oxford"
    
    @property
    def target_column(self) -> str:
        return "status"
    
    @property
    def drop_columns(self) -> List[str]:
        return ["name"]
    
    @property
    def subject_column(self) -> Optional[str]:
        return "name"  # Subject identifier for group-aware splitting
    
    @property
    def positive_class(self) -> Optional[str]:
        return None  # Already encoded as 0/1
    
    def detect(self, df: pd.DataFrame) -> bool:
        """Detect Parkinson's dataset by column names."""
        required_cols = {'name', 'MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'status'}
        return required_cols.issubset(set(df.columns))
    
    def adapt(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        """Adapt Parkinson's dataset with subject tracking.
        
        Important: Multiple recordings per subject, so we need
        to track subject IDs for group-aware splitting.
        """
        metadata = {
            'adapter': self.name,
            'target_column': self.target_column,
            'dropped_columns': [],
            'subject_column': self.subject_column
        }
        
        df = df.copy()
        
        # Extract subject IDs BEFORE dropping 'name' column
        subject_ids = None
        if self.subject_column and self.subject_column in df.columns:
            subject_ids = df[self.subject_column].copy()
            # Extract subject number from name (e.g., "phon_R01_S01_1" -> "R01_S01")
            # This groups all recordings from same subject together
            subject_ids = subject_ids.str.extract(r'(phon_)?([A-Z0-9]+_S[0-9]+)', expand=False)[1]
            metadata['unique_subjects'] = subject_ids.nunique()
        
        # Drop name column after extracting subject info
        for col in self.drop_columns:
            if col in df.columns:
                df = df.drop(columns=[col])
                metadata['dropped_columns'].append(col)
        
        # Extract target
        y = df[self.target_column]
        X = df.drop(columns=[self.target_column])
        
        metadata['features'] = list(X.columns)
        metadata['samples'] = len(X)
        metadata['subject_ids'] = subject_ids.tolist() if subject_ids is not None else None
        
        return X, y, metadata


class AdapterRegistry:
    """Registry for dataset adapters."""
    
    def __init__(self):
        self._adapters: List[DatasetAdapter] = [
            BreastCancerAdapter(),
            HeartDiseaseAdapter(),
            ParkinsonsAdapter(),
        ]
    
    def detect_adapter(self, df: pd.DataFrame) -> Optional[DatasetAdapter]:
        """Detect the appropriate adapter for a DataFrame.
        
        Args:
            df: DataFrame to check
        
        Returns:
            Matching adapter or None
        """
        for adapter in self._adapters:
            if adapter.detect(df):
                return adapter
        return None
    
    def get_adapter(self, name: str) -> Optional[DatasetAdapter]:
        """Get adapter by name.
        
        Args:
            name: Adapter name
        
        Returns:
            Adapter instance or None
        """
        for adapter in self._adapters:
            if adapter.name == name:
                return adapter
        return None
    
    def list_adapters(self) -> List[str]:
        """List all available adapter names."""
        return [adapter.name for adapter in self._adapters]
