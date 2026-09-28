"""
test_full_platform_flow.py
Complete End-to-End Integration Test for Phases 1 through 14.

Pipeline Sequence:
  Phase 1: Dataset Upload & Storage Ingestion (Arzaan / Shweta)
  Phases 2-6: Dataset Profiling, Validation, Preprocessing & PCA Feature Reduction (Jayed)
  Phase 9: Experiment Planning & Rule Engine (Piyush)
  Phases 7, 8, 10: Model Training & Execution — LR, SVM, RF + VQC Quantum Circuit (Piyush)
  Phase 11: Benchmarking & Recommendation Verdict (Piyush)
  Phase 12: Model Explainability — SHAP & Quantum Sensitivity (Radha)
  Phases 13 & 14: Cost Report & 16-Section HTML Report Generation (Radha)
"""

import os
import sys
import json
from pathlib import Path

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath("."))

from backend.storage.database import init_db
from backend.main import app
from fastapi.testclient import TestClient

def test_full_pipeline_flow():
    print("==========================================================")
    print("   TESTING FULL PLATFORM PIPELINE FLOW (PHASES 1 - 14)    ")
    print("==========================================================")

    # Initialize DB tables
    init_db()

    with TestClient(app) as client:
        # --------------------------------------------------------------------------
        # STEP 1: Phase 1 & API — Upload Dataset (Arzaan / Shweta)
        # --------------------------------------------------------------------------
        print("\n--- [Phase 1] Uploading Dataset via POST /api/datasets/upload ---")
        sample_csv_path = Path("fixtures/breast_cancer.csv")
        if not sample_csv_path.exists():
            sample_csv_path = Path("fixtures/diabetes.csv")

        with open(sample_csv_path, "rb") as f:
            response = client.post(
                "/api/datasets/upload",
                files={"file": (sample_csv_path.name, f, "text/csv")},
            )

        assert response.status_code == 201, f"Upload failed: {response.text}"
        upload_data = response.json()
        dataset_id = upload_data["dataset_id"]
        display_id = upload_data["display_id"]
        storage_path = upload_data["storage_path"]
        print(f"[PASS] Dataset Uploaded | dataset_id={dataset_id} | display_id={display_id}")
        print(f"       Storage Path: {storage_path}")

        # --------------------------------------------------------------------------
        # STEP 2: Phase 2-6 — Dataset Profiling & Metadata (Jayed)
        # --------------------------------------------------------------------------
        print("\n--- [Phases 2-6] Verifying Profiling & Feature Pipeline Capabilities ---")
        res_list = client.get("/api/datasets")
        assert res_list.status_code == 200
        print(f"[PASS] Registered Datasets Count: {res_list.json()['total']}")

        res_detail = client.get(f"/api/datasets/{dataset_id}")
        assert res_detail.status_code == 200
        print(f"[PASS] Dataset Detail Retrieved | sha256={res_detail.json()['sha256'][:16]}...")

        # --------------------------------------------------------------------------
        # STEP 3: Phase 9, 7, 8, 10 — Create & Run Experiment (Piyush)
        # --------------------------------------------------------------------------
        print("\n--- [Phases 7-10] Creating Experiment Record via POST /api/experiments ---")
        exp_payload = {
            "dataset_id": dataset_id,
            "dataset_path": str(sample_csv_path),
            "n_components": 4,          # 4 PCA components / qubits for fast test execution
            "random_state": 42,
            "quantum_enabled": True,
            "dev_mode": True,            # fast epochs
        }

        res_create = client.post("/api/experiments", json=exp_payload)
        assert res_create.status_code == 201, f"Create experiment failed: {res_create.text}"
        experiment_id = res_create.json()["experiment_id"]
        print(f"[PASS] Experiment Record Created | experiment_id={experiment_id}")

        print("\n--- Running Experiment Executor Pipeline ---")
        from backend.experiments.executor import ExperimentExecutor
        from backend.experiments.manager import ExperimentManager

        manager = ExperimentManager()
        executor = ExperimentExecutor(manager=manager, dev_mode=True)
        
        # Run full training pipeline
        results = executor.run(
            experiment_id=experiment_id,
            dataset_path=str(sample_csv_path),
            n_components=4,
            random_state=42,
            quantum_enabled=True,
        )

        assert results["status"] == "completed"
        print(f"[PASS] Execution Engine COMPLETED | Models Trained: {list(results['results']['models'].keys())}")

        # --------------------------------------------------------------------------
        # STEP 4: Phase 11 — Benchmarking & Recommendation Verdict (Piyush)
        # --------------------------------------------------------------------------
        print("\n--- [Phase 11] Polling Results & Recommendation API ---")
        res_status = client.get(f"/api/experiments/{experiment_id}/status")
        assert res_status.status_code == 200
        assert res_status.json()["status"] == "COMPLETED"
        print(f"[PASS] Experiment Status API: {res_status.json()['status']}")

        res_results = client.get(f"/api/experiments/{experiment_id}/results")
        assert res_results.status_code == 200
        print(f"[PASS] Experiment Results API: {len(res_results.json()['results']['models'])} models present")

        res_rec = client.get(f"/api/experiments/{experiment_id}/recommendation")
        assert res_rec.status_code == 200
        rec_data = res_rec.json()
        print(f"[PASS] Recommendation Verdict: {rec_data['classification']}")
        print(f"       Recommendation Text: {rec_data['recommendation_text'][:120]}...")

        # --------------------------------------------------------------------------
        # STEP 5: Phase 12 — Explainability API (Radha)
        # --------------------------------------------------------------------------
        print("\n--- [Phase 12] Requesting Model Explanations via GET /api/experiments/{id}/explanation ---")
        res_exp = client.get(f"/api/experiments/{experiment_id}/explanation")
        assert res_exp.status_code == 200
        exp_data = res_exp.json()
        print(f"[PASS] Explainability Data Generated for Models: {exp_data['models_explained']}")
        print(f"       Explainer Method: {exp_data['explainability_method']}")
        if exp_data.get("quantum_circuit_info"):
            qci = exp_data["quantum_circuit_info"]
            # Multi-model format: {"VQC": {...}, "QuantumSVM": {...}}
            if "qubits" in qci:
                print(f"       Quantum Qubits: {qci['qubits']}")
            else:
                for qname, qinfo in qci.items():
                    print(f"       {qname} Qubits: {qinfo.get('qubits', 'N/A')}")

        # --------------------------------------------------------------------------
        # STEP 6: Phase 13 & 14 — HTML & Cost Report Generation (Radha)
        # --------------------------------------------------------------------------
        print("\n--- [Phases 13 & 14] Generating 16-Section Report via POST /api/experiments/{id}/report ---")
        res_rpt_gen = client.post(f"/api/experiments/{experiment_id}/report")
        assert res_rpt_gen.status_code == 200
        rpt_info = res_rpt_gen.json()
        print(f"[PASS] Report Generated | report_id={rpt_info['report_id']}")
        print(f"       Report Path: {rpt_info['report_path']}")
        print(f"       Cost Report Path: {rpt_info['cost_report_path']}")

        # Download / View HTML Report
        res_rpt = client.get(f"/api/experiments/{experiment_id}/report")
        assert res_rpt.status_code == 200
        assert "RESEARCH / BENCHMARKING SYSTEM" in res_rpt.text
        assert "Q-Diagnose" in res_rpt.text
        print(f"[PASS] HTML Report Content Verified ({len(res_rpt.text)} bytes)")

        # --------------------------------------------------------------------------
        # STEP 7: Deliverable 4 — Live Patient Inference & Threshold Tuning
        # --------------------------------------------------------------------------
        print("\n--- [PS Deliverable 4] Testing Live Patient Scoring & Threshold Tuning ---")
        pred_payload = {
            "features": [17.99, 10.38, 122.8, 1001.0],
            "decision_threshold": 0.35,
            "model_name": "vqc",
        }
        res_pred = client.post(f"/api/experiments/{experiment_id}/predict", json=pred_payload)
        assert res_pred.status_code == 200, f"Predict failed: {res_pred.text}"
        pred_data = res_pred.json()
        print(f"[PASS] Patient Scoring API: Prediction={pred_data['prediction_label']}")
        print(f"       Risk Level: {pred_data['risk_stratification']['risk_level']}")
        print(f"       Action: {pred_data['risk_stratification']['action_recommendation']}")

        res_tune = client.post(f"/api/experiments/{experiment_id}/threshold-tune?target_sensitivity=0.90")
        assert res_tune.status_code == 200
        tune_data = res_tune.json()
        print(f"[PASS] Threshold Tuning API: Optimal Threshold={tune_data['optimal_threshold']} (Achieved Sensitivity={tune_data['achieved_sensitivity']:.1%})")

        # --------------------------------------------------------------------------
        # STEP 8: Naeem's Frontend UI Verification
        # --------------------------------------------------------------------------
        print("\n--- [Naeem's Module] Verifying Clinical Frontend UI ---")
        res_ui = client.get("/")
        assert res_ui.status_code == 200, f"UI route failed: {res_ui.status_code}"
        assert "Q-Diagnose" in res_ui.text
        assert "Hybrid Quantum-Classical Disease Detection Platform" in res_ui.text
        print(f"[PASS] Clinical UI SPA Loaded Successfully ({len(res_ui.text)} bytes)")

    print("\n==========================================================")
    print("   ALL PHASES (1 - 14 + UI) INTEGRATED & VERIFIED!        ")
    print("==========================================================")

if __name__ == "__main__":
    test_full_pipeline_flow()
