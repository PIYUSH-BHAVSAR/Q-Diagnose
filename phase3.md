# PHASE 3 — Dataset Validation & Quality Assessment

Phase 2 told us:

> **“What appears to be inside this dataset?”**

Phase 3 now asks:

> **“Is this dataset actually valid, usable, and safe for our disease-detection experiment?”**

This phase is where we **verify the assumptions made by Phase 2**.

---

## 1. Position in the pipeline

```text
PHASE 1
Dataset Ingestion & Registration
        ↓
PHASE 2
Dataset Profiling & Discovery
        ↓
┌──────────────────────────────────────┐
│ PHASE 3                              │
│ Dataset Validation & Quality         │
│ Assessment                           │
└──────────────────┬───────────────────┘
                   ↓
PHASE 4
Preprocessing Pipeline
```

---

# 2. Core principle

Phase 3 **detects problems but does not fix them**.

For example:

```text
Missing values = 4.2%
```

Phase 3 says:

> ⚠️ Missing values detected.

It does **not** fill them.

Phase 4 decides:

> Use median imputation.

Similarly:

```text
Class imbalance = 80/20
```

Phase 3 says:

> ⚠️ Moderate imbalance.

Phase 4 decides whether to use:

* class weights
* resampling
* SMOTE
* threshold adjustment

---

# 3. Input

Phase 3 receives:

```text
dataset_id
+
dataset_profile
```

Example:

```text
DS-000001
```

and:

```json
{
  "modality": "TABULAR",
  "rows": 20000,
  "columns": 33,
  "target_candidate": "disease",
  "task_candidate": "BINARY_CLASSIFICATION"
}
```

---

# 4. Phase 3 workflow

```text
Dataset Profile
       ↓
Target Validation
       ↓
Schema Validation
       ↓
Missing Data Assessment
       ↓
Duplicate Assessment
       ↓
Class Balance Assessment
       ↓
Data Type Validation
       ↓
Data Range / Value Validation
       ↓
Leakage Detection
       ↓
Image/Label Alignment* 
       ↓
Train/Test Split Feasibility
       ↓
Dataset Quality Score
       ↓
Validation Report
```

`*` only for image datasets.

---

# 5. Module 3.1 — Target Validation

Phase 2 might say:

```text
Target candidate:
disease
```

Phase 3 verifies it.

### Checks

* Does the column exist?
* Is it populated?
* How many unique values?
* Are the values valid?
* Is it actually predictive-label-like?
* Is it an identifier accidentally being interpreted as a target?

Example:

```text
disease

0 → 14,500
1 → 5,500
```

Result:

```text
TARGET VALID
```

---

# 6. Target failure example

Suppose:

```text
patient_id

10001
10002
10003
...
```

Phase 2 might have identified it as a candidate because of its position or structure.

Phase 3 should reject it:

```text
TARGET INVALID

Reason:
Column behaves like an identifier.
```

---

# 7. Target missing-value check

Example:

```text
Total samples: 20,000
Missing target: 240
```

Phase 3:

```text
WARNING

1.2% of samples have no target label.
```

It does not remove them.

---

# 8. Module 3.2 — Schema Validation

The profile says:

```text
26 numerical
7 categorical
```

Phase 3 verifies that the actual values agree with that interpretation.

Example:

```text
age
```

Expected:

```text
numeric
```

But the actual data contains:

```text
25
31
unknown
45
N/A
```

This may become:

```text
WARNING:
Unexpected non-numeric values detected.
```

---

# 9. Data-type problems

Examples:

```text
age:
"25 years"

blood_pressure:
"120/80"

cholesterol:
"high"
```

Phase 3 records these as quality issues.

It does not transform them.

---

# 10. Module 3.3 — Missing Data Assessment

Calculate:

### Dataset-level

```text
Total missing values
Missing percentage
```

### Column-level

```text
age              0.1%
cholesterol      3.2%
blood_pressure   8.7%
```

### Sample-level

```text
Patient 1042:
63% fields missing
```

---

# 11. Why this matters

We don't want Phase 4 to blindly run:

```text
StandardScaler()
```

on a dataset containing:

```text
NaN
unknown
?
N/A
```

Phase 3 identifies this first.

---

# 12. Missing-value severity

We can define simple rules.

Example:

```text
0%
    → PASS

0–5%
    → LOW

5–20%
    → MODERATE

>20%
    → HIGH
```

These thresholds should be configurable rather than hard-coded permanently.

---

# 13. Module 3.4 — Duplicate Assessment

For tabular data:

```text
Exact duplicate rows
```

Example:

```text
20,000 rows
17 exact duplicates
```

Output:

```text
WARNING:
17 duplicate rows detected.
```

For images:

```text
identical file hash
```

Potentially:

```text
17 duplicate images detected.
```

Again:

> **Do not delete them here.**

---

# 14. Module 3.5 — Class Balance Validation

If the task is classification:

```text
Healthy       72%
Disease       28%
```

Phase 3 calculates:

```text
imbalance ratio
minority percentage
class counts
```

Example:

```text
Class 0: 14,500
Class 1: 5,500

Ratio = 2.64 : 1
```

Output:

```text
MODERATE IMBALANCE
```

---

# 15. Extreme imbalance

Example:

```text
Healthy: 98.7%
Disease: 1.3%
```

Phase 3:

```text
HIGH IMBALANCE

Risk:
Accuracy may be misleading.
```

This becomes important later because our platform explicitly cares about:

* sensitivity
* specificity
* AUC

and not just accuracy.

---

# 16. Module 3.6 — Value Range Validation

This checks whether values appear structurally reasonable.

Examples:

```text
age = -17
```

```text
BMI = 900
```

```text
heart_rate = -5
```

The system can flag these as:

```text
POSSIBLE INVALID VALUES
```

---

# 17. Important medical-data principle

We should **not automatically declare a value medically impossible unless we have a justified domain rule**.

For example:

```text
age > 120
```

can reasonably be flagged.

But something like:

```text
cholesterol = 350
```

should not automatically be deleted.

It could be a real measurement.

Therefore Phase 3 distinguishes:

```text
STRUCTURAL INVALIDITY
```

from:

```text
POTENTIAL OUTLIER
```

---

# 18. Module 3.7 — Outlier Assessment

We can calculate statistical indicators such as:

* IQR
* z-score
* percentile boundaries

Example:

```text
cholesterol

Potential outliers:
132 samples
```

Output:

```text
INFO:
Potential statistical outliers detected.
```

Do not remove them.

Phase 4 decides whether treatment is appropriate.

---

# 19. Module 3.8 — Data Leakage Detection

This is one of the **most important modules in Phase 3**.

We need to prevent the model from accidentally receiving information that reveals the target.

Example:

```text
target:
disease

feature:
diagnosis_code
```

If:

```text
diagnosis_code
```

essentially encodes the disease label, the model can appear extremely accurate without genuinely learning the underlying pattern.

The validator should flag suspicious relationships.

---

# 20. Identifier detection

Columns such as:

```text
patient_id
record_id
image_id
case_id
```

may be legitimate identifiers but should normally not become predictive features.

Phase 3 can mark:

```text
patient_id → IDENTIFIER CANDIDATE
```

Phase 4 can exclude it.

---

# 21. Module 3.9 — Train/Test Leakage Risk

The most important rule:

> **The test set must remain untouched until final evaluation.**

Phase 3 establishes the conditions for a future split.

For example:

```text
70% train
15% validation
15% test
```

But Phase 3 should not train models yet.

---

# 22. Patient-level leakage

For medical data, this is particularly important.

Suppose:

```text
Patient A
 ├── image 1
 ├── image 2
 └── image 3
```

If:

```text
image 1 → training
image 2 → test
```

the model may effectively see the same patient in both sets.

That creates leakage.

Therefore, if a patient identifier exists:

```text
patient_id
```

we should flag that the eventual split should be:

```text
patient-level split
```

rather than random image-level splitting.

---

# 23. Image/Label Validation

For image datasets:

```text
images/
labels.csv
```

Phase 3 checks:

```text
Every image has label?
Every label has image?
Any duplicate image?
Any missing image?
Any invalid image?
```

Example:

```text
Images: 10,000
Labels: 10,000

Matched: 9,998
Unmatched images: 2
Unmatched labels: 0
```

Result:

```text
WARNING:
2 images have no valid label.
```

---

# 24. Image consistency

Check:

```text
dimensions
channels
formats
corrupted files
```

Example:

```text
9,800 images → 224×224 RGB
200 images → 512×512 RGB
```

Output:

```text
WARNING:
Mixed image dimensions detected.
```

Phase 4 decides how to standardize them.

---

# 25. Module 3.10 — Dataset Suitability

After all checks, we calculate an overall quality status.

For example:

```text
PASS
PASS_WITH_WARNINGS
BLOCKED
```

### PASS

No critical issues.

### PASS_WITH_WARNINGS

Usable but requires preprocessing.

### BLOCKED

Cannot safely proceed.

---

# 26. Example Quality Report

```text
Dataset:
DS-000001

Modality:
TABULAR

Task:
Binary Classification

─────────────────────────────

Target validation       ✓ PASS
Schema validation       ✓ PASS
Missing values          ⚠ WARNING
Duplicates              ⚠ WARNING
Class balance           ⚠ WARNING
Value validation        ✓ PASS
Leakage check           ✓ PASS

─────────────────────────────

Overall:
PASS WITH WARNINGS
```

---

# 27. Quality Score

We can optionally calculate a quality score.

Example:

```text
Dataset Quality Score

92 / 100
```

But this should **not** be treated as a medical-quality score.

It's only:

> **technical dataset readiness**

For example:

```text
Data completeness
Schema consistency
Label integrity
Duplicate level
Structural integrity
```

---

# 28. Critical vs Non-Critical Issues

This distinction is important.

## Critical

```text
Target missing entirely
Corrupted dataset
No usable labels
Image-label mapping impossible
Severe structural corruption
```

→ `BLOCKED`

---

## Warning

```text
Missing values
Class imbalance
Potential outliers
Duplicate candidates
Mixed image sizes
```

→ `PASS_WITH_WARNINGS`

---

## Informational

```text
32 features
20,000 samples
3 categorical columns
```

→ `PASS`

---

# 29. Phase 3 Output

The output should contain:

```json
{
  "dataset_id": "DS-000001",

  "validation_status": "PASS_WITH_WARNINGS",

  "target_validation": {
    "status": "PASS",
    "target": "disease"
  },

  "schema_validation": {
    "status": "PASS"
  },

  "missing_values": {
    "status": "WARNING",
    "percentage": 1.7
  },

  "duplicates": {
    "status": "WARNING",
    "count": 12
  },

  "class_balance": {
    "status": "WARNING",
    "ratio": 2.64
  },

  "leakage": {
    "status": "PASS"
  },

  "outliers": {
    "status": "INFO"
  },

  "quality_score": 92,

  "next_phase": "PREPROCESSING"
}
```

---

# 30. What Phase 3 Does NOT Do

This boundary is critical.

Phase 3 does **not**:

* impute missing values
* normalize features
* encode categories
* remove duplicates
* remove outliers
* balance classes
* perform PCA
* select features
* train models
* choose VQC
* choose XGBoost

It only answers:

> **"What is wrong or potentially problematic?"**

---

# 31. Phase 3 → Phase 4 Contract

Phase 4 receives:

```text
dataset_id
+
dataset_profile
+
validation_report
```

For example:

```text
DS-000001

Task:
Binary classification

Target:
disease

Issues:
1.7% missing
2.64:1 class imbalance
12 duplicate candidates
3 potential outlier groups
```

Phase 4 can then make actual transformation decisions.

---

# 32. Phase 3 Architecture

```text
                 DATASET PROFILE
                       |
                       v
              ┌─────────────────┐
              │ Target Validator│
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Schema Validator│
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Missing Data    │
              │ Analyzer        │
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Duplicate       │
              │ Analyzer        │
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Class Balance   │
              │ Analyzer        │
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Range / Outlier │
              │ Analyzer        │
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Leakage         │
              │ Analyzer        │
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Image/Label     │
              │ Validator       │
              └────────┬────────┘
                       |
                       v
              ┌─────────────────┐
              │ Quality         │
              │ Assessment      │
              └────────┬────────┘
                       |
                       v
                VALIDATION REPORT
```

---

# 33. Phase 3 Success Criteria

We should not move to Phase 4 until:

* [ ] Target candidate is validated
* [ ] Schema is checked
* [ ] Missing values are quantified
* [ ] Duplicate candidates are identified
* [ ] Class imbalance is measured
* [ ] Invalid-value candidates are detected
* [ ] Outlier indicators are generated
* [ ] Identifier columns are detected
* [ ] Leakage risks are checked
* [ ] Patient-level split risks are identified where applicable
* [ ] Image-label relationships are validated where applicable
* [ ] Dataset receives PASS / PASS_WITH_WARNINGS / BLOCKED
* [ ] Validation report is stored
* [ ] Original dataset remains untouched

---

# 34. The Three-Phase Boundary So Far

```text
┌─────────────────────────────────────────────┐
│ PHASE 1 — INGESTION                         │
│                                             │
│ "What did the user give us?"                │
│                                             │
│ Receive → verify → hash → store → register │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ PHASE 2 — PROFILING                          │
│                                             │
│ "What is inside it?"                        │
│                                             │
│ Inspect → understand → profile → infer      │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ PHASE 3 — VALIDATION                         │
│                                             │
│ "Can we actually use it?"                   │
│                                             │
│ Verify → detect problems → assess readiness │
└─────────────────────┬───────────────────────┘
                      ↓
                 PHASE 4
              PREPROCESSING
```

The key principle is that **Phase 3 identifies problems, but Phase 4 owns the decisions about how to fix/transform them**.
