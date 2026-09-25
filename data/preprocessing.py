# data/preprocessing.py
# Phase 5 — Data Preprocessing
# Responsibility: Clean and prepare the dataset after validation.
# Fixes the issues detected by the validator.
# Standalone version — no dependency on core/config.py or core/exceptions.py.

import pandas as pd
import numpy as np

from config import CONFIG
from exceptions import PreprocessingError


class DataPreprocessor:
    """
    Cleans and prepares a validated dataset for feature engineering.

    Steps performed:
    A. Replace biologically impossible zeros with NaN (dataset-specific)
    B. Remove duplicate rows
    C. Handle missing values (median for numerical, mode for categorical)
    D. Data type conversion
    E. Record preprocessing summary

    Does NOT remove outliers automatically.
    Does NOT apply scaling (that is Feature Pipeline's responsibility).
    """

    def __init__(self, dataset_name: str = None):
        """
        Parameters
        ----------
        dataset_name : str, optional
            Used to apply dataset-specific rules (e.g. zero-as-missing for diabetes).
        """
        self.dataset_name = dataset_name
        self._cfg         = CONFIG["preprocessing"]

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def preprocess(
        self,
        df: pd.DataFrame,
        validation_report: dict,
    ) -> tuple:
        """
        Clean and prepare the dataset.

        Parameters
        ----------
        df : pd.DataFrame
            Validated dataset.
        validation_report : dict
            Output from DataValidator.validate() — used to guide decisions.

        Returns
        -------
        tuple : (pd.DataFrame, dict)
            - Cleaned DataFrame
            - Preprocessing summary dict

        Raises
        ------
        PreprocessingError
            If preprocessing fails unexpectedly.
        """
        try:
            # Check if pipeline is blocked
            if validation_report.get("validation_status") == "BLOCKED":
                raise PreprocessingError(
                    "Cannot preprocess: validation status is BLOCKED. "
                    f"Critical issues: {validation_report.get('critical_issues', [])}"
                )

            summary = {
                "rows_before":           int(df.shape[0]),
                "columns_before":        int(df.shape[1]),
                "duplicates_removed":    0,
                "missing_values_before": int(df.isnull().sum().sum()),
                "missing_values_after":  0,
                "transformations":       [],
            }

            # Step A: Replace impossible zeros with NaN
            df = self._handle_impossible_zeros(df, summary)

            # Step B: Remove duplicates
            if self._cfg["remove_duplicates"]:
                df = self._remove_duplicates(df, summary)

            # Step C: Impute missing values
            df = self._impute_missing(df, summary)

            # Step D: Convert data types
            df = self._convert_dtypes(df, summary)

            summary["rows_after"]          = int(df.shape[0])
            summary["columns_after"]       = int(df.shape[1])
            summary["missing_values_after"] = int(df.isnull().sum().sum())

            return df, summary

        except PreprocessingError:
            raise
        except Exception as e:
            raise PreprocessingError(f"Preprocessing failed: {e}") from e

    # ──────────────────────────────────────────────────────────────────────────
    # Private steps
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_impossible_zeros(self, df: pd.DataFrame, summary: dict) -> pd.DataFrame:
        """
        Replace biologically impossible zero values with NaN.
        Only applied to datasets defined in config zero_as_missing_columns.
        Example: Glucose=0 in diabetes dataset is biologically impossible.
        """
        if self.dataset_name is None:
            return df

        zero_cols = self._cfg["zero_as_missing_columns"].get(self.dataset_name, [])
        cols_found = [c for c in zero_cols if c in df.columns]

        if cols_found:
            zeros_replaced = 0
            for col in cols_found:
                count = int((df[col] == 0).sum())
                if count > 0:
                    df[col] = df[col].replace(0, np.nan)
                    zeros_replaced += count

            if zeros_replaced > 0:
                summary["transformations"].append(
                    f"Replaced {zeros_replaced} biologically impossible zeros "
                    f"with NaN in columns: {cols_found}"
                )

        return df

    def _remove_duplicates(self, df: pd.DataFrame, summary: dict) -> pd.DataFrame:
        """Remove exact duplicate rows."""
        before = len(df)
        df     = df.drop_duplicates().reset_index(drop=True)
        removed = before - len(df)

        summary["duplicates_removed"] = removed
        if removed > 0:
            summary["transformations"].append(
                f"Removed {removed} duplicate rows."
            )

        return df

    def _impute_missing(self, df: pd.DataFrame, summary: dict) -> pd.DataFrame:
        """
        Impute missing values.
        - Numerical: median (robust to outliers)
        - Categorical / object: mode
        """
        numerical_strategy   = self._cfg["numerical_imputation"]
        categorical_strategy = self._cfg["categorical_imputation"]

        cols_imputed = []

        for col in df.columns:
            missing_count = int(df[col].isnull().sum())
            if missing_count == 0:
                continue

            if pd.api.types.is_numeric_dtype(df[col]):
                if numerical_strategy == "median":
                    fill_val = df[col].median()
                else:
                    fill_val = df[col].mean()
                df[col] = df[col].fillna(fill_val)
                cols_imputed.append(
                    f"{col} ({missing_count} values, {numerical_strategy}={round(float(fill_val), 4)})"
                )

            else:
                mode_vals = df[col].mode()
                if len(mode_vals) > 0:
                    fill_val = mode_vals.iloc[0]
                    df[col] = df[col].fillna(fill_val)
                    cols_imputed.append(
                        f"{col} ({missing_count} values, mode='{fill_val}')"
                    )

        if cols_imputed:
            summary["transformations"].append(
                f"Imputed missing values in: {cols_imputed}"
            )

        return df

    def _convert_dtypes(self, df: pd.DataFrame, summary: dict) -> pd.DataFrame:
        """
        Convert columns to appropriate data types.
        - Numeric-looking object columns → numeric
        - Ensure no object columns remain in numerical-only datasets
        """
        converted = []

        for col in df.columns:
            if df[col].dtype == object:
                # Try converting to numeric
                converted_series = pd.to_numeric(df[col], errors="ignore")
                if converted_series.dtype != object:
                    df[col] = converted_series
                    converted.append(col)

        if converted:
            summary["transformations"].append(
                f"Converted to numeric dtype: {converted}"
            )

        return df
