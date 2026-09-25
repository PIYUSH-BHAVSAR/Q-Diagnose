# tests/test_profiler.py
import os
import pytest
import pandas as pd

from data.adapters import DataAdapter
from data.profiler import DataProfiler

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def load_dataset(name, dataset_name=None):
    adapter = DataAdapter(dataset_name=dataset_name or name)
    return adapter.load(os.path.join(FIXTURES, f"{name}.csv"))


class TestDataProfiler:

    def test_profile_returns_dict(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert isinstance(profile, dict)

    def test_profile_has_required_fields(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        required = [
            "dataset_id", "profile_id", "modality",
            "dimensions", "features", "target",
            "task", "missing_values", "duplicates",
            "status", "profiled_at",
        ]
        for field in required:
            assert field in profile, f"Missing field: {field}"

    def test_correct_row_count_diabetes(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert profile["dimensions"]["rows"] == len(df)

    def test_correct_column_count_diabetes(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert profile["dimensions"]["columns"] == len(df.columns)

    def test_detects_target_diabetes(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert profile["target"]["candidate"] == "Outcome"

    def test_detects_target_heart_disease(self):
        df = load_dataset("heart_disease")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-002")
        assert profile["target"]["candidate"] == "target"

    def test_detects_binary_classification_task(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert profile["task"]["candidate"] == "BINARY_CLASSIFICATION"

    def test_missing_values_count(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        expected_missing = int(df.isnull().sum().sum())
        assert profile["missing_values"]["total"] == expected_missing

    def test_duplicate_count(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        expected_dupes = int(df.duplicated().sum())
        assert profile["duplicates"]["candidate_count"] == expected_dupes

    def test_status_is_profiled(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert profile["status"] == "PROFILED"

    def test_class_distribution_breast_cancer(self):
        df = load_dataset("breast_cancer")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-003")
        dist = profile["class_distribution"]
        assert isinstance(dist, dict)
        assert len(dist) > 0

    def test_numerical_and_categorical_feature_counts(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        n_num = profile["features"]["numerical"]
        n_cat = profile["features"]["categorical"]
        assert n_num + n_cat == len(df.columns)

    def test_profile_id_format(self):
        df = load_dataset("diabetes")
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_id="test-001")
        assert profile["profile_id"].startswith("PROFILE-")
