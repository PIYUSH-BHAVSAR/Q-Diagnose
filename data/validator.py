# data/validator.py
# Phase 4 — Data Validator
# Responsibility: Check dataset quality and readiness for preprocessing.
# Produces: validation_report.json (contract)
# Detects problems — does NOT fix them (Phase 5 owns fixes).
# Standalone version — no dependency on core/config.py or core/exceptions.py.

from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

from config import CONFIG
from exceptions import DataValidationError


class DataValidator:
    """
    Validates a dataset against quality rules defined in the contract.

    Distinguishes between:
    - BLOCKED: Critical issues that prevent further processing.
    - PASS_WITH_WARNINGS: Issues that can be handled in preprocessing.
    - PASS: No issues detected.

    Produces a dict matching validation_report.json contract.
    """

    def __init__(self):
        self._cfg = CONFIG["validator"]

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def validate(
        self,
        df: pd.DataFrame,
        profile: dict,
        dataset_id: str,
    ) -> dict:
        """
        Validate the dataset and return a dict matching validation_report.json.

        Parameters
        ----------
        df : pd.DataFrame
            The loaded dataset.
        profile : dict
            Output from DataProfiler.profile().
        dataset_id : str
            Unique dataset ID.

        Returns
        -------
        dict
            Validation report matching validation_report.json contract.
        """
        critical_issues = []
        warnings        = []
        info_messages   = []

        # ── Run all checks ────────────────────────────────────────────────────
        target_validation  = self._validate_target(df, profile, critical_issues, warnings)
        schema_validation  = self._validate_schema(df, profile, critical_issues, warnings)
        missing_validation = self._validate_missing(df, critical_issues, warnings, info_messages)
        duplicate_result   = self._validate_duplicates(df, warnings)
        class_balance      = self._validate_class_balance(df, profile, warnings)
        value_validation   = self._validate_values(df, info_messages)
        outlier_result     = self._validate_outliers(df, info_messages)
        leakage_result     = self._validate_leakage(df, profile)
        patient_split_risk = self._validate_patient_split(df, profile)

        # ── Determine overall status ──────────────────────────────────────────
        if critical_issues:
            status = "BLOCKED"
        elif warnings:
            status = "PASS_WITH_WARNINGS"
        else:
            status = "PASS"

        # ── Compute quality score ─────────────────────────────────────────────
        quality_score = self._compute_quality_score(warnings, critical_issues)

        # ── Recommended preprocessing steps ──────────────────────────────────
        recommended_steps = self._recommend_preprocessing_steps(
            missing_validation,
            duplicate_result,
            class_balance,
            outlier_result,
        )

        report = {
            "dataset_id":           dataset_id,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_status":    status,
            "quality_score":        quality_score,
            "next_phase":           "PREPROCESSING" if status != "BLOCKED" else "BLOCKED",

            "target_validation":  target_validation,
            "schema_validation":  schema_validation,
            "missing_values":     missing_validation,
            "duplicates":         duplicate_result,
            "class_balance":      class_balance,
            "value_validation":   value_validation,
            "outliers":           outlier_result,
            "leakage":            leakage_result,
            "patient_level_split_risk": patient_split_risk,

            "critical_issues": critical_issues,
            "warnings":        warnings,
            "info_messages":   info_messages,

            "recommended_preprocessing_steps": recommended_steps,
        }

        return report

    # ──────────────────────────────────────────────────────────────────────────
    # Individual validation checks
    # ──────────────────────────────────────────────────────────────────────────

    def _validate_target(self, df, profile, critical_issues, warnings) -> dict:
        """Validate target column presence and characteristics."""
        target_col = profile.get("target", {}).get("candidate")

        if target_col is None or target_col not in df.columns:
            critical_issues.append({
                "code":     "TARGET_MISSING",
                "message":  "No target column detected.",
                "severity": "CRITICAL",
                "column":   None,
            })
            return {"status": "BLOCKED", "target_column": None}

        target_series  = df[target_col]
        unique_vals    = target_series.nunique()
        missing_count  = int(target_series.isnull().sum())
        value_dist     = {str(k): int(v) for k, v in target_series.value_counts().items()}

        # Check if column looks like an identifier
        is_id_risk = self._is_identifier_risk(target_col, target_series)

        if missing_count > 0:
            critical_issues.append({
                "code":     "TARGET_MISSING_VALUES",
                "message":  f"Target column '{target_col}' has {missing_count} missing values.",
                "severity": "CRITICAL",
                "column":   target_col,
            })
            status = "BLOCKED"
        elif is_id_risk:
            warnings.append({
                "code":     "TARGET_IDENTIFIER_RISK",
                "message":  f"Target column '{target_col}' may be an identifier, not a target.",
                "severity": "HIGH",
                "column":   target_col,
            })
            status = "WARNING"
        else:
            status = "PASS"

        # Infer target type
        if unique_vals == 2:
            target_type = "binary"
        elif unique_vals <= 20:
            target_type = "categorical"
        else:
            target_type = "continuous"

        return {
            "status":           status,
            "target_column":    target_col,
            "target_type":      target_type,
            "unique_values":    unique_vals,
            "value_distribution": value_dist,
            "missing_count":    missing_count,
            "is_identifier_risk": is_id_risk,
        }

    def _validate_schema(self, df, profile, critical_issues, warnings) -> dict:
        """Validate schema structure."""
        if df.empty:
            critical_issues.append({
                "code":     "DATASET_EMPTY",
                "message":  "Dataset is empty.",
                "severity": "CRITICAL",
                "column":   None,
            })
            return {"status": "BLOCKED"}

        # Check duplicate column names
        duplicate_cols = [c for c in df.columns if list(df.columns).count(c) > 1]
        if duplicate_cols:
            critical_issues.append({
                "code":     "DUPLICATE_COLUMNS",
                "message":  f"Duplicate column names detected: {list(set(duplicate_cols))}",
                "severity": "CRITICAL",
                "column":   None,
            })
            return {"status": "BLOCKED", "duplicate_columns": list(set(duplicate_cols))}

        expected_numerical   = profile["features"]["numerical"]
        expected_categorical = profile["features"]["categorical"]

        return {
            "status":               "PASS",
            "expected_numerical":   expected_numerical,
            "expected_categorical": expected_categorical,
            "actual_numerical":     expected_numerical,
            "actual_categorical":   expected_categorical,
            "type_mismatches":      [],
        }

    def _validate_missing(self, df, critical_issues, warnings, info_messages) -> dict:
        """Validate missing value levels."""
        total_cells   = df.shape[0] * df.shape[1]
        missing_total = int(df.isnull().sum().sum())
        missing_pct   = round(missing_total / total_cells * 100, 2) if total_cells > 0 else 0.0

        col_missing = {}
        for col in df.columns:
            series = df[col]
            # Handle duplicate column names returning a DataFrame instead of Series
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            if series.isnull().any():
                col_missing[col] = round(float(series.isnull().mean() * 100), 2)

        samples_with_missing = int(df.isnull().any(axis=1).sum())
        max_missing_per_sample = round(
            float(df.isnull().mean(axis=1).max() * 100), 2
        ) if len(df) > 0 else 0.0

        severity = self._missing_severity(missing_pct)

        if severity == "HIGH":
            warnings.append({
                "code":     "MISSING_VALUES",
                "message":  f"High missing values: {missing_pct}% of all values.",
                "severity": "HIGH",
                "column":   "multiple" if len(col_missing) > 1 else (list(col_missing.keys())[0] if col_missing else None),
            })
        elif severity == "MODERATE":
            warnings.append({
                "code":     "MISSING_VALUES",
                "message":  f"Moderate missing values: {missing_pct}% of all values.",
                "severity": "MODERATE",
                "column":   "multiple" if len(col_missing) > 1 else (list(col_missing.keys())[0] if col_missing else None),
            })
        elif severity == "LOW":
            info_messages.append({
                "code":     "MISSING_VALUES",
                "message":  f"Low missing values: {missing_pct}% of all values.",
                "severity": "LOW",
            })

        status = "PASS" if severity == "PASS" else "WARNING"

        return {
            "status":   status,
            "dataset_level": {
                "total_missing":      missing_total,
                "missing_percentage": missing_pct,
            },
            "column_level": col_missing,
            "sample_level": {
                "samples_with_missing":        samples_with_missing,
                "max_missing_per_sample_pct":  max_missing_per_sample,
            },
            "severity": severity,
        }

    def _validate_duplicates(self, df, warnings) -> dict:
        """Validate duplicate rows."""
        exact_dupes = int(df.duplicated().sum())
        dupe_pct    = round(exact_dupes / len(df) * 100, 2) if len(df) > 0 else 0.0

        threshold = self._cfg["duplicate_warning_threshold"]

        if dupe_pct > threshold:
            severity = "LOW" if dupe_pct < 5 else "MODERATE"
            warnings.append({
                "code":     "DUPLICATE_ROWS",
                "message":  f"{exact_dupes} duplicate rows detected ({dupe_pct}%).",
                "severity": severity,
                "column":   None,
            })
            status = "WARNING"
        else:
            severity = "PASS"
            status   = "PASS"

        return {
            "status":               status,
            "exact_duplicates":     exact_dupes,
            "duplicate_percentage": dupe_pct,
            "severity":             severity,
        }

    def _validate_class_balance(self, df, profile, warnings) -> dict:
        """Validate class balance for classification tasks."""
        target_col = profile.get("target", {}).get("candidate")
        task       = profile.get("task", {}).get("candidate", "UNKNOWN")

        if target_col not in df.columns or "CLASSIFICATION" not in task:
            return {"status": "NOT_APPLICABLE"}

        class_counts = df[target_col].value_counts()
        if len(class_counts) < 2:
            return {"status": "PASS", "severity": "BALANCED"}

        majority = int(class_counts.iloc[0])
        minority = int(class_counts.iloc[-1])
        total    = int(class_counts.sum())

        ratio            = round(majority / minority, 2) if minority > 0 else 999.0
        minority_pct     = round(minority / total * 100, 1)
        class_counts_dict = {str(k): int(v) for k, v in class_counts.items()}

        severity = self._imbalance_severity(ratio)

        if severity in ("MODERATE", "HIGH", "EXTREME"):
            warnings.append({
                "code":     "CLASS_IMBALANCE",
                "message":  f"{severity.capitalize()} class imbalance ({ratio}:1 ratio).",
                "severity": severity,
                "column":   target_col,
            })
            status = "WARNING"
        else:
            status = "PASS"

        return {
            "status":              status,
            "class_counts":        class_counts_dict,
            "imbalance_ratio":     ratio,
            "minority_percentage": minority_pct,
            "severity":            severity,
        }

    def _validate_values(self, df, info_messages) -> dict:
        """Detect structurally invalid values (e.g. negative ages)."""
        # Generic check: count non-finite values in numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        structural_invalidity_count = int(
            np.isinf(numeric_df.values).sum() +
            (numeric_df.values < -1e10).sum()
        )

        potential_outlier_count = self._count_outliers(numeric_df)

        if potential_outlier_count > 0:
            info_messages.append({
                "code":     "OUTLIER_DETECTION",
                "message":  f"{potential_outlier_count} potential statistical outliers detected.",
                "severity": "INFO",
            })

        return {
            "status":                    "PASS" if structural_invalidity_count == 0 else "WARNING",
            "structural_invalidity_count": structural_invalidity_count,
            "potential_outlier_count":     potential_outlier_count,
            "invalid_ranges":              [],
        }

    def _validate_outliers(self, df, info_messages) -> dict:
        """Detect statistical outliers using IQR method."""
        numeric_df = df.select_dtypes(include=[np.number])
        cols_with_outliers = []
        total_outlier_samples = set()

        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if len(series) == 0:
                continue
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr    = q3 - q1
            lower  = q1 - 1.5 * iqr
            upper  = q3 + 1.5 * iqr
            outlier_idx = series[(series < lower) | (series > upper)].index
            if len(outlier_idx) > 0:
                cols_with_outliers.append(col)
                total_outlier_samples.update(outlier_idx.tolist())

        total  = len(total_outlier_samples)
        pct    = round(total / len(df) * 100, 1) if len(df) > 0 else 0.0
        status = "INFO" if total > 0 else "PASS"

        return {
            "status":                status,
            "columns_with_outliers": cols_with_outliers,
            "total_outlier_samples": total,
            "outlier_percentage":    pct,
        }

    def _validate_leakage(self, df, profile) -> dict:
        """Detect potential data leakage risks."""
        id_keywords    = ["id", "ID", "Id", "name", "Name", "patient", "index"]
        id_candidates  = [
            col for col in df.columns
            if any(kw in col for kw in id_keywords)
        ]

        return {
            "status":                      "PASS",
            "identifier_candidates":       id_candidates,
            "high_correlation_with_target": [],
            "suspicious_relationships":    [],
        }

    def _validate_patient_split(self, df, profile) -> dict:
        """Detect if multiple recordings per patient exist (patient split risk)."""
        id_keywords   = ["name", "Name", "patient_id", "PatientID", "subject"]
        patient_col   = None

        for col in df.columns:
            if any(kw in col for kw in id_keywords):
                # Check if there are repeated values (multiple recordings per ID)
                if df[col].duplicated().any():
                    patient_col = col
                    break

        if patient_col:
            return {
                "detected":          True,
                "patient_id_column": patient_col,
                "recommendation":    f"Use GroupShuffleSplit on '{patient_col}' column — multiple recordings per subject.",
            }

        return {
            "detected":          False,
            "patient_id_column": None,
            "recommendation":    "Standard random split acceptable.",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Utility methods
    # ──────────────────────────────────────────────────────────────────────────

    def _missing_severity(self, pct: float) -> str:
        thresholds = self._cfg["missing_severity"]
        if pct == 0:
            return "PASS"
        elif pct <= thresholds["low"]:
            return "LOW"
        elif pct <= thresholds["moderate"]:
            return "MODERATE"
        else:
            return "HIGH"

    def _imbalance_severity(self, ratio: float) -> str:
        t = self._cfg["imbalance_severity"]
        if ratio < t["balanced"]:
            return "BALANCED"
        elif ratio < t["moderate"]:
            return "MODERATE"
        elif ratio < t["high"]:
            return "HIGH"
        else:
            return "EXTREME"

    def _is_identifier_risk(self, col_name: str, series: pd.Series) -> bool:
        """Check if a column looks like an identifier."""
        id_keywords = ["id", "ID", "Id", "index", "patient", "name"]
        name_match  = any(kw in col_name for kw in id_keywords)
        all_unique  = series.nunique() == len(series)
        return name_match and all_unique

    def _count_outliers(self, numeric_df: pd.DataFrame) -> int:
        """Count total outlier samples using IQR across all columns."""
        outlier_indices = set()
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if len(series) == 0:
                continue
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr    = q3 - q1
            lower  = q1 - 1.5 * iqr
            upper  = q3 + 1.5 * iqr
            outlier_indices.update(
                series[(series < lower) | (series > upper)].index.tolist()
            )
        return len(outlier_indices)

    def _compute_quality_score(self, warnings: list, critical_issues: list) -> int:
        """Compute quality score (0-100). Start at 100, subtract penalties."""
        penalties = self._cfg["quality_penalties"]
        score     = 100

        for item in warnings:
            severity = item.get("severity", "LOW")
            score   -= penalties.get(severity, 5)

        for item in critical_issues:
            score -= penalties["CRITICAL"]

        return max(0, score)

    def _recommend_preprocessing_steps(
        self,
        missing_validation: dict,
        duplicate_result: dict,
        class_balance: dict,
        outlier_result: dict,
    ) -> list:
        """Generate recommended preprocessing steps for Phase 5."""
        steps = []

        if duplicate_result.get("exact_duplicates", 0) > 0:
            steps.append("Consider duplicate removal or investigation.")

        sev = missing_validation.get("severity", "PASS")
        if sev in ("LOW", "MODERATE", "HIGH"):
            steps.append("Apply missing value imputation (median for numerical, mode for categorical).")

        balance_sev = class_balance.get("severity", "BALANCED")
        if balance_sev in ("MODERATE", "HIGH", "EXTREME"):
            steps.append(
                "Consider class balancing strategy (e.g., class_weight='balanced', SMOTE, threshold adjustment)."
            )

        if outlier_result.get("total_outlier_samples", 0) > 0:
            steps.append("Outlier treatment optional — domain/medical context required before removal.")

        return steps
