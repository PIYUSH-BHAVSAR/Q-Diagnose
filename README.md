<div align="center">

<br/>

<img src="https://img.shields.io/badge/SIH_2026-PS_SIH26139-crimson?style=for-the-badge" />
&nbsp;
<img src="https://img.shields.io/badge/Theme-MedTech_%2F_BioTech_%2F_HealthTech-8b5cf6?style=for-the-badge" />
&nbsp;
<img src="https://img.shields.io/badge/Team-QuantWarrior_%C2%B7_IT--01-06b6d4?style=for-the-badge" />

<br/><br/>

# ⚛ Q-Diagnose

### Hybrid Quantum–Classical Machine Learning Platform for Early Disease Detection

<br/>

> **Biomedical Data → Classical + Quantum Intelligence → Evidence-Based Decision**

<br/>

*We don't assume quantum advantage — we measure it.*

<br/>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![PennyLane](https://img.shields.io/badge/PennyLane-QML-7C3AED?style=flat)](https://pennylane.ai)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)

</div>

---

## Who We Are

**Team QuantWarrior · IT-01 · Smart India Hackathon 2026**

Six engineers building at the intersection of quantum computing and medical AI:

| Member | Role |
|---|---|
| Piyush Bhavsar | ML orchestration · experiment executor · API layer |
| Arzaan | Storage layer · data ingestion · config system |
| Shweta | Dataset upload & profiling API |
| Jayed | Feature engineering pipeline · PCA · adapters |
| Radha | Explainability · report generator |
| Naeem | React frontend · UI components · dashboard |

**Problem Statement:** SIH26139 — Hybrid Quantum Machine Learning Platform for Early Disease Detection
**Category:** Software · MedTech / BioTech / HealthTech

---

## The Problem

Biomedical datasets — genomic profiles, clinical indicators, imaging features — are high-dimensional, noisy, and heterogeneous. Classical ML models have achieved real success here, but they hit a ceiling on the most complex feature interactions.

Quantum Machine Learning offers a theoretical path beyond that ceiling through superposition and entanglement. The catch: **no one has demonstrated that it actually helps on real biomedical data in a fair, measurable way.**

Most QML research either:
- Tests on toy datasets with no clinical relevance
- Compares quantum against weak classical baselines
- Reports accuracy without sensitivity, specificity, or cost

**That gap is exactly what Q-Diagnose fills.**

---

## Our Answer

> *Instead of asking "Can quantum detect disease?" — Q-Diagnose answers: **"When is quantum actually worth using?"***

We built a full end-to-end platform that runs classical and quantum models side by side on the same biomedical data, with the same split, the same preprocessing, and the same evaluation criteria — then produces a measured, evidence-based verdict:

| Outcome | Meaning |
|---|---|
| 🟣 **QUANTUM_ADVANTAGE** | QML outperforms on recall + AUC by meaningful margins |
| 🔵 **PERFORMANCE_PARITY** | Equal performance — pick classical for cost |
| 🟠 **TRADEOFF** | Higher recall but higher cost — context-dependent |
| 🔴 **CLASSICAL_ADVANTAGE** | Classical suffices — avoid QML overhead |

The verdict requires **recall delta > 3pp AND AUC delta > 1pp** to declare quantum advantage. Nothing is assumed. Everything is measured.

---

## What It Delivers

Mapped to the 5 PS deliverables:

| Deliverable | What Q-Diagnose Provides |
|---|---|
| **D1 · Data Pre-processing & Feature Engineering** | Ingestion pipeline with format guard, SHA-256 dedup, auto-profiling, NaN imputation, StandardScaler (train-only fit), PCA dimensionality reduction, stratified split |
| **D2 · Hybrid Quantum-Classical Architecture** | FastAPI orchestrator → feature pipeline → classical arm (LR/SVM/RF on full features) + quantum arm (VQC on PCA-reduced features = qubits), identical splits for both arms |
| **D3 · Quantum ML Models** | PennyLane VQC with angle encoding, RealAmplitudes ansatz, COBYLA optimiser on local simulator; QuantumSVM with quantum kernel |
| **D4 · Prediction & Decision Support** | Live patient inference endpoint, probability scoring, risk stratification (LOW / MODERATE / HIGH / CRITICAL), threshold tuning for target sensitivity/specificity |
| **D5 · Software Platform / Prototype** | Full React dashboard — upload, profile, design experiment, live progress polling, metric comparison charts, explainability view, HTML report download |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        React Frontend  ·  port 5173                      │
│                                                                           │
│   Datasets ──► Profile ──► Design Experiment ──► Run ──► Results         │
│                                      ↑  polls /status every 2s           │
└────────────────────────┬────────────────────────────────────────────────┘
                         │  /api/*  via Vite proxy
┌────────────────────────▼────────────────────────────────────────────────┐
│                       FastAPI Backend  ·  port 8000                      │
│                                                                           │
│  POST /api/datasets/upload          GET  /api/datasets/{id}/profile      │
│  POST /api/experiments              POST /api/experiments/{id}/run       │
│  GET  /api/experiments/{id}/status  GET  /api/experiments/{id}/results   │
│  GET  /api/experiments/{id}/recommendation  /explanation  /report        │
│  POST /api/experiments/{id}/predict  /threshold-tune                     │
│  GET  /api/demo/{name}              ← serve bundled demo CSVs            │
└──────┬──────────────────────────────────────────┬───────────────────────┘
       │                                          │
┌──────▼──────────────┐                ┌──────────▼────────────────────────┐
│   Feature Pipeline  │                │      Experiment Executor           │
│                     │                │   (BackgroundTask — non-blocking)  │
│  1. Drop NaN cols   │                │                                    │
│  2. Drop id cols    │                │  CREATED → VALIDATING              │
│  3. Impute NaN      │                │  → PREPROCESSING                   │
│  4. Encode target   │                │  → RUNNING_CLASSICAL               │
│  5. StandardScaler  │◄───────────────│  → RUNNING_QUANTUM                 │
│     (train-fit only)│                │  → BENCHMARKING                    │
│  6. PCA → n_qubits  │                │  → COMPLETED / FAILED              │
│  7. 80/20 stratified│                │                                    │
└──────┬──────────────┘                └──────────┬────────────────────────┘
       │                                          │
┌──────▼──────────────┐                ┌──────────▼────────────────────────┐
│   Classical Arm     │                │        Quantum Arm (PennyLane)     │
│                     │                │                                    │
│  LogisticRegression │                │  Angle encoding → qubit register   │
│  SVM  (RBF kernel)  │                │  RealAmplitudes ansatz             │
│  Random Forest      │                │  COBYLA optimiser                  │
│                     │                │  default.qubit local simulator     │
│  Trains on X_train  │                │  Trains on X_train_reduced         │
│  (full features)    │                │  (PCA → n_components == n_qubits)  │
└──────┬──────────────┘                └──────────┬────────────────────────┘
       └────────────────────┬───────────────────── ┘
                   ┌────────▼────────┐
                   │  Benchmarking   │
                   │                 │
                   │  Accuracy       │
                   │  Precision      │
                   │  Recall         │
                   │  F1-Score       │
                   │  ROC-AUC        │
                   │  Specificity    │
                   │  PR-AUC         │
                   └────────┬────────┘
                   ┌────────▼────────┐
                   │  Recommendation │
                   │                 │
                   │  QUANTUM_       │
                   │   ADVANTAGE     │
                   │  PERFORMANCE_   │
                   │   PARITY        │
                   │  TRADEOFF       │
                   │  CLASSICAL_     │
                   │   ADVANTAGE     │
                   └─────────────────┘
```

---

## The 15-Phase Pipeline

```
Phase 01–03  ·  DATA FOUNDATION
  01  Ingest & Register      Upload CSV, validate format, SHA-256 dedupe, store
  02  Profile                Auto-detect target, task type, class distribution
  03  Validate               Quality gates — missing values, row count, task type

Phase 04–06  ·  REPRESENTATION
  04  Preprocess             Impute NaN, encode categoricals, handle identifiers
  05  Feature Engineering    StandardScaler (train-fit), class weight computation
  06  Dimensionality Reduce  PCA → n_components (= number of qubits)

Phase 07–08  ·  MODEL BRANCHES
  07  Classical Models       LR, SVM (RBF), Random Forest on full feature matrix
  08  Quantum Models         VQC (angle encoding + RealAmplitudes) on PCA matrix

Phase 09–10  ·  EXPERIMENT
  09  Planner                Rule-based plan — split, scaler, qubit budget
  10  Executor               Orchestrate both arms, track progress, store artifacts

Phase 11     ·  BENCHMARK
  11  Comparison             Same split, same data, 7 metrics per model

Phase 12     ·  EXPLAINABILITY
  12  XAI                    Gini importance (classical), circuit structure (quantum)

Phase 13     ·  RESOURCE ANALYSIS
  13  Cost & Resources       Qubits, circuit depth, gate count, runtime, memory

Phase 14–15  ·  DECIDE & REPORT
  14  Recommendation         Evidence-based verdict (4 possible outcomes)
  15  Report                 16-section HTML report + JSON cost report
```

---

## Repository Structure

```
Q-Diagnose/
│
├── backend/                    ← FastAPI application
│   ├── api/                    ← HTTP route handlers
│   │   ├── datasets.py         ← upload, profile, validate
│   │   └── experiments.py      ← create, run, status, results, report
│   ├── benchmarking/           ← MetricsCalculator, ModelComparison, RecommendationEngine
│   ├── core/                   ← config loader, exceptions, logging
│   ├── data/                   ← DatasetIngestionService, adapters
│   ├── experiments/            ← ExperimentExecutor, ExperimentManager
│   ├── explainability/         ← classical (Gini), quantum (circuit info)
│   ├── models/
│   │   ├── classical/          ← LR, SVM, RandomForest wrappers
│   │   └── quantum/            ← VQC, QuantumSVM, circuit, encoding
│   ├── planner/                ← ExperimentPlanner, rule engine
│   ├── reports/                ← 16-section HTML + cost JSON generator
│   ├── storage/                ← SQLAlchemy ORM, repositories, file storage
│   └── main.py                 ← FastAPI app entry point + demo endpoints
│
├── features/                   ← Standalone feature engineering pipeline
│   ├── pipeline.py             ← FeaturePipeline (split, scale, PCA)
│   └── reducer.py              ← DimensionalityReducer
│
├── frontend/                   ← React 18 + Vite dashboard
│   ├── src/
│   │   ├── components/         ← 14 UI components (charts, tables, cards)
│   │   ├── hooks/              ← useExperiment (polling), useDataset
│   │   ├── lib/                ← adapters.js, format.js, fieldMap.js
│   │   ├── pages/              ← Dashboard, Datasets, DatasetDetail,
│   │   │                          ExperimentNew, ExperimentDetail, Reports
│   │   └── services/api.js     ← single HTTP client, pure live mode
│   ├── package.json
│   └── vite.config.js          ← proxy /api → localhost:8000
│
├── data/
│   └── demo/
│       └── breast_cancer.csv   ← 569×32, zero NaN, ready to run
│
├── datasets/                   ← Raw source datasets (4 biomedical)
│   ├── Breast Cancer Wisconsin Diagnostic/
│   ├── Heart Disease UCI/
│   ├── Parkinson's Disease/
│   └── Pima Indians Diabetes/
│
├── fixtures/                   ← Clean CSVs for testing (4 datasets)
├── mocks/                      ← Contract-shaped JSON fixtures
├── contracts/                  ← Interface contract JSON schemas
├── docs/                       ← Architecture docs (15 phases + 6 guides)
│   ├── phase1.md … phase15.md
│   ├── guide_arzaan.md … guide_shweta.md
│   ├── phases.md
│   └── ISSUES.md
│
├── config.yaml                 ← Platform configuration
├── requirements.txt            ← Python dependencies
├── README.md                   ← You are here
└── SETUP.md                    ← Quick start guide
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Language | Python 3.11 |
| Backend framework | FastAPI + Uvicorn |
| Classical ML | scikit-learn (LR, SVM, RandomForest) |
| Quantum ML | PennyLane (VQC), Qiskit (backend abstraction) |
| Feature engineering | NumPy, pandas, scikit-learn PCA + StandardScaler |
| Explainability | Gini importance + quantum circuit structure analysis |
| Database | SQLite via SQLAlchemy ORM |
| Frontend | React 18, Vite, Chart.js, Lucide icons |
| Configuration | YAML + Pydantic dataclasses |
| Deployment path | Local simulator → Cloud simulator → NISQ hardware |

---

## Supported Datasets

| Dataset | Rows | Features | Target | Source |
|---|---|---|---|---|
| Breast Cancer Wisconsin | 569 | 30 | `diagnosis` (M/B) | UCI ML Repository |
| Heart Disease Cleveland | 303 | 13 | `target` (0/1) | UCI ML Repository |
| Pima Indians Diabetes | 768 | 8 | `Outcome` (0/1) | UCI ML Repository |
| Parkinson's Disease | 195 | 22 | `status` (0/1) | UCI ML Repository |

---

## Quick Start

### 1 — Clone

```bash
git clone https://github.com/PIYUSH-BHAVSAR/Q-Diagnose.git
cd Q-Diagnose
```

### 2 — Backend

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3 — Frontend

```bash
cd frontend
npm install
cd ..
```

### 4 — Run

**Terminal 1 — Backend** (from repo root):
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend** (from repo root):
```bash
cd frontend
npm run dev
```

**Terminal 3 — Public URL via ngrok** (optional):
```bash
ngrok http 5173
```

Open **http://localhost:5173** · API docs at **http://localhost:8000/docs**

### 5 — First run in 30 seconds

1. Go to **Datasets** → click **Try demo** — breast cancer CSV uploads automatically
2. Wait ~3s for profiling → click **Design experiment**
3. Set PCA components = 4, `dev_mode = true`, `quantum_enabled = false` for a fast first run
4. Click **Run benchmark** → watch the live pipeline stepper
5. Results, comparison chart and recommendation appear when complete
6. Click **Generate report** for the full 16-section HTML report

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/config` | Platform configuration |
| `GET` | `/api/demo/{name}` | Download bundled demo CSV |
| `POST` | `/api/datasets/upload` | Upload CSV / XLSX / ZIP |
| `GET` | `/api/datasets` | List all datasets |
| `GET` | `/api/datasets/{id}/profile` | Dataset profiling results |
| `POST` | `/api/datasets/{id}/validate` | ML pipeline compatibility check |
| `POST` | `/api/experiments` | Create experiment |
| `POST` | `/api/experiments/{id}/run` | Start execution (returns 202 immediately) |
| `GET` | `/api/experiments/{id}/status` | Poll live progress |
| `GET` | `/api/experiments/{id}/results` | Full model results |
| `GET` | `/api/experiments/{id}/recommendation` | Quantum vs classical verdict |
| `GET` | `/api/experiments/{id}/explanation` | Feature importance + circuit info |
| `POST` | `/api/experiments/{id}/report` | Generate HTML + cost reports |
| `GET` | `/api/experiments/{id}/report` | Download HTML report |
| `POST` | `/api/experiments/{id}/predict` | Live patient inference |
| `POST` | `/api/experiments/{id}/threshold-tune` | Sensitivity/specificity tuning |

---

## Key Design Decisions

**No data leakage** — `StandardScaler` and PCA are fit on the train split only, then applied to the test split. The test set never influences any fitted parameter.

**Identical arms** — classical and quantum models train on the exact same 80/20 stratified split. The comparison is apples-to-apples.

**Classical on full features, quantum on reduced** — PCA reduction maps the feature space to the qubit budget. Classical models get the full feature matrix; the reduction is specific to the quantum arm.

**Background tasks own their DB session** — the HTTP request session closes after the response. Background tasks open a fresh `SessionLocal()` and close it in a `finally` block.

**Disk is source of truth** — all experiment state is written as JSON manifest files. The SQLite DB is a convenience index that can be rebuilt from disk.

**Honest benchmarking** — the recommendation engine requires recall delta > 3pp AND AUC delta > 1pp to declare `QUANTUM_ADVANTAGE`. Marginal differences land in `PERFORMANCE_PARITY`.

---

## Academic Foundations

| Paper | Relevance |
|---|---|
| Farhi & Neven (2018) — *Classification with Quantum Neural Networks on Near Term Processors* | VQC foundation |
| Havlíček et al. (2019), Nature — *Supervised Learning with Quantum Enhanced Feature Spaces* | Quantum kernel / QSVM |
| Cerezo et al. (2021), Nature Rev. Phys. — *Variational Quantum Algorithms* | Hybrid QML architecture |
| Preskill (2018) — *Quantum Computing in the NISQ Era and Beyond* | Resource constraint framing |
| Lundberg & Lee (2017), NeurIPS — *A Unified Approach to Interpreting Model Predictions* | SHAP explainability |
| Steyerberg et al. (2010) — *Assessing the Performance of Prediction Models* | Sensitivity, specificity, ROC-AUC evaluation |

---

## Current Status (SIH 2026)

- ✅ 4 biomedical datasets ingested and validated
- ✅ End-to-end pipeline operational (classical arm)
- ✅ VQC quantum arm on local PennyLane simulator
- ✅ Live experiment dashboard with 2-second polling
- ✅ Explainability module (feature importance + circuit info)
- ✅ 16-section HTML report generator
- ✅ Risk stratification + threshold tuning endpoints
- ✅ Demo CSV one-click upload from the UI
- 🔄 Cloud quantum simulator backend (path ready)
- 🔄 NISQ hardware deployment (architecture supports it)

---

## Docs

All architecture and implementation docs are in [`docs/`](docs/):

- [`docs/phases.md`](docs/phases.md) — full 15-phase overview
- [`docs/phase1.md`](docs/phase1.md) … [`docs/phase15.md`](docs/phase15.md) — per-phase specs
- [`docs/guide_piyush.md`](docs/guide_piyush.md) — ML orchestration guide
- [`docs/guide_arzaan.md`](docs/guide_arzaan.md) — storage & ingestion guide
- [`docs/guide_jayed.md`](docs/guide_jayed.md) — feature pipeline guide
- [`docs/guide_shweta.md`](docs/guide_shweta.md) — datasets API guide
- [`docs/guide_radha.md`](docs/guide_radha.md) — explainability & reports guide
- [`docs/guide_naeem.md`](docs/guide_naeem.md) — frontend guide

---

<div align="center">

**QuantWarrior · IT-01 · SIH 2026 · PS SIH26139**

*Hybrid Quantum–Classical Platform for Early Disease Detection*

</div>
