
# PHASE 2 — Dataset Profiling & Discovery

## 1. Purpose

Phase 2 answers:

> **"What is actually inside the dataset we registered in Phase 1?"**

Phase 1 only knows:

```text
DS-000001
↓
original.zip
↓
ZIP
```

Phase 2 investigates the contents and creates a **Dataset Profile** that all subsequent phases can use.

---

# 2. Input

Phase 2 receives:

```text
dataset_id
```

Example:

```text
DS-000001
```

It retrieves the original immutable dataset from Phase 1.

Possible inputs:

```text
CSV
XLSX
ZIP
```

---

# 3. Phase 2 Does

```text
Dataset ID
    ↓
Retrieve raw dataset
    ↓
Inspect package/content
    ↓
Determine dataset structure
    ↓
Determine modality
    ↓
Analyze schema
    ↓
Identify target/label candidates
    ↓
Infer ML task
    ↓
Calculate basic statistics
    ↓
Detect structural issues
    ↓
Create Dataset Profile
```

---

# 4. Module 2.1 — Dataset Loader

### Input

```text
DS-000001
```

### Work

1. Retrieve dataset metadata.
2. Retrieve raw source.
3. Verify source exists.
4. Verify hash if required.
5. Open dataset using the appropriate reader.

### Examples

```text
CSV → pandas
XLSX → openpyxl/pandas
ZIP → controlled archive reader
```

### Output

```text
Dataset object / package reference
```

---

# 5. Module 2.2 — Package Inspection

This is particularly important for ZIP.

Example:

```text
skin_cancer.zip

├── images/
├── labels.csv
└── metadata.csv
```

Profiler identifies the internal structure:

```text
directories:
images/

files:
labels.csv
metadata.csv
```

But it still **doesn't modify the original package**.

---

# 6. Module 2.3 — Modality Detection

Now we determine:

> **What kind of data is this?**

Possible results:

```text
TABULAR
IMAGE
MULTIMODAL
UNSUPPORTED
```

### Example 1

```text
heart.csv
```

Output:

```text
modality = TABULAR
```

### Example 2

```text
skin_cancer.zip
    └── images/*.jpg
```

Output:

```text
modality = IMAGE
```

### Example 3

```text
medical.zip
├── images/
├── clinical.csv
└── labels.csv
```

Output:

```text
modality = MULTIMODAL
```

---

# 7. Important: Modality Detection Is Not Guesswork

We should use deterministic rules.

For example:

```text
IF majority of usable files are CSV/XLSX
    → TABULAR

IF image files + labels are detected
    → IMAGE

IF meaningful image + tabular data are linked
    → MULTIMODAL

OTHERWISE
    → UNKNOWN / UNSUPPORTED
```

We can improve these rules later.

---

# 8. Module 2.4 — Tabular Schema Analysis

If modality is `TABULAR`, inspect:

```text
columns
data types
row count
column count
missing values
unique values
```

Example:

```text
age              integer
blood_pressure   float
cholesterol      float
sex              categorical
disease          categorical
```

---

# 9. Module 2.5 — Dataset Statistics

For every tabular dataset:

### Basic

```text
Rows
Columns
```

### Numerical

```text
min
max
mean
median
standard deviation
```

### Categorical

```text
unique values
frequency
```

### Missingness

```text
missing count
missing percentage
```

Example:

```text
Rows:             20,000
Columns:              33

Numerical:            26
Categorical:           7

Missing values:     1.7%
```

---

# 10. Module 2.6 — Target / Label Discovery

This is one of the most important parts.

The system needs to identify potential target columns.

Possible candidate names:

```text
target
label
class
diagnosis
disease
outcome
y
```

But we should **not blindly assume** the column named `diagnosis` is the target.

The profiler should generate:

```text
Target candidates
```

Example:

```text
Potential targets:

1. disease       confidence: HIGH
2. diagnosis     confidence: MEDIUM
3. outcome       confidence: LOW
```

The user can confirm later.

---

# 11. Target Discovery Rules

Possible signals:

### Column position

Target often appears near the end.

### Data type

Classification target often has limited unique values.

### Naming

```text
disease
diagnosis
outcome
label
target
```

### Relationship to identifiers

Don't select:

```text
patient_id
```

just because it has low unique values.

---

# 12. Module 2.7 — Task Discovery

Once a target candidate is identified, infer the **candidate ML task**.

Possible tasks:

```text
Binary Classification
Multiclass Classification
Regression
Unknown
```

Example:

```text
disease:

0 = healthy
1 = disease
```

→

```text
BINARY CLASSIFICATION
```

Example:

```text
stage:

I
II
III
IV
```

→

```text
MULTICLASS CLASSIFICATION
```

Example:

```text
risk_score:

0.21
0.73
0.48
...
```

→

```text
REGRESSION
```

---

# 13. Important: Task Is a Candidate, Not Final Truth

Phase 2 should produce:

```text
inferred_task
```

not:

```text
final_task
```

Why?

Because Phase 3 will validate whether this interpretation is actually valid.

So:

```text
Phase 2:
"I think this is binary classification."

Phase 3:
"Let's verify that."
```

---

# 14. Module 2.8 — Class Distribution

For classification candidates:

```text
Disease = 0
Disease = 1
```

calculate:

```text
Class 0: 14,500 → 72.5%
Class 1:  5,500 → 27.5%
```

Then flag:

```text
class_imbalance = MODERATE
```

Again, this is a **profile observation**, not a preprocessing decision.

Phase 4 will decide what to do about it.

---

# 15. Module 2.9 — Duplicate Candidates

Profiler can identify potential duplicates.

For tabular data:

```text
duplicate rows
```

For images:

```text
identical file hashes
```

Potential output:

```text
duplicate_candidates = 17
```

It should **not delete them**.

Deletion/handling belongs to later validation.

---

# 16. Module 2.10 — Image Profiling

If modality = IMAGE, profile:

```text
number of images
formats
width
height
channels
file sizes
```

Example:

```text
Images:       10,000
Format:       JPG
Resolution:   224 × 224
Channels:     3
```

Also inspect:

```text
label availability
image-label mapping
```

---

# 17. Module 2.11 — Multimodal Profiling

If the dataset contains:

```text
clinical.csv
+
images/
```

the profiler tries to identify relationships.

For example:

```text
patient_id
```

appears in both.

Then:

```text
Image
   ↕
patient_id
   ↕
Clinical record
```

Profile:

```text
image modality
+
tabular modality
+
linking key
```

But **do not merge them yet**.

That is a later pipeline decision.

---

# 18. Module 2.12 — Dataset Size

Profile:

```text
samples
features
storage size
```

For example:

```text
Samples:       20,000
Features:          32
Raw size:       2.4 GB
```

For images:

```text
Images:        10,000
Average size:  280 KB
```

---

# 19. Module 2.13 — Basic Structural Warnings

Phase 2 should produce warnings such as:

```text
WARNING:
Potential class imbalance.

WARNING:
Target candidate not confidently identified.

WARNING:
17 duplicate candidates found.

WARNING:
Mixed image resolutions detected.

WARNING:
No obvious label file found.
```

These are **warnings**, not corrections.

---

# 20. Dataset Profile Output

The final output should be a structured object.

Example for tabular data:

```json
{
  "dataset_id": "DS-000001",

  "modality": "TABULAR",

  "dimensions": {
    "rows": 20000,
    "columns": 33
  },

  "features": {
    "numerical": 26,
    "categorical": 7
  },

  "target": {
    "candidate": "disease",
    "confidence": "HIGH"
  },

  "task": {
    "candidate": "BINARY_CLASSIFICATION",
    "confidence": "HIGH"
  },

  "class_distribution": {
    "0": 14500,
    "1": 5500
  },

  "missing_values": {
    "total": 340,
    "percentage": 1.7
  },

  "duplicates": {
    "candidate_count": 12
  },

  "warnings": [
    "Moderate class imbalance",
    "Duplicate candidates detected"
  ],

  "status": "PROFILED"
}
```

---

# 21. Example — Skin Cancer ZIP

Input:

```text
DS-000002
```

Profiler finds:

```text
ZIP
 ↓
images/
labels.csv
metadata.csv
```

Output:

```json
{
  "dataset_id": "DS-000002",

  "modality": "IMAGE",

  "samples": 10000,

  "image": {
    "formats": ["JPG"],
    "width": 224,
    "height": 224,
    "channels": 3
  },

  "labels": {
    "source": "labels.csv",
    "classes": [
      "benign",
      "malignant"
    ]
  },

  "task": {
    "candidate": "BINARY_CLASSIFICATION",
    "confidence": "HIGH"
  },

  "warnings": [],

  "status": "PROFILED"
}
```

---

# 22. What Phase 2 DOES NOT DO

Very important.

### It does NOT:

* remove missing values
* remove duplicates
* normalize data
* encode categorical features
* select features
* perform PCA
* balance classes
* train models
* choose XGBoost
* choose VQC
* choose number of qubits
* run quantum circuits
* modify the original dataset

Those belong to later phases.

---

# 23. Phase 2 → Phase 3 Contract

Phase 2 outputs:

```text
Dataset Profile
```

Phase 3 receives:

```text
dataset_id
+
dataset_profile
```

Then Phase 3 asks:

> **"Is this dataset actually valid and suitable for our disease-detection experiment?"**

---

# 24. Phase 2 Architecture

```text
                 DATASET ID
                     |
                     v
             ┌──────────────┐
             │ Dataset      │
             │ Loader       │
             └──────┬───────┘
                    |
                    v
             ┌──────────────┐
             │ Package      │
             │ Inspector    │
             └──────┬───────┘
                    |
                    v
             ┌──────────────┐
             │ Modality     │
             │ Detector     │
             └──────┬───────┘
                    |
          ┌─────────┴──────────┐
          |                    |
          v                    v
      TABULAR                IMAGE
          |                    |
          v                    v
   Schema Analyzer       Image Analyzer
          |                    |
          └─────────┬──────────┘
                    |
                    v
             ┌──────────────┐
             │ Target/Label │
             │ Discovery    │
             └──────┬───────┘
                    |
                    v
             ┌──────────────┐
             │ Task         │
             │ Discovery    │
             └──────┬───────┘
                    |
                    v
             ┌──────────────┐
             │ Statistics & │
             │ Warnings     │
             └──────┬───────┘
                    |
                    v
             ┌──────────────┐
             │ Dataset      │
             │ Profile      │
             └──────────────┘
```

---

# 25. Phase 2 Success Criteria

We consider Phase 2 complete when it can:

* [ ] Load a registered dataset by ID
* [ ] Inspect CSV
* [ ] Inspect XLSX
* [ ] Safely inspect ZIP contents
* [ ] Detect tabular/image/multimodal structure
* [ ] Calculate dataset dimensions
* [ ] Analyze schema
* [ ] Identify target candidates
* [ ] Infer candidate ML task
* [ ] Calculate class distribution
* [ ] Calculate missing-value statistics
* [ ] Detect duplicate candidates
* [ ] Profile image properties where applicable
* [ ] Generate warnings
* [ ] Store a versioned Dataset Profile
* [ ] Pass the profile to Phase 3

---

# 26. Final Phase 2 Definition

> **Phase 2 transforms the registered raw dataset into a structured understanding of its contents and ML characteristics, without modifying the source data or making final preprocessing/model decisions.**

The boundary is:

```text
PHASE 1
"What did the user give us?"
        ↓
PHASE 2
"What is inside it?"
        ↓
PHASE 3
"Is it valid and suitable?"
```

That gives us a clean foundation for the rest of the system.
