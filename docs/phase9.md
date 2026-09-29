# PHASE 9 — Experiment Planning & Orchestration

## 1. Purpose

Phase 7 created the **classical model candidates and baseline**.

Phase 8 created the **quantum model candidates and configurations**.

Phase 9 is where we decide:

> **"Exactly which experiments should be run, in what order, with which dataset representation, model, parameters, backend, and evaluation protocol?"**

This is the phase where our earlier idea of a **rule-based/agentic decision layer** becomes useful.

But we should keep an important distinction:

> The first version does **not need an LLM agent**.

We can build a deterministic **rule-based experiment planner** first.

Later, an agent can sit on top of it.

---

# 2. Position in the System

```text
PHASE 1
Dataset Ingestion
        ↓
PHASE 2
Dataset Profiling
        ↓
PHASE 3
Dataset Validation
        ↓
PHASE 4
Preprocessing
        ↓
PHASE 5
Feature Engineering
        ↓
PHASE 6
Feature Selection & Reduction
        ↓
       ┌───────────────────────┐
       │                       │
       ↓                       ↓
PHASE 7                  PHASE 8
Classical ML             Quantum ML
Candidates               Candidates
       │                       │
       └───────────┬───────────┘
                   ↓
┌──────────────────────────────────────┐
│ PHASE 9                              │
│ EXPERIMENT PLANNING & ORCHESTRATION  │
└──────────────────┬───────────────────┘
                   ↓
               PHASE 10
          Model Training & Execution
                   ↓
               PHASE 11
        Quantum vs Classical Benchmark
```

---

# 3. The Main Problem Phase 9 Solves

By now, we could have:

```text
3 classical models

2 quantum algorithms

3 feature representations

2 circuit depths

2 encodings
```

That already creates:

```text
3 × 2 × 3 × 2 × 2
=
72 possible experiments
```

We do **not** want the system blindly running all 72.

Instead:

```text
Dataset characteristics
        ↓
Rules
        ↓
Candidate filtering
        ↓
Experiment prioritization
        ↓
Experiment plan
```

---

# 4. Why This Is Important

This is the beginning of our platform becoming intelligent.

Instead of the user saying:

> "Run VQC with 8 qubits."

the platform can determine:

```text
Dataset
 ↓
Binary classification
 ↓
1,200 samples
 ↓
16 selected features
 ↓
Small-data regime
 ↓
QML feasible
 ↓
VQC + quantum kernel selected
 ↓
8 and 16 feature representations
 ↓
Local simulator
 ↓
Controlled experiments
```

---

# 5. But We Should NOT Call It "AI Agent" Yet

Our initial implementation should be:

```text
Rule Engine
+
Experiment Planner
+
Model Registry
+
Resource Estimator
```

For example:

```text
IF
feature_dimension <= 16
AND
sample_count <= threshold
AND
task == binary_classification

THEN
consider VQC
consider quantum kernel
```

This is:

> **deterministic and explainable.**

Later:

```text
LLM Agent
      ↓
interprets user goal
      ↓
calls Rule Engine
      ↓
selects tools
      ↓
creates experiment plan
```

That gives us an **agentic layer without making the core scientific pipeline non-deterministic**.

---

# 6. Input

Phase 9 receives:

```text
dataset profile
+
validation report
+
preprocessing configuration
+
feature representations
+
classical model candidates
+
quantum model candidates
+
resource estimates
```

Example:

```text
Dataset:
1,500 samples
20 engineered features

Representations:
REP-001 = 20 features
QREP-001 = 8 features
QREP-002 = 16 features

Classical:
Logistic Regression
SVM
Random Forest
XGBoost

Quantum:
VQC
Quantum Kernel
```

---

# 7. High-Level Flow

```text
                    INPUTS
                      │
                      ▼
             ┌─────────────────┐
             │ Task Analyzer   │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Feasibility     │
             │ Rules           │
             └────────┬────────┘
                      │
                      ▼
             Candidate Filtering
                      │
                      ▼
             ┌─────────────────┐
             │ Experiment      │
             │ Generator       │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Resource        │
             │ Estimator       │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Priority /      │
             │ Scheduling      │
             └────────┬────────┘
                      │
                      ▼
             EXPERIMENT PLAN
                      │
                      ▼
                   PHASE 10
```

---

# 8. Module 9.1 — Task Analyzer

First identify:

```text
task_type
target
number_of_classes
sample_count
feature_count
data_modality
```

Example:

```json
{
  "task": "binary_classification",
  "samples": 1500,
  "features": 16,
  "classes": 2,
  "modality": "tabular"
}
```

This information controls the rest of the planning process.

---

# 9. Module 9.2 — Dataset Regime Classification

The planner can categorize the dataset.

For example:

```text
Small:
< 5,000 samples

Medium:
5,000–100,000

Large:
> 100,000
```

These are configurable engineering categories, not universal scientific thresholds.

Why do this?

Because QML experiments on:

```text
1,000 samples
```

are very different from:

```text
1,000,000 samples
```

---

# 10. Feature-Dimension Rules

Example:

```text
IF features <= 8
    → direct small quantum candidate

IF features <= 16
    → compact quantum candidate

IF features > 16
    → require dimensionality reduction

IF features > 64
    → quantum branch requires aggressive compression
```

These are **initial engineering rules**.

We can tune them later based on our actual experiments.

---

# 11. Sample-Size Rules

Suppose:

```text
samples = 500
features = 8
```

A quantum experiment may be relatively manageable.

But:

```text
samples = 1,000,000
features = 8
```

training a variational circuit through millions of repeated circuit evaluations could be computationally expensive.

Therefore the planner can say:

```text
QML:
small/controlled subset for initial experiment
```

while:

```text
Classical:
full dataset
```

But for the final scientific comparison, we must be very careful about fairness.

---

# 12. Module 9.3 — Classical Candidate Filtering

Suppose Phase 7 produced:

```text
Logistic Regression
SVM
Random Forest
XGBoost
```

Phase 9 might decide:

```text
Always run:
Logistic Regression

Run:
SVM

Run:
XGBoost

Optional:
Random Forest
```

Why?

We don't need every model for every representation.

---

# 13. Quantum Candidate Filtering

Suppose Phase 8 produced:

```text
QMODEL-001
VQC / 8 qubits / 2 layers

QMODEL-002
VQC / 8 qubits / 4 layers

QMODEL-003
Quantum Kernel / 8 features
```

Phase 9 checks:

```text
Is feature dimension compatible?
Is simulator available?
Is estimated workload acceptable?
Is this configuration redundant?
```

Then produces:

```text
Selected:
QMODEL-001
QMODEL-003

Defer:
QMODEL-002
```

---

# 14. Module 9.4 — Experiment Matrix

This is one of the most important outputs.

Example:

| Experiment | Representation | Classical/Quantum | Model               | Qubits | Backend         |
| ---------- | -------------- | ----------------- | ------------------- | -----: | --------------- |
| EXP-001    | REP-001        | Classical         | Logistic Regression |      — | CPU             |
| EXP-002    | REP-001        | Classical         | XGBoost             |      — | CPU             |
| EXP-003    | QREP-001       | Classical         | SVM                 |      — | CPU             |
| EXP-004    | QREP-001       | Quantum           | VQC                 |      8 | Local Simulator |
| EXP-005    | QREP-001       | Quantum           | Quantum Kernel      |      8 | Local Simulator |
| EXP-006    | QREP-002       | Quantum           | VQC                 |     16 | Local Simulator |

This matrix defines exactly what will happen.

---

# 15. Fair Comparison Groups

We should explicitly create **comparison groups**.

Example:

```text
GROUP-A

Representation:
QREP-001

Classical:
SVM

Quantum:
VQC

Same:
dataset
split
features
```

This allows:

```text
SVM vs VQC
```

under controlled conditions.

---

# 16. Best-Classical Comparison

Another group:

```text
GROUP-B

Best classical representation
        ↓
XGBoost
```

versus:

```text
Best quantum configuration
        ↓
VQC
```

This answers:

> "What is the strongest practical solution?"

---

# 17. Two Comparison Questions

Our system should preserve both:

### Question 1

> Which approach performs best overall?

```text
Best Classical
vs
Best Quantum
```

### Question 2

> Does the quantum learning method add value under the same compact representation?

```text
Same Representation
      ↓
Classical
      vs
Quantum
```

These are different scientific questions.

---

# 18. Module 9.5 — Experiment Priority

Not every experiment has equal importance.

Assign priority:

```text
P0 = mandatory
P1 = important
P2 = optional
```

Example:

```text
P0
XGBoost baseline

P0
VQC 8-qubit

P0
Quantum Kernel 8-feature

P1
SVM on QREP-001

P1
VQC 16-qubit

P2
VQC 16-qubit + deeper circuit
```

---

# 19. Why Priority Matters

Suppose our laptop has:

```text
8 GB RAM
```

and:

```text
QMODEL-006
```

would take 10 hours.

We shouldn't run it before knowing whether:

```text
QMODEL-001
```

already gives useful results.

So:

```text
Cheap experiments
       ↓
Validate pipeline
       ↓
Moderate experiments
       ↓
Expensive experiments
```

---

# 20. Module 9.6 — Resource-Aware Planning

For every experiment estimate:

```text
CPU time
RAM
GPU requirement
quantum circuit count
shots
estimated simulation memory
storage
```

Example:

```text
EXP-004

Qubits: 8
Depth: 2
Shots: 1024

Estimated:
RAM = 500 MB
CPU = 2 cores
Time = 15 minutes
```

Then:

```text
EXP-006

Qubits: 16
Depth: 6
Shots: 4096

Estimated:
RAM = 8 GB+
Time = several hours
```

The planner can prioritize accordingly.

---

# 21. Module 9.7 — Execution Budget

We should introduce a budget.

For example:

```json
{
  "max_experiment_time_minutes": 120,
  "max_local_memory_gb": 8,
  "max_qubits": 16,
  "max_shots": 4096
}
```

Then the planner rejects or defers experiments exceeding the budget.

---

# 22. This Addresses Our Cost Concern

Remember the concern we discussed:

> "What about cost? What does this actually provide for people?"

The experiment planner starts addressing that technically.

Instead of:

```text
Run everything
```

we use:

```text
Scientific value
+
performance
+
resource requirements
+
cost constraints
```

to determine what to run.

---

# 23. Module 9.8 — Experiment Configuration

Every experiment gets a complete immutable configuration.

Example:

```json
{
  "experiment_id": "EXP-Q-000001",

  "dataset": "DS-000001",

  "representation": "QREP-001",

  "model": "QMODEL-001",

  "backend": "LOCAL_SIMULATOR",

  "shots": 1024,

  "seed": 42,

  "evaluation_protocol": "STRATIFIED_5FOLD",

  "metrics": [
    "accuracy",
    "recall",
    "specificity",
    "f1",
    "roc_auc",
    "pr_auc"
  ]
}
```

This configuration is the **contract** for Phase 10.

---

# 24. Module 9.9 — Reproducibility

Experiment IDs:

```text
EXP-C-000001
EXP-C-000002

EXP-Q-000001
EXP-Q-000002
```

Each experiment has:

```text
dataset version
feature version
model version
configuration
random seed
backend
execution parameters
```

This allows us to reproduce any result.

---

# 25. Module 9.10 — Rule-Based Decision Engine

Now we reach the part related to our earlier "agentic" discussion.

The first version can use rules.

Example:

```text
RULE-001

IF
task = binary classification
AND
features <= 16
AND
samples <= 5000

THEN
enable VQC
```

Another:

```text
RULE-002

IF
features > 16

THEN
require dimensionality reduction
before quantum execution
```

Another:

```text
RULE-003

IF
estimated simulation memory > available RAM

THEN
reject configuration
```

---

# 26. More Advanced Rules

Example:

```text
IF
dataset_size is small
AND
feature_dimension is small
AND
binary classification

THEN
priority:
VQC
Quantum Kernel
```

Another:

```text
IF
feature_dimension > quantum_limit

THEN
generate PCA candidate
```

Another:

```text
IF
quantum model depth > threshold
AND
no evidence of improvement

THEN
deprioritize
```

---

# 27. Rule Engine Output

The engine might say:

```text
Dataset:
DS-000001

Task:
Binary classification

Recommended experiments:

1. XGBoost baseline
2. SVM on quantum representation
3. 8-qubit VQC
4. 8-feature quantum kernel

Deferred:

16-qubit VQC
Reason:
resource budget

Rejected:

32-qubit VQC
Reason:
local simulation exceeds memory budget
```

This is already an **intelligent experiment planner**.

---

# 28. Where an Agent Can Be Added Later

Eventually:

```text
                USER
                 |
                 ↓
          "Analyze this dataset"
                 |
                 ↓
             AI AGENT
                 |
        ┌────────┼─────────┐
        ↓        ↓         ↓
    Profiler   Rule     Registry
               Engine
        │        │         │
        └────────┼─────────┘
                 ↓
          Experiment Plan
```

The agent can interpret the task and invoke the deterministic components.

But:

> **The scientific decisions should remain traceable to explicit rules/configurations.**

We don't want:

```text
LLM randomly decides:
"Let's use 11 qubits because it sounds good."
```

---

# 29. Explainable Decision Trace

This is extremely important.

For every decision, record:

```text
Decision:
Select QMODEL-001

Reason:
- binary classification
- feature dimension = 8
- available local simulator
- estimated memory = 1.2 GB
- within experiment budget
```

Another:

```text
Decision:
Reject QMODEL-006

Reason:
- 32 qubits
- estimated simulation memory > available memory
```

This gives us an **auditable decision system**.

---

# 30. Agentic vs Rule-Based

Our architecture can therefore evolve:

### Version 1

```text
Rule-Based Planner
```

### Version 2

```text
Rule-Based Planner
+
Automated experiment scheduler
```

### Version 3

```text
Agent
+
Rule Engine
+
Tool Registry
+
Experiment Scheduler
```

The core scientific pipeline doesn't need to change.

---

# 31. Module 9.11 — Experiment Queue

The final experiment plan becomes a queue:

```text
QUEUE

1. EXP-C-001
   XGBoost
   P0

2. EXP-Q-001
   VQC 8-qubit
   P0

3. EXP-Q-002
   Quantum Kernel
   P0

4. EXP-C-002
   SVM on QREP-001
   P1

5. EXP-Q-003
   VQC 16-qubit
   P2
```

Phase 10 executes this queue.

---

# 32. Module 9.12 — Failure Handling

Experiments can fail.

Example:

```text
VQC
 ↓
Out of memory
```

The planner should not simply crash.

It should record:

```text
EXP-Q-003
STATUS = FAILED

Reason:
MemoryExceeded
```

Then potentially:

```text
Fallback:
reduce qubits
reduce shots
use smaller representation
```

But fallback actions must be explicitly defined.

---

# 33. Example Complete Planning Scenario

Suppose our dataset is:

```text
Skin Cancer

Images:
3,000

CNN embedding:
1280 dimensions
```

Phase 6 produces:

```text
QREP-001
16 features

QREP-002
8 features
```

Phase 7:

```text
XGBoost
AUC = 0.94
```

Phase 8:

```text
QMODEL-001
VQC
8 qubits

QMODEL-002
VQC
16 qubits

QMODEL-003
Quantum Kernel
8 qubits
```

Phase 9 analyzes:

```text
3,000 samples
+
8/16 features
+
local simulator
+
8 GB RAM
```

---

# 34. Planner Decision

It creates:

```text
P0

EXP-001
XGBoost
best classical representation

EXP-002
SVM
8-feature representation

EXP-003
VQC
8 qubits

EXP-004
Quantum Kernel
8 qubits
```

Then:

```text
P1

EXP-005
VQC
16 qubits
```

And:

```text
P2

EXP-006
VQC
16 qubits
deeper circuit
```

---

# 35. Execution Strategy

The system executes:

```text
P0
 ↓
validate pipeline
 ↓
collect results
 ↓
P1
 ↓
compare
 ↓
P2 only if justified
```

This saves resources.

---

# 36. Phase 9 Output

The main output is:

```text
EXPERIMENT PLAN
```

Example:

```json
{
  "plan_id": "PLAN-000001",

  "dataset_id": "DS-000001",

  "experiments": [
    {
      "id": "EXP-C-001",
      "priority": "P0",
      "model": "XGBoost",
      "representation": "REP-001"
    },
    {
      "id": "EXP-C-002",
      "priority": "P0",
      "model": "SVM",
      "representation": "QREP-001"
    },
    {
      "id": "EXP-Q-001",
      "priority": "P0",
      "model": "VQC",
      "representation": "QREP-001"
    },
    {
      "id": "EXP-Q-002",
      "priority": "P0",
      "model": "QUANTUM_KERNEL",
      "representation": "QREP-001"
    }
  ],

  "status": "READY_FOR_EXECUTION"
}
```

---

# 37. Experiment Plan Artifact

We should physically save:

```text
experiments/
│
├── PLAN-000001/
│
│   ├── plan.json
│   ├── experiment_matrix.csv
│   │
│   ├── EXP-C-001/
│   │   └── config.json
│   │
│   ├── EXP-Q-001/
│   │   └── config.json
│   │
│   └── EXP-Q-002/
│       └── config.json
```

This is extremely useful for reproducibility.

---

# 38. What Phase 9 Does NOT Do

Phase 9 does **not**:

* train models
* run quantum circuits
* calculate final accuracy
* claim quantum advantage
* perform final benchmarking
* perform explainability
* make the final user-facing medical prediction

It creates the **execution plan**.

---

# 39. Phase 9 Success Criteria

Phase 9 is complete when the system can:

* [ ] Analyze dataset/task characteristics
* [ ] Read available feature representations
* [ ] Read classical model candidates
* [ ] Read quantum model candidates
* [ ] Apply feasibility rules
* [ ] Filter invalid configurations
* [ ] Generate experiment combinations
* [ ] Create fair comparison groups
* [ ] Prioritize experiments
* [ ] Estimate resource requirements
* [ ] Enforce execution budgets
* [ ] Create immutable experiment configurations
* [ ] Maintain experiment IDs
* [ ] Generate execution queues
* [ ] Record decision reasons
* [ ] Handle deferred/rejected configurations
* [ ] Produce a reproducible experiment plan

---

# 40. The Nine-Phase Architecture

```text
                    DATASET
                       ↓
                 ┌───────────┐
                 │ PHASE 1   │
                 │ INGESTION │
                 └─────┬─────┘
                       ↓
                 ┌───────────┐
                 │ PHASE 2   │
                 │ PROFILING  │
                 └─────┬─────┘
                       ↓
                 ┌───────────┐
                 │ PHASE 3   │
                 │ VALIDATION │
                 └─────┬─────┘
                       ↓
                 ┌───────────┐
                 │ PHASE 4   │
                 │ PREPROCESS │
                 └─────┬─────┘
                       ↓
                 ┌───────────┐
                 │ PHASE 5   │
                 │ FEATURE    │
                 │ ENGINEERING│
                 └─────┬─────┘
                       ↓
                 ┌───────────┐
                 │ PHASE 6   │
                 │ SELECTION  │
                 │ / REDUCTION│
                 └─────┬─────┘
                       ↓
              ┌────────┴─────────┐
              ↓                  ↓
        ┌───────────┐      ┌───────────┐
        │ PHASE 7   │      │ PHASE 8   │
        │ CLASSICAL │      │ QUANTUM   │
        │ MODELS    │      │ MODELS    │
        └─────┬─────┘      └─────┬─────┘
              │                  │
              └────────┬─────────┘
                       ↓
                ┌─────────────┐
                │  PHASE 9    │
                │ EXPERIMENT  │
                │ PLANNER     │
                └──────┬──────┘
                       ↓
                   PHASE 10
                 EXECUTION
```

---

## The most important idea of Phase 9

This is where our original **"hybrid rule-based/agentic system"** idea becomes concrete:

```text
Dataset
   ↓
Profile
   ↓
Rules understand the situation
   ↓
Feature representation selected
   ↓
Classical candidates identified
   ↓
Quantum candidates identified
   ↓
Resource constraints checked
   ↓
Experiments ranked
   ↓
Experiment plan generated
   ↓
Execution
```

And later we can put an agent on top:

```text
                AGENT
                  ↓
        ┌───────────────────┐
        │ Experiment Planner│
        └─────────┬─────────┘
                  ↓
          Rule Engine
                  ↓
       Model / Feature Registry
                  ↓
        Experiment Queue
```

**The agent suggests and orchestrates; the deterministic pipeline validates and executes.**

That separation will make the eventual platform much more reliable, reproducible, and defensible in the SIH presentation.
