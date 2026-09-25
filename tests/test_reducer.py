# tests/test_reducer.py
import os
import pytest
import numpy as np

from data.adapters import DataAdapter
from data.profiler import DataProfiler
from data.validator import DataValidator
from data.preprocessing import DataPreprocessor
from features.pipeline import FeaturePipeline
from features.reducer import DimensionalityReducer
from exceptions import DimensionalityReductionError

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def get_scaled_arrays(name):
    """Run pipeline up to scaling step and return X_train_scaled, X_test_scaled."""
    adapter      = DataAdapter(dataset_name=name)
    profiler     = DataProfiler()
    validator    = DataValidator()
    preprocessor = DataPreprocessor(dataset_name=name)
    pipeline     = FeaturePipeline(dataset_name=name)

    df      = adapter.load(os.path.join(FIXTURES, f"{name}.csv"))
    profile = profiler.profile(df, dataset_id=f"test-{name}")
    report  = validator.validate(df, profile, dataset_id=f"test-{name}")
    clean_df, _ = preprocessor.preprocess(df, report)

    result = pipeline.fit_transform(clean_df, experiment_id=f"EXP-REDUCER-{name}")
    return result.X_train, result.X_test, result


class TestDimensionalityReducer:

    def test_returns_three_items(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        result  = reducer.fit_transform(X_train, X_test)
        assert len(result) == 3

    def test_correct_output_shape_train(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        X_train_r, X_test_r, meta = reducer.fit_transform(X_train, X_test)
        assert X_train_r.shape == (100, 4)

    def test_correct_output_shape_test(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        X_train_r, X_test_r, meta = reducer.fit_transform(X_train, X_test)
        assert X_test_r.shape == (20, 4)

    def test_output_dtype_float64(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        X_train_r, X_test_r, _ = reducer.fit_transform(X_train, X_test)
        assert X_train_r.dtype == np.float64
        assert X_test_r.dtype == np.float64

    def test_metadata_fields(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        _, _, meta = reducer.fit_transform(X_train, X_test)
        assert "original_features" in meta
        assert "n_components" in meta
        assert "explained_variance_ratio" in meta
        assert "variance_retained" in meta

    def test_variance_retained_between_0_and_1(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        _, _, meta = reducer.fit_transform(X_train, X_test)
        assert 0.0 < meta["variance_retained"] <= 1.0

    def test_n_components_capped_at_n_features(self):
        """If n_components > n_features, should cap at n_features."""
        reducer = DimensionalityReducer(n_components=20)
        X_train = np.random.rand(50, 5)   # only 5 features
        X_test  = np.random.rand(10, 5)
        X_train_r, X_test_r, meta = reducer.fit_transform(X_train, X_test)
        assert X_train_r.shape[1] <= 5
        assert meta["n_components"] <= 5

    def test_explained_variance_ratio_sums_to_total_variance(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        _, _, meta = reducer.fit_transform(X_train, X_test)
        ratio_sum = sum(meta["explained_variance_ratio"])
        # Allow small floating point rounding difference (rounding to 6 decimals)
        assert abs(ratio_sum - meta["variance_retained"]) < 1e-4

    def test_component_names(self):
        reducer = DimensionalityReducer(n_components=4)
        X_train = np.random.rand(100, 10)
        X_test  = np.random.rand(20, 10)
        reducer.fit_transform(X_train, X_test)
        names = reducer.get_component_names()
        assert names == ["PC1", "PC2", "PC3", "PC4"]

    def test_diabetes_8_components_on_8_features(self):
        """
        Diabetes has 8 features. PCA with 8 components = rotation, not reduction.
        variance_retained should be 1.0.
        """
        X_train, X_test, result = get_scaled_arrays("diabetes")
        reducer = DimensionalityReducer(n_components=8)
        X_train_r, X_test_r, meta = reducer.fit_transform(X_train, X_test)
        # Shape: same number of features (rotation only)
        assert X_train_r.shape[1] == min(8, X_train.shape[1])
        assert abs(meta["variance_retained"] - 1.0) < 1e-5

    def test_breast_cancer_8_components_reduces_dimensions(self):
        """Breast Cancer has 30 features → PCA with 8 components reduces to 8."""
        X_train, X_test, result = get_scaled_arrays("breast_cancer")
        reducer = DimensionalityReducer(n_components=8)
        X_train_r, X_test_r, meta = reducer.fit_transform(X_train, X_test)
        assert X_train_r.shape[1] == 8
        # original_features matches whatever pipeline produced (30+ due to encoding)
        assert meta["original_features"] == X_train.shape[1]
        assert meta["variance_retained"] <= 1.0

    def test_component_names_not_fitted_raises(self):
        reducer = DimensionalityReducer(n_components=4)
        with pytest.raises(DimensionalityReductionError):
            reducer.get_component_names()
