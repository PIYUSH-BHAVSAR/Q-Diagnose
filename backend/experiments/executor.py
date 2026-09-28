"""
backend/experiments/executor.py
Owner: Piyush
Phase: 10

ExperimentExecutor — the main coordination engine.
From phase10.md §3: "Phase 9 says: What? Phase 10 says: Run it."

Orchestrates the full experiment pipeline:
    1. Validate experiment config
    2. Load + run Jayed's feature pipeline
    3. Run classical models (LR, SVM, RF) on full features
    4. Run VQC on PCA-reduced features
    5. Run benchmarking + recommendation
    6. Store all results

Key rules enforced here:
    - Classical trains on X_train (full features) — phase10.md §12
    - VQC trains on X_train_reduced (PCA) — guide_piyush.md critical rules
    - Status transitions exactly as specified — phase10.md §32-33
    - API returns immediately; executor runs as BackgroundTask — phase10.md §23
    - All results stored in artifacts/experiments/{id}/ — phase10.md §34
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from backend.benchmarking.comparison import ModelComparison
from backend.benchmarking.recommendation import RecommendationEngine
from backend.core.config import config
from backend.core.logging import get_logger
from backend.experiments.manager import ExperimentManager, ExperimentStatus
from backend.models.registry import ModelRegistry
from backend.models.result import ModelResult

logger = get_logger(__name__)


class ExperimentExecutor:
    """
    Runs a complete experiment end-to-end.

    Usage (from FastAPI BackgroundTask — phase10.md §23):
        executor = ExperimentExecutor()
        executor.run(experiment_id, dataset_path, manager)

    Usage (direct — testing):
        result = executor.run_from_path("data/demo/breast_cancer.csv", n_components=8)
    """

    def __init__(
        self,
        manager: Optional[ExperimentManager] = None,
        dev_mode: bool = False,
    ) -> None:
        self.manager = manager or ExperimentManager()
        self.registry = ModelRegistry()
        self.comparator = ModelComparison()
        self.recommender = RecommendationEngine()
        self.dev_mode = dev_mode   # dev_mode=True uses fast VQC (epochs=10, n_qubits=4)

    # ── Public entry point ────────────────────────────────────────────────────

    def run(
        self,
        experiment_id: str,
        dataset_path: str,
        n_components: int = 8,
        random_state: int = 42,
        quantum_enabled: bool = True,
    ) -> dict:
        """
        Execute the full experiment pipeline for a given experiment_id.

        Called from FastAPI BackgroundTask — must not raise uncaught exceptions.
        All errors are caught, logged, and stored in the experiment manifest.

        Returns final results dict (also stored as artifact).
        """
        logger.info("Executor starting | experiment=%s | dataset=%s", experiment_id, dataset_path)

        try:
            return self._execute(experiment_id, dataset_path, n_components, random_state, quantum_enabled)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            logger.error("Experiment %s FAILED: %s", experiment_id, error_msg)
            self.manager.update_status(
                experiment_id,
                ExperimentStatus.FAILED,
                stage="failed",
                error_message=str(exc),
            )
            return {"experiment_id": experiment_id, "status": "FAILED", "error": str(exc)}

    def run_from_path(
        self,
        dataset_path: str,
        n_components: int = 8,
        random_state: int = 42,
        dataset_id: str = "DS-DEMO",
    ) -> dict:
        """
        Convenience method for testing — creates experiment, runs it, returns results.
        No FastAPI dependency.
        """
        exp_id = self.manager.create_experiment(dataset_id, {
            "dataset_path": dataset_path,
            "n_components": n_components,
            "random_state":  random_state,
        })
        return self.run(exp_id, dataset_path, n_components, random_state)

    # ── Private pipeline ──────────────────────────────────────────────────────

    def _execute(
        self,
        experiment_id: str,
        dataset_path: str,
        n_components: int,
        random_state: int,
        quantum_enabled: bool,
    ) -> dict:
        """Full pipeline — each stage updates status."""

        # ── VALIDATING ────────────────────────────────────────────────────────
        self.manager.update_status(
            experiment_id, ExperimentStatus.VALIDATING,
            stage="validating", progress=0.05,
        )
        path_obj = Path(dataset_path)
        if not path_obj.exists():
            fname = path_obj.name
            resolved = None
            for candidate_dir in [Path("fixtures"), Path("datasets"), Path("data"), Path("./")]:
                if candidate_dir.exists():
                    matches = list(candidate_dir.glob(f"**/{fname}"))
                    if matches:
                        resolved = str(matches[0])
                        break
            if resolved:
                logger.info(f"Resolved dataset_path '{dataset_path}' -> '{resolved}'")
                dataset_path = resolved
            else:
                raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        # ── PREPROCESSING — run Jayed's pipeline ──────────────────────────────
        self.manager.update_status(
            experiment_id, ExperimentStatus.PREPROCESSING,
            stage="preprocessing", progress=0.10,
        )
        processed = self._run_data_pipeline(dataset_path, n_components, random_state)

        # ── RUNNING_CLASSICAL ─────────────────────────────────────────────────
        self.manager.update_status(
            experiment_id, ExperimentStatus.RUNNING_CLASSICAL,
            stage="running_classical", progress=0.20,
            current_model="logistic_regression",
        )
        classical_results = self._train_classical_models(
            processed, experiment_id, random_state
        )

        # ── RUNNING_QUANTUM ───────────────────────────────────────────────────
        quantum_results: Dict[str, ModelResult] = {}
        if quantum_enabled and processed.n_components <= 8:
            self.manager.update_status(
                experiment_id, ExperimentStatus.RUNNING_QUANTUM,
                stage="running_quantum", progress=0.65,
                current_model="quantum_models",
                completed_models=list(classical_results.keys()),
            )
            quantum_results = self._train_quantum_models(
                processed, experiment_id, random_state
            )
        else:
            logger.info("Quantum disabled for experiment %s (n_components=%d)", experiment_id, n_components)

        # ── BENCHMARKING ──────────────────────────────────────────────────────
        self.manager.update_status(
            experiment_id, ExperimentStatus.BENCHMARKING,
            stage="benchmarking", progress=0.85,
            completed_models=list(classical_results.keys()) + list(quantum_results.keys()),
        )
        all_results = dict(classical_results)
        all_results.update(quantum_results)

        comparison = self.comparator.compare(all_results)
        recommendation = self.recommender.recommend(comparison)

        # ── Assemble final results ────────────────────────────────────────────
        models_serialized = {
            name: result.to_dict()
            for name, result in all_results.items()
        }

        final = {
            "experiment_id": experiment_id,
            "status":        "COMPLETED",
            "completed_at":  datetime.now(timezone.utc).isoformat(),
            "results": {
                "models":      models_serialized,
                "comparison":  {
                    **recommendation,
                    "performance_table": comparison.to_dict()["performance_table"],
                },
                "pipeline_info": {
                    "n_train":           int(len(processed.y_train)),
                    "n_test":            int(len(processed.y_test)),
                    "n_features":        int(processed.X_train.shape[1]),
                    "n_components":      processed.n_components,
                    "variance_retained": round(float(processed.variance_retained), 4),
                    "preprocessing_id":  processed.preprocessing_id,
                    "split_strategy":    processed.split_strategy,
                },
            },
        }

        self.manager.store_results(experiment_id, final)
        self.manager.store_recommendation(experiment_id, recommendation)
        self.manager.update_status(
            experiment_id, ExperimentStatus.COMPLETED,
            stage="completed", progress=1.0,
            completed_models=list(all_results.keys()),
        )

        logger.info("Experiment %s completed | models=%s | classification=%s",
                    experiment_id, list(all_results.keys()),
                    recommendation.get("classification"))
        return final

    # ── Data pipeline ─────────────────────────────────────────────────────────

    def _run_data_pipeline(self, dataset_path: str, n_components: int, random_state: int):
        """
        Run Jayed's adapter + feature pipeline.
        Returns FeaturePipelineResult.
        """
        import pandas as pd
        from backend.data.adapters import registry
        from features.pipeline import FeaturePipeline

        df = pd.read_csv(dataset_path)

        # ── Pre-clean before handing off to FeaturePipeline ──────────────────
        # 1. Drop columns that are entirely NaN (e.g. trailing empty column
        #    "Unnamed: 32" in the Kaggle breast-cancer CSV)
        all_nan_cols = [c for c in df.columns if df[c].isna().all()]
        if all_nan_cols:
            logger.info("Dropping all-NaN columns: %s", all_nan_cols)
            df = df.drop(columns=all_nan_cols)

        # 2. Drop known patient-identifier columns that are not features
        id_cols = [c for c in df.columns if c.lower() in ("id", "patient_id", "sample_id", "name")]
        # Only drop if the column is NOT the target (safety guard)
        target_candidates = {"target", "label", "diagnosis", "outcome", "Outcome", "status", "y"}
        id_cols = [c for c in id_cols if c not in target_candidates]
        if id_cols:
            logger.info("Dropping identifier columns: %s", id_cols)
            df = df.drop(columns=id_cols)

        # 3. Drop any remaining columns with > 50% NaN (too sparse to be useful)
        thresh = len(df) * 0.5
        sparse_cols = [c for c in df.columns if df[c].isna().sum() > thresh]
        if sparse_cols:
            logger.warning("Dropping >50%% NaN columns: %s", sparse_cols)
            df = df.drop(columns=sparse_cols)

        # 4. Impute remaining NaN values with column median (numeric) or mode (categorical)
        for col in df.columns:
            if df[col].isna().any():
                if df[col].dtype in (float, int) or str(df[col].dtype).startswith(("float", "int")):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    mode = df[col].mode()
                    df[col] = df[col].fillna(mode.iloc[0] if len(mode) else "unknown")

        pipeline = FeaturePipeline()
        processed = pipeline.fit_transform(df)
        return processed

    # ── Classical training ────────────────────────────────────────────────────

    def _train_classical_models(
        self,
        processed,
        experiment_id: str,
        random_state: int,
    ) -> Dict[str, ModelResult]:
        """
        Train LR, SVM, RF on FULL features (X_train, X_test).
        phase10.md §12: no data leakage.
        """
        models = self.registry.get_classical_models(random_state=random_state)
        results: Dict[str, ModelResult] = {}
        total = len(models)

        for i, (name, model) in enumerate(models.items()):
            logger.info("Training classical model: %s", name)
            try:
                result = model.fit(
                    processed.X_train, processed.y_train,
                    processed.X_test,  processed.y_test,
                    experiment_id=experiment_id,
                )
                results[name] = result
                logger.info(
                    "  %s -> acc=%.3f recall=%.3f auc=%.3f time=%.2fs",
                    name, result.accuracy, result.recall, result.roc_auc,
                    result.training_time_seconds,
                )
            except Exception as exc:
                logger.error("Classical model %s failed: %s", name, exc)
                results[name] = ModelResult.failed(experiment_id, "CLASSICAL", name, str(exc), random_state)

            # Update progress after each model
            progress = 0.20 + (i + 1) / total * 0.40
            self.manager.update_status(
                experiment_id, ExperimentStatus.RUNNING_CLASSICAL,
                stage="running_classical",
                progress=progress,
                current_model=name,
                completed_models=list(results.keys()),
            )

        return results

    # ── Quantum training ──────────────────────────────────────────────────────

    def _train_quantum_models(
        self,
        processed,
        experiment_id: str,
        random_state: int,
    ) -> Dict[str, ModelResult]:
        """
        Train quantum models (VQC, QuantumSVM) on PCA-REDUCED features (X_train_reduced, X_test_reduced).
        CRITICAL: NOT on X_train (full features) — phase8.md + guide rules.
        """
        quantum_models = self.registry.get_quantum_models(
            n_qubits=processed.n_components,
            random_state=random_state,
            dev_mode=self.dev_mode,
        )
        results: Dict[str, ModelResult] = {}
        for name, model in quantum_models.items():
            logger.info("Training quantum model: %s", name)
            try:
                result = model.fit(
                    processed.X_train_reduced, processed.y_train,
                    processed.X_test_reduced,  processed.y_test,
                    experiment_id=experiment_id,
                )
                results[name] = result
                logger.info(
                    "  %s -> acc=%.3f recall=%.3f auc=%.3f circuits=%d time=%.1fs",
                    name, result.accuracy, result.recall, result.roc_auc,
                    result.total_circuit_executions or 0,
                    result.training_time_seconds,
                )
            except Exception as exc:
                logger.error("Quantum model %s training failed: %s", name, exc)
                results[name] = ModelResult.failed(experiment_id, "QUANTUM", name, str(exc), random_state)
        return results
