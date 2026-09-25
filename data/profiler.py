# data/profiler.py
# Phase 3 — Data Profiler
# Responsibility: Understand the structure and characteristics of the dataset.
# Produces: dataset_profile.json (contract)
# Standalone version — no dependency on core/config.py or core/exceptions.py.

import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

from config import CONFIG
from exceptions import ProfilingError


class DataProfiler:
    """
    Profiles a pandas DataFrame and produces a dataset_profile dict
    matching the dataset_profile.json contract.

    The profiler is fully generic — no hardcoded column names or dataset
    specific logic. It detects modality, dimensions, feature types,
    missing values, duplicates, target candidate, and class distribution.
    """

    def __init__(self):
        self._cfg = CONFIG["profiler"]
        self._profile_counter = 0

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def profile(self, df: pd.DataFrame, dataset_id: str) -> dict:
        """
        Profile the dataset and return a dict matching dataset_profile.json.

        Parameters
        ----------
        df : pd.DataFrame
            The loaded dataset (after adapter processing).
        dataset_id : str
            Unique ID for this dataset (from dataset_upload_response.json).

        Returns
        -------
        dict
            Profile matching the dataset_profile.json contract.

        Raises
        ------
        ProfilingError
            If profiling fails due to unexpected data structure.
        """
        try:
            self._profile_counter += 1
            profile_id = f"PROFILE-{self._profile_counter:06d}"

            numerical_cols, categorical_cols = self._detect_column_types(df)
            target_candidate, target_confidence = self._detect_target(df)
            task_candidate, task_confidence   = self._infer_task(df, target_candidate)
            class_distribution                = self._get_class_distribution(df, target_candidate)
            missing_total, missing_pct, missing_by_col = self._get_missing_info(df)
            duplicate_count                   = int(df.duplicated().sum())
            warnings                          = self._generate_warnings(df, target_candidate, class_distribution)

            profile = {
                "dataset_id":  dataset_id,
                "profile_id":  profile_id,
                "modality":    self._cfg["modality"],

                "dimensions": {
                    "rows":    int(df.shape[0]),
                    "columns": int(df.shape[1]),
                },

                "features": {
                    "numerical":   len(numerical_cols),
                    "categorical": len(categorical_cols),
                    "numerical_columns":   numerical_cols,
                    "categorical_columns": categorical_cols,
                },

                "target": {
                    "candidate":  target_candidate,
                    "confidence": target_confidence,
                },

                "task": {
                    "candidate":  task_candidate,
                    "confidence": task_confidence,
                },

                "class_distribution": class_distribution,

                "missing_values": {
                    "total":      missing_total,
                    "percentage": round(missing_pct, 4),
                    "by_column":  missing_by_col,
                },

                "duplicates": {
                    "candidate_count": duplicate_count,
                },

                "warnings":    warnings,
                "status":      "PROFILED",
                "profiled_at": datetime.now(timezone.utc).isoformat(),
            }

            return profile

        except ProfilingError:
            raise
        except Exception as e:
            raise ProfilingError(f"Profiling failed: {e}") from e

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _detect_column_types(self, df: pd.DataFrame):
        """Separate columns into numerical and categorical."""
        numerical_cols   = []
        categorical_cols = []

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                unique_count = df[col].nunique()
                # Low unique numerical → treat as categorical (e.g. binary flags)
                if unique_count <= self._cfg["categorical_unique_threshold"]:
                    categorical_cols.append(col)
                else:
                    numerical_cols.append(col)
            else:
                categorical_cols.append(col)

        return numerical_cols, categorical_cols

    def _detect_target(self, df: pd.DataFrame):
        """
        Detect the most likely target column.
        Priority: common target names → last column fallback.
        """
        common_names = [
            "target", "label", "class", "diagnosis", "disease",
            "outcome", "Outcome", "status", "y", "response",
        ]

        for name in common_names:
            if name in df.columns:
                return name, "HIGH"

        # Fallback: last column
        last_col = df.columns[-1]
        return last_col, "LOW"

    def _infer_task(self, df: pd.DataFrame, target_col: Optional[str]):
        """Infer the ML task type from the target column."""
        if target_col is None or target_col not in df.columns:
            return "UNKNOWN", "LOW"

        unique_vals = df[target_col].nunique()

        if unique_vals == 2:
            return "BINARY_CLASSIFICATION", "HIGH"
        elif 2 < unique_vals <= 20:
            return "MULTICLASS_CLASSIFICATION", "MEDIUM"
        else:
            return "REGRESSION", "MEDIUM"

    def _get_class_distribution(self, df: pd.DataFrame, target_col: Optional[str]) -> dict:
        """Get class distribution for classification targets."""
        if target_col is None or target_col not in df.columns:
            return {}

        unique_vals = df[target_col].nunique()
        if unique_vals > 20:
            return {}

        dist = df[target_col].value_counts().to_dict()
        return {str(k): int(v) for k, v in dist.items()}

    def _get_missing_info(self, df: pd.DataFrame):
        """Calculate missing value statistics."""
        missing_by_col_raw = df.isnull().sum()
        missing_by_col     = {
            col: int(count)
            for col, count in missing_by_col_raw.items()
            if count > 0
        }
        total_cells  = df.shape[0] * df.shape[1]
        missing_total = int(missing_by_col_raw.sum())
        missing_pct   = (missing_total / total_cells * 100) if total_cells > 0 else 0.0

        return missing_total, missing_pct, missing_by_col

    def _generate_warnings(
        self,
        df: pd.DataFrame,
        target_col: Optional[str],
        class_distribution: dict,
    ) -> list:
        """Generate profile-level warnings."""
        warnings = []

        # Class imbalance warning
        if class_distribution and len(class_distribution) == 2:
            counts = list(class_distribution.values())
            majority = max(counts)
            minority = min(counts)
            total    = sum(counts)

            majority_pct = round(majority / total * 100, 1)
            minority_pct = round(minority / total * 100, 1)

            ratio = majority / minority if minority > 0 else float("inf")

            if ratio >= 3.0:
                warnings.append(
                    f"Severe class imbalance: {minority_pct}% vs {majority_pct}%"
                )
            elif ratio >= 1.5:
                warnings.append(
                    f"Class imbalance detected: {majority_pct}% vs {minority_pct}%"
                )

        # High missing values warning
        total_cells   = df.shape[0] * df.shape[1]
        missing_total = int(df.isnull().sum().sum())
        if total_cells > 0:
            missing_pct = missing_total / total_cells * 100
            if missing_pct > 20:
                warnings.append(f"High missing values: {round(missing_pct, 1)}% of all values")
            elif missing_pct > 5:
                warnings.append(f"Moderate missing values: {round(missing_pct, 1)}% of all values")

        return warnings
