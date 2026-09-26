"""Classical model explainability using SHAP.

Phase 12 — Explainability Engine (classical side).

Supports:
  - RandomForestClassifier  → shap.TreeExplainer
  - LogisticRegression      → shap.LinearExplainer
  - SVC / other             → shap.KernelExplainer (background capped at 50 samples)

Public interface
----------------
explainer = ClassicalExplainer(model, feature_names)
explainer.fit_explainer(X_background)

global_imp = explainer.global_importance(X)        # list of dicts, sorted by importance
sample_exp = explainer.explain_sample(x_row, ...)  # dict with per-feature shap_value + effect
"""

from typing import List, Optional, Union

import numpy as np

from backend.core.logging import logger


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_KERNEL_BACKGROUND = 50  # KernelExplainer background sample cap


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _resolve_feature_names(
    n_features: int,
    feature_names: Optional[List[str]]
) -> List[str]:
    """Return feature names, generating generic ones when not supplied."""
    if feature_names and len(feature_names) == n_features:
        return list(feature_names)
    return [f"feature_{i}" for i in range(n_features)]


def _detect_model_family(model) -> str:
    """Detect model type by class name.

    Returns one of: 'tree', 'linear', 'kernel'
    """
    class_name = type(model).__name__

    tree_models = {
        "RandomForestClassifier",
        "RandomForestRegressor",
        "DecisionTreeClassifier",
        "DecisionTreeRegressor",
        "GradientBoostingClassifier",
        "GradientBoostingRegressor",
        "ExtraTreesClassifier",
        "ExtraTreesRegressor",
        "XGBClassifier",
        "LGBMClassifier",
        "CatBoostClassifier",
    }
    linear_models = {
        "LogisticRegression",
        "LogisticRegressionCV",
        "LinearSVC",
        "LinearRegression",
        "Ridge",
        "Lasso",
        "ElasticNet",
        "SGDClassifier",
    }

    if class_name in tree_models:
        return "tree"
    if class_name in linear_models:
        return "linear"
    return "kernel"


# ---------------------------------------------------------------------------
# ClassicalExplainer
# ---------------------------------------------------------------------------

class ClassicalExplainer:
    """SHAP-based explainer for classical scikit-learn models.

    Parameters
    ----------
    model : fitted sklearn estimator
        A trained classifier (RandomForest, LogisticRegression, SVC, …).
    feature_names : list of str, optional
        Names that correspond to each column in the feature matrix.
        If omitted, generic names ("feature_0", "feature_1", …) are used.
    """

    def __init__(
        self,
        model,
        feature_names: Optional[List[str]] = None,
    ) -> None:
        self.model = model
        self.feature_names = feature_names  # finalised in fit_explainer
        self._explainer = None
        self._model_family: Optional[str] = None

    # ------------------------------------------------------------------
    # fit_explainer
    # ------------------------------------------------------------------

    def fit_explainer(
        self,
        X_background: np.ndarray,
    ) -> None:
        """Build the appropriate SHAP explainer for the fitted model.

        Must be called once before ``global_importance`` or
        ``explain_sample``.

        Parameters
        ----------
        X_background : np.ndarray, shape (n_samples, n_features)
            Representative data used to initialise the explainer.
            For KernelExplainer this becomes the background dataset
            (automatically subsampled to at most MAX_KERNEL_BACKGROUND rows).
        """
        try:
            import shap
        except ImportError as exc:
            raise ImportError(
                "SHAP is required for ClassicalExplainer. "
                "Install it with: pip install shap"
            ) from exc

        n_features = X_background.shape[1]

        # Resolve feature names now that we know the feature count
        self.feature_names = _resolve_feature_names(n_features, self.feature_names)

        self._model_family = _detect_model_family(self.model)
        logger.info(
            f"ClassicalExplainer: detected model family '{self._model_family}' "
            f"for {type(self.model).__name__}"
        )

        if self._model_family == "tree":
            self._explainer = shap.TreeExplainer(self.model)
            logger.info("ClassicalExplainer: using shap.TreeExplainer")

        elif self._model_family == "linear":
            # LinearExplainer expects a background summary (mean or kmeans)
            background = shap.utils.sample(X_background, min(MAX_KERNEL_BACKGROUND, len(X_background)))
            self._explainer = shap.LinearExplainer(self.model, background)
            logger.info("ClassicalExplainer: using shap.LinearExplainer")

        else:
            # Fallback: KernelExplainer — cap background samples
            n_bg = min(MAX_KERNEL_BACKGROUND, len(X_background))
            if len(X_background) > n_bg:
                rng = np.random.default_rng(42)
                idx = rng.choice(len(X_background), size=n_bg, replace=False)
                background = X_background[idx]
                logger.info(
                    f"ClassicalExplainer: KernelExplainer background "
                    f"subsampled {len(X_background)} → {n_bg} rows"
                )
            else:
                background = X_background

            # Use predict_proba if available, else predict
            predict_fn = (
                self.model.predict_proba
                if hasattr(self.model, "predict_proba")
                else self.model.predict
            )
            self._explainer = shap.KernelExplainer(predict_fn, background)
            logger.info("ClassicalExplainer: using shap.KernelExplainer (fallback)")

    # ------------------------------------------------------------------
    # _get_shap_values
    # ------------------------------------------------------------------

    def _get_shap_values(self, X: np.ndarray) -> np.ndarray:
        """Compute raw SHAP values for X.

        Normalises the output across explainer types so it always returns
        a 2-D array of shape (n_samples, n_features) corresponding to the
        positive-class (binary classification) contribution.

        Raises
        ------
        RuntimeError
            If fit_explainer() has not been called.
        """
        if self._explainer is None:
            raise RuntimeError(
                "fit_explainer() must be called before computing SHAP values."
            )

        raw = self._explainer.shap_values(X)

        # shap.TreeExplainer on a binary classifier returns a list of two
        # arrays [class_0_values, class_1_values].  We want class 1 (positive).
        if isinstance(raw, list):
            # Binary classification → take index 1 (positive class)
            values = np.array(raw[1])
        else:
            values = np.array(raw)

        # KernelExplainer on predict_proba returns shape (n_samples, n_features, 2)
        # for binary classifiers; take the last axis (positive class).
        if values.ndim == 3:
            values = values[:, :, 1]

        return values  # (n_samples, n_features)

    # ------------------------------------------------------------------
    # global_importance
    # ------------------------------------------------------------------

    def global_importance(
        self,
        X: np.ndarray,
    ) -> List[dict]:
        """Compute global feature importance as mean absolute SHAP values.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            Dataset over which to average (typically the test set).

        Returns
        -------
        list of dict, sorted descending by ``importance``::

            [
                {
                    "feature_name": "mean_radius",
                    "feature_index": 0,
                    "importance": 0.187,
                },
                ...
            ]
        """
        logger.info(f"Computing global feature importance over {len(X)} samples")

        shap_vals = self._get_shap_values(X)          # (n, f)
        mean_abs = np.abs(shap_vals).mean(axis=0)      # (f,)
        mean_abs_normalised = mean_abs / (mean_abs.sum() + 1e-12)  # relative importance

        result = [
            {
                "feature_name": self.feature_names[i],
                "feature_index": i,
                "importance": float(round(mean_abs_normalised[i], 6)),
            }
            for i in range(len(self.feature_names))
        ]

        result.sort(key=lambda d: d["importance"], reverse=True)
        return result

    # ------------------------------------------------------------------
    # explain_sample
    # ------------------------------------------------------------------

    def explain_sample(
        self,
        x: np.ndarray,
        feature_values: Optional[np.ndarray] = None,
        prediction: Optional[int] = None,
        prediction_score: Optional[float] = None,
        actual_label: Optional[int] = None,
    ) -> dict:
        """Explain the model's prediction for a single sample.

        Parameters
        ----------
        x : np.ndarray, shape (n_features,) or (1, n_features)
            The sample to explain.
        feature_values : np.ndarray, optional
            Raw (un-scaled) feature values for the sample, used for
            display purposes.  Defaults to ``x`` if not supplied.
        prediction : int, optional
            Predicted class label (0 or 1).
        prediction_score : float, optional
            Model confidence score.
        actual_label : int, optional
            Ground-truth label (if known).

        Returns
        -------
        dict matching the ``feature_importance`` array from
        ``contracts/explanation.json``::

            {
                "feature_importance": [
                    {
                        "feature_name": "mean_radius",
                        "feature_index": 0,
                        "feature_value": 17.23,
                        "importance": 0.312,
                        "effect": "positive",   # "positive" | "negative"
                        "shap_value": 0.312,
                    },
                    ...
                ],
                "explainability_method": "SHAP",
                "model_family": "tree",
                "base_value": 0.42,
            }
        """
        x_2d = np.atleast_2d(x)

        shap_vals = self._get_shap_values(x_2d)  # (1, n_features)
        shap_row = shap_vals[0]                   # (n_features,)

        # Feature values for display
        if feature_values is not None:
            fv = np.atleast_1d(feature_values)
        else:
            fv = x_2d[0]

        # Per-feature entries
        feature_importance = []
        for i, sv in enumerate(shap_row):
            feature_importance.append(
                {
                    "feature_name": self.feature_names[i],
                    "feature_index": i,
                    "feature_value": float(fv[i]) if i < len(fv) else None,
                    "importance": float(round(abs(sv), 6)),
                    "effect": "positive" if sv >= 0 else "negative",
                    "shap_value": float(round(sv, 6)),
                }
            )

        # Sort by absolute SHAP magnitude (most influential first)
        feature_importance.sort(key=lambda d: d["importance"], reverse=True)

        # Base value — available on TreeExplainer / LinearExplainer
        base_value: Optional[float] = None
        if hasattr(self._explainer, "expected_value"):
            ev = self._explainer.expected_value
            if isinstance(ev, (list, np.ndarray)):
                # Binary classifier: index 1 = positive class base
                base_value = float(ev[1]) if len(ev) > 1 else float(ev[0])
            else:
                base_value = float(ev)

        result: dict = {
            "feature_importance": feature_importance,
            "explainability_method": "SHAP",
            "model_family": self._model_family,
            "base_value": base_value,
        }

        # Optionally attach prediction context if the caller provides it
        if prediction is not None:
            result["prediction"] = int(prediction)
        if prediction_score is not None:
            result["prediction_score"] = float(prediction_score)
        if actual_label is not None:
            result["actual_label"] = int(actual_label)
            result["is_correct"] = (prediction == actual_label) if prediction is not None else None

        return result
