"""
backend/planner/experiment_planner.py
Owner: Piyush
Phase: 9

ExperimentPlanner — rule-based deterministic experiment plan generator.
From phase9.md §5-8 + guide_piyush.md §6:

    "The first version does NOT need an LLM agent.
     We can build a deterministic rule-based experiment planner first."

    Input:  DatasetProfile + ValidationResult + n_components + max_qubits
    Output: ExperimentConfig dict with full decision_trace

Output shape matches contracts/experiment_config.json:
    {
        "task": "BINARY_CLASSIFICATION",
        "preprocessing": ["standard_scaling"],
        "reduction": {"method": "PCA", "components": 8},
        "classical_models": ["logistic_regression", "svm", "random_forest"],
        "quantum_models": ["vqc"],
        "quantum_enabled": true,
        "evaluation": {...},
        "use_class_weight": true,
        "decision_trace": {"rules_applied": [...], "reason": "..."}
    }
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.planner.rules import (
    rule_001_task_check,
    rule_002_quantum_feasibility,
    rule_003_dataset_regime,
    rule_004_class_imbalance,
    rule_005_feature_dimension,
    MAX_QUBITS_DEFAULT,
)


class ExperimentPlanner:
    """
    Deterministic rule-based experiment planner.

    Reads dataset characteristics and produces a complete, immutable
    experiment configuration. Every decision is recorded in decision_trace.

    Usage:
        planner = ExperimentPlanner()
        config = planner.plan(profile, validation, n_components=8)
        # config["quantum_enabled"] → True/False
        # config["decision_trace"]["rules_applied"] → list of rule messages
    """

    def plan(
        self,
        profile,               # DatasetProfile from Jayed's profiler
        validation,            # ValidationResult from Jayed's validator
        n_components: int = 8,
        max_qubits: int = MAX_QUBITS_DEFAULT,
        random_state: int = 42,
        test_size: float = 0.20,
    ) -> dict:
        """
        Produce experiment configuration by applying planning rules.

        Args:
            profile:      DatasetProfile — has task_candidate, rows, numerical_count
            validation:   ValidationResult — has class_balance dict
            n_components: PCA components from Jayed's FeaturePipelineResult
            max_qubits:   Max qubits supported (default 8 — phase8.md §14)
            random_state: Reproducibility seed
            test_size:    Train/test split ratio

        Returns:
            dict — complete experiment config with decision_trace
        """
        rules_applied = []
        errors = []

        # ── RULE-001: Task type check ─────────────────────────────────────────
        task_candidate = getattr(profile, "task_candidate", "BINARY_CLASSIFICATION")
        r001_pass, r001_msg = rule_001_task_check(task_candidate)
        rules_applied.append(r001_msg)
        if not r001_pass:
            errors.append(r001_msg)
            raise ValueError(r001_msg)

        # ── RULE-002: Quantum feasibility ─────────────────────────────────────
        r002_pass, r002_msg = rule_002_quantum_feasibility(n_components, max_qubits)
        rules_applied.append(r002_msg)
        quantum_enabled = r002_pass

        # ── RULE-003: Dataset regime ──────────────────────────────────────────
        n_rows = getattr(profile, "rows", 0)
        regime, r003_msg = rule_003_dataset_regime(n_rows)
        rules_applied.append(r003_msg)

        # ── RULE-004: Class imbalance ─────────────────────────────────────────
        class_balance = getattr(validation, "class_balance", {})
        imbalance_ratio = class_balance.get("imbalance_ratio", 1.0)
        if isinstance(imbalance_ratio, dict):
            imbalance_ratio = imbalance_ratio.get("value", 1.0)
        use_class_weight, r004_msg = rule_004_class_imbalance(float(imbalance_ratio))
        rules_applied.append(r004_msg)

        # ── RULE-005: Feature dimension category ──────────────────────────────
        dim_category, r005_msg = rule_005_feature_dimension(n_components)
        rules_applied.append(r005_msg)

        # ── Build quantum config ──────────────────────────────────────────────
        quantum_models = []
        quantum_config = {}
        if quantum_enabled:
            actual_qubits = min(n_components, max_qubits)
            quantum_models = ["vqc"]
            quantum_config = {
                "model":      "VQC",
                "n_qubits":   actual_qubits,
                "n_layers":   2,
                "shots":      1024,
                "epochs":     100,
                "batch_size": 32,
                "learning_rate": 0.01,
                "early_stopping_patience": 5,
                "encoding":   "angle_encoding",
                "backend":    "LOCAL_SIMULATOR",
            }
            if regime == "SMALL":
                quantum_config["shots"] = 512
                rules_applied.append(
                    "RULE-003b: Small dataset → reducing quantum shots to 512."
                )

        # ── Build evaluation config ───────────────────────────────────────────
        split_strategy = "stratified"
        if regime == "SMALL":
            rules_applied.append(
                "RULE-003c: Small dataset → enforce stratified split to preserve class distribution."
            )

        evaluation = {
            "split_strategy": split_strategy,
            "test_size":      test_size,
            "random_state":   random_state,
            "cv_folds":       5,
        }

        # ── Classical model list ──────────────────────────────────────────────
        classical_models = ["logistic_regression", "svm", "random_forest"]

        # ── Assemble full config ──────────────────────────────────────────────
        config = {
            "experiment_id":    f"EXP-{uuid.uuid4().hex[:8].upper()}",
            "created_at":       datetime.now(timezone.utc).isoformat(),
            "task":             task_candidate,
            "dataset_regime":   regime,
            "preprocessing":    ["standard_scaling"],
            "reduction": {
                "method":     "PCA",
                "components": n_components,
            },
            "classical_models": classical_models,
            "quantum_models":   quantum_models,
            "quantum_enabled":  quantum_enabled,
            "quantum_config":   quantum_config,
            "evaluation":       evaluation,
            "use_class_weight": use_class_weight,
            "class_weight":     "balanced" if use_class_weight else None,
            "decision_trace": {
                "rules_applied": rules_applied,
                "errors":        errors,
                "reason":        "Rule-based deterministic planning — no LLM involved.",
                "planner_version": "1.0.0",
            },
        }

        return config
