# Developer Guide — Naeem
## Scope: Full Frontend (React + Vite) consuming all backend APIs

---

## 1. Scope Summary

You own the **entire user interface** — every screen a user sees, every interaction they take, and every API call that connects those interactions to the backend. The frontend is a React + Vite single-page application that communicates with a FastAPI backend running on `http://localhost:8000`. You are building six distinct views: (1) a **Dashboard** showing platform stats and quick-start actions; (2) a **Dataset Upload and Profile** page where a user drops in a CSV and sees what the platform found inside it; (3) an **Experiment Setup** page that shows the system-generated plan before the user kicks off a run; (4) an **Experiment Progress** page that shows live stage-by-stage execution progress via polling; (5) a **Results and Comparison** page showing a side-by-side classical vs. quantum benchmark table with charts; and (6) an **Explainability + Cost** view with feature importance, quantum circuit details, and resource usage. You do not write any Python. You do not touch the backend. Your job is to consume the JSON contracts that your teammates produce and build a clean, functional interface around them. On Day 1, all backends are mocked — you build against hardcoded JSON that matches the exact contract shapes so you can develop independently without waiting for anyone else.

---

## 2. Exact Phase Numbers

From the **architecture document**:
- **Phase 1, §31–33** (phase1.md): Frontend upload flow — uploading state, validation state, registration result, "Profile Dataset →" button.
- **Phase 14, §4–6** (phase14.md): Complete user flow — upload → profile → plan → run → compare → explain → report.
- **Phase 14, §35–41** (phase14.md): Final UI structure — Dashboard, Datasets, Experiments, Results, Reports tabs.
- **Phase 15, §10–17** (phase15.md): Demo mode, 5-minute demo script, narrative.

From the **MVP implementation plan**:
- **MVP Phase 13** (§34): Execution progress UI — stage indicators with ✓/●/○ states.
- **MVP Phase 24** (§52): Frontend pages — `/`, `/datasets`, `/datasets/:id`, `/experiments`, `/experiments/new`, `/experiments/:id`, `/reports`.
- **MVP Phase 53–60** (§53–60): Dashboard, dataset upload, dataset profile screen (cards), pipeline visualization.
- **MVP Phase 57** (§57): Experiment planning screen — "WHY THIS PIPELINE?" section.
- **MVP Phase 58** (§58): Experiment running screen — live stage progress.
- **MVP Phase 59–60** (§59–60): Results screen — best classical, best quantum, comparison table.
- **MVP Phase 61** (§61): Error handling — user-friendly messages, not Python tracebacks.
- **MVP Phase 79** (§79): Execution architecture — frontend polls `GET /experiments/{id}/status` for progress.
- **MVP Phase 80** (§80): Long-running jobs — `POST /run` returns immediately, frontend polls status.
- **MVP Phase 83–84** (§83–84): The "wow" moment — QUANTUM VALUE ASSESSMENT screen.
- **MVP Phase 84** (§84): Medical disclaimer — never call predictions "diagnosis."
- **MVP Phase 93** (§93): React UI consumes backend. Never put ML logic in React.

---

## 3. Files / Folders You Must Create

All paths relative to `d:\projects\SIH2026\mvp\frontend\`:

```
frontend/
├── package.json                      ← already exists (vite + react)
├── index.html
├── vite.config.js
└── src/
    ├── main.jsx                      ← React root + router setup
    ├── App.jsx                       ← Layout shell + nav sidebar
    ├── index.css                     ← global styles
    │
    ├── services/
    │   └── api.js                    ← ALL API calls live here
    │
    ├── hooks/
    │   ├── useDataset.js             ← fetch dataset + profile
    │   └── useExperiment.js          ← create, run, poll status, fetch results
    │
    ├── components/
    │   ├── StageProgress.jsx         ← ✓/●/○ stage indicator
    │   ├── MetricsTable.jsx          ← model comparison table
    │   ├── FeatureImportanceBar.jsx  ← horizontal importance bars
    │   ├── ClassDistributionChart.jsx← pie/bar chart of class split
    │   ├── MetricsBadge.jsx          ← single metric pill (recall: 93.5%)
    │   ├── FileDropzone.jsx          ← drag-and-drop CSV uploader
    │   └── Disclaimer.jsx            ← research system warning banner
    │
    └── pages/
        ├── Dashboard.jsx             ← home / stats / quick-start
        ├── Datasets.jsx              ← list of uploaded datasets
        ├── DatasetDetail.jsx         ← profile view for one dataset
        ├── ExperimentNew.jsx         ← plan preview + "Run" button
        ├── ExperimentDetail.jsx      ← progress + results + explain + cost
        └── Reports.jsx               ← list of generated reports
```

You do NOT create, modify, or even look at:
- Anything under `backend/` → backend teammates own that
- `config.yaml`, `requirements.txt`, `mvp.db` → backend

---

## 4. Input Contracts (what the backend returns to you)

You call these endpoints. Every response shape is guaranteed by your teammates' contracts. Build against these exact shapes — do not invent fields.

### Base URL
```
http://localhost:8000
```

### 4a. Upload dataset
```
POST /api/datasets/upload
Body: FormData { file: <File> }

Response 201:
{
  "dataset_id":          "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "display_id":          "DS-000001",
  "status":              "REGISTERED",
  "filename":            "breast_cancer.csv",
  "container_type":      "CSV",
  "upload_timestamp":    "2026-09-10T14:23:45.123Z",
  "file_size_bytes":     125847,
  "sha256":              "a1b2c3d4...",
  "storage_path":        "datasets/DS-000001/raw/original.csv",
  "is_duplicate":        false,
  "duplicate_of":        null,
  "validation_warnings": [],
  "rejection_reason":    null
}

Response 400: { "detail": "Unsupported format: txt" }
Response 413: { "detail": "File size 150MB exceeds limit of 100MB" }
```

### 4b. List datasets
```
GET /api/datasets

Response 200:
{
  "datasets": [
    {
      "dataset_id":       "a1b2c3d4-...",
      "display_id":       "DS-000001",
      "filename":         "breast_cancer.csv",
      "container_type":   "CSV",
      "file_size_bytes":  125847,
      "status":           "REGISTERED",
      "upload_timestamp": "2026-09-10T14:23:45.123Z",
      "has_profile":      true
    }
  ],
  "total": 1
}
```

### 4c. Get dataset profile
```
GET /api/datasets/{dataset_id}/profile

Response 200:
{
  "dataset_id":   "a1b2c3d4-...",
  "profile_id":   "PROFILE-000001",
  "modality":     "TABULAR",
  "dimensions":   { "rows": 569, "columns": 32 },
  "features":     { "numerical": 30, "categorical": 1 },
  "target":       { "candidate": "diagnosis", "confidence": "HIGH" },
  "task":         { "candidate": "BINARY_CLASSIFICATION", "confidence": "HIGH" },
  "class_distribution": { "0": 357, "1": 212 },
  "missing_values": { "total": 0, "percentage": 0.0, "by_column": {} },
  "duplicates":   { "candidate_count": 0 },
  "warnings":     ["Class imbalance detected: 62.7% vs 37.3%"],
  "status":       "PROFILED",
  "profiled_at":  "2026-09-10T14:25:12.456Z"
}

Response 202: { "status": "profiling_in_progress", "dataset_id": "..." }
Response 404: { "detail": "Dataset not found" }
```

### 4d. Create experiment
```
POST /api/experiments
Body: { "dataset_id": "a1b2c3d4-...", "n_components": 8 }

Response 201:
{ "experiment_id": "EXP-000001", "status": "CREATED", "dataset_id": "..." }
```

### 4e. Run experiment
```
POST /api/experiments/{experiment_id}/run

Response 200:
{ "experiment_id": "EXP-000001", "status": "started" }
```

### 4f. Poll experiment status
```
GET /api/experiments/{experiment_id}/status

Response 200:
{
  "experiment_id":      "EXP-000001",
  "status":             "RUNNING",
  "stage":              "quantum_training",
  "progress":           0.67,
  "started_at":         "2026-09-10T14:30:00Z",
  "elapsed_seconds":    412,
  "circuit_executions": 8320,
  "current_model":      "VQC",
  "completed_models":   ["logistic_regression", "svm", "random_forest"],
  "error_message":      null
}

status enum: CREATED | VALIDATING | PREPROCESSING | RUNNING_CLASSICAL |
             RUNNING_QUANTUM | BENCHMARKING | EXPLAINING | COMPLETED | FAILED
```

### 4g. Get results
```
GET /api/experiments/{experiment_id}/results

Response 200:
{
  "experiment_id": "EXP-000001",
  "status": "COMPLETED",
  "models": {
    "logistic_regression": {
      "model_type": "CLASSICAL", "model_name": "LogisticRegression",
      "status": "COMPLETED",
      "metrics": {
        "accuracy": 0.921, "precision": 0.901, "recall": 0.882,
        "specificity": 0.941, "f1_score": 0.891, "roc_auc": 0.937, "pr_auc": 0.881
      },
      "resource_usage": {
        "training_time_seconds": 2.3,
        "inference_time_seconds": 0.008,
        "memory_peak_mb": 124.5
      },
      "quantum_metrics": null
    },
    "svm": { ... },
    "random_forest": { ... },
    "vqc": {
      "model_type": "QUANTUM", "model_name": "VQC",
      "status": "COMPLETED",
      "metrics": {
        "accuracy": 0.941, "precision": 0.921, "recall": 0.935,
        "specificity": 0.945, "f1_score": 0.928, "roc_auc": 0.961, "pr_auc": 0.892
      },
      "resource_usage": {
        "training_time_seconds": 842.1,
        "inference_time_seconds": 17.4,
        "memory_peak_mb": 1247.8
      },
      "quantum_metrics": {
        "qubits": 8, "circuit_depth": 12, "gate_count": 156,
        "two_qubit_gates": 42, "shots": 1024,
        "total_circuit_executions": 19932,
        "backend_type": "LOCAL_SIMULATOR",
        "encoding_method": "angle_encoding"
      }
    }
  },
  "comparison": {
    "classification": "TRADEOFF",
    "classical_best": {
      "model_name": "RandomForest",
      "metrics": { "accuracy": 0.953, "recall": 0.903, "roc_auc": 0.973 },
      "training_time_seconds": 42.7
    },
    "quantum_best": {
      "model_name": "VQC", "qubits": 8,
      "metrics": { "accuracy": 0.941, "recall": 0.935, "roc_auc": 0.961 },
      "training_time_seconds": 842.1,
      "total_circuit_executions": 19932
    },
    "performance_differences": {
      "accuracy_delta": -0.012, "recall_delta": 0.032, "auc_delta": -0.012
    },
    "resource_comparison": {
      "training_time_ratio": 19.7,
      "inference_time_ratio": 1450.0
    },
    "observations": [
      "VQC achieved +3.2pp higher recall than RandomForest (93.5% vs 90.3%)",
      "RandomForest achieved +1.2pp higher ROC-AUC (97.3% vs 96.1%)",
      "VQC required 19.7x more training time"
    ],
    "recommendation_text": "VQC shows higher sensitivity with a computational tradeoff..."
  }
}
```

### 4h. Get explanation
```
GET /api/experiments/{experiment_id}/explanation?model_name=VQC

Response 200:
{
  "explanation_id":  "EXPL-000001",
  "experiment_id":   "EXP-Q-000001",
  "sample_id":       "TEST_SAMPLE_042",
  "prediction": { "value": 1, "score": 0.873, "actual_label": 1, "is_correct": true },
  "feature_importance": [
    { "feature_name": "mean_radius",           "importance": 0.312, "effect": "positive" },
    { "feature_name": "worst_concave_points",  "importance": 0.241, "effect": "positive" },
    { "feature_name": "mean_texture",          "importance": 0.087, "effect": "negative" }
  ],
  "global_importance": [
    { "feature_name": "worst_radius",          "importance": 0.187 },
    { "feature_name": "worst_concave_points",  "importance": 0.156 }
  ],
  "quantum_circuit_explanation": {
    "qubits": 8, "circuit_depth": 12,
    "encoding_method": "angle_encoding",
    "feature_to_qubit_mapping": { "PC1": "qubit_0", "PC2": "qubit_1" }
  },
  "pipeline_trace": [
    { "phase": "Phase 1", "component": "Ingestion",          "artifact": "DS-000001" },
    { "phase": "Phase 4", "component": "Preprocessing",      "artifact": "PREP-000001" },
    { "phase": "Phase 6", "component": "Feature Reduction",  "dimensions": "30 -> 8" },
    { "phase": "Phase 8", "component": "Quantum Model",      "artifact": "VQC" },
    { "phase": "Phase 10","component": "Execution",          "artifact": "EXP-Q-000001" }
  ],
  "warnings": [
    "Explanation based on model behavior, not medical causality.",
    "Score is uncalibrated — not a clinical probability.",
    "Research system — not a clinical diagnosis."
  ],
  "explainability_method": "feature_perturbation"
}
```

### 4i. Generate / get report
```
POST /api/experiments/{experiment_id}/report
→ { "report_path": "artifacts/reports/EXP-000001_report.html" }

GET /api/experiments/{experiment_id}/report
→ HTML file (Content-Type: text/html)
```

### 4j. Health check
```
GET /api/health
→ { "status": "healthy" }
```

---

## 5. Output (what you produce)

Your output is a running React app at `http://localhost:5173` with six working pages. No JSON contracts to produce — your output IS the user interface.

---

## 6. Step-by-Step Build Order

### Day 1 — Build everything against hardcoded mocks

**Key principle for Day 1:** Every API call in `services/api.js` has a `MOCK_MODE` flag. When `MOCK_MODE = true`, the service returns the hardcoded data below instead of hitting the server. This means you build all 6 pages completely on Day 1 without needing anyone else's backend to be ready.

**Hour 1: Project setup + API service layer**

If `frontend/` isn't initialized yet:
```bash
cd d:/projects/SIH2026/mvp/frontend
npm create vite@latest . -- --template react
npm install
npm install react-router-dom axios
```

Create `src/services/api.js` — this is the only file that knows the backend URL:

```javascript
// src/services/api.js
const BASE_URL = 'http://localhost:8000';
const MOCK_MODE = true; // flip to false when backend is ready

// ─── Mock data ──────────────────────────────────────────────────────────────

const MOCK_UPLOAD = {
  dataset_id: 'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7',
  display_id: 'DS-000001', status: 'REGISTERED',
  filename: 'breast_cancer.csv', container_type: 'CSV',
  upload_timestamp: '2026-09-10T14:23:45.123Z',
  file_size_bytes: 125847, sha256: 'a1b2c3d4...abc',
  storage_path: 'datasets/DS-000001/raw/original.csv',
  is_duplicate: false, duplicate_of: null,
  validation_warnings: [], rejection_reason: null
};

const MOCK_PROFILE = {
  dataset_id: 'a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7',
  profile_id: 'PROFILE-000001', modality: 'TABULAR',
  dimensions: { rows: 569, columns: 32 },
  features: { numerical: 30, categorical: 1 },
  target: { candidate: 'diagnosis', confidence: 'HIGH' },
  task: { candidate: 'BINARY_CLASSIFICATION', confidence: 'HIGH' },
  class_distribution: { '0': 357, '1': 212 },
  missing_values: { total: 0, percentage: 0.0, by_column: {} },
  duplicates: { candidate_count: 0 },
  warnings: ['Class imbalance detected: 62.7% vs 37.3%'],
  status: 'PROFILED', profiled_at: '2026-09-10T14:25:12.456Z'
};

const MOCK_STATUS_SEQUENCE = [
  { status: 'RUNNING', stage: 'preprocessing',       progress: 0.20, completed_models: [], current_model: null, elapsed_seconds: 8,   circuit_executions: 0 },
  { status: 'RUNNING', stage: 'classical_training',  progress: 0.35, completed_models: ['logistic_regression'], current_model: 'svm', elapsed_seconds: 15,  circuit_executions: 0 },
  { status: 'RUNNING', stage: 'classical_training',  progress: 0.50, completed_models: ['logistic_regression','svm'], current_model: 'random_forest', elapsed_seconds: 28, circuit_executions: 0 },
  { status: 'RUNNING', stage: 'quantum_training',    progress: 0.67, completed_models: ['logistic_regression','svm','random_forest'], current_model: 'VQC', elapsed_seconds: 412, circuit_executions: 8320 },
  { status: 'RUNNING', stage: 'benchmarking',        progress: 0.85, completed_models: ['logistic_regression','svm','random_forest','vqc'], current_model: null, elapsed_seconds: 860, circuit_executions: 19932 },
  { status: 'COMPLETED', stage: 'completed',         progress: 1.0,  completed_models: ['logistic_regression','svm','random_forest','vqc'], current_model: null, elapsed_seconds: 875, circuit_executions: 19932 },
];
let _mockStatusIdx = 0;

const MOCK_RESULTS = {
  experiment_id: 'EXP-000001', status: 'COMPLETED',
  models: {
    logistic_regression: { model_type:'CLASSICAL', model_name:'LogisticRegression', status:'COMPLETED', metrics:{ accuracy:0.921, precision:0.901, recall:0.882, specificity:0.941, f1_score:0.891, roc_auc:0.937, pr_auc:0.881 }, resource_usage:{ training_time_seconds:2.3, inference_time_seconds:0.008, memory_peak_mb:124.5 }, quantum_metrics:null },
    svm: { model_type:'CLASSICAL', model_name:'SVM', status:'COMPLETED', metrics:{ accuracy:0.930, precision:0.912, recall:0.894, specificity:0.952, f1_score:0.903, roc_auc:0.948, pr_auc:0.891 }, resource_usage:{ training_time_seconds:8.4, inference_time_seconds:0.015, memory_peak_mb:215.3 }, quantum_metrics:null },
    random_forest: { model_type:'CLASSICAL', model_name:'RandomForest', status:'COMPLETED', metrics:{ accuracy:0.953, precision:0.941, recall:0.903, specificity:0.982, f1_score:0.921, roc_auc:0.973, pr_auc:0.941 }, resource_usage:{ training_time_seconds:42.7, inference_time_seconds:0.012, memory_peak_mb:382.5 }, quantum_metrics:null },
    vqc: { model_type:'QUANTUM', model_name:'VQC', status:'COMPLETED', metrics:{ accuracy:0.941, precision:0.921, recall:0.935, specificity:0.945, f1_score:0.928, roc_auc:0.961, pr_auc:0.892 }, resource_usage:{ training_time_seconds:842.1, inference_time_seconds:17.4, memory_peak_mb:1247.8 }, quantum_metrics:{ qubits:8, circuit_depth:12, gate_count:156, two_qubit_gates:42, shots:1024, total_circuit_executions:19932, backend_type:'LOCAL_SIMULATOR', encoding_method:'angle_encoding' } },
  },
  comparison: {
    classification: 'TRADEOFF',
    classical_best: { model_name:'RandomForest', metrics:{ accuracy:0.953, recall:0.903, roc_auc:0.973 }, training_time_seconds:42.7 },
    quantum_best:   { model_name:'VQC', qubits:8, metrics:{ accuracy:0.941, recall:0.935, roc_auc:0.961 }, training_time_seconds:842.1, total_circuit_executions:19932 },
    performance_differences: { accuracy_delta:-0.012, recall_delta:0.032, auc_delta:-0.012 },
    resource_comparison: { training_time_ratio:19.7, inference_time_ratio:1450.0 },
    observations: [
      'VQC achieved +3.2pp higher recall than RandomForest (93.5% vs 90.3%)',
      'RandomForest achieved +1.2pp higher ROC-AUC (97.3% vs 96.1%)',
      'VQC required 19.7x more training time',
    ],
    recommendation_text: 'VQC shows higher sensitivity (+3.2pp recall) with a significant computational cost (19.7x training time). Consider VQC when recall is the primary objective and resources are available. RandomForest achieves better overall discrimination (AUC) with far lower compute cost.',
  }
};

const MOCK_EXPLANATION = {
  explanation_id:'EXPL-000001', experiment_id:'EXP-000001', sample_id:'TEST_SAMPLE_042',
  prediction:{ value:1, score:0.873, actual_label:1, is_correct:true },
  feature_importance:[
    { feature_name:'mean_radius',          importance:0.312, effect:'positive' },
    { feature_name:'worst_concave_points', importance:0.241, effect:'positive' },
    { feature_name:'worst_area',           importance:0.198, effect:'positive' },
    { feature_name:'mean_perimeter',       importance:0.163, effect:'positive' },
    { feature_name:'mean_texture',         importance:0.087, effect:'negative' },
    { feature_name:'smoothness_worst',     importance:0.071, effect:'negative' },
  ],
  global_importance:[
    { feature_name:'worst_radius',          importance:0.187 },
    { feature_name:'worst_concave_points',  importance:0.156 },
    { feature_name:'mean_concave_points',   importance:0.134 },
    { feature_name:'worst_perimeter',       importance:0.121 },
    { feature_name:'mean_radius',           importance:0.098 },
  ],
  quantum_circuit_explanation:{ qubits:8, circuit_depth:12, encoding_method:'angle_encoding', feature_to_qubit_mapping:{ PC1:'qubit_0', PC2:'qubit_1', PC3:'qubit_2', PC4:'qubit_3', PC5:'qubit_4', PC6:'qubit_5', PC7:'qubit_6', PC8:'qubit_7' } },
  pipeline_trace:[
    { phase:'Phase 1', component:'Ingestion',         artifact:'DS-000001' },
    { phase:'Phase 4', component:'Preprocessing',     artifact:'PREP-000001', note:'StandardScaler fitted on training data only' },
    { phase:'Phase 6', component:'Feature Reduction', artifact:'QREP-000001', dimensions:'30 → 8', method:'PCA', variance_retained:'94%' },
    { phase:'Phase 8', component:'Quantum Model',     artifact:'VQC', qubits:8 },
    { phase:'Phase 10',component:'Execution',         artifact:'EXP-000001', backend:'LOCAL_SIMULATOR' },
  ],
  warnings:[
    'Explanation based on model behavior, not medical causality.',
    'Score is uncalibrated — not a clinical probability.',
    'Research system — not a clinical diagnosis.',
  ],
  explainability_method:'feature_perturbation',
};

// ─── API functions ──────────────────────────────────────────────────────────

export async function uploadDataset(file) {
  if (MOCK_MODE) {
    await delay(800);
    return MOCK_UPLOAD;
  }
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${BASE_URL}/api/datasets/upload`, { method:'POST', body:fd });
  if (!r.ok) throw await r.json();
  return r.json();
}

export async function listDatasets() {
  if (MOCK_MODE) {
    await delay(300);
    return { datasets:[{ ...MOCK_UPLOAD, has_profile:true }], total:1 };
  }
  const r = await fetch(`${BASE_URL}/api/datasets`);
  return r.json();
}

export async function getDatasetProfile(datasetId) {
  if (MOCK_MODE) {
    await delay(400);
    // Simulate 202 → 200 transition: return profile directly
    return MOCK_PROFILE;
  }
  const r = await fetch(`${BASE_URL}/api/datasets/${datasetId}/profile`);
  if (r.status === 202) return { status:'profiling_in_progress' };
  if (!r.ok) throw await r.json();
  return r.json();
}

export async function createExperiment(datasetId, nComponents=8) {
  if (MOCK_MODE) {
    await delay(300);
    _mockStatusIdx = 0; // reset progress simulation
    return { experiment_id:'EXP-000001', status:'CREATED', dataset_id:datasetId };
  }
  const r = await fetch(`${BASE_URL}/api/experiments`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ dataset_id:datasetId, n_components:nComponents })
  });
  return r.json();
}

export async function runExperiment(experimentId) {
  if (MOCK_MODE) {
    await delay(200);
    return { experiment_id:experimentId, status:'started' };
  }
  const r = await fetch(`${BASE_URL}/api/experiments/${experimentId}/run`, { method:'POST' });
  return r.json();
}

export async function getExperimentStatus(experimentId) {
  if (MOCK_MODE) {
    await delay(600);
    const s = MOCK_STATUS_SEQUENCE[Math.min(_mockStatusIdx, MOCK_STATUS_SEQUENCE.length-1)];
    if (_mockStatusIdx < MOCK_STATUS_SEQUENCE.length-1) _mockStatusIdx++;
    return { experiment_id:experimentId, ...s };
  }
  const r = await fetch(`${BASE_URL}/api/experiments/${experimentId}/status`);
  return r.json();
}

export async function getExperimentResults(experimentId) {
  if (MOCK_MODE) {
    await delay(400);
    return MOCK_RESULTS;
  }
  const r = await fetch(`${BASE_URL}/api/experiments/${experimentId}/results`);
  return r.json();
}

export async function getExplanation(experimentId, modelName='VQC') {
  if (MOCK_MODE) {
    await delay(500);
    return MOCK_EXPLANATION;
  }
  const r = await fetch(`${BASE_URL}/api/experiments/${experimentId}/explanation?model_name=${modelName}`);
  return r.json();
}

export async function generateReport(experimentId) {
  if (MOCK_MODE) {
    await delay(600);
    return { report_path:`artifacts/reports/${experimentId}_report.html` };
  }
  const r = await fetch(`${BASE_URL}/api/experiments/${experimentId}/report`, { method:'POST' });
  return r.json();
}

export async function checkHealth() {
  if (MOCK_MODE) return { status:'healthy' };
  const r = await fetch(`${BASE_URL}/api/health`);
  return r.json();
}

function delay(ms) { return new Promise(res => setTimeout(res, ms)); }
```

**Hour 2: Router + Layout shell**

```jsx
// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

```jsx
// src/App.jsx
import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Datasets from './pages/Datasets';
import DatasetDetail from './pages/DatasetDetail';
import ExperimentNew from './pages/ExperimentNew';
import ExperimentDetail from './pages/ExperimentDetail';
import Reports from './pages/Reports';

export default function App() {
  return (
    <div style={{ display:'flex', minHeight:'100vh', fontFamily:'system-ui,sans-serif' }}>
      {/* Sidebar */}
      <nav style={{ width:200, background:'#1a1a2e', padding:'20px 0', color:'white' }}>
        <div style={{ padding:'0 20px 20px', fontSize:18, fontWeight:'bold', color:'#e94560' }}>
          ⚛ QuantWarriors
        </div>
        {[
          { to:'/',           label:'Dashboard'   },
          { to:'/datasets',   label:'Datasets'    },
          { to:'/experiments',label:'Experiments' },
          { to:'/reports',    label:'Reports'     },
        ].map(({to, label}) => (
          <NavLink key={to} to={to} end={to=='/'}
            style={({isActive}) => ({
              display:'block', padding:'10px 20px', color: isActive ? '#e94560' : '#aaa',
              textDecoration:'none', background: isActive ? 'rgba(233,69,96,0.1)' : 'transparent'
            })}>
            {label}
          </NavLink>
        ))}
        <div style={{ position:'absolute', bottom:20, left:20, fontSize:11, color:'#555' }}>
          v1.0 MVP · SIH 2026
        </div>
      </nav>

      {/* Main content */}
      <main style={{ flex:1, padding:32, background:'#f5f7fa', overflow:'auto' }}>
        <Routes>
          <Route path="/"                         element={<Dashboard />} />
          <Route path="/datasets"                 element={<Datasets />} />
          <Route path="/datasets/:datasetId"      element={<DatasetDetail />} />
          <Route path="/experiments/new/:datasetId" element={<ExperimentNew />} />
          <Route path="/experiments/:expId"       element={<ExperimentDetail />} />
          <Route path="/reports"                  element={<Reports />} />
        </Routes>
      </main>
    </div>
  );
}
```

**Hour 2–3: Reusable components**

```jsx
// src/components/StageProgress.jsx
// Visual pipeline progress: ✓ completed · ● running · ○ pending
const STAGES = [
  { key:'preprocessing',    label:'Preprocessing'   },
  { key:'classical_training',label:'Classical Models'},
  { key:'quantum_training', label:'Quantum VQC'      },
  { key:'benchmarking',     label:'Benchmarking'     },
  { key:'completed',        label:'Complete'         },
];

export default function StageProgress({ status, stage, completedModels=[], circuitExecutions=0 }) {
  const currentIdx = STAGES.findIndex(s => s.key === stage);

  return (
    <div style={{ margin:'20px 0' }}>
      {STAGES.map((s, i) => {
        const done    = i < currentIdx || status === 'COMPLETED';
        const running = i === currentIdx && status === 'RUNNING';
        const icon    = done ? '✓' : running ? '●' : '○';
        const color   = done ? '#2e7d32' : running ? '#1565c0' : '#999';
        return (
          <div key={s.key} style={{ display:'flex', alignItems:'center', margin:'8px 0' }}>
            <span style={{ fontSize:18, color, marginRight:10, width:24 }}>{icon}</span>
            <span style={{ color, fontWeight: running ? 'bold' : 'normal' }}>{s.label}</span>
            {running && s.key === 'quantum_training' && circuitExecutions > 0 && (
              <span style={{ marginLeft:16, fontSize:12, color:'#888' }}>
                {circuitExecutions.toLocaleString()} circuit executions
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

```jsx
// src/components/MetricsTable.jsx
const METRIC_LABELS = {
  accuracy:'Accuracy', recall:'Recall (Sensitivity)', specificity:'Specificity',
  f1_score:'F1 Score', roc_auc:'ROC-AUC', pr_auc:'PR-AUC',
  training_time_seconds:'Train Time (s)', memory_peak_mb:'Peak RAM (MB)'
};

export default function MetricsTable({ models }) {
  const names = Object.keys(models || {});
  if (!names.length) return <p>No results yet.</p>;

  const metricKeys = ['accuracy','recall','specificity','f1_score','roc_auc','pr_auc'];
  const bestRecall = Math.max(...names.map(n => models[n].metrics?.recall ?? 0));
  const bestAUC    = Math.max(...names.map(n => models[n].metrics?.roc_auc ?? 0));

  return (
    <div style={{ overflowX:'auto' }}>
      <table style={{ borderCollapse:'collapse', width:'100%', fontSize:14 }}>
        <thead>
          <tr style={{ background:'#1a1a2e', color:'white' }}>
            <th style={th}>Model</th>
            <th style={th}>Type</th>
            {metricKeys.map(k => <th key={k} style={th}>{METRIC_LABELS[k]}</th>)}
            <th style={th}>Train Time</th>
          </tr>
        </thead>
        <tbody>
          {names.map(name => {
            const r = models[name];
            const m = r.metrics || {};
            const isQuantum = r.model_type === 'QUANTUM';
            return (
              <tr key={name} style={{ background: isQuantum ? '#e3f2fd' : 'white' }}>
                <td style={td}>{r.model_name}</td>
                <td style={td}>
                  <span style={{
                    padding:'2px 8px', borderRadius:12, fontSize:11, fontWeight:'bold',
                    background: isQuantum ? '#1565c0' : '#37474f', color:'white'
                  }}>
                    {r.model_type}
                  </span>
                </td>
                {metricKeys.map(k => {
                  const val = m[k];
                  const isTopRecall = k==='recall' && Math.abs(val-bestRecall)<0.001;
                  const isTopAUC    = k==='roc_auc' && Math.abs(val-bestAUC)<0.001;
                  return (
                    <td key={k} style={{
                      ...td,
                      fontWeight: isTopRecall||isTopAUC ? 'bold' : 'normal',
                      color: isTopRecall||isTopAUC ? '#2e7d32' : 'inherit'
                    }}>
                      {val !== undefined ? (val * 100).toFixed(1) + '%' : '—'}
                    </td>
                  );
                })}
                <td style={td}>{r.resource_usage?.training_time_seconds?.toFixed(1)}s</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p style={{ fontSize:12, color:'#888', marginTop:8 }}>
        Bold green = best value for that metric.
        Quantum models highlighted in blue.
      </p>
    </div>
  );
}

const th = { padding:'10px 14px', textAlign:'left', whiteSpace:'nowrap' };
const td = { padding:'8px 14px', borderBottom:'1px solid #eee' };
```

```jsx
// src/components/FeatureImportanceBar.jsx
export default function FeatureImportanceBar({ features, title='Feature Importance' }) {
  if (!features?.length) return null;
  const maxImp = Math.max(...features.map(f => f.importance));

  return (
    <div>
      <h4 style={{ marginBottom:12 }}>{title}</h4>
      {features.slice(0, 10).map((f, i) => (
        <div key={i} style={{ marginBottom:8 }}>
          <div style={{ display:'flex', justifyContent:'space-between', fontSize:13 }}>
            <span>{f.feature_name}</span>
            <span style={{ color: f.effect==='positive' ? '#2e7d32' : '#c62828' }}>
              {f.effect === 'positive' ? '+' : '−'} {(f.importance * 100).toFixed(1)}%
            </span>
          </div>
          <div style={{ background:'#eee', height:8, borderRadius:4, marginTop:3 }}>
            <div style={{
              width: `${(f.importance / maxImp) * 100}%`,
              height:8, borderRadius:4,
              background: f.effect==='positive' ? '#2e7d32' : '#c62828'
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}
```

```jsx
// src/components/Disclaimer.jsx
export default function Disclaimer() {
  return (
    <div style={{
      background:'#fff3e0', border:'2px solid #e65100', borderRadius:8,
      padding:'12px 20px', margin:'16px 0', fontSize:13
    }}>
      <strong>⚠ RESEARCH / BENCHMARKING SYSTEM</strong>
      <br />
      Predictions are for research purposes only. They are <strong>NOT</strong> clinical
      diagnoses and must not be used for medical decisions.
    </div>
  );
}
```

**Hour 3–5: Pages — Dashboard + Datasets + DatasetDetail**

```jsx
// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listDatasets, checkHealth } from '../services/api';

export default function Dashboard() {
  const [datasets, setDatasets] = useState([]);
  const [health, setHealth]     = useState(null);

  useEffect(() => {
    checkHealth().then(setHealth);
    listDatasets().then(d => setDatasets(d.datasets || []));
  }, []);

  return (
    <div>
      <h1 style={{ color:'#1a1a2e' }}>⚛ QuantWarriors</h1>
      <p style={{ color:'#555', fontSize:16 }}>
        Hybrid Quantum-Classical Disease Detection Platform
      </p>

      {/* Stats row */}
      <div style={{ display:'flex', gap:16, margin:'24px 0' }}>
        {[
          { label:'Datasets',    value: datasets.length },
          { label:'Backend',     value: health?.status === 'healthy' ? '✓ Online' : '⚠ Offline' },
          { label:'Quantum',     value: 'Local Sim' },
          { label:'Models',      value: 'LR · SVM · RF · VQC' },
        ].map(card => (
          <div key={card.label} style={{
            flex:1, background:'white', borderRadius:12, padding:20, boxShadow:'0 2px 8px rgba(0,0,0,0.08)'
          }}>
            <div style={{ fontSize:22, fontWeight:'bold', color:'#1a1a2e' }}>{card.value}</div>
            <div style={{ fontSize:13, color:'#888', marginTop:4 }}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Demo quick-start */}
      <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.08)' }}>
        <h3>Quick Start</h3>
        <Link to="/datasets">
          <button style={btnPrimary}>+ Upload Dataset</button>
        </Link>
        <p style={{ fontSize:13, color:'#888', marginTop:12 }}>
          Or use a demo dataset: Breast Cancer · Heart Disease · Parkinson's
        </p>
      </div>

      {/* Pipeline diagram */}
      <div style={{ background:'white', borderRadius:12, padding:24, marginTop:16, boxShadow:'0 2px 8px rgba(0,0,0,0.08)' }}>
        <h3>Platform Pipeline</h3>
        <div style={{ display:'flex', alignItems:'center', flexWrap:'wrap', gap:8, fontSize:13 }}>
          {['Upload CSV','Profile','Validate','Preprocess','PCA → 8D','Classical + Quantum','Compare','Explain','Report'].map((s,i,arr) => (
            <>
              <span key={s} style={{ background:'#1a1a2e', color:'white', padding:'4px 12px', borderRadius:20 }}>{s}</span>
              {i < arr.length-1 && <span key={`arrow-${i}`} style={{ color:'#aaa' }}>→</span>}
            </>
          ))}
        </div>
      </div>
    </div>
  );
}

const btnPrimary = {
  background:'#e94560', color:'white', border:'none', padding:'10px 24px',
  borderRadius:8, fontSize:14, cursor:'pointer'
};
```

```jsx
// src/pages/Datasets.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadDataset, listDatasets } from '../services/api';
import FileDropzone from '../components/FileDropzone';

export default function Datasets() {
  const [datasets, setDatasets] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { listDatasets().then(d => setDatasets(d.datasets || [])); }, []);

  async function handleUpload(file) {
    setUploading(true);
    setUploadError(null);
    try {
      const result = await uploadDataset(file);
      if (result.status === 'REGISTERED') {
        navigate(`/datasets/${result.dataset_id}`);
      }
    } catch (err) {
      setUploadError(err.detail || 'Upload failed. Please check the file format.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h2>Datasets</h2>

      <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.08)', marginBottom:24 }}>
        <h3>Upload Biomedical Dataset</h3>
        <p style={{ color:'#666', fontSize:13 }}>Supported formats: CSV (tabular biomedical data)</p>
        <FileDropzone onFile={handleUpload} disabled={uploading} />
        {uploading && <p style={{ color:'#1565c0' }}>⟳ Uploading and analysing...</p>}
        {uploadError && (
          <div style={{ background:'#ffebee', border:'1px solid #ef9a9a', borderRadius:8, padding:12, color:'#c62828', marginTop:12 }}>
            ⚠ {uploadError}
          </div>
        )}
      </div>

      <h3>Registered Datasets ({datasets.length})</h3>
      {datasets.length === 0 ? (
        <p style={{ color:'#888' }}>No datasets yet. Upload one above.</p>
      ) : (
        <div style={{ display:'grid', gap:12 }}>
          {datasets.map(ds => (
            <div key={ds.dataset_id} onClick={() => navigate(`/datasets/${ds.dataset_id}`)}
              style={{ background:'white', borderRadius:12, padding:16, cursor:'pointer',
                       boxShadow:'0 2px 8px rgba(0,0,0,0.06)', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <div>
                <div style={{ fontWeight:'bold' }}>{ds.filename}</div>
                <div style={{ fontSize:13, color:'#888' }}>
                  {ds.display_id} · {(ds.file_size_bytes/1024).toFixed(1)} KB · {ds.container_type}
                </div>
              </div>
              <span style={{
                padding:'4px 12px', borderRadius:20, fontSize:12, fontWeight:'bold',
                background: ds.has_profile ? '#e8f5e9' : '#fff8e1',
                color: ds.has_profile ? '#2e7d32' : '#f57f17'
              }}>
                {ds.has_profile ? '✓ Profiled' : '⟳ Profiling'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

```jsx
// src/components/FileDropzone.jsx
import { useRef, useState } from 'react';

export default function FileDropzone({ onFile, disabled }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current.click()}
      style={{
        border: `2px dashed ${dragging ? '#1565c0' : '#ccc'}`,
        borderRadius:12, padding:40, textAlign:'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        background: dragging ? '#e3f2fd' : '#fafafa',
        transition:'all 0.2s'
      }}
    >
      <div style={{ fontSize:36 }}>📂</div>
      <div style={{ marginTop:8, color:'#555' }}>
        {disabled ? 'Uploading...' : 'Drop CSV here, or click to browse'}
      </div>
      <div style={{ fontSize:12, color:'#aaa', marginTop:4 }}>CSV only · max 100MB</div>
      <input ref={inputRef} type="file" accept=".csv" hidden
             onChange={e => e.target.files[0] && onFile(e.target.files[0])} />
    </div>
  );
}
```

```jsx
// src/pages/DatasetDetail.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getDatasetProfile } from '../services/api';
import Disclaimer from '../components/Disclaimer';

export default function DatasetDetail() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    async function load() {
      const data = await getDatasetProfile(datasetId);
      if (data.status === 'profiling_in_progress') {
        setPolling(true);
        setTimeout(load, 2000); // retry in 2s
      } else {
        setProfile(data);
        setPolling(false);
      }
    }
    load();
  }, [datasetId]);

  if (polling || !profile) return <p>⟳ Profiling dataset... <small>(this may take a moment)</small></p>;

  const totalSamples = Object.values(profile.class_distribution || {}).reduce((a,b)=>a+b,0);

  return (
    <div>
      <button onClick={() => navigate('/datasets')} style={{ background:'none', border:'none', cursor:'pointer', color:'#1565c0', marginBottom:16 }}>
        ← Back to Datasets
      </button>

      <h2>{profile.dimensions.rows} samples · {profile.dimensions.columns - 1} features</h2>

      <Disclaimer />

      {/* Stats cards */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, margin:'20px 0' }}>
        {[
          { label:'Samples',        value: profile.dimensions.rows },
          { label:'Features',       value: profile.features.numerical },
          { label:'Classes',        value: Object.keys(profile.class_distribution||{}).length },
          { label:'Missing Values', value: profile.missing_values.total === 0 ? '✓ None' : profile.missing_values.total },
        ].map(c => (
          <div key={c.label} style={{ background:'white', borderRadius:12, padding:20, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', textAlign:'center' }}>
            <div style={{ fontSize:26, fontWeight:'bold', color:'#1a1a2e' }}>{c.value}</div>
            <div style={{ fontSize:13, color:'#888' }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* Task and target */}
      <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
        <h3>Dataset Understanding</h3>
        <table style={{ width:'100%', fontSize:14 }}>
          <tbody>
            {[
              ['Target Column',   profile.target.candidate],
              ['Task',            profile.task.candidate.replace('_',' ')],
              ['Target Confidence', profile.target.confidence],
              ['Modality',        profile.modality],
            ].map(([k,v]) => (
              <tr key={k}>
                <td style={{ padding:'6px 0', color:'#888', width:'40%' }}>{k}</td>
                <td style={{ fontWeight:'bold' }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Class distribution */}
      {profile.class_distribution && (
        <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
          <h3>Class Distribution</h3>
          {Object.entries(profile.class_distribution).map(([cls, count]) => (
            <div key={cls} style={{ marginBottom:10 }}>
              <div style={{ display:'flex', justifyContent:'space-between', fontSize:13 }}>
                <span>Class {cls}</span>
                <span>{count} ({(count/totalSamples*100).toFixed(1)}%)</span>
              </div>
              <div style={{ background:'#eee', height:10, borderRadius:5, marginTop:4 }}>
                <div style={{ width:`${count/totalSamples*100}%`, height:10, borderRadius:5, background:'#1565c0' }} />
              </div>
            </div>
          ))}
          {profile.warnings?.map((w, i) => (
            <p key={i} style={{ color:'#e65100', fontSize:13, margin:'8px 0' }}>⚠ {w}</p>
          ))}
        </div>
      )}

      {/* Start experiment */}
      <div style={{ background:'#e3f2fd', borderRadius:12, padding:24 }}>
        <h3>Ready to Experiment</h3>
        <p style={{ color:'#555', fontSize:14 }}>
          System will run: Logistic Regression, SVM, Random Forest (Classical)
          + VQC with 8 qubits (Quantum) on a 30→8 PCA representation.
        </p>
        <button onClick={() => navigate(`/experiments/new/${datasetId}`)}
          style={{ background:'#e94560', color:'white', border:'none', padding:'12px 28px', borderRadius:8, fontSize:15, cursor:'pointer' }}>
          Design Experiment →
        </button>
      </div>
    </div>
  );
}
```

**Hour 5–6: ExperimentNew page**

```jsx
// src/pages/ExperimentNew.jsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { createExperiment, runExperiment } from '../services/api';

const PLAN = {
  task: 'Binary Classification',
  preprocessing: 'StandardScaler (fitted on training data only)',
  reduction: 'PCA → 8 principal components (≈94% variance retained)',
  classicalModels: ['Logistic Regression', 'SVM', 'Random Forest'],
  quantumModel: 'VQC — 8 qubits · 2 layers · 1024 shots',
  evaluation: 'Stratified 80/20 split · seed=42',
  backend: 'Local Quantum Simulator (PennyLane default.qubit)',
  rules: [
    'Binary classification detected → classification experiment',
    'Numerical features > quantum dimensions → PCA required',
    '8 PCA features ≤ 8 max qubits → quantum model enabled',
    'Class imbalance 1.68:1 → class_weight=balanced applied',
    'Stratified split preserves class proportions',
  ]
};

export default function ExperimentNew() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const [running, setRunning] = useState(false);

  async function handleRun() {
    setRunning(true);
    try {
      const { experiment_id } = await createExperiment(datasetId, 8);
      await runExperiment(experiment_id);
      navigate(`/experiments/${experiment_id}`);
    } catch {
      setRunning(false);
    }
  }

  return (
    <div>
      <h2>Experiment Plan</h2>

      <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
        <h3 style={{ color:'#1565c0' }}>Why This Pipeline?</h3>
        {PLAN.rules.map((r, i) => (
          <div key={i} style={{ display:'flex', alignItems:'flex-start', margin:'8px 0', fontSize:14 }}>
            <span style={{ color:'#2e7d32', marginRight:10, marginTop:2 }}>✓</span>
            <span>{r}</span>
          </div>
        ))}
      </div>

      <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
        <h3>Configured Pipeline</h3>
        <table style={{ width:'100%', fontSize:14 }}>
          <tbody>
            {Object.entries({
              'Task':              PLAN.task,
              'Preprocessing':     PLAN.preprocessing,
              'Feature Reduction': PLAN.reduction,
              'Classical Models':  PLAN.classicalModels.join(' · '),
              'Quantum Model':     PLAN.quantumModel,
              'Evaluation':        PLAN.evaluation,
              'Quantum Backend':   PLAN.backend,
            }).map(([k,v]) => (
              <tr key={k} style={{ borderBottom:'1px solid #f0f0f0' }}>
                <td style={{ padding:'8px 0', color:'#888', width:'35%', fontSize:13 }}>{k}</td>
                <td style={{ fontWeight:'500' }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button onClick={handleRun} disabled={running}
        style={{ background: running ? '#aaa' : '#e94560', color:'white', border:'none',
                 padding:'14px 36px', borderRadius:8, fontSize:16, cursor: running ? 'not-allowed' : 'pointer', width:'100%' }}>
        {running ? '⟳ Starting experiment...' : '▶  Run Experiment'}
      </button>
    </div>
  );
}
```

### Day 2

**Hour 1–4: ExperimentDetail (progress + results + explanation + cost)**

This is the most complex page — it has 4 tabs:

```jsx
// src/pages/ExperimentDetail.jsx
import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getExperimentStatus, getExperimentResults, getExplanation, generateReport } from '../services/api';
import StageProgress from '../components/StageProgress';
import MetricsTable from '../components/MetricsTable';
import FeatureImportanceBar from '../components/FeatureImportanceBar';
import Disclaimer from '../components/Disclaimer';

export default function ExperimentDetail() {
  const { expId } = useParams();
  const [status,      setStatus]      = useState(null);
  const [results,     setResults]     = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [tab,         setTab]         = useState('progress');
  const [reportUrl,   setReportUrl]   = useState(null);
  const intervalRef = useRef(null);

  // Poll status until completed or failed
  useEffect(() => {
    async function poll() {
      const s = await getExperimentStatus(expId);
      setStatus(s);
      if (s.status === 'COMPLETED') {
        clearInterval(intervalRef.current);
        const r = await getExperimentResults(expId);
        setResults(r);
        const e = await getExplanation(expId, 'VQC');
        setExplanation(e);
        setTab('results');
      } else if (s.status === 'FAILED') {
        clearInterval(intervalRef.current);
      }
    }
    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => clearInterval(intervalRef.current);
  }, [expId]);

  async function handleGenerateReport() {
    const r = await generateReport(expId);
    setReportUrl(`http://localhost:8000/api/experiments/${expId}/report`);
  }

  const tabs = [
    { key:'progress',    label:'Progress'     },
    { key:'results',     label:'Results'      },
    { key:'explain',     label:'Explainability'},
    { key:'cost',        label:'Cost & Resources' },
  ];

  return (
    <div>
      <Disclaimer />

      {/* Tab bar */}
      <div style={{ display:'flex', gap:4, marginBottom:24, borderBottom:'2px solid #eee', paddingBottom:0 }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{
              padding:'10px 20px', border:'none', cursor:'pointer', fontSize:14,
              background: tab===t.key ? '#1a1a2e' : 'transparent',
              color: tab===t.key ? 'white' : '#555',
              borderRadius:'8px 8px 0 0'
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Progress tab */}
      {tab === 'progress' && (
        <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)' }}>
          <h3>Experiment: {expId}</h3>
          {status ? (
            <>
              <StageProgress
                status={status.status}
                stage={status.stage}
                completedModels={status.completed_models}
                circuitExecutions={status.circuit_executions}
              />
              <div style={{ marginTop:16, color:'#888', fontSize:13 }}>
                Elapsed: {status.elapsed_seconds}s
                {status.current_model && ` · Running: ${status.current_model}`}
                {status.circuit_executions > 0 && ` · Circuit executions: ${status.circuit_executions.toLocaleString()}`}
              </div>
              {status.status === 'FAILED' && (
                <div style={{ background:'#ffebee', padding:12, borderRadius:8, color:'#c62828', marginTop:12 }}>
                  ⚠ Experiment failed: {status.error_message || 'Unknown error'}
                </div>
              )}
            </>
          ) : <p>Loading...</p>}
        </div>
      )}

      {/* Results tab */}
      {tab === 'results' && results && (
        <div>
          {/* Quantum Value Assessment — the "wow" screen */}
          <div style={{
            background:'linear-gradient(135deg,#1a1a2e,#16213e)', color:'white',
            borderRadius:16, padding:32, marginBottom:24, textAlign:'center'
          }}>
            <h2 style={{ margin:0, fontSize:22 }}>QUANTUM VALUE ASSESSMENT</h2>
            <div style={{ fontSize:42, fontWeight:'bold', margin:'16px 0', color:
              results.comparison.classification === 'QUANTUM_ADVANTAGE' ? '#4caf50' :
              results.comparison.classification === 'TRADEOFF' ? '#ff9800' :
              results.comparison.classification === 'PERFORMANCE_PARITY' ? '#2196f3' : '#ef5350'
            }}>
              {results.comparison.classification.replace('_',' ')}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:24, maxWidth:500, margin:'20px auto' }}>
              {[
                { label:'Best Classical ('+results.comparison.classical_best.model_name+')', ...results.comparison.classical_best.metrics },
                { label:'Best Quantum (VQC)', ...results.comparison.quantum_best.metrics },
              ].map((m, i) => (
                <div key={i} style={{ background:'rgba(255,255,255,0.1)', borderRadius:12, padding:16 }}>
                  <div style={{ fontSize:13, color:'#aaa', marginBottom:8 }}>{m.label}</div>
                  {[['Recall', m.recall], ['ROC-AUC', m.roc_auc], ['Accuracy', m.accuracy]].map(([k,v]) => (
                    <div key={k} style={{ display:'flex', justifyContent:'space-between', margin:'4px 0' }}>
                      <span style={{ fontSize:13, color:'#ccc' }}>{k}</span>
                      <span style={{ fontWeight:'bold' }}>{(v*100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <div style={{ fontSize:13, color:'#aaa', maxWidth:500, margin:'0 auto' }}>
              {results.comparison.recommendation_text}
            </div>
          </div>

          {/* Key observations */}
          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
            <h3>Key Observations</h3>
            {results.comparison.observations.map((obs, i) => (
              <div key={i} style={{ display:'flex', alignItems:'flex-start', margin:'8px 0', fontSize:14 }}>
                <span style={{ color:'#1565c0', marginRight:10 }}>•</span>
                <span>{obs}</span>
              </div>
            ))}
          </div>

          {/* Full comparison table */}
          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)' }}>
            <h3>All Models Comparison</h3>
            <MetricsTable models={results.models} />
          </div>

          {/* Resource comparison */}
          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginTop:16 }}>
            <h3>Resource Comparison</h3>
            <table style={{ width:'100%', fontSize:14, borderCollapse:'collapse' }}>
              <thead>
                <tr style={{ background:'#f5f7fa' }}>
                  {['Model','Type','Train Time','Inference','Memory','Circuit Executions'].map(h=>(
                    <th key={h} style={{ padding:'8px 12px', textAlign:'left', borderBottom:'2px solid #eee' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(results.models).map(([name, r]) => (
                  <tr key={name}>
                    <td style={tdc}>{r.model_name}</td>
                    <td style={tdc}>{r.model_type}</td>
                    <td style={tdc}>{r.resource_usage.training_time_seconds.toFixed(1)}s</td>
                    <td style={tdc}>{(r.resource_usage.inference_time_seconds*1000).toFixed(0)}ms</td>
                    <td style={tdc}>{r.resource_usage.memory_peak_mb.toFixed(0)} MB</td>
                    <td style={tdc}>{r.quantum_metrics?.total_circuit_executions?.toLocaleString() ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button onClick={handleGenerateReport} style={{
            marginTop:16, background:'#1565c0', color:'white', border:'none',
            padding:'12px 28px', borderRadius:8, fontSize:14, cursor:'pointer'
          }}>
            📄 Generate Report
          </button>
          {reportUrl && <a href={reportUrl} target="_blank" rel="noreferrer" style={{ marginLeft:12, color:'#1565c0' }}>Open Report →</a>}
        </div>
      )}

      {/* Explainability tab */}
      {tab === 'explain' && explanation && (
        <div>
          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
            <h3>Sample Prediction Explanation</h3>
            <div style={{ display:'flex', gap:16, flexWrap:'wrap' }}>
              <div style={{ background: explanation.prediction.value===1 ? '#ffebee' : '#e8f5e9', borderRadius:8, padding:16, minWidth:150 }}>
                <div style={{ fontSize:11, color:'#888' }}>Prediction</div>
                <div style={{ fontSize:20, fontWeight:'bold', color: explanation.prediction.value===1 ? '#c62828' : '#2e7d32' }}>
                  {explanation.prediction.value === 1 ? 'POSITIVE' : 'NEGATIVE'}
                </div>
              </div>
              <div style={{ background:'#f5f5f5', borderRadius:8, padding:16, minWidth:150 }}>
                <div style={{ fontSize:11, color:'#888' }}>Model Score</div>
                <div style={{ fontSize:20, fontWeight:'bold' }}>{explanation.prediction.score.toFixed(3)}</div>
                <div style={{ fontSize:11, color:'#e65100', marginTop:4 }}>Uncalibrated — not a probability</div>
              </div>
              <div style={{ background: explanation.prediction.is_correct ? '#e8f5e9' : '#ffebee', borderRadius:8, padding:16, minWidth:150 }}>
                <div style={{ fontSize:11, color:'#888' }}>Correct?</div>
                <div style={{ fontSize:20, fontWeight:'bold' }}>{explanation.prediction.is_correct ? '✓ Yes' : '✗ No'}</div>
              </div>
            </div>
            {explanation.warnings.map((w,i) => (
              <p key={i} style={{ fontSize:12, color:'#e65100', margin:'6px 0' }}>⚠ {w}</p>
            ))}
          </div>

          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
            <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)' }}>
              <FeatureImportanceBar features={explanation.feature_importance} title="This Prediction — Top Features" />
            </div>
            <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)' }}>
              <FeatureImportanceBar features={explanation.global_importance} title="Global Feature Importance" />
            </div>
          </div>

          {explanation.quantum_circuit_explanation && (
            <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginTop:16 }}>
              <h3>⚛ Quantum Circuit</h3>
              <div style={{ display:'flex', gap:24, flexWrap:'wrap' }}>
                {[
                  ['Qubits',        explanation.quantum_circuit_explanation.qubits],
                  ['Circuit Depth', explanation.quantum_circuit_explanation.circuit_depth],
                  ['Encoding',      explanation.quantum_circuit_explanation.encoding_method],
                  ['Backend',       'LOCAL_SIMULATOR'],
                ].map(([k,v]) => (
                  <div key={k} style={{ background:'#e3f2fd', borderRadius:8, padding:'12px 20px', textAlign:'center' }}>
                    <div style={{ fontSize:18, fontWeight:'bold', color:'#1565c0' }}>{v}</div>
                    <div style={{ fontSize:12, color:'#888' }}>{k}</div>
                  </div>
                ))}
              </div>
              <h4 style={{ marginTop:16 }}>Feature → Qubit Mapping</h4>
              <div style={{ display:'flex', gap:8, flexWrap:'wrap', fontSize:12 }}>
                {Object.entries(explanation.quantum_circuit_explanation.feature_to_qubit_mapping).map(([feat, qubit]) => (
                  <div key={feat} style={{ background:'#f5f5f5', padding:'4px 10px', borderRadius:20 }}>
                    {feat} → {qubit}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginTop:16 }}>
            <h3>Pipeline Trace</h3>
            <div style={{ fontSize:13 }}>
              {explanation.pipeline_trace.map((step, i) => (
                <div key={i} style={{ display:'flex', alignItems:'flex-start', margin:'12px 0' }}>
                  <div style={{ background:'#1a1a2e', color:'white', borderRadius:20, padding:'2px 10px', fontSize:11, marginRight:12, whiteSpace:'nowrap' }}>
                    {step.phase}
                  </div>
                  <div>
                    <div style={{ fontWeight:'bold' }}>{step.component}</div>
                    <div style={{ color:'#888' }}>
                      {step.artifact && `→ ${step.artifact}`}
                      {step.dimensions && ` (${step.dimensions})`}
                      {step.note && ` — ${step.note}`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Cost tab */}
      {tab === 'cost' && results && (
        <div>
          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginBottom:16 }}>
            <h3>Quantum Resource Usage</h3>
            {results.models.vqc?.quantum_metrics && (
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16 }}>
                {[
                  ['Qubits',             results.models.vqc.quantum_metrics.qubits],
                  ['Circuit Depth',      results.models.vqc.quantum_metrics.circuit_depth],
                  ['Gate Count',         results.models.vqc.quantum_metrics.gate_count],
                  ['Two-Qubit Gates',    results.models.vqc.quantum_metrics.two_qubit_gates],
                  ['Shots/Execution',    results.models.vqc.quantum_metrics.shots],
                  ['Total Executions',   results.models.vqc.quantum_metrics.total_circuit_executions?.toLocaleString()],
                  ['Backend',            results.models.vqc.quantum_metrics.backend_type],
                  ['Encoding',           results.models.vqc.quantum_metrics.encoding_method],
                  ['Train Time',         results.models.vqc.resource_usage.training_time_seconds.toFixed(1)+'s'],
                ].map(([k,v]) => (
                  <div key={k} style={{ background:'#e3f2fd', borderRadius:8, padding:'12px 16px' }}>
                    <div style={{ fontSize:16, fontWeight:'bold', color:'#1565c0' }}>{v}</div>
                    <div style={{ fontSize:12, color:'#888' }}>{k}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ background:'#e8f5e9', borderRadius:12, padding:20, border:'1px solid #a5d6a7' }}>
            <h3 style={{ margin:0, color:'#2e7d32' }}>Financial Cost: ₹0</h3>
            <p style={{ color:'#555', fontSize:14, margin:'8px 0 0' }}>
              This experiment ran on a <strong>local quantum simulator</strong>.
              No cloud quantum services were used. Computational cost is CPU time and RAM only.
            </p>
          </div>

          <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)', marginTop:16 }}>
            <h3>Performance vs Cost</h3>
            <table style={{ width:'100%', fontSize:14, borderCollapse:'collapse' }}>
              <thead>
                <tr style={{ background:'#f5f7fa' }}>
                  {['Model','ROC-AUC','Recall','Train Time','Cost Ratio'].map(h=>(
                    <th key={h} style={{ padding:'8px 12px', textAlign:'left', borderBottom:'2px solid #eee' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(results.models).map(([name, r]) => {
                  const baseTime = results.models.logistic_regression?.resource_usage?.training_time_seconds || 1;
                  const ratio = (r.resource_usage.training_time_seconds / baseTime).toFixed(1);
                  return (
                    <tr key={name}>
                      <td style={tdc}>{r.model_name}</td>
                      <td style={tdc}>{(r.metrics.roc_auc*100).toFixed(1)}%</td>
                      <td style={tdc}>{(r.metrics.recall*100).toFixed(1)}%</td>
                      <td style={tdc}>{r.resource_usage.training_time_seconds.toFixed(1)}s</td>
                      <td style={tdc}>{ratio}×</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Loading state for non-progress tabs before completion */}
      {(tab !== 'progress') && !results && (
        <div style={{ textAlign:'center', padding:40, color:'#888' }}>
          ⟳ Waiting for experiment to complete...
        </div>
      )}
    </div>
  );
}

const tdc = { padding:'8px 12px', borderBottom:'1px solid #f0f0f0' };
```

**Hour 4–5: Reports page + global CSS**

```jsx
// src/pages/Reports.jsx
import { useState } from 'react';

export default function Reports() {
  // Reports are opened via link in ExperimentDetail — this page is a placeholder
  return (
    <div>
      <h2>Reports</h2>
      <p style={{ color:'#888' }}>
        Reports are generated from the Experiment Results tab.
        Click "Generate Report" after an experiment completes.
      </p>
      <div style={{ background:'white', borderRadius:12, padding:24, boxShadow:'0 2px 8px rgba(0,0,0,0.07)' }}>
        <p style={{ color:'#1565c0' }}>
          Reports open as full HTML pages at{' '}
          <code>http://localhost:8000/api/experiments/&#123;id&#125;/report</code>
        </p>
      </div>
    </div>
  );
}
```

```css
/* src/index.css */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f5f7fa; }
h1, h2, h3, h4 { color: #1a1a2e; }
button:hover { opacity: 0.9; }
a { color: #1565c0; }
```

**Hour 5–6: Flip MOCK_MODE to false and test against real backend**

In `src/services/api.js`, change:
```javascript
const MOCK_MODE = false;
```

Run both servers:
```bash
# Terminal 1 — backend
cd d:/projects/SIH2026/mvp
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend  
cd d:/projects/SIH2026/mvp/frontend
npm run dev
```

Walk through the full flow:
1. `http://localhost:5173` → Dashboard shows "✓ Online"
2. Datasets → Upload `data/demo/breast_cancer.csv`
3. Redirects to DatasetDetail → 569 rows, 30 features, diagnosis target
4. "Design Experiment →" → ExperimentNew shows the plan
5. "Run Experiment" → Progress page polls every 2 seconds
6. Completion → switches to Results tab with QUANTUM VALUE ASSESSMENT
7. Explainability tab shows feature importance bars + circuit info
8. Cost tab shows 0 financial cost + quantum resource metrics

---

## 7. Mock Data to Build Against on Day 1

All mock data is embedded directly in `src/services/api.js` under `MOCK_MODE = true`. The exact shapes match the backend contracts described in §4. You do not need to create any additional mock files.

The four demo datasets your teammates will populate the backend with:

| Dataset | Rows | Features | Target | Notes |
|---|---|---|---|---|
| Breast Cancer Wisconsin | 569 | 30 | `diagnosis` (M/B) | Main demo dataset |
| Heart Disease UCI | 303 | 13 | `target` (0/1) | Second demo |
| Parkinson's Disease | 195 | 22 | `status` (0/1) | Grouped split |
| Pima Indians Diabetes | 768 | 8 | `Outcome` (0/1) | Optional |

---

## 8. Definition of Done

**Setup:**
- [ ] `npm run dev` starts without errors at `localhost:5173`.
- [ ] `npm run build` produces no TypeScript/ESLint errors.
- [ ] CORS works — browser console shows no CORS errors when calling `localhost:8000`.

**API layer:**
- [ ] `src/services/api.js` is the single source for ALL API calls — no `fetch` calls in components.
- [ ] `MOCK_MODE = true` mode works completely without a running backend.
- [ ] `MOCK_MODE = false` mode works when backend is running on port 8000.
- [ ] Upload errors (400, 413) display user-friendly messages, not raw JSON.

**Dashboard:**
- [ ] Shows dataset count, backend health status, and platform pipeline diagram.
- [ ] "Upload Dataset" button navigates to Datasets page.

**Datasets page:**
- [ ] FileDropzone accepts drag-and-drop and click-to-browse CSV files.
- [ ] Uploading shows "⟳ Uploading and analysing..." state.
- [ ] After successful upload redirects to DatasetDetail.
- [ ] Lists all registered datasets with profiling status badge.

**DatasetDetail page:**
- [ ] Shows 4 stat cards: Samples, Features, Classes, Missing Values.
- [ ] Shows target candidate and task type.
- [ ] Shows class distribution bars with percentages.
- [ ] Shows imbalance warnings if present.
- [ ] Polls automatically when profiling is in progress (202 response).
- [ ] "Design Experiment →" button navigates to ExperimentNew.

**ExperimentNew page:**
- [ ] Shows all pipeline configuration items.
- [ ] Shows "Why This Pipeline?" with rules checked.
- [ ] "Run Experiment" creates experiment, triggers run, navigates to ExperimentDetail.

**ExperimentDetail — Progress tab:**
- [ ] Shows ✓/●/○ stage indicators.
- [ ] Polls `GET /status` every 2 seconds while running.
- [ ] Shows circuit execution count during quantum training stage.
- [ ] Automatically switches to Results tab when status = COMPLETED.
- [ ] Shows error message if status = FAILED.

**ExperimentDetail — Results tab:**
- [ ] QUANTUM VALUE ASSESSMENT hero section shows classification in large text.
- [ ] Classification colored: green=QUANTUM_ADVANTAGE, orange=TRADEOFF, blue=PARITY, red=CLASSICAL_ADVANTAGE.
- [ ] Shows both best classical and best quantum metrics side-by-side.
- [ ] Full comparison table with all 4 models (LR, SVM, RF, VQC).
- [ ] Best recall highlighted in green, best AUC highlighted in green.
- [ ] Resource table includes quantum circuit executions for VQC row.
- [ ] "Generate Report" button creates report and shows "Open Report →" link.

**ExperimentDetail — Explainability tab:**
- [ ] Shows prediction value (POSITIVE/NEGATIVE), score, and correct/incorrect badge.
- [ ] Shows "Uncalibrated — not a probability" warning under score.
- [ ] Shows top-feature importance bars (positive = green, negative = red).
- [ ] Shows global feature importance bars.
- [ ] Shows quantum circuit info card (qubits, depth, encoding, mapping).
- [ ] Shows pipeline trace with all phase steps.
- [ ] Shows 3 warning disclaimers.

**ExperimentDetail — Cost tab:**
- [ ] Shows quantum resource grid (qubits, circuit depth, gate count, shots, executions).
- [ ] Shows "Financial Cost: ₹0" with local simulator explanation.
- [ ] Shows performance vs cost table with all 4 models.

**Disclaimer:**
- [ ] `<Disclaimer />` component appears on DatasetDetail, ExperimentDetail, and anywhere predictions are shown.
- [ ] Text says "RESEARCH / BENCHMARKING SYSTEM" and "NOT clinical diagnoses."
- [ ] Prediction score on explainability tab says "Uncalibrated — not a probability."

---

## 9. Common Failure Modes to Avoid

**From implementaion_plan.md §93 — Never put ML logic in React:**
> "The UI should consume the backend rather than contain ML logic. Never put PCA, VQC, RandomForest, SHAP inside React."
- **Fix:** `src/services/api.js` calls backend APIs. Zero `import sklearn`, zero data science code in any `.jsx` file. React only displays and interacts.

**From implementaion_plan.md §80 — Never block on long experiments:**
> "The frontend should never wait for the entire experiment in one HTTP request."
- **Fix:** `POST /experiments/{id}/run` returns immediately. Frontend polls `GET /status` every 2 seconds with `setInterval`. Never use `await` on a request that could take 15 minutes.

**From implementaion_plan.md §84 — Medical disclaimer:**
> "Do not call the output 'diagnosis' in the sense of a clinical decision."
- **Fix:** Prediction display says "POSITIVE" or "NEGATIVE", never "Diagnosed with cancer". `<Disclaimer />` component always visible alongside predictions.

**From phase12.md §20–21 — Uncalibrated scores:**
> "0.91 does not automatically mean 91% probability of disease."
- **Fix:** Score display always shows "Model Score" not "Probability". Include "Uncalibrated — not a clinical probability" text under every score display.

**CORS during development:**
> Vite dev server on port 5173 calling FastAPI on port 8000 without CORS config causes blocked requests.
- **Fix:** `backend/main.py` already has CORS middleware for `localhost:5173`. If you still get CORS errors, check that the backend is running and that your API calls use the exact base URL `http://localhost:8000` (not `https://`).

**Polling memory leak:**
> `setInterval` inside `useEffect` that doesn't clean up causes multiple intervals to stack.
- **Fix:** Always `return () => clearInterval(intervalRef.current)` from the `useEffect` cleanup. Use `useRef` to store the interval ID so it survives re-renders.

**From implementaion_plan.md §61 — User-friendly errors:**
> "Bad: `KeyError: target`. Good: `DATASET ERROR — We could not identify the target column.`"
- **Fix:** Catch API errors in try/catch, display the `error.detail` field from the backend response in a styled error box. Never let raw `[object Object]` appear in the UI.

**Vite proxy (optional but helpful):**
> If you want to avoid hardcoding `localhost:8000` everywhere, configure a Vite proxy:
```js
// vite.config.js
export default {
  server: {
    proxy: { '/api': 'http://localhost:8000' }
  }
}
```
Then `api.js` uses `/api/...` instead of `http://localhost:8000/api/...`. This also eliminates CORS issues entirely in dev.

---

## 10. Ready-to-Paste First Prompt

```
I am building the complete frontend for a Hybrid Quantum-Classical Disease Detection 
Platform called QuantWarriors. Tech stack: React 18 + Vite + React Router v6.
No TypeScript. No Redux. No external UI library (plain CSS-in-JS inline styles only).

Project root: d:/projects/SIH2026/mvp/frontend/
Backend URL: http://localhost:8000

I need these 6 pages:
1. Dashboard (/) — platform stats, quick-start, pipeline diagram
2. Datasets (/datasets) — CSV upload dropzone + dataset list
3. DatasetDetail (/datasets/:id) — profile stats, class distribution, → start experiment
4. ExperimentNew (/experiments/new/:datasetId) — show plan, "Run" button
5. ExperimentDetail (/experiments/:expId) — 4 tabs: Progress | Results | Explainability | Cost
6. Reports (/reports) — placeholder pointing to generated HTML reports

API contracts I must consume (all backend, I never write ML code):
- POST /api/datasets/upload → { dataset_id, display_id, status, filename, ... }
- GET  /api/datasets → { datasets: [...], total }
- GET  /api/datasets/:id/profile → { dimensions, features, target, class_distribution, warnings }
  (returns 202 { status: "profiling_in_progress" } while computing — must poll)
- POST /api/experiments → { experiment_id }
- POST /api/experiments/:id/run → { status: "started" } (returns immediately!)
- GET  /api/experiments/:id/status → { status, stage, progress, circuit_executions, ... }
  (poll every 2s while RUNNING, stop when COMPLETED or FAILED)
- GET  /api/experiments/:id/results → { models: {lr, svm, rf, vqc}, comparison: {...} }
- GET  /api/experiments/:id/explanation?model_name=VQC → { feature_importance, quantum_circuit_explanation, pipeline_trace, warnings }
- POST /api/experiments/:id/report → { report_path }
- GET  /api/experiments/:id/report → HTML file

CRITICAL RULES:
1. ALL api calls go through src/services/api.js — zero fetch() calls in components
2. MOCK_MODE flag in api.js: when true, return hardcoded JSON matching contracts above
3. Never put ML logic in React (no sklearn, no numpy, no PCA)
4. POST /run returns immediately — use setInterval polling for status, never await long work
5. Always show Disclaimer component when displaying predictions
6. Prediction score label = "Model Score" NOT "Probability" 
7. Include text "Uncalibrated — not a clinical probability" near every score display
8. Clean up setInterval in useEffect cleanup to prevent memory leaks

Key UI features:
- ExperimentDetail Results tab: large "QUANTUM VALUE ASSESSMENT" hero with classification 
  (QUANTUM_ADVANTAGE=green / TRADEOFF=orange / PERFORMANCE_PARITY=blue / CLASSICAL_ADVANTAGE=red)
- MetricsTable: all 4 models, highlight best recall and best AUC in green bold
- StageProgress: ✓ done / ● running / ○ pending for preprocessing→classical→quantum→benchmarking
- FeatureImportanceBar: horizontal bars, positive=green, negative=red
- Circuit info card: qubits, circuit depth, encoding method, feature→qubit mapping

Build the files in this order:
1. src/services/api.js (with MOCK_MODE=true and all mock data)
2. src/components/Disclaimer.jsx
3. src/components/StageProgress.jsx
4. src/components/MetricsTable.jsx
5. src/components/FeatureImportanceBar.jsx
6. src/components/FileDropzone.jsx
7. src/App.jsx (layout + router)
8. src/pages/Dashboard.jsx
9. src/pages/Datasets.jsx
10. src/pages/DatasetDetail.jsx
11. src/pages/ExperimentNew.jsx
12. src/pages/ExperimentDetail.jsx (the big one — 4 tabs)
13. src/pages/Reports.jsx

After each file, show what it looks like (describe the UI). 
After all files are done, tell me how to flip MOCK_MODE=false and test with the real backend.
```
