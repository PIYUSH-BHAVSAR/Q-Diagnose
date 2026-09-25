# tests/test_pipeline.py
import os
import pytest
import numpy as np
import pandas as pd

from data.adapters import DataAdapter
from data.profiler import DataProfiler
from data.validator import DataValidator
from data.preprocessing import DataPreprocessor
from features.pipeline import FeaturePipeline
from schemas import FeaturePipelineResult

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def get_clean_df(name):
    adapter      = DataAdapter(dataset_name=name)
    profiler     = DataProfiler()
    validator    = DataValidator()
    preprocessor = DataPreprocessor(dataset_name=name)

    df      = adapter.load(os.path.join(FIXTURES, f"{name}.csv"))
    profile = profiler.profile(df, dataset_id=f"test-{name}")
    report  = validator.validate(df, profile, dataset_id=f"test-{name}")
    clean_df, _ = preprocessor.preprocess(df, report)
    return clean_df


class TestFeaturePipeline:

    def test_returns_feature_pipeline_result(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-001")
        assert isinstance(result, FeaturePipelineResult)

    def test_x_train_is_float64(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-002")
        assert result.X_train.dtype == np.float64

    def test_y_train_is_int64(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-003")
        assert result.y_train.dtype == np.int64

    def test_correct_split_ratio(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-004")
        total    = len(result.y_train) + len(result.y_test)
        test_pct = len(result.y_test) / total
        assert abs(test_pct - 0.20) < 0.05  # within 5% tolerance

    def test_feature_names_match_columns(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-005")
        assert len(result.feature_names) == result.X_train.shape[1]

    def test_reduced_feature_names_are_pc_labels(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-006")
        for i, name in enumerate(result.reduced_feature_names):
            assert name == f"PC{i+1}"

    def test_preprocessing_id_format(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-007")
        assert result.preprocessing_id.startswith("PREP-")
        assert len(result.preprocessing_id) == 13  # "PREP-" + 8 chars

    def test_class_weights_dict(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-008")
        assert isinstance(result.class_weights, dict)
        assert len(result.class_weights) == 2

    def test_stratified_split_strategy_diabetes(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-009")
        assert result.split_strategy == "stratified"

    def test_grouped_split_strategy_parkinsons(self):
        import pandas as pd
        adapter      = DataAdapter(dataset_name="parkinsons")
        profiler     = DataProfiler()
        validator    = DataValidator()
        preprocessor = DataPreprocessor(dataset_name="parkinsons")

        raw_df   = adapter.load(os.path.join(FIXTURES, "parkinsons.csv"))
        # Keep the original CSV (with 'name') aligned to clean df rows
        original_df = pd.read_csv(os.path.join(FIXTURES, "parkinsons.csv"))

        profile  = profiler.profile(raw_df, dataset_id="test-parkinsons")
        report   = validator.validate(raw_df, profile, dataset_id="test-parkinsons")
        clean_df, _ = preprocessor.preprocess(raw_df, report)

        # Align original_df to clean_df index (after duplicate removal)
        aligned_original = original_df.loc[clean_df.index].reset_index(drop=True)
        clean_df = clean_df.reset_index(drop=True)

        pipeline = FeaturePipeline(dataset_name="parkinsons")
        result   = pipeline.fit_transform(
            clean_df,
            experiment_id="EXP-TEST-010",
            original_df=aligned_original,
        )
        assert result.split_strategy == "grouped"

    def test_no_data_leakage_shapes(self):
        """X_test must be transformed with train-fitted scaler, not refitted."""
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-011")
        assert result.X_train.shape[1] == result.X_test.shape[1]

    def test_to_dict_serializable(self):
        import json
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        result   = pipeline.fit_transform(clean_df, experiment_id="EXP-TEST-012")
        d = result.to_dict()
        # Should be JSON serializable (no numpy types)
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_artifacts_saved_to_disk(self):
        clean_df = get_clean_df("diabetes")
        pipeline = FeaturePipeline(dataset_name="diabetes")
        exp_id   = "EXP-TEST-ARTIFACTS"
        result   = pipeline.fit_transform(clean_df, experiment_id=exp_id)

        data_dir = os.path.join("artifacts", "experiments", exp_id, "data")
        assert os.path.exists(os.path.join(data_dir, "X_train.npy"))
        assert os.path.exists(os.path.join(data_dir, "X_test.npy"))
        assert os.path.exists(os.path.join(data_dir, "y_train.npy"))
        assert os.path.exists(os.path.join(data_dir, "y_test.npy"))
        assert os.path.exists(os.path.join(data_dir, "feature_names.json"))
        assert os.path.exists(os.path.join(data_dir, "pipeline_metadata.json"))
