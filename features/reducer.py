# features/reducer.py
# Phase 6 — Dimensionality Reduction (PCA)
# Responsibility: Reduce feature space for quantum model compatibility.
# Produces: X_train_reduced, X_test_reduced, pca_metadata
# Standalone version — no dependency on core/config.py or core/exceptions.py.

import numpy as np
from sklearn.decomposition import PCA

from config import CONFIG
from exceptions import DimensionalityReductionError


class DimensionalityReducer:
    """
    Applies PCA to reduce feature dimensions.

    Key rules:
    - PCA is fit on training data only (no leakage).
    - PCA is applied to test data using the fitted transform.
    - n_components = min(config_n_components, n_features) to avoid sklearn errors.
    - For Diabetes (8 features, 8 components): result is a rotation, not reduction.
      variance_retained will be 1.0 — this is expected and correct.

    Produces pca_metadata matching the pca_output contract fields.
    """

    def __init__(self, n_components: int = None):
        """
        Parameters
        ----------
        n_components : int, optional
            Number of PCA components. Defaults to config value (8).
        """
        self._cfg        = CONFIG["reducer"]
        self.n_components = n_components or self._cfg["n_components"]
        self._pca        = None

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def fit_transform(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
    ) -> tuple:
        """
        Fit PCA on training data and transform both train and test.

        Parameters
        ----------
        X_train : np.ndarray
            Scaled training feature matrix, shape (n_train, n_features).
        X_test : np.ndarray
            Scaled test feature matrix, shape (n_test, n_features).

        Returns
        -------
        tuple : (X_train_reduced, X_test_reduced, pca_metadata)
            - X_train_reduced : np.ndarray, shape (n_train, n_components)
            - X_test_reduced  : np.ndarray, shape (n_test,  n_components)
            - pca_metadata    : dict with PCA statistics

        Raises
        ------
        DimensionalityReductionError
            If PCA fails.
        """
        try:
            n_features = X_train.shape[1]

            # Cap components to avoid sklearn error
            actual_components = min(self.n_components, n_features)

            # Fit PCA on training data only (data leakage prevention)
            self._pca = PCA(
                n_components=actual_components,
                random_state=self._cfg["random_state"],
            )

            X_train_reduced = self._pca.fit_transform(X_train)

            # Transform test using fitted PCA (do NOT fit_transform on test)
            X_test_reduced = self._pca.transform(X_test)

            # Build metadata
            explained_variance_ratio = self._pca.explained_variance_ratio_.tolist()
            total_variance           = float(np.sum(self._pca.explained_variance_ratio_))

            pca_metadata = {
                "original_features":      n_features,
                "n_components":           actual_components,
                "explained_variance_ratio": [round(v, 6) for v in explained_variance_ratio],
                "variance_retained":       round(total_variance, 6),
            }

            return (
                X_train_reduced.astype(np.float64),
                X_test_reduced.astype(np.float64),
                pca_metadata,
            )

        except DimensionalityReductionError:
            raise
        except Exception as e:
            raise DimensionalityReductionError(f"PCA failed: {e}") from e

    def get_component_names(self) -> list:
        """Return PC label names: ['PC1', 'PC2', ...]"""
        if self._pca is None:
            raise DimensionalityReductionError("PCA has not been fitted yet. Call fit_transform first.")
        return [f"PC{i+1}" for i in range(self._pca.n_components_)]
