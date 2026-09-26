"""Quantum model explainability using perturbation-based analysis.

Phase 12 — Explainability Engine (quantum side).

Approach
--------
The VQC is a black-box from the explainability perspective — we never
retrain it or touch its parameters.  Instead we measure how much each
input feature *matters* by replacing it with its background mean one
at a time and recording the absolute change in the prediction score.
This is the classical perturbation / "feature occlusion" technique
adapted for a quantum circuit.

Key design decisions
--------------------
- No model retraining.  Only vqc.predict_proba() is called.
- Explanation workload is capped at MAX_EXPLAIN_SAMPLES (20 rows) to
  keep inference time acceptable.
- Each feature is perturbed N_PERTURBATIONS (5) times per sample,
  using slightly different replacement values drawn around the column
  mean, and the results are averaged to reduce variance.
- circuit_info() reads metadata directly from the fitted VQC object —
  no new circuit is built.
- build_pipeline_trace() produces the pipeline_trace array described
  in contracts/explanation.json.

Public interface
----------------
explainer = QuantumExplainer(vqc_model, feature_names, original_feature_names)
explainer.fit(X_background)           # required once — computes column statistics

importance = explainer.perturbation_importance(X_test)   # list[dict], sorted
info       = explainer.circuit_info()                    # dict
scores     = explainer.predict_scores(X)                 # np.ndarray [0,1]
score      = explainer.predict_single_score(x)           # float [0,1]
trace      = explainer.build_pipeline_trace(...)         # list[dict]
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from backend.core.logging import logger


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_EXPLAIN_SAMPLES: int = 20   # cap on test rows used for explanation
N_PERTURBATIONS: int = 5        # independent perturbations per feature per sample
_DISCLAIMER = (
    "This explanation is based on input perturbation analysis and reflects "
    "sensitivity of the model output to input changes, not medical causality. "
    "Quantum advantage is not claimed. This system output is not a clinical "
    "diagnosis and must not replace professional medical judgement."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_feature_names(n: int, names: Optional[List[str]]) -> List[str]:
    """Return provided names if they match length, else generate generics."""
    if names and len(names) == n:
        return list(names)
    return [f"feature_{i}" for i in range(n)]


# ---------------------------------------------------------------------------
# QuantumExplainer
# ---------------------------------------------------------------------------

class QuantumExplainer:
    """Perturbation-based explainer for a fitted VQCModel.

    Parameters
    ----------
    vqc_model : VQCModel
        A *fitted* VQCModel instance.  ``vqc_model.is_fitted`` must be
        ``True`` when ``fit()`` is called.
    feature_names : list[str], optional
        Names of the reduced / PCA features that the VQC actually sees
        (e.g. ``["PC1", "PC2", …]``).  If omitted, generic names are
        generated.
    original_feature_names : list[str], optional
        Pre-PCA feature names from the raw dataset.  Used only for
        pipeline trace documentation; does not affect scoring.
    """

    def __init__(
        self,
        vqc_model: Any,
        feature_names: Optional[List[str]] = None,
        original_feature_names: Optional[List[str]] = None,
    ) -> None:
        self.vqc = vqc_model
        self._raw_feature_names = feature_names
        self.original_feature_names: List[str] = original_feature_names or []

        # Resolved after fit()
        self.feature_names: List[str] = []
        self._col_means: Optional[np.ndarray] = None
        self._col_stds: Optional[np.ndarray] = None
        self._is_fit: bool = False

    # ------------------------------------------------------------------
    # fit
    # ------------------------------------------------------------------

    def fit(self, X_background: np.ndarray) -> "QuantumExplainer":
        """Compute background statistics needed for perturbation.

        Must be called once before ``perturbation_importance`` or
        ``predict_scores``.  Typically ``X_background`` is the training
        set (or a representative sample of it).

        Parameters
        ----------
        X_background : np.ndarray, shape (n_samples, n_features)
            Background data.  Column means and standard deviations are
            computed here and reused for every subsequent call.

        Returns
        -------
        self
        """
        if not self.vqc.is_fitted:
            raise RuntimeError(
                "The VQCModel must be fitted before building the explainer."
            )

        n_features = X_background.shape[1]
        self.feature_names = _resolve_feature_names(
            n_features, self._raw_feature_names
        )

        self._col_means = X_background.mean(axis=0)       # (n_features,)
        self._col_stds  = X_background.std(axis=0) + 1e-8  # avoid /0

        self._is_fit = True
        logger.info(
            f"QuantumExplainer fitted: n_features={n_features}, "
            f"background_samples={len(X_background)}"
        )
        return self

    # ------------------------------------------------------------------
    # predict_scores  (batch)
    # ------------------------------------------------------------------

    def predict_scores(self, X: np.ndarray) -> np.ndarray:
        """Return positive-class probability scores for every row in X.

        Wraps ``vqc.predict_proba`` and returns a plain ``np.ndarray``
        of shape ``(n_samples,)`` with values in ``[0, 1]``.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        np.ndarray, shape (n_samples,)
        """
        self._require_fitted_vqc()
        scores = self.vqc.predict_proba(X)
        return np.asarray(scores, dtype=float).ravel()

    # ------------------------------------------------------------------
    # predict_single_score
    # ------------------------------------------------------------------

    def predict_single_score(self, x: np.ndarray) -> float:
        """Return the positive-class probability score for a single sample.

        Parameters
        ----------
        x : np.ndarray, shape (n_features,) or (1, n_features)

        Returns
        -------
        float in [0, 1]
        """
        self._require_fitted_vqc()
        x_2d = np.atleast_2d(x)
        return float(self.predict_scores(x_2d)[0])

    # ------------------------------------------------------------------
    # perturbation_importance
    # ------------------------------------------------------------------

    def perturbation_importance(
        self,
        X: np.ndarray,
        n_perturbations: int = N_PERTURBATIONS,
        random_state: int = 42,
    ) -> List[dict]:
        """Compute global feature importance via mean-replacement perturbation.

        Algorithm
        ---------
        For each feature ``j``:
          1. Replace column ``j`` with small random variations around its
             background mean (``n_perturbations`` realisations).
          2. Score every perturbed sample with the VQC.
          3. Compute ``|score_original - score_perturbed|`` for each row.
          4. Average over all rows and all perturbations.

        The procedure is repeated for all features.  Importance values are
        then normalised to sum to 1 so they are comparable across models.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            Typically the test split.  Capped internally at
            ``MAX_EXPLAIN_SAMPLES`` rows for efficiency.
        n_perturbations : int
            Number of independent perturbation draws per feature.
            Defaults to ``N_PERTURBATIONS`` (5).
        random_state : int
            Seed for reproducible perturbation draws.

        Returns
        -------
        list[dict], sorted descending by ``importance``::

            [
                {
                    "feature_name":  "PC1",
                    "feature_index": 0,
                    "importance":    0.312,   # normalised [0,1]
                    "rank":          1,
                },
                ...
            ]

        Raises
        ------
        RuntimeError
            If ``fit()`` has not been called first.
        """
        self._require_fit()

        # Cap workload
        if len(X) > MAX_EXPLAIN_SAMPLES:
            rng_idx = np.random.default_rng(random_state)
            idx = rng_idx.choice(len(X), size=MAX_EXPLAIN_SAMPLES, replace=False)
            X_work = X[idx]
            logger.info(
                f"QuantumExplainer: perturbation workload capped "
                f"{len(X)} → {MAX_EXPLAIN_SAMPLES} samples"
            )
        else:
            X_work = X.copy()

        n_samples, n_features = X_work.shape
        rng = np.random.default_rng(random_state)

        # Baseline scores — shape (n_samples,)
        baseline = self.predict_scores(X_work)

        # Importance accumulator — shape (n_features,)
        importance_acc = np.zeros(n_features, dtype=float)

        logger.info(
            f"QuantumExplainer: computing perturbation importance "
            f"(samples={n_samples}, features={n_features}, "
            f"perturbations={n_perturbations})"
        )

        for j in range(n_features):
            delta_acc = 0.0

            for _ in range(n_perturbations):
                X_pert = X_work.copy()

                # Replace column j with background mean + tiny Gaussian noise
                # The noise scale (5 % of std) keeps replacement values
                # realistic while providing multiple independent draws.
                noise = rng.normal(
                    loc=0.0,
                    scale=0.05 * self._col_stds[j],
                    size=n_samples,
                )
                X_pert[:, j] = self._col_means[j] + noise

                pert_scores = self.predict_scores(X_pert)
                delta_acc += np.abs(baseline - pert_scores).mean()

            importance_acc[j] = delta_acc / n_perturbations

        # Normalise to relative importance (sum = 1)
        total = importance_acc.sum()
        if total > 1e-12:
            importance_norm = importance_acc / total
        else:
            importance_norm = importance_acc  # all-zero edge case

        # Build result list
        result = [
            {
                "feature_name":  self.feature_names[j],
                "feature_index": j,
                "importance":    float(round(importance_norm[j], 6)),
                "rank":          0,   # filled below after sort
            }
            for j in range(n_features)
        ]
        result.sort(key=lambda d: d["importance"], reverse=True)
        for rank, entry in enumerate(result, start=1):
            entry["rank"] = rank

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
        n_perturbations: int = N_PERTURBATIONS,
        random_state: int = 42,
    ) -> dict:
        """Explain the VQC prediction for a single sample.

        Uses per-feature perturbation to compute a local importance and
        derive the *direction* of each feature's effect (whether replacing
        it with the background mean increases or decreases the score).

        Parameters
        ----------
        x : np.ndarray, shape (n_features,)
        feature_values : np.ndarray, optional
            Raw (un-scaled/un-reduced) display values.  Falls back to ``x``.
        prediction : int, optional
        prediction_score : float, optional
        actual_label : int, optional
        n_perturbations : int
        random_state : int

        Returns
        -------
        dict matching the ``feature_importance`` structure in
        ``contracts/explanation.json``::

            {
                "feature_importance": [
                    {
                        "feature_name":  "PC1",
                        "feature_index": 0,
                        "feature_value": 1.23,
                        "importance":    0.198,
                        "effect":        "positive",
                        "shap_value":    0.198,   # signed perturbation delta
                    },
                    ...
                ],
                "explainability_method": "feature_perturbation",
                "warnings": [...],
            }
        """
        self._require_fit()

        x_1d = np.atleast_1d(x).astype(float)
        x_2d = x_1d.reshape(1, -1)
        n_features = x_2d.shape[1]

        rng = np.random.default_rng(random_state)
        baseline_score = self.predict_single_score(x_2d)

        fv = np.atleast_1d(feature_values) if feature_values is not None else x_1d

        feature_importance = []

        for j in range(n_features):
            signed_deltas = []

            for _ in range(n_perturbations):
                x_pert = x_2d.copy()
                noise = rng.normal(
                    loc=0.0,
                    scale=0.05 * self._col_stds[j],
                )
                x_pert[0, j] = self._col_means[j] + noise
                pert_score = self.predict_single_score(x_pert)
                # Positive delta: removing this feature lowers the score
                # → feature was pushing prediction UP (positive effect)
                signed_deltas.append(baseline_score - pert_score)

            signed_mean = float(np.mean(signed_deltas))
            abs_importance = abs(signed_mean)

            feature_importance.append(
                {
                    "feature_name":  self.feature_names[j],
                    "feature_index": j,
                    "feature_value": float(fv[j]) if j < len(fv) else None,
                    "importance":    float(round(abs_importance, 6)),
                    "effect":        "positive" if signed_mean >= 0 else "negative",
                    "shap_value":    float(round(signed_mean, 6)),
                }
            )

        feature_importance.sort(key=lambda d: d["importance"], reverse=True)

        result: dict = {
            "feature_importance":     feature_importance,
            "explainability_method":  "feature_perturbation",
            "warnings":               [_DISCLAIMER],
        }

        if prediction is not None:
            result["prediction"] = int(prediction)
        if prediction_score is not None:
            result["prediction_score"] = float(prediction_score)
        if actual_label is not None:
            result["actual_label"] = int(actual_label)
            if prediction is not None:
                result["is_correct"] = (prediction == actual_label)

        return result

    # ------------------------------------------------------------------
    # circuit_info
    # ------------------------------------------------------------------

    def circuit_info(self) -> dict:
        """Return quantum circuit metadata for the explanation contract.

        Reads directly from the fitted VQC — no new circuit is created.

        Returns
        -------
        dict matching ``quantum_circuit_explanation`` in
        ``contracts/explanation.json``::

            {
                "qubits":                 8,
                "n_layers":               2,
                "circuit_depth":          40,
                "encoding_method":        "angle_encoding",
                "backend_type":           "local_simulator",
                "feature_to_qubit_mapping": {"PC1": "qubit_0", ...},
                "measured_qubits":        [0],
                "measurement":            "PauliZ(qubit_0)",
                "n_params":               32,
                "shots":                  null,
                "circuit_diagram":        "...",
            }

        Raises
        ------
        RuntimeError
            If the VQC has not been fitted.
        """
        self._require_fitted_vqc()

        vqc = self.vqc
        n_qubits: int = vqc.n_qubits
        n_layers: int = vqc.n_layers

        # Circuit depth estimate from the VQC model itself
        circuit_depth: int = vqc._estimate_depth()

        # Encoding method comes from the VariationalCircuit config
        encoding_method: str = "angle_encoding"
        if vqc.circuit is not None and hasattr(vqc.circuit, "encoding"):
            raw_enc = vqc.circuit.encoding or "angle"
            encoding_method = f"{raw_enc}_encoding"

        # Backend — always local simulator in MVP
        backend_type: str = "local_simulator"
        if vqc.device is not None:
            device_name = getattr(vqc.device, "name", None) or getattr(
                vqc.device, "short_name", "default.qubit"
            )
            backend_type = f"local_simulator ({device_name})"

        # Feature → qubit mapping using resolved feature names
        feature_names_for_map = self.feature_names if self._is_fit else (
            _resolve_feature_names(n_qubits, self._raw_feature_names)
        )
        feature_to_qubit_mapping: Dict[str, str] = {
            feature_names_for_map[i]: f"qubit_{i}"
            for i in range(min(n_qubits, len(feature_names_for_map)))
        }

        # Parameter count
        n_params: int = 0
        if vqc.circuit is not None:
            n_params = vqc.circuit.n_params
        elif vqc.params_ is not None:
            n_params = int(np.asarray(vqc.params_).size)

        return {
            "qubits":                   n_qubits,
            "n_layers":                 n_layers,
            "circuit_depth":            circuit_depth,
            "encoding_method":          encoding_method,
            "backend_type":             backend_type,
            "feature_to_qubit_mapping": feature_to_qubit_mapping,
            "measured_qubits":          [0],
            "measurement":              "PauliZ(qubit_0)",
            "n_params":                 n_params,
            "shots":                    vqc.shots,
            "circuit_diagram":          vqc.get_circuit_diagram(),
        }

    # ------------------------------------------------------------------
    # build_pipeline_trace
    # ------------------------------------------------------------------

    def build_pipeline_trace(
        self,
        dataset_id: str = "DS-UNKNOWN",
        experiment_id: str = "EXP-UNKNOWN",
        preprocessing_id: str = "PREP-UNKNOWN",
        feature_engineering_id: str = "FE-UNKNOWN",
        reduction_id: str = "QREP-UNKNOWN",
        n_original_features: Optional[int] = None,
        n_reduced_features: Optional[int] = None,
        backend_name: str = "LOCAL_SIMULATOR",
    ) -> List[dict]:
        """Build the pipeline_trace array described in the explanation contract.

        Each entry documents one phase of the experiment pipeline that
        contributed to this explanation.  Consumers (report generator,
        audit trail, frontend) use this to trace a prediction back to its
        source data.

        Parameters
        ----------
        dataset_id : str
            Artifact ID of the uploaded dataset (e.g. ``"DS-000001"``).
        experiment_id : str
            Artifact ID of the running experiment (e.g. ``"EXP-Q-000001"``).
        preprocessing_id : str
            Artifact ID of the preprocessing step.
        feature_engineering_id : str
            Artifact ID of the feature engineering step.
        reduction_id : str
            Artifact ID of the dimensionality reduction step.
        n_original_features : int, optional
            Number of raw features before PCA.  Inferred from
            ``original_feature_names`` if not provided.
        n_reduced_features : int, optional
            Number of PCA components.  Falls back to ``vqc.n_qubits``.
        backend_name : str
            Human-readable quantum backend name for the trace entry.

        Returns
        -------
        list[dict] matching ``pipeline_trace`` in ``contracts/explanation.json``::

            [
                {"phase": "Phase 1",  "component": "Ingestion",            "artifact": "DS-000001"},
                {"phase": "Phase 4",  "component": "Preprocessing",        "artifact": "PREP-000001"},
                {"phase": "Phase 5",  "component": "Feature Engineering",  "artifact": "FE-000001"},
                {"phase": "Phase 6",  "component": "Feature Reduction",    "artifact": "QREP-000001",
                 "method": "PCA",  "dimensions": "30 -> 8"},
                {"phase": "Phase 8",  "component": "Quantum Model",        "artifact": "VQC",
                 "qubits": 8},
                {"phase": "Phase 10", "component": "Execution",            "artifact": "EXP-Q-000001",
                 "backend": "LOCAL_SIMULATOR"},
                {"phase": "Phase 12", "component": "Explainability",       "artifact": experiment_id,
                 "method": "feature_perturbation"},
            ]
        """
        n_orig = n_original_features or len(self.original_feature_names) or "?"
        n_red  = n_reduced_features  or (self.vqc.n_qubits if self.vqc else 8)

        trace: List[dict] = [
            {
                "phase":     "Phase 1",
                "component": "Ingestion",
                "artifact":  dataset_id,
            },
            {
                "phase":     "Phase 4",
                "component": "Preprocessing",
                "artifact":  preprocessing_id,
            },
            {
                "phase":     "Phase 5",
                "component": "Feature Engineering",
                "artifact":  feature_engineering_id,
            },
            {
                "phase":     "Phase 6",
                "component": "Feature Reduction",
                "artifact":  reduction_id,
                "method":    "PCA",
                "dimensions": f"{n_orig} -> {n_red}",
            },
            {
                "phase":     "Phase 8",
                "component": "Quantum Model",
                "artifact":  "VQC",
                "qubits":    self.vqc.n_qubits if self.vqc else n_red,
            },
            {
                "phase":     "Phase 10",
                "component": "Execution",
                "artifact":  experiment_id,
                "backend":   backend_name,
            },
            {
                "phase":     "Phase 12",
                "component": "Explainability",
                "artifact":  experiment_id,
                "method":    "feature_perturbation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]
        return trace

    # ------------------------------------------------------------------
    # Internal guards
    # ------------------------------------------------------------------

    def _require_fit(self) -> None:
        """Raise if fit() has not been called."""
        if not self._is_fit:
            raise RuntimeError(
                "QuantumExplainer.fit() must be called before this method."
            )

    def _require_fitted_vqc(self) -> None:
        """Raise if the wrapped VQC model is not fitted."""
        if self.vqc is None or not self.vqc.is_fitted:
            raise RuntimeError(
                "The provided VQCModel is not fitted.  "
                "Call vqc.fit() before building the explainer."
            )
