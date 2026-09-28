"""
backend/data/adapters.py
Owner: Arzaan (stub) — Jayed fills in concrete adapters
Purpose: DatasetAdapter base class + AdapterRegistry.

Jayed will subclass DatasetAdapter to create:
  - BreastCancerAdapter   (drops 'id' column, encodes 'diagnosis' M/B → 1/0)
  - HeartDiseaseAdapter   (handles '?' missing values, drops none)
  - DiabetesAdapter       (handles zero-coded missing values)
  - ParkinsonsAdapter     (drops 'name' identifier column)

The registry auto-detects which adapter fits a given DataFrame by calling
each adapter's detect() method in registration order.

Usage (Jayed's profiler):
    from backend.data.adapters import registry

    adapter = registry.detect_adapter(df)
    if adapter:
        X, y, meta = adapter.adapt(df)
    else:
        # Generic tabular handling (no dataset-specific cleanup)
        ...

Contract alignment:
  - Target column names confirmed per contracts/NOTES.md item #1:
      Breast Cancer: 'diagnosis'  (M/B → 1/0)
      Heart Disease: 'target'     (already 0/1 after header was added)
      Diabetes:      'Outcome'    (0/1)
      Parkinson's:   'status'     (0/1)
  - Raw column counts (from dataset_profile.json contract):
      Breast Cancer: 32 cols (id + diagnosis + 30 features)
      Heart Disease: 14 cols (13 features + target)
      Diabetes:       9 cols (8 features + Outcome)
      Parkinson's:   24 cols (name + status + 22 features)
"""

from __future__ import annotations

import abc
from typing import Any, Dict, Optional, Tuple

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Lazy pandas import
try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Base class — Jayed extends this
# ---------------------------------------------------------------------------

class DatasetAdapter(abc.ABC):
    """
    Abstract base for dataset-specific adapters.

    Each adapter handles one (or a family of) datasets:
      1. detect(df) — returns True if this adapter recognises the DataFrame
      2. adapt(df)  — applies dataset-specific cleaning, returns (X, y, meta)

    Concrete adapters must implement both methods.
    Register with AdapterRegistry.register(adapter_instance).
    """

    #: Unique name for logging and identification
    name: str = "base"

    @abc.abstractmethod
    def detect(self, df: "pd.DataFrame") -> bool:
        """
        Return True if this adapter should handle the given DataFrame.
        Called by AdapterRegistry.detect_adapter() on every registered adapter.

        Implementations should check for known column names or structural
        signatures — never hardcode row counts.

        Example:
            def detect(self, df):
                return "diagnosis" in df.columns and "radius_mean" in df.columns
        """

    @abc.abstractmethod
    def adapt(
        self, df: "pd.DataFrame"
    ) -> Tuple["pd.DataFrame", "pd.Series", Dict[str, Any]]:
        """
        Apply dataset-specific transformations and return:
          X    — feature DataFrame (target and identifier columns removed)
          y    — target Series (integer 0/1)
          meta — dict with adapter metadata:
                   {
                     "target_column":   "diagnosis",
                     "dropped_columns": ["id"],
                     "encoding":        {"M": 1, "B": 0},  # if applicable
                     "n_features":      30,
                     "adapter_name":    "BreastCancerAdapter",
                   }

        Rules:
          - Do NOT modify the input df in-place (work on a copy).
          - Do NOT hardcode row counts.
          - Do NOT perform train/test splitting — that is Phase 4's job.
          - Do NOT apply scaling — that is Phase 4's job.
        """


# ---------------------------------------------------------------------------
# AdapterRegistry
# ---------------------------------------------------------------------------

class AdapterRegistry:
    """
    Registry of dataset adapters.  Adapters are tried in registration order.
    First adapter whose detect() returns True is used.

    Usage:
        registry = AdapterRegistry()
        registry.register(BreastCancerAdapter())
        registry.register(ParkinsonsAdapter())

        adapter = registry.detect_adapter(df)
        if adapter:
            X, y, meta = adapter.adapt(df)
    """

    def __init__(self) -> None:
        self._adapters: list[DatasetAdapter] = []

    def register(self, adapter: DatasetAdapter) -> None:
        """Register an adapter. Later-registered adapters have lower priority."""
        if not isinstance(adapter, DatasetAdapter):
            raise TypeError(
                f"Expected DatasetAdapter subclass, got {type(adapter).__name__}"
            )
        self._adapters.append(adapter)
        logger.info("Adapter registered | name=%s", adapter.name)

    def detect_adapter(self, df: "pd.DataFrame") -> Optional[DatasetAdapter]:
        """
        Try each registered adapter in order.
        Returns the first adapter whose detect() returns True, or None.
        """
        if not _PANDAS_AVAILABLE:
            raise ImportError("pandas required for AdapterRegistry.detect_adapter()")

        for adapter in self._adapters:
            try:
                if adapter.detect(df):
                    logger.info(
                        "Adapter matched | adapter=%s columns=%d",
                        adapter.name, len(df.columns),
                    )
                    return adapter
            except Exception as exc:
                logger.warning(
                    "Adapter detect() raised exception | adapter=%s error=%s",
                    adapter.name, exc,
                )
        logger.info(
            "No adapter matched | columns=%s", list(df.columns[:5])
        )
        return None

    def list_adapters(self) -> list[str]:
        """Return names of all registered adapters in priority order."""
        return [a.name for a in self._adapters]

    def __len__(self) -> int:
        return len(self._adapters)

    def __repr__(self) -> str:
        return f"<AdapterRegistry adapters={self.list_adapters()!r}>"


# ---------------------------------------------------------------------------
# Module-level registry singleton — Jayed calls registry.register(...)
# ---------------------------------------------------------------------------

registry: AdapterRegistry = AdapterRegistry()

# ---------------------------------------------------------------------------
# Concrete stub adapters (structural signatures only — Jayed completes logic)
# NOTE: These are intentionally lightweight so Jayed can replace them without
#       merge conflicts. The detect() methods are fully implemented; adapt()
#       bodies are left as TODO stubs.
# ---------------------------------------------------------------------------

class BreastCancerAdapter(DatasetAdapter):
    """
    Handles the Breast Cancer Wisconsin Diagnostic dataset.
    Raw CSV: 569 rows × 32 cols (id + diagnosis + 30 features)
    Target: 'diagnosis'  →  M=1, B=0
    Drop:   'id' (patient identifier, not a feature)
    """
    name = "BreastCancerAdapter"

    def detect(self, df: "pd.DataFrame") -> bool:
        return (
            "diagnosis" in df.columns
            and "radius_mean" in df.columns
            and "texture_mean" in df.columns
        )

    def adapt(
        self, df: "pd.DataFrame"
    ) -> Tuple["pd.DataFrame", "pd.Series", Dict[str, Any]]:
        # TODO (Jayed): implement full adaptation
        df = df.copy()
        target_col = "diagnosis"
        drop_cols = [c for c in ["id"] if c in df.columns]

        y = df[target_col].map({"M": 1, "B": 0}).astype(int)
        X = df.drop(columns=[target_col] + drop_cols)

        meta = {
            "target_column": target_col,
            "dropped_columns": drop_cols,
            "encoding": {"M": 1, "B": 0},
            "n_features": len(X.columns),
            "adapter_name": self.name,
        }
        return X, y, meta


class HeartDiseaseAdapter(DatasetAdapter):
    """
    Handles the Heart Disease UCI dataset.
    Raw CSV: 303 rows × 14 cols (13 features + target)
    Target: 'target'  →  already 0/1 after binarisation during setup
    Missing: '?' values may appear in 'ca' and 'thal' columns
    """
    name = "HeartDiseaseAdapter"

    def detect(self, df: "pd.DataFrame") -> bool:
        return (
            "target" in df.columns
            and "thalach" in df.columns
            and "trestbps" in df.columns
        )

    def adapt(
        self, df: "pd.DataFrame"
    ) -> Tuple["pd.DataFrame", "pd.Series", Dict[str, Any]]:
        # TODO (Jayed): implement full adaptation
        df = df.copy()
        target_col = "target"

        y = df[target_col].astype(int)
        X = df.drop(columns=[target_col])

        meta = {
            "target_column": target_col,
            "dropped_columns": [],
            "encoding": {},
            "n_features": len(X.columns),
            "adapter_name": self.name,
        }
        return X, y, meta


class DiabetesAdapter(DatasetAdapter):
    """
    Handles the Pima Indians Diabetes dataset.
    Raw CSV: 768 rows × 9 cols (8 features + Outcome)
    Target: 'Outcome'  →  0/1
    Note: Glucose, BloodPressure, SkinThickness, Insulin, BMI have zero-coded
          missing values (biologically impossible zeros). Phase 3 flags these.
    """
    name = "DiabetesAdapter"

    def detect(self, df: "pd.DataFrame") -> bool:
        return (
            "Outcome" in df.columns
            and "Glucose" in df.columns
            and "Pregnancies" in df.columns
        )

    def adapt(
        self, df: "pd.DataFrame"
    ) -> Tuple["pd.DataFrame", "pd.Series", Dict[str, Any]]:
        # TODO (Jayed): implement full adaptation
        df = df.copy()
        target_col = "Outcome"

        y = df[target_col].astype(int)
        X = df.drop(columns=[target_col])

        meta = {
            "target_column": target_col,
            "dropped_columns": [],
            "encoding": {},
            "n_features": len(X.columns),
            "adapter_name": self.name,
        }
        return X, y, meta


class ParkinsonsAdapter(DatasetAdapter):
    """
    Handles the Parkinson's Disease dataset (UCI Voice Measurements).
    Raw CSV: 195 rows × 24 cols (name + status + 22 features)
    Target: 'status'  →  0/1
    Drop:   'name' (patient identifier — also used for GroupShuffleSplit by Jayed)

    Note from processed_data_schema.md:
      Parkinson's must use GroupShuffleSplit on 'name' column because multiple
      recordings exist per patient. Standard random split would leak patient data.
    """
    name = "ParkinsonsAdapter"

    def detect(self, df: "pd.DataFrame") -> bool:
        return (
            "status" in df.columns
            and "name" in df.columns
            and "MDVP:Fo(Hz)" in df.columns
        )

    def adapt(
        self, df: "pd.DataFrame"
    ) -> Tuple["pd.DataFrame", "pd.Series", Dict[str, Any]]:
        # TODO (Jayed): implement full adaptation
        df = df.copy()
        target_col = "status"
        # Keep 'name' available in meta for GroupShuffleSplit but remove from X
        groups = df["name"].copy() if "name" in df.columns else None
        drop_cols = [c for c in ["name"] if c in df.columns]

        y = df[target_col].astype(int)
        X = df.drop(columns=[target_col] + drop_cols)

        meta = {
            "target_column": target_col,
            "dropped_columns": drop_cols,
            "encoding": {},
            "n_features": len(X.columns),
            "adapter_name": self.name,
            "groups": groups,   # pass to GroupShuffleSplit in Phase 4
            "requires_grouped_split": True,
            "group_column": "name",
        }
        return X, y, meta


# ---------------------------------------------------------------------------
# Register the concrete adapters on the module-level registry
# ---------------------------------------------------------------------------

registry.register(BreastCancerAdapter())
registry.register(HeartDiseaseAdapter())
registry.register(DiabetesAdapter())
registry.register(ParkinsonsAdapter())
