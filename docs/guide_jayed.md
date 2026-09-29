# Developer Guide — Jayed
## Scope: Data Pipeline (Profiling, Validation, Preprocessing, Adapters, Feature Pipeline, PCA/Reduction)

---

## 1. Scope Summary

You own the entire **data understanding and preparation pipeline** — every transformation that happens to a dataset between Arzaan's ingestion and Piyush's model training. This covers five distinct phases: (1) **Profiling** — inspect a registered CSV and produce a structured description of its modality, target candidate, class distribution, missing values, and data types; (2) **Validation** — determine whether the dataset is safe and usable, flag warnings and blockers without modifying any data; (3) **Preprocessing** — apply the actual transformations (imputation, scaling, encoding, splitting) using a reproducible pipeline fitted only on training data; (4) **Dataset Adapters** — handle the quirks of each of the four reference datasets (Breast Cancer has an `id` column to drop, Heart Disease uses `target` or `num`, Parkinson's has a `name` subject column for grouped splitting, Diabetes uses `Outcome`); (5) **Feature pipeline and PCA/reduction** — build the scikit-learn pipeline that reduces features to quantum-compatible dimensions (4 or 8 components from config) and exposes the train/test NumPy arrays that Piyush's models consume. Your final output — the `FeaturePipelineResult` dataclass containing `X_train`, `X_test`, `y_train`, `y_test`, `X_train_reduced`, `X_test_reduced` — is the most critical handoff in the entire platform: if the shapes are wrong or data leaks across the split, every downstream model result is scientifically invalid.

---

## 2. Exact Phase Numbers

From the **architecture document**:
- **Phase 2** (phase2.md): Dataset Profiling & Discovery — Modules 2.1–2.13: Dataset Loader (§4), Package Inspection (§5), Modality Detection (§6–7), Tabular Schema Analysis (§8), Statistics (§9), Target/Label Discovery (§10–11), Task Discovery (§12–13), Class Distribution (§14), Duplicate Candidates (§15), Dataset Profile Output (§20).
- **Phase 3** (phase3.md): Dataset Validation & Quality Assessment — Modules 3.1–3.10: Target Validation (§5–7), Schema Validation (§8–9), Missing Data Assessment (§10–12), Duplicate Assessment (§13), Class Balance Validation (§14–15), Value Range Validation (§16–17), Outlier Assessment (§18), Leakage Detection (§19–20), Train/Test Feasibility (§21–22), Quality Score (§27), Critical vs Non-Critical (§28), Phase 3 Output (§29).
- **Phase 4** (phase4.md): Preprocessing Pipeline — Modules 4.1–4.8: Decision Engine (§7), Splitting strategy (§9–11), Missing value handling (§12–13), Categorical encoding (§14–15), Numerical scaling (§15), Outlier handling (§16), Duplicate handling (§17), Class imbalance (§18). The critical rule: **split before fitting any transformer** (§6).
- **Phase 5** (phase5.md): Feature Engineering — Modules 5.1–5.8: Feature Inventory (§6), Candidate generation (§8), Domain-aware features (§14), Feature registry (§20–21), Lineage (§21). For MVP: focus on the tabular path, not CNN embeddings.
- **Phase 6** (phase6.md): Feature Selection & Dimensionality Reduction — Modules 6.1–6.10: Low-variance filtering (§10), Correlation analysis (§11), Univariate selection (§13), PCA (§17), Multiple candidate dimensions (§19), Quantum-compatible representation (§20–21), No data leakage rule (§32), Phase 6 output (§37).

From the **MVP implementation plan**:
- **MVP Phase 2** (§10–11): Profiling — rows, columns, dtypes, missing, duplicates, target candidates, class distribution. MUST calculate from actual CSV, never hardcode.
- **MVP Phase 3** (§12): Validation — readable, target exists, binary classification, numeric features available.
- **MVP Phase 4–7** (§13–17): Target detection, adapters, data cleaning, train/test split strategy.
- **MVP Phase 7** (§17): Split — 80/20 stratified default; Parkinson's uses group-aware split if subject column present.
- **MVP Phase 8** (§18): Preprocessing — `StandardScaler`, optional `OneHotEncoder`.
- **MVP Phase 8** (§19–21): Feature reduction — PCA to 4 or 8 components (from config), configurable. Must be fitted only on training data.
- **MVP Phase 9** (§22–26): Planner reads profile/validation to produce the experiment plan.
- **MVP Phase 16** (§50): Leakage prevention — never PCA entire dataset before splitting.
- **Dataset Adapters** (§14): `BreastCancerAdapter`, `HeartDiseaseAdapter`, `ParkinsonsAdapter`.

---

## 3. Files / Folders You Must Create

All paths relative to `d:\projects\SIH2026\mvp\`:

```
backend/
├── data/
│   ├── __init__.py
│   ├── profiler.py           ← DatasetProfiler: profile(df) → DatasetProfile
│   ├── validator.py          ← DatasetValidator: validate(df, profile) → ValidationResult
│   ├── preprocessing.py      ← PreprocessingPipeline: fit_transform, transform
│   ├── adapters.py           ← extend Arzaan's stub with 3 concrete adapters
│   └── loader.py             ← extend Arzaan's stub if needed (profile trigger)
│
└── features/
    ├── __init__.py
    ├── pipeline.py           ← FeaturePipeline: fit_transform() → FeaturePipelineResult
    ├── reducer.py            ← DimensionalityReducer: PCA wrapper, fit/transform
    └── selector.py           ← FeatureSelector: low-variance filter, correlation filter
```

You do NOT create:
- `backend/api/` routes → Shweta / Piyush
- `backend/models/` → Piyush
- `backend/storage/` → Arzaan

---

## 4. Input Contract (what you consume)

You receive your input from **Arzaan's** ingestion output. His `DatasetLoader.get_dataset_info()` returns:

```python
{
    "id":       "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",   # dataset UUID
    "name":     "breast_cancer.csv",
    "path":     "datasets/DS-000001/raw/original.csv",       # path to raw immutable CSV
    "hash":     "a1b2c3d4...",
    "rows":     None,   # not yet known — Arzaan stores raw file only
    "columns":  None,
    "target":   None
}
```

You also read from `config.yaml` (via `backend.core.config`):

```yaml
experiment:
  random_state: 42
  test_size: 0.20

feature_reduction:
  method: pca
  variance_threshold: 0.95

quantum:
  max_qubits: 8
  candidate_dimensions: [4, 8]
```

---

## 5. Output Contracts

### 5a. `contracts/dataset_profile.json` — consumed by Shweta (API), Piyush (experiment planner)

```json
{
  "dataset_id":   "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "profile_id":   "PROFILE-000001",
  "modality":     "TABULAR",
  "dimensions": {
    "rows":    569,
    "columns": 32
  },
  "features": {
    "numerical":   30,
    "categorical":  1
  },
  "target": {
    "candidate":  "diagnosis",
    "confidence": "HIGH"
  },
  "task": {
    "candidate":  "BINARY_CLASSIFICATION",
    "confidence": "HIGH"
  },
  "class_distribution": { "0": 357, "1": 212 },
  "missing_values": {
    "total": 0,
    "percentage": 0.0,
    "by_column": {}
  },
  "duplicates": { "candidate_count": 0 },
  "warnings": ["Class imbalance detected: 62.7% vs 37.3%"],
  "status":       "PROFILED",
  "profiled_at":  "2026-09-10T14:25:12.456Z"
}
```

### 5b. `contracts/validation_report.json` — consumed by Piyush (planner gate)

```json
{
  "dataset_id":        "a1b2c3d4-...",
  "validation_status": "PASS_WITH_WARNINGS",
  "quality_score":     92,
  "next_phase":        "PREPROCESSING",
  "target_validation": { "status": "PASS", "target_column": "diagnosis" },
  "missing_values":    { "status": "PASS", "severity": "PASS" },
  "duplicates":        { "status": "PASS" },
  "class_balance":     { "status": "WARNING", "imbalance_ratio": 1.68, "severity": "MODERATE" },
  "leakage":           { "status": "PASS", "identifier_candidates": ["id"] },
  "outliers":          { "status": "INFO" },
  "critical_issues":   [],
  "warnings": [
    { "code": "CLASS_IMBALANCE", "message": "Moderate imbalance (1.68:1)", "severity": "MODERATE" }
  ]
}
```

**validation_status enum:** `PASS` | `PASS_WITH_WARNINGS` | `BLOCKED`
Only `BLOCKED` prevents the experiment from proceeding.

### 5c. `contracts/processed_data_schema.md` — consumed by Piyush (model inputs)

Your `FeaturePipelineResult` dataclass is the live Python object that replaces the JSON contract here. It must expose exactly these attributes:

```python
@dataclass
class FeaturePipelineResult:
    # Full-feature arrays (for classical models)
    X_train:          np.ndarray   # shape (n_train, n_features_scaled)  e.g. (455, 30) BC
    X_test:           np.ndarray   # shape (n_test,  n_features_scaled)  e.g. (114, 30) BC
    y_train:          np.ndarray   # shape (n_train,)                    e.g. (455,)
    y_test:           np.ndarray   # shape (n_test,)                     e.g. (114,)

    # Reduced arrays (for quantum models and fair classical comparison)
    X_train_reduced:  np.ndarray   # shape (n_train, n_components)       e.g. (455, 8)
    X_test_reduced:   np.ndarray   # shape (n_test,  n_components)       e.g. (114, 8)

    # Metadata
    n_components:       int          # e.g. 8
    feature_names:      List[str]    # original feature column names
    reduced_feature_names: List[str] # ["PC1", "PC2", ..., "PC8"]
    variance_retained:  float        # e.g. 0.94
    preprocessing_id:   str          # "PREP-000001"
    split_strategy:     str          # "stratified" or "grouped"
    test_size:          float        # 0.20
    random_state:       int          # 42
    class_weights:      dict         # {0: 1.0, 1: 1.68} for imbalance handling

    def to_dict(self) -> dict: ...   # for JSON serialization in executor.py
```

**Expected shapes for all 4 datasets (with 8 PCA components, 80/20 split):**
```
Breast Cancer:  X_train (455,30), X_test (114,30), X_train_reduced (455,8), X_test_reduced (114,8)
Heart Disease:  X_train (242,13), X_test (61,13),  X_train_reduced (242,8), X_test_reduced (61,8)
Parkinson's:    X_train (156,22), X_test (39,22),  X_train_reduced (156,8), X_test_reduced (39,8)
Diabetes:       X_train (614,8),  X_test (154,8),  X_train_reduced (614,8), X_test_reduced (154,8)
```
*(Exact numbers depend on stratification — these are approximate. Do not hardcode them.)*

---

## 6. Step-by-Step Build Order

### Day 1

**Hour 1–2: Read the actual CSVs first — before writing any code**

```python
import pandas as pd

for name, path in [
    ("breast_cancer", "data/demo/breast_cancer.csv"),
    ("heart_disease", "data/demo/heart_disease.csv"),
    ("parkinsons",    "data/demo/parkinsons.csv"),
]:
    df = pd.read_csv(path)
    print(f"\n=== {name} ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Dtypes:\n{df.dtypes}")
    print(f"Missing: {df.isnull().sum().sum()}")
    print(f"Head:\n{df.head(2)}")
```

Record: exact target column name, columns to drop, whether a subject/group column exists. Build your adapters from this ground truth — not from assumptions.

**Hour 2–4: Dataset Adapters (`backend/data/adapters.py`)**

Extend Arzaan's `AdapterRegistry` / `DatasetAdapter` base class:

```python
class BreastCancerAdapter(DatasetAdapter):
    name = "breast_cancer"
    
    def detect(self, df: pd.DataFrame) -> bool:
        # Look for 'diagnosis' column with M/B values AND numeric feature columns
        return ("diagnosis" in df.columns and 
                df["diagnosis"].isin(["M", "B", 0, 1]).all())
    
    def adapt(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, dict]:
        df = df.copy()
        # Drop identifier
        if "id" in df.columns:
            df = df.drop(columns=["id"])
        # Encode target: M=1 (malignant/positive), B=0
        y = (df["diagnosis"].map({"M": 1, "B": 0})
             .fillna(df["diagnosis"]).astype(int))
        X = df.drop(columns=["diagnosis"])
        return X, y, {"subject_ids": None, "adapter": self.name}


class HeartDiseaseAdapter(DatasetAdapter):
    name = "heart_disease"
    
    def detect(self, df: pd.DataFrame) -> bool:
        # UCI Heart Disease has columns like 'age', 'sex', 'cp', 'trestbps'
        # target column may be 'target' or 'num'
        return any(c in df.columns for c in ["target", "num"]) and "age" in df.columns
    
    def adapt(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, dict]:
        df = df.copy()
        target_col = "target" if "target" in df.columns else "num"
        # Binarize: 0=no disease, 1=disease (collapse values > 1 to 1)
        y = (df[target_col] > 0).astype(int)
        X = df.drop(columns=[target_col])
        # Handle missing values indicated by '?' in some versions
        X = X.replace("?", np.nan)
        X = X.apply(pd.to_numeric, errors="coerce")
        return X, y, {"subject_ids": None, "adapter": self.name}


class ParkinsonsAdapter(DatasetAdapter):
    name = "parkinsons"
    
    def detect(self, df: pd.DataFrame) -> bool:
        return "status" in df.columns and "MDVP:Fo(Hz)" in df.columns
    
    def adapt(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, dict]:
        df = df.copy()
        # 'name' column is subject identifier — extract for grouped splitting
        subject_ids = None
        if "name" in df.columns:
            subject_ids = df["name"].values
            df = df.drop(columns=["name"])
        y = df["status"].astype(int)
        X = df.drop(columns=["status"])
        return X, y, {"subject_ids": subject_ids, "adapter": self.name}
```

Register all adapters in `AdapterRegistry.__init__`.

**Hour 4–6: Profiler (`backend/data/profiler.py`)**

```python
@dataclass
class DatasetProfile:
    dataset_id: str
    profile_id: str
    modality: str          # "TABULAR" for MVP
    rows: int
    columns: int
    numerical_count: int
    categorical_count: int
    target_candidate: str
    target_confidence: str  # HIGH / MEDIUM / LOW / NONE
    task_candidate: str     # BINARY_CLASSIFICATION etc
    task_confidence: str
    class_distribution: dict
    missing_total: int
    missing_percentage: float
    missing_by_column: dict
    duplicate_count: int
    warnings: List[str]
    recommended_target: str  # for generic CSV
    status: str
    profiled_at: str
    
    def to_dict(self) -> dict: ...


class DatasetProfiler:
    def profile(self, df: pd.DataFrame, dataset_id: str, filename: str = "") -> DatasetProfile:
        ...
```

Logic inside `profile()`:
1. Count rows, columns, dtypes.
2. Detect numerical vs categorical columns (use `pd.api.types.is_numeric_dtype`).
3. Calculate missing values per column and total.
4. Detect exact duplicate rows.
5. Find target candidate: columns named `diagnosis`, `target`, `status`, `Outcome`, `label`, `class` in that priority, OR the last column if shape is narrow, OR column with fewest unique values < 20 that looks like a label.
6. Infer task: if candidate target has 2 unique non-null values → `BINARY_CLASSIFICATION`.
7. Calculate class distribution for binary targets.
8. Generate warnings: class imbalance > 1.5:1, missing > 5%, duplicates > 0.
9. Produce profile dict matching the contract above.

Test:
```python
df = pd.read_csv("data/demo/breast_cancer.csv")
profile = DatasetProfiler().profile(df, "test-id", "breast_cancer.csv")
assert profile.rows == 569
assert profile.target_candidate == "diagnosis"
assert profile.task_candidate == "BINARY_CLASSIFICATION"
assert profile.numerical_count == 30
```

**Hour 6–8: Validator (`backend/data/validator.py`)**

```python
@dataclass
class ValidationResult:
    dataset_id: str
    validation_status: str   # PASS / PASS_WITH_WARNINGS / BLOCKED
    quality_score: int       # 0-100
    next_phase: str
    target_validation: dict
    missing_values: dict
    duplicates: dict
    class_balance: dict
    leakage: dict
    outliers: dict
    critical_issues: List[dict]
    warnings: List[dict]
    info_messages: List[dict]
    recommended_preprocessing_steps: List[str]
    
    @property
    def is_valid(self) -> bool:
        return self.validation_status != "BLOCKED"
    
    def to_dict(self) -> dict: ...


class DatasetValidator:
    def validate(self, df: pd.DataFrame, profile: DatasetProfile,
                 target_column: str = None) -> ValidationResult:
        ...
```

Logic:
1. **Target validation:** Does the target column exist? Is it populated? Unique value count 2–20? Not an identifier? → PASS / FAIL (BLOCKED if FAIL).
2. **Missing values:** Use profile. 0% → PASS, 0–5% → LOW WARNING, 5–20% → MODERATE WARNING, >20% → HIGH WARNING.
3. **Duplicates:** > 0 → WARNING (not BLOCKED).
4. **Class balance:** Compute imbalance_ratio = majority_count / minority_count. < 1.5 → PASS, 1.5–3 → MODERATE WARNING, 3–10 → HIGH WARNING, > 10 → EXTREME (potential blocker).
5. **Leakage:** Flag columns named `id`, `patient_id`, `record_id`, `name`, `subject` as `identifier_candidates`. High-correlation-with-target check: any column with Pearson |r| > 0.95 with target is suspicious.
6. **Outliers (INFO only):** IQR method. Count samples with any feature outside 1.5*IQR. Never block for outliers.
7. **Quality score:** Start at 100, subtract: 5 per LOW warning, 10 per MODERATE, 20 per HIGH, 40 per CRITICAL.
8. **BLOCKED conditions (from phase3.md §28):** target missing entirely, all features are NaN, severe structural corruption.

Test:
```python
profile = profiler.profile(df, "test-id")
result = DatasetValidator().validate(df, profile)
assert result.is_valid  # Breast Cancer should pass
assert result.validation_status == "PASS_WITH_WARNINGS"  # has class imbalance
assert "id" in result.leakage["identifier_candidates"]
```

### Day 2

**Hour 1–3: Preprocessing Pipeline (`backend/data/preprocessing.py`)**

```python
@dataclass
class PreprocessingConfig:
    test_size: float = 0.20
    random_state: int = 42
    numerical_imputation: str = "median"
    categorical_imputation: str = "most_frequent"
    scaling: str = "standard"   # standard | minmax | robust
    handle_imbalance: str = "class_weight"  # class_weight | none
    remove_duplicates: bool = True


class PreprocessingPipeline:
    def __init__(self, config: PreprocessingConfig): ...
    
    def fit_transform(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        subject_ids: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
        """
        Returns: X_train, X_test, y_train, y_test, metadata
        metadata contains: preprocessing_id, scaler, imputer, feature_names, class_weights
        NEVER fit scaler/imputer on test data.
        """
        ...
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Apply already-fitted transformations to new data."""
        ...
```

**CRITICAL — leakage-safe split pattern:**
```python
# CORRECT ORDER — enforced in your code
if subject_ids is not None:
    # Grouped split for Parkinson's
    from sklearn.model_selection import GroupShuffleSplit
    gss = GroupShuffleSplit(test_size=config.test_size, random_state=config.random_state)
    train_idx, test_idx = next(gss.split(X, y, groups=subject_ids))
else:
    from sklearn.model_selection import train_test_split
    train_idx = ...  # stratified split indices

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

# ONLY NOW fit transformations — on X_train only
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # fit on train
X_test_scaled  = scaler.transform(X_test)         # transform test with train params
```

Compute class weights for imbalance:
```python
from sklearn.utils.class_weight import compute_class_weight
weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
class_weights = dict(zip(np.unique(y_train), weights))
```

**Hour 3–5: Feature Pipeline + PCA (`backend/features/`)**

`backend/features/reducer.py`:
```python
class DimensionalityReducer:
    def __init__(self, n_components: int, random_state: int = 42): ...
    
    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        """Fit PCA on training data only. Returns transformed X_train."""
        self.pca = PCA(n_components=self.n_components, random_state=self.random_state)
        return self.pca.fit_transform(X_train)
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply fitted PCA to any data (test, validation)."""
        return self.pca.transform(X)
    
    @property
    def variance_retained(self) -> float:
        return float(np.sum(self.pca.explained_variance_ratio_))
    
    @property
    def component_names(self) -> List[str]:
        return [f"PC{i+1}" for i in range(self.n_components)]
```

`backend/features/selector.py`:
```python
class FeatureSelector:
    """Low-variance filter + correlation filter — runs on training data only."""
    
    def fit_transform(self, X_train: np.ndarray, feature_names: List[str],
                      variance_threshold: float = 0.01) -> Tuple[np.ndarray, List[str]]:
        # Remove near-zero-variance features
        from sklearn.feature_selection import VarianceThreshold
        selector = VarianceThreshold(threshold=variance_threshold)
        X_filtered = selector.fit_transform(X_train)
        selected_names = [feature_names[i] for i in selector.get_support(indices=True)]
        self._selector = selector
        return X_filtered, selected_names
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        return self._selector.transform(X)
```

`backend/features/pipeline.py` — the main integration:
```python
@dataclass
class FeaturePipelineResult:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    X_train_reduced: np.ndarray
    X_test_reduced: np.ndarray
    n_components: int
    feature_names: List[str]
    reduced_feature_names: List[str]
    variance_retained: float
    preprocessing_id: str
    split_strategy: str
    test_size: float
    random_state: int
    class_weights: dict
    
    def to_dict(self) -> dict:
        return {
            "n_components": self.n_components,
            "variance_retained": self.variance_retained,
            "preprocessing_id": self.preprocessing_id,
            "split_strategy": self.split_strategy,
            "test_size": self.test_size,
            "n_train": len(self.y_train),
            "n_test": len(self.y_test),
            "feature_names": self.feature_names,
            "reduced_feature_names": self.reduced_feature_names,
            "class_weights": self.class_weights,
        }


class FeaturePipeline:
    def __init__(self, test_size: float = 0.20, random_state: int = 42,
                 n_components: int = 8, max_qubits: int = 8): ...
    
    def fit_transform(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        subject_ids: Optional[np.ndarray] = None
    ) -> FeaturePipelineResult:
        """
        Full pipeline: split → impute → scale → select → reduce.
        Returns FeaturePipelineResult with all arrays ready for models.
        """
        ...
```

**Hour 5–6: End-to-end test on all 4 datasets**

```python
# Test all datasets produce correct output shapes
test_cases = [
    ("data/demo/breast_cancer.csv", None),
    ("data/demo/heart_disease.csv", None),
    ("data/demo/parkinsons.csv",    None),   # adapter provides subject_ids
]

registry = AdapterRegistry()

for path, _ in test_cases:
    df = pd.read_csv(path)
    adapter = registry.detect_adapter(df)
    assert adapter is not None, f"No adapter detected for {path}"
    X, y, meta = adapter.adapt(df)
    
    pipeline = FeaturePipeline(n_components=8)
    result = pipeline.fit_transform(X, y, meta.get("subject_ids"))
    
    print(f"{path}:")
    print(f"  X_train shape:         {result.X_train.shape}")
    print(f"  X_train_reduced shape: {result.X_train_reduced.shape}")
    print(f"  y_train shape:         {result.y_train.shape}")
    print(f"  variance retained:     {result.variance_retained:.3f}")
    
    # Shape assertions
    assert result.X_train_reduced.shape[1] == 8
    assert result.X_test_reduced.shape[1] == 8
    assert len(result.y_train) + len(result.y_test) == len(y)
    assert result.variance_retained > 0.7  # sanity: at least 70% variance in 8 PCs
```

**Hour 6–8: Wire profiler/validator into executor.py**

In `backend/experiments/executor.py` (Piyush owns this file but you need to verify your outputs work inside it):
```python
# These lines already exist in executor.py — verify your classes satisfy them:
from backend.data.profiler import DatasetProfiler
from backend.data.validator import DatasetValidator
from backend.data.adapters import AdapterRegistry
from backend.features.pipeline import FeaturePipeline, FeaturePipelineResult

profiler = DatasetProfiler()
profile = profiler.profile(df, dataset_id, dataset_info['name'])

validator = DatasetValidator()
validation = validator.validate(df, profile, target_column)

if not validation.is_valid:
    raise ValueError(f"Dataset validation failed: {validation.issues}")

adapter = registry.detect_adapter(df)
X, y, metadata = adapter.adapt(df)
processed = feature_pipeline.fit_transform(X, y, subject_ids)
```

---

## 7. Mock Data to Build Against on Day 1

Use **Breast Cancer Wisconsin** for all Day 1 development. Here is the full ground truth to verify against (read directly from the CSV, do not hardcode):

**What the CSV actually contains:**
- 569 rows × 32 columns
- `id` column: integer patient identifier — **must be dropped**
- `diagnosis` column: `M` (malignant=1) or `B` (benign=0) — **encode to 0/1**
- Remaining 30 columns: all `float64`, names like `radius_mean`, `texture_mean`, ..., `fractal_dimension_worst`
- Zero missing values
- Class distribution: 357 B (benign=0), 212 M (malignant=1) → imbalance ratio 1.68:1

**Expected profiler output:**
```python
DatasetProfile(
    rows=569, columns=32,
    numerical_count=30, categorical_count=1,   # 'diagnosis' is categorical before encoding
    target_candidate="diagnosis", target_confidence="HIGH",
    task_candidate="BINARY_CLASSIFICATION",
    class_distribution={"0": 357, "1": 212},   # after M/B → 0/1 mapping
    missing_total=0, missing_percentage=0.0,
    warnings=["Class imbalance detected: 62.7% vs 37.3%"]
)
```

**Expected validation output:**
```python
ValidationResult(
    validation_status="PASS_WITH_WARNINGS",
    quality_score=92,
    leakage={"identifier_candidates": ["id"], "high_correlation_with_target": []},
    class_balance={"imbalance_ratio": 1.68, "severity": "MODERATE", "status": "WARNING"}
)
```

**Expected FeaturePipelineResult shapes (80/20 stratified, 8 PCA components):**
```
X_train.shape          → (455, 30)
X_test.shape           → (114, 30)
X_train_reduced.shape  → (455, 8)
X_test_reduced.shape   → (114, 8)
y_train.shape          → (455,)
y_test.shape           → (114,)
variance_retained      → ~0.94 (will vary, should be > 0.80)
```

---

## 8. Definition of Done

- [ ] `DatasetProfiler.profile()` runs on all 4 demo CSVs without error and returns a `DatasetProfile` with correct row/column counts, target candidate, task type, class distribution, and missing value stats — calculated from the actual data, zero hardcoded values.
- [ ] Profiler correctly identifies `diagnosis` (Breast Cancer), `target` (Heart Disease), `status` (Parkinson's) as target candidates.
- [ ] `DatasetValidator.validate()` returns `PASS_WITH_WARNINGS` (not `BLOCKED`) for all 4 demo datasets.
- [ ] Validator flags `id` column in Breast Cancer and `name` column in Parkinson's as identifier candidates.
- [ ] Validator flags class imbalance in Parkinson's (75.4% positive class) as HIGH WARNING.
- [ ] `BreastCancerAdapter.adapt()` drops `id`, encodes `M→1 / B→0`, returns X with 30 numeric columns.
- [ ] `HeartDiseaseAdapter.adapt()` handles `target` or `num` column, binarizes values > 1.
- [ ] `ParkinsonsAdapter.adapt()` extracts `name` column as `subject_ids` for grouped split.
- [ ] `AdapterRegistry.detect_adapter(df)` returns correct adapter for all 3 known datasets.
- [ ] `PreprocessingPipeline.fit_transform()` splits **before** fitting any transformer — verified by checking that `scaler.mean_` is calculated from train indices only.
- [ ] Parkinson's dataset uses `GroupShuffleSplit` when `subject_ids` are present; no patient appears in both train and test.
- [ ] `FeaturePipeline.fit_transform()` returns `FeaturePipelineResult` with `X_train_reduced.shape[1] == n_components` for all 4 datasets.
- [ ] PCA is fitted only on `X_train`; `X_test_reduced` uses `pca.transform()` (not `fit_transform()`).
- [ ] `FeaturePipelineResult.to_dict()` is JSON-serializable (no numpy arrays in output).
- [ ] `class_weights` dict in result is non-empty and reflects training set imbalance.
- [ ] `variance_retained` > 0.80 for 8 PCA components on all 4 datasets.
- [ ] Running `python -c "from backend.data.profiler import DatasetProfiler"` succeeds with no import errors.
- [ ] Running the end-to-end test script (§6, Day 2, Hour 5–6) passes all shape assertions.
- [ ] `DatasetProfile.to_dict()` output matches the `dataset_profile.json` contract structure.
- [ ] `ValidationResult.to_dict()` output matches the `validation_report.json` contract structure.

---

## 9. Common Failure Modes to Avoid

**From phase4.md §6 — Split before fitting transformers (the single most important rule):**
> "Correct: split → fit scaler on TRAIN only → transform TRAIN → apply same scaler to TEST. Wrong: normalize full dataset then split."
- **Fix:** Your `PreprocessingPipeline.fit_transform()` must call `train_test_split` or `GroupShuffleSplit` as the very first operation. All `scaler.fit_transform()` calls happen after, on train data only.

**From phase6.md §32 — PCA leakage:**
> "Feature selection must not use the test set. Calculate feature importance on TRAIN only."
- **Fix:** `pca.fit_transform(X_train)` then `pca.transform(X_test)`. Never `pca.fit_transform(X_all)`.

**From phase3.md §17, phase3.md §18 — Outliers are not errors:**
> "We should NOT automatically declare a value medically impossible unless we have a justified domain rule. cholesterol=350 could be a real measurement."
- **Fix:** Mark outliers as INFO-level only. Never drop outlier rows in preprocessing without explicit configuration. The validator flags, the preprocessor preserves by default.

**From implementaion_plan.md §11 — Never hardcode dataset facts:**
> "The profiler must calculate it from the uploaded CSV. Do NOT hardcode 569 rows, 30 features."
- **Fix:** Every number in `DatasetProfile` must come from `df.shape`, `df.dtypes`, `df.isnull()`, etc. Zero magic constants.

**From phase3.md §20 — Identifier columns must not become features:**
> "`patient_id`, `record_id`, `image_id` — should normally not become predictive features."
- **Fix:** Adapters explicitly drop identifier columns before returning X. Validator flags remaining identifier-looking columns.

**From implementaion_plan.md §17 — Parkinson's subject leakage:**
> "For Parkinson's, because multiple recordings can belong to the same subject, use a group-aware split if the downloaded dataset contains a subject identifier."
- **Fix:** `ParkinsonsAdapter` returns `subject_ids` (the `name` column values). `FeaturePipeline` uses `GroupShuffleSplit` when `subject_ids is not None`.

**From phase6.md §23 — Unfair quantum comparisons:**
> "Bad comparison: Classical uses 1280 features, quantum uses 8. We cannot conclude 'quantum is worse'."
- **Fix:** `FeaturePipelineResult` always exposes **both** `X_train` (full scaled) and `X_train_reduced` (PCA). Piyush runs classical models on full features AND on reduced features for the fair comparison group.

**From phase4.md §15 — Do not apply quantum-specific scaling in preprocessing:**
> "Do not hard-code quantum scaling into generic preprocessing yet. That decision belongs partly to Phase 6/8 when we know the quantum encoding."
- **Fix:** `PreprocessingPipeline` uses `StandardScaler` (general purpose). The quantum model in Piyush's code applies angle-encoding-specific range mapping internally.

**From phase3.md §2 — Validator detects, preprocessor fixes:**
> "Phase 3 detects problems but does not fix them. Phase 4 decides how to fix."
- **Fix:** `DatasetValidator` returns a report with warnings. It does **not** drop rows, impute values, or modify the DataFrame. All mutations happen in `PreprocessingPipeline`.

---

## 10. Ready-to-Paste First Prompt

```
I am building the data pipeline for a Hybrid Quantum-Classical Disease Detection Platform 
called QuantWarriors. My job is to implement Phases 2–6 from the architecture:

1. DatasetProfiler (Phase 2): inspect a pandas DataFrame and produce a structured profile
2. DatasetValidator (Phase 3): check dataset quality — detect problems, never fix them
3. Dataset Adapters (Phase 4): handle quirks of 3 known medical CSVs
4. PreprocessingPipeline (Phase 4): split → impute → scale (leakage-safe)
5. FeatureSelector (Phase 6): low-variance filter
6. DimensionalityReducer (Phase 6): PCA wrapper
7. FeaturePipeline (Phase 6): orchestrates everything, returns FeaturePipelineResult

Tech stack: Python 3.10, pandas 2.1, numpy 1.26, scikit-learn 1.3.

Project root: d:/projects/SIH2026/mvp/
Config: quantum.max_qubits=8, quantum.candidate_dimensions=[4,8], 
        experiment.test_size=0.20, experiment.random_state=42

The four reference datasets (all in data/demo/):
- breast_cancer.csv: 569×32, target='diagnosis' (M/B), drop 'id' column
- heart_disease.csv: 303×14, target='target' or 'num' (0/1 or 0-4 binarize)
- parkinsons.csv:    195×24, target='status', subject='name' (grouped split!)
- (diabetes not in demo folder but support in adapter registry)

CRITICAL RULES that must be enforced in code:
1. Train/test SPLIT happens BEFORE any scaler or PCA fitting
2. PCA is fitted on X_train only; X_test uses pca.transform() never fit_transform()
3. Parkinson's uses GroupShuffleSplit on 'name' column to avoid patient leakage
4. DatasetValidator only REPORTS problems — never modifies any data
5. No magic constants — all counts come from df.shape, df.dtypes, df.isnull()
6. Identifier columns ('id', 'name', 'patient_id') are dropped by adapters, not by generic code

The FeaturePipelineResult dataclass that downstream model code consumes:
  X_train          np.ndarray  (n_train, n_features)      e.g. (455, 30) for breast cancer
  X_test           np.ndarray  (n_test,  n_features)      e.g. (114, 30)
  y_train          np.ndarray  (n_train,)
  y_test           np.ndarray  (n_test,)
  X_train_reduced  np.ndarray  (n_train, n_components)    e.g. (455, 8)
  X_test_reduced   np.ndarray  (n_test,  n_components)    e.g. (114, 8)
  variance_retained float       e.g. 0.94
  class_weights    dict         e.g. {0: 0.80, 1: 1.34}

Start with:
1. backend/data/adapters.py — implement BreastCancerAdapter, HeartDiseaseAdapter, ParkinsonsAdapter
2. backend/data/profiler.py — DatasetProfiler.profile() returning DatasetProfile dataclass
3. backend/data/validator.py — DatasetValidator.validate() returning ValidationResult dataclass  
4. backend/data/preprocessing.py — PreprocessingPipeline.fit_transform()
5. backend/features/reducer.py — DimensionalityReducer (PCA wrapper)
6. backend/features/selector.py — FeatureSelector (variance threshold)
7. backend/features/pipeline.py — FeaturePipeline.fit_transform() → FeaturePipelineResult

After each file, show me how to test it against breast_cancer.csv.
For the final integration test, run all 4 datasets through FeaturePipeline and print shapes.
```
