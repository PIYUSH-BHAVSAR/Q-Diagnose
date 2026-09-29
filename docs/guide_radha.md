# Developer Guide — Radha
## Scope: Explainability (Classical + Quantum) and Report / Resource Generation

---

## 1. Scope Summary

You own the **"why" and "how much" layers** — the two final analytical layers that transform raw model predictions and resource measurements into evidence that judges and users can actually understand. Your work covers two phases: (1) **Explainability** (Phase 12) — for classical models you produce SHAP-based feature importance and prediction-level explanations; for the quantum model you produce perturbation-based feature importance, circuit structure visualization data, and a complete pipeline lineage trace; (2) **Cost and resource reporting** (Phase 13) — you collect CPU time, RAM usage, training time, inference time, and quantum-specific metrics (qubits, shots, circuit executions) then assemble them into a `cost_report.json` with performance-vs-cost comparison and a plain-language scalability assessment. You also own the FastAPI endpoints that serve these results and the final HTML/JSON report generator that produces the experiment summary document. You work entirely from outputs that Piyush has already computed — you receive `ModelResult` objects and the `ComparisonResult`. You never re-run models. You never train anything. Your job is interpretation and communication.

---

## 2. Exact Phase Numbers

From the **architecture document**:
- **Phase 12** (phase12.md): Explainability & Interpretation — Levels 1–4 (§4), Prediction explanation (§6–7), Classical SHAP (§8–9), Quantum perturbation-based methods (§10–12), Quantum feature ablation (§12), Quantum circuit explanation (§14–15), Pipeline trace (§16–17), Decision trace from Phase 9 (§18–19), Global explainability (§22–23), Error analysis (§24–25), Explanation artifacts (§31), Four-tab dashboard (§36–40), Explanation warnings/disclaimers (§42).
- **Phase 13** (phase13.md): Cost, Scalability & Deployment — Computational cost (§4), Quantum cost metrics (§5), Financial cost local (§6), Resource profiler (§8), Example resource report (§9), Dataset-size scaling (§10), Performance-vs-cost curve (§33), Pareto frontier (§36), Scalability decision (§44), User-level cost view (§41), System-level cost breakdown (§42–43), Phase 13 output (§46).
- **Phase 15** (phase15.md §24–30): Report structure — 16 sections, executive summary, limitations, conclusion language.

From the **MVP implementation plan**:
- **MVP Phase 17** (§40–41): Explainability — SHAP for classical, circuit trace + PCA lineage for quantum.
- **MVP Phase 18** (§42–44): Resource monitoring — `time.perf_counter()`, `psutil`, quantum circuit executions.
- **MVP Phase 19** (§45): Cost analysis — show local execution metrics, no fake cloud costs.
- **MVP Phase 20** (§46–48): Final recommendation — already from Piyush's benchmarking, you display it.
- **MVP Phase 23** (§51): Report generation — HTML/PDF with 16 sections.
- **API Design** (§78): `GET /api/experiments/{id}/explanation`, `POST /api/experiments/{id}/report`, `GET /api/experiments/{id}/report`.

---

## 3. Files / Folders You Must Create

All paths relative to `d:\projects\SIH2026\mvp\`:

```
backend/
├── explainability/
│   ├── __init__.py
│   ├── classical.py          ← ClassicalExplainer: SHAP + feature importance
│   └── quantum.py            ← QuantumExplainer: perturbation + circuit info + lineage
│
└── reports/
    ├── __init__.py
    └── generator.py          ← ReportGenerator: assembles final HTML report

artifacts/
└── reports/                  ← output directory for generated HTML reports
```

You extend the experiments API:
```
backend/api/
└── experiments.py            ← ADD these routes (Piyush owns this file but you add to it):
    GET /api/experiments/{id}/explanation
    POST/GET /api/experiments/{id}/report
```

You do NOT create or modify:
- `backend/models/` → Piyush
- `backend/benchmarking/` → Piyush
- `backend/data/` → Jayed
- `backend/storage/` → Arzaan
- `backend/api/datasets.py` → Shweta

---

## 4. Input Contract (what you consume)

You receive **Piyush's** `ModelResult` objects from `artifacts/experiments/{id}/` or directly from the executor. The exact fields you need:

```python
# From ModelResult (Piyush's output):
result.model_name             # "LogisticRegression", "SVM", "RandomForest", "VQC"
result.model_type             # "CLASSICAL" or "QUANTUM"
result.predictions_test       # np.ndarray of 0/1 predictions
result.scores_test            # np.ndarray of probability scores
result.accuracy               # float
result.recall                 # float
result.specificity            # float
result.roc_auc                # float
result.confusion_matrix       # [[TN, FP], [FN, TP]]
result.training_time_seconds  # float
result.inference_time_seconds # float
result.memory_peak_mb         # float
result.qubits                 # int (VQC only, else None)
result.circuit_depth          # int (VQC only)
result.gate_count             # int (VQC only)
result.two_qubit_gates        # int (VQC only)
result.shots                  # int (VQC only)
result.total_circuit_executions # int (VQC only)
result.backend_type           # "LOCAL_SIMULATOR" (VQC only)

# The actual fitted model object (for SHAP):
result._model                 # sklearn estimator — you need Piyush to expose this
```

You also receive the `FeaturePipelineResult` from Jayed (for building pipeline trace and feature names):
```python
processed.X_test              # np.ndarray — needed for SHAP explainer
processed.X_test_reduced      # np.ndarray — needed for quantum perturbation
processed.feature_names       # List[str]  — original feature names
processed.reduced_feature_names  # ["PC1", ..., "PC8"]
processed.n_components        # 8
processed.preprocessing_id    # "PREP-000001"
processed.variance_retained   # 0.94
```

And the experiment config from Piyush's planner:
```python
plan["decision_trace"]["rules_applied"]  # list of rules for pipeline trace
plan["reduction"]["components"]           # 8
plan["quantum_enabled"]                   # True/False
```

---

## 5. Output Contracts

### 5a. `contracts/explanation.json` — consumed by frontend and Naeem's explainability tab

```json
{
  "explanation_id":  "EXPL-000001",
  "experiment_id":   "EXP-Q-000001",
  "sample_id":       "TEST_SAMPLE_042",
  "prediction": {
    "value":        1,
    "score":        0.873,
    "actual_label": 1,
    "is_correct":   true
  },
  "feature_importance": [
    { "feature_name": "mean_radius",
      "feature_index": 0, "feature_value": 17.23,
      "importance": 0.312, "effect": "positive" },
    { "feature_name": "worst_concave_points",
      "feature_index": 7, "feature_value": 0.145,
      "importance": 0.241, "effect": "positive" },
    { "feature_name": "mean_texture",
      "feature_index": 1, "feature_value": 10.38,
      "importance": 0.087, "effect": "negative" }
  ],
  "global_importance": [
    { "feature_name": "worst_radius",         "importance": 0.187 },
    { "feature_name": "worst_concave_points", "importance": 0.156 },
    { "feature_name": "mean_concave_points",  "importance": 0.134 }
  ],
  "quantum_circuit_explanation": {
    "qubits": 8, "circuit_depth": 12, "encoding_method": "angle_encoding",
    "feature_to_qubit_mapping": {
      "PC1": "qubit_0", "PC2": "qubit_1", "PC8": "qubit_7"
    },
    "circuit_diagram_url": null
  },
  "pipeline_trace": [
    { "phase": "Phase 1", "component": "Ingestion",        "artifact": "DS-000001" },
    { "phase": "Phase 4", "component": "Preprocessing",    "artifact": "PREP-000001" },
    { "phase": "Phase 6", "component": "Feature Reduction","artifact": "QREP-000001",
      "method": "PCA", "dimensions": "30 -> 8" },
    { "phase": "Phase 8", "component": "Quantum Model",    "artifact": "VQC", "qubits": 8 },
    { "phase": "Phase 10","component": "Execution",        "artifact": "EXP-Q-000001",
      "backend": "LOCAL_SIMULATOR" }
  ],
  "model_decision_reason": "The model predicted POSITIVE (malignant) with score 0.873...",
  "warnings": [
    "Explanation based on perturbation analysis — not causal.",
    "Score is uncalibrated — not a clinical probability.",
    "Research system output — not a clinical diagnosis."
  ],
  "explainability_method": "feature_perturbation",
  "explanation_timestamp": "2026-09-10T16:45:23.789Z"
}
```

### 5b. `contracts/cost_report.json` — consumed by frontend cost tab and final report

```json
{
  "experiment_id": "EXP-Q-000001",
  "report_timestamp": "2026-09-10T16:30:00Z",
  "performance_summary": { "roc_auc": 0.94, "recall": 0.935 },
  "computational_cost": {
    "training": {
      "wall_clock_time_seconds": 842,
      "ram_peak_gb": 3.2,
      "cpu_utilization_avg_percent": 82
    },
    "inference": { "avg_time_ms": 45 }
  },
  "quantum_cost": {
    "qubits": 8, "circuit_depth": 12,
    "gate_count": 156, "two_qubit_gates": 42,
    "shots_per_execution": 1024,
    "total_circuit_executions": 19932
  },
  "pipeline_cost_breakdown": {
    "preprocessing_seconds": 12,
    "feature_reduction_seconds": 3,
    "quantum_training_seconds": 842,
    "evaluation_seconds": 8,
    "total_pipeline_seconds": 865,
    "quantum_percentage": 97.3
  },
  "comparison_classical_baseline": {
    "classical_model": "RandomForest",
    "classical_training_seconds": 42,
    "quantum_training_seconds": 842,
    "speedup_classical": 20.0,
    "verdict": "Classical RandomForest trains 20x faster with 1.2pp higher ROC-AUC"
  },
  "scalability_assessment": {
    "current_environment": "LOCAL_LAPTOP",
    "this_experiment_status": "FEASIBLE",
    "recommended_max_qubits": 8,
    "note": "16 qubits would require ~16GB RAM"
  },
  "financial_cost_local": { "estimate": 0, "note": "Local execution. No cloud cost." }
}
```

---

## 6. Step-by-Step Build Order

### Day 1

**Hour 1–2: Classical Explainer with SHAP**

```python
# backend/explainability/classical.py
import shap
import numpy as np
from typing import List, Optional

class ClassicalExplainer:
    """SHAP-based explainability for classical sklearn models."""
    
    def __init__(self, model, model_name: str, feature_names: List[str]):
        """
        model: fitted sklearn estimator (LogisticRegression, SVC, RandomForest)
        """
        self.model = model
        self.model_name = model_name
        self.feature_names = feature_names
        self._explainer = None
        self._shap_values = None
    
    def fit_explainer(self, X_train: np.ndarray):
        """Fit SHAP explainer on training data. Call after model is trained."""
        if self.model_name == "RandomForest":
            self._explainer = shap.TreeExplainer(self.model)
        elif self.model_name in ("LogisticRegression",):
            self._explainer = shap.LinearExplainer(
                self.model, X_train, feature_perturbation="interventional"
            )
        else:
            # Model-agnostic fallback — works for SVM
            self._explainer = shap.KernelExplainer(
                self.model.predict_proba,
                shap.sample(X_train, min(50, len(X_train)))  # background sample
            )
    
    def global_importance(self, X_test: np.ndarray, top_k: int = 10) -> List[dict]:
        """
        Returns top_k features by mean absolute SHAP value across test set.
        """
        if self._explainer is None:
            raise RuntimeError("Call fit_explainer() first")
        
        shap_values = self._explainer.shap_values(X_test)
        
        # For binary classification, shap_values may be [class0, class1] — take class 1
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        mean_abs = np.abs(shap_values).mean(axis=0)
        ranked_idx = np.argsort(mean_abs)[::-1][:top_k]
        
        return [
            {
                "feature_name":  self.feature_names[i],
                "feature_index": int(i),
                "importance":    float(mean_abs[i]),
                "rank":          int(rank + 1)
            }
            for rank, i in enumerate(ranked_idx)
        ]
    
    def explain_sample(self, sample: np.ndarray, actual_label: Optional[int] = None,
                       prediction: Optional[int] = None,
                       score: Optional[float] = None) -> List[dict]:
        """
        Returns per-feature SHAP explanation for a single sample.
        """
        if self._explainer is None:
            raise RuntimeError("Call fit_explainer() first")
        
        shap_values = self._explainer.shap_values(sample.reshape(1, -1))
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        sv = shap_values[0]  # shape (n_features,)
        ranked_idx = np.argsort(np.abs(sv))[::-1]
        
        return [
            {
                "feature_name":  self.feature_names[i],
                "feature_index": int(i),
                "feature_value": float(sample[i]),
                "importance":    float(abs(sv[i])),
                "effect":        "positive" if sv[i] > 0 else "negative",
                "shap_value":    float(sv[i])
            }
            for i in ranked_idx
        ]
```

Test against Breast Cancer (use Piyush's mock data or real pipeline):
```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from backend.explainability.classical import ClassicalExplainer

# Quick test with random data
X_train = np.random.randn(200, 10)
y_train = (X_train[:, 0] + X_train[:, 2] > 0).astype(int)
X_test  = np.random.randn(50, 10)
feature_names = [f"feat_{i}" for i in range(10)]

model = RandomForestClassifier(n_estimators=10, random_state=42).fit(X_train, y_train)
explainer = ClassicalExplainer(model, "RandomForest", feature_names)
explainer.fit_explainer(X_train)

global_imp = explainer.global_importance(X_test)
print("Global importance:", global_imp[:3])
assert len(global_imp) <= 10
assert all("feature_name" in x for x in global_imp)

sample_exp = explainer.explain_sample(X_test[0])
print("Sample explanation:", sample_exp[:2])
```

**Hour 2–4: Quantum Explainer (perturbation-based)**

For the quantum VQC, SHAP doesn't apply directly because the quantum circuit operates on PCA components, not original features. Use perturbation:

```python
# backend/explainability/quantum.py
import numpy as np
from typing import List, Optional

class QuantumExplainer:
    """
    Perturbation-based feature importance for VQC.
    Also generates circuit structure information and pipeline trace.
    """
    
    def __init__(self, vqc_model, feature_names: List[str],
                 original_feature_names: List[str]):
        """
        vqc_model: fitted VQCModel instance
        feature_names: PCA component names ["PC1", ..., "PC8"]
        original_feature_names: original feature names ["radius_mean", ...]
        """
        self.model = vqc_model
        self.feature_names = feature_names          # quantum input features (PCA)
        self.original_names = original_feature_names  # original features (for UI)
    
    def perturbation_importance(self, X_test: np.ndarray,
                                 n_perturbations: int = 10) -> List[dict]:
        """
        Compute feature importance by perturbing each feature and measuring
        change in prediction probability.
        
        Returns features ranked by mean |delta_score| across test samples.
        """
        baseline_scores = self._predict_scores(X_test)
        
        importance = np.zeros(X_test.shape[1])
        
        for feat_idx in range(X_test.shape[1]):
            deltas = []
            for _ in range(n_perturbations):
                X_perturbed = X_test.copy()
                # Perturb feature with noise
                noise = np.random.normal(0, 0.5, len(X_test))
                X_perturbed[:, feat_idx] += noise
                perturbed_scores = self._predict_scores(X_perturbed)
                deltas.append(np.mean(np.abs(perturbed_scores - baseline_scores)))
            importance[feat_idx] = np.mean(deltas)
        
        # Normalize
        if importance.max() > 0:
            importance = importance / importance.max()
        
        ranked_idx = np.argsort(importance)[::-1]
        return [
            {
                "feature_name":  self.feature_names[i],
                "feature_index": int(i),
                "importance":    float(importance[i]),
                "rank":          int(rank + 1)
            }
            for rank, i in enumerate(ranked_idx)
        ]
    
    def explain_sample(self, sample: np.ndarray, prediction: int,
                       score: float, actual_label: Optional[int] = None) -> List[dict]:
        """Perturbation importance for a single sample."""
        baseline = self._predict_single_score(sample)
        results = []
        
        for feat_idx in range(len(sample)):
            deltas = []
            for _ in range(5):
                s = sample.copy()
                s[feat_idx] += np.random.normal(0, 0.5)
                deltas.append(abs(self._predict_single_score(s) - baseline))
            
            importance = float(np.mean(deltas))
            results.append({
                "feature_name":  self.feature_names[feat_idx],
                "feature_index": int(feat_idx),
                "feature_value": float(sample[feat_idx]),
                "importance":    importance,
                "effect":        "positive" if sample[feat_idx] > 0 else "negative"
            })
        
        return sorted(results, key=lambda x: x["importance"], reverse=True)
    
    def circuit_info(self) -> dict:
        """Return quantum circuit structure for display."""
        return {
            "qubits":          self.model.n_qubits,
            "n_layers":        self.model.n_layers,
            "circuit_depth":   self.model.n_layers * 2 + 1,
            "encoding_method": "angle_encoding",
            "backend_type":    "LOCAL_SIMULATOR",
            "feature_to_qubit_mapping": {
                name: f"qubit_{i}"
                for i, name in enumerate(self.feature_names)
            },
            "measurement": "PauliZ(qubit_0)"
        }
    
    def _predict_scores(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities for a batch."""
        # Call VQC's circuit with stored parameters
        circuit = self.model._circuit
        params  = self.model._params
        encoder = self.model.encoder
        
        X_enc = encoder.scale_features(X)
        raw   = np.array([circuit(x, params) for x in X_enc])
        return (raw + 1) / 2  # PauliZ [-1,1] → [0,1]
    
    def _predict_single_score(self, sample: np.ndarray) -> float:
        circuit = self.model._circuit
        params  = self.model._params
        x_enc   = self.model.encoder.scale_features(sample.reshape(1, -1))[0]
        raw     = float(circuit(x_enc, params))
        return (raw + 1) / 2
```

**Note on quantum perturbation performance:** `perturbation_importance()` runs multiple circuit executions per feature. For 8 features × 10 perturbations × test set, this adds up. Use `n_perturbations=5` for development, limit test set to 20 samples for the explanation demo. The explanation is computed once and cached.

**Hour 4–6: Pipeline Trace Builder**

```python
# Part of backend/explainability/quantum.py or a shared utility

def build_pipeline_trace(dataset_id: str, preprocessing_id: str,
                          n_original_features: int, n_reduced_features: int,
                          experiment_id: str, model_name: str,
                          backend_type: str, plan_decision_trace: dict) -> List[dict]:
    """
    Build the complete pipeline lineage trace for the explanation.
    Every prediction should be traceable back to its source.
    """
    trace = [
        {
            "phase": "Phase 1",
            "component": "Dataset Ingestion",
            "artifact": dataset_id,
            "description": "Raw CSV received, hashed, registered"
        },
        {
            "phase": "Phase 4",
            "component": "Preprocessing",
            "artifact": preprocessing_id,
            "description": "StandardScaler fitted on training data only"
        },
    ]
    
    if n_original_features != n_reduced_features:
        trace.append({
            "phase": "Phase 6",
            "component": "Dimensionality Reduction",
            "artifact": f"QREP-{experiment_id[-6:]}",
            "method": "PCA",
            "dimensions": f"{n_original_features} → {n_reduced_features}",
            "description": "PCA fitted on training data. Test set transformed separately."
        })
    
    trace.append({
        "phase": "Phase 8",
        "component": "Model",
        "artifact": model_name,
        "description": f"{'Variational Quantum Classifier' if model_name == 'VQC' else model_name}"
    })
    
    trace.append({
        "phase": "Phase 10",
        "component": "Execution",
        "artifact": experiment_id,
        "backend": backend_type,
        "decision_rules": plan_decision_trace.get("rules_applied", [])
    })
    
    return trace
```

**Hour 6–8: Cost Report Generator**

```python
# backend/reports/generator.py (cost section)

class CostReportGenerator:
    def generate(self, experiment_id: str, all_results: dict,
                 best_classical_name: str) -> dict:
        """
        all_results: {"logistic_regression": ModelResult, "vqc": ModelResult, ...}
        """
        vqc = all_results.get("vqc")
        classical_best = all_results.get(best_classical_name)
        
        if vqc is None:
            return {"error": "No quantum model result available"}
        
        # Pipeline cost breakdown
        total_time = sum(
            r.training_time_seconds + r.inference_time_seconds
            for r in all_results.values()
        )
        quantum_time = (vqc.training_time_seconds + vqc.inference_time_seconds)
        quantum_pct  = (quantum_time / total_time * 100) if total_time > 0 else 0
        
        # Classical comparison
        verdict = "COMPARABLE"
        if classical_best:
            speedup = vqc.training_time_seconds / max(
                classical_best.training_time_seconds, 0.001)
            if speedup > 5 and classical_best.roc_auc >= vqc.roc_auc:
                verdict = f"Classical {best_classical_name} trains {speedup:.1f}x faster with comparable or higher AUC"
            elif vqc.recall > classical_best.recall + 0.03:
                verdict = f"VQC achieves +{(vqc.recall - classical_best.recall)*100:.1f}pp higher recall at {speedup:.1f}x compute cost"
        
        return {
            "experiment_id": experiment_id,
            "report_timestamp": datetime.utcnow().isoformat() + "Z",
            "performance_summary": {
                "roc_auc": vqc.roc_auc,
                "recall":  vqc.recall
            },
            "computational_cost": {
                "training": {
                    "wall_clock_time_seconds": round(vqc.training_time_seconds, 1),
                    "ram_peak_gb": round(vqc.memory_peak_mb / 1024, 2),
                },
                "inference": {
                    "avg_time_ms": round(vqc.inference_time_seconds * 1000, 1)
                }
            },
            "quantum_cost": {
                "qubits":                  vqc.qubits,
                "circuit_depth":           vqc.circuit_depth,
                "gate_count":              vqc.gate_count,
                "two_qubit_gates":         vqc.two_qubit_gates,
                "shots_per_execution":     vqc.shots,
                "total_circuit_executions": vqc.total_circuit_executions,
            },
            "pipeline_cost_breakdown": {
                "total_pipeline_seconds":  round(total_time, 1),
                "quantum_training_seconds": round(vqc.training_time_seconds, 1),
                "quantum_percentage":       round(quantum_pct, 1),
            },
            "comparison_classical_baseline": {
                "classical_model":          best_classical_name,
                "classical_training_secs":  round(classical_best.training_time_seconds, 1),
                "quantum_training_secs":    round(vqc.training_time_seconds, 1),
                "verdict":                  verdict,
            },
            "scalability_assessment": self._scalability_verdict(vqc.qubits),
            "financial_cost_local": {
                "estimate": 0,
                "note": "Local execution. No cloud quantum cost."
            }
        }
    
    def _scalability_verdict(self, n_qubits: int) -> dict:
        if n_qubits <= 8:
            status = "FEASIBLE"
            note = f"{n_qubits} qubits: feasible on local machine."
        elif n_qubits <= 12:
            status = "FEASIBLE_HIGH_RESOURCE"
            note = f"{n_qubits} qubits: feasible but requires high RAM (6–16GB)."
        else:
            status = "NOT_RECOMMENDED_LOCAL"
            note = f"{n_qubits} qubits: not recommended for local simulation."
        return {
            "current_environment": "LOCAL_LAPTOP",
            "this_experiment_status": status,
            "recommended_max_qubits": 8,
            "note": note
        }
```

### Day 2

**Hour 1–3: Full Explanation Assembler**

```python
# backend/explainability/ — explanation orchestrator

class ExplainabilityEngine:
    """Orchestrates explanation generation for all models in an experiment."""
    
    def explain_experiment(self, experiment_id: str, all_results: dict,
                            processed: "FeaturePipelineResult",
                            plan: dict, dataset_id: str) -> dict:
        """
        Returns a dict keyed by model_name, each value = explanation.json shape.
        """
        explanations = {}
        
        for model_name, result in all_results.items():
            if result.model_type == "CLASSICAL":
                explanation = self._explain_classical(
                    model_name, result, processed, experiment_id
                )
            else:
                explanation = self._explain_quantum(
                    model_name, result, processed, plan, experiment_id, dataset_id
                )
            explanations[model_name] = explanation
        
        return explanations
    
    def _explain_classical(self, model_name, result, processed, experiment_id):
        explainer = ClassicalExplainer(
            result._model, model_name, processed.feature_names
        )
        explainer.fit_explainer(processed.X_train)
        
        global_imp = explainer.global_importance(processed.X_test, top_k=10)
        
        # Explain one example prediction (use first test sample for demo)
        sample_idx  = 0
        sample      = processed.X_test[sample_idx]
        prediction  = int(result.predictions_test[sample_idx])
        score       = float(result.scores_test[sample_idx])
        actual      = int(processed.y_test[sample_idx])
        
        local_exp = explainer.explain_sample(sample, actual, prediction, score)
        
        return self._build_explanation_dict(
            experiment_id=experiment_id,
            model_name=model_name,
            sample_idx=sample_idx,
            prediction=prediction,
            score=score,
            actual=actual,
            feature_importance=local_exp[:10],
            global_importance=global_imp,
            quantum_circuit=None,
            pipeline_trace=self._classical_trace(experiment_id),
            method="SHAP"
        )
    
    def _explain_quantum(self, model_name, result, processed, plan,
                         experiment_id, dataset_id):
        q_explainer = QuantumExplainer(
            result._model,
            processed.reduced_feature_names,
            processed.feature_names
        )
        
        # Limit to small subset for performance
        X_subset = processed.X_test_reduced[:20]
        global_imp = q_explainer.perturbation_importance(X_subset, n_perturbations=5)
        
        sample_idx = 0
        sample     = processed.X_test_reduced[sample_idx]
        prediction = int(result.predictions_test[sample_idx])
        score      = float(result.scores_test[sample_idx])
        actual     = int(processed.y_test[sample_idx])
        
        local_exp = q_explainer.explain_sample(sample, prediction, score, actual)
        circuit_info = q_explainer.circuit_info()
        
        pipeline_trace = build_pipeline_trace(
            dataset_id=dataset_id,
            preprocessing_id=processed.preprocessing_id,
            n_original_features=len(processed.feature_names),
            n_reduced_features=processed.n_components,
            experiment_id=experiment_id,
            model_name="VQC",
            backend_type="LOCAL_SIMULATOR",
            plan_decision_trace=plan.get("decision_trace", {})
        )
        
        return self._build_explanation_dict(
            experiment_id=experiment_id,
            model_name=model_name,
            sample_idx=sample_idx,
            prediction=prediction,
            score=score,
            actual=actual,
            feature_importance=local_exp[:8],
            global_importance=global_imp,
            quantum_circuit=circuit_info,
            pipeline_trace=pipeline_trace,
            method="feature_perturbation"
        )
    
    def _build_explanation_dict(self, experiment_id, model_name, sample_idx,
                                 prediction, score, actual, feature_importance,
                                 global_importance, quantum_circuit, pipeline_trace,
                                 method):
        from datetime import datetime
        is_correct = (prediction == actual) if actual is not None else None
        
        return {
            "explanation_id":       f"EXPL-{experiment_id[-8:]}-{model_name}",
            "experiment_id":        experiment_id,
            "sample_id":            f"TEST_SAMPLE_{sample_idx:03d}",
            "prediction": {
                "value":        prediction,
                "score":        round(score, 4),
                "actual_label": actual,
                "is_correct":   is_correct
            },
            "feature_importance":   feature_importance,
            "global_importance":    global_importance,
            "quantum_circuit_explanation": quantum_circuit,
            "pipeline_trace":       pipeline_trace,
            "model_decision_reason": self._generate_reason(
                model_name, prediction, score, feature_importance),
            "warnings": [
                "Explanation is based on model behavior, not medical causality.",
                "Score is uncalibrated — not a clinical probability.",
                "This is a research/benchmarking system. Not a clinical diagnosis."
            ],
            "explainability_method": method,
            "explanation_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_reason(self, model_name, prediction, score, top_features):
        label = "POSITIVE (disease)" if prediction == 1 else "NEGATIVE (healthy)"
        top = top_features[0]["feature_name"] if top_features else "unknown"
        return (
            f"The {model_name} model predicted {label} with score {score:.3f}. "
            f"The strongest contributing feature was '{top}'. "
            f"This prediction is for research benchmarking only."
        )
    
    def _classical_trace(self, experiment_id):
        return [
            {"phase": "Phase 1", "component": "Ingestion",     "artifact": "dataset"},
            {"phase": "Phase 4", "component": "Preprocessing", "artifact": "StandardScaler"},
            {"phase": "Phase 7", "component": "Classical Model","artifact": "sklearn"},
            {"phase": "Phase 10","component": "Execution",     "artifact": experiment_id}
        ]
```

**Hour 3–5: HTML Report Generator**

```python
# backend/reports/generator.py
from datetime import datetime

class ReportGenerator:
    """Generates an HTML experiment report matching the 16-section structure."""
    
    TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <title>QuantWarriors QML Experiment Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; }}
    h1 {{ color: #1a1a2e; }}
    h2 {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 5px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #0f3460; color: white; }}
    .highlight {{ background-color: #e8f5e9; }}
    .warning {{ color: #e65100; font-style: italic; }}
    .metric-good {{ color: #2e7d32; font-weight: bold; }}
    .disclaimer {{ background: #fff3e0; border: 1px solid #e65100; 
                   padding: 15px; margin: 20px 0; }}
  </style>
</head>
<body>
  <h1>🔬 QuantWarriors — Hybrid QML Experiment Report</h1>
  <p>Generated: {timestamp} | Experiment: {experiment_id}</p>
  
  <div class="disclaimer">
    <strong>⚠️ RESEARCH / BENCHMARKING SYSTEM</strong><br>
    Predictions generated by this platform are for research and benchmarking purposes 
    only. They are NOT clinical diagnoses. Results must not be used for medical decisions.
  </div>

  <h2>1. Executive Summary</h2>
  {executive_summary}

  <h2>2. Dataset Profile</h2>
  {dataset_profile}

  <h2>3. Experiment Plan</h2>
  {experiment_plan}

  <h2>4. Classical Models — Results</h2>
  {classical_results}

  <h2>5. Quantum Model (VQC) — Results</h2>
  {quantum_results}

  <h2>6. Model Comparison</h2>
  {comparison_table}

  <h2>7. Quantum vs Classical Assessment</h2>
  {assessment}

  <h2>8. Feature Importance (Classical)</h2>
  {classical_importance}

  <h2>9. Feature Importance (Quantum)</h2>
  {quantum_importance}

  <h2>10. Quantum Circuit Information</h2>
  {circuit_info}

  <h2>11. Resource Usage</h2>
  {resource_usage}

  <h2>12. Cost Analysis</h2>
  {cost_analysis}

  <h2>13. Pipeline Lineage</h2>
  {pipeline_trace}

  <h2>14. Limitations</h2>
  {limitations}

  <h2>15. Conclusion</h2>
  {conclusion}

  <h2>16. Reproduction Information</h2>
  {reproduction}
</body>
</html>"""
    
    def generate(self, experiment_id: str, all_results: dict,
                 dataset_profile: dict, plan: dict,
                 comparison: dict, explanations: dict,
                 cost_report: dict) -> str:
        """Returns HTML string."""
        
        sections = {
            "timestamp":       datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "experiment_id":   experiment_id,
            "executive_summary": self._executive_summary(comparison, all_results),
            "dataset_profile":   self._dataset_profile_section(dataset_profile),
            "experiment_plan":   self._plan_section(plan),
            "classical_results": self._classical_table(all_results),
            "quantum_results":   self._quantum_section(all_results),
            "comparison_table":  self._comparison_table(all_results),
            "assessment":        self._assessment_section(comparison),
            "classical_importance": self._importance_section(explanations, "RandomForest"),
            "quantum_importance":   self._importance_section(explanations, "VQC"),
            "circuit_info":         self._circuit_section(explanations),
            "resource_usage":       self._resource_section(all_results),
            "cost_analysis":        self._cost_section(cost_report),
            "pipeline_trace":       self._trace_section(explanations),
            "limitations":          self._limitations_section(),
            "conclusion":           self._conclusion_section(comparison),
            "reproduction":         self._reproduction_section(experiment_id, plan),
        }
        
        return self.TEMPLATE.format(**sections)
    
    def _limitations_section(self) -> str:
        return """<ul>
        <li>Results are from a local quantum <strong>simulator</strong>, not real quantum hardware.</li>
        <li>Quantum advantage claims are specific to this dataset and experimental configuration.</li>
        <li>Model scores are uncalibrated and should not be interpreted as clinical probabilities.</li>
        <li>Explainability methods (SHAP, perturbation) describe model behavior, not medical causality.</li>
        <li>Training used 80% of available data — results may vary on different splits or larger datasets.</li>
        </ul>"""
    
    def _conclusion_section(self, comparison: dict) -> str:
        classification = comparison.get("classification", "INCONCLUSIVE")
        observations   = comparison.get("observations", [])
        obs_html = "".join(f"<li>{o}</li>" for o in observations)
        return f"""
        <p><strong>Classification: {classification}</strong></p>
        <ul>{obs_html}</ul>
        <p class="warning">
        These findings are specific to the evaluated dataset and experimental configuration.
        They do not constitute proof of general quantum advantage.
        </p>"""
    
    # ... remaining section helpers follow same pattern
    def _executive_summary(self, comparison, all_results): return "<p>See comparison section.</p>"
    def _dataset_profile_section(self, p): return f"<p>Rows: {p.get('dimensions',{}).get('rows','?')} | Target: {p.get('target',{}).get('candidate','?')}</p>"
    def _plan_section(self, plan): return f"<p>Models: {plan.get('classical_models',[])} + {plan.get('quantum_models',[])}</p>"
    def _classical_table(self, results): return "<p>See model comparison table.</p>"
    def _quantum_section(self, results): return "<p>See model comparison table.</p>"
    def _comparison_table(self, results):
        rows = "".join(
            f"<tr><td>{name}</td><td>{r.model_type}</td>"
            f"<td>{r.accuracy:.3f}</td><td>{r.recall:.3f}</td>"
            f"<td>{r.specificity:.3f}</td><td>{r.roc_auc:.3f}</td>"
            f"<td>{r.training_time_seconds:.1f}s</td></tr>"
            for name, r in results.items()
        )
        return f"""<table><tr>
        <th>Model</th><th>Type</th><th>Accuracy</th><th>Recall</th>
        <th>Specificity</th><th>ROC-AUC</th><th>Train Time</th>
        </tr>{rows}</table>"""
    def _assessment_section(self, c): return f"<p><strong>{c.get('classification','?')}</strong><br>{c.get('recommendation_text','')}</p>"
    def _importance_section(self, explanations, model_name):
        exp = explanations.get(model_name, {})
        items = exp.get("global_importance", [])[:10]
        rows = "".join(f"<tr><td>{x['feature_name']}</td><td>{x['importance']:.4f}</td></tr>" for x in items)
        return f"<table><tr><th>Feature</th><th>Importance</th></tr>{rows}</table>"
    def _circuit_section(self, explanations):
        vqc = explanations.get("VQC", {})
        ci  = vqc.get("quantum_circuit_explanation", {})
        if not ci: return "<p>No quantum circuit info.</p>"
        return f"<p>Qubits: {ci.get('qubits')} | Depth: {ci.get('circuit_depth')} | Encoding: {ci.get('encoding_method')}</p>"
    def _resource_section(self, results):
        rows = "".join(
            f"<tr><td>{name}</td><td>{r.training_time_seconds:.1f}s</td><td>{r.memory_peak_mb:.0f}MB</td></tr>"
            for name, r in results.items()
        )
        return f"<table><tr><th>Model</th><th>Train Time</th><th>Memory</th></tr>{rows}</table>"
    def _cost_section(self, cost): return f"<p>Quantum executions: {cost.get('quantum_cost',{}).get('total_circuit_executions','?')} | Backend: LOCAL_SIMULATOR | Financial cost: ₹0</p>"
    def _trace_section(self, explanations):
        vqc   = explanations.get("VQC", {})
        trace = vqc.get("pipeline_trace", [])
        items = "".join(f"<li><strong>{t['phase']}</strong>: {t['component']} → {t.get('artifact','')}</li>" for t in trace)
        return f"<ul>{items}</ul>"
    def _reproduction_section(self, exp_id, plan):
        return f"<p>Experiment ID: {exp_id} | Seed: {plan.get('evaluation',{}).get('random_state',42)} | Config: config.yaml</p>"
    
    def save(self, html: str, experiment_id: str) -> str:
        import os
        path = f"artifacts/reports/{experiment_id}_report.html"
        os.makedirs("artifacts/reports", exist_ok=True)
        with open(path, "w") as f:
            f.write(html)
        return path
```

**Hour 5–6: FastAPI routes (add to experiments.py)**

Coordinate with Piyush — add these to `backend/api/experiments.py`:

```python
@router.get("/{experiment_id}/explanation")
def get_explanation(experiment_id: str, model_name: str = None, db=Depends(get_db)):
    """
    Returns explanation.json contract.
    Optional ?model_name=VQC to get specific model's explanation.
    """
    # Load stored explanation from artifacts/experiments/{id}/explanations.json
    path = f"artifacts/experiments/{experiment_id}/explanations.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Explanation not yet computed")
    with open(path) as f:
        explanations = json.load(f)
    
    if model_name:
        if model_name not in explanations:
            raise HTTPException(status_code=404, detail=f"No explanation for {model_name}")
        return explanations[model_name]
    return explanations


@router.post("/{experiment_id}/report", status_code=201)
def generate_report(experiment_id: str, db=Depends(get_db)):
    """Generate and save HTML report for a completed experiment."""
    # Load all stored results
    results_path = f"artifacts/experiments/{experiment_id}/results.json"
    if not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail="Experiment results not found")
    
    # Report generation (synchronous — fast enough)
    from backend.reports.generator import ReportGenerator
    generator = ReportGenerator()
    # ... load all required data and generate
    report_path = generator.save(html, experiment_id)
    return {"report_path": report_path, "experiment_id": experiment_id}


@router.get("/{experiment_id}/report")
def get_report(experiment_id: str):
    """Return the HTML report file."""
    path = f"artifacts/reports/{experiment_id}_report.html"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not generated yet")
    from fastapi.responses import FileResponse
    return FileResponse(path, media_type="text/html")
```

**Hour 6–8: End-to-end test**

```python
# Test the full explanation + report pipeline
import json, os

# Assume experiment was already run by Piyush's executor
experiment_id = "TEST-EXP-001"

# Test cost report
from backend.reports.generator import CostReportGenerator
cost_gen = CostReportGenerator()
# ... load model results and run

# Test explanation
from backend.explainability.classical import ClassicalExplainer
# Use mock sklearn model and data
import numpy as np
from sklearn.ensemble import RandomForestClassifier
X = np.random.randn(100, 10)
y = (X[:, 0] > 0).astype(int)
model = RandomForestClassifier(n_estimators=10, random_state=42).fit(X[:80], y[:80])
explainer = ClassicalExplainer(model, "RandomForest", [f"f{i}" for i in range(10)])
explainer.fit_explainer(X[:80])
gi = explainer.global_importance(X[80:])
assert len(gi) <= 10
assert all(0 <= x["importance"] <= 1 for x in gi)

# Test HTML report generation
from backend.reports.generator import ReportGenerator
rg = ReportGenerator()
html = rg.generate(
    experiment_id="TEST-001",
    all_results={},
    dataset_profile={"dimensions": {"rows": 569}, "target": {"candidate": "diagnosis"}},
    plan={"classical_models": ["rf"], "quantum_models": ["vqc"],
          "evaluation": {"random_state": 42}},
    comparison={"classification": "TRADEOFF", "observations": ["VQC recall higher"],
                "recommendation_text": "VQC shows recall tradeoff"},
    explanations={},
    cost_report={"quantum_cost": {"total_circuit_executions": 19932}}
)
assert "<html>" in html
assert "RESEARCH / BENCHMARKING SYSTEM" in html
assert "TRADEOFF" in html
print("Report generated successfully, length:", len(html))
```

---

## 7. Mock Data to Build Against on Day 1

Use this concrete mock `ModelResult` data to test your explainability and report code before Piyush's models are ready:

```python
from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Real sklearn model for SHAP testing
X_train = np.random.RandomState(42).randn(400, 30)
y_train = (X_train[:, 0] + X_train[:, 2] > 0).astype(int)
X_test  = np.random.RandomState(99).randn(100, 30)
y_test  = (X_test[:, 0] + X_test[:, 2] > 0).astype(int)

rf_model = RandomForestClassifier(n_estimators=50, random_state=42).fit(X_train, y_train)
y_pred  = rf_model.predict(X_test)
y_scores = rf_model.predict_proba(X_test)[:, 1]

FEATURE_NAMES = [
    "radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean",
    "compactness_mean", "concavity_mean", "concave_points_mean", "symmetry_mean",
    "fractal_dimension_mean",
    # ... 20 more
] + [f"feature_{i}" for i in range(20)]

# Mock ModelResult (matches Piyush's dataclass)
class MockModelResult:
    model_type    = "CLASSICAL"
    model_name    = "RandomForest"
    accuracy      = 0.953
    recall        = 0.903
    specificity   = 0.982
    roc_auc       = 0.973
    predictions_test = y_pred
    scores_test      = y_scores
    training_time_seconds  = 42.7
    inference_time_seconds = 0.012
    memory_peak_mb = 382.5
    qubits = None
    total_circuit_executions = None
    _model = rf_model

class MockVQCResult:
    model_type    = "QUANTUM"
    model_name    = "VQC"
    accuracy      = 0.941
    recall        = 0.935
    specificity   = 0.945
    roc_auc       = 0.961
    training_time_seconds  = 842.1
    inference_time_seconds = 17.4
    memory_peak_mb = 1247.8
    qubits = 8; circuit_depth = 12; gate_count = 156; two_qubit_gates = 42
    shots = 1024; total_circuit_executions = 19932; backend_type = "LOCAL_SIMULATOR"
```

---

## 8. Definition of Done

**Classical Explainability:**
- [ ] `ClassicalExplainer.fit_explainer()` works for RandomForest (TreeExplainer), LogisticRegression (LinearExplainer), SVM (KernelExplainer fallback).
- [ ] `global_importance()` returns a ranked list of up to 10 features with `feature_name`, `importance`, `rank`.
- [ ] `explain_sample()` returns per-feature SHAP values with `effect` ("positive"/"negative") for a single test sample.
- [ ] SHAP values do not raise errors on Breast Cancer data (569 samples, 30 features).

**Quantum Explainability:**
- [ ] `QuantumExplainer.perturbation_importance()` completes within 2 minutes for 20 test samples, 8 features, 5 perturbations.
- [ ] `circuit_info()` returns qubits, circuit_depth, encoding_method, feature_to_qubit_mapping.
- [ ] `build_pipeline_trace()` returns a list with at least 4 trace steps covering ingestion → preprocessing → reduction → model.

**Cost Report:**
- [ ] `CostReportGenerator.generate()` returns a dict matching `contracts/cost_report.json` structure.
- [ ] `quantum_cost.total_circuit_executions` comes from `ModelResult.total_circuit_executions` — not hardcoded.
- [ ] `financial_cost_local.estimate = 0` always for local execution.
- [ ] `scalability_assessment.this_experiment_status = "FEASIBLE"` for 8-qubit VQC.
- [ ] `pipeline_cost_breakdown.quantum_percentage` reflects actual measured time split.

**HTML Report:**
- [ ] `ReportGenerator.generate()` produces valid HTML with all 16 sections.
- [ ] Report contains the disclaimer: "RESEARCH / BENCHMARKING SYSTEM — not clinical diagnosis".
- [ ] Report contains the comparison table with all 4 models (LR, SVM, RF, VQC).
- [ ] `ReportGenerator.save()` writes the HTML file to `artifacts/reports/{experiment_id}_report.html`.
- [ ] Opening the HTML file in a browser renders without JavaScript errors.

**API endpoints:**
- [ ] `GET /api/experiments/{id}/explanation` returns 200 with explanation.json contract shape.
- [ ] `GET /api/experiments/{id}/explanation?model_name=VQC` returns VQC-specific explanation.
- [ ] `GET /api/experiments/{id}/explanation` returns 404 if explanation not yet computed.
- [ ] `POST /api/experiments/{id}/report` generates the HTML file and returns its path.
- [ ] `GET /api/experiments/{id}/report` serves the HTML file with `Content-Type: text/html`.

**Warnings and disclaimers:**
- [ ] Every explanation JSON contains the three warning strings from the contract.
- [ ] `model_decision_reason` text never uses words like "diagnoses", "confirms", "proves".
- [ ] Report conclusion section never claims "quantum advantage proven" — uses "observed" qualifier.

---

## 9. Common Failure Modes to Avoid

**From phase12.md §7 — Don't claim causality:**
> "We should NOT say: 'Feature A caused the disease.' Instead: 'Feature A contributed strongly to the model's prediction.'"
- **Fix:** All explanation text uses "contributed to", "influenced", "associated with" — never "caused" or "proves".

**From phase12.md §20–21 — Uncalibrated scores:**
> "A prediction score of 0.91 does not automatically mean 91% probability of disease unless the model has been appropriately calibrated."
- **Fix:** Always include in warnings: `"Score is uncalibrated — not a clinical probability."` Set `is_calibrated: false` in explanation JSON.

**From phase12.md §42 — Explainability ≠ clinical validity:**
> "It does not guarantee that an explanation is the true internal causal mechanism."
- **Fix:** Include in every explanation: `"This is a research system output, not a clinical diagnosis."` Don't let this warning get removed as "unnecessary."

**SHAP with SVM — KernelExplainer is slow:**
> `shap.KernelExplainer` with an SVM background requires many evaluations and can be very slow on full test sets.
- **Fix:** Use `shap.sample(X_train, 50)` as background data. Limit `X_test` to 30 samples for the explanation. For the demo, prioritize RandomForest (TreeExplainer) — it's fast.

**PennyLane circuit function for perturbation:**
> The quantum model's circuit is a PennyLane QNode. Calling it inside a Python loop with large batches is slow.
- **Fix:** Limit perturbation testing to 20 samples and 5 perturbations per feature for the demo. Clearly label in the explanation metadata that the perturbation analysis is approximate.

**From phase13.md §6 — Financial cost clarity:**
> "When running locally: Financial quantum cost ≈ 0. But computational cost ≠ 0."
- **Fix:** `financial_cost_local.estimate = 0` with `note: "Local execution. No cloud quantum cost."` Never invent a rupee/dollar figure for local runs.

**From phase15.md §27 — Freeze benchmark, don't cherry-pick:**
> "Do not keep changing the benchmark until you get a preferred result."
- **Fix:** Report the actual measured numbers from `ModelResult`. Do not round up VQC metrics or round down classical metrics to make the comparison look better.

**From phase15.md §36 — Honest research claims:**
> "Every claim should be: OBSERVED, SUPPORTED BY LITERATURE, or FUTURE WORK."
- **Fix:** The conclusion section must state results as "observed on the evaluated dataset" — not as universal truths.

---

## 10. Ready-to-Paste First Prompt

```
I am building the explainability and report generation layer for a Hybrid Quantum-Classical 
Disease Detection Platform called QuantWarriors. My scope is Phases 12–13 plus final report.

Tech stack: Python 3.10, shap 0.43, scikit-learn 1.3, PennyLane 0.33, FastAPI 0.104+.

Project root: d:/projects/SIH2026/mvp/
Reference datasets: Breast Cancer (569×30, diagnosis M/B), Heart Disease (303×13), 
                    Parkinson's (195×22), Diabetes (768×8)

I receive ModelResult objects from Piyush's model training layer. Key fields I use:
- model_type: "CLASSICAL" or "QUANTUM"
- model_name: "LogisticRegression", "SVM", "RandomForest", "VQC"
- predictions_test, scores_test: np.ndarray for explanation
- accuracy, recall, specificity, f1_score, roc_auc: float metrics
- training_time_seconds, memory_peak_mb: resource measurements
- qubits, circuit_depth, gate_count, total_circuit_executions: quantum fields
- _model: the fitted sklearn estimator (for SHAP)

I also receive FeaturePipelineResult from Jayed:
- X_train, X_test, y_test: np.ndarray
- X_train_reduced, X_test_reduced: PCA-reduced arrays for quantum
- feature_names: original column names
- reduced_feature_names: ["PC1", ..., "PC8"]

OUTPUT CONTRACT 1 — explanation.json shape:
{
  "explanation_id": "EXPL-000001",
  "experiment_id": "EXP-Q-000001",
  "sample_id": "TEST_SAMPLE_042",
  "prediction": {"value": 1, "score": 0.873, "actual_label": 1, "is_correct": true},
  "feature_importance": [
    {"feature_name": "mean_radius", "importance": 0.312, "effect": "positive"}
  ],
  "global_importance": [{"feature_name": "worst_radius", "importance": 0.187}],
  "quantum_circuit_explanation": {
    "qubits": 8, "circuit_depth": 12, "encoding_method": "angle_encoding",
    "feature_to_qubit_mapping": {"PC1": "qubit_0", ...}
  },
  "pipeline_trace": [
    {"phase": "Phase 1", "component": "Ingestion", "artifact": "DS-000001"},
    {"phase": "Phase 6", "component": "Feature Reduction", "dimensions": "30 -> 8"}
  ],
  "warnings": [
    "Explanation based on model behavior, not medical causality.",
    "Score is uncalibrated — not a clinical probability.",
    "Research system — not a clinical diagnosis."
  ],
  "explainability_method": "SHAP"
}

OUTPUT CONTRACT 2 — cost_report.json with:
- computational_cost: wall_clock_time_seconds, ram_peak_gb
- quantum_cost: qubits, circuit_depth, gate_count, total_circuit_executions
- comparison_classical_baseline: speed ratio, verdict
- scalability_assessment: FEASIBLE / FEASIBLE_HIGH_RESOURCE / NOT_RECOMMENDED
- financial_cost_local: {estimate: 0, note: "Local execution..."}

CRITICAL RULES:
1. Never claim causality — use "contributed to", not "caused"
2. Never interpret uncalibrated scores as probabilities
3. Never claim "quantum advantage proven" — use "observed on evaluated dataset"
4. SHAP KernelExplainer (for SVM) must use only 50 background samples max
5. Quantum perturbation analysis: max 20 test samples, 5 perturbations per feature
6. Report HTML must include the disclaimer: "RESEARCH / BENCHMARKING SYSTEM"
7. financial_cost_local.estimate must be 0 for all local simulator runs

Build in this order:
1. backend/explainability/classical.py — ClassicalExplainer with SHAP
2. backend/explainability/quantum.py — QuantumExplainer + build_pipeline_trace()
3. backend/explainability/__init__.py — ExplainabilityEngine orchestrator
4. backend/reports/generator.py — CostReportGenerator + ReportGenerator (HTML)
5. Add GET /explanation and POST/GET /report routes to experiments.py

For each file, provide test code using mock sklearn models and random numpy arrays.
Do not require actual VQC or real dataset to test — the test mocks should work standalone.
```
