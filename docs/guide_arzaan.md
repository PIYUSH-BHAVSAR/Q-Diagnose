# Developer Guide — Arzaan
## Scope: Ingestion, Storage (SQLite), Core Config / Logging / Exceptions

---

## 1. Scope Summary

You own the **foundation layer** that every other teammate builds on top of. This means three things: (1) the CSV upload and ingestion pipeline that receives a file, validates its format and safety, hashes it, assigns it a unique ID, and saves the original immutable copy to disk; (2) the SQLite database layer and file-storage abstraction that stores dataset metadata and experiment records; and (3) the core infrastructure modules — config, logging, and exceptions — that every other backend file imports from. If your layer is broken, nothing else works. The good news is that your scope has no ML dependencies at all — you're working in pure Python with FastAPI, SQLAlchemy, and the standard library. Your output is the `dataset_upload_response.json` contract that Shweta's API layer and Jayed's profiler will consume. You must also wire up `backend/main.py` (already scaffolded) and make sure it starts cleanly.

---

## 2. Exact Phase Numbers

From the **architecture document (phase1.md – phase15.md)**:
- **Phase 1** (phase1.md): Dataset Ingestion & Registration — all 48 sections are yours: File Receiver (§9), Format Validator (§10–11), ZIP Security Validation (§13–15), File Hashing (§16–18), Dataset ID Generation (§19–20), Raw Dataset Storage (§21–22), Dataset Registry (§24–25), Status Lifecycle (§26), Error States (§27), API Design (§28–30), Logging (§39), Security Considerations (§40).

From the **MVP implementation plan (implementaion_plan.md)**:
- **MVP Phase 0** (§8–9): Environment setup, verify imports.
- **MVP Phase 1** (§9–10): Dataset ingestion endpoint, file reception, hash, ID generation, profile trigger.
- **MVP Phase 26** (§63): Logging — timestamp, experiment_id, stage, model, duration, status, error.
- **MVP Phase 27** (§64): Reproducibility — every experiment stores seed, dataset_hash, config.
- **Storage Strategy** (§77): `data/uploads/`, `artifacts/models/`, `artifacts/experiments/EXP-XXXXX/`, `artifacts/reports/`.
- **Database Entities** (§76): Dataset table, Experiment table, ModelResult table, Report table.
- **API Design** (§78): `POST /api/datasets/upload`, `GET /api/datasets`, `GET /api/datasets/{id}`, `GET /api/datasets/{id}/profile`.

---

## 3. Files / Folders You Must Create

Work inside `d:\projects\SIH2026\mvp\`. Everything listed below is your responsibility to create and own:

```
backend/
├── main.py                          ← already scaffolded, wire up routers + startup
├── core/
│   ├── __init__.py
│   ├── config.py                    ← read config.yaml, expose typed settings
│   ├── logging.py                   ← structured logger setup
│   └── exceptions.py                ← all custom exceptions used platform-wide
├── storage/
│   ├── __init__.py
│   ├── database.py                  ← SQLAlchemy engine, session factory, Base
│   ├── models.py                    ← ORM models: Dataset, Experiment, ModelResult, Report
│   ├── repositories.py              ← DatasetRepository, ExperimentRepository (CRUD)
│   └── files.py                     ← local filesystem storage abstraction
├── data/
│   ├── __init__.py
│   ├── loader.py                    ← DatasetLoader: load_csv(), get_dataset_info()
│   └── adapters.py                  ← AdapterRegistry stub (Jayed fills in adapters)

data/
├── uploads/                         ← landing folder for raw uploaded CSVs
└── demo/
    ├── breast_cancer.csv
    ├── heart_disease.csv
    └── parkinsons.csv

artifacts/
├── experiments/
├── models/
└── reports/
```

Files you do NOT create (those belong to teammates):
- `backend/data/profiler.py`, `validator.py`, `preprocessing.py` → Jayed
- `backend/api/datasets.py` (the route handlers) → Shweta
- `backend/api/experiments.py`, `results.py`, `reports.py` → Piyush

---

## 4. Input Contract (what you receive)

Your input is a raw HTTP multipart file upload — there is no upstream contract JSON for Phase 1. You are the system entry point.

**HTTP request shape:**
```
POST /api/datasets/upload
Content-Type: multipart/form-data

file: <binary CSV/ZIP/XLSX>
```

Internal to your ingestion service, you receive:
- `UploadFile` from FastAPI (filename, content_type, file object)
- `config.yaml` values (max_file_size_mb, supported_formats, storage.base_path)

---

## 5. Output Contract

Your output is consumed by **Shweta** (HTTP response to frontend), **Jayed** (profiler reads the storage path), and **Piyush** (experiment manager reads dataset_id from DB).

### `contracts/dataset_upload_response.json` — verbatim

```json
{
  "dataset_id":        "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "display_id":        "DS-000001",
  "status":            "REGISTERED",
  "filename":          "breast_cancer.csv",
  "container_type":    "CSV",
  "upload_timestamp":  "2026-09-10T14:23:45.123Z",
  "file_size_bytes":   125847,
  "sha256":            "a1b2c3d4e5f67890abcdef1234...",
  "storage_path":      "datasets/DS-000001/raw/original.csv",
  "is_duplicate":      false,
  "duplicate_of":      null,
  "validation_warnings": [],
  "rejection_reason":  null
}
```

**Status enum values:** `REGISTERED`, `REJECTED`, `INVALID_FORMAT`, `UNSAFE_ARCHIVE`, `SIZE_LIMIT_EXCEEDED`, `STORAGE_ERROR`

**Database record shape** (SQLAlchemy model `Dataset`):
```python
id              UUID (primary key)
display_id      str  "DS-000001"
original_filename str
container_type  str  "CSV"
file_size_bytes int
sha256          str (64-char hex)
raw_storage_path str
upload_timestamp datetime
status          str
created_by      str (default "system")
```

---

## 6. Step-by-Step Build Order

### Day 1

**Morning — Foundation (no FastAPI yet, just Python modules)**

1. **core/config.py** — Load `config.yaml` using `pyyaml`. Expose a `Config` dataclass or Pydantic `BaseSettings` with fields: `storage_base_path`, `max_file_size_mb`, `supported_formats`, `quantum_config`, `experiment`, `classical_models`. Test: `from backend.core.config import config; print(config.storage_base_path)`.

2. **core/logging.py** — Set up Python `logging` with a structured format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`. Create a `get_logger(name)` helper. Test: import and log an INFO message.

3. **core/exceptions.py** — Define all custom exceptions used platform-wide:
   ```python
   class QMLPlatformError(Exception): pass
   class DatasetValidationError(QMLPlatformError): pass
   class UnsupportedFormatError(QMLPlatformError): pass
   class StorageError(QMLPlatformError): pass
   class ExperimentNotFoundError(QMLPlatformError): pass
   class DataLeakageError(QMLPlatformError): pass
   ```

4. **storage/database.py** — SQLAlchemy setup:
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker, declarative_base
   
   DATABASE_URL = "sqlite:///./mvp.db"
   engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
   SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
   Base = declarative_base()
   
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   
   def init_db():
       Base.metadata.create_all(bind=engine)
   ```

5. **storage/models.py** — ORM models for Dataset, Experiment, ModelResult, Report. Use `UUID` as primary key stored as `String(36)`. Test: run `init_db()` and verify `mvp.db` is created with all tables.

6. **storage/files.py** — File storage abstraction:
   ```python
   class LocalFileStorage:
       def __init__(self, base_path: str): ...
       def save_dataset(self, dataset_id: str, file_bytes: bytes, filename: str) -> str: ...
       def get_dataset_path(self, dataset_id: str) -> str: ...
       def save_artifact(self, experiment_id: str, name: str, data: bytes) -> str: ...
       def read_dataset(self, dataset_id: str) -> bytes: ...
   ```
   Storage layout: `{base_path}/datasets/{dataset_id}/raw/original{ext}`.

**Afternoon — Ingestion Service**

7. **data/loader.py** — `DatasetLoader` class:
   ```python
   class DatasetLoader:
       def load_csv(self, file_path: str) -> Tuple[str, pd.DataFrame]:
           """Returns (dataset_id, dataframe)."""
       def get_dataset_info(self, dataset_id: str) -> dict:
           """Returns {id, name, path, hash, rows, columns, target}."""
   ```

8. **Ingestion service** (can live in `data/loader.py` or a new `data/ingestion.py`):
   - `validate_format(filename, content_type)` → checks extension against `supported_formats`, detects MIME signature for CSV (starts with printable text, not binary magic bytes).
   - `calculate_sha256(file_bytes)` → returns 64-char hex string.
   - `check_duplicate(sha256, db_session)` → query Dataset table by sha256.
   - `generate_display_id(db_session)` → `DS-{count+1:06d}` format.
   - `ingest(upload_file, db_session)` → orchestrates the full pipeline, returns `dataset_upload_response.json` shape as a dict.

9. **Test ingestion against Breast Cancer dataset**:
   ```python
   # test manually
   result = ingestion_service.ingest_from_path("data/demo/breast_cancer.csv", db)
   assert result["status"] == "REGISTERED"
   assert result["filename"] == "breast_cancer.csv"
   assert len(result["sha256"]) == 64
   assert result["container_type"] == "CSV"
   ```

10. **storage/repositories.py** — `DatasetRepository`:
    ```python
    class DatasetRepository:
        def create(self, db, dataset_data: dict) -> Dataset: ...
        def get_by_id(self, db, dataset_id: str) -> Optional[Dataset]: ...
        def get_by_sha256(self, db, sha256: str) -> Optional[Dataset]: ...
        def list_all(self, db) -> List[Dataset]: ...
        def update_status(self, db, dataset_id: str, status: str): ...
    ```

### Day 2

**Morning — Wire FastAPI + Validate all 4 datasets**

11. **backend/main.py** — already scaffolded. Verify it imports cleanly. Add `init_db()` call in `startup_event`. Make sure `GET /api/health` returns `{"status": "healthy"}` and server starts on port 8000.

12. **data/adapters.py** — Stub for `AdapterRegistry` so Jayed can fill in adapters:
    ```python
    class DatasetAdapter:
        name: str
        def detect(self, df: pd.DataFrame) -> bool: ...
        def adapt(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, dict]: ...
    
    class AdapterRegistry:
        def __init__(self):
            self._adapters: List[DatasetAdapter] = []
        def register(self, adapter: DatasetAdapter): ...
        def detect_adapter(self, df: pd.DataFrame) -> Optional[DatasetAdapter]: ...
    ```

13. **Test all 4 datasets through ingestion**:
    - `breast_cancer.csv` → 569 rows, 32 cols, sha256 computed, stored at correct path.
    - `heart_disease.csv` → 303 rows, 14 cols.
    - `parkinsons.csv` → 195 rows, 24 cols.
    - Duplicate upload → `is_duplicate: true`, `duplicate_of: <existing_id>`.

14. **Error case testing**:
    - Upload a `.txt` file → status `INVALID_FORMAT`.
    - Upload a file exceeding `max_file_size_mb` → status `SIZE_LIMIT_EXCEEDED`.
    - Corrupt binary file renamed to `.csv` → `INVALID_FILE` or `STORAGE_ERROR`.

15. **ZIP validation stub** (for future image support): add `validate_zip(zip_bytes)` in ingestion that checks: zip is valid, no path traversal (`../`), entry count < 100,000, estimated uncompressed size < `max_uncompressed_size_gb` × 1GB. Return early with `UNSAFE_ARCHIVE` if checks fail. (No need to fully implement image pipeline — just gate it.)

16. **Coordinate with Shweta**: hand her the ingestion service's `ingest()` method signature and the exact `dataset_upload_response.json` shape so she can wire the FastAPI route handler in `backend/api/datasets.py`.

---

## 7. Mock Data to Build Against on Day 1

Use **Breast Cancer Wisconsin** (`data/demo/breast_cancer.csv`) for all Day 1 testing. Do not hardcode anything about it — treat it like an unknown upload.

Expected facts you'll discover by actually reading it (don't hardcode these):
- 569 rows, 32 columns
- Column `id` is a patient identifier (should be flagged, not a feature)
- Column `diagnosis` has values `M` and `B`
- All other columns are numeric float64
- Zero missing values

**Hardcode-free test pattern:**
```python
import pandas as pd
df = pd.read_csv("data/demo/breast_cancer.csv")
print(f"Shape: {df.shape}")         # (569, 32)
print(f"Dtypes:\n{df.dtypes}")
print(f"Missing: {df.isnull().sum().sum()}")
print(f"Columns: {df.columns.tolist()}")
```

**Concrete mock upload response to build against (Day 1):**
```json
{
  "dataset_id": "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "display_id": "DS-000001",
  "status": "REGISTERED",
  "filename": "breast_cancer.csv",
  "container_type": "CSV",
  "upload_timestamp": "2026-09-10T14:23:45.123Z",
  "file_size_bytes": 125847,
  "sha256": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
  "storage_path": "datasets/DS-000001/raw/original.csv",
  "is_duplicate": false,
  "duplicate_of": null,
  "validation_warnings": [],
  "rejection_reason": null
}
```

---

## 8. Definition of Done

- [ ] `backend/core/config.py` loads `config.yaml` and exposes typed config object; all other modules import from it without error.
- [ ] `backend/core/logging.py` provides a `get_logger()` function; log messages include timestamp, level, module name, and message.
- [ ] `backend/core/exceptions.py` defines at minimum: `QMLPlatformError`, `DatasetValidationError`, `UnsupportedFormatError`, `StorageError`, `ExperimentNotFoundError`.
- [ ] `backend/storage/database.py` creates `mvp.db` on first run with all 4 tables (Dataset, Experiment, ModelResult, Report).
- [ ] `backend/storage/models.py` ORM models match the field list in §5 above.
- [ ] `backend/storage/repositories.py` CRUD for Dataset works: create, get_by_id, get_by_sha256, list_all.
- [ ] `backend/storage/files.py` saves and retrieves dataset files; storage path follows `datasets/{id}/raw/original{ext}` pattern.
- [ ] `backend/data/loader.py` reads a CSV into a pandas DataFrame and returns a `(dataset_id, df)` tuple without hardcoding column names.
- [ ] Ingestion pipeline for `breast_cancer.csv`: status `REGISTERED`, sha256 is 64-char hex, file exists at storage path, record in DB.
- [ ] Ingestion pipeline for all 4 demo datasets produces `REGISTERED` status.
- [ ] Duplicate detection: uploading same file twice produces `is_duplicate: true` on second upload.
- [ ] Format rejection: `.exe` or `.pdf` upload returns `status: INVALID_FORMAT` (not a 500 error).
- [ ] `python -m uvicorn backend.main:app --reload` starts without import errors.
- [ ] `GET /api/health` returns `{"status": "healthy"}`.
- [ ] `GET /api/config` returns quantum, experiment, and classical_models config sections.
- [ ] `backend/data/adapters.py` exports `AdapterRegistry` and `DatasetAdapter` base class for Jayed to extend.
- [ ] Original dataset file is never modified after ingestion (confirm file hash matches sha256 stored in DB after re-read).
- [ ] All folder structure under `data/uploads/` and `artifacts/` created on startup or first use.

---

## 9. Common Failure Modes to Avoid

**From phase1.md, §11 — Do not trust file extensions alone:**
> A user could rename `malware.exe` to `dataset.csv`. Do not rely only on `filename.endswith(".csv")`. Use file-signature/content validation.
- **Fix:** Check the first few bytes of the file for UTF-8 / printable content, not just extension. Reject binary magic bytes.

**From phase1.md, §22 — Never overwrite the original:**
> Never do: `original.csv → cleaned.csv → overwrite original.csv`.
- **Fix:** Write to `datasets/{id}/raw/original.csv` once. All derived versions go under `processed/`. Never open the raw file with `"w"` mode.

**From phase1.md, §23 — Don't hardcode `local` storage everywhere:**
> The code should depend on `StorageBackend`, not `LocalStorage` directly.
- **Fix:** Use `LocalFileStorage` behind a storage interface so future S3/MinIO migration is possible without touching ingestion logic.

**From phase1.md, §38 — Environment awareness:**
> Business logic must NOT depend on "local" mode directly.
- **Fix:** Config drives the storage backend type. If `config.storage.backend == "local"`, use `LocalFileStorage`. Don't scatter `os.path.join("./data", ...)` directly in business logic.

**From implementaion_plan.md, §11 — Do NOT hardcode dataset facts:**
> The profiler must calculate it from the uploaded CSV. Do NOT hardcode `569 rows, 30 features`.
- **Fix:** Your loader must calculate row/column counts dynamically from the file. Never embed dataset-specific numbers in code.

**From phase1.md, §18 — Duplicate ≠ Invalid:**
> `duplicate ≠ invalid`. A user may intentionally upload the same dataset for a new project.
- **Fix:** Set `is_duplicate: true` but still return `status: REGISTERED` and store the new record. Do not reject duplicates silently.

**From phase1.md, §39 — Never log sensitive biomedical data:**
> Never log sensitive biomedical data itself.
- **Fix:** Log metadata only (dataset_id, filename, size, sha256 prefix). Never log actual row content.

**From phase1.md, §14 — ZIP inspection ≠ deep processing:**
> Phase 1 should not perform deep dataset discovery on ZIP contents. It can inspect metadata, not extract/analyze ML content.
- **Fix:** Only check archive validity, entry count, uncompressed size, and path safety. Do NOT load images or parse CSV inside the ZIP in Phase 1.

**SQLAlchemy thread safety:**
> SQLite + FastAPI async background tasks can cause `check_same_thread` issues.
- **Fix:** Pass `connect_args={"check_same_thread": False}` to `create_engine`. Use dependency injection for `get_db()`.

---

## 10. Ready-to-Paste First Prompt

Paste this verbatim into your AI IDE to start:

```
I am building the foundation layer of a Hybrid Quantum-Classical Disease Detection Platform 
called QuantWarriors. My job is to implement:

1. Core infrastructure (config, logging, exceptions)
2. SQLite storage layer (SQLAlchemy ORM models + repositories)
3. File storage abstraction (local filesystem)
4. Dataset ingestion pipeline (CSV upload → validate → hash → save → register)

Tech stack: Python 3.10, FastAPI 0.104+, SQLAlchemy 2.0, pydantic-settings 2.1, pyyaml 6.0, 
pandas 2.1, uvicorn.

Project root: d:/projects/SIH2026/mvp/
Config file: d:/projects/SIH2026/mvp/config.yaml (already exists)
Main FastAPI app: d:/projects/SIH2026/mvp/backend/main.py (already scaffolded)

The output contract I must produce is this JSON shape (returned by the upload endpoint):
{
  "dataset_id": "<UUID>",
  "display_id": "DS-000001",
  "status": "REGISTERED",
  "filename": "breast_cancer.csv",
  "container_type": "CSV",
  "upload_timestamp": "2026-09-10T14:23:45.123Z",
  "file_size_bytes": 125847,
  "sha256": "<64-char hex>",
  "storage_path": "datasets/DS-000001/raw/original.csv",
  "is_duplicate": false,
  "duplicate_of": null,
  "validation_warnings": [],
  "rejection_reason": null
}

Status enum: REGISTERED | REJECTED | INVALID_FORMAT | UNSAFE_ARCHIVE | SIZE_LIMIT_EXCEEDED | STORAGE_ERROR

Critical rules:
- NEVER modify the original uploaded file after saving it
- NEVER trust file extensions alone — check file content/magic bytes
- NEVER hardcode dataset-specific values (row counts, column names, etc.)
- NEVER log raw biomedical data content
- Duplicate files (same SHA-256) return is_duplicate=true but still register successfully
- Storage must go through a LocalFileStorage abstraction class (not raw os.path calls)

SQLite tables needed: Dataset, Experiment, ModelResult, Report
Storage layout: {base_path}/datasets/{dataset_id}/raw/original{ext}

Start by creating these files in order:
1. backend/core/config.py
2. backend/core/logging.py
3. backend/core/exceptions.py
4. backend/storage/database.py
5. backend/storage/models.py
6. backend/storage/repositories.py
7. backend/storage/files.py
8. backend/data/loader.py
9. backend/data/adapters.py (stub only — base class and registry)

After each file, show me how to test it. Do not create any ML, quantum, or API route 
files — those belong to other teammates.
```
