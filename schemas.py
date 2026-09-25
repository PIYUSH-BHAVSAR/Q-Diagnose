# schemas.py
# Shared dataclass for the FeaturePipelineResult.
# This is the handoff object between Jayed's pipeline (Phases 2-6)
# and Piyush's model pipeline (Phases 7-10).
# Radha's explainability engine (Phase 12) also loads artifacts
# saved by this pipeline.

from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np


@dataclass
class FeaturePipelineResult:
    """
    Complete output of the feature pipeline (Phases 2-6).

    Full-feature arrays are consumed by classical models.
    Reduced arrays are consumed by quantum models.
    Artifacts are saved to disk for Radha's explainability engine.
    """

    # ── Full-feature arrays (classical models train on these) ─────────────────
    X_train: np.ndarray          # float64, shape (n_train, n_features)
    X_test:  np.ndarray          # float64, shape (n_test,  n_features)
    y_train: np.ndarray          # int64,   shape (n_train,)
    y_test:  np.ndarray          # int64,   shape (n_test,)

    # ── PCA-reduced arrays (quantum models train on these) ────────────────────
    X_train_reduced: np.ndarray  # float64, shape (n_train, n_components)
    X_test_reduced:  np.ndarray  # float64, shape (n_test,  n_components)

    # ── Feature name lists ────────────────────────────────────────────────────
    feature_names:         List[str]   # original column names
    reduced_feature_names: List[str]   # ["PC1", "PC2", ...]

    # ── Metadata ──────────────────────────────────────────────────────────────
    n_components:      int    # PCA components used (e.g. 8)
    variance_retained: float  # fraction of variance kept by PCA (e.g. 0.94)
    preprocessing_id:  str    # "PREP-{8-char-hex}" e.g. "PREP-A1B2C3D4"
    split_strategy:    str    # "stratified" or "grouped"
    test_size:         float  # 0.20
    random_state:      int    # 42
    class_weights:     Dict   # {0: 0.80, 1: 1.34} — informational only

    def to_dict(self) -> dict:
        """
        JSON-serialisable summary (no numpy arrays).
        Used for pipeline_metadata.json artifact storage.
        Consumed by Radha's explainability engine.
        """
        return {
            "n_train":               int(len(self.y_train)),
            "n_test":                int(len(self.y_test)),
            "n_features":            int(self.X_train.shape[1]),
            "n_components":          self.n_components,
            "variance_retained":     round(float(self.variance_retained), 4),
            "preprocessing_id":      self.preprocessing_id,
            "split_strategy":        self.split_strategy,
            "test_size":             self.test_size,
            "random_state":          self.random_state,
            "feature_names":         self.feature_names,
            "reduced_feature_names": self.reduced_feature_names,
            "class_weights": {
                str(k): round(float(v), 4)
                for k, v in self.class_weights.items()
            },
        }
