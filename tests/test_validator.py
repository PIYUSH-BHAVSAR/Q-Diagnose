# tests/test_validator.py
import os
import pytest
import pandas as pd
import numpy as np

from data.adapters import DataAdapter
from data.profiler import DataProfiler
from data.validator import DataValidator

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def get_df_and_profile(name):
    adapter  = DataAdapter(dataset_name=name)
    profiler = DataProfiler()
    df       = adapter.load(os.path.join(FIXTURES, f"{name}.csv"))
    profile  = profiler.profile(df, dataset_id=f"test-{name}")
    return df, profile


class TestDataValidator:

    def test_validate_returns_dict(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        assert isinstance(report, dict)

    def test_report_has_required_fields(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        required = [
            "dataset_id", "validation_timestamp", "validation_status",
            "quality_score", "next_phase", "critical_issues", "warnings",
        ]
        for field in required:
            assert field in report, f"Missing field: {field}"

    def test_empty_dataset_is_blocked(self):
        empty_df  = pd.DataFrame()
        profiler  = DataProfiler()
        profile   = {"target": {"candidate": None}, "task": {"candidate": "UNKNOWN"},
                     "features": {"numerical": 0, "categorical": 0}}
        validator = DataValidator()
        report    = validator.validate(empty_df, profile, dataset_id="empty")
        assert report["validation_status"] == "BLOCKED"

    def test_quality_score_is_int_in_range(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        score = report["quality_score"]
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_diabetes_has_warnings(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        # Diabetes has class imbalance → should have warnings
        assert report["validation_status"] in ("PASS_WITH_WARNINGS", "PASS")

    def test_target_validation_present(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        assert "target_validation" in report
        assert report["target_validation"]["target_column"] == "Outcome"

    def test_missing_values_section(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        assert "missing_values" in report
        assert "total_missing" in report["missing_values"]["dataset_level"]

    def test_duplicate_section(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        assert "duplicates" in report
        assert "exact_duplicates" in report["duplicates"]

    def test_duplicate_columns_blocked(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "target": [0, 1]})
        df.columns = ["a", "a", "target"]  # duplicate column
        profile = {
            "target": {"candidate": "target"},
            "task":   {"candidate": "BINARY_CLASSIFICATION"},
            "features": {"numerical": 2, "categorical": 0},
        }
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="dup-cols")
        assert report["validation_status"] == "BLOCKED"

    def test_class_balance_section(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        assert "class_balance" in report

    def test_leakage_section(self):
        df, profile = get_df_and_profile("breast_cancer")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-bc")
        assert "leakage" in report

    def test_recommended_steps_is_list(self):
        df, profile = get_df_and_profile("diabetes")
        validator = DataValidator()
        report = validator.validate(df, profile, dataset_id="test-001")
        assert isinstance(report["recommended_preprocessing_steps"], list)
