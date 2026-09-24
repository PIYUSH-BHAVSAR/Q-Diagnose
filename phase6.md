# PHASE 6 — Feature Selection & Dimensionality Reduction

## 1. Purpose

Phase 5 produced a potentially useful feature representation.

Phase 6 now answers the critical question:

> **"Which features should actually be given to our models, and how many can we keep without losing important information?"**

This is the phase where the **classical and quantum requirements begin to diverge**.

The quantum branch has an additional constraint:

> Current quantum simulators and near-term quantum hardware generally work with a relatively small number of qubits, so we cannot simply send a high-dimensional biomedical feature vector directly into a small quantum circuit.

Therefore Phase 6 must create a **compact, information-preserving representation** suitable for downstream experiments.

---

# 2. Position in the System

```text
PHASE 1
Dataset Ingestion & Registration
        ↓
PHASE 2
Dataset Profiling & Discovery
        ↓
PHASE 3
Dataset Validation & Quality Assessment
        ↓
PHASE 4
Preprocessing Pipeline
        ↓
PHASE 5
Feature Engineering
        ↓
┌──────────────────────────────────────────┐
│ PHASE 6                                  │
│ FEATURE SELECTION & DIMENSIONALITY       │
│ REDUCTION                                │
└──────────────────┬───────────────────────┘
                   ↓
PHASE 7
Classical Model Selection & Baseline Training
        +
PHASE 8
Quantum Model Selection & Configuration
```

---

# 3. Core Principle

We should **not assume that fewer features automatically means better performance**.

The objective is:

```text
Keep useful information
        +
Remove irrelevant/redundant information
        +
Control computational complexity
        +
Create a quantum-compatible representation
```

So Phase 6 is an optimization problem:

```text
Information
    ↑
    |
    |       ●
    |     ●
    |   ●
    | ●
    └────────────────→
             Features
```

We want the **smallest useful representation**, not simply the smallest one.

---

# 4. Why This Phase Is Critical for QML

Suppose a skin-cancer image goes through a CNN:

```text
Skin Image
    ↓
MobileNetV2
    ↓
1280-dimensional embedding
```

A quantum circuit with:

```text
8 qubits
```

cannot simply accept all 1280 values as 1280 independent quantum inputs.

We need:

```text
1280 features
       ↓
Feature selection / reduction
       ↓
16 features
       ↓
Quantum-compatible representation
       ↓
Quantum model
```

So Phase 6 acts as the **bridge between classical feature extraction and quantum learning**.

---

# 5. Input

Phase 6 receives:

```text
dataset_id
+
dataset_profile
+
validation_report
+
preprocessing_pipeline
+
feature_engineering_pipeline
+
engineered feature dataset
```

Example:

```text
Dataset:
DS-000001

Preprocessing:
PREP-000001

Feature engineering:
FE-000001

Candidate features:
128
```

---

# 6. Phase 6 High-Level Flow

```text
                ENGINEERED FEATURES
                        |
                        v
             ┌─────────────────────┐
             │ Feature Analysis    │
             └──────────┬──────────┘
                        |
                        v
             ┌─────────────────────┐
             │ Remove Redundant /  │
             │ Invalid Features    │
             └──────────┬──────────┘
                        |
                        v
             ┌─────────────────────┐
             │ Feature Selection   │
             │ Methods             │
             └──────────┬──────────┘
                        |
                        v
             Candidate Feature Sets
                        |
                        v
             ┌─────────────────────┐
             │ Dimensionality      │
             │ Reduction           │
             └──────────┬──────────┘
                        |
                        v
             Multiple Representations
                        |
                        v
             ┌─────────────────────┐
             │ Information /       │
             │ Performance Check   │
             └──────────┬──────────┘
                        |
                        v
             ┌─────────────────────┐
             │ Quantum-Compatible  │
             │ Representation      │
             └──────────┬──────────┘
                        |
                        v
                 FEATURE SETS
                        |
              ┌─────────┴─────────┐
              ↓                   ↓
       Classical Features    Quantum Features
              |                   |
              ↓                   ↓
           PHASE 7             PHASE 8
```

---

# 7. Important Architecture Decision

We should **not create only one feature representation**.

Instead, Phase 6 can produce multiple representations.

For example:

```text
                 Engineered Data
                       |
          ┌────────────┴────────────┐
          ↓                         ↓
   Classical Representation   Quantum Representation
          |                         |
       64 features               8 features
          |                         |
          ↓                         ↓
       Phase 7                  Phase 8
```

This is important because:

> A feature representation that is excellent for a classical model may not be practical for a quantum circuit.

---

# 8. Module 6.1 — Feature Analysis

First, inspect the candidate feature space.

For every feature:

```text
feature_id
feature_name
feature_type
source
variance
target relationship
correlation
missingness
```

Example:

```text
FEAT-001
age
original
numerical

FEAT-032
pulse_pressure
derived

FEAT-081
cnn_embedding_081
deep_embedding
```

---

# 9. Module 6.2 — Remove Obviously Unusable Features

Some features should not enter the model.

Examples:

```text
constant feature
duplicate feature
identifier
leakage feature
invalid feature
```

Example:

```text
patient_id
```

should generally not become a predictive feature.

Output:

```text
128 candidate features
        ↓
119 usable features
```

---

# 10. Module 6.3 — Low-Variance Filtering

Suppose:

```text
feature_A:

0
0
0
0
0
1
0
0
```

This feature may contain very little useful information.

We can calculate variance and flag/remove features below a configurable threshold.

Example:

```text
119 features
        ↓
112 features
```

The threshold must be configurable.

---

# 11. Module 6.4 — Correlation Analysis

Suppose:

```text
systolic_bp
systolic_bp_duplicate
```

are almost perfectly correlated.

Keeping both may add redundancy.

Example:

```text
correlation = 0.99
```

We can flag one as a redundant candidate.

---

# 12. Important Medical Caveat

High correlation does **not automatically mean "delete this feature."**

Two correlated medical measurements may both carry useful information.

Therefore:

```text
Correlation
     ↓
Candidate redundancy signal
```

not:

```text
Correlation
     ↓
Automatically delete
```

The selection strategy should consider downstream model performance and domain context.

---

# 13. Module 6.5 — Univariate Feature Selection

We can evaluate individual features against the target.

Possible methods include:

```text
ANOVA
Chi-square
Mutual information
Correlation-based methods
```

For example:

```text
Feature                MI score

glucose                0.31
BMI                    0.27
age                    0.22
cholesterol            0.18
feature_X              0.01
```

This gives us a ranking.

---

# 14. Module 6.6 — Model-Based Selection

Another approach is to use a classical model to estimate feature importance.

For example:

```text
Random Forest
XGBoost
Logistic Regression
```

could provide:

```text
Feature
   ↓
Importance score
```

Example:

```text
glucose       0.31
BMI           0.21
age           0.18
cholesterol   0.14
...
```

However, **the final model selection belongs to Phase 7**.

Phase 6 can use a lightweight selection method or agreed baseline selector without making the final model decision.

---

# 15. Module 6.7 — Recursive Feature Selection

For certain datasets, we may test:

```text
128 features
 ↓
64
 ↓
32
 ↓
16
 ↓
8
```

and observe how useful the representation remains.

This gives us a curve:

```text
Performance
   ↑
   |             ●
   |          ●
   |       ●
   |    ●
   | ●
   └────────────────────→
       8  16  32  64
          Features
```

The objective is to identify a good **performance/complexity tradeoff**.

---

# 16. Module 6.8 — Dimensionality Reduction

Feature selection keeps original features.

Dimensionality reduction creates a **new compact representation**.

Important distinction:

### Feature selection

```text
100 features
   ↓
Keep 16 original features
```

### Dimensionality reduction

```text
100 features
   ↓
PCA
   ↓
16 new components
```

The components may not directly correspond to individual original medical variables.

---

# 17. PCA

One candidate technique:

```text
Principal Component Analysis
```

Example:

```text
128 features
      ↓
PCA
      ↓
16 components
```

The components preserve as much variance as possible according to PCA.

But:

> PCA is not guaranteed to preserve the information most relevant to disease classification.

Therefore we should not assume PCA is always optimal.

---

# 18. Other Possible Reduction Methods

Depending on the dataset:

```text
PCA
Kernel PCA
Autoencoder
Truncated SVD
Feature selection
Domain-guided reduction
```

For the initial implementation, we should keep the pipeline manageable.

A good starting set is:

```text
Feature Selection
+
PCA
```

and optionally later:

```text
Autoencoder
```

for complex image embeddings.

---

# 19. Why We Should Test Multiple Reduction Sizes

For QML, we might have:

```text
4 features
8 features
12 features
16 features
```

We shouldn't decide:

> "Quantum = 8 features"

without testing.

Instead:

```text
Candidate dimensions:

4
8
12
16
```

can be evaluated.

---

# 20. Quantum-Compatible Representation

This is where Phase 6 becomes specifically important to our project.

Suppose:

```text
CNN embedding
1280 dimensions
```

We might generate:

```text
1280
 ↓
PCA
 ↓
64
 ↓
feature selection
 ↓
16
 ↓
quantum representation
```

The final output could be:

```text
Q-FEAT-000001

dimension = 16
```

This is then passed to Phase 8.

---

# 21. Number of Qubits Is Not Automatically Equal to Number of Features

This is an important point.

Depending on the quantum encoding strategy, the relationship can differ.

For simple angle encoding:

```text
1 feature → approximately 1 qubit
```

so:

```text
8 features
→
8 qubits
```

could be a straightforward design.

But other encodings can represent information differently.

Therefore Phase 6 should produce:

```text
feature_dimension
```

while Phase 8 decides:

```text
encoding_strategy
qubit_configuration
circuit architecture
```

---

# 22. Quantum Branch Example

Suppose Phase 5 produces:

```text
1280 CNN features
```

Phase 6 creates candidate representations:

```text
1280
 ↓
PCA-64
 ↓
PCA-32
 ↓
PCA-16
 ↓
PCA-8
```

Then we may create:

```text
QREP-001 → 8 features
QREP-002 → 16 features
QREP-003 → 32 features
```

Phase 8 can later test which representation works best with the available quantum model/backend.

---

# 23. Classical Branch

We should **not force the classical model to use only 8 features** just because the quantum model does.

For example:

```text
Classical:
64 features

Quantum:
8 features
```

But when comparing models, we need **two comparison modes**.

### Mode A — Best achievable model

```text
Classical → optimized classical representation
Quantum   → optimized quantum representation
```

This answers:

> What is the best practical performance each approach can achieve?

### Mode B — Same representation

```text
Same 8 features
       ↓
Classical model
       +
Quantum model
```

This answers:

> Is the difference actually caused by the learning method rather than feature representation?

This distinction will be **extremely important in Phase 11 benchmarking**.

---

# 24. Avoiding Unfair Quantum Comparisons

Bad comparison:

```text
Classical:
1280 features
Powerful XGBoost

Quantum:
8 features
VQC
```

Then:

```text
Accuracy:
Classical = 94%
Quantum = 84%
```

We cannot conclude:

> "Quantum is worse."

The representations are radically different.

Better:

```text
Same reduced representation
       |
       ├── Classical model
       |
       └── Quantum model
```

and separately:

```text
Best practical classical
vs
Best practical quantum
```

Phase 6 prepares these representations.

---

# 25. Module 6.9 — Representation Evaluation

For each candidate representation:

```text
8 features
16 features
32 features
64 features
```

calculate things such as:

```text
variance retained
feature count
memory requirement
processing requirement
```

and optionally a lightweight downstream evaluation.

The important point:

> **Don't train the entire final experiment here.**

Phase 6 prepares and evaluates candidate representations.

Phase 7/8 handle proper model selection and training.

---

# 26. Quantum Resource Awareness

Each candidate quantum representation should include:

```text
feature_dimension
estimated_qubits
encoding_candidate
circuit_input_size
```

Example:

```json
{
  "representation_id": "QREP-001",
  "dimensions": 8,
  "estimated_qubits": 8,
  "encoding": "angle_encoding_candidate"
}
```

This is **resource metadata**, not yet the final quantum architecture.

---

# 27. Module 6.10 — Information Retention

For PCA:

```text
8 components
→ 82% variance retained

16 components
→ 94% variance retained

32 components
→ 98% variance retained
```

This helps us understand the compression tradeoff.

But remember:

> Higher variance retention does not necessarily mean higher disease-classification performance.

Therefore both should eventually be considered.

---

# 28. Representation Score

We can create a technical score such as:

```text
Representation Score
```

based on:

```text
Information retention
+
feature usefulness
+
dimensionality
+
redundancy
+
quantum compatibility
```

But this should be used as a **decision aid**, not treated as a universal truth.

---

# 29. Phase 6 Decision Engine

The phase can eventually produce:

```text
Candidate Representations

REP-001
64 features
Classical

REP-002
32 features
Classical / Quantum candidate

REP-003
16 features
Quantum candidate

REP-004
8 features
Quantum candidate
```

Then Phase 7 and Phase 8 evaluate them properly.

---

# 30. Feature Registry Extension

Phase 5 created:

```text
FEAT-001
FEAT-002
...
```

Phase 6 should create:

```text
REP-001
REP-002
QREP-001
```

Example:

```json
{
  "representation_id": "QREP-001",

  "source_feature_pipeline": "FE-000001",

  "method": "PCA",

  "input_dimension": 1280,

  "output_dimension": 8,

  "variance_retained": 0.82,

  "target": "disease",

  "intended_use": "quantum_candidate"
}
```

---

# 31. Reproducibility

Every reduction/selection operation must be reproducible.

Record:

```text
representation_id
dataset_id
feature_engineering_id
method
parameters
random_seed
input_dimension
output_dimension
created_at
```

For PCA:

```text
components = 16
seed = 42
```

For feature selection:

```text
method = mutual_information
top_k = 16
```

---

# 32. No Data Leakage

This is critical.

Feature selection must not use the test set.

Correct:

```text
TRAIN
 ↓
calculate feature importance
 ↓
select features
 ↓
transform TRAIN
 ↓
apply same selection to VALIDATION
 ↓
apply same selection to TEST
```

Incorrect:

```text
TRAIN + VALIDATION + TEST
 ↓
feature selection
```

The latter leaks information.

---

# 33. Example — Tabular Dataset

Phase 5:

```text
48 candidate features
```

Phase 6:

```text
Remove:
5 redundant
3 low variance

Remaining:
40
```

Then:

```text
Feature Selection
 ↓
20 useful features
```

Then:

```text
PCA
 ↓
8 components
```

Outputs:

```text
Classical Representation:
20 selected original features

Quantum Representation:
8 PCA components
```

---

# 34. Example — Skin Cancer

Phase 5:

```text
Image
 ↓
MobileNetV2
 ↓
1280 features
```

Phase 6:

```text
1280
 ↓
remove problematic/redundant dimensions if appropriate
 ↓
PCA-64
 ↓
PCA-32
 ↓
PCA-16
 ↓
PCA-8
```

Candidate representations:

```text
REP-IMG-64
REP-IMG-32
REP-IMG-16
REP-IMG-08
```

Phase 8 can later evaluate the quantum candidates.

---

# 35. What Phase 6 Does NOT Do

Phase 6 does **not**:

* choose final classical algorithm
* choose VQC
* choose QSVM
* choose QNN
* decide the final quantum circuit
* execute quantum circuits
* perform final model training
* claim quantum advantage
* compare final model performance
* calculate actual cloud quantum cost

Those belong to later phases.

---

# 36. Phase 6 Outputs

The phase should produce:

### 1. Selected feature representation(s)

```text
REP-001
```

### 2. Quantum candidate representation(s)

```text
QREP-001
QREP-002
```

### 3. Feature/reduction metadata

```text
method
parameters
dimensions
variance retention
lineage
```

### 4. Reproducible transformation pipeline

```text
RED-000001
```

---

# 37. Example Final Output

```json
{
  "dataset_id": "DS-000001",

  "feature_engineering_id": "FE-000001",

  "representations": [
    {
      "id": "REP-001",
      "type": "CLASSICAL",
      "method": "feature_selection",
      "dimension": 20
    },
    {
      "id": "QREP-001",
      "type": "QUANTUM_CANDIDATE",
      "method": "PCA",
      "dimension": 8,
      "estimated_qubits": 8
    },
    {
      "id": "QREP-002",
      "type": "QUANTUM_CANDIDATE",
      "method": "PCA",
      "dimension": 16,
      "estimated_qubits": 16
    }
  ],

  "status": "READY_FOR_MODEL_SELECTION"
}
```

---

# 38. Phase 6 Architecture

```text
                    FEATURE SET
                         |
                         v
              ┌─────────────────────┐
              │ Feature Analyzer    │
              └──────────┬──────────┘
                         |
                         v
              ┌─────────────────────┐
              │ Redundancy /        │
              │ Low-Variance Filter │
              └──────────┬──────────┘
                         |
                         v
              ┌─────────────────────┐
              │ Feature Selection   │
              └──────────┬──────────┘
                         |
                         v
              ┌─────────────────────┐
              │ Dimensionality      │
              │ Reduction           │
              └──────────┬──────────┘
                         |
              ┌──────────┴──────────┐
              ↓                     ↓
      Classical Candidate      Quantum Candidate
      Representations          Representations
              |                     |
              ↓                     ↓
          Phase 7                Phase 8
```

---

# 39. Phase 6 Success Criteria

Phase 6 is complete when the system can:

* [ ] Analyze engineered feature space
* [ ] Detect constant/near-constant features
* [ ] Detect redundant features
* [ ] Identify identifier-like features
* [ ] Perform controlled feature selection
* [ ] Support mutual-information/statistical selection
* [ ] Support model-based selection where appropriate
* [ ] Perform dimensionality reduction
* [ ] Support PCA initially
* [ ] Generate multiple candidate dimensions
* [ ] Create classical feature representations
* [ ] Create quantum-compatible candidate representations
* [ ] Track feature lineage
* [ ] Track reduction lineage
* [ ] Prevent test-set leakage
* [ ] Record reproducible parameters
* [ ] Estimate quantum input dimensions/qubit requirements
* [ ] Produce versioned representations
* [ ] Hand off representations to Phases 7 and 8

---

# 40. The Six-Phase Boundary

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
"Is it usable?"
        ↓
VALIDATION

PHASE 4
"How do we clean and prepare it?"
        ↓
PREPROCESSING

PHASE 5
"What useful information can we represent?"
        ↓
FEATURE ENGINEERING

PHASE 6
"Which representation should actually enter
the models, and how small can we make it?"
        ↓
CLASSICAL BRANCH       QUANTUM BRANCH
        ↓                     ↓
    PHASE 7              PHASE 8
```

### The key QML idea introduced in Phase 6

```text
High-dimensional biomedical data
              ↓
       Classical feature
          extraction
              ↓
      Feature engineering
              ↓
     Selection / reduction
              ↓
    ┌─────────┴──────────┐
    ↓                    ↓
Classical             Quantum
representation        representation
    ↓                    ↓
Many features       Few features
                         ↓
                   Quantum encoding
                         ↓
                    Quantum model
```

This is the point where our **hybrid architecture becomes technically practical** rather than trying to force raw high-dimensional biomedical data directly into a quantum circuit.
