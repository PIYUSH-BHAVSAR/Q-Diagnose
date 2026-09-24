# Developer Guide — Piyush
## Scope: ML Models (Classical + Quantum) + Orchestration (Executor/Manager, Benchmarking, Recommendation, FastAPI Core + Experiments API)

---

## 1. Scope Summary

You own the **scientific engine and execution layer** of the entire platform. This breaks into four concrete areas: (1) **Classical ML models** — Logistic Regression, SVM, and Random Forest wrappers that accept `X_train/X_test/y_train/y_test` arrays from Jayed's pipeline and return a standardized `ModelResult` object with full metrics; (2) **Quantum ML model** — a PennyLane-based Variational Quantum Classifier (VQC) with angle encoding, parameterized circuit, local simulator backend, and a `QuantumBackend` abstraction so the backend can be swapped without rewriting the model; (3) **Experiment orchestration** — the `ExperimentManager` (creates/tracks/stores experiment records in SQLite), `ExperimentExecutor` (the main coordinator that already exists in `executor.py` — you fill in the gaps), and `ExperimentPlanner` (rule-based planner that reads dataset profile and produces the experiment configuration); (4) **Benchmarking and recommendation** — `MetricsCalculator` (accuracy, precision, recall, specificity, F1, ROC-AUC, PR-AUC, confusion matrix), `ModelComparison` (side-by-side table), and `RecommendationEngine` (QUANTUM_ADVANTAGE / TRADEOFF / CLASSICAL_ADVANTAGE verdict). You also own the FastAPI routes for experiments: `POST /api/experiments`, `POST /api/experiments/{id}/run`, `GET /api/experiments/{id}/status`, `GET /api/experiments/{id}/results`, `GET /api/experiments/{id}/recommendation`. Your most important rule: **never fabricate or manipulate results to make quantum look better than it is.** The platform's credibility depends on honest measurement.

---

## 2. Exact Phase Numbers

From the **architecture document**:
- **Phase 7** (phase7.md): Classical Model Selection & Baseline Training — Model registry (§8), Multiple models (§9), Baseline first (§11), Cross-validation (§14–15), Evaluation metrics (§16–18), Confusion matrix (§18), Resource measurement (§23), Reproducibility (§24), Fair comparison Mode A and B (§29–30), Phase 7 output (§32).
- **Phase 8** (phase8.md): Quantum Model Selection & Configuration — Feasibility analyzer (§6), Quantum model registry (§7), VQC (§8), Angle encoding (§10–13), Qubit configuration (§14–15), Ansatz/circuit (§16–17), Backend abstraction (§21–25), Training strategy (§30), Resource estimation (§26–29), Quantum candidate generation (§31–32).
- **Phase 9** (phase9.md): Experiment Planning & Orchestration — Task analyzer (§8), Dataset regime classification (§9), Feature dimension rules (§10), Classical/quantum candidate filtering (§12–13), Experiment matrix (§14), Fair comparison groups (§15–17), Priority system (§18), Resource-aware planning (§20), Execution budget (§21), Experiment configuration (§23), Rule-based decision engine (§25–27), Experiment queue (§31).
- **Phase 10** (phase10.md): Model Training & Execution — Execution validator (§6), Environment preparation (§8), Dataset integrity check (§10), No data leakage (§12), Model builder (§13), Classical training engine (§16), Quantum training engine (§17–20), Batch processing (§21), Execution modes (§23), Inference (§25), Metrics calculation (§27), Resource monitoring (§28–29), Error handling (§30), Experiment status (§32–33), Artifact storage (§34).
- **Phase 11** (phase11.md): Benchmarking — Result validation (§7), Comparison types (§8), Performance comparison (§9), Medical metrics priority (§10), Confusion matrix comparison (§11), ROC curve (§13), Statistical significance (§15), Generalization (§19–20), Resource comparison (§21), Quantum advantage classification (§25–26), Decision summary (§34), Final decision categories (§41).

From the **MVP implementation plan**:
- **MVP Phase 9–11** (§22–29): Planner rules, planner output, show plan to user.
- **MVP Phase 10–11** (§27–29): Classical models — LR, SVM, RF.
- **MVP Phase 11** (§29–31): Quantum model — VQC, angle encoding, 8 qubits, 2 layers, 1024 shots.
- **MVP Phase 12** (§32–33): Experiment manager, states, IDs.
- **MVP Phase 13** (§34): Execution progress tracking.
- **MVP Phase 14–15** (§35–37): Metrics — accuracy, precision, recall, specificity, F1, ROC-AUC, confusion matrix.
- **MVP Phase 15** (§37): Unified result structure for all models.
- **MVP Phase 17–18** (§43–44): Resource monitoring — `time.perf_counter()`, `psutil`.
- **MVP Phase 20** (§46–48): Recommendation engine logic.
- **MVP Phase 27** (§64): Reproducibility — store seed, dataset_hash, config.
- **API Design** (§78): `POST /api/experiments`, `POST /api/experiments/{id}/run`, `GET /api/experiments/{id}/status`, `GET /api/experiments/{id}/results`, `GET /api/experiments/{id}/recommendation`.

---

## 3. Files / Folders You Must Create

All paths relative to `d:\projects\SIH2026\mvp\`:

```
backend/
├── models/
│   ├── __init__.py
│   ├── registry.py                  ← ModelRegistry: lists all available models
│   ├── classical/
│   │   ├── __init__.py
│   │   ├── logistic_regression.py   ← LogisticRegressionModel
│   │   ├── svm.py                   ← SVMModel
│   │   └── random_forest.py         ← RandomForestModel
│   └── quantum/
│       ├── __init__.py
│       ├── backend.py               ← QuantumBackend ABC + LocalSimulatorBackend
│       ├── encoding.py              ← AngleEncoder: features → quantum rotations
│       ├── circuit.py               ← VQCCircuit: build PennyLane circuit
│       └── vqc.py                   ← VQCModel: train/predict, wraps circuit + backend
│
├── benchmarking/
│   ├── __init__.py
│   ├── metrics.py                   ← MetricsCalculator: all 7 metrics + confusion matrix
│   ├── comparison.py                ← ModelComparison: side-by-side results table
│   └── recommendation.py           ← RecommendationEngine: verdict logic
│
├── planner/
│   ├── __init__.py
│   ├── rules.py                     ← PlannerRules: constants + rule functions
│   └── experiment_planner.py        ← ExperimentPlanner: produces ExperimentConfig
│
├── experiments/
│   ├── __init__.py
│   ├── manager.py                   ← ExperimentManager: CRUD + status updates
│   └── executor.py                  ← ExperimentExecutor (already scaffolded — fill gaps)
│
├── resources/
│   ├── __init__.py
│   └── monitor.py                   ← ResourceMonitor: CPU, RAM, time tracking
│
└── api/
    └── experiments.py               ← FastAPI routes for experiments
```

You do NOT create or modify:
- `backend/data/` → Jayed
- `backend/storage/` → Arzaan
- `backend/api/datasets.py` → Shweta
- `backend/explainability/` → Radha
- `backend/reports/` → Radha

---

## 4. Input Contract (what you consume)

You receive `FeaturePipelineResult` from **Jayed's** pipeline. The exact dataclass:

```python
@dataclass
class FeaturePipelineResult:
    X_train:          np.ndarray   # (455, 30) for Breast Cancer full features
    X_test:           np.ndarray   # (114, 30)
    y_train:          np.ndarray   # (455,)
    y_test:           np.ndarray   # (114,)
    X_train_reduced:  np.ndarray   # (455, 8)  — PCA-reduced for quantum
    X_test_reduced:   np.ndarray   # (114, 8)
    n_components:     int          # 8
    feature_names:    List[str]    # ["radius_mean", "texture_mean", ...]
    reduced_feature_names: List[str]  # ["PC1", "PC2", ..., "PC8"]
    variance_retained: float       # 0.94
    preprocessing_id: str          # "PREP-000001"
    split_strategy:   str          # "stratified"
    test_size:        float        # 0.20
    random_state:     int          # 42
    class_weights:    dict         # {0: 0.80, 1: 1.34}
```

You also read the dataset profile from **Jayed's** `DatasetProfile`:
```python
profile.task_candidate          # "BINARY_CLASSIFICATION"
profile.rows                    # 569
profile.numerical_count         # 30
profile.class_distribution      # {"0": 357, "1": 212}
profile.target_candidate        # "diagnosis"
```

And validation report from **Jayed's** `ValidationResult`:
```python
validation.class_balance["imbalance_ratio"]  # 1.68
validation.leakage["identifier_candidates"]   # ["id"]
```

---

## 5. Output Contracts

### 5a. `ModelResult` — produced by every model, consumed by benchmarking and Radha

This is the unified result object. Every classical and quantum model must return exactly this shape:

```python
@dataclass
class ModelResult:
    experiment_id:    str
    model_type:       str    # "CLASSICAL" or "QUANTUM"
    model_name:       str    # "LogisticRegression", "SVM", "RandomForest", "VQC"
    representation_id: str   # "REP-000001" or "QREP-000001"
    status:           str    # "COMPLETED", "FAILED", "TIMEOUT", "OUT_OF_MEMORY"
    
    # Predictions (for Phase 11/12 analysis)
    predictions_train: np.ndarray
    predictions_test:  np.ndarray
    scores_test:       np.ndarray   # probabilities / raw scores for ROC curve
    
    # Metrics
    accuracy:    float
    precision:   float
    recall:      float
    specificity: float
    f1_score:    float
    roc_auc:     float
    pr_auc:      float
    confusion_matrix: List[List[int]]  # [[TN, FP], [FN, TP]]
    
    # Resources
    training_time_seconds:  float
    inference_time_seconds: float
    memory_peak_mb:         float
    model_size_mb:          float
    
    # Quantum-specific (None for classical)
    qubits:                   Optional[int]
    circuit_depth:            Optional[int]
    gate_count:               Optional[int]
    two_qubit_gates:          Optional[int]
    shots:                    Optional[int]
    total_circuit_executions: Optional[int]
    backend_type:             Optional[str]
    encoding_method:          Optional[str]
    
    # Training history
    training_history: dict   # {"epochs": [...], "train_loss": [...], "val_loss": [...]}
    
    # Reproducibility
    hyperparameters: dict
    random_seed:     int
    execution_timestamp: str
    error_message:   Optional[str]
    
    def to_dict(self) -> dict: ...   # fully JSON-serializable, no numpy arrays
    def metrics_dict(self) -> dict: ...
```

### 5b. `contracts/model_result.json` — verbatim example

```json
{
  "experiment_id":   "EXP-Q-000001",
  "model_type":      "QUANTUM",
  "model_name":      "VQC",
  "representation_id": "QREP-000001",
  "status":          "COMPLETED",
  "metrics": {
    "accuracy":    0.941,
    "precision":   0.921,
    "recall":      0.935,
    "specificity": 0.945,
    "f1_score":    0.928,
    "roc_auc":     0.961,
    "pr_auc":      0.892
  },
  "confusion_matrix": [[52, 3], [4, 55]],
  "resource_usage": {
    "training_time_seconds":  842.1,
    "inference_time_seconds": 17.4,
    "memory_peak_mb":         1247.8
  },
  "quantum_metrics": {
    "qubits": 8, "circuit_depth": 12, "gate_count": 156,
    "two_qubit_gates": 42, "shots": 1024,
    "total_circuit_executions": 19932,
    "backend_type": "LOCAL_SIMULATOR",
    "encoding_method": "angle_encoding"
  }
}
```

### 5c. `contracts/recommendation.json` — verbatim example

```json
{
  "benchmark_id":   "BENCH-000001",
  "dataset_id":     "a1b2c3d4-...",
  "classical_best": {
    "model_name": "RandomForest",
    "metrics":    { "accuracy": 0.953, "recall": 0.903, "roc_auc": 0.973 },
    "training_time_seconds": 42.7
  },
  "quantum_best": {
    "model_name": "VQC", "qubits": 8,
    "metrics":    { "accuracy": 0.941, "recall": 0.935, "roc_auc": 0.961 },
    "training_time_seconds": 842.1,
    "total_circuit_executions": 19932
  },
  "performance_differences": {
    "accuracy_delta": -0.012,
    "recall_delta":    0.032,
    "auc_delta":      -0.012
  },
  "resource_comparison": {
    "training_time_ratio": 19.7,
    "inference_time_ratio": 1450.0
  },
  "classification": "TRADEOFF",
  "observations": [
    "VQC achieved +3.2pp higher recall than RandomForest (93.5% vs 90.3%)",
    "RandomForest achieved +1.2pp higher ROC-AUC (97.3% vs 96.1%)",
    "VQC required 19.7x more training time"
  ],
  "recommendation_text": "VQC shows higher sensitivity with a computational tradeoff..."
}
```

### 5d. `contracts/experiment_status.json` — consumed by frontend polling

```json
{
  "experiment_id": "EXP-000001",
  "status":        "RUNNING",
  "stage":         "quantum_training",
  "progress":      0.67,
  "started_at":    "2026-09-10T14:30:00Z",
  "elapsed_seconds": 412,
  "circuit_executions": 8320,
  "current_model": "VQC",
  "completed_models": ["logistic_regression", "svm", "random_forest"],
  "error_message": null
}
```

---

## 6. Step-by-Step Build Order

### Day 1

**Hour 1–2: Metrics Calculator (start here — everything depends on it)**

```python
# backend/benchmarking/metrics.py
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)

class MetricsCalculator:
    @staticmethod
    def compute(y_true: np.ndarray, y_pred: np.ndarray,
                y_scores: np.ndarray) -> dict:
        """
        Compute all metrics required by the platform.
        y_scores: continuous scores/probabilities for ROC/PR curves.
        """
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        return {
            "accuracy":    float(accuracy_score(y_true, y_pred)),
            "precision":   float(precision_score(y_true, y_pred, zero_division=0)),
            "recall":      float(recall_score(y_true, y_pred, zero_division=0)),
            "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
            "f1_score":    float(f1_score(y_true, y_pred, zero_division=0)),
            "roc_auc":     float(roc_auc_score(y_true, y_scores)),
            "pr_auc":      float(average_precision_score(y_true, y_scores)),
            "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        }
```

Test immediately:
```python
import numpy as np
from backend.benchmarking.metrics import MetricsCalculator

y_true   = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 0])
y_pred   = np.array([1, 0, 1, 0, 0, 1, 1, 0, 1, 0])
y_scores = np.array([0.9, 0.1, 0.8, 0.4, 0.2, 0.7, 0.6, 0.3, 0.85, 0.15])

m = MetricsCalculator.compute(y_true, y_pred, y_scores)
assert 0 < m["recall"] <= 1
assert 0 < m["specificity"] <= 1
assert m["confusion_matrix"] == [[3, 1], [1, 5]]
print("Metrics:", m)
```

**Hour 2–4: Classical Models**

All three models follow the exact same interface:

```python
# backend/models/classical/logistic_regression.py
import time, psutil, os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import label_binarize
from backend.benchmarking.metrics import MetricsCalculator

class LogisticRegressionModel:
    def __init__(self, random_state: int = 42, max_iter: int = 1000,
                 class_weight: str = "balanced"):
        self.model = LogisticRegression(
            random_state=random_state, max_iter=max_iter,
            class_weight=class_weight
        )
        self.random_state = random_state
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_test: np.ndarray,  y_test: np.ndarray,
            feature_names: list = None) -> "ModelResult":
        
        proc = psutil.Process(os.getpid())
        mem_before = proc.memory_info().rss / (1024 * 1024)
        
        t_start = time.perf_counter()
        self.model.fit(X_train, y_train)
        training_time = time.perf_counter() - t_start
        
        mem_after = proc.memory_info().rss / (1024 * 1024)
        
        # Inference timing
        t_infer = time.perf_counter()
        y_pred  = self.model.predict(X_test)
        inference_time = time.perf_counter() - t_infer
        
        y_scores = self.model.predict_proba(X_test)[:, 1]
        y_pred_train = self.model.predict(X_train)
        
        metrics = MetricsCalculator.compute(y_test, y_pred, y_scores)
        
        return ModelResult(
            model_type="CLASSICAL",
            model_name="LogisticRegression",
            representation_id="REP-000001",
            status="COMPLETED",
            predictions_train=y_pred_train,
            predictions_test=y_pred,
            scores_test=y_scores,
            training_time_seconds=training_time,
            inference_time_seconds=inference_time,
            memory_peak_mb=max(mem_after - mem_before, 0.0),
            hyperparameters={"max_iter": 1000, "class_weight": "balanced",
                             "random_state": self.random_state},
            random_seed=self.random_state,
            **metrics  # unpack all metric fields
        )
```

Repeat the same pattern for `SVMModel` (use `SVC(probability=True)`) and `RandomForestModel`. They share the identical interface — only the sklearn class and hyperparameters change.

Test against Breast Cancer:
```python
import pandas as pd, numpy as np
from backend.data.adapters import AdapterRegistry
from backend.features.pipeline import FeaturePipeline
from backend.models.classical.random_forest import RandomForestModel

df = pd.read_csv("data/demo/breast_cancer.csv")
registry = AdapterRegistry()
adapter = registry.detect_adapter(df)
X, y, meta = adapter.adapt(df)
processed = FeaturePipeline(n_components=8).fit_transform(X, y)

rf = RandomForestModel(random_state=42)
result = rf.fit(processed.X_train, processed.y_train,
                processed.X_test,  processed.y_test)

assert result.status == "COMPLETED"
assert 0.80 < result.accuracy < 1.0
assert 0.80 < result.roc_auc  < 1.0
assert result.recall > 0.70
print(f"RF: acc={result.accuracy:.3f} recall={result.recall:.3f} auc={result.roc_auc:.3f}")
```

**Hour 4–6: Quantum Backend + Encoding**

```python
# backend/models/quantum/backend.py
from abc import ABC, abstractmethod
import pennylane as qml

class QuantumBackend(ABC):
    @abstractmethod
    def get_device(self, n_qubits: int): ...
    
    @abstractmethod
    def get_resource_info(self) -> dict: ...

class LocalSimulatorBackend(QuantumBackend):
    def get_device(self, n_qubits: int):
        return qml.device("default.qubit", wires=n_qubits)
    
    def get_resource_info(self) -> dict:
        return {"type": "LOCAL_SIMULATOR", "provider": "PennyLane",
                "device": "default.qubit"}
```

```python
# backend/models/quantum/encoding.py
import pennylane as qml
import numpy as np

class AngleEncoder:
    """Encodes classical features as rotation angles on qubits."""
    
    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
    
    def encode(self, features: np.ndarray):
        """Apply RY rotations for each feature on corresponding qubit."""
        # features should be in range [-pi, pi] — handled by preprocessing
        for i, x in enumerate(features[:self.n_qubits]):
            qml.RY(x * np.pi, wires=i)
    
    def scale_features(self, X: np.ndarray) -> np.ndarray:
        """Scale features to [-1, 1] range for angle encoding.
        StandardScaler output (mean=0, std=1) clips to ~3 sigmas.
        Map to [-pi, pi] for RY rotation gates.
        """
        # Clip to ±3 std, then scale to [-1, 1]
        X_clipped = np.clip(X, -3, 3) / 3.0
        return X_clipped
```

```python
# backend/models/quantum/circuit.py
import pennylane as qml
import numpy as np
from backend.models.quantum.encoding import AngleEncoder

def build_vqc_circuit(n_qubits: int, n_layers: int, device):
    """Returns a QNode that takes (features, params) and outputs prediction score."""
    
    encoder = AngleEncoder(n_qubits)
    
    @qml.qnode(device)
    def circuit(features, params):
        # Layer 0: Angle encoding
        encoder.encode(features)
        
        # Variational layers
        for layer in range(n_layers):
            # Trainable rotations
            for qubit in range(n_qubits):
                qml.RY(params[layer * n_qubits * 2 + qubit], wires=qubit)
                qml.RZ(params[layer * n_qubits * 2 + n_qubits + qubit], wires=qubit)
            # Entanglement: linear CNOT chain
            for qubit in range(n_qubits - 1):
                qml.CNOT(wires=[qubit, qubit + 1])
        
        return qml.expval(qml.PauliZ(0))  # measurement on first qubit
    
    return circuit

def count_params(n_qubits: int, n_layers: int) -> int:
    return n_layers * n_qubits * 2  # RY + RZ per qubit per layer
```

**Hour 6–8: VQC Model**

```python
# backend/models/quantum/vqc.py
import time, psutil, os
import numpy as np
import pennylane as qml
from backend.models.quantum.backend import LocalSimulatorBackend
from backend.models.quantum.circuit import build_vqc_circuit, count_params
from backend.models.quantum.encoding import AngleEncoder
from backend.benchmarking.metrics import MetricsCalculator

class VQCModel:
    def __init__(self, n_qubits: int = 8, n_layers: int = 2, shots: int = 1024,
                 epochs: int = 100, batch_size: int = 32, learning_rate: float = 0.01,
                 random_state: int = 42):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.shots = shots
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.encoder = AngleEncoder(n_qubits)
        self.backend = LocalSimulatorBackend()
        self._circuit_executions = 0
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_test: np.ndarray,  y_test: np.ndarray) -> "ModelResult":
        
        np.random.seed(self.random_state)
        proc = psutil.Process(os.getpid())
        mem_before = proc.memory_info().rss / (1024 * 1024)
        
        # Scale features for angle encoding
        X_train_enc = self.encoder.scale_features(X_train)
        X_test_enc  = self.encoder.scale_features(X_test)
        
        # Build circuit on local simulator
        device  = self.backend.get_device(self.n_qubits)
        circuit = build_vqc_circuit(self.n_qubits, self.n_layers, device)
        
        # Initialize parameters
        n_params = count_params(self.n_qubits, self.n_layers)
        params = np.random.uniform(-np.pi, np.pi, n_params)
        
        # Convert binary labels to ±1 for PauliZ measurement
        y_train_pm = np.where(y_train == 1, 1.0, -1.0)
        
        # Training loop
        train_losses, val_losses = [], []
        t_start = time.perf_counter()
        
        opt = qml.AdamOptimizer(stepsize=self.learning_rate)
        
        for epoch in range(self.epochs):
            # Mini-batch
            indices = np.random.permutation(len(X_train_enc))
            batch_loss = 0.0
            
            for start in range(0, min(len(X_train_enc), self.batch_size * 10),
                               self.batch_size):
                batch_idx = indices[start:start + self.batch_size]
                X_batch = X_train_enc[batch_idx]
                y_batch = y_train_pm[batch_idx]
                
                def cost_fn(p):
                    predictions = np.array([circuit(x, p) for x in X_batch])
                    self._circuit_executions += len(X_batch)
                    return np.mean((predictions - y_batch) ** 2)
                
                params, loss = opt.step_and_cost(cost_fn, params)
                batch_loss += float(loss)
            
            avg_loss = batch_loss / max(1, len(X_train_enc) // self.batch_size)
            train_losses.append(avg_loss)
            
            # Validation loss every 5 epochs
            if epoch % 5 == 0:
                val_preds = np.array([circuit(x, params) for x in X_test_enc[:20]])
                self._circuit_executions += 20
                val_y = np.where(y_test[:20] == 1, 1.0, -1.0)
                val_loss = float(np.mean((val_preds - val_y) ** 2))
                val_losses.append(val_loss)
        
        training_time = time.perf_counter() - t_start
        
        # Store params for inference
        self._params = params
        self._circuit = circuit
        
        # Inference on test set
        t_infer = time.perf_counter()
        raw_scores = np.array([circuit(x, params) for x in X_test_enc])
        self._circuit_executions += len(X_test_enc)
        inference_time = time.perf_counter() - t_infer
        
        # Convert PauliZ expectation [-1,1] → probability [0,1]
        y_scores = (raw_scores + 1) / 2
        y_pred   = (y_scores >= 0.5).astype(int)
        y_pred_train = (
            (np.array([circuit(x, params) for x in X_train_enc]) + 1) / 2 >= 0.5
        ).astype(int)
        self._circuit_executions += len(X_train_enc)
        
        mem_after = proc.memory_info().rss / (1024 * 1024)
        
        metrics = MetricsCalculator.compute(y_test, y_pred, y_scores)
        
        return ModelResult(
            model_type="QUANTUM",
            model_name="VQC",
            representation_id="QREP-000001",
            status="COMPLETED",
            predictions_train=y_pred_train,
            predictions_test=y_pred,
            scores_test=y_scores,
            training_time_seconds=training_time,
            inference_time_seconds=inference_time,
            memory_peak_mb=max(mem_after - mem_before, 0.0),
            qubits=self.n_qubits,
            circuit_depth=self.n_layers * 2 + 1,
            gate_count=self.n_qubits * self.n_layers * 2 + (self.n_qubits - 1) * self.n_layers,
            two_qubit_gates=(self.n_qubits - 1) * self.n_layers,
            shots=self.shots,
            total_circuit_executions=self._circuit_executions,
            backend_type="LOCAL_SIMULATOR",
            encoding_method="angle_encoding",
            training_history={
                "epochs": list(range(self.epochs)),
                "train_loss": train_losses,
                "val_loss": val_losses,
            },
            hyperparameters={
                "n_qubits": self.n_qubits, "n_layers": self.n_layers,
                "shots": self.shots, "epochs": self.epochs,
                "learning_rate": self.learning_rate, "random_state": self.random_state
            },
            random_seed=self.random_state,
            **metrics
        )
```

### Day 2

**Hour 1–2: Benchmarking + Recommendation**

```python
# backend/benchmarking/comparison.py
class ModelComparison:
    def compare(self, results: dict) -> "ComparisonResult":
        """
        results: {"logistic_regression": ModelResult, "svm": ..., "vqc": ...}
        Returns ComparisonResult with best classical, best quantum, diffs.
        """
        classical = {k: v for k, v in results.items() if v.model_type == "CLASSICAL"}
        quantum   = {k: v for k, v in results.items() if v.model_type == "QUANTUM"}
        
        best_classical = max(classical.values(), key=lambda r: r.roc_auc) if classical else None
        best_quantum   = max(quantum.values(),   key=lambda r: r.roc_auc) if quantum   else None
        
        return ComparisonResult(
            classical_results=classical,
            quantum_results=quantum,
            best_classical=best_classical,
            best_quantum=best_quantum,
        )
```

```python
# backend/benchmarking/recommendation.py
class RecommendationEngine:
    def recommend(self, comparison: ComparisonResult) -> dict:
        """
        Produces the recommendation.json contract.
        Never fabricates or forces quantum advantage.
        """
        bc = comparison.best_classical
        bq = comparison.best_quantum
        
        if bc is None or bq is None:
            return {"classification": "INCONCLUSIVE", "reason": "Missing results"}
        
        recall_delta = bq.recall - bc.recall
        auc_delta    = bq.roc_auc - bc.roc_auc
        time_ratio   = bq.training_time_seconds / max(bc.training_time_seconds, 0.001)
        
        # Classification logic — based on measurable evidence only
        if recall_delta > 0.03 and auc_delta > 0.01:
            classification = "QUANTUM_ADVANTAGE"
        elif recall_delta > 0.02 and auc_delta >= -0.01:
            classification = "TRADEOFF"
        elif abs(recall_delta) <= 0.02 and abs(auc_delta) <= 0.02:
            classification = "PERFORMANCE_PARITY"
        else:
            classification = "CLASSICAL_ADVANTAGE"
        
        observations = []
        observations.append(
            f"VQC achieved {recall_delta:+.1%} recall vs {bc.model_name}"
        )
        observations.append(
            f"{bc.model_name} achieved {-auc_delta:+.3f} higher ROC-AUC"
            if auc_delta < 0 else
            f"VQC achieved {auc_delta:+.3f} higher ROC-AUC"
        )
        observations.append(
            f"VQC required {time_ratio:.1f}x more training time"
        )
        
        return {
            "benchmark_id": f"BENCH-{...}",
            "classical_best": _result_summary(bc),
            "quantum_best":   _result_summary(bq),
            "performance_differences": {
                "accuracy_delta": round(bq.accuracy - bc.accuracy, 4),
                "recall_delta":   round(recall_delta, 4),
                "auc_delta":      round(auc_delta, 4),
            },
            "resource_comparison": {
                "training_time_ratio":  round(time_ratio, 1),
                "inference_time_ratio": round(
                    bq.inference_time_seconds / max(bc.inference_time_seconds, 0.0001), 1),
                "memory_ratio": round(
                    bq.memory_peak_mb / max(bc.memory_peak_mb, 0.01), 1),
            },
            "classification": classification,
            "observations":   observations,
            "recommendation_text": _generate_text(classification, bc, bq),
        }
```

**Hour 2–3: Experiment Planner**

```python
# backend/planner/experiment_planner.py
from backend.data.profiler import DatasetProfile
from backend.data.validator import ValidationResult

class ExperimentPlanner:
    """Rule-based planner. No LLM. Deterministic and explainable."""
    
    def plan(self, profile: DatasetProfile, validation: ValidationResult,
             n_components: int, max_qubits: int = 8) -> dict:
        rules_applied = []
        
        # RULE-001: Only binary classification supported in MVP
        if profile.task_candidate != "BINARY_CLASSIFICATION":
            raise ValueError(f"Only BINARY_CLASSIFICATION supported. Got: {profile.task_candidate}")
        rules_applied.append("RULE-001: Binary classification detected")
        
        # RULE-002: Quantum feasibility check
        quantum_enabled = n_components <= max_qubits
        if quantum_enabled:
            rules_applied.append(f"RULE-002: {n_components} features ≤ {max_qubits} qubits, quantum enabled")
        else:
            rules_applied.append(f"RULE-002: {n_components} features > {max_qubits} qubits, quantum disabled")
        
        # RULE-003: Sample size regime
        if profile.rows < 500:
            rules_applied.append("RULE-003: Small dataset (<500 samples) — use stratified split, limit quantum shots")
        
        # RULE-004: Class imbalance handling
        imbalance = validation.class_balance.get("imbalance_ratio", 1.0)
        use_class_weight = imbalance > 1.5
        if use_class_weight:
            rules_applied.append(f"RULE-004: Imbalance {imbalance:.1f}:1 — apply class_weight='balanced'")
        
        return {
            "task": profile.task_candidate,
            "preprocessing": ["standard_scaling"],
            "reduction": {"method": "PCA", "components": n_components},
            "classical_models": ["logistic_regression", "svm", "random_forest"],
            "quantum_models": ["vqc"] if quantum_enabled else [],
            "quantum_enabled": quantum_enabled,
            "evaluation": {
                "split": "stratified",
                "test_size": 0.20,
                "random_state": 42,
            },
            "use_class_weight": use_class_weight,
            "decision_trace": {
                "rules_applied": rules_applied,
                "reason": "Rule-based deterministic planning"
            }
        }
```

**Hour 3–5: Experiment Manager + fill gaps in Executor**

```python
# backend/experiments/manager.py
from enum import Enum

class ExperimentStatus(str, Enum):
    CREATED        = "CREATED"
    VALIDATING     = "VALIDATING"
    PREPROCESSING  = "PREPROCESSING"
    RUNNING_CLASSICAL = "RUNNING_CLASSICAL"
    RUNNING_QUANTUM   = "RUNNING_QUANTUM"
    BENCHMARKING   = "BENCHMARKING"
    EXPLAINING     = "EXPLAINING"
    COMPLETED      = "COMPLETED"
    FAILED         = "FAILED"

class ExperimentManager:
    def create_experiment(self, dataset_id: str, configuration: dict) -> str:
        """Creates DB record, returns experiment_id."""
        ...
    
    def update_status(self, experiment_id: str, status: ExperimentStatus,
                      error: str = None): ...
    
    def get_experiment(self, experiment_id: str) -> dict: ...
    
    def store_results(self, experiment_id: str, results: dict): ...
    
    def get_status(self, experiment_id: str) -> dict:
        """Returns experiment_status.json contract shape."""
        ...
```

In `executor.py` (already scaffolded), fill in:
1. `_train_classical_models()` — call LR, SVM, RF with `processed.X_train` / `processed.X_test`
2. `_train_quantum_model()` — call VQC with `processed.X_train_reduced` / `processed.X_test_reduced`
3. Wire `ModelComparison` and `RecommendationEngine` into the `run()` flow after all models complete

**Hour 5–6: FastAPI Experiments routes**

```python
# backend/api/experiments.py
router = APIRouter(prefix="/api/experiments", tags=["experiments"])

@router.post("", status_code=201)
async def create_experiment(payload: CreateExperimentRequest, db=Depends(get_db)):
    """Create experiment record. Returns experiment_id."""
    ...

@router.post("/{experiment_id}/run")
async def run_experiment(experiment_id: str, background_tasks: BackgroundTasks,
                         db=Depends(get_db)):
    """Trigger experiment execution in background."""
    background_tasks.add_task(_execute_experiment, experiment_id)
    return {"experiment_id": experiment_id, "status": "started"}

@router.get("/{experiment_id}/status")
def get_status(experiment_id: str, db=Depends(get_db)):
    """Poll execution progress. Naeem calls this every 2 seconds."""
    ...

@router.get("/{experiment_id}/results")
def get_results(experiment_id: str, db=Depends(get_db)):
    """Return full model comparison results."""
    ...

@router.get("/{experiment_id}/recommendation")
def get_recommendation(experiment_id: str, db=Depends(get_db)):
    """Return the recommendation.json contract."""
    ...
```

**Hour 6–8: End-to-end test**

```python
# Test the complete experiment pipeline manually
import pandas as pd
from backend.data.adapters import AdapterRegistry
from backend.features.pipeline import FeaturePipeline
from backend.experiments.executor import ExperimentExecutor

executor = ExperimentExecutor()
result = executor.run(
    dataset_path="data/demo/breast_cancer.csv",
    n_components=8
)

assert result["status"] == "completed"
models = result["results"]["models"]

# All 4 models present
assert "logistic_regression" in models
assert "svm" in models
assert "random_forest" in models
assert "vqc" in models

# VQC quantum metrics present
vqc = models["vqc"]
assert vqc["quantum_metrics"]["qubits"] == 8
assert vqc["quantum_metrics"]["backend_type"] == "LOCAL_SIMULATOR"

# All metrics computed
for name, model in models.items():
    assert "recall"  in model["metrics"]
    assert "roc_auc" in model["metrics"]
    assert 0 < model["metrics"]["roc_auc"] < 1

# Recommendation present
comparison = result["results"]["comparison"]
assert comparison["classification"] in [
    "QUANTUM_ADVANTAGE", "TRADEOFF", "PERFORMANCE_PARITY", "CLASSICAL_ADVANTAGE"
]
print("Classification:", comparison["classification"])
print("VQC recall:", models["vqc"]["metrics"]["recall"])
print("RF recall:", models["random_forest"]["metrics"]["recall"])
```

**Important VQC performance note:** For the MVP demo, limit `epochs=30` and `batch_size=16` during development to keep training under 5 minutes. Increase to `epochs=100` for the final benchmark run. Use `n_components=4` first if 8 qubits is too slow on your machine — confirm the pipeline works before scaling up.

---

## 7. Mock Data to Build Against on Day 1

Use **Breast Cancer Wisconsin** as your primary test dataset. Build against the following mock `FeaturePipelineResult` on Day 1 before Jayed's pipeline is ready:

```python
# Mock data to build against (Day 1 only — replace with real pipeline output on Day 2)
import numpy as np

class MockFeaturePipelineResult:
    def __init__(self):
        np.random.seed(42)
        n_train, n_test, n_feat, n_comp = 455, 114, 30, 8
        
        self.X_train          = np.random.randn(n_train, n_feat)
        self.X_test           = np.random.randn(n_test,  n_feat)
        self.y_train          = np.random.randint(0, 2, n_train)
        self.y_test           = np.random.randint(0, 2, n_test)
        self.X_train_reduced  = np.random.randn(n_train, n_comp)
        self.X_test_reduced   = np.random.randn(n_test,  n_comp)
        self.n_components     = n_comp
        self.feature_names    = [f"feature_{i}" for i in range(n_feat)]
        self.reduced_feature_names = [f"PC{i+1}" for i in range(n_comp)]
        self.variance_retained = 0.94
        self.preprocessing_id  = "PREP-000001"
        self.split_strategy    = "stratified"
        self.test_size         = 0.20
        self.random_state      = 42
        self.class_weights     = {0: 0.80, 1: 1.34}
```

Use this to test LR, SVM, RF, and VQC independently before the pipeline integration.

**Expected benchmark results (real Breast Cancer data, 8 PCA components):**
- Random Forest: accuracy ~0.93–0.96, recall ~0.88–0.95, ROC-AUC ~0.97–0.99
- VQC (30 epochs, 8 qubits): accuracy ~0.85–0.94, recall ~0.88–0.95, ROC-AUC ~0.90–0.97
- VQC will be slower than classical — expect 2–15 minutes training time depending on machine

---

## 8. Definition of Done

**Metrics:**
- [ ] `MetricsCalculator.compute()` returns all 7 metrics: accuracy, precision, recall, specificity, f1, roc_auc, pr_auc, plus confusion_matrix as `[[TN,FP],[FN,TP]]`.
- [ ] `specificity = TN / (TN + FP)` — computed manually, not a sklearn built-in.

**Classical Models:**
- [ ] All 3 classical models share identical interface: `fit(X_train, y_train, X_test, y_test) -> ModelResult`.
- [ ] All 3 return `model_type="CLASSICAL"` and non-null values for all 7 metrics.
- [ ] `class_weight="balanced"` is applied for all 3 classical models.
- [ ] Training time and inference time are measured with `time.perf_counter()`.
- [ ] Memory peak measured with `psutil`.

**VQC:**
- [ ] VQC uses PennyLane `default.qubit` device (no Qiskit).
- [ ] Angle encoding: each feature scaled and encoded as `RY(x * pi, wires=i)`.
- [ ] Circuit has configurable `n_qubits`, `n_layers` from config.
- [ ] `QuantumBackend` abstraction exists — VQC does not hardcode `default.qubit`.
- [ ] `total_circuit_executions` is tracked and included in `ModelResult`.
- [ ] VQC returns `model_type="QUANTUM"` and all quantum_metrics fields populated.
- [ ] VQC trains on `X_train_reduced` (8 PCA components), NOT on `X_train` (30 features).
- [ ] VQC `predict_proba`-equivalent: PauliZ expectation mapped to `[0,1]` probability.

**Orchestration:**
- [ ] `ExperimentPlanner.plan()` returns a dict with `quantum_enabled=True` for Breast Cancer (30→8 features, 8 qubits).
- [ ] `ExperimentManager` creates an experiment record in SQLite and returns a UUID experiment_id.
- [ ] Experiment status transitions: `CREATED → PREPROCESSING → RUNNING_CLASSICAL → RUNNING_QUANTUM → BENCHMARKING → COMPLETED`.
- [ ] `ExperimentExecutor.run()` runs all 4 models and returns results without crashing.
- [ ] Results stored in `artifacts/experiments/{experiment_id}/` as JSON files.

**Benchmarking:**
- [ ] `ModelComparison.compare()` identifies best classical by `roc_auc` and best quantum by `roc_auc`.
- [ ] `RecommendationEngine.recommend()` returns one of: `QUANTUM_ADVANTAGE`, `TRADEOFF`, `PERFORMANCE_PARITY`, `CLASSICAL_ADVANTAGE`.
- [ ] Recommendation text is based on actual measured metrics — zero hardcoded conclusions.

**API:**
- [ ] `POST /api/experiments` returns `201` with `experiment_id`.
- [ ] `POST /api/experiments/{id}/run` triggers background execution, returns immediately.
- [ ] `GET /api/experiments/{id}/status` returns `experiment_status.json` contract shape.
- [ ] `GET /api/experiments/{id}/results` returns all model results in `model_result.json` shape.
- [ ] `GET /api/experiments/{id}/recommendation` returns `recommendation.json` contract shape.
- [ ] End-to-end: upload breast_cancer.csv → create experiment → run → poll status → get results → all assertions in test script pass.

---

## 9. Common Failure Modes to Avoid

**From phase10.md §12 — Data leakage in execution:**
> "The test set must remain untouched until final evaluation."
- **Fix:** Classical models train on `processed.X_train`, evaluate on `processed.X_test`. VQC trains on `processed.X_train_reduced`, evaluates on `processed.X_test_reduced`. Never call `.fit()` on test data.

**From phase11.md §26 — Never claim quantum supremacy:**
> "Never say 'Quantum accuracy > classical therefore quantum supremacy'."
- **Fix:** `RecommendationEngine` uses conservative thresholds. `QUANTUM_ADVANTAGE` requires > 3pp improvement on recall AND > 1pp improvement on AUC. Even then, label it `QUANTUM_ADVANTAGE` — not "supremacy". Always show the resource cost alongside the performance.

**From phase8.md §27 — Qubit count is exponential cost:**
> "State-vector simulator: 8 qubits → 256 amplitudes, 16 qubits → 65,536 amplitudes."
- **Fix:** Default to 8 qubits. Never silently increase qubit count. If `n_components > max_qubits`, set `quantum_enabled=False` in the planner. Do NOT resize the circuit to match a 16-feature PCA.

**From phase7.md §4 — Weak classical baseline is scientifically invalid:**
> "Do not compare weak classical vs carefully tuned quantum."
- **Fix:** All classical models use `class_weight="balanced"` and reasonable default hyperparameters. Use `RandomForestClassifier(n_estimators=100)` not `n_estimators=1`.

**From phase8.md §13 — No double-preprocessing:**
> "We already scaled the data in Phase 4. Phase 8 should not randomly apply another normalization."
- **Fix:** `AngleEncoder.scale_features()` only clips and rescales — it does NOT call `StandardScaler` again. Jayed's `StandardScaler` already ran. You just map `[-3, 3]` → `[-1, 1]` for the rotation gates.

**From implementaion_plan.md §80 — Never block on long-running work:**
> "The frontend should never wait for the entire experiment in one HTTP request."
- **Fix:** `POST /api/experiments/{id}/run` triggers a `BackgroundTask`. Return immediately with `{"status": "started"}`. Frontend polls `GET /api/experiments/{id}/status`.

**PennyLane gradient + numpy:**
> PennyLane's `AdamOptimizer.step_and_cost()` requires the cost function to return a scalar, not a numpy array.
- **Fix:** Return `np.mean(...)` not a vector from the cost function. Use `float()` to convert output to Python scalar when storing losses.

**From implementaion_plan.md §86 — No fabricated quantum advantage:**
> "We must explicitly avoid claiming: 'Quantum advantage has been proven.'"
- **Fix:** `recommendation_text` must include the word "observed" or "evaluated dataset" and never claim universal advantage. If classical wins, say so clearly.

---

## 10. Ready-to-Paste First Prompt

```
I am building the ML models, experiment orchestration, and benchmarking layer for a Hybrid 
Quantum-Classical Disease Detection Platform called QuantWarriors. My scope is Phases 7–11 
from the architecture.

Tech stack: Python 3.10, scikit-learn 1.3, PennyLane 0.33, numpy 1.26, FastAPI 0.104+,
psutil 5.9, SQLAlchemy 2.0.

Project root: d:/projects/SIH2026/mvp/
Config: quantum.max_qubits=8, quantum.layers=2, quantum.shots=1024, 
        quantum.candidate_dimensions=[4,8], experiment.random_state=42

Input I receive from the data pipeline (FeaturePipelineResult dataclass):
  X_train:          np.ndarray  (455, 30)  — full scaled features
  X_test:           np.ndarray  (114, 30)
  y_train:          np.ndarray  (455,)
  y_test:           np.ndarray  (114,)
  X_train_reduced:  np.ndarray  (455, 8)  — 8 PCA components for quantum
  X_test_reduced:   np.ndarray  (114, 8)
  class_weights:    dict        {0: 0.80, 1: 1.34}

Output contracts I must match:
1. ModelResult dataclass (unified for all models):
   - model_type: "CLASSICAL" or "QUANTUM"
   - metrics: accuracy, precision, recall, specificity, f1_score, roc_auc, pr_auc
   - confusion_matrix: [[TN, FP], [FN, TP]]
   - resource_usage: training_time_seconds, inference_time_seconds, memory_peak_mb
   - quantum_metrics (QUANTUM only): qubits, circuit_depth, gate_count, two_qubit_gates,
     shots, total_circuit_executions, backend_type="LOCAL_SIMULATOR", encoding_method

2. recommendation.json: classification = QUANTUM_ADVANTAGE|TRADEOFF|PERFORMANCE_PARITY|CLASSICAL_ADVANTAGE
   Based ONLY on measured metrics. Never fabricate or force quantum to win.

CRITICAL RULES:
1. Classical models train on X_train (full 30 features), predict on X_test
2. VQC trains on X_train_reduced (8 PCA components), predicts on X_test_reduced
3. QuantumBackend abstraction must exist — VQC never hardcodes default.qubit directly
4. Specificity = TN / (TN + FP) — must be computed manually, not from sklearn
5. Angle encoding: scale features to [-1, 1], apply RY(x * pi, wires=i)
6. Training uses PennyLane AdamOptimizer, NOT torch/tensorflow
7. total_circuit_executions must be tracked and included in ModelResult
8. Recommendation is based on thresholds applied to MEASURED deltas only
9. API runs experiments as BackgroundTasks — never blocks HTTP response

Build in this order:
1. backend/benchmarking/metrics.py — MetricsCalculator.compute()
2. backend/models/classical/logistic_regression.py — fit() → ModelResult
3. backend/models/classical/svm.py
4. backend/models/classical/random_forest.py
5. backend/models/quantum/backend.py — QuantumBackend ABC + LocalSimulatorBackend
6. backend/models/quantum/encoding.py — AngleEncoder
7. backend/models/quantum/circuit.py — build_vqc_circuit() returning QNode
8. backend/models/quantum/vqc.py — VQCModel.fit() → ModelResult
9. backend/benchmarking/comparison.py — ModelComparison.compare()
10. backend/benchmarking/recommendation.py — RecommendationEngine.recommend()
11. backend/planner/experiment_planner.py — ExperimentPlanner.plan()
12. backend/experiments/manager.py — ExperimentManager CRUD
13. backend/api/experiments.py — FastAPI routes

After each step, show a runnable test. For the VQC, start with epochs=10, n_qubits=4 for 
fast testing, then scale up. Show timing for each test so I know if it's too slow.
```
