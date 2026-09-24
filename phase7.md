# PHASE 7 — Classical Model Selection & Baseline Training

## 1. Purpose

Phase 6 produced the feature representations.

Phase 7 now establishes the **classical machine-learning baseline**.

The central question is:

> **"How well can conventional machine-learning methods solve this disease-detection problem using the available data and representations?"**

This baseline is absolutely essential because our problem statement explicitly requires us to benchmark the hybrid quantum-classical approach against **purely classical models**.

We cannot meaningfully claim that QML is useful unless we know what strong classical models can already achieve on the **same problem**.

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
Feature Selection & Dimensionality Reduction
        ↓
┌────────────────────────────────────────────┐
│ PHASE 7                                    │
│ CLASSICAL MODEL SELECTION & BASELINE       │
│ TRAINING                                   │
└────────────────────┬───────────────────────┘
                     │
                     ├───────────────┐
                     ↓               ↓
               PHASE 8           PHASE 9
            Quantum Model      Experiment
             Selection         Planning
```

---

# 3. Why Phase 7 Exists

Our final system needs to answer something like:

```text
Classical ML:
Accuracy = 92.4%
Recall = 91.2%
AUC = 94.1%

Hybrid QML:
Accuracy = 91.8%
Recall = 93.0%
AUC = 94.7%
```

Without the classical numbers, the quantum numbers mean almost nothing.

Therefore:

> **Classical ML is not a side feature of the platform. It is the reference point against which the quantum approach is evaluated.**

---

# 4. Core Principle

We should not compare:

```text
weak classical model
vs
carefully tuned quantum model
```

because that would make the comparison unfair.

Instead:

```text
Same dataset
Same target
Same data split
Same preprocessing
Comparable feature representation
        ↓
Classical model
        vs
Quantum model
```

Phase 7 establishes the classical side of that comparison.

---

# 5. Input

Phase 7 receives:

```text
dataset_id
+
validation_report
+
preprocessing_pipeline
+
feature_engineering_pipeline
+
representation(s)
```

For example:

```text
Dataset:
DS-000001

Preprocessing:
PREP-000001

Feature engineering:
FE-000001

Representations:
REP-001 → 20 features
QREP-001 → 8 features
QREP-002 → 16 features
```

---

# 6. High-Level Flow

```text
                REPRESENTATIONS
                      |
                      v
             ┌──────────────────┐
             │ Classical Model  │
             │ Candidate Engine  │
             └────────┬─────────┘
                      |
                      v
        ┌─────────────────────────────┐
        │ Candidate Classical Models  │
        └──────────────┬──────────────┘
                       |
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Logistic       SVM        Tree Models
      Regression                  / Boosting
          |            |            |
          └────────────┼────────────┘
                       ↓
               Training / Validation
                       ↓
                Model Evaluation
                       ↓
               Model Comparison
                       ↓
              Baseline Selection
                       ↓
               CLASSICAL BASELINE
                       ↓
                   PHASE 9
```

---

# 7. Module 7.1 — Identify ML Task

Phase 2 already proposed a task.

Phase 3 validated it.

Phase 7 uses that information.

Example:

```text
Target:
disease

Task:
Binary Classification
```

Therefore candidate models might include:

```text
Logistic Regression
SVM
Random Forest
Gradient Boosting
XGBoost
```

For regression:

```text
Linear Regression
Random Forest Regressor
Gradient Boosting Regressor
```

For multiclass classification:

```text
Logistic Regression
Random Forest
SVM
Gradient Boosting
```

---

# 8. Initial Model Registry

We should maintain a controlled registry.

Example:

```text
CLASSICAL MODELS

C-001
Logistic Regression

C-002
Random Forest

C-003
SVM

C-004
Gradient Boosting

C-005
XGBoost
```

Each model has metadata:

```text
model_id
model_type
supported_tasks
hyperparameters
resource requirements
```

---

# 9. Why Multiple Classical Models?

Because there is no universally best classical algorithm.

For example:

### Logistic Regression

Good baseline for:

```text
linear relationships
interpretable coefficients
```

### SVM

Potentially useful for:

```text
high-dimensional feature spaces
smaller datasets
```

### Random Forest

Useful for:

```text
nonlinear relationships
mixed feature types
```

### Gradient Boosting / XGBoost

Often strong for:

```text
structured/tabular data
nonlinear interactions
```

The system should test several reasonable candidates rather than arbitrarily choosing one.

---

# 10. Module 7.2 — Model Compatibility

Not every model is appropriate for every dataset.

Example:

```text
Image
 ↓
Raw pixels
```

should not necessarily go directly into:

```text
Logistic Regression
```

Instead, our Phase 5/6 representation might be:

```text
Image
 ↓
CNN embedding
 ↓
Feature reduction
 ↓
Classical classifier
```

Similarly:

```text
Tabular
 ↓
20 engineered features
 ↓
Classical classifier
```

So Phase 7 uses the **representations produced by Phase 6**.

---

# 11. Module 7.3 — Baseline First

Before hyperparameter tuning, we need a simple baseline.

Example:

```text
Logistic Regression
default/configured parameters
```

Then:

```text
Random Forest
default/configured parameters
```

Then:

```text
SVM
default/configured parameters
```

This gives us a first estimate.

Example:

```text
Model               AUC

Logistic Regression 0.88
Random Forest       0.91
SVM                 0.90
XGBoost             0.93
```

---

# 12. Why Baseline Before Optimization?

Suppose we immediately tune XGBoost for 3 hours and obtain:

```text
AUC = 0.94
```

We don't know whether that improvement was worth the computational cost.

Instead:

```text
Baseline XGBoost:
0.91

Tuned XGBoost:
0.94
```

Now we know the tuning produced:

```text
+0.03 AUC
```

This becomes important later when we compare:

```text
performance
vs
computation
vs
cost
```

---

# 13. Module 7.4 — Training

Training should happen only on:

```text
TRAIN
```

Example:

```text
TRAIN
 ↓
Classical Model
 ↓
Learn parameters
```

Validation:

```text
VALIDATION
 ↓
Model evaluation
```

Test:

```text
TEST
 ↓
FINAL evaluation only
```

The test set should remain untouched during model selection.

---

# 14. Module 7.5 — Cross-Validation

For many tabular datasets, we can use:

```text
Stratified K-Fold Cross Validation
```

Example:

```text
5-fold CV

Fold 1
Fold 2
Fold 3
Fold 4
Fold 5
```

Output:

```text
AUC:
0.91
0.93
0.92
0.90
0.92

Mean:
0.916

Std:
0.011
```

This gives us a more stable estimate than a single split.

---

# 15. Patient-Level Cross-Validation

If the dataset contains multiple records per patient, ordinary K-fold can leak information.

Instead:

```text
Patient A
Patient B
Patient C
...
```

must remain grouped.

So Phase 7 reads the split strategy from Phase 4.

If Phase 4 says:

```text
group = patient_id
```

then Phase 7 uses a compatible group-aware validation strategy.

---

# 16. Module 7.6 — Evaluation Metrics

Because this is **disease detection**, accuracy alone is not enough.

We should calculate:

### Accuracy

```text
correct predictions
-------------------
total predictions
```

---

### Precision

Of the cases predicted as disease:

> How many actually had disease?

---

### Recall / Sensitivity

Of the actual disease cases:

> How many did we detect?

This is especially important for **early disease detection**.

---

### Specificity

Of the healthy cases:

> How many did we correctly identify as healthy?

---

### F1 Score

Balances:

```text
precision
+
recall
```

---

### ROC-AUC

Measures discrimination across classification thresholds.

---

### PR-AUC

Especially useful when disease prevalence is low / classes are imbalanced.

---

# 17. Example

Suppose:

```text
1000 patients

900 healthy
100 disease
```

Model:

```text
Accuracy = 95%
```

That sounds good.

But suppose:

```text
Disease detected:
40 / 100
```

Then:

```text
Recall = 40%
```

That's potentially unacceptable for an early-detection system.

Therefore the platform should prominently report:

```text
Sensitivity
Specificity
AUC
```

not only accuracy.

---

# 18. Confusion Matrix

For binary classification:

```text
                    PREDICTED
                  Healthy Disease

ACTUAL Healthy      TN       FP
       Disease      FN       TP
```

From this:

```text
Sensitivity = TP / (TP + FN)

Specificity = TN / (TN + FP)

Precision = TP / (TP + FP)
```

This becomes a major output of Phase 7.

---

# 19. Module 7.7 — Hyperparameter Search

Once baseline models are established, the system can perform controlled tuning.

Example for Random Forest:

```text
n_estimators:
100
300
500

max_depth:
5
10
20

min_samples_split:
2
5
10
```

For SVM:

```text
C
gamma
kernel
```

For XGBoost:

```text
learning_rate
max_depth
n_estimators
subsample
```

---

# 20. Important: Don't Exhaustively Search Everything

Our project also needs to evaluate:

```text
Quantum computation
Classical computation
Cost
Scalability
```

If we spend huge amounts of compute tuning classical models, the comparison becomes inefficient.

Therefore we should initially use:

```text
small controlled search
```

and only expand it if justified.

---

# 21. Model Selection Objective

We should not select the classical model using:

```text
Accuracy only
```

Instead use a configurable objective.

For disease detection:

```text
Primary:
Recall / Sensitivity
```

with:

```text
Secondary:
Specificity
ROC-AUC
PR-AUC
F1
Accuracy
```

The exact priority should depend on the disease/task.

---

# 22. Multi-Objective Model Evaluation

We can think of every model as:

```text
Model
 ↓
Performance
 ↓
Compute
 ↓
Memory
 ↓
Training time
 ↓
Inference time
```

Example:

```text
Model        AUC    Recall   Train Time

Logistic     0.88   0.84     2 sec
RandomForest 0.91   0.89     8 sec
XGBoost      0.93   0.92     42 sec
```

Later Phase 13 can add:

```text
quantum cost
cloud cost
energy/resource estimates
```

---

# 23. Module 7.8 — Resource Measurement

For each classical experiment, record:

```text
training time
inference time
CPU usage
RAM usage
model size
number of parameters
```

Example:

```json
{
  "model_id": "C-005",
  "training_time_seconds": 42.8,
  "inference_time_ms": 4.2,
  "memory_mb": 382,
  "model_size_mb": 12.4
}
```

This will become important when comparing the classical and quantum approaches.

---

# 24. Module 7.9 — Reproducibility

Every experiment receives an ID.

Example:

```text
EXP-C-000001
```

Store:

```text
dataset_id
preprocessing_id
feature_representation_id
model_id
hyperparameters
random_seed
training configuration
metrics
resource usage
```

So we can reproduce:

```text
XGBoost
+
REP-001
+
PREP-000001
```

later.

---

# 25. Classical Model Registry

After training:

```text
C-001 Logistic Regression
C-002 Random Forest
C-003 SVM
C-004 Gradient Boosting
C-005 XGBoost
```

The system records their results.

Example:

| Model               | Accuracy | Recall | Specificity | ROC-AUC |
| ------------------- | -------: | -----: | ----------: | ------: |
| Logistic Regression |    88.2% |  84.1% |       89.5% |    0.90 |
| Random Forest       |    90.1% |  88.3% |       90.7% |    0.92 |
| SVM                 |    89.7% |  86.8% |       91.2% |    0.92 |
| XGBoost             |    92.4% |  91.5% |       92.8% |    0.95 |

---

# 26. Baseline Selection

We should select a **strong classical baseline**, not necessarily the model with the highest raw accuracy.

Example:

```text
XGBoost
```

might be selected because:

```text
High AUC
High sensitivity
Good specificity
Reasonable training cost
```

rather than simply:

```text
Highest accuracy
```

---

# 27. Important: One Classical Baseline vs Classical Benchmark Suite

We should retain **both concepts**.

### Classical benchmark suite

```text
Logistic Regression
Random Forest
SVM
XGBoost
...
```

### Primary classical baseline

```text
Best validated classical model
```

So later we can report:

```text
Classical benchmark:
LR / RF / SVM / XGBoost

Primary baseline:
XGBoost
```

---

# 28. Connection to Quantum Branch

Eventually we want something like:

```text
                   SAME DATASET
                        |
                 SAME TEST SET
                        |
             ┌──────────┴──────────┐
             ↓                     ↓
       Classical Branch       Quantum Branch
             ↓                     ↓
       XGBoost / SVM             VQC / QSVM
             ↓                     ↓
          Metrics               Metrics
             └──────────┬──────────┘
                        ↓
                PHASE 11
              Benchmarking
```

Phase 7 establishes the left side.

---

# 29. Fair Comparison Mode

There should be at least two classical experiment modes.

## Mode A — Best Classical

Use the strongest suitable classical representation:

```text
REP-001
20 features
        ↓
XGBoost
```

This tells us:

> What can conventional ML achieve in the best practical setup?

---

## Mode B — Quantum-Matched Classical

Suppose quantum uses:

```text
QREP-001
8 features
```

We also run:

```text
QREP-001
   ↓
Classical XGBoost / SVM / Logistic Regression
```

Now:

```text
Same representation
Same data
Same target
Same split
```

and compare:

```text
Classical
vs
Quantum
```

This is essential for scientific credibility.

---

# 30. Example

Suppose:

### Best classical

```text
XGBoost
20 features

Accuracy = 93%
Recall = 92%
AUC = 95%
```

### Same 8-feature representation

```text
XGBoost
8 features

Accuracy = 89%
Recall = 87%
AUC = 91%
```

### Quantum

```text
VQC
8 features

Accuracy = 90%
Recall = 89%
AUC = 92%
```

Now we can make two conclusions:

1. XGBoost is the strongest practical classical solution.
2. On the same compact representation, VQC slightly outperforms XGBoost.

That's much more meaningful than simply saying:

> "Quantum achieved 90%."

---

# 31. What Phase 7 Does NOT Do

Phase 7 does **not**:

* choose the quantum algorithm
* design quantum circuits
* determine qubit count
* run quantum hardware
* claim quantum advantage
* compare final quantum/classical performance
* calculate quantum cost
* perform explainability
* make the final system recommendation

Those happen later.

---

# 32. Phase 7 Output

The primary output:

```text
CLASSICAL BASELINE PACKAGE
```

containing:

```text
Best classical model
+
benchmark model results
+
metrics
+
resource usage
+
configuration
+
model artifact
```

Example:

```json
{
  "dataset_id": "DS-000001",

  "baseline_experiment": "EXP-C-000005",

  "model": "XGBoost",

  "representation": "REP-001",

  "metrics": {
    "accuracy": 0.924,
    "recall": 0.915,
    "specificity": 0.928,
    "roc_auc": 0.95,
    "pr_auc": 0.91
  },

  "resources": {
    "training_time_seconds": 42.8,
    "inference_time_ms": 4.2,
    "memory_mb": 382
  },

  "status": "BASELINE_READY"
}
```

---

# 33. Model Lineage

We should be able to trace:

```text
DS-000001
      ↓
PREP-000001
      ↓
FE-000001
      ↓
REP-001
      ↓
XGBoost
      ↓
EXP-C-000005
      ↓
Baseline Results
```

This is important because later, when someone asks:

> "How did you get 92.4%?"

we can trace the entire pipeline.

---

# 34. Phase 7 Architecture

```text
                   PHASE 6
                REPRESENTATIONS
                       |
                       v
             ┌──────────────────┐
             │ Model Registry   │
             └────────┬─────────┘
                      |
          ┌───────────┼────────────┐
          ↓           ↓            ↓
       Logistic      SVM       Tree/Boosting
          |           |            |
          └───────────┼────────────┘
                      ↓
             ┌──────────────────┐
             │ Training Engine  │
             └────────┬─────────┘
                      |
                      v
             ┌──────────────────┐
             │ Validation / CV  │
             └────────┬─────────┘
                      |
                      v
             ┌──────────────────┐
             │ Metrics Engine   │
             └────────┬─────────┘
                      |
                      v
             ┌──────────────────┐
             │ Resource         │
             │ Measurement      │
             └────────┬─────────┘
                      |
                      v
             ┌──────────────────┐
             │ Model Ranking     │
             └────────┬─────────┘
                      |
                      v
              CLASSICAL BASELINE
                      |
                      ↓
                  PHASE 11
```

---

# 35. Phase 7 Success Criteria

Phase 7 is complete when we can:

* [ ] Identify the ML task
* [ ] Load appropriate classical model candidates
* [ ] Maintain a classical model registry
* [ ] Train baseline models
* [ ] Perform appropriate cross-validation
* [ ] Respect patient/group-level splitting
* [ ] Perform controlled hyperparameter tuning
* [ ] Calculate accuracy
* [ ] Calculate precision
* [ ] Calculate recall/sensitivity
* [ ] Calculate specificity
* [ ] Calculate F1
* [ ] Calculate ROC-AUC
* [ ] Calculate PR-AUC where appropriate
* [ ] Generate confusion matrices
* [ ] Measure training/inference time
* [ ] Measure memory/model size
* [ ] Store reproducible experiment configurations
* [ ] Select a primary classical baseline
* [ ] Preserve benchmark results for all candidate models
* [ ] Produce a quantum-matched classical baseline
* [ ] Store model artifacts and lineage

---

# 36. The Seven-Phase Boundary

```text
PHASE 1
"What did we receive?"
        ↓
INGESTION

PHASE 2
"What is inside?"
        ↓
PROFILING

PHASE 3
"Can we use it?"
        ↓
VALIDATION

PHASE 4
"How do we clean/prepare it?"
        ↓
PREPROCESSING

PHASE 5
"What useful information can we represent?"
        ↓
FEATURE ENGINEERING

PHASE 6
"Which representation should we use?"
        ↓
FEATURE SELECTION / REDUCTION

PHASE 7
"How well can classical ML solve it?"
        ↓
CLASSICAL BASELINE

PHASE 8
"How should the quantum model solve it?"
```

## The key output of Phase 7

```text
                  DATASET
                     ↓
             Classical Benchmark
                     ↓
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
      LR             SVM        XGBoost
       ↓             ↓             ↓
     Metrics       Metrics       Metrics
       └─────────────┼─────────────┘
                     ↓
           BEST CLASSICAL BASELINE
                     +
          QUANTUM-MATCHED BASELINE
```

This gives us the **reference line** that Phase 8's quantum models must beat—or, if they don't beat it, the system must honestly report that and evaluate whether they offer some other advantage such as sensitivity, resource profile, or scalability.
