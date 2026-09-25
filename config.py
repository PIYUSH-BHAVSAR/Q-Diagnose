# config.py
# Standalone pipeline configuration for Q-Diagnose phases 2-6.
# During team integration, replace with: from core.config import config

CONFIG = {

    # ── Adapter settings ──────────────────────────────────────────────────────
    "adapter": {
        # Columns to drop before processing (identifiers, not features)
        "drop_columns": {
            "breast_cancer": ["id"],
            "parkinsons":    ["name"],
        },
        # Supported file formats
        "supported_formats": ["csv", "json"],
    },

    # ── Profiler settings ─────────────────────────────────────────────────────
    "profiler": {
        # Threshold for detecting a column as categorical
        "categorical_unique_threshold": 20,
        # Modality detection (only TABULAR supported for now)
        "modality": "TABULAR",
    },

    # ── Validator settings ────────────────────────────────────────────────────
    "validator": {
        # Missing value severity thresholds (percentage)
        "missing_severity": {
            "low":      5.0,
            "moderate": 20.0,
            # above moderate → HIGH
        },
        # Class imbalance ratio thresholds
        "imbalance_severity": {
            "balanced": 1.5,
            "moderate": 3.0,
            "high":     10.0,
            # above high → EXTREME
        },
        # Duplicate percentage threshold for WARNING
        "duplicate_warning_threshold": 1.0,
        # Quality score penalties
        "quality_penalties": {
            "LOW":      5,
            "MODERATE": 10,
            "HIGH":     20,
            "CRITICAL": 40,
        },
    },

    # ── Preprocessing settings ────────────────────────────────────────────────
    "preprocessing": {
        # Strategy for numerical missing values: "median" or "mean"
        "numerical_imputation":   "median",
        # Strategy for categorical missing values: "mode"
        "categorical_imputation": "mode",
        # Whether to remove duplicate rows
        "remove_duplicates": True,
        # Datasets with biologically impossible zeros treated as missing
        "zero_as_missing_columns": {
            "diabetes": [
                "Glucose",
                "BloodPressure",
                "SkinThickness",
                "Insulin",
                "BMI",
            ],
        },
    },

    # ── Feature pipeline settings ─────────────────────────────────────────────
    "feature_pipeline": {
        # Train / test split ratio
        "test_size":    0.20,
        "random_state": 42,
        # Scaler to apply: "standard" (StandardScaler) or "minmax" (MinMaxScaler)
        "scaler": "standard",
        # Target column names per dataset
        "target_columns": {
            "breast_cancer": "diagnosis",
            "heart_disease": "target",
            "diabetes":      "Outcome",
            "parkinsons":    "status",
        },
        # Datasets that require GroupShuffleSplit (multiple recordings per patient)
        "grouped_split_datasets": {
            "parkinsons": "name",   # group column
        },
        # Binary target encoding map (for string targets like M/B)
        "target_encoding": {
            "breast_cancer": {"M": 1, "B": 0},
        },
    },

    # ── PCA / Dimensionality reduction settings ───────────────────────────────
    "reducer": {
        # Default number of PCA components for quantum representation
        "n_components": 8,
        "random_state": 42,
    },

    # ── Artifact storage ──────────────────────────────────────────────────────
    "artifacts": {
        "base_dir": "artifacts/experiments",
    },
}
