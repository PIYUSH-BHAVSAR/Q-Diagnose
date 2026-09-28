<div align="center">

# ⚛ Q-Diagnose

### Hybrid Quantum-Classical Machine Learning Platform for Early Disease Detection

**SIH 2026 · Problem Statement 3 · Team QuantWarriors**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![PennyLane](https://img.shields.io/badge/PennyLane-QML-7C3AED?style=flat)](https://pennylane.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

</div>

---

## The Problem

Classical ML models plateau when applied to high-dimensional, noisy biomedical data — genomics, imaging features, electronic health records. They miss intricate cross-feature correlations that live in complex, non-linear manifolds. Meanwhile, pure quantum computing is still years from practical clinical use.

**Q-Diagnose bridges that gap.** It is a production-grade benchmarking platform that runs classical algorithms and a Variational Quantum Classifier (VQC) side-by-side on the same biomedical dataset, then gives an honest, evidence-based verdict on whether quantum advantage was achieved.

---

## How It Satisfies Every Deliverable

| PS Deliverable | What Q-Diagnose Delivers |
|---|---|
| **D1 · Data Pre-processing & Feature Engineering** | Full ingestion pipeline — format validation, SHA-256 dedup, magic-byte security check, background profiling, StandardScaler fitted on train only, PCA dimensionality reduction, NaN imputation, identifier column removal |
| **D2 · Hybrid Quantum-Classical Architecture** | FastAPI orchestrator → `FeaturePipeline` → classical arm (LR, SVM, RF on full features) + quantum arm (VQC on PCA-reduced features = qubits), identical train/test split for both arms — no leakage |
| **D3 · Quantum ML Models** | PennyLane VQC with angle encoding, parameterised RealAmplitudes ansatz, COBYLA optimiser, local simulator; QuantumSVM stub ready for hardware backend swap |
| **D4 · Prediction & Decision Support** | Live patient inference endpoint, probability scoring, risk stratification (LOW / MODERATE / HIGH / CRITICAL), threshold tuning to hit target sensitivity/specificity |
| **D5 · Software Platform / Prototype** | Full React dashboard — dataset upload, profiling, experiment creation, live progress polling, metric comparison charts, HTML report download, explainability view |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React Frontend (Vite)                        │
│  Dashboard → Upload → Profile → Plan → Run → Poll → Results → Report│
└──────────────────────────┬──────────────────────────────────────────┘
                           │  HTTP /api/*  (Vite proxy → port 8000)
┌──────────────────────────▼──────────────────────────────────────────┐
│                       FastAPI Backend                                │
│                                                                      │
│   POST /api/datasets/upload   GET /api/datasets/{id}/profile        │
│   POST /api/experiments       POST /api/experiments/{id}/run        │
│   GET  /api/experiments/{id}/status   (polled every 2s)             │
│   GET  /api/experiments/{id}/results  /recommendation  /explanation │
│   POST /api/experiments/{id}/report   /predict                      │
└────────┬────────────────────────────────────┬────────────────────────┘
         │                                    │
┌────────▼──────────┐              ┌──────────▼──────────────────────┐
│  Feature Pipeline │              │     Experiment Executor          │
│                   │              │  (BackgroundTask — non-blocking) │
│ 1. Format guard   │              │                                  │
│ 2. NaN impute     │              │  CREATED → VALIDATING            │
│ 3. Drop id cols   │              │  → PREPROCESSING                 │
│ 4. StandardScaler │              │  → RUNNING_CLASSICAL             │
│ 5. PCA (n=qubits) │              │  → RUNNING_QUANTUM               │
│ 6. Stratified     │              │  → BENCHMARKING                  │
│    80/20 split    │              │  → COMPLETED / FAILED            │
└───────────────────┘              └──────────────────────────────────┘
         │                                    │
┌────────▼──────────┐              ┌──────────▼──────────────────────┐
│  Classical Arm    │              │       Quantum Arm (PennyLane)   │
│                   │              │                                  │
│ LogisticRegression│              │  Angle encoding → qubit register │
│ SVM (RBF kernel)  │              │  RealAmplitudes ansatz           │
│ Random Forest     │              │  COBYLA optimiser                │
│                   │              │  Local simulator (default.qubit) │
│ Trains on X_train │              │  Trains on X_train_reduced       │
│ (full features)   │              │  (PCA → n_components qubits)     │
└────────┬──────────┘              └──────────┬──────────────────────┘
         └────────────────┬───────────────────┘
                 ┌────────▼────────┐
                 │  Benchmarking   │
                 │                 │
                 │ Accuracy        │
                 │ Precision       │
                 │ Recall          │
                 │ F1-Score        │
                 │ ROC-AUC         │
                 │ PR-AUC          │
                 │ Specificity     │
                 └────────┬────────┘
                 ┌────────▼────────┐
                 │  Recommendation │
                 │                 │
                 │ QUANTUM_ADVANTAGE│
                 │ PERFORMANCE_    │
                 │   PARITY        │
                 │ CLASSICAL_      │
                 │   ADVANTAGE     │
                 │ TRADEOFF        │
                 └─────────────────┘
```

---

## Repository Structure

```
Q-Diagnose/
│
├── backend/                    # FastAPI application
│   ├── api/
│   │   ├── datasets.py         # Upload, profile, validate endpoints
│   │   └── experiments.py      # Full experiment lifecycle endpoints
│   ├── benchmarking/
│   │   ├── comparison.py       # ModelComparison — ROC-AUC ranked table
│   │   ├── metrics.py          # MetricsCalculator
│   │   ├── recommendation.py   # RecommendationEngine — quantum vs classical verdict
│   │   └── risk_stratification.py  # RiskStratifier + ThresholdTuner
│   ├── core/
│   │   ├── config.py           # Typed config loader (config.yaml)
│   │   ├── exceptions.py       # Domain exceptions
│   │   └── logging.py          # Structured logging
│   ├── data/
│   │   ├── adapters.py         # Dataset-specific adapters (BreastCancer, Heart, etc.)
│   │   └── loader.py           # DatasetIngestionService + DatasetLoader
│   ├── experiments/
│   │   ├── executor.py         # ExperimentExecutor — full pipeline orchestration
│   │   └── manager.py          # ExperimentManager — status + artifact CRUD
│   ├── models/
│   │   ├── classical/          # LR, SVM, RandomForest wrappers
│   │   ├── quantum/            # VQC (PennyLane), QuantumSVM
│   │   ├── registry.py         # ModelRegistry
│   │   └── result.py           # ModelResult dataclass
│   ├── reports/
│   │   └── generator.py        # 16-section HTML report + cost JSON
│   ├── storage/
│   │   ├── database.py         # SQLite + SQLAlchemy setup
│   │   ├── files.py            # LocalFileStorage
│   │   ├── models.py           # ORM models (Dataset, Experiment, ModelResult)
│   │   └── repositories.py     # Repository pattern — all DB queries
│   └── main.py                 # FastAPI app entry point
│
├── features/                   # Feature engineering pipeline (standalone)
│   ├── pipeline.py             # FeaturePipeline — split, scale, PCA
│   └── reducer.py              # DimensionalityReducer (PCA)
│
├── frontend/                   # React + Vite dashboard
│   ├── src/
│   │   ├── components/         # UI components (charts, tables, cards)
│   │   ├── hooks/              # useExperiment, useDataset
│   │   ├── lib/
│   │   │   ├── adapters.js     # Response shape normalisation
│   │   │   ├── fieldMap.js     # Field name mappings
│   │   │   └── format.js       # Display formatters
│   │   ├── pages/              # Dashboard, Datasets, DatasetDetail,
│   │   │                       # ExperimentNew, ExperimentDetail, Reports
│   │   └── services/api.js     # Single HTTP client (no mock fallback)
│   ├── package.json
│   └── vite.config.js          # Proxy: /api → localhost:8000
│
├── data/
│   └── demo/
│       └── breast_cancer.csv   # 569×32 Wisconsin Diagnostic (clean, no NaN)
│
├── mocks/                      # Contract-shaped JSON fixtures (4 datasets × 9 types)
│   ├── breast_cancer/
│   ├── heart_disease/
│   ├── parkinsons/
│   └── diabetes/
│
├── contracts/                  # Interface contracts (JSON schemas)
├── config.yaml                 # Platform configuration
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Quick Start

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Git | any |

---

### 1 — Clone

```bash
git clone https://github.com/PIYUSH-BHAVSAR/Q-Diagnose.git
cd Q-Diagnose
```

---

### 2 — Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3 — Frontend Setup

```bash
cd frontend
npm install
cd ..
```

---

### 4 — Run (two terminals from repo root)

**Terminal 1 — Backend:**
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

> **Swagger API docs:** http://localhost:8000/docs

---

### 5 — Run Your First Experiment

1. **Upload a dataset** — click *Upload CSV* and drop `data/demo/breast_cancer.csv`
2. **Wait for profiling** — the background profiler runs automatically (~3 seconds)
3. **Design experiment** — click *Design experiment* on the dataset card
4. **Configure** — set PCA components = 4 for a fast run, or 8 for a full benchmark
5. **Click Run** — the executor trains 3 classical models + 1 VQC in the background
6. **Watch the pipeline** — the UI polls status every 2 seconds and fills in results live
7. **View results** — metrics table, bar chart, quantum vs classical recommendation
8. **Generate report** — click *Generate report* for a full 16-section HTML report

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/config` | Platform configuration |
| `POST` | `/api/datasets/upload` | Upload CSV/XLSX/ZIP dataset |
| `GET` | `/api/datasets` | List all datasets |
| `GET` | `/api/datasets/{id}` | Dataset metadata |
| `GET` | `/api/datasets/{id}/profile` | Profiling results (poll until PROFILED) |
| `POST` | `/api/datasets/{id}/validate` | ML pipeline compatibility check |
| `POST` | `/api/experiments` | Create experiment |
| `GET` | `/api/experiments` | List all experiments |
| `GET` | `/api/experiments/{id}` | Experiment manifest |
| `POST` | `/api/experiments/{id}/run` | Start execution (returns 202 immediately) |
| `GET` | `/api/experiments/{id}/status` | Poll progress |
| `GET` | `/api/experiments/{id}/results` | Full model results |
| `GET` | `/api/experiments/{id}/recommendation` | Quantum vs classical verdict |
| `GET` | `/api/experiments/{id}/explanation` | Feature importance + circuit info |
| `POST` | `/api/experiments/{id}/report` | Generate HTML + cost reports |
| `GET` | `/api/experiments/{id}/report` | Download HTML report |
| `POST` | `/api/experiments/{id}/predict` | Live patient inference |
| `POST` | `/api/experiments/{id}/threshold-tune` | Sensitivity/specificity threshold tuning |

---

## Supported Datasets

| Dataset | Rows | Features | Task | Target |
|---|---|---|---|---|
| Breast Cancer Wisconsin | 569 | 30 | Binary classification | `diagnosis` (M/B) |
| Heart Disease UCI | 303 | 13 | Binary classification | `target` (0/1) |
| Pima Indians Diabetes | 768 | 8 | Binary classification | `Outcome` (0/1) |
| Parkinson's Disease | 195 | 22 | Binary classification | `status` (0/1) |

Drop any of these into the upload UI — the adapter registry auto-detects the dataset type and applies the correct preprocessing (e.g. drops the `id` column for breast cancer, uses GroupShuffleSplit for Parkinson's).

---

## Team

| Member | Role |
|---|---|
| Piyush Bhavsar | ML orchestration, experiment executor, API layer |
| Arzaan | Storage layer, data ingestion, config system |
| Shweta | Dataset upload & profiling API |
| Jayed | Feature engineering pipeline, PCA, adapters |
| Radha | Explainability, reports generator |
| Naeem | Frontend dashboard, UI components |

---

## Technical Notes

- **No data leakage** — `StandardScaler` is fit on train split only, then applied to test. PCA likewise.
- **Identical splits** — classical and quantum arms see the exact same rows. The comparison is apples-to-apples.
- **Quantum circuit** — angle encoding maps each PCA component to one qubit rotation. `n_components` = number of qubits. Default = 8.
- **Honest benchmarking** — the recommendation engine requires recall delta > 3pp AND AUC delta > 1pp to declare `QUANTUM_ADVANTAGE`. Anything less is `PERFORMANCE_PARITY` or `CLASSICAL_ADVANTAGE`.
- **Background tasks** — `/run` returns 202 immediately. The executor runs in a FastAPI `BackgroundTask` with its own DB session (not the request session, which closes after the HTTP response).
- **Resilient storage** — all experiment state is written to JSON manifest files on disk. DB is a convenience index; the disk artifacts are the source of truth.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
<sub>Built for Smart India Hackathon 2026 · Problem Statement 3</sub>
</div>
