# tests/test_adapters.py
import os
import pytest
import pandas as pd

from data.adapters import DataAdapter
from exceptions import DataLoadError

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


class TestDataAdapter:

    def test_load_csv_breast_cancer(self):
        adapter = DataAdapter(dataset_name="breast_cancer")
        df = adapter.load(os.path.join(FIXTURES, "breast_cancer.csv"))
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        # 'id' column should be dropped
        assert "id" not in df.columns

    def test_load_csv_heart_disease(self):
        adapter = DataAdapter(dataset_name="heart_disease")
        df = adapter.load(os.path.join(FIXTURES, "heart_disease.csv"))
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "target" in df.columns

    def test_load_csv_diabetes(self):
        adapter = DataAdapter(dataset_name="diabetes")
        df = adapter.load(os.path.join(FIXTURES, "diabetes.csv"))
        assert isinstance(df, pd.DataFrame)
        assert "Outcome" in df.columns

    def test_load_csv_parkinsons(self):
        adapter = DataAdapter(dataset_name="parkinsons")
        df = adapter.load(os.path.join(FIXTURES, "parkinsons.csv"))
        assert isinstance(df, pd.DataFrame)
        # 'name' column should be retained (used for GroupShuffleSplit later)
        assert len(df) > 0

    def test_column_names_stripped(self):
        adapter = DataAdapter()
        df = adapter.load(os.path.join(FIXTURES, "diabetes.csv"))
        for col in df.columns:
            assert col == col.strip(), f"Column '{col}' has leading/trailing whitespace"

    def test_load_nonexistent_file_raises(self):
        adapter = DataAdapter()
        with pytest.raises(DataLoadError):
            adapter.load("nonexistent_file.csv")

    def test_load_unsupported_format_raises(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("col1,col2\n1,2\n")
        adapter = DataAdapter()
        with pytest.raises(DataLoadError):
            adapter.load(str(f))

    def test_load_valid_json_string(self):
        import json
        data = [{"age": 25, "bmi": 22.5, "target": 0},
                {"age": 30, "bmi": 28.0, "target": 1}]
        json_str = json.dumps(data)
        adapter = DataAdapter()
        df = adapter.load(json_str)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["age", "bmi", "target"]

    def test_drop_columns_for_breast_cancer(self):
        adapter = DataAdapter(dataset_name="breast_cancer")
        df = adapter.load(os.path.join(FIXTURES, "breast_cancer.csv"))
        assert "id" not in df.columns

    def test_no_drop_columns_without_dataset_name(self):
        adapter = DataAdapter(dataset_name=None)
        df = adapter.load(os.path.join(FIXTURES, "breast_cancer.csv"))
        # id column should be present since no dataset name given
        assert "id" in df.columns
