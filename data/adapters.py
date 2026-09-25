# data/adapters.py
# Phase 2 — Data Adapter
# Responsibility: Load raw dataset files into a standard pandas DataFrame.
# Standalone version — no dependency on core/config.py or core/exceptions.py.
# During team integration: swap config and exceptions imports.

import os
import json
import pandas as pd

from config import CONFIG
from exceptions import DataLoadError


class DataAdapter:
    """
    Converts raw data sources (CSV, JSON) into a standard pandas DataFrame.
    Drops identifier columns (e.g. 'id', 'name') that are not features.
    Keeps the rest of the pipeline independent from the data source format.
    """

    def __init__(self, dataset_name: str = None):
        """
        Parameters
        ----------
        dataset_name : str, optional
            Name key used to look up dataset-specific drop columns.
            Examples: "breast_cancer", "parkinsons"
            If None, no dataset-specific columns are dropped.
        """
        self.dataset_name = dataset_name
        self._cfg = CONFIG["adapter"]

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def load(self, source: str) -> pd.DataFrame:
        """
        Load data from a file path or JSON string into a DataFrame.

        Parameters
        ----------
        source : str
            File path to a CSV or JSON file, or a raw JSON string.

        Returns
        -------
        pd.DataFrame
            Standardized DataFrame ready for profiling.

        Raises
        ------
        DataLoadError
            If the file cannot be loaded or format is unsupported.
        """
        if not isinstance(source, str):
            raise DataLoadError(f"Source must be a string file path or JSON string, got {type(source)}")

        # Detect source type
        if os.path.isfile(source):
            return self._load_from_file(source)
        else:
            # Try treating it as a raw JSON string
            return self._load_from_json_string(source)

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _load_from_file(self, filepath: str) -> pd.DataFrame:
        """Load from a CSV or JSON file path."""
        ext = os.path.splitext(filepath)[1].lower().lstrip(".")

        if ext == "csv":
            df = self._load_csv(filepath)
        elif ext == "json":
            df = self._load_json_file(filepath)
        else:
            raise DataLoadError(
                f"Unsupported file format: '.{ext}'. "
                f"Supported formats: {self._cfg['supported_formats']}"
            )

        return self._post_process(df, filepath)

    def _load_csv(self, filepath: str) -> pd.DataFrame:
        """Load a CSV file."""
        try:
            df = pd.read_csv(filepath)
            return df
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV '{filepath}': {e}") from e

    def _load_json_file(self, filepath: str) -> pd.DataFrame:
        """Load a JSON file (records or dict format)."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            if isinstance(data, list):
                # List of records: [{col: val}, ...]
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Dict of columns: {col: [val, ...]}
                df = pd.DataFrame(data)
            else:
                raise DataLoadError(f"Unsupported JSON structure in '{filepath}'")

            return df
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"Failed to load JSON file '{filepath}': {e}") from e

    def _load_from_json_string(self, json_str: str) -> pd.DataFrame:
        """Load from a raw JSON string."""
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                raise DataLoadError("Unsupported JSON string structure.")
            return self._post_process(df, source="json_string")
        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON string: {e}") from e

    def _post_process(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Apply post-load processing:
        - Basic checks (non-empty, has columns)
        - Drop identifier columns defined in config
        - Strip whitespace from column names
        """
        if df.empty:
            raise DataLoadError(f"Loaded dataset from '{source}' is empty.")

        if df.columns.tolist() == []:
            raise DataLoadError(f"Loaded dataset from '{source}' has no columns.")

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Drop dataset-specific identifier columns
        drop_cols = self._get_drop_columns()
        cols_to_drop = [c for c in drop_cols if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        # Reset index
        df = df.reset_index(drop=True)

        return df

    def _get_drop_columns(self) -> list:
        """Return columns to drop for the current dataset."""
        if self.dataset_name is None:
            return []
        return self._cfg["drop_columns"].get(self.dataset_name, [])
