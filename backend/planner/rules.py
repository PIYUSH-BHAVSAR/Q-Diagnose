"""
backend/planner/rules.py
Owner: Piyush
Phase: 9

PlannerRules — constants and rule functions for the experiment planner.
From phase9.md §5-10 + guide_piyush.md §6:

    "Our initial implementation should be: Rule Engine + Experiment Planner.
     For example: IF feature_dimension <= 16 AND task == binary_classification
                  THEN consider VQC."
    "This is: deterministic and explainable."

Rules (from phase9.md §8-11):
    RULE-001: Task type check — only BINARY_CLASSIFICATION supported
    RULE-002: Quantum feasibility — n_components <= max_qubits
    RULE-003: Dataset regime — small (<500), medium (500-5000), large (>5000)
    RULE-004: Class imbalance handling — imbalance > 1.5 → class_weight='balanced'
    RULE-005: Feature dimension — determines quantum candidacy threshold
"""

from __future__ import annotations

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_QUBITS_DEFAULT = 8           # phase8.md §14 — default max qubits in MVP
SMALL_DATASET_THRESHOLD = 500    # phase9.md §9 — small regime
MEDIUM_DATASET_THRESHOLD = 5000  # phase9.md §9 — medium regime
IMBALANCE_THRESHOLD = 1.5        # phase9.md guide §6 RULE-004
FEATURE_DIM_QUANTUM_HARD_LIMIT = 16   # phase9.md §10

# ── Rule functions ────────────────────────────────────────────────────────────


def rule_001_task_check(task_candidate: str) -> tuple[bool, str]:
    """
    RULE-001: Only BINARY_CLASSIFICATION supported in MVP.
    Returns (passed, message).
    """
    supported = {"BINARY_CLASSIFICATION"}
    if task_candidate in supported:
        return True, f"RULE-001: Task '{task_candidate}' is supported."
    return False, f"RULE-001: Task '{task_candidate}' is NOT supported. Only BINARY_CLASSIFICATION in MVP."


def rule_002_quantum_feasibility(n_components: int, max_qubits: int = MAX_QUBITS_DEFAULT) -> tuple[bool, str]:
    """
    RULE-002: Quantum enabled iff n_components <= max_qubits.
    From guide_piyush.md §9: "Never silently increase qubit count."
    """
    if n_components <= max_qubits:
        return True, f"RULE-002: {n_components} PCA components <= {max_qubits} qubits → quantum ENABLED."
    return False, f"RULE-002: {n_components} PCA components > {max_qubits} qubits → quantum DISABLED."


def rule_003_dataset_regime(n_rows: int) -> tuple[str, str]:
    """
    RULE-003: Classify dataset size regime.
    Returns (regime, message).
    """
    if n_rows < SMALL_DATASET_THRESHOLD:
        return "SMALL", f"RULE-003: {n_rows} samples < {SMALL_DATASET_THRESHOLD} → small regime, use stratified split."
    elif n_rows < MEDIUM_DATASET_THRESHOLD:
        return "MEDIUM", f"RULE-003: {n_rows} samples → medium regime."
    else:
        return "LARGE", f"RULE-003: {n_rows} samples > {MEDIUM_DATASET_THRESHOLD} → large regime, consider QML subset."


def rule_004_class_imbalance(imbalance_ratio: float) -> tuple[bool, str]:
    """
    RULE-004: Apply class_weight='balanced' if imbalance > threshold.
    """
    if imbalance_ratio > IMBALANCE_THRESHOLD:
        return True, f"RULE-004: Imbalance ratio {imbalance_ratio:.2f} > {IMBALANCE_THRESHOLD} → use class_weight='balanced'."
    return False, f"RULE-004: Imbalance ratio {imbalance_ratio:.2f} <= {IMBALANCE_THRESHOLD} → class weights optional."


def rule_005_feature_dimension(n_components: int) -> tuple[str, str]:
    """
    RULE-005: Feature dimension category.
    From phase9.md §10.
    """
    if n_components <= 8:
        return "SMALL_QUANTUM", f"RULE-005: {n_components} features → direct small quantum candidate."
    elif n_components <= 16:
        return "COMPACT_QUANTUM", f"RULE-005: {n_components} features → compact quantum candidate."
    else:
        return "CLASSICAL_ONLY", f"RULE-005: {n_components} features > 16 → quantum requires aggressive compression."
