# ISSUES.md — Internal Consistency Audit
## Hybrid QML Disease Detection Platform
**Audited:** All 6 guide files, all 10 contracts + 3 doc files in /contracts/, 15 phase docs, MVP implementation plan  
**Auditor:** Kiro (automated cross-reference, September 10 2026)

---

## CRITICAL FINDING BEFORE THE NUMBERED ISSUES

### The /mocks/ folder does not exist.

The task premise states "40 populated example files, 4 datasets × 10 contracts" exist in `/mocks/`. A recursive filesystem search of `d:\projects\SIH2026\` confirmed **no `/mocks/` directory and no mock data files of this description exist anywhere in the project.** All items labelled "mocks" in the search results are node_modules or venv library internals.

**Impact of this finding on the audit scope:**
- Issues 2 (Mock-to-contract mismatch) and 3 (Cross-dataset mock consistency) from the task brief cannot be fully audited — there are no mock files to compare against contracts.
- Issues 4 (Contradicting verdicts within mock set) cannot be audited for the same reason.
- All other checks (field name drift, ownership gaps, missing handoffs, unit mismatches, phase citations, NOTES.md resolution) are auditable and are fully reported below.

---

## SEVERITY LEGEND
- **BLOCKING** — Will cause a runtime crash or wrong data flowing between teammates the moment integration starts.
- **MODERATE** — Will cause integration confusion, wrong assumptions, or silent bugs that are hard to trace.
- **MINOR** — Cosmetic inconsistency; will not break anything but should be cleaned up for clarity.

---

## SECTION 1 — BLOCKING ISSUES

---

### B-01 · Field name drift: `experiment_status.json` contract vs `guide_piyush.md` and `guide_naeem.md`

**Files:** `contracts/experiment_status.json`, `guide_piyush.md` §5d, `guide_naeem.md` §4f

**Detail:**

The authoritative contract `experiment_status.json` defines these fields:
```
"circuit_executions_so_far"   (exact field name in contract)
"message"                     (present in contract, not in guides)
"current_epoch"               (present in contract)
"total_epochs"                (present in contract)
"estimated_remaining_seconds" (present in contract)
"resource_snapshot"           (present in contract)
```

`guide_piyush.md` §5d shows this shape as the contract Piyush must produce:
```json
{
  "circuit_executions": 8320,       ← WRONG FIELD NAME (contract says circuit_executions_so_far)
  "current_model": "VQC",           ← INVENTED FIELD (not in contract)
  "completed_models": [...],        ← INVENTED FIELD (not in contract)
  "error_message": null             ← INVENTED FIELD (not in contract)
}
```

`guide_naeem.md` §4f shows the polling response Naeem must consume:
```json
{
  "circuit_executions": 8320,       ← WRONG FIELD NAME
  "current_model": "VQC",           ← INVENTED FIELD
  "completed_models": [...],        ← INVENTED FIELD
}
```

`guide_naeem.md` also hardcodes stage values `"preprocessing"`, `"classical_training"`, `"quantum_training"`, `"benchmarking"` in `MOCK_STATUS_SEQUENCE` and in `StageProgress.jsx`. The contract's `_examples` for `stage` are `"loading_data"`, `"preprocessing"`, `"training_classical"`, `"training_quantum"`, `"circuit_execution"` — three of Naeem's five stage key strings are different from the contract examples.

The contract `status` enum is:
```
"QUEUED" | "INITIALIZING" | "RUNNING" | "TRAINING" | "INFERENCE" | "EVALUATING" | "COMPLETED" | "FAILED" | "TIMEOUT"
```

Both guides list the status enum as:
```
"CREATED" | "VALIDATING" | "PREPROCESSING" | "RUNNING_CLASSICAL" | "RUNNING_QUANTUM" | "BENCHMARKING" | "EXPLAINING" | "COMPLETED" | "FAILED"
```
Nine out of eleven values differ. This is a complete enum mismatch. Piyush will produce one set of strings; Naeem's frontend will never match the expected RUNNING/TRAINING/etc. states.

**Suggested fix:** Decide which status enum is canonical (the contract or the guides) and update the losing side. The guide versions (RUNNING_CLASSICAL, RUNNING_QUANTUM, BENCHMARKING) are arguably more useful for the frontend — if adopted, update `experiment_status.json`. If the contract is canonical, update both guides and Piyush's `ExperimentStatus` enum in `manager.py`.

---

### B-02 · Field name drift: `model_result.json` contract vs `guide_piyush.md` — `f1_score` vs `f1`

**Files:** `contracts/model_result.json`, `guide_piyush.md` §5b, `guide_naeem.md` §4g

**Detail:**

`contracts/model_result.json` uses the field name `"f1_score"`:
```json
"f1_score": { "_type": "float [0-1]", ... }
```

`guide_piyush.md` §5b and `guide_piyush.md`'s `MetricsCalculator.compute()` code both use `"f1_score"` — consistent.

However `guide_naeem.md` §4g shows the results API mock with:
```json
"metrics": {
  "accuracy": 0.921, "precision": 0.901, "recall": 0.882,
  "specificity": 0.941, "f1_score": 0.891, "roc_auc": 0.937, "pr_auc": 0.881
}
```
And `guide_naeem.md`'s `MetricsTable.jsx` component iterates over `metricKeys = ['accuracy','recall','specificity','f1_score','roc_auc','pr_auc']` — consistent here.

But `guide_piyush.md`'s `RecommendationEngine` code does:
```python
"f1_score":    float(f1_score(y_true, y_pred, zero_division=0)),
```
while `MetricsCalculator.compute()` returns key `"f1_score"` — fine.

The inconsistency is in `guide_piyush.md`'s `ModelResult` dataclass which lists field `f1_score` but `guide_piyush.md`'s `VQCModel.fit()` does `**metrics` to unpack — this only works if MetricsCalculator's keys exactly match the dataclass field names. If anyone uses `"f1"` anywhere in a dict unpack it will silently fail.

**Secondary drift:** `contracts/model_result.json` has `"pr_auc"` as a top-level key. `guide_piyush.md`'s MetricsCalculator returns `"pr_auc"`. Consistent. But `guide_naeem.md` MetricsTable renders keys `['accuracy','recall','specificity','f1_score','roc_auc','pr_auc']` — only 6 of the 7 metrics (omits `precision`). This is a display omission, not a naming bug, but Naeem will never show precision in his comparison table.

**Suggested fix:** Add `"precision"` to `metricKeys` in `MetricsTable.jsx`. Confirm all dict keys use `f1_score` not `f1` in every usage.

---

### B-03 · Split ratio conflict between `processed_data_schema.md` and every guide

**Files:** `contracts/processed_data_schema.md`, `guide_jayed.md` §5c, `guide_piyush.md` §7, `guide_naeem.md` §7

**Detail:**

`contracts/processed_data_schema.md` states:
> "Split proportions: approximately **70% train, 15% validation, 15% test** (stratified)."

And gives shapes:
```
Breast Cancer:  X_train (398, 30), X_validation (86, 30), X_test (85, 30)
```
(398+86+85 = 569 ✓, 70/15/15 split)

`guide_jayed.md` §5c defines `FeaturePipelineResult` with only `X_train` and `X_test` — **no `X_validation`**:
```python
X_train: np.ndarray   # (455, 30)   ← 80% of 569
X_test:  np.ndarray   # (114, 30)   ← 20% of 569
```

`guide_jayed.md` §6 uses `test_size=0.20` and `config.yaml` says `test_size: 0.20`.

The shapes are incompatible:
- Contract: 398 train / 86 validation / 85 test (70/15/15)
- Guide/config: 455 train / 114 test (80/20, no validation)

`guide_piyush.md` §7 mock data uses `n_train=455, n_test=114` (80/20).
`guide_naeem.md` §7 table says `X_train (455,30)`, `X_test (114,30)` (80/20).

Three guides and the config all agree on 80/20. The contract disagrees. This also means `X_validation` and `y_validation` fields in the contract don't exist in the actual `FeaturePipelineResult` dataclass — anyone building against the contract will expect a validation set that doesn't exist.

**This is NOTES.md item #2 left silently unresolved** — the guides resolved it one way (80/20), the contract resolved it a different way (70/15/15), with no cross-update.

**Suggested fix:** Pick one split. If 80/20 is correct (consistent with config.yaml), update `processed_data_schema.md` to use 80/20 shapes, remove `X_validation`/`y_validation` fields, and update row counts. If 70/15/15 is correct, add `X_validation`/`y_validation` to `FeaturePipelineResult` and update all guides.

---

### B-04 · `FeaturePipelineResult` missing `X_train` — contracts/processed_data_schema.md describes it but guide_piyush.md §4 only references the reduced arrays for VQC

**Files:** `guide_piyush.md` §4, `contracts/processed_data_schema.md`, `guide_jayed.md` §5c

**Detail:**

`guide_piyush.md` §4 describes the input contract as:
```python
X_train:          np.ndarray   # (455, 30) for Breast Cancer full features
X_test:           np.ndarray   # (114, 30)
X_train_reduced:  np.ndarray   # (455, 8)
X_test_reduced:   np.ndarray   # (114, 8)
```
This is correct and complete.

However `guide_piyush.md`'s classical model code:
```python
result = rf.fit(processed.X_train, processed.y_train, processed.X_test, processed.y_test)
```
...passes `X_train` (full 30 features) to classical models. VQC gets `X_train_reduced`. This is correct per the fair comparison design.

The problem is `guide_piyush.md`'s `ExperimentExecutor._train_classical_models()` method signature in executor.py only lists `processed` as the argument. The existing `executor.py` (which Piyush must fill in) currently does:
```python
result = model.fit(
    processed.X_train,  processed.y_train,
    processed.X_test,   processed.y_test,
    processed.reduced_feature_names   ← WRONG: passes reduced_feature_names to classical model
)
```
Looking at the existing `executor.py` code, classical models receive `processed.reduced_feature_names` as `feature_names` argument, but classical models train on `X_train` (full 30 features). The `feature_names` array will have 8 PCA names ("PC1"–"PC8") but the model was trained on 30 features. Any SHAP explanation by Radha that uses these feature names will label features incorrectly.

**Suggested fix:** In `executor.py._train_classical_models()`, pass `processed.feature_names` (full 30 names) to classical models, and `processed.reduced_feature_names` only to VQC.

---

### B-05 · `validation.issues` referenced in executor.py but `ValidationResult` has no `.issues` field

**Files:** `guide_jayed.md` §6 (executor.py integration snippet), `contracts/validation_report.json`

**Detail:**

`guide_jayed.md` §6 shows this code that will exist in `executor.py`:
```python
if not validation.is_valid:
    raise ValueError(f"Dataset validation failed: {validation.issues}")
```

The `ValidationResult` dataclass defined in `guide_jayed.md` §6 has fields:
`validation_status`, `quality_score`, `next_phase`, `target_validation`, `missing_values`, `duplicates`, `class_balance`, `leakage`, `outliers`, `critical_issues`, `warnings`, `info_messages`, `recommended_preprocessing_steps`

There is no `.issues` field. The correct field is `.critical_issues` (list of dicts) or `.warnings` (list of dicts).

`validation.issues` will raise `AttributeError` at runtime when a dataset has problems.

**Suggested fix:** Change to `raise ValueError(f"Dataset validation failed: {validation.critical_issues}")` or define a `@property issues` on `ValidationResult` that returns `critical_issues`.

---

### B-06 · `guide_piyush.md` `ModelResult` dataclass missing `experiment_id` but `to_dict()` returns it; downstream consumers require it

**Files:** `guide_piyush.md` §5a, `contracts/model_result.json`

**Detail:**

`contracts/model_result.json` has `"experiment_id"` as the first field.

`guide_piyush.md` §5a lists `experiment_id: str` in the `ModelResult` dataclass — present.

However `guide_piyush.md`'s `LogisticRegressionModel.fit()` constructs the return as:
```python
return ModelResult(
    model_type="CLASSICAL",
    model_name="LogisticRegression",
    representation_id="REP-000001",   ← HARDCODED string
    status="COMPLETED",
    ...
    **metrics
)
```
`experiment_id` is never passed in any classical model's `fit()` call shown in the guide. The `ExperimentExecutor._train_classical_models()` doesn't show how `experiment_id` gets assigned to the result. Radha's `ExplainabilityEngine._explain_classical()` accesses `result.experiment_id` — this will be None or missing unless explicitly set.

Also `representation_id="REP-000001"` is hardcoded as a constant string. Every experiment for every dataset will show the same representation ID regardless of which PCA transform was actually used.

**Suggested fix:** `ExperimentExecutor` must pass `experiment_id` and `representation_id` into each model's `fit()` method (as additional parameters) or set them on the result object afterward.

---

### B-07 · `guide_radha.md` references `result._model` but `guide_piyush.md` never exposes `_model` on `ModelResult`

**Files:** `guide_radha.md` §4, `guide_piyush.md` §5a

**Detail:**

`guide_radha.md` §4 states:
```python
result._model  # sklearn estimator — you need Piyush to expose this
```

`guide_radha.md`'s `ClassicalExplainer.__init__` and `ExplainabilityEngine._explain_classical()` both do:
```python
explainer = ClassicalExplainer(result._model, model_name, processed.feature_names)
```

The `ModelResult` dataclass defined in `guide_piyush.md` §5a has no `_model` field. It stores metrics, predictions, and resource usage but not the fitted sklearn estimator itself.

Without `_model`, `ClassicalExplainer` has nothing to pass to SHAP. The `TreeExplainer(self.model)` call will fail because `self.model` would be None.

**Suggested fix:** Either (a) add `_model: Optional[Any]` field to `ModelResult` and have each classical model's `fit()` store `self.model` there, or (b) have the executor store models separately in `artifacts/experiments/{id}/models/` and have Radha load them from disk using joblib.

---

### B-08 · `guide_shweta.md` imports `DatasetIngestionService` and `FileSizeLimitError` that Arzaan has not been told to create

**Files:** `guide_shweta.md` §6, `guide_arzaan.md` §6

**Detail:**

`guide_shweta.md` §6 Hour 2–3 shows:
```python
ingestion = DatasetIngestionService(db=db)
result = ingestion.ingest(filename=file.filename, content_type=file.content_type, file_bytes=file_bytes)
```
and:
```python
except FileSizeLimitError as e:
    raise HTTPException(status_code=413, detail=str(e))
```

`guide_arzaan.md` §6 tells Arzaan to create an ingestion pipeline inside `data/loader.py` or `data/ingestion.py` with functions `validate_format()`, `calculate_sha256()`, `check_duplicate()`, `generate_display_id()`, and `ingest()`. The service is described as a function or method named `ingest`, not a class named `DatasetIngestionService`.

`guide_arzaan.md`'s `core/exceptions.py` defines: `QMLPlatformError`, `DatasetValidationError`, `UnsupportedFormatError`, `StorageError`, `ExperimentNotFoundError`, `DataLeakageError`. It does **not** include `FileSizeLimitError`.

Shweta's code will fail on import of both `DatasetIngestionService` and `FileSizeLimitError`.

**Suggested fix:** Either (a) Arzaan creates a `DatasetIngestionService` class and adds `FileSizeLimitError` to `exceptions.py`, or (b) Shweta uses the function-based `ingest()` API and catches `StorageError` for the size-limit case. The guides need to agree on which interface pattern Arzaan produces.

---

### B-09 · `guide_piyush.md` `RecommendationEngine.recommend()` contains a Python syntax error (`f"BENCH-{...}"`)

**Files:** `guide_piyush.md` §6 Day 2 Hour 1–2

**Detail:**

The code shown:
```python
return {
    "benchmark_id": f"BENCH-{...}",   ← literal ... is not valid Python f-string content
```

`f"BENCH-{...}"` will raise `SyntaxError` at runtime in Python. The `...` (Ellipsis) cannot be used as an f-string expression this way, and even if it could it would produce `"BENCH-Ellipsis"` not a real ID.

**Suggested fix:** Replace with `f"BENCH-{uuid.uuid4().hex[:8].upper()}"` or pass in a `benchmark_id` parameter.

---

### B-10 · `guide_piyush.md` `ExperimentPlanner.plan()` accesses `validation.class_balance.get("imbalance_ratio")` but `ValidationResult.class_balance` is a dict with different key structure

**Files:** `guide_piyush.md` §6 Day 2 Hour 2–3, `guide_jayed.md` §6, `contracts/validation_report.json`

**Detail:**

`guide_piyush.md`'s `ExperimentPlanner.plan()`:
```python
imbalance = validation.class_balance.get("imbalance_ratio", 1.0)
```

`guide_jayed.md` defines `ValidationResult.class_balance` as a dict:
```python
class_balance: dict
```

`contracts/validation_report.json` example shows the nested structure as:
```json
"class_balance": {
  "status": "WARNING",
  "class_counts": { "M": 212, "B": 357 },
  "imbalance_ratio": 1.68,
  "minority_percentage": 37.3,
  "severity": "MODERATE"
}
```

So `validation.class_balance.get("imbalance_ratio")` would work IF Jayed implements `class_balance` exactly as the contract shows. But `guide_jayed.md`'s `DatasetValidator` defines `class_balance` inside `ValidationResult` as just a plain `dict` with no specification of what keys it must have.

If Jayed returns the class_balance dict with a slightly different structure (e.g., nesting it differently or omitting `imbalance_ratio` at the top level), Piyush's planner will silently get 1.0 as the default and never apply class weighting even for severely imbalanced datasets like Parkinson's (3.06:1).

**Suggested fix:** Jayed must ensure `class_balance` dict always contains `"imbalance_ratio"` at the top level (as shown in the contract). Add a contract-compliance assertion test.

---

## SECTION 2 — MODERATE ISSUES

---

### M-01 · `guide_naeem.md` `StageProgress.jsx` hardcodes stage keys that don't match the contract OR the guide's own mock data consistently

**Files:** `guide_naeem.md` §6, `contracts/experiment_status.json`

**Detail:**

`StageProgress.jsx` defines:
```javascript
const STAGES = [
  { key:'preprocessing' },
  { key:'classical_training' },
  { key:'quantum_training' },
  { key:'benchmarking' },
  { key:'completed' },
];
```

`MOCK_STATUS_SEQUENCE` uses stages: `'preprocessing'`, `'classical_training'`, `'quantum_training'`, `'benchmarking'`, `'completed'` — consistent with STAGES.

`contracts/experiment_status.json` `stage._examples` lists: `"loading_data"`, `"preprocessing"`, `"training_classical"`, `"training_quantum"`, `"quantum_encoding"`, `"circuit_execution"`, `"inference"`, `"metrics_calculation"`.

Note: contract uses `"training_classical"` not `"classical_training"`, and `"training_quantum"` not `"quantum_training"`. If Piyush emits contract-defined stage strings, `StageProgress.jsx`'s `currentIdx` will always be -1 and every stage will show as pending (○).

**Suggested fix:** Align. Pick one set of stage strings and update both the contract and the frontend component.

---

### M-02 · `guide_shweta.md` profile endpoint stores profile at wrong path relative to what the profiler returns

**Files:** `guide_shweta.md` §6 Hour 2–3, `guide_jayed.md` §6

**Detail:**

`guide_shweta.md`'s `_run_profiling_background()`:
```python
profile_path = storage_path.replace("/raw/original.csv", "/profile.json")
```
This produces: `datasets/DS-000001/profile.json`

`guide_shweta.md`'s `get_dataset_profile()` endpoint checks:
```python
profile_path = os.path.join(config.storage_base_path, f"datasets/{dataset_id}/profile.json")
```
This also looks at `datasets/{dataset_id}/profile.json` — consistent within Shweta's code.

However `guide_arzaan.md`'s `LocalFileStorage.save_dataset()` stores files at:
```
{base_path}/datasets/{dataset_id}/raw/original{ext}
```
The profile would be stored at `{base_path}/datasets/{dataset_id}/profile.json` — one level up from `raw/`. The `storage_path` returned by Arzaan's ingestion is a relative path like `datasets/DS-000001/raw/original.csv`. The replace operation will fail silently if the path separator or the exact string `/raw/original.csv` doesn't match exactly (e.g., Windows backslash separators vs. forward slashes, or different file extensions like `.xlsx`).

**Suggested fix:** Don't derive the profile path from the storage path string manipulation. Instead, use a dedicated `get_profile_path(dataset_id)` helper in `LocalFileStorage`.

---

### M-03 · `guide_jayed.md` `DatasetProfile.to_dict()` output structure doesn't match `contracts/dataset_profile.json` field nesting

**Files:** `guide_jayed.md` §5a vs §6, `contracts/dataset_profile.json`

**Detail:**

`contracts/dataset_profile.json` top-level fields include:
```json
"dimensions": { "rows": 569, "columns": 32 },
"features":   { "numerical": 30, "categorical": 1 },
"target":     { "candidate": "diagnosis", "confidence": "HIGH" },
"task":       { "candidate": "BINARY_CLASSIFICATION", "confidence": "HIGH" }
```

`guide_jayed.md`'s `DatasetProfile` dataclass has flat fields:
```python
rows: int
columns: int
numerical_count: int       ← flat, not nested under "features"
categorical_count: int     ← flat, not nested under "features"
target_candidate: str      ← flat, not nested under "target"
target_confidence: str     ← flat, not nested under "target"
task_candidate: str        ← flat, not nested under "task"
task_confidence: str       ← flat, not nested under "task"
```

If `DatasetProfile.to_dict()` naively serializes the dataclass fields, Shweta's `DatasetProfileResponse` Pydantic model (which expects nested `dimensions`, `features`, `target`, `task` dicts) will fail validation.

This affects `guide_shweta.md`'s:
```python
return DatasetProfileResponse(**profile_data)
```
which requires `profile_data["dimensions"]["rows"]` but would receive `profile_data["rows"]`.

**Suggested fix:** `DatasetProfile.to_dict()` must explicitly build the nested structure matching the contract. This needs to be specified in `guide_jayed.md`'s definition of `to_dict()`.

---

### M-04 · `guide_jayed.md` `FeaturePipelineResult.class_weights` type inconsistency vs config

**Files:** `guide_jayed.md` §5c, `guide_piyush.md` §4

**Detail:**

`guide_jayed.md` §5c defines: `class_weights: dict  # {0: 1.0, 1: 1.68} for imbalance handling`

`guide_piyush.md` §4 expects: `class_weights: dict  # {0: 0.80, 1: 1.34}`

`guide_jayed.md` §6 uses:
```python
from sklearn.utils.class_weight import compute_class_weight
weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
class_weights = dict(zip(np.unique(y_train), weights))
```

`compute_class_weight("balanced")` returns weights that multiply inversely with class frequency. For Breast Cancer (62.7% B, 37.3% M), this gives approximately `{0: 0.80, 1: 1.34}` — matches Piyush's example.

But `guide_jayed.md`'s example shows `{0: 1.0, 1: 1.68}` which does NOT match computed balanced weights. The values `{0: 1.0, 1: 1.68}` suggest a ratio-based approach rather than sklearn's balanced formula. 

This will not break anything at runtime (dict is a dict), but the example is misleading. Piyush's models use `class_weight="balanced"` with sklearn directly (ignoring the class_weights from the pipeline result entirely), so the actual weights may differ from what Jayed computed.

**Suggested fix:** Clarify in `guide_jayed.md` that `class_weights` is informational metadata; Piyush's models should use `class_weight="balanced"` in sklearn which computes weights internally, not the precomputed dict.

---

### M-05 · `guide_piyush.md` Parkinson's feature count inconsistent with contract and guide_jayed.md

**Files:** `guide_piyush.md` §7 mock, `guide_jayed.md` §5c, `contracts/processed_data_schema.md`, `contracts/README.md`

**Detail:**

`contracts/README.md` states: Parkinson's has **22 numerical voice measurements** (22 features).
`contracts/processed_data_schema.md` shows: `X_train (136, 22)` for Parkinson's.
`guide_jayed.md` §5c shows: `X_train (156,22)` for Parkinson's.

But `guide_arzaan.md` §6 step 13 says: `parkinsons.csv → 195 rows, 24 cols.`

The actual Parkinson's UCI dataset has 24 columns total (including `name` identifier and `status` target), leaving 22 features after dropping `name` and `status`. So 22 features is correct for model input.

The row counts differ:
- `contracts/processed_data_schema.md`: X_train (136, 22) — implies 70% of 195 ≈ 136 (70/15/15 split)
- `guide_jayed.md`: X_train (156,22) — implies 80% of 195 ≈ 156 (80/20 split)

This is the same B-03 split conflict manifesting in a dataset-specific context.

**Additionally:** `guide_naeem.md` §7 table says Parkinson's has **22 features** — correct. But Arzaan's test step shows `parkinsons.csv → 195 rows, 24 cols` which will confuse Arzaan into thinking there are 24 features when there are actually 22 model features (24 total columns minus `name` and `status`).

**Suggested fix:** Clarify in guide_arzaan.md that Parkinson's has 24 raw columns but only 22 become features after dropping `name` and `status`.

---

### M-06 · `guide_piyush.md` Diabetes dataset: X_train_reduced shape is wrong

**Files:** `guide_jayed.md` §5c, `guide_piyush.md` §7

**Detail:**

`guide_jayed.md` §5c shows:
```
Diabetes: X_train (614,8), X_test (154,8), X_train_reduced (614,8), X_test_reduced (154,8)
```

For the Pima Indians Diabetes dataset with 8 original features (after removing `Outcome` target), after StandardScaler there are 8 scaled features. PCA with `n_components=8` on 8 features produces 8 components — which is just a rotation, not a reduction. So `X_train_reduced == X_train` (same shape). This is technically correct but misleading.

`guide_piyush.md` §7 mock uses `n_feat=30, n_comp=8` for all datasets, which is wrong for Diabetes (which only has 8 features). If PCA n_components=8 is applied to a dataset that already has only 8 features, sklearn's PCA will produce 8 components correctly, but the quantum model would be trained on the same 8 features as the classical model with no actual dimensionality reduction benefit.

**More critically:** `guide_jayed.md`'s `FeaturePipeline` with `n_components=8` will fail on Diabetes's 8-feature dataset if the PCA variance threshold check tries to explain 94% variance with 8 components from 8 inputs — PCA needs `n_components <= n_features`. This works fine (n_components=8, n_features=8 is valid), but the `variance_retained` assertion `> 0.70` would give 1.0 (100%), which is vacuously true and potentially confusing.

**Suggested fix:** Document in guides that for Diabetes (8 features), PCA n_components=8 is a no-op dimensionality reduction. The platform should use `n_components=min(n_components, n_features)` logic.

---

### M-07 · `contracts/validation_report.json` `example_heart_disease` shows `class_balance.severity="BALANCED"` — not a defined enum value

**Files:** `contracts/validation_report.json`

**Detail:**

`contracts/validation_report.json` `field_definitions` states:
```
"class_balance.imbalance_ratio": "float: Majority:minority class ratio"
```

The `example_heart_disease` uses:
```json
"class_balance": {
  "class_counts": { "0": 138, "1": 165 },
  "imbalance_ratio": 1.20,
  "severity": "BALANCED"
}
```

But `guide_jayed.md` §6 defines severity levels as:
```python
< 1.5 → PASS, 1.5–3 → MODERATE WARNING, 3–10 → HIGH WARNING, > 10 → EXTREME
```

The contract uses `"BALANCED"` as a severity value but the guide uses `"PASS"` for the same condition. Two different string values for the same state.

`contracts/validation_report.json`'s `field_definitions` also says severity is:
```
"enum: PASS (0%), LOW (0-5%), MODERATE (5-20%), HIGH (>20%)"
```
(this refers to missing_values.severity, not class_balance.severity)

There is no defined enum for `class_balance.severity` in the field_definitions. The contract example uses `"BALANCED"` but Jayed's guide uses `"PASS"`. Naeem's frontend or any code checking for this value will not find a match.

**Suggested fix:** Define a consistent enum for `class_balance.severity`: `"BALANCED" | "MODERATE" | "HIGH" | "EXTREME"` or `"PASS" | "MODERATE" | "HIGH" | "EXTREME"`. Pick one and apply everywhere.

---

### M-08 · `guide_piyush.md` experiment status endpoint returns `experiment_status.json` contract shape but Piyush's `ExperimentManager.get_status()` produces fields from a different schema

**Files:** `guide_piyush.md` §5d, §6 Day 2 Hour 3–5, `contracts/experiment_status.json`

**Detail:**

`guide_piyush.md` §5d says the status endpoint must return the `experiment_status.json` contract shape including `circuit_executions`, `current_model`, `completed_models`. But as established in B-01, these fields don't exist in the actual contract.

Additionally, `guide_piyush.md`'s `ExperimentManager.get_status()` stub says it "Returns experiment_status.json contract shape" but the implementation is left as `...`. There's no specification of how `current_model`, `completed_models`, and `circuit_executions` get tracked during execution.

The `ExperimentExecutor.run()` executes models sequentially but never updates a shared "current status" object that the polling endpoint can read. With background task execution, there's a race condition: the executor runs in a background thread/task and writes to SQLite, but there's no mechanism described for streaming or updating `current_model` and `completed_models` in real time.

**Suggested fix:** Add a `progress_data` JSON column to the Experiment SQLite table. Have the executor update it after each model completes. The `get_status()` endpoint reads from this column.

---

### M-09 · `guide_radha.md` cost report field `comparison_classical_baseline.classical_training_secs` doesn't match `contracts/cost_report.json`

**Files:** `guide_radha.md` §5b and §6, `contracts/cost_report.json`

**Detail:**

`contracts/cost_report.json` example uses:
```json
"comparison_classical_baseline": {
  "classical_model": "RandomForest",
  "classical_training_seconds": 42,    ← _seconds suffix
  "quantum_training_seconds": 842,     ← _seconds suffix
  "speedup_classical": 20.0,
  "verdict": "..."
}
```

`guide_radha.md` §6 `CostReportGenerator.generate()` produces:
```python
"comparison_classical_baseline": {
  "classical_model":          best_classical_name,
  "classical_training_secs":  round(...),   ← _secs suffix (truncated)
  "quantum_training_secs":    round(...),   ← _secs suffix (truncated)
  "verdict":                  verdict,
}
```

The field names are `classical_training_secs` vs `classical_training_seconds` — different suffixes. Naeem's frontend (which reads the cost report) and the contract both expect `_seconds`.

Also: `speedup_classical` field is in the contract but missing from Radha's code.

**Suggested fix:** Rename `_secs` to `_seconds` in Radha's code. Add `"speedup_classical"` field calculation.

---

### M-10 · `guide_naeem.md` mock status sequence uses `completed_models` (list) but contract field is absent; the frontend will break when flipping MOCK_MODE=false

**Files:** `guide_naeem.md` §4f mock, `contracts/experiment_status.json`

**Detail:**

`guide_naeem.md`'s `MOCK_STATUS_SEQUENCE` entries all include `completed_models: [...]` and `current_model: "..."`. When `MOCK_MODE=false`, Naeem's frontend code reads:
```javascript
completedModels={status.completed_models}
circuitExecutions={status.circuit_executions}
```

`contracts/experiment_status.json` has neither `completed_models`, `current_model`, nor `circuit_executions` (it has `circuit_executions_so_far`). Real API responses will have `circuit_executions_so_far: null` (not `circuit_executions: 8320`), causing `status.circuit_executions` to be `undefined`, breaking the display.

**Suggested fix:** Add `?? 0` fallback for all non-contract fields in the frontend: `status.circuit_executions ?? status.circuit_executions_so_far ?? 0`. Agree with Piyush on the field names before integration day.

---

### M-11 · `guide_shweta.md` and `guide_arzaan.md` disagree on who stores the `is_duplicate` and `duplicate_of` fields in the database

**Files:** `guide_arzaan.md` §5, `guide_shweta.md` §5

**Detail:**

`guide_arzaan.md` §5 Database record shape:
```python
id, display_id, original_filename, container_type, file_size_bytes, sha256,
raw_storage_path, upload_timestamp, status, created_by
```
Note: `is_duplicate` and `duplicate_of` are **not listed** in Arzaan's ORM model definition.

`guide_shweta.md` §5 Detail response requires:
```json
{
  "is_duplicate": false,
  "duplicate_of": null
}
```

`guide_shweta.md` §6 accesses:
```python
is_duplicate=ds.is_duplicate if hasattr(ds, 'is_duplicate') else False,
duplicate_of=ds.duplicate_of if hasattr(ds, 'duplicate_of') else None
```

The `hasattr` check is a silent fallback for the missing fields. But the upload contract also requires `is_duplicate` in the response. Arzaan's ingestion service returns `is_duplicate` in the response dict, but if it's never persisted to the DB, then `GET /api/datasets/{id}` will always return `is_duplicate=False` even for actual duplicates.

**Suggested fix:** Add `is_duplicate: bool` and `duplicate_of: Optional[str]` to Arzaan's SQLAlchemy `Dataset` ORM model. Update guide_arzaan.md §5 field list.

---

### M-12 · NOTES.md item #8 (Backend type consistency) silently resolved differently in different guides

**Files:** `contracts/NOTES.md` §8, `guide_piyush.md`, `contracts/model_result.json`, `contracts/experiment_config.json`

**Detail:**

NOTES.md item #8 flags that phases 8, 13, and 15 use three different names for the same backends:
- Phase 8: `LOCAL_SIMULATOR`, `REMOTE_SIMULATOR`, `REAL_QUANTUM_HARDWARE`
- Phase 13: `LOCAL_SIMULATOR`, `CLOUD_SIMULATOR`, `HARDWARE`
- Phase 15: `Local Simulator`, `Cloud Simulator`, `Real Hardware`

The contracts and guides resolved this silently without updating NOTES.md:
- `contracts/model_result.json` uses `"LOCAL_SIMULATOR"` — SCREAMING_SNAKE_CASE
- `contracts/experiment_config.json` uses `"LOCAL_SIMULATOR"`, `"CLOUD_SIMULATOR"`, `"HARDWARE"` — Phase 13 naming
- `guide_piyush.md` hardcodes `backend_type="LOCAL_SIMULATOR"` — consistent
- `guide_naeem.md` shows `backend_type:'LOCAL_SIMULATOR'` — consistent

However `experiment_config.json` uses `"HARDWARE"` while `model_result.json` doesn't show a hardware example. Also `"REMOTE_SIMULATOR"` from Phase 8 appears nowhere in any contract or guide — silently dropped without acknowledgement.

**Suggested fix:** Mark NOTES.md item #8 as RESOLVED with the chosen values: `LOCAL_SIMULATOR | CLOUD_SIMULATOR | QUANTUM_HARDWARE`. Update any contract that still uses just `HARDWARE`. Add `REMOTE_SIMULATOR` → `CLOUD_SIMULATOR` mapping note.

---

### M-13 · NOTES.md item #9 (Experiment ID prefixes) is unresolved and guides are inconsistent

**Files:** `contracts/NOTES.md` §9, `guide_piyush.md` §6, `guide_arzaan.md` §6

**Detail:**

NOTES.md item #9: "EXP-C-000001 for classical vs EXP-001 (no prefix) vs EXP-Q-000001"

`guide_piyush.md` §5b shows `"EXP-Q-000001"` as an example experiment_id in model_result.json.
`guide_piyush.md` §5d shows `"EXP-000001"` (no type prefix) as an example experiment_status.json.
`guide_arzaan.md` §6 step 13 test uses `"EXP-000001"` format (no prefix).
`guide_naeem.md` throughout uses `"EXP-000001"` (no prefix).

Three different formats in active use across the guides. The experiment_id format is used as a primary key and folder name (`artifacts/experiments/{experiment_id}/`). If Piyush creates `EXP-C-000001` and Naeem polls `GET /experiments/EXP-000001/status`, they will get 404.

**Suggested fix:** Standardize on one format. Recommend `EXP-{SEQUENCE}` (simple, no type prefix) for simplicity, since the type is already stored in the `model_type` field. Update all guides.

---

### M-14 · `guide_jayed.md` `DatasetProfile` has `missing_by_column` but `contracts/dataset_profile.json` has `missing_values.by_column` (nested differently)

**Files:** `guide_jayed.md` §6 `DatasetProfile` dataclass, `contracts/dataset_profile.json`

**Detail:**

`guide_jayed.md` `DatasetProfile` dataclass fields:
```python
missing_total: int
missing_percentage: float
missing_by_column: dict    ← flat field
```

`contracts/dataset_profile.json` nests these under `missing_values`:
```json
"missing_values": {
  "total": 0,
  "percentage": 0.0,
  "by_column": {}
}
```

`DatasetProfile.to_dict()` must produce the nested form, but the dataclass flat form uses `missing_total`, `missing_percentage`, `missing_by_column` — different names than `total`, `percentage`, `by_column`.

Similarly:
- Dataclass: `duplicate_count: int` → Contract: `"duplicates": { "candidate_count": 0 }`
- Dataclass: `warnings: List[str]` → Contract: `"warnings": ["Class imbalance detected..."]` — same structure, fine

**Suggested fix:** Specify `DatasetProfile.to_dict()` explicitly in guide_jayed.md, showing the exact mapping from dataclass fields to contract JSON keys.

---

### M-15 · `guide_jayed.md` `FeaturePipelineResult.to_dict()` returns `feature_names` and `reduced_feature_names` as lists but `contracts/processed_data_schema.md` says feature names are stored separately as `feature_names.json`

**Files:** `guide_jayed.md` §5c, `contracts/processed_data_schema.md`

**Detail:**

`contracts/processed_data_schema.md` storage section:
```
datasets/DS-000001/processed/PREP-000001/
├── feature_names.json   # JSON array of strings
├── metadata.json        # JSON object
└── preprocessing.json
```

`guide_jayed.md`'s `FeaturePipelineResult.to_dict()` returns `feature_names` and `reduced_feature_names` inline within the dict. This is fine for in-memory use but means feature names aren't stored separately as the contract specifies. Radha's explainability needs `feature_names` — she accesses it via `processed.feature_names` (Python object) not from a file. This is fine for the Python integration but mismatches the storage contract.

If anyone tries to load `feature_names.json` from disk (following the contract's storage format), it won't exist.

**Suggested fix:** Have `FeaturePipeline.fit_transform()` also save `feature_names.json` to the preprocessing artifact path, in addition to including it in the result dataclass.

---

## SECTION 3 — MINOR ISSUES

---

### N-01 · `guide_arzaan.md` and `guide_shweta.md` use different field names for the ORM `Dataset.original_filename` column

**Files:** `guide_arzaan.md` §5, `guide_shweta.md` §6

**Detail:**

`guide_arzaan.md` §5 ORM model: field is `original_filename`.
`guide_shweta.md` §6: accesses `ds.original_filename` — consistent.
`guide_shweta.md` §5 Detail response uses `"filename"` as the JSON key — consistent with contract.

No actual breakage, but the ORM field name (`original_filename`) vs the JSON response field name (`filename`) could confuse implementers. Suggest adding a comment to both guides noting this mapping.

---

### N-02 · `guide_piyush.md`'s `_result_summary()` helper is called but never defined

**Files:** `guide_piyush.md` §6 Day 2 Hour 1–2

**Detail:**

`RecommendationEngine.recommend()` calls:
```python
"classical_best": _result_summary(bc),
"quantum_best":   _result_summary(bq),
...
"recommendation_text": _generate_text(classification, bc, bq),
```

Neither `_result_summary` nor `_generate_text` is defined anywhere in the guide. These are called as module-level functions but their implementations are omitted.

**Suggested fix:** Define both helper functions explicitly in the guide, or mark them as `# TODO: implement` so Piyush knows they're stubs.

---

### N-03 · `contracts/NOTES.md` item #7 (Calibrated vs Uncalibrated Probabilities) is still unresolved

**Files:** `contracts/NOTES.md` §7, `contracts/model_result.json`, `contracts/explanation.json`, `guide_piyush.md`

**Detail:**

NOTES.md item #7 asks: "Who is responsible for calibration (Phase 10, Phase 11, or Phase 12)?"

Current state:
- `contracts/model_result.json` has `prediction_scores` (uncalibrated)
- `contracts/explanation.json` has `confidence_calibration.is_calibrated: false`
- `guide_piyush.md` never performs calibration
- `guide_radha.md` never performs calibration but adds the disclaimer "Score is uncalibrated"
- `guide_naeem.md` shows "Uncalibrated — not a probability" in the UI

The ambiguity is resolved by omission: nobody calibrates. This is fine for MVP but the NOTES.md item still shows as unresolved (no ✅ marker), which could cause confusion for future implementers.

**Suggested fix:** Add a status update to NOTES.md item #7: "RESOLVED FOR MVP — No calibration in v1. All scores are uncalibrated. Phase 12 adds disclaimer to explanation output."

---

### N-04 · `contracts/NOTES.md` item #5 (PCA candidate count selection) is silently resolved as "single value" by config but contract still implies multiple candidates

**Files:** `contracts/NOTES.md` §5, `contracts/experiment_config.json`, `config.yaml`

**Detail:**

`config.yaml`: `candidate_dimensions: [4, 8]` — suggests multiple candidates are evaluated.
`guide_jayed.md` §4 input: `quantum.candidate_dimensions: [4, 8]`
`guide_piyush.md` §4: `n_components = n_components or q_config.get('candidate_dimensions', [8])[0]` — takes only the first element.

So in practice only one dimension is evaluated per experiment. But `config.yaml` still lists `[4, 8]` implying two candidates will be generated, which doesn't happen.

**Suggested fix:** Either change `config.yaml` to `candidate_dimensions: 8` (single value), or implement multi-representation experiments. Mark NOTES.md item #5 as RESOLVED with the chosen approach.

---

### N-05 · `guide_naeem.md` `MOCK_EXPLANATION` global_importance has a duplicate `mean_radius` entry

**Files:** `guide_naeem.md` §6 `MOCK_EXPLANATION`

**Detail:**

```javascript
global_importance:[
  { feature_name:'worst_radius',          importance:0.187 },
  { feature_name:'worst_concave_points',  importance:0.156 },
  { feature_name:'mean_concave_points',   importance:0.134 },
  { feature_name:'worst_perimeter',       importance:0.121 },
  { feature_name:'mean_radius',           importance:0.098 },  ← also appears in feature_importance
],
```

`feature_importance` also has `{ feature_name:'mean_radius', importance:0.312, effect:'positive' }`. The same feature appearing in both arrays at different importance values could confuse developers reading the mock.

**Suggested fix:** Use distinct feature names in `global_importance` vs `feature_importance` mock arrays.

---

### N-06 · `contracts/NOTES.md` item #11 (Explainability method selection) is silently resolved by guide_radha.md but not marked resolved

**Files:** `contracts/NOTES.md` §11, `guide_radha.md` §6

**Detail:**

NOTES.md item #11: "What defines 'compatible' for SHAP?"

`guide_radha.md` answers this implicitly:
- RandomForest → `shap.TreeExplainer`
- LogisticRegression → `shap.LinearExplainer`
- SVM → `shap.KernelExplainer` (fallback)
- VQC → perturbation-based (not SHAP)

This resolves the ambiguity but NOTES.md still shows it as unresolved (⚠️).

**Suggested fix:** Update NOTES.md item #11 with ✅ RESOLVED status and the decision matrix.

---

### N-07 · `guide_shweta.md` Phase 1 API path cited as `/api/v1/datasets` but all guides use `/api/datasets` (no version prefix)

**Files:** `guide_shweta.md` §2, `contracts/README.md`, all other guides

**Detail:**

`guide_shweta.md` §2 phase citation says:
> "Phase 1, §28–30 (phase1.md): API design — `POST /api/v1/datasets`, `GET /api/v1/datasets/{dataset_id}`"

Phase1.md §28 actually says `POST /api/v1/datasets` with the `/v1/` version prefix.

But `guide_shweta.md`'s own API design (§5) uses `POST /api/datasets/upload` (no `/v1/`), as does `guide_naeem.md`, `backend/main.py`, and all contracts.

The phase doc uses `/v1/` but the implementation does not. This is a minor discrepancy (the version prefix was intentionally omitted from the MVP) but the guide's phase citation creates confusion.

**Suggested fix:** Add a note in guide_shweta.md: "Phase 1.md uses /api/v1/ prefix but the MVP omits API versioning for simplicity."

---

### N-08 · `guide_piyush.md` cites Phase 11 for benchmarking but omits Radha's Phase 12/13 from the phase citation section

**Files:** `guide_piyush.md` §2

**Detail:**

Piyush owns Phase 11 (benchmarking) which is correct. However `guide_piyush.md` §2 also includes the `recommendation.json` output, which by the README.md contract table is described as "Phase 11 Benchmark" output. Radha's guide says she produces `cost_report.json` (Phase 13) and `explanation.json` (Phase 12).

The phase boundaries are consistent. The minor issue is that `guide_piyush.md` §2 cites Phase 11.md §34 ("Decision Summary") and §41 ("Final Decision Categories") but these describe the recommendation output — and `guide_piyush.md`'s scope section correctly owns this. No factual error, just worth confirming there's no overlap with Radha's Phase 11 ownership.

**Suggested fix:** No change needed. Confirming: Piyush owns benchmark + recommendation (Phase 11); Radha owns explainability (Phase 12) + cost report (Phase 13).

---

### N-09 · `guide_radha.md` `QuantumExplainer.circuit_info()` returns `n_layers` but `contracts/explanation.json` `quantum_circuit_explanation` does not have an `n_layers` field

**Files:** `guide_radha.md` §6, `contracts/explanation.json`

**Detail:**

`guide_radha.md`'s `circuit_info()` returns:
```python
{
  "qubits": ...,
  "n_layers": ...,      ← extra field not in contract
  "circuit_depth": ...,
  "encoding_method": ...,
  ...
}
```

`contracts/explanation.json` `quantum_circuit_explanation` has: `qubits`, `circuit_depth`, `encoding_method`, `feature_to_qubit_mapping`, `circuit_diagram_url`.

No `n_layers` field in the contract. Adding it won't break anything (Naeem's frontend simply won't display it unless explicitly coded), but it's a contract drift.

**Suggested fix:** Either add `n_layers` to the contract (it's useful information) or remove it from `circuit_info()`.

---

### N-10 · `guide_radha.md` `explanation_timestamp` format uses `.isoformat() + "Z"` which is incorrect for UTC timestamps in Python

**Files:** `guide_radha.md` §6 `_build_explanation_dict`

**Detail:**

```python
"explanation_timestamp": datetime.utcnow().isoformat() + "Z"
```

`datetime.utcnow()` returns a naive datetime with no timezone info. `.isoformat()` on a naive datetime produces `"2026-09-10T16:45:23.789000"` — then appending `"Z"` produces `"2026-09-10T16:45:23.789000Z"` which is not valid ISO 8601 (the microseconds are 6 digits, and naive datetime + Z is technically incorrect). Most parsers will handle it, but it's better practice to use `datetime.now(timezone.utc).isoformat()` which produces the properly formatted UTC timestamp.

This matches the contract `_example`: `"2026-09-10T16:45:23.789Z"` — note 3-digit milliseconds vs Python's 6-digit microseconds.

**Suggested fix:** Use `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"` to produce 3-digit milliseconds matching the contract example format.

---

## SECTION 4 — UNRESOLVED NOTES.md AMBIGUITIES

The following items from `contracts/NOTES.md` remain **unresolved in practice** — the guides and contracts have silently diverged or made different assumptions without updating NOTES.md:

| # | NOTES.md Item | Status | How guides resolved it (or didn't) |
|---|---|---|---|
| 1 | Target column name ambiguity | ✅ Effectively resolved | All guides and adapters use confirmed names: `diagnosis`, `target`/`num`, `status`, `Outcome`. Not marked resolved in NOTES.md. |
| 2 | Train/validation/test split ratios | ❌ **UNRESOLVED — BLOCKING (see B-03)** | Contract uses 70/15/15; all guides and config use 80/20. Active conflict. |
| 3 | Feature count after encoding | ⚠️ Partially resolved | profile.columns remains raw count; feature_names list gives post-encoding count. Not documented. |
| 4 | Quantum circuit execution count semantics | ⚠️ Silently resolved | guide_piyush.md counts `self._circuit_executions += len(X_batch)` — each sample is 1 execution regardless of shots. Not documented in NOTES.md. |
| 5 | PCA component count selection | ⚠️ Silently resolved | Guides take `[0]` of candidate_dimensions list. NOTES.md still shows as open. |
| 6 | Class weighting strategy | ⚠️ Partially resolved | guide_jayed.md computes class_weights; guide_piyush.md ignores them and uses `class_weight="balanced"` in sklearn. Dual approach not reconciled. |
| 7 | Calibrated vs uncalibrated probabilities | ⚠️ Silently resolved by omission | Nobody calibrates; guides add disclaimers. NOTES.md still shows as open. |
| 8 | Backend type consistency | ⚠️ Mostly resolved | Guides use LOCAL_SIMULATOR consistently. NOTES.md shows as open. |
| 9 | Experiment ID prefixes | ❌ **UNRESOLVED — MODERATE (see M-13)** | Three different formats used across guides. |
| 10 | Resource monitoring granularity | ⚠️ Silently resolved | All guides use peak values + total time. Not documented. |
| 11 | Explainability method selection | ✅ Resolved by guide_radha.md | Decision matrix defined but NOTES.md not updated. |
| 12 | Demo mode vs benchmark mode | ❌ **UNRESOLVED** | No guide implements execution_mode field. guide_naeem.md has MOCK_MODE but that's a frontend dev convenience, not the same concept. |
| 13 | Statistical significance testing | ❌ **UNRESOLVED** | No guide implements repeated runs or confidence intervals. Phase 11 requirement silently dropped from MVP. |
| 14 | Quantum encoding parameter ranges | ⚠️ Silently resolved | guide_piyush.md uses `np.clip(X, -3, 3) / 3.0` in AngleEncoder. Not in any contract. |
| 15 | Quantum vs Hybrid model classification | ⚠️ Silently resolved | guide_piyush.md VQC returns `model_type="QUANTUM"`. Not documented in NOTES.md. |

**Summary:** 4 items unresolved with code impact (items 2, 9, 12, 13), 8 items silently resolved without updating NOTES.md, 3 items genuinely resolved.

---

## SECTION 5 — OWNERSHIP / BOUNDARY GAPS

### OG-01 · Zero producers for: `representation_id` on `ModelResult`

`contracts/model_result.json` requires `representation_id`. `guide_piyush.md` hardcodes `"REP-000001"` and `"QREP-000001"` as constants. Nobody generates actual representation IDs. Jayed's `FeaturePipeline` returns `preprocessing_id` but no `representation_id`.

### OG-02 · Zero producers for: experiment `plan` object stored persistently

`guide_radha.md` §4 requires `plan["decision_trace"]["rules_applied"]` to build the pipeline trace. The plan is created by Piyush's `ExperimentPlanner.plan()` but there's no guidance on where it gets stored. If Radha's explainability runs after the executor completes, she needs the plan from somewhere — but neither guide specifies that the plan dict is saved to `artifacts/experiments/{id}/plan.json`.

### OG-03 · Zero producers for: `profile_id` on `DatasetProfile`

`contracts/dataset_profile.json` requires `profile_id` (e.g., `"PROFILE-000001"`). `guide_jayed.md`'s `DatasetProfile` dataclass has a `profile_id` field but no guidance on how to generate unique profile IDs. Jayed's build order doesn't include a `ProfileRepository` or ID generation step.

### OG-04 · Duplicate producer for: ingestion route in `guide_arzaan.md` vs `guide_shweta.md`

`guide_arzaan.md` §2 cites "API Design (§78): POST /api/datasets/upload" as Arzaan's responsibility. `guide_shweta.md` §2 also cites the same endpoint and owns the route handler. The route handler is Shweta's but the endpoint logic is Arzaan's — this is intended. However `guide_arzaan.md` §2 should clarify that Arzaan owns the service layer, not the route handler, to avoid both developers implementing the same FastAPI route.

### OG-05 · Zero producers for: `benchmark_id` on `recommendation.json`

`contracts/recommendation.json` requires `"benchmark_id": "BENCH-000001"`. `guide_piyush.md`'s `RecommendationEngine.recommend()` returns `"benchmark_id": f"BENCH-{...}"` (broken syntax, see B-09) — no valid benchmark ID is generated. There's no `BenchmarkRepository` or ID generation in any guide.

---

## SECTION 6 — MISSING HANDOFFS

### MH-01 · `guide_radha.md` requires `X_train` from `FeaturePipelineResult` but has no mechanism to receive it after experiment completion

`guide_radha.md`'s `ExplainabilityEngine._explain_classical()` needs `processed.X_train` and `processed.X_test` to fit the SHAP explainer. The `FeaturePipelineResult` is an in-memory Python object created during `ExperimentExecutor.run()`. After the executor finishes and the results are stored to disk, the `FeaturePipelineResult` object is gone. Radha's endpoints are called after the fact (via `GET /api/experiments/{id}/explanation`) — there's no `FeaturePipelineResult` object available at that point.

Neither guide specifies saving `X_train.npy`, `X_test.npy`, etc. to disk as part of the executor's artifact storage, nor how Radha would reload them.

**Suggested fix:** The executor must save `X_train.npy`, `X_test.npy`, `X_train_reduced.npy`, `X_test_reduced.npy`, and `feature_names.json` to `artifacts/experiments/{id}/data/` during execution. Add this to guide_piyush.md's executor artifact storage step.

### MH-02 · `guide_shweta.md` requires `DatasetIngestionService` class but `guide_arzaan.md` defines a function-based interface

See B-08 for full detail. The handoff contract between Arzaan (ingestion service) and Shweta (route handler) is unspecified — Shweta assumes a class, Arzaan describes functions.

### MH-03 · `guide_naeem.md` `GET /experiments/{id}/results` expects nested `results.models.{name}.metrics` but `guide_piyush.md` API route returns unspecified shape

`guide_piyush.md`'s `get_results()` endpoint stub says "Return full model comparison results" with implementation as `...`. The exact JSON serialization shape is not specified. `guide_naeem.md` expects `results.models.vqc.metrics.recall` but if Piyush serializes `ModelResult` differently (e.g., flat structure), Naeem's frontend will silently show `undefined` for all metrics.

**Suggested fix:** Add a concrete `ExperimentResultsResponse` Pydantic model to `guide_piyush.md` that exactly matches what `guide_naeem.md` §4g expects.

---

## SECTION 7 — UNIT / TYPE MISMATCHES

### UT-01 · `inference_time_seconds` vs `inference_time_ms` confusion

- `contracts/model_result.json`: `"inference_time_seconds": { "_example_classical": 0.012 }` — seconds
- `contracts/cost_report.json`: `"inference": { "avg_time_ms": 45 }` — milliseconds
- `guide_radha.md` §6: `"avg_time_ms": round(vqc.inference_time_seconds * 1000, 1)` — converts seconds to ms ✓

This is consistent but the two units in two contracts could confuse developers who read one contract and build against the other.

- `guide_naeem.md` §4g: `(r.resource_usage.inference_time_seconds*1000).toFixed(0)+'ms'` — converts correctly ✓

No breakage, but the unit inconsistency between contracts is a maintenance risk.

### UT-02 · `elapsed_seconds` type: `float` in contract vs `integer` in guide mocks

- `contracts/experiment_status.json`: `"elapsed_seconds": { "_type": "float", "_example": 412.5 }`
- `guide_naeem.md` mock: `elapsed_seconds: 8` / `elapsed_seconds: 412` — integers
- `guide_piyush.md` §5d: `"elapsed_seconds": 412` — integer

JavaScript treats float vs integer transparently, but if a Pydantic model on the backend enforces `float` and receives an integer, it'll coerce silently. Not a runtime bug, but worth noting for type-strict consumers.

### UT-03 · `memory_peak_mb` is `float` throughout, but `guide_radha.md` converts to `ram_peak_gb` without matching field name

- `contracts/model_result.json`: `"memory_peak_mb": { "_type": "float" }`
- `contracts/cost_report.json`: `"ram_peak_gb"` (different field name, different unit)
- `guide_radha.md`: `"ram_peak_gb": round(vqc.memory_peak_mb / 1024, 2)` — converts MB to GB ✓

The conversion is correct but `ram_peak_gb` in the cost report and `memory_peak_mb` in the model result are two different names for the same measurement. Naeem's frontend will need to know which contract's field to read from which endpoint.

### UT-04 · `file_size_bytes` is always `int` — consistent across all files ✓

No issues found. All guides and contracts use `int` for file sizes.

### UT-05 · Status enum case — all contracts and guides use SCREAMING_SNAKE_CASE consistently ✓

No issues found. `"REGISTERED"`, `"PASS_WITH_WARNINGS"`, `"BLOCKED"`, `"COMPLETED"`, `"QUANTUM_ADVANTAGE"` all SCREAMING_SNAKE_CASE throughout.

### UT-06 · `quality_score` type: `int` in contract, enforced?

- `contracts/validation_report.json`: `"quality_score": "integer 0-100"`
- `guide_jayed.md`: `quality_score: int  # 0-100` — correct
- Score calculation: `Start at 100, subtract: 5 per LOW, 10 per MODERATE, 20 per HIGH, 40 per CRITICAL`
- This can produce negative scores for datasets with multiple critical issues — e.g., 100 - 40 - 40 = 20, fine; but 100 - 40 - 40 - 40 = -20 is possible. The contract says `0-100` but the guide doesn't clamp the value.

**Suggested fix:** Add `quality_score = max(0, quality_score)` in the validator.

---

## SECTION 8 — PHASE CITATION ACCURACY

### PC-01 · `guide_piyush.md` correctly maps Phases 7–11 ✓

Phase 7 (classical models), Phase 8 (quantum models), Phase 9 (experiment planner), Phase 10 (executor), Phase 11 (benchmarking) — all correctly mapped to Piyush.

### PC-02 · `guide_jayed.md` correctly maps Phases 2–6 ✓

Phase 2 (profiling), Phase 3 (validation), Phase 4 (preprocessing), Phase 5 (feature engineering), Phase 6 (reduction) — all correctly mapped to Jayed.

### PC-03 · `guide_arzaan.md` Phase 1 citation is accurate ✓

Phase 1 §9–47 correctly mapped.

### PC-04 · `guide_radha.md` Phase 12–13 correctly mapped ✓

Phase 12 (explainability), Phase 13 (cost/scalability) — correct.

### PC-05 · `guide_naeem.md` Phase 14–15 citations are accurate ✓

Phase 14 §4–6 (user flow), Phase 15 §10–17 (demo mode) — correct.

### PC-06 · `guide_shweta.md` Phase 1 §28–30 citation: minor path discrepancy

Phase 1.md §28 shows API path `/api/v1/datasets` but Shweta's implementation uses `/api/datasets`. Already covered in N-07.

### PC-07 · `guide_piyush.md` MVP Phase citation accuracy issue — "MVP Phase 14–15" does not match what those sections cover

`guide_piyush.md` §2 cites "MVP Phase 14–15 (§35–37): Metrics". However the MVP implementation plan §35–37 is titled "PHASE 14 — Metrics" and "PHASE 15 — Classical vs Quantum Benchmark". These are accurate for Piyush's scope. The section content does discuss these metrics. Correct.

---

## APPENDIX: Summary Statistics

| Category | Count |
|---|---|
| BLOCKING issues | 10 (B-01 through B-10) |
| MODERATE issues | 15 (M-01 through M-15) |
| MINOR issues | 10 (N-01 through N-10) |
| UNRESOLVED NOTES.md items (with code impact) | 4 (items 2, 9, 12, 13) |
| UNRESOLVED NOTES.md items (silently resolved, needs doc update) | 8 |
| Ownership gaps | 5 (OG-01 through OG-05) |
| Missing handoffs | 3 (MH-01 through MH-03) |
| Unit/type mismatches | 6 (UT-01 through UT-06, 1 actual issue) |
| **TOTAL distinct issues** | **35+** |

| Premise finding | |
|---|---|
| /mocks/ folder exists | ❌ Does not exist — 40 mock files are absent |
| Contracts exist | ✅ All 10 contracts present |
| Phase docs exist | ✅ All 15 phase docs present |
| Guide files exist | ✅ All 6 guide files present |

---

*Audit completed. No fixes applied. All findings are reports only.*
