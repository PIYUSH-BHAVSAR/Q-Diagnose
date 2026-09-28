"""
test_piyush_pipeline.py
Test script for Piyush's ML Models, Orchestration & Benchmarking layer.
Tests all classical models, VQC model, metrics, comparison, recommendation, planner, manager, and executor.
"""

import os
import sys
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))

def test_metrics():
    print("--- 1. Testing MetricsCalculator ---")
    from backend.benchmarking.metrics import MetricsCalculator

    y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0, 0, 1, 1, 0, 1, 0])
    y_scores = np.array([0.9, 0.1, 0.8, 0.4, 0.2, 0.7, 0.6, 0.3, 0.85, 0.15])

    m = MetricsCalculator.compute(y_true, y_pred, y_scores)
    print("Metrics result:", m)
    assert "specificity" in m
    assert m["confusion_matrix"] == [[4, 1], [1, 4]]
    print("[PASS] MetricsCalculator PASSED\n")

def test_classical_models():
    print("--- 2. Testing Classical Models ---")
    from backend.models.classical import LogisticRegressionModel, SVMModel, RandomForestModel

    np.random.seed(42)
    X_train = np.random.randn(100, 10)
    y_train = np.random.randint(0, 2, 100)
    X_test = np.random.randn(25, 10)
    y_test = np.random.randint(0, 2, 25)

    for ModelClass in [LogisticRegressionModel, SVMModel, RandomForestModel]:
        model = ModelClass(random_state=42)
        res = model.fit(X_train, y_train, X_test, y_test)
        assert res.status == "COMPLETED"
        assert res.model_type == "CLASSICAL"
        assert 0.0 <= res.accuracy <= 1.0
        print(f"[PASS] {res.model_name}: accuracy={res.accuracy:.3f}, recall={res.recall:.3f}, auc={res.roc_auc:.3f}")
    print("[PASS] All Classical Models PASSED\n")

def test_quantum_vqc():
    print("--- 3. Testing VQC Quantum Model ---")
    from backend.models.quantum import VQCModel

    np.random.seed(42)
    # 4 qubits / PCA features for fast test, 10 epochs
    X_train_red = np.random.randn(40, 4)
    y_train = np.random.randint(0, 2, 40)
    X_test_red = np.random.randn(10, 4)
    y_test = np.random.randint(0, 2, 10)

    vqc = VQCModel(n_qubits=4, n_layers=2, epochs=5, batch_size=8, random_state=42)
    res = vqc.fit(X_train_red, y_train, X_test_red, y_test)

    assert res.status == "COMPLETED"
    assert res.model_type == "QUANTUM"
    assert res.qubits == 4
    assert res.total_circuit_executions > 0
    print(f"[PASS] VQC: accuracy={res.accuracy:.3f}, recall={res.recall:.3f}, executions={res.total_circuit_executions}")
    print("[PASS] VQC Quantum Model PASSED\n")

def test_planner():
    print("--- 4. Testing ExperimentPlanner ---")
    from backend.planner.experiment_planner import ExperimentPlanner

    class MockProfile:
        task_candidate = "BINARY_CLASSIFICATION"
        rows = 400
        numerical_count = 30

    class MockValidation:
        class_balance = {"imbalance_ratio": 1.8}

    planner = ExperimentPlanner()
    plan_cfg = planner.plan(MockProfile(), MockValidation(), n_components=8)
    assert plan_cfg["quantum_enabled"] is True
    assert plan_cfg["use_class_weight"] is True
    assert len(plan_cfg["decision_trace"]["rules_applied"]) >= 4
    print("[PASS] Planner decision trace rules count:", len(plan_cfg["decision_trace"]["rules_applied"]))
    print("[PASS] ExperimentPlanner PASSED\n")

def test_executor_end_to_end():
    print("--- 5. Testing End-to-End Executor on Fixture Data ---")
    from backend.experiments.executor import ExperimentExecutor

    dataset_path = "fixtures/breast_cancer.csv"
    if not os.path.exists(dataset_path):
        dataset_path = "fixtures/diabetes.csv"

    executor = ExperimentExecutor(dev_mode=True)
    res = executor.run_from_path(dataset_path=dataset_path, n_components=4)

    assert res["status"] == "completed"
    models = res["results"]["models"]
    assert "LogisticRegression" in models
    assert "RandomForest" in models
    assert "SVM" in models
    assert "VQC" in models

    recommendation = res["results"]["comparison"]
    print(f"[PASS] Recommended Classification: {recommendation['classification']}")
    print(f"[PASS] Observation sample count: {len(recommendation['observations'])}")
    print("[PASS] End-to-End Executor PASSED\n")

if __name__ == "__main__":
    print("==========================================")
    print("   RUNNING PIYUSH PIPELINE TEST SUITE    ")
    print("==========================================")
    test_metrics()
    test_classical_models()
    test_quantum_vqc()
    test_planner()
    test_executor_end_to_end()
    print("==========================================")
    print("   ALL TESTS COMPLETED SUCCESSFULLY!      ")
    print("==========================================")
