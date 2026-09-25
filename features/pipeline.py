# features/pipeline.py
# Phase 6 — Feature Engineering Pipeline
# Responsibility: Convert cleaned dataset into model-ready arrays.
# Produces: FeaturePipelineResult (handoff to Piyush's model pipeline)
# Standalone version — no dependency on core/config.py or core/exceptions.py.

import uuid
import json
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.utils.class_weight import compute_class_weight

from config import CONFIG
from exceptions import FeatureEngineeringError
from schemas import FeaturePipelineResult
from features.reducer import DimensionalityReducer


class FeaturePipeline:
    """
    Converts a cleaned dataset into a FeaturePipelineResult.

    Steps:
    A. Separate features (X) and target (y)
    B. Encode target (string → int if needed)
    C. Train / test split (stratified or grouped for Parkinson's)
    D. Encode categorical features (one-hot)
    E. Scale numerical features (StandardScaler by default)
    F. Compute class weights (informational)
    G. Apply PCA via DimensionalityReducer
    H. Save artifacts to disk
    I. Return FeaturePipelineResult
    """

    def __init__(self, dataset_name: str = None):
        """
        Parameters
        ----------
        dataset_name : str, optional
            Used to look up target column, grouped split settings,
            and target encoding from config.
        """
        self.dataset_name = dataset_name
        self._cfg         = CONFIG["feature_pipeline"]
        self._reducer_cfg = CONFIG["reducer"]
        self._scaler      = None

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def fit_transform(
        self,
        df: pd.DataFrame,
        experiment_id: str = None,
        target_col: str = None,
        original_df: pd.DataFrame = None,
    ) -> FeaturePipelineResult:
        """
        Run the full feature engineering pipeline.

        Parameters
        ----------
        df : pd.DataFrame
            Cleaned dataset from DataPreprocessor.
        experiment_id : str, optional
            Used for artifact storage path. Auto-generated if None.
        target_col : str, optional
            Override target column name. If None, detected from config/profiler.

        Returns
        -------
        FeaturePipelineResult
            Fully populated result object ready for Piyush's model pipeline.

        Raises
        ------
        FeatureEngineeringError
            If pipeline fails.
        """
        try:
            if experiment_id is None:
                experiment_id = "EXP-" + uuid.uuid4().hex[:8].upper()

            preprocessing_id = "PREP-" + uuid.uuid4().hex[:8].upper()

            # Step A: Determine target column
            target_col = self._resolve_target_col(df, target_col)

            # Step B: Separate X and y
            X_raw, y_raw = self._separate_features_target(df, target_col)

            # Step C: Encode target (M/B → 1/0 etc.)
            y = self._encode_target(y_raw)

            # Step D: Encode categorical features
            X_encoded, feature_names = self._encode_categorical(X_raw)

            # Step E: Train / test split
            X_train_raw, X_test_raw, y_train, y_test, split_strategy = \
                self._split_data(X_encoded, y, original_df if original_df is not None else df, target_col)

            # Step F: Scale features (fit on train, transform test)
            X_train_scaled, X_test_scaled = self._scale_features(X_train_raw, X_test_raw)

            # Step G: Compute class weights (informational)
            class_weights = self._compute_class_weights(y_train)

            # Step H: Apply PCA
            reducer = DimensionalityReducer()
            X_train_reduced, X_test_reduced, pca_meta = reducer.fit_transform(
                X_train_scaled, X_test_scaled
            )

            reduced_feature_names = [f"PC{i+1}" for i in range(X_train_reduced.shape[1])]

            # Build result
            result = FeaturePipelineResult(
                X_train=X_train_scaled,
                X_test=X_test_scaled,
                y_train=y_train,
                y_test=y_test,
                X_train_reduced=X_train_reduced,
                X_test_reduced=X_test_reduced,
                feature_names=feature_names,
                reduced_feature_names=reduced_feature_names,
                n_components=pca_meta["n_components"],
                variance_retained=pca_meta["variance_retained"],
                preprocessing_id=preprocessing_id,
                split_strategy=split_strategy,
                test_size=self._cfg["test_size"],
                random_state=self._cfg["random_state"],
                class_weights=class_weights,
            )

            # Step I: Save artifacts to disk
            self._save_artifacts(result, experiment_id)

            return result

        except FeatureEngineeringError:
            raise
        except Exception as e:
            raise FeatureEngineeringError(f"Feature pipeline failed: {e}") from e

    # ──────────────────────────────────────────────────────────────────────────
    # Private steps
    # ──────────────────────────────────────────────────────────────────────────

    def _resolve_target_col(self, df: pd.DataFrame, override: str) -> str:
        """Determine target column from override, config, or auto-detection."""
        if override and override in df.columns:
            return override

        # Config lookup
        if self.dataset_name:
            cfg_target = self._cfg["target_columns"].get(self.dataset_name)
            if cfg_target and cfg_target in df.columns:
                return cfg_target

        # Auto-detect common names
        common = ["target", "label", "class", "diagnosis", "outcome",
                  "Outcome", "status", "y"]
        for name in common:
            if name in df.columns:
                return name

        # Fallback: last column
        return df.columns[-1]

    def _separate_features_target(self, df, target_col):
        """Split DataFrame into X and y."""
        if target_col not in df.columns:
            raise FeatureEngineeringError(f"Target column '{target_col}' not found in DataFrame.")

        y = df[target_col].copy()
        X = df.drop(columns=[target_col])
        return X, y

    def _encode_target(self, y: pd.Series) -> np.ndarray:
        """Encode target to integer labels."""
        # Check if dataset-specific encoding is configured
        if self.dataset_name:
            encoding_map = self._cfg.get("target_encoding", {}).get(self.dataset_name)
            if encoding_map:
                y = y.map(encoding_map)

        # If still non-numeric, use LabelEncoder
        if not pd.api.types.is_numeric_dtype(y):
            le = LabelEncoder()
            y  = le.fit_transform(y.astype(str))
        else:
            y = y.values

        return y.astype(np.int64)

    def _encode_categorical(self, X: pd.DataFrame):
        """One-hot encode categorical columns."""
        cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

        if cat_cols:
            X = pd.get_dummies(X, columns=cat_cols, drop_first=False)

        feature_names = X.columns.tolist()
        return X, feature_names

    def _split_data(self, X, y, df_original, target_col):
        """
        Split into train/test.
        Uses GroupShuffleSplit for Parkinson's (patient-level split).
        Uses StratifiedShuffleSplit for all others.
        """
        test_size    = self._cfg["test_size"]
        random_state = self._cfg["random_state"]

        # Check if grouped split is needed
        grouped_split_datasets = self._cfg.get("grouped_split_datasets", {})
        group_col = grouped_split_datasets.get(self.dataset_name) if self.dataset_name else None

        # Convert X to numpy for splitting
        X_arr = X.values.astype(np.float64) if isinstance(X, pd.DataFrame) else X
        y_arr = y if isinstance(y, np.ndarray) else np.array(y)

        if group_col and group_col in df_original.columns and len(df_original) == len(X_arr):
            # GroupShuffleSplit — ensures same patient not in both train and test
            groups = df_original[group_col].values
            gss    = GroupShuffleSplit(
                n_splits=1,
                test_size=test_size,
                random_state=random_state,
            )
            train_idx, test_idx = next(gss.split(X_arr, y_arr, groups=groups))
            X_train = X_arr[train_idx]
            X_test  = X_arr[test_idx]
            y_train = y_arr[train_idx]
            y_test  = y_arr[test_idx]
            split_strategy = "grouped"
        else:
            # Stratified split — preserves class distribution
            X_train, X_test, y_train, y_test = train_test_split(
                X_arr, y_arr,
                test_size=test_size,
                stratify=y_arr,
                random_state=random_state,
            )
            split_strategy = "stratified"

        return (
            X_train.astype(np.float64),
            X_test.astype(np.float64),
            y_train.astype(np.int64),
            y_test.astype(np.int64),
            split_strategy,
        )

    def _scale_features(self, X_train, X_test):
        """
        Scale features.
        CRITICAL: fit on train only, transform test with fitted scaler.
        This prevents data leakage.
        """
        scaler_type = self._cfg.get("scaler", "standard")

        if scaler_type == "minmax":
            self._scaler = MinMaxScaler()
        else:
            self._scaler = StandardScaler()

        X_train_scaled = self._scaler.fit_transform(X_train)
        X_test_scaled  = self._scaler.transform(X_test)

        return X_train_scaled.astype(np.float64), X_test_scaled.astype(np.float64)

    def _compute_class_weights(self, y_train: np.ndarray) -> dict:
        """Compute balanced class weights (informational only)."""
        classes = np.unique(y_train)
        weights = compute_class_weight("balanced", classes=classes, y=y_train)
        return {int(cls): round(float(w), 4) for cls, w in zip(classes, weights)}

    def _save_artifacts(self, result: FeaturePipelineResult, experiment_id: str):
        """
        Save all arrays and metadata to disk.
        Required by Radha's explainability engine (Phase 12).
        """
        base_dir = CONFIG["artifacts"]["base_dir"]
        data_dir = os.path.join(base_dir, experiment_id, "data")
        os.makedirs(data_dir, exist_ok=True)

        # Save numpy arrays
        np.save(os.path.join(data_dir, "X_train.npy"),         result.X_train)
        np.save(os.path.join(data_dir, "X_test.npy"),          result.X_test)
        np.save(os.path.join(data_dir, "X_train_reduced.npy"), result.X_train_reduced)
        np.save(os.path.join(data_dir, "X_test_reduced.npy"),  result.X_test_reduced)
        np.save(os.path.join(data_dir, "y_train.npy"),         result.y_train)
        np.save(os.path.join(data_dir, "y_test.npy"),          result.y_test)

        # Save feature names
        with open(os.path.join(data_dir, "feature_names.json"), "w") as f:
            json.dump(result.feature_names, f)

        # Save pipeline metadata
        with open(os.path.join(data_dir, "pipeline_metadata.json"), "w") as f:
            json.dump(result.to_dict(), f, indent=2)
