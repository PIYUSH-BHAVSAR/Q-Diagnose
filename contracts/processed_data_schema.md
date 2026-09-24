# Processed Data Schema

**Phase 4 Output → Phase 5/6/7/8 Input**  
**Version:** 1.1.0  
**Produced by:** Phase 4 preprocessing pipeline (Jayed)  
**Consumed by:** Phase 6 dimensionality reduction, Phase 7/8 model training (Piyush), Phase 12 explainability (Radha)

> **DECISION 2026-09-10 (fixes ISSUES.md B-03):**  
> Split is **80/20 stratified, no validation set.** The original contract had 70/15/15 — this conflicted with `config.yaml` (`test_size: 0.20`), all guide code, and all mock data. 80/20 is canonical. `X_validation` and `y_validation` are removed. If early stopping is needed for VQC, use the first 20% of `X_train` as an internal hold-out inside the training loop — do **not** expose a separate validation array.

> **DECISION 2026-09-10 (fixes ISSUES.md MH-01):**  
> Processed arrays **must be saved to disk** at `artifacts/experiments/{experiment_id}/data/` so Radha's explainability engine can load them after training completes. See Storage Format section below.

---

## Python Object — `FeaturePipelineResult`

This is the in-memory dataclass that `FeaturePipeline.fit_transform()` returns and that `ExperimentExecutor.run()` consumes directly.

```python
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class FeaturePipelineResult:
    # ── Full-feature arrays (classical models train on these) ──────────────────
    X_train:        np.ndarray   # float64, shape (n_train, n_features)
    X_test:         np.ndarray   # float64, shape (n_test,  n_features)
    y_train:        np.ndarray   # int64,   shape (n_train,)
    y_test:         np.ndarray   # int64,   shape (n_test,)

    # ── PCA-reduced arrays (quantum model trains on these) ─────────────────────
    X_train_reduced: np.ndarray  # float64, shape (n_train, n_components)
    X_test_reduced:  np.ndarray  # float64, shape (n_test,  n_components)

    # ── Feature name lists ─────────────────────────────────────────────────────
    feature_names:         List[str]   # original column names, length = n_features
    reduced_feature_names: List[str]   # ["PC1", "PC2", ...], length = n_components

    # ── Metadata ───────────────────────────────────────────────────────────────
    n_components:       int    # PCA components used (from config, e.g. 8)
    variance_retained:  float  # fraction of variance kept by PCA (e.g. 0.94)
    preprocessing_id:   str    # "PREP-{8-char-hex}" e.g. "PREP-A1B2C3D4"
    split_strategy:     str    # "stratified" or "grouped" (Parkinson's)
    test_size:          float  # 0.20
    random_state:       int    # 42
    class_weights:      dict   # sklearn balanced weights, e.g. {0: 0.80, 1: 1.34}
                               # INFORMATIONAL ONLY — Piyush passes class_weight="balanced"
                               # to sklearn directly; this dict is for display/logging.

    def to_dict(self) -> dict:
        """JSON-serialisable summary (no numpy arrays). Used for artifact storage."""
        return {
            "n_train":              int(len(self.y_train)),
            "n_test":               int(len(self.y_test)),
            "n_features":           int(self.X_train.shape[1]),
            "n_components":         self.n_components,
            "variance_retained":    round(float(self.variance_retained), 4),
            "preprocessing_id":     self.preprocessing_id,
            "split_strategy":       self.split_strategy,
            "test_size":            self.test_size,
            "random_state":         self.random_state,
            "feature_names":        self.feature_names,
            "reduced_feature_names": self.reduced_feature_names,
            "class_weights":        {str(k): round(float(v), 4)
                                     for k, v in self.class_weights.items()},
        }
```

---

## Shape Reference — All 4 Datasets (80/20 split, 8 PCA components)

> Row counts are approximate due to stratified splitting. Do **not** hardcode them.

| Dataset | X_train | X_test | X_train_reduced | X_test_reduced | y_train | y_test |
|---|---|---|---|---|---|---|
| Breast Cancer (569 rows, 30 features) | (455, 30) | (114, 30) | (455, 8) | (114, 8) | (455,) | (114,) |
| Heart Disease (303 rows, 13 features) | (242, 13) | (61, 13) | (242, 8) | (61, 8) | (242,) | (61,) |
| Diabetes (768 rows, 8 features) | (614, 8) | (154, 8) | (614, 8) | (154, 8) | (614,) | (154,) |
| Parkinson's (195 rows, 22 features)* | (156, 22) | (39, 22) | (156, 8) | (39, 8) | (156,) | (39,) |

\* Parkinson's uses `GroupShuffleSplit` on the `name` column — row counts may vary slightly because groups (patients) cannot be fractionally split. The 80/20 ratio is approximate.

> **Note on Diabetes (8 features, 8 PCA components):**  
> PCA with `n_components=8` on 8 features is a rotation, not a reduction — `X_train_reduced` and `X_train` will have the same shape. `variance_retained` will be 1.0. This is expected. The platform uses `n_components = min(n_components, n_features)` to avoid sklearn errors.

---

## Feature Names Reference

| Dataset | n_features | Example names |
|---|---|---|
| Breast Cancer | 30 | `radius_mean`, `texture_mean`, `perimeter_mean`, ..., `fractal_dimension_worst` |
| Heart Disease | 13 | `age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal` |
| Diabetes | 8 | `Pregnancies`, `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, `BMI`, `DiabetesPedigreeFunction`, `Age` |
| Parkinson's | 22 | `MDVP:Fo(Hz)`, `MDVP:Fhi(Hz)`, `MDVP:Flo(Hz)`, ..., `PPE` |

> Breast Cancer raw CSV has 32 columns: `id` (dropped by adapter) + `diagnosis` (target, encoded to 0/1) + 30 features.  
> Parkinson's raw CSV has 24 columns: `name` (dropped, used for grouped split) + `status` (target) + 22 features.  
> **Arzaan's ingestion reports raw column counts (32 and 24). Jayed's adapters produce 30 and 22 model features. These numbers are both correct for their respective contexts.**

---

## Class Distributions After 80/20 Split

```python
# Breast Cancer
y_train: {0: 285, 1: 170}   # approx 62.6% / 37.4% (stratified preserves ratio)
y_test:  {0:  72, 1:  42}

# Heart Disease
y_train: {0: 110, 1: 132}   # approx 45.5% / 54.5%
y_test:  {0:  28, 1:  33}

# Diabetes
y_train: {0: 400, 1: 214}   # approx 65.1% / 34.9%
y_test:  {0: 100, 1:  54}

# Parkinson's (grouped split — exact counts vary with patient grouping)
y_train: {0:  38, 1: 118}   # approx 24.4% / 75.6%
y_test:  {0:  10, 1:  29}
```

---

## `preprocessing_id` Format

```
"PREP-{8-char-uppercase-hex}"
e.g. "PREP-A1B2C3D4"
```

Generated by: `"PREP-" + uuid.uuid4().hex[:8].upper()`

The `preprocessing_id` links back to the stored `preprocessing.json` artifact file.

---

## `class_weights` — Informational Only

`class_weights` in `FeaturePipelineResult` is computed by sklearn's `compute_class_weight("balanced", ...)` on `y_train` and stored for logging/display. **Piyush's models pass `class_weight="balanced"` directly to sklearn constructors — they do not consume this dict as input.**

Expected values (approximate, based on training split):

| Dataset | class_weights |
|---|---|
| Breast Cancer | `{0: 0.80, 1: 1.34}` |
| Heart Disease | `{0: 1.10, 1: 0.91}` |
| Diabetes | `{0: 0.77, 1: 1.43}` |
| Parkinson's | `{0: 2.05, 1: 0.66}` |

---

## Data Leakage Prevention — Non-Negotiable Rules

1. `train_test_split` (or `GroupShuffleSplit`) is called **first**, before any transformer is fitted.
2. `StandardScaler.fit_transform(X_train)` — fitted on train only.
3. `StandardScaler.transform(X_test)` — applies train-fitted scaler to test.
4. `PCA.fit_transform(X_train_scaled)` — fitted on train only.
5. `PCA.transform(X_test_scaled)` — applies train-fitted PCA to test.
6. **Never** call `fit_transform` on `X_test` or on the combined dataset.

---

## Disk Storage — Required for Explainability

`ExperimentExecutor.run()` must save the following files **before** calling the benchmarking engine. Radha's explainability engine loads these from disk when `GET /api/experiments/{id}/explanation` is called.

```
artifacts/experiments/{experiment_id}/data/
├── X_train.npy              # np.save — full scaled features, shape (n_train, n_features)
├── X_test.npy               # np.save — full scaled features, shape (n_test, n_features)
├── X_train_reduced.npy      # np.save — PCA features, shape (n_train, n_components)
├── X_test_reduced.npy       # np.save — PCA features, shape (n_test, n_components)
├── y_train.npy              # np.save — labels, shape (n_train,)
├── y_test.npy               # np.save — labels, shape (n_test,)
├── feature_names.json       # json.dump — list of original feature name strings
└── pipeline_metadata.json   # json.dump — FeaturePipelineResult.to_dict()
```

**Load pattern in Radha's explainability engine:**
```python
import numpy as np, json, os

data_dir = f"artifacts/experiments/{experiment_id}/data"

X_train = np.load(os.path.join(data_dir, "X_train.npy"))
X_test  = np.load(os.path.join(data_dir, "X_test.npy"))
X_test_reduced = np.load(os.path.join(data_dir, "X_test_reduced.npy"))
y_test  = np.load(os.path.join(data_dir, "y_test.npy"))

with open(os.path.join(data_dir, "feature_names.json")) as f:
    feature_names = json.load(f)

with open(os.path.join(data_dir, "pipeline_metadata.json")) as f:
    meta = json.load(f)
    reduced_feature_names = meta["reduced_feature_names"]
```

**Save pattern in Piyush's executor (add to `ExperimentExecutor.run()` after `feature_pipeline.fit_transform()`):**
```python
import numpy as np, json, os

data_dir = f"artifacts/experiments/{experiment_id}/data"
os.makedirs(data_dir, exist_ok=True)

np.save(os.path.join(data_dir, "X_train.npy"),         processed.X_train)
np.save(os.path.join(data_dir, "X_test.npy"),          processed.X_test)
np.save(os.path.join(data_dir, "X_train_reduced.npy"), processed.X_train_reduced)
np.save(os.path.join(data_dir, "X_test_reduced.npy"),  processed.X_test_reduced)
np.save(os.path.join(data_dir, "y_train.npy"),         processed.y_train)
np.save(os.path.join(data_dir, "y_test.npy"),          processed.y_test)

with open(os.path.join(data_dir, "feature_names.json"), "w") as f:
    json.dump(processed.feature_names, f)

with open(os.path.join(data_dir, "pipeline_metadata.json"), "w") as f:
    json.dump(processed.to_dict(), f, indent=2)
```

---

## Model Artifact Storage — Required for SHAP

Trained sklearn models must be saved to disk so Radha can load them for SHAP without re-training.

```
artifacts/experiments/{experiment_id}/models/
├── logistic_regression.pkl   # joblib.dump
├── svm.pkl                   # joblib.dump
├── random_forest.pkl         # joblib.dump
└── vqc_params.npy            # np.save — VQC parameter array (not a pkl)
```

**Save in each classical model's `fit()` method (or in the executor):**
```python
import joblib, os

models_dir = f"artifacts/experiments/{experiment_id}/models"
os.makedirs(models_dir, exist_ok=True)
joblib.dump(self.model, os.path.join(models_dir, "random_forest.pkl"))
```

`model_result.json` includes `model_artifact_path` pointing to the `.pkl` file so Radha's engine knows where to load from.
