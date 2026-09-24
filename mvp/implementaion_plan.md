# QUANT WARRIORS

# Hybrid Quantum Machine Learning Disease Detection Platform

## Complete Local MVP Implementation Plan

---

# 1. Project Objective

Build a fully working local MVP of the SIH Problem Statement:

> **Hybrid Quantum Machine Learning Platform for Early Disease Detection**

The MVP will initially support **CSV-based biomedical tabular datasets**.

The first supported datasets are:

1. Breast Cancer Wisconsin Diagnostic — primary demonstration dataset
2. Heart Disease UCI — second demonstration dataset
3. Parkinson's Disease — third demonstration dataset

The system must not be a collection of disconnected notebooks.

It must behave like a single platform:

```text
CSV Upload
    ↓
Dataset Understanding
    ↓
Dataset Validation
    ↓
Automatic Task Detection
    ↓
Preprocessing
    ↓
Feature Engineering
    ↓
Dimensionality Reduction
    ↓
Experiment Planning
    ↓
Classical Models
       +
Quantum Model
    ↓
Controlled Evaluation
    ↓
Model Comparison
    ↓
Explainability
    ↓
Resource / Cost Analysis
    ↓
Final Recommendation
    ↓
Experiment Report
```

---

# 2. MVP Philosophy

The MVP should prove one important idea:

> **The platform does not assume quantum ML is better. It experimentally determines whether the quantum approach provides a useful trade-off against classical ML.**

Therefore, every quantum experiment must have a corresponding classical baseline.

The system should be capable of producing any of these conclusions:

```text
QUANTUM ADVANTAGE
```

or

```text
QUANTUM PERFORMANCE PARITY
```

or

```text
CLASSICAL MODEL PREFERRED
```

or

```text
INCONCLUSIVE / INSUFFICIENT EVIDENCE
```

The system must never fabricate or force a quantum advantage.

---

# 3. MVP Scope

## Included

```text
✓ CSV upload
✓ CSV parsing
✓ Dataset profiling
✓ Dataset validation
✓ Target detection
✓ Binary classification detection
✓ Numerical feature detection
✓ Missing-value analysis
✓ Duplicate analysis
✓ Class imbalance analysis
✓ Train/test split
✓ Scaling
✓ Feature selection/reduction
✓ PCA
✓ Classical ML
✓ VQC
✓ Local quantum simulation
✓ Experiment planning
✓ Experiment execution
✓ Metrics
✓ Classical vs quantum comparison
✓ Basic explainability
✓ Resource monitoring
✓ Runtime measurement
✓ Quantum resource measurement
✓ Final recommendation
✓ Experiment history
✓ Results visualization
✓ Local report generation
```

---

# 4. Explicitly Out of Scope for MVP

Do NOT implement these before the core pipeline works:

```text
✗ Medical image pipeline
✗ Genomics pipeline
✗ EHR pipeline
✗ Real quantum hardware
✗ Cloud quantum execution
✗ LLM agent
✗ Autonomous unrestricted model selection
✗ Multi-user authentication
✗ Kubernetes
✗ Microservice deployment
✗ Production cloud deployment
✗ Complex distributed training
✗ Dozens of QML algorithms
```

These belong to the future/full platform.

---

# 5. MVP Technical Stack

Use a simple local architecture.

## Frontend

Recommended:

```text
React
+
Vite
```

UI libraries can be added only if they speed up development.

---

## Backend

```text
Python
FastAPI
```

FastAPI handles:

```text
CSV upload
dataset analysis
experiment creation
experiment execution
status
results
reports
```

---

## Machine Learning

```text
Python
pandas
numpy
scikit-learn
```

---

## Quantum ML

Use one quantum framework consistently.

Recommended:

```text
PennyLane
```

Primary model:

```text
Variational Quantum Classifier
(VQC)
```

The quantum backend initially runs locally using a simulator.

---

## Explainability

For classical models:

```text
SHAP
```

If SHAP integration becomes a time problem, implement permutation/feature importance first and add SHAP after the core pipeline works.

---

## Visualization

Frontend:

```text
Chart.js
```

or another lightweight charting library.

---

## Storage

For the MVP:

```text
SQLite
```

plus local filesystem storage for:

```text
datasets
experiment artifacts
models
reports
```

No database server is necessary.

---

# 6. High-Level Architecture

```text
                    USER
                     │
                     ▼
              ┌──────────────┐
              │   FRONTEND   │
              │    React     │
              └──────┬───────┘
                     │ HTTP
                     ▼
              ┌──────────────┐
              │   FASTAPI    │
              │   BACKEND    │
              └──────┬───────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
   DATA ENGINE   EXPERIMENT    STORAGE
                    ENGINE
       │             │
       │       ┌─────┴─────┐
       │       │           │
       ▼       ▼           ▼
   PROFILER  CLASSICAL   QUANTUM
   VALIDATOR  ENGINE      ENGINE
   PREPROCESS
       │          │          │
       └──────────┴──────────┘
                  │
                  ▼
           BENCHMARK ENGINE
                  │
                  ▼
        EXPLAINABILITY ENGINE
                  │
                  ▼
          RESOURCE MONITOR
                  │
                  ▼
            REPORT ENGINE
```

---

# 7. Recommended Repository Structure

Create the project like this:

```text
quant-warriors-qml/
│
├── README.md
├── MVP_IMPLEMENTATION_PLAN.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── backend/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── datasets.py
│   │   ├── experiments.py
│   │   ├── results.py
│   │   └── reports.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── data/
│   │   ├── loader.py
│   │   ├── profiler.py
│   │   ├── validator.py
│   │   ├── adapters.py
│   │   └── preprocessing.py
│   │
│   ├── features/
│   │   ├── selector.py
│   │   ├── reducer.py
│   │   └── pipeline.py
│   │
│   ├── models/
│   │   ├── registry.py
│   │   │
│   │   ├── classical/
│   │   │   ├── logistic_regression.py
│   │   │   ├── svm.py
│   │   │   └── random_forest.py
│   │   │
│   │   └── quantum/
│   │       ├── encoding.py
│   │       ├── circuit.py
│   │       ├── vqc.py
│   │       └── backend.py
│   │
│   ├── planner/
│   │   ├── rules.py
│   │   └── experiment_planner.py
│   │
│   ├── experiments/
│   │   ├── manager.py
│   │   ├── executor.py
│   │   └── tracker.py
│   │
│   ├── benchmarking/
│   │   ├── metrics.py
│   │   ├── comparison.py
│   │   └── recommendation.py
│   │
│   ├── explainability/
│   │   ├── classical.py
│   │   └── quantum.py
│   │
│   ├── resources/
│   │   └── monitor.py
│   │
│   ├── reports/
│   │   └── generator.py
│   │
│   └── storage/
│       ├── database.py
│       ├── models.py
│       └── files.py
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── App.jsx
│   │
│   └── package.json
│
├── data/
│   ├── demo/
│   │   ├── breast_cancer.csv
│   │   ├── heart_disease.csv
│   │   └── parkinsons.csv
│   │
│   └── uploads/
│
├── artifacts/
│   ├── experiments/
│   ├── models/
│   └── reports/
│
└── tests/
    ├── test_profiler.py
    ├── test_validator.py
    ├── test_preprocessing.py
    ├── test_features.py
    ├── test_classical.py
    ├── test_quantum.py
    ├── test_benchmark.py
    └── test_end_to_end.py
```

---

# 8. PHASE 0 — Environment Setup

## Goal

Get the local environment running before writing application logic.

Install:

```text
Python
FastAPI
Uvicorn
pandas
numpy
scikit-learn
PennyLane
SHAP
psutil
joblib
SQLAlchemy
Pydantic
```

Frontend:

```text
Node.js
React
Vite
```

---

## Verify

Run:

```text
python --version
```

Then test:

```python
import pandas
import sklearn
import pennylane
import fastapi
import shap
```

The quantum simulator must execute a tiny circuit before continuing.

---

# 9. PHASE 1 — Dataset Ingestion

## Input

User uploads:

```text
.csv
```

Example:

```text
breast_cancer.csv
```

---

## Backend responsibility

Endpoint:

```text
POST /datasets/upload
```

Process:

```text
Receive file
   ↓
Check extension
   ↓
Check file size
   ↓
Save file
   ↓
Generate dataset ID
   ↓
Load with pandas
   ↓
Start profiling
```

---

## Output

```json
{
  "dataset_id": "DS-000001",
  "filename": "breast_cancer.csv",
  "status": "uploaded"
}
```

---

# 10. PHASE 2 — Dataset Profiling

This is the first major visible feature.

After upload, the system should automatically inspect the CSV.

## Calculate

```text
number of rows
number of columns
column names
data types
missing values
unique values
duplicate rows
numerical columns
categorical columns
possible target columns
class distribution
```

---

## Example UI

```text
DATASET PROFILE

Dataset
Breast Cancer Wisconsin

Rows
569

Columns
32

Numerical features
30

Categorical columns
1

Missing values
0

Duplicates
0

Possible target
diagnosis

Classes
B / M
```

---

# 11. Dataset Profiling Must Use the Actual Files

Do NOT hardcode:

```text
569 rows
30 features
```

into the platform.

The profiler must calculate it from the uploaded CSV.

This is essential because the platform should appear generic.

---

# 12. PHASE 3 — Dataset Validation

The validator checks whether the dataset can actually be processed.

Checks:

```text
✓ CSV readable
✓ At least one row
✓ Target exists
✓ Target has valid classes
✓ Features contain usable data
✓ No completely empty columns
✓ No invalid infinite values
✓ Numeric conversion possible where expected
```

---

## Validation result

```text
DATASET VALIDATION

✓ File readable
✓ Target detected
✓ Binary classification
✓ Numerical features available
✓ Missing values handled
✓ Suitable for MVP pipeline

STATUS: READY
```

---

# 13. PHASE 4 — Target Detection

The system needs to know:

> Which column is the thing we are predicting?

For known demo datasets, adapters can define the target explicitly.

For generic uploads:

```text
Target candidate detection
```

can inspect:

```text
column name
unique count
data type
position
```

If confidence is low:

```text
Target column unclear.

Please select target:
[ dropdown ]
```

For MVP, user selection is acceptable.

---

# 14. Dataset Adapters

Create:

```text
BreastCancerAdapter
HeartDiseaseAdapter
ParkinsonsAdapter
```

Adapters handle dataset-specific issues.

Example:

```text
Breast Cancer
target = diagnosis
drop = id
```

Heart Disease:

```text
target = target / num
```

depending on the exact downloaded file schema.

Parkinson's:

```text
target = status
subject/group column = subject identifier
```

The adapter must be based on the **actual CSV schema we receive**, not assumptions.

---

# 15. PHASE 5 — Data Cleaning

Pipeline:

```text
Raw CSV
   ↓
Remove invalid rows/columns
   ↓
Handle missing values
   ↓
Encode categorical variables
   ↓
Separate X / y
```

Output:

```text
X
y
metadata
```

---

# 16. Avoid Data Leakage

This is critical.

Never perform:

```text
PCA on complete dataset
```

before train/test splitting.

Correct:

```text
Raw data
 ↓
Train/Test split
 ↓
Fit scaler on TRAIN only
 ↓
Transform train
Transform test
 ↓
Fit PCA on TRAIN only
 ↓
Transform train
Transform test
```

This must be enforced in the code.

Use scikit-learn pipelines where possible.

---

# 17. PHASE 6 — Train/Test Strategy

Default:

```text
80% train
20% test
```

with:

```text
stratification
```

for ordinary binary datasets.

Example:

```text
Train: 80%
Test: 20%
random_state = 42
```

For Parkinson's, because multiple recordings can belong to the same subject, use a **group-aware split** if the downloaded dataset contains a subject identifier.

The platform should display:

```text
Evaluation Strategy

Stratified split
```

or:

```text
Group-aware split
```

---

# 18. PHASE 7 — Preprocessing

For numerical features:

```text
StandardScaler
```

Pipeline:

```text
X
 ↓
Imputation if required
 ↓
Scaling
```

Categorical features:

```text
OneHotEncoder
```

if needed.

The output must be numerical.

---

# 19. PHASE 8 — Feature Selection / Reduction

This is where the classical-to-quantum bridge happens.

The quantum circuit cannot efficiently accept dozens/hundreds/thousands of raw features.

Therefore:

```text
Original features
       ↓
Feature selection/reduction
       ↓
Compact representation
       ↓
Quantum encoding
```

---

# 20. PCA Strategy

For MVP:

```text
PCA → 4 or 8 components
```

The exact value should depend on:

```text
dataset dimension
available quantum simulation budget
configured max qubits
```

For example:

```text
30 features
    ↓
PCA
    ↓
8 components
    ↓
8 qubits
```

---

# 21. Important: PCA Must Be Configurable

Configuration:

```yaml
quantum:
  max_qubits: 8

feature_reduction:
  candidate_dimensions:
    - 4
    - 8
```

The system can decide:

```text
4 features
OR
8 features
```

based on feasibility.

---

# 22. PHASE 9 — Experiment Planner

This is where our "intelligent" behavior starts.

For MVP, use a **rule-based planner**.

Not an LLM.

---

# 23. Planner Input

The planner receives:

```json
{
  "task": "binary_classification",
  "samples": 569,
  "features": 30,
  "numerical_features": 30,
  "class_count": 2,
  "imbalance": "low",
  "max_qubits": 8
}
```

---

# 24. Planner Rules

Example:

```text
IF binary classification
    → classification experiment

IF numerical features > quantum dimensions
    → dimensionality reduction

IF reduced dimensions <= max_qubits
    → quantum model allowed

IF class imbalance is high
    → prioritize recall, F1 and PR-AUC

IF sample count is small
    → use stratified evaluation

IF dataset has repeated subjects
    → use group-aware split
```

---

# 25. Planner Output

Example:

```json
{
  "task": "binary_classification",

  "preprocessing": [
    "standard_scaling"
  ],

  "reduction": {
    "method": "PCA",
    "components": 8
  },

  "classical_models": [
    "logistic_regression",
    "svm",
    "random_forest"
  ],

  "quantum_models": [
    "vqc"
  ],

  "evaluation": {
    "split": "stratified",
    "test_size": 0.2,
    "random_state": 42
  }
}
```

---

# 26. Show the Plan to the User

This should be one of the strongest UI screens.

```text
SYSTEM-GENERATED EXPERIMENT PLAN

Task
Binary Classification

Input
30 numerical features

Representation
Standardization
        ↓
PCA
        ↓
8 dimensions

Classical
✓ Logistic Regression
✓ SVM
✓ Random Forest

Quantum
✓ VQC

Evaluation
80/20 stratified split

Quantum backend
Local simulator
```

---

# 27. PHASE 10 — Classical Model Engine

Implement three models first.

## Model 1

```text
Logistic Regression
```

## Model 2

```text
SVM
```

## Model 3

```text
Random Forest
```

---

# 28. Important Benchmark Rule

For fairness, classical and quantum models should operate on the same processed representation whenever possible.

For example:

```text
Dataset
 ↓
Train/Test split
 ↓
Scaling
 ↓
PCA → 8 features
 ↓
 ┌───────────────┬───────────────┐
 ↓               ↓
Classical        Quantum
```

This lets us compare the learning models rather than comparing completely different feature pipelines.

---

# 29. PHASE 11 — Quantum Model

Implement:

```text
VQC
```

first.

Architecture:

```text
8 classical features
       ↓
Angle Encoding
       ↓
8 qubits
       ↓
Variational layers
       ↓
Measurement
       ↓
Binary prediction
```

---

# 30. Quantum Circuit

Basic structure:

```text
Input features
      ↓
RY rotations
      ↓
Entangling gates
      ↓
RY/RZ trainable rotations
      ↓
Entanglement
      ↓
Measurement
```

The circuit depth should be configurable.

Example:

```yaml
quantum:
  qubits: 8
  layers: 2
  shots: 1024
```

For the first MVP, start smaller if runtime is too high.

---

# 31. Quantum Backend Abstraction

Create:

```text
QuantumBackend
```

Even though we only use a local simulator now.

Interface:

```python
class QuantumBackend:

    def execute(self, circuit, params):
        ...

    def get_device_info(self):
        ...

    def get_resource_info(self):
        ...
```

Current:

```text
QuantumBackend
      ↓
Local Simulator
```

Future:

```text
QuantumBackend
      ↓
Cloud Simulator
```

or:

```text
QuantumBackend
      ↓
Real Quantum Hardware
```

This satisfies our future scalability architecture without requiring hardware tomorrow.

---

# 32. PHASE 12 — Experiment Manager

Every run gets an ID.

Example:

```text
EXP-000001
```

Store:

```text
dataset
configuration
models
seed
preprocessing
feature reduction
quantum configuration
backend
start time
end time
status
```

---

# 33. Experiment States

```text
CREATED
   ↓
VALIDATING
   ↓
PREPROCESSING
   ↓
RUNNING_CLASSICAL
   ↓
RUNNING_QUANTUM
   ↓
BENCHMARKING
   ↓
EXPLAINING
   ↓
COMPLETED
```

Failure:

```text
FAILED
```

---

# 34. PHASE 13 — Execution Progress

The UI must show actual stages.

Example:

```text
EXPERIMENT EXP-000001

✓ Dataset validation
✓ Train/test preparation
✓ Feature scaling
✓ PCA reduction

✓ Logistic Regression
✓ SVM
✓ Random Forest

● VQC
  Training...
  
○ Benchmark
○ Explainability
○ Report
```

This gives the user the "complete experience" you asked for.

---

# 35. PHASE 14 — Metrics

For disease detection, don't show only accuracy.

Calculate:

```text
Accuracy
Precision
Recall / Sensitivity
Specificity
F1
ROC-AUC
Confusion Matrix
```

If appropriate:

```text
PR-AUC
```

---

# 36. Why Recall Matters

For disease screening, missing positive cases can be particularly important.

Therefore the platform should highlight:

```text
Recall / Sensitivity
```

along with:

```text
Specificity
```

instead of treating accuracy as the only metric.

---

# 37. PHASE 15 — Classical vs Quantum Benchmark

Create one normalized result structure.

Example:

```json
{
  "model": "VQC",
  "type": "quantum",

  "metrics": {
    "accuracy": 0.91,
    "precision": 0.90,
    "recall": 0.93,
    "specificity": 0.89,
    "f1": 0.91,
    "roc_auc": 0.94
  },

  "runtime": {
    "training_seconds": 42.3,
    "inference_seconds": 0.8
  },

  "quantum_resources": {
    "qubits": 8,
    "layers": 2,
    "shots": 1024
  }
}
```

Classical results use the same top-level structure.

---

# 38. Results Dashboard

Main comparison:

```text
MODEL COMPARISON

┌─────────────────────────────────────────────┐
│ Model          Type        Accuracy         │
├─────────────────────────────────────────────┤
│ Logistic Reg   Classical    XX.X%           │
│ SVM            Classical    XX.X%           │
│ Random Forest  Classical    XX.X%           │
│ VQC            Quantum      XX.X%           │
└─────────────────────────────────────────────┘
```

Additional tabs:

```text
Performance
Recall
Specificity
AUC
Runtime
Resources
```

---

# 39. PHASE 16 — Confusion Matrix

For every model:

```text
              Actual
             0      1

Predicted 0  TN     FN

Predicted 1  FP     TP
```

Display it visually.

The user can select:

```text
Logistic Regression
SVM
Random Forest
VQC
```

and inspect the confusion matrix.

---

# 40. PHASE 17 — Explainability

For classical models:

```text
SHAP
```

or feature importance.

Show:

```text
WHY DID THE MODEL PREDICT THIS?

Feature 1     █████████
Feature 2     ███████
Feature 3     █████
Feature 4     ███
```

---

# 41. Quantum Explainability

For MVP, don't claim that the circuit itself is fully medically interpretable.

Instead show:

```text
QUANTUM MODEL EXPLANATION

Input representation
        ↓
PCA Feature 1
PCA Feature 2
...
PCA Feature 8
        ↓
Angle Encoding
        ↓
Quantum Circuit
        ↓
Measurement
        ↓
Prediction
```

Also show the circuit diagram.

This is an **execution explanation**, not a clinical causal explanation.

---

# 42. PHASE 18 — Resource Monitoring

Measure actual runtime.

Use:

```text
time.perf_counter()
```

for:

```text
training time
inference time
preprocessing time
```

Use:

```text
psutil
```

for:

```text
RAM
CPU
```

---

# 43. Quantum Resource Metrics

Record:

```text
number of qubits
number of variational layers
shots
circuit executions
circuit depth
simulation runtime
```

Example:

```text
QUANTUM RESOURCES

Qubits              8
Variational layers  2
Shots               1024
Circuit executions  8,240
Runtime             41.8 sec
Backend             Local Simulator
```

---

# 44. PHASE 19 — Cost Analysis

For local execution, don't invent a monetary cloud cost.

Show:

```text
Execution Mode
LOCAL

External Quantum Cost
None

Measured Compute
CPU time
RAM
Quantum simulation runtime
```

Later, cloud backends can calculate actual provider costs.

---

# 45. Cost/Performance Visualization

Create:

```text
Performance vs Runtime
```

For example:

```text
              Performance
                   ↑
                   │       VQC
                   │
                   │
                   │
                   │ RF
                   │
                   └────────────────→ Runtime
```

The actual positions must come from measured results.

---

# 46. PHASE 20 — Final Recommendation Engine

This is the platform's key output.

The system evaluates:

```text
predictive performance
+
recall
+
specificity
+
AUC
+
runtime
+
resource consumption
```

---

# 47. Recommendation Logic

Example:

```text
IF quantum improves key metric
AND improvement is statistically/experimentally meaningful
AND resource cost is acceptable
    → "Promising Quantum Benefit"

IF quantum and classical are approximately equivalent
    → "Performance Parity"

IF classical performs better
OR quantum cost is disproportionately high
    → "Classical Model Preferred"
```

Do not use arbitrary thresholds without documenting them.

For MVP, recommendation rules should be transparent.

---

# 48. Example Final Output

```text
FINAL SYSTEM ASSESSMENT

Quantum model:
VQC

Best classical model:
Random Forest

Performance:
Quantum shows higher recall.

Cost:
Quantum simulation requires significantly
more runtime.

Assessment:
PROMISING FOR RECALL,
BUT WITH A COMPUTATIONAL TRADE-OFF.
```

Or, based on actual results:

```text
CLASSICAL MODEL PREFERRED

Reason:
Classical model achieved comparable or better
predictive performance with substantially lower
computational cost.
```

---

# 49. PHASE 21 — Experiment History

Create:

```text
Experiments
```

page.

Example:

```text
EXP-000001
Breast Cancer
VQC vs Classical
Completed

EXP-000002
Heart Disease
VQC vs Classical
Completed

EXP-000003
Parkinson's
VQC vs Classical
Failed
```

Clicking an experiment opens its complete results.

---

# 50. PHASE 22 — Experiment Detail Page

Show:

```text
Experiment ID

Dataset
Task
Dataset size

Preprocessing
Feature reduction

Classical models
Quantum models

Quantum backend

Evaluation protocol

Results

Explainability

Resources

Recommendation
```

---

# 51. PHASE 23 — Report Generation

Generate a local HTML or PDF report.

Structure:

```text
QUANT WARRIORS
Hybrid QML Experiment Report

1. Executive Summary

2. Dataset Profile

3. Data Quality

4. Preprocessing

5. Feature Reduction

6. Experiment Plan

7. Classical Models

8. Quantum Model

9. Evaluation Method

10. Results

11. Quantum vs Classical

12. Explainability

13. Resource Usage

14. Cost Analysis

15. Final Recommendation

16. Limitations
```

---

# 52. PHASE 24 — Frontend Pages

The frontend should have approximately these pages.

```text
/
Dashboard

/datasets
Datasets

/datasets/:id
Dataset Details

/experiments
Experiment History

/experiments/new
Create Experiment

/experiments/:id
Experiment Execution / Results

/reports
Reports
```

Don't create dozens of unnecessary pages.

---

# 53. Dashboard

Home screen:

```text
QUANT WARRIORS

Hybrid Quantum Disease Detection

Datasets
3

Experiments
12

Completed
10

Running
1

Failed
1
```

Then:

```text
[ Upload Dataset ]

[ Try Breast Cancer Demo ]

[ Try Heart Disease Demo ]

[ Try Parkinson's Demo ]
```

---

# 54. Dataset Upload Experience

Screen:

```text
UPLOAD BIOMEDICAL DATASET

┌────────────────────────────────┐
│                                │
│       Drop CSV here            │
│                                │
│       or                      │
│                                │
│       [ Browse Files ]         │
│                                │
└────────────────────────────────┘
```

After upload:

```text
Analyzing dataset...
```

Then automatically navigate to the profile.

---

# 55. Dataset Profile Screen

Use cards:

```text
569
Samples

30
Features

2
Classes

0
Missing Values
```

Then:

```text
TARGET DISTRIBUTION
```

and:

```text
FEATURE TYPES
```

and:

```text
DATA QUALITY
✓ Good
```

---

# 56. Pipeline Visualization

This should be highly visible.

```text
DATASET
   ↓
VALIDATE
   ↓
PREPROCESS
   ↓
PCA
   ↓
CLASSICAL + QUANTUM
   ↓
BENCHMARK
   ↓
EXPLAIN
   ↓
COST
   ↓
RECOMMEND
```

Each stage should change:

```text
grey → active → green
```

as the experiment executes.

---

# 57. Experiment Planning Screen

Display:

```text
WHY THIS PIPELINE?

✓ Binary classification detected
✓ Numerical features detected
✓ PCA required for compact quantum representation
✓ 8-dimensional representation fits configured
  quantum simulation budget
✓ Disease classification requires recall
  and specificity
✓ Classical baselines included
```

This is one of the most important screens for demonstrating our architecture.

---

# 58. Experiment Running Screen

Display real progress.

```text
EXPERIMENT EXP-000001

Dataset Validation      ✓
Preprocessing           ✓
Feature Reduction       ✓

Logistic Regression     ✓
SVM                     ✓
Random Forest           ✓

VQC                     ● RUNNING

Benchmark               ○
Explainability          ○
Report                  ○
```

---

# 59. Results Screen

Top:

```text
EXPERIMENT COMPLETE
```

Then:

```text
BEST CLASSICAL
Random Forest

BEST QUANTUM
VQC
```

Then comparison.

---

# 60. Results Should Never Hide the Cost

Display performance and cost together.

Example:

```text
                    Classical     Quantum

Recall                 XX.X%        XX.X%
AUC                    XX.X%        XX.X%
Runtime                 X sec        XX sec
Memory                  X MB         XX MB
Qubits                     -             8
```

This prevents misleading "accuracy-only" conclusions.

---

# 61. PHASE 25 — Error Handling

Every operation needs a user-friendly error.

Bad:

```text
KeyError: target
```

Good:

```text
DATASET ERROR

We could not confidently identify
the target column.

Please select the column containing
the disease outcome.
```

---

# 62. Quantum Failure

Bad:

```text
Python exception
```

Good:

```text
QUANTUM EXECUTION FAILED

Reason:
Simulation exceeded configured resource limit.

Suggested action:
Reduce quantum dimensions from 8 to 4
or reduce circuit depth.
```

---

# 63. PHASE 26 — Logging

Backend logs:

```text
timestamp
experiment_id
stage
model
duration
status
error
```

Example:

```text
[12:04:31]
EXP-000001
VQC
training
started

[12:05:12]
EXP-000001
VQC
training
completed
41.2s
```

---

# 64. PHASE 27 — Reproducibility

Every experiment should store:

```text
random seed
dataset hash
dataset ID
preprocessing configuration
PCA configuration
model configuration
quantum configuration
backend
train/test split
```

Example:

```json
{
  "seed": 42,
  "dataset_hash": "...",
  "pca_components": 8,
  "qubits": 8,
  "layers": 2,
  "shots": 1024,
  "backend": "local"
}
```

---

# 65. PHASE 28 — Testing

## Unit tests

Test:

```text
profiler
validator
preprocessor
PCA
classical models
quantum circuit
metrics
recommendation
```

---

# 66. Integration Test

Test:

```text
CSV
 ↓
Profiler
 ↓
Preprocessor
 ↓
PCA
 ↓
Classical
 ↓
Quantum
 ↓
Benchmark
```

---

# 67. End-to-End Test

The most important test:

```text
Upload CSV
 ↓
Profile
 ↓
Validate
 ↓
Build plan
 ↓
Run experiment
 ↓
Generate results
 ↓
Explain
 ↓
Resource analysis
 ↓
Recommendation
```

If this works, the MVP is genuinely functional.

---

# 68. PHASE 29 — First Dataset Implementation

Start ONLY with:

```text
Breast Cancer Wisconsin Diagnostic
```

Do not start all three simultaneously.

---

# 69. Breast Cancer First Vertical Slice

Implement:

```text
breast_cancer.csv
      ↓
Profile
      ↓
Target detection
      ↓
Train/test split
      ↓
Scaling
      ↓
PCA → 4/8
      ↓
Logistic Regression
      ↓
SVM
      ↓
Random Forest
      ↓
VQC
      ↓
Metrics
      ↓
Comparison
```

Do not move to Heart Disease until this works.

---

# 70. Then Add Heart Disease

Once the generic pipeline works:

```text
heart_disease.csv
```

should require only:

```text
HeartDiseaseAdapter
```

and configuration adjustments.

The rest of the pipeline remains unchanged.

---

# 71. Then Add Parkinson's

Add:

```text
ParkinsonsAdapter
```

Pay particular attention to:

```text
subject/group information
```

to prevent subject leakage where applicable.

---

# 72. Generic CSV Support

After the three known datasets work:

```text
Upload Your CSV
```

should work for a compatible binary classification CSV.

The system should not need to know beforehand that it is:

```text
Breast Cancer
Heart Disease
Parkinson's
```

---

# 73. Dataset Compatibility Screen

For unknown CSV:

```text
DATASET COMPATIBILITY

Task
✓ Binary classification

Numerical features
✓ Detected

Target
⚠ User confirmation required

Missing values
✓ Manageable

Quantum representation
✓ Feasible

Status:
READY AFTER TARGET SELECTION
```

---

# 74. MVP Configuration

Create:

```text
config.yaml
```

Example:

```yaml
experiment:
  random_state: 42
  test_size: 0.20

classical:
  models:
    - logistic_regression
    - svm
    - random_forest

quantum:
  model: vqc
  max_qubits: 8
  candidate_dimensions:
    - 4
    - 8
  layers: 2
  shots: 1024

resources:
  max_runtime_seconds: 300
```

These values should be configurable.

---

# 75. Data Flow

Complete backend data flow:

```text
Uploaded CSV
     ↓
Dataset ID
     ↓
Dataset Registry
     ↓
Profiler
     ↓
Validation
     ↓
Dataset Metadata
     ↓
Experiment Planner
     ↓
Experiment Configuration
     ↓
Preprocessing Pipeline
     ↓
Train/Test Data
     ↓
Feature Reduction
     ↓
Model Execution
     ↓
Raw Results
     ↓
Benchmark Engine
     ↓
Explanation
     ↓
Resource Analysis
     ↓
Recommendation
     ↓
Report
```

---

# 76. Database Entities

SQLite tables:

## Dataset

```text
id
name
filename
path
hash
rows
columns
target
created_at
```

## Experiment

```text
id
dataset_id
status
configuration
created_at
started_at
completed_at
```

## ModelResult

```text
id
experiment_id
model
model_type
metrics
runtime
resources
```

## Report

```text
id
experiment_id
path
created_at
```

---

# 77. Storage Strategy

Dataset:

```text
data/uploads/
```

Models:

```text
artifacts/models/
```

Experiment outputs:

```text
artifacts/experiments/EXP-000001/
```

Reports:

```text
artifacts/reports/
```

Example:

```text
EXP-000001/
├── config.json
├── preprocessing.pkl
├── pca.pkl
├── classical/
│   ├── logistic.pkl
│   ├── svm.pkl
│   └── random_forest.pkl
├── quantum/
│   └── vqc.json
├── metrics.json
├── predictions.csv
└── resource_usage.json
```

---

# 78. API Design

## Dataset

```text
POST /api/datasets/upload
GET  /api/datasets
GET  /api/datasets/{id}
GET  /api/datasets/{id}/profile
```

## Experiment

```text
POST /api/experiments
GET  /api/experiments
GET  /api/experiments/{id}
POST /api/experiments/{id}/run
GET  /api/experiments/{id}/status
```

## Results

```text
GET /api/experiments/{id}/results
GET /api/experiments/{id}/explanation
GET /api/experiments/{id}/resources
GET /api/experiments/{id}/recommendation
```

## Reports

```text
POST /api/experiments/{id}/report
GET  /api/experiments/{id}/report
```

---

# 79. Execution Architecture for MVP

Do not introduce Celery/Redis immediately.

Start with:

```text
FastAPI
   ↓
Background task
   ↓
Experiment Executor
```

If experiments become too long or unreliable, introduce a job queue later.

The architecture should still keep the executor isolated so this migration is possible.

---

# 80. Long-Running Experiment Behavior

The frontend should never wait for the entire experiment in one HTTP request.

Correct:

```text
POST /experiments/{id}/run
        ↓
returns experiment ID
        ↓
background execution
        ↓
frontend polls status
```

Example:

```text
GET /experiments/EXP-000001/status
```

Response:

```json
{
  "status": "running",
  "stage": "quantum_training",
  "progress": 67
}
```

---

# 81. Demo Mode

Create:

```text
DEMO MODE
```

but do not fake results.

Demo mode may use:

```text
small dataset subset
fixed seed
known configuration
```

and optionally cached completed experiments.

If cached:

```text
RESULT SOURCE:
Previously completed benchmark
```

If live:

```text
RESULT SOURCE:
Live local execution
```

---

# 82. Main Demo Story

The entire demo should be:

```text
1. Upload Breast Cancer CSV

2. Platform profiles it

3. Platform identifies binary classification

4. Platform explains preprocessing

5. Platform reduces 30 → 8 dimensions

6. Platform creates classical + quantum experiment

7. Models run

8. Results appear

9. Explainability appears

10. Resource usage appears

11. Platform produces final recommendation
```

This is the complete MVP story.

---

# 83. The "Wow" Moment

The strongest screen should say:

```text
                    QUANTUM VALUE ASSESSMENT

              Classical          Quantum

Recall          XX.X%             XX.X%
AUC             XX.X%             XX.X%
Runtime          X sec             XX sec

                     ↓

             ┌─────────────────────┐
             │  FINAL ASSESSMENT   │
             │                     │
             │  Based on measured  │
             │  performance and    │
             │  computational cost │
             └─────────────────────┘
```

The key is that this assessment comes from **actual experiment results**.

---

# 84. Medical Disclaimer

The platform should display:

```text
RESEARCH / BENCHMARKING SYSTEM

Predictions generated by this platform
are for research and benchmarking purposes
and are not clinical diagnoses.
```

Do not call the output:

```text
diagnosis
```

in the sense of a clinical decision.

Use:

```text
model prediction
classification
risk prediction
benchmark result
```

---

# 85. What the MVP Demonstrates Against the SIH PS

The SIH requirements map as follows:

| SIH Requirement        | MVP Implementation                       |
| ---------------------- | ---------------------------------------- |
| Data ingestion         | CSV upload                               |
| Data preprocessing     | Cleaning + scaling                       |
| Feature engineering    | Feature pipeline                         |
| Feature selection      | PCA/reduction                            |
| Hybrid model           | Classical + VQC                          |
| Training               | Both branches                            |
| Inference              | Both branches                            |
| Performance evaluation | Benchmark engine                         |
| Explainability         | SHAP/feature explanation + circuit trace |
| Classical comparison   | LR + SVM + RF                            |
| Quantum simulator      | Local PennyLane simulator                |
| Scalability            | Resource/runtime measurements            |
| Hardware compatibility | QuantumBackend abstraction               |
| Documentation          | README + report                          |
| Platform               | React + FastAPI                          |

---

# 86. What the MVP Does NOT Claim

We must explicitly avoid claiming:

```text
"Quantum advantage has been proven."

"Quantum is faster."

"Quantum is more accurate for all diseases."

"The model is clinically validated."

"The model can diagnose patients."

"We tested real quantum hardware."
```

unless our actual experiments genuinely establish the relevant statement.

---

# 87. Success Criteria

The MVP is complete when a clean run can perform:

```text
CSV
 ↓
Upload
 ↓
Profile
 ↓
Validate
 ↓
Plan
 ↓
Preprocess
 ↓
Reduce
 ↓
Train classical models
 ↓
Train VQC
 ↓
Predict
 ↓
Calculate metrics
 ↓
Compare
 ↓
Explain
 ↓
Measure resources
 ↓
Recommend
 ↓
Generate report
```

without manually opening a notebook or running a separate Python script.

---

# 88. Build Order

This is the exact order we should follow.

## STEP 1

Environment.

```text
Python
FastAPI
React
PennyLane
scikit-learn
```

---

## STEP 2

Read the actual three CSVs.

For each dataset record:

```text
filename
columns
rows
dtypes
target candidates
missing values
duplicates
class distribution
subject/group information
```

Do this BEFORE writing dataset-specific preprocessing.

---

## STEP 3

Build:

```text
Dataset Loader
```

---

## STEP 4

Build:

```text
Profiler
```

---

## STEP 5

Build:

```text
Validator
```

---

## STEP 6

Build:

```text
Preprocessing Pipeline
```

---

## STEP 7

Build:

```text
Feature Reduction
```

---

## STEP 8

Build:

```text
Classical Model Engine
```

Get this fully working.

---

## STEP 9

Build:

```text
VQC
```

Test it independently first.

---

## STEP 10

Connect:

```text
Classical + VQC
```

under one experiment.

---

## STEP 11

Build:

```text
Benchmark Engine
```

---

## STEP 12

Build:

```text
Resource Monitor
```

---

## STEP 13

Build:

```text
Recommendation Engine
```

---

## STEP 14

Build FastAPI endpoints.

---

## STEP 15

Build the React UI around the already-working backend.

---

## STEP 16

Connect frontend and backend.

---

## STEP 17

Add experiment history.

---

## STEP 18

Add explainability.

---

## STEP 19

Add report generation.

---

## STEP 20

Test complete end-to-end flow.

---

# 89. Priority Order

## P0 — Must Work

```text
CSV upload
Profiler
Validator
Preprocessing
PCA
Logistic Regression
SVM
Random Forest
VQC
Metrics
Comparison
```

## P1 — Important

```text
Experiment planner
Progress tracking
Explainability
Resource monitoring
Recommendation
```

## P2 — Nice to Have

```text
Experiment history
Report generation
Polished charts
Demo mode
```

## P3 — Later

```text
Cloud quantum
Real hardware
LLM agent
Images
Genomics
EHR
Authentication
```

---

# 90. Definition of "Done"

Do NOT say the MVP is done because:

```text
the frontend loads
```

or:

```text
the VQC runs in a notebook
```

The MVP is done only when:

```text
User
 ↓
Uploads CSV
 ↓
Sees dataset profile
 ↓
Sees system-generated experiment plan
 ↓
Clicks Run
 ↓
Sees real progress
 ↓
Classical models execute
 ↓
Quantum model executes
 ↓
Results are generated
 ↓
Results are compared
 ↓
Explanation is shown
 ↓
Resources are shown
 ↓
Recommendation is generated
```

---

# 91. First Milestone

Before touching the frontend, we should achieve this from a Python script:

```text
python run_experiment.py breast_cancer.csv
```

and receive:

```text
DATASET PROFILE
       ↓
EXPERIMENT PLAN
       ↓
CLASSICAL RESULTS
       ↓
QUANTUM RESULTS
       ↓
COMPARISON
       ↓
RESOURCE USAGE
       ↓
RECOMMENDATION
```

If this works, the core product exists.

The UI then becomes a presentation/interface layer around a proven engine.

---

# 92. Second Milestone

Turn that engine into:

```text
FastAPI
```

so:

```text
POST /datasets/upload
POST /experiments
POST /experiments/{id}/run
GET /experiments/{id}/status
GET /experiments/{id}/results
```

work.

---

# 93. Third Milestone

Build the React interface.

The UI should consume the backend rather than contain ML logic.

Never put:

```text
PCA
VQC
RandomForest
SHAP
```

inside React.

React only displays and interacts with the backend.

---

# 94. Fourth Milestone

Run the same platform on:

```text
Breast Cancer
Heart Disease
Parkinson's
```

without changing the core engine.

---

# 95. Final MVP Architecture

```text
                         USER
                          │
                          ▼
                    ┌───────────┐
                    │   REACT   │
                    │    UI     │
                    └─────┬─────┘
                          │
                          ▼
                    ┌───────────┐
                    │  FASTAPI  │
                    └─────┬─────┘
                          │
              ┌───────────┼────────────┐
              │           │            │
              ▼           ▼            ▼
           DATA       EXPERIMENT    STORAGE
          ENGINE        ENGINE
              │           │
       ┌──────┼──────┐    │
       ▼      ▼      ▼    │
   Profiler Validator Prep
                           │
                           ▼
                    Feature Reduction
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
           CLASSICAL              QUANTUM
           ENGINE                 ENGINE
                │                     │
       ┌────────┼────────┐            │
       ▼        ▼        ▼            ▼
      LR       SVM       RF          VQC
                │                     │
                └──────────┬──────────┘
                           ▼
                    BENCHMARK ENGINE
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              EXPLAINABILITY   RESOURCES
                    │             │
                    └──────┬──────┘
                           ▼
                  RECOMMENDATION
                           │
                           ▼
                        REPORT
```

---

# 96. The Final User Experience

The complete MVP should feel like this:

```text
┌─────────────────────────────────────────────┐
│              QUANT WARRIORS                │
│                                             │
│  Hybrid Quantum Disease Detection          │
│                                             │
│  [ Upload Biomedical CSV ]                 │
│                                             │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ DATASET UNDERSTANDING                       │
│                                             │
│ 569 samples     30 features    2 classes   │
│                                             │
│ Target: diagnosis                           │
│ Missing: 0                                  │
│ Status: ✓ Ready                             │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ EXPERIMENT PLAN                             │
│                                             │
│ Standardize → PCA → 8 dimensions           │
│                                             │
│ Classical: LR / SVM / RF                   │
│ Quantum: VQC                               │
│ Backend: Local Simulator                   │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ RUNNING EXPERIMENT                          │
│                                             │
│ ✓ Preprocessing                             │
│ ✓ Classical models                          │
│ ● Quantum VQC                               │
│ ○ Benchmark                                 │
│ ○ Explainability                            │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ RESULTS                                     │
│                                             │
│ Classical vs Quantum                       │
│                                             │
│ Accuracy   Recall   AUC   Runtime           │
│                                             │
│ [comparison charts]                         │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ EXPLAINABILITY                              │
│                                             │
│ Top contributing features                  │
│ Quantum circuit                            │
│ Prediction pathway                         │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ RESOURCE & COST                             │
│                                             │
│ Qubits: 8                                  │
│ Shots: 1024                                │
│ Runtime: XX sec                            │
│ CPU / RAM: XX                              │
│ Backend: Local Simulator                   │
└─────────────────────────────────────────────┘
                    ↓

┌─────────────────────────────────────────────┐
│ FINAL ASSESSMENT                            │
│                                             │
│      QUANTUM VALUE ASSESSMENT              │
│                                             │
│ Performance:      ↑                         │
│ Recall:           ↑                         │
│ Computational:    Higher                    │
│                                             │
│ CONCLUSION:                                 │
│ Quantum shows promise for the evaluated    │
│ metric, with a computational trade-off.     │
└─────────────────────────────────────────────┘
```

---

# 97. The Main Engineering Principle

Build **one vertical slice completely** before expanding.

The first target is:

```text
Breast Cancer CSV
      ↓
Complete working backend
      ↓
Complete working experiment
      ↓
Complete working UI
```

Only after that:

```text
Heart Disease
      ↓
Parkinson's
```

Then:

```text
Generic CSV
```

Then later:

```text
Images
Genomics
EHR
Hardware
Agentic planning
```

---

# 98. What We Should Start With Right Now

The immediate next task is **not coding the VQC**.

First:

## Inspect the three actual CSV files.

For each file we need to establish the ground truth:

```text
1. Exact filename
2. Number of rows
3. Number of columns
4. Exact column names
5. Data types
6. Target column
7. Target values
8. Missing values
9. Duplicate rows
10. ID columns
11. Subject/group columns
12. Categorical columns
13. Numerical columns
14. Potential leakage columns
15. Class imbalance
```

Only after that should we finalize the dataset adapters and preprocessing rules.

That prevents us from building a pipeline around an assumed Kaggle schema that differs from the files you actually downloaded.

---

# 99. Immediate Build Sequence

Therefore our next actual coding sequence should be:

```text
STEP 1
Inspect CSVs
       ↓
STEP 2
Create project repository
       ↓
STEP 3
Implement DatasetLoader
       ↓
STEP 4
Implement DatasetProfiler
       ↓
STEP 5
Implement Validator
       ↓
STEP 6
Implement BreastCancerAdapter
       ↓
STEP 7
Implement preprocessing
       ↓
STEP 8
Implement PCA
       ↓
STEP 9
Implement LR/SVM/RF
       ↓
STEP 10
Implement VQC
       ↓
STEP 11
Create unified ExperimentRunner
       ↓
STEP 12
Create BenchmarkEngine
       ↓
STEP 13
Create ResourceMonitor
       ↓
STEP 14
Create RecommendationEngine
       ↓
STEP 15
Expose through FastAPI
       ↓
STEP 16
Build React UI
       ↓
STEP 17
Connect everything
       ↓
STEP 18
Run complete demo
```

---

# 100. Final Definition of Our MVP

The MVP is **not**:

> "A VQC that predicts breast cancer."

The MVP is:

> **A local interactive hybrid-QML experimentation platform that accepts biomedical CSV data, automatically understands and prepares the dataset, constructs a controlled classical-versus-quantum experiment, executes both approaches, compares predictive performance and computational resources, explains the results, and produces an evidence-based recommendation.**

That is the product we should build for the internal hackathon.
