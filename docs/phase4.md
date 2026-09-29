# PHASE 4 — Preprocessing Pipeline

## 1. Purpose

Phase 3 told us:

> **"What is wrong with the dataset and is it usable?"**

Phase 4 now answers:

> **"How should we transform the validated dataset into a clean, model-ready dataset without causing data leakage?"**

This is the first phase where the system **actually changes the data**—but importantly, it never overwrites the original dataset.

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
┌──────────────────────────────────────┐
│ PHASE 4                              │
│ PREPROCESSING PIPELINE               │
└──────────────────┬───────────────────┘
                   ↓
PHASE 5
Feature Engineering
```

---

# 3. Core Principle

Phase 4 should **not have one fixed preprocessing pipeline**.

This is important because our platform is supposed to work with different biomedical datasets.

For example:

### Dataset A

```text
Tabular
20,000 samples
32 features
2% missing
categorical columns
```

may require:

```text
Imputation
Encoding
Scaling
```

### Dataset B

```text
Skin images
10,000 images
224×224
RGB
```

may require:

```text
Resize
Normalization
Image augmentation
```

### Dataset C

```text
Image + clinical data
```

may require preprocessing for **both modalities**.

Therefore Phase 4 should have a:

> **Preprocessing Decision Engine**

that uses the Phase 2 profile + Phase 3 validation report to construct an appropriate pipeline.

---

# 4. Input

Phase 4 receives:

```text
dataset_id
+
dataset_profile
+
validation_report
```

Example:

```text
Dataset:
DS-000001

Modality:
TABULAR

Task:
Binary Classification

Target:
disease

Issues:
1.7% missing
2.64:1 imbalance
categorical features
potential outliers
```

---

# 5. Phase 4 High-Level Flow

```text
                DATASET
                   │
                   ▼
          Dataset Profile
                   │
                   +
          Validation Report
                   │
                   ▼
       ┌───────────────────────┐
       │ Preprocessing         │
       │ Decision Engine       │
       └───────────┬───────────┘
                   │
                   ▼
             Preprocessing
             Plan Generated
                   │
                   ▼
             Data Splitting
                   │
          ┌────────┴────────┐
          ▼                 ▼
       TRAIN             TEST
          │                 │
          ▼                 │
   Fit preprocessing        │
          │                 │
          ▼                 │
    Transform TRAIN         │
                            │
                            ▼
                     Transform TEST
                   using TRAIN-fitted
                     transformations
                            │
                            ▼
                    Processed Dataset
```

The train/test boundary is **extremely important**.

---

# 6. First Decision — Split Before Learning Transformations

We must avoid this mistake:

```text
❌ WRONG

Entire dataset
      ↓
Calculate mean
      ↓
Normalize
      ↓
Split train/test
```

This leaks information from the test set into training.

Instead:

```text
✅ CORRECT

Raw validated dataset
        ↓
Train/Test Split
        ↓
     TRAIN
        ↓
Fit preprocessing
        ↓
Transform TRAIN
        ↓
Use same fitted transformations
        ↓
Transform TEST
```

This becomes one of the platform's core reproducibility rules.

---

# 7. Module 4.1 — Preprocessing Decision Engine

This module decides **what preprocessing operations are necessary**.

It receives:

```text
Dataset Profile
+
Validation Report
```

Example:

```text
Numerical features = 26
Categorical = 7
Missing = 1.7%
Class imbalance = moderate
```

It produces:

```text
Preprocessing Plan
```

Example:

```json
{
  "split": {
    "strategy": "stratified"
  },

  "missing_values": {
    "numerical": "median",
    "categorical": "most_frequent"
  },

  "categorical": {
    "encoding": "one_hot"
  },

  "numerical": {
    "scaling": "standard"
  },

  "imbalance": {
    "strategy": "class_weight"
  }
}
```

This plan is **recorded before execution**.

---

# 8. Why We Need a Plan

We don't want:

```text
Python code
   ↓
random preprocessing
```

We want:

```text
Dataset
   ↓
Profile
   ↓
Validation
   ↓
Preprocessing Plan
   ↓
Execution
```

Then the experiment can later say:

```text
This model was trained using:

Median imputation
One-hot encoding
Standard scaling
Stratified 80/20 split
Class weighting
```

This is essential for comparing:

```text
Classical model
vs
Quantum model
```

fairly.

---

# 9. Module 4.2 — Dataset Splitting

For supervised disease detection, we need:

```text
Training
Validation
Test
```

Example:

```text
70% TRAIN
15% VALIDATION
15% TEST
```

Or:

```text
80% TRAIN
20% TEST
```

depending on the experiment.

The split strategy should depend on the dataset.

---

# 10. Stratification

For classification:

```text
Healthy = 72%
Disease = 28%
```

we generally want the splits to preserve approximately the same class proportions.

So the system may choose:

```text
stratified split
```

rather than a completely random split.

---

# 11. Patient-Level Splitting

For medical datasets, this is even more important.

Suppose:

```text
Patient A
 ├── image 1
 ├── image 2
 └── image 3
```

We must avoid:

```text
TRAIN:
image 1
image 2

TEST:
image 3
```

Instead:

```text
Patient A
    ↓
TRAIN
```

or:

```text
Patient A
    ↓
TEST
```

as a whole.

Therefore Phase 4 reads the Phase 3 leakage/split assessment.

If patient identifiers exist:

```text
split_strategy = GROUPED_BY_PATIENT
```

---

# 12. Module 4.3 — Missing Value Handling

Phase 3 may have reported:

```text
cholesterol:
3.2% missing
```

Phase 4 decides how to handle it.

### Numerical

Possible strategies:

```text
Median
Mean
Model-based imputation
```

For a robust first implementation:

```text
Median
```

is a good default.

---

### Categorical

Possible:

```text
Most frequent
Explicit "Unknown"
```

---

# 13. Important: Fit Imputation Only on Training Data

Correct:

```text
TRAIN
 ↓
calculate median
 ↓
fit imputer
 ↓
transform TRAIN
 ↓
transform TEST using same imputer
```

Not:

```text
TRAIN + TEST
 ↓
calculate median
```

because that leaks test information.

---

# 14. Module 4.4 — Categorical Encoding

Biomedical datasets often contain:

```text
sex
smoking_status
family_history
blood_group
```

Machine-learning models need numerical representations.

Possible approaches:

### One-hot encoding

```text
sex

Male
Female
```

becomes:

```text
sex_Male
sex_Female
```

---

### Ordinal encoding

Only when categories genuinely have an order.

For example:

```text
Low
Medium
High
```

could become:

```text
0
1
2
```

We should **not automatically ordinal-encode arbitrary categories**, because that can create a false numerical relationship.

---

# 15. Module 4.5 — Numerical Scaling

This is particularly important for our QML system.

Suppose:

```text
age:             18–90
cholesterol:     100–500
income:          20,000–2,000,000
```

Their numerical scales are very different.

Possible scaling:

```text
StandardScaler
MinMaxScaler
RobustScaler
```

For the initial system:

```text
Standard scaling
```

can be the default for classical models.

But for quantum models, we may eventually require a specific range such as:

```text
[-1, 1]
```

or:

```text
[0, π]
```

depending on the chosen quantum encoding.

**Do not hard-code quantum scaling into generic preprocessing yet.**

That decision belongs partly to Phase 6/8 when we know the feature representation and quantum encoding.

---

# 16. Module 4.6 — Outlier Handling

Phase 3 may say:

```text
Potential outliers detected.
```

Phase 4 can decide whether to:

```text
Keep
Clip
Transform
Remove
```

But we should be conservative.

In medical data:

> An unusual measurement is not automatically an error.

Therefore the initial default should usually be:

```text
Keep outliers
```

unless there is strong evidence they are invalid.

---

# 17. Module 4.7 — Duplicate Handling

Phase 3 may have found:

```text
17 duplicate rows
```

Phase 4 decides how to handle them.

Possible strategy:

```text
Remove exact duplicates
```

But this should happen **after considering whether duplicates represent legitimate repeated measurements**.

For the first tabular benchmark datasets, exact duplicate rows can generally be removed from the training pool, with the operation recorded.

---

# 18. Module 4.8 — Class Imbalance Handling

Suppose:

```text
Healthy = 72%
Disease = 28%
```

The system should not automatically use SMOTE.

Possible strategies:

```text
Class weights
Oversampling
Undersampling
SMOTE
Threshold adjustment
```

For the initial platform:

> **Class weighting should be preferred as a low-risk baseline for many tabular classification experiments.**

Why?

It doesn't synthetically create medical samples.

For example:

```text
Disease
↓
higher training loss weight
```

The actual strategy can later be selected experimentally.

---

# 19. Image Preprocessing

If Phase 2 says:

```text
modality = IMAGE
```

the preprocessing branch changes.

```text
Image Dataset
     ↓
Resize
     ↓
Normalize
     ↓
Optional augmentation
     ↓
Model-ready images
```

---

# 20. Image Resize

Suppose:

```text
Image 1 = 600×450
Image 2 = 1024×768
Image 3 = 224×224
```

The model may require:

```text
224×224
```

So Phase 4 standardizes dimensions.

---

# 21. Image Normalization

Pixel values:

```text
0–255
```

may become:

```text
0–1
```

or use model-specific normalization.

The chosen transformation is recorded in the preprocessing plan.

---

# 22. Image Augmentation

Possible:

```text
rotation
horizontal flip
crop
brightness adjustment
zoom
```

But this is a biomedical system.

We should **not blindly apply arbitrary augmentation**.

For example, if a transformation changes clinically relevant structure, it may be inappropriate.

So augmentation should be:

```text
dataset/model-specific
```

and configurable.

---

# 23. Multimodal Preprocessing

Suppose:

```text
Clinical data
+
Skin image
```

We preprocess separately:

```text
                 Dataset
                    |
          ┌─────────┴─────────┐
          ↓                   ↓
     Clinical Data          Images
          ↓                   ↓
   Missing handling       Resize
   Encoding               Normalize
   Scaling                Augmentation
          ↓                   ↓
          └─────────┬─────────┘
                    ↓
             Ready for fusion
```

Actual fusion belongs later.

---

# 24. Preprocessing Pipeline Object

Every preprocessing run should create a **pipeline definition**.

Example:

```json
{
  "pipeline_id": "PREP-000001",

  "dataset_id": "DS-000001",

  "split": {
    "strategy": "stratified",
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
    "random_seed": 42
  },

  "numerical": {
    "imputation": "median",
    "scaling": "standard"
  },

  "categorical": {
    "encoding": "one_hot",
    "imputation": "most_frequent"
  },

  "imbalance": {
    "strategy": "class_weight"
  },

  "outliers": {
    "strategy": "keep"
  }
}
```

---

# 25. Reproducibility

Every preprocessing run must have:

```text
pipeline_id
dataset_id
configuration
random seed
software version
timestamp
```

Example:

```text
PREP-000001
DS-000001
seed = 42
```

Then if we obtain:

```text
Classical accuracy = 91.4%
Quantum accuracy = 90.8%
```

we know they were evaluated on the same preprocessing version.

---

# 26. Data Lineage

We should create:

```text
RAW DATA
   │
   └── DS-000001
          │
          ▼
      PROFILE
          │
          ▼
      VALIDATION
          │
          ▼
      PREPROCESSING
          │
          ▼
   PREP-000001
```

The original data remains untouched.

---

# 27. Output Storage

Example:

```text
datasets/
│
└── DS-000001/
    │
    ├── raw/
    │   └── original.csv
    │
    ├── profile/
    │   └── profile_v1.json
    │
    ├── validation/
    │   └── validation_v1.json
    │
    └── processed/
        └── PREP-000001/
            ├── train/
            ├── validation/
            ├── test/
            └── preprocessing.json
```

---

# 28. What Phase 4 Outputs

The most important output is:

```text
PREPROCESSED DATASET
```

plus:

```text
PREPROCESSING PIPELINE DEFINITION
```

Example:

```text
Dataset:
DS-000001

Preprocessing:
PREP-000001

Status:
READY_FOR_FEATURE_ENGINEERING
```

---

# 29. Phase 4 Does NOT Do

This boundary is extremely important.

Phase 4 does **not**:

* choose XGBoost
* choose Random Forest
* choose SVM
* choose VQC
* choose QSVM
* choose number of qubits
* select final features
* perform PCA specifically for quantum encoding
* train models
* compare quantum vs classical

Those are later phases.

---

# 30. Why Feature Engineering Is Separate

Suppose we have:

```text
age
systolic_bp
diastolic_bp
```

Feature engineering could create:

```text
pulse_pressure =
systolic_bp - diastolic_bp
```

That's not generic cleaning.

That's **creating a new predictive representation**.

Therefore:

```text
Phase 4:
Make data clean and consistent.

Phase 5:
Make the representation more informative.
```

---

# 31. Phase 4 Architecture

```text
                  PROFILE
                     +
                VALIDATION
                     |
                     v
        ┌────────────────────────┐
        │ Preprocessing Decision │
        │ Engine                 │
        └───────────┬────────────┘
                    |
                    v
          Preprocessing Plan
                    |
                    v
             Dataset Split
                    |
          ┌─────────┴─────────┐
          ↓                   ↓
       TRAIN                TEST
          |
          v
   Fit Transformers
          |
          v
 Transform TRAIN
          |
          +
          |
          └───────────────┐
                          ↓
                 Transform VALIDATION
                          |
                          ↓
                    Transform TEST
                          |
                          v
                 PROCESSED DATA
                          |
                          v
                    PHASE 5
```

---

# 32. Phase 4 Example — Heart Disease

### Input

```text
20,000 samples

26 numerical
7 categorical

1.7% missing

72/28 class distribution
```

### Decision engine

Creates:

```text
Stratified split
Median numerical imputation
Most-frequent categorical imputation
One-hot encoding
Standard scaling
Class weighting
Keep statistical outliers
```

### Output

```text
TRAIN
14,000 samples

VALIDATION
3,000 samples

TEST
3,000 samples
```

with transformed feature matrices ready for Phase 5.

---

# 33. Phase 4 Example — Skin Cancer

Input:

```text
10,000 JPG images
224×224
benign / malignant
```

Decision engine:

```text
Patient-level split if patient IDs exist
Resize if needed
Model-compatible normalization
Controlled augmentation on training only
```

Output:

```text
TRAIN
VALIDATION
TEST
```

with the transformation configuration recorded.

---

# 34. The Most Important Rule for Augmentation

Never augment validation/test data like training data.

Correct:

```text
TRAIN
 ↓
augmentation
 ↓
model
```

Validation:

```text
VALIDATION
 ↓
normalization
 ↓
model
```

Test:

```text
TEST
 ↓
normalization
 ↓
model
```

No random training augmentation should leak into evaluation.

---

# 35. Phase 4 Success Criteria

We should consider Phase 4 complete when the system can:

* [ ] Generate a preprocessing plan
* [ ] Split data appropriately
* [ ] Perform stratified splitting
* [ ] Support patient/group-level splitting where necessary
* [ ] Handle missing values
* [ ] Encode categorical variables
* [ ] Scale numerical features
* [ ] Handle exact duplicates according to the validation decision
* [ ] Handle class imbalance according to the selected strategy
* [ ] Process image datasets
* [ ] Keep test data isolated
* [ ] Fit transformations only on training data
* [ ] Preserve original data
* [ ] Save preprocessing configuration
* [ ] Produce reproducible processed datasets
* [ ] Produce a `PREP-*` pipeline ID
* [ ] Hand off model-ready data to Phase 5

---

# 36. Final Boundary

The first four phases now have very clean responsibilities:

```text
┌──────────────────────────────────────┐
│ PHASE 1                              │
│ INGESTION                            │
│                                      │
│ What did the user give us?          │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│ PHASE 2                              │
│ PROFILING                            │
│                                      │
│ What is inside it?                  │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│ PHASE 3                              │
│ VALIDATION                           │
│                                      │
│ Can we safely/usefully use it?      │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│ PHASE 4                              │
│ PREPROCESSING                        │
│                                      │
│ How do we make it model-ready?      │
└──────────────────┬───────────────────┘
                   ↓
              PHASE 5
         FEATURE ENGINEERING
```

**The key Phase 4 output is not just a cleaned dataset. It is a `Preprocessing Plan + Reproducible Processed Dataset`.** That distinction will become very important when we later run the *same* processed data through classical and quantum models for a fair comparison.
