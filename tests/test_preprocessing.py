# tests/test_preprocessing.py
import os
import pytest
import pandas as pd
import numpy as np

from data.adapters import DataAdapter
from data.profiler import DataProfiler
from data.validator import DataValidator
from data.preprocessing import DataPreprocessor
from exceptions import PreprocessingError

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def get_pipeline(name):
    adapter   = DataAdapter(dataset_name=name)
    profiler  = DataProfiler()
    validator = DataValidator()
    df        = adapter.load(os.path.join(FIXTURES, f"{name}.csv"))
    profile   = profiler.profile(df, dataset_id=f"test-{name}")
    report    = validator.validate(df, profile, dataset_id=f"test-{name}")
    return df, report


class TestDataPreprocessor:

    def test_returns_dataframe_and_summary(self):
        df, report = get_pipeline("diabetes")
        preprocessor = DataPreprocessor(dataset_name="diabetes")
        clean_df, summary = preprocessor.preprocess(df, report)
        assert isinstance(clean_df, pd.DataFrame)
        assert isinstance(summary, dict)

    def test_no_missing_values_after_preprocessing(self):
        df, report = get_pipeline("diabetes")
        preprocessor = DataPreprocessor(dataset_name="diabetes")
        clean_df, summary = preprocessor.preprocess(df, report)
        assert clean_df.isnull().sum().sum() == 0

    def test_duplicates_removed(self):
        # Create a DataFrame with duplicates
        df = pd.DataFrame({
            "age": [25, 25, 30, 30, 35],
            "bmi": [22.5, 22.5, 28.0, 28.0, 31.5],
            "target": [0, 0, 1, 1, 0],
        })
        report = {"validation_status": "PASS_WITH_WARNINGS", "critical_issues": []}
        preprocessor = DataPreprocessor()
        clean_df, summary = preprocessor.preprocess(df, report)
        assert clean_df.duplicated().sum() == 0
        assert summary["duplicates_removed"] == 2

    def test_summary_has_required_fields(self):
        df, report = get_pipeline("diabetes")
        preprocessor = DataPreprocessor(dataset_name="diabetes")
        _, summary = preprocessor.preprocess(df, report)
        required = [
            "rows_before", "rows_after", "columns_before", "columns_after",
            "duplicates_removed", "missing_values_before", "missing_values_after",
            "transformations",
        ]
        for field in required:
            assert field in summary, f"Missing summary field: {field}"

    def test_impossible_zeros_replaced_diabetes(self):
        df, report = get_pipeline("diabetes")
        preprocessor = DataPreprocessor(dataset_name="diabetes")
        clean_df, summary = preprocessor.preprocess(df, report)
        # After imputation, columns like Glucose should have no zeros
        # (zeros were replaced by NaN then imputed)
        assert clean_df["Glucose"].min() > 0

    def test_blocked_status_raises(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        blocked_report = {
            "validation_status": "BLOCKED",
            "critical_issues": [{"code": "DATASET_EMPTY", "message": "empty"}],
        }
        preprocessor = DataPreprocessor()
        with pytest.raises(PreprocessingError):
            preprocessor.preprocess(df, blocked_report)

    def test_rows_before_geq_rows_after(self):
        df, report = get_pipeline("diabetes")
        preprocessor = DataPreprocessor(dataset_name="diabetes")
        _, summary = preprocessor.preprocess(df, report)
        assert summary["rows_before"] >= summary["rows_after"]

    def test_transformations_is_list(self):
        df, report = get_pipeline("diabetes")
        preprocessor = DataPreprocessor(dataset_name="diabetes")
        _, summary = preprocessor.preprocess(df, report)
        assert isinstance(summary["transformations"], list)

    def test_heart_disease_preprocessing(self):
        df, report = get_pipeline("heart_disease")
        preprocessor = DataPreprocessor(dataset_name="heart_disease")
        clean_df, summary = preprocessor.preprocess(df, report)
        assert isinstance(clean_df, pd.DataFrame)
        assert clean_df.isnull().sum().sum() == 0

    def test_parkinsons_preprocessing(self):
        df, report = get_pipeline("parkinsons")
        preprocessor = DataPreprocessor(dataset_name="parkinsons")
        clean_df, summary = preprocessor.preprocess(df, report)
        assert isinstance(clean_df, pd.DataFrame)
