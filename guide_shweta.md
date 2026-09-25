# Developer Guide — Shweta
## Scope: Dataset API Endpoints (supporting Arzaan)

---

## 1. Scope Summary

You own the **dataset-facing HTTP layer** — the FastAPI route handlers that sit between the React frontend and the backend services built by Arzaan and Jayed. Your four endpoints let the frontend upload a CSV, list all registered datasets, fetch a single dataset's metadata, and retrieve a dataset's profile. You are not building any ML logic, storage, or profiling code — you are wiring existing services into clean, well-structured HTTP routes. Your work is the first thing Naeem (frontend) will call, so your API contract must be stable on Day 1. You also own one supporting piece: triggering the profiler automatically after a successful upload, so by the time the frontend receives the upload response, profiling has either completed or started in the background. Think of yourself as the "glue" layer — your job is to get the plumbing exactly right: correct HTTP status codes, correct response shapes, good error messages, and no silent failures.

---

## 2. Exact Phase Numbers

From the **architecture document**:
- **Phase 1, §28–30** (phase1.md): API design — `POST /api/v1/datasets`, `GET /api/v1/datasets/{dataset_id}`, `GET /api/v1/datasets` — exact request/response shapes.
- **Phase 1, §31–33** (phase1.md): Frontend flow after upload — uploading state, validation state, registration result.
- **Phase 2** (phase2.md §4): Phase 2 is triggered by Phase 1 output; your endpoint should kick off profiling after registration.

From the **MVP implementation plan**:
- **MVP Phase 1** (§9): `POST /datasets/upload` — receive file, check extension, check size, save, generate ID, load with pandas, start profiling.
- **MVP Phase 24** (§52): Frontend pages — `/datasets`, `/datasets/:id`. Your API backs both.
- **MVP Phase 54–55** (§54–55): Dataset upload experience and dataset profile screen — the data your endpoints serve.
- **API Design** (§78):
  ```
  POST /api/datasets/upload
  GET  /api/datasets
  GET  /api/datasets/{id}
  GET  /api/datasets/{id}/profile
  ```

---

## 3. Files / Folders You Must Create

All paths relative to `d:\projects\SIH2026\mvp\`:

```
backend/
└── api/
    ├── __init__.py
    └── datasets.py     ← ALL your work lives here
```

You do NOT create or modify:
- `backend/data/ingestion.py` or `loader.py` → Arzaan owns ingestion logic
- `backend/data/profiler.py` → Jayed owns profiling logic
- `backend/storage/` → Arzaan
- `backend/api/experiments.py`, `results.py`, `reports.py` → Piyush

The `backend/main.py` already has `app.include_router(datasets.router)` — your router just needs to exist with the right prefix.

---

## 4. Input Contract (what you receive)

**Upload endpoint — HTTP request:**
```
POST /api/datasets/upload
Content-Type: multipart/form-data

file:        <binary content>      # UploadFile from FastAPI
```

**List endpoint:**
```
GET /api/datasets
```
Optional query params (nice-to-have for Day 2): `?limit=20&offset=0`

**Detail endpoint:**
```
GET /api/datasets/{dataset_id}
```

**Profile endpoint:**
```
GET /api/datasets/{dataset_id}/profile
```

You get the `dataset_id` from the URL path. It is a UUID string.

**What services you call (Arzaan's layer):**
```python
from backend.data.loader import DatasetLoader          # get_dataset_info()
from backend.storage.repositories import DatasetRepository  # list_all(), get_by_id()
from backend.storage.database import get_db           # FastAPI dependency

# You also call Jayed's profiler (after upload):
from backend.data.profiler import DatasetProfiler     # profile()
```

---

## 5. Output Contracts

### Upload response — `contracts/dataset_upload_response.json`

```json
{
  "dataset_id":          "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "display_id":          "DS-000001",
  "status":              "REGISTERED",
  "filename":            "breast_cancer.csv",
  "container_type":      "CSV",
  "upload_timestamp":    "2026-09-10T14:23:45.123Z",
  "file_size_bytes":     125847,
  "sha256":              "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
  "storage_path":        "datasets/DS-000001/raw/original.csv",
  "is_duplicate":        false,
  "duplicate_of":        null,
  "validation_warnings": [],
  "rejection_reason":    null
}
```

HTTP status: `201 Created` on success, `400 Bad Request` on format/size error, `422` on validation error, `500` on storage failure.

### List response

```json
{
  "datasets": [
    {
      "dataset_id":       "a1b2c3d4-...",
      "display_id":       "DS-000001",
      "filename":         "breast_cancer.csv",
      "container_type":   "CSV",
      "file_size_bytes":  125847,
      "status":           "REGISTERED",
      "upload_timestamp": "2026-09-10T14:23:45.123Z",
      "has_profile":      true
    }
  ],
  "total": 1
}
```

### Detail response

```json
{
  "dataset_id":        "a1b2c3d4-...",
  "display_id":        "DS-000001",
  "filename":          "breast_cancer.csv",
  "container_type":    "CSV",
  "file_size_bytes":   125847,
  "sha256":            "a1b2c3d4...",
  "status":            "REGISTERED",
  "upload_timestamp":  "2026-09-10T14:23:45.123Z",
  "storage_path":      "datasets/DS-000001/raw/original.csv",
  "is_duplicate":      false,
  "duplicate_of":      null
}
```

HTTP status: `200 OK`, or `404 Not Found` with `{"detail": "Dataset DS-XXXXX not found"}`.

### Profile response — `contracts/dataset_profile.json`

```json
{
  "dataset_id":   "a1b2c3d4-...",
  "profile_id":   "PROFILE-000001",
  "modality":     "TABULAR",
  "dimensions": { "rows": 569, "columns": 32 },
  "features":   { "numerical": 30, "categorical": 1 },
  "target": {
    "candidate":  "diagnosis",
    "confidence": "HIGH"
  },
  "task": {
    "candidate":  "BINARY_CLASSIFICATION",
    "confidence": "HIGH"
  },
  "class_distribution": { "0": 357, "1": 212 },
  "missing_values": { "total": 0, "percentage": 0.0, "by_column": {} },
  "duplicates":   { "candidate_count": 0 },
  "warnings":     ["Class imbalance detected: 62.7% vs 37.3%"],
  "status":       "PROFILED",
  "profiled_at":  "2026-09-10T14:25:12.456Z"
}
```

HTTP status: `200 OK`, `404` if dataset not found, `202 Accepted` with `{"status": "profiling_in_progress"}` if profiling hasn't completed yet.

---

## 6. Step-by-Step Build Order

### Day 1

**Hour 1: Pydantic response models**

Define all response schemas using Pydantic before writing any route logic. This gives you type safety and auto-docs in `/docs`.

```python
# backend/api/datasets.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DatasetUploadResponse(BaseModel):
    dataset_id: str
    display_id: str
    status: str
    filename: str
    container_type: str
    upload_timestamp: str
    file_size_bytes: int
    sha256: str
    storage_path: str
    is_duplicate: bool
    duplicate_of: Optional[str]
    validation_warnings: List[str]
    rejection_reason: Optional[str]

class DatasetSummary(BaseModel):
    dataset_id: str
    display_id: str
    filename: str
    container_type: str
    file_size_bytes: int
    status: str
    upload_timestamp: str
    has_profile: bool

class DatasetListResponse(BaseModel):
    datasets: List[DatasetSummary]
    total: int

class DatasetDetailResponse(BaseModel):
    dataset_id: str
    display_id: str
    filename: str
    container_type: str
    file_size_bytes: int
    sha256: str
    status: str
    upload_timestamp: str
    storage_path: str
    is_duplicate: bool
    duplicate_of: Optional[str]

class DatasetProfileResponse(BaseModel):
    dataset_id: str
    profile_id: str
    modality: str
    dimensions: dict
    features: dict
    target: dict
    task: dict
    class_distribution: dict
    missing_values: dict
    duplicates: dict
    warnings: List[str]
    status: str
    profiled_at: str
```

**Hour 2–3: Upload endpoint**

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.post("/upload", response_model=DatasetUploadResponse, status_code=201)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a biomedical CSV dataset.
    
    - Validates format (CSV/XLSX/ZIP only)
    - Checks file size against config limit
    - Computes SHA-256 hash
    - Saves immutable original to storage
    - Registers metadata in database
    - Triggers profiling in background
    """
    try:
        file_bytes = await file.read()
        
        # Call Arzaan's ingestion service
        ingestion = DatasetIngestionService(db=db)
        result = ingestion.ingest(
            filename=file.filename,
            content_type=file.content_type,
            file_bytes=file_bytes
        )
        
        # Trigger profiling in background if registration succeeded
        if result["status"] == "REGISTERED":
            background_tasks.add_task(
                _run_profiling_background,
                dataset_id=result["dataset_id"],
                storage_path=result["storage_path"]
            )
        
        return DatasetUploadResponse(**result)
    
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileSizeLimitError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_profiling_background(dataset_id: str, storage_path: str):
    """Background task: run profiler and store profile in DB."""
    try:
        import pandas as pd
        from backend.data.profiler import DatasetProfiler
        
        df = pd.read_csv(storage_path)
        profiler = DatasetProfiler()
        profile = profiler.profile(df, dataset_id)
        
        # Store profile result — you need a ProfileRepository or store as JSON
        # For MVP: store as JSON file alongside the dataset
        import json, os
        profile_path = storage_path.replace("/raw/original.csv", "/profile.json")
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        with open(profile_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Background profiling failed for {dataset_id}: {e}")
        # Don't raise — background task failure should not crash the request
```

**Hour 3–4: List and Detail endpoints**

```python
@router.get("", response_model=DatasetListResponse)
def list_datasets(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all registered datasets."""
    repo = DatasetRepository()
    datasets = repo.list_all(db)[offset:offset+limit]
    total = len(repo.list_all(db))
    
    summaries = []
    for ds in datasets:
        # Check if profile exists
        profile_path = f"datasets/{ds.id}/profile.json"
        has_profile = os.path.exists(
            os.path.join(config.storage_base_path, profile_path)
        )
        summaries.append(DatasetSummary(
            dataset_id=str(ds.id),
            display_id=ds.display_id,
            filename=ds.original_filename,
            container_type=ds.container_type,
            file_size_bytes=ds.file_size_bytes,
            status=ds.status,
            upload_timestamp=ds.upload_timestamp.isoformat(),
            has_profile=has_profile
        ))
    
    return DatasetListResponse(datasets=summaries, total=total)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get a single dataset's registration details."""
    repo = DatasetRepository()
    ds = repo.get_by_id(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    return DatasetDetailResponse(
        dataset_id=str(ds.id),
        display_id=ds.display_id,
        filename=ds.original_filename,
        container_type=ds.container_type,
        file_size_bytes=ds.file_size_bytes,
        sha256=ds.sha256,
        status=ds.status,
        upload_timestamp=ds.upload_timestamp.isoformat(),
        storage_path=ds.raw_storage_path,
        is_duplicate=ds.is_duplicate if hasattr(ds, 'is_duplicate') else False,
        duplicate_of=ds.duplicate_of if hasattr(ds, 'duplicate_of') else None
    )
```

**Hour 4–5: Profile endpoint**

```python
@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
def get_dataset_profile(dataset_id: str, db: Session = Depends(get_db)):
    """
    Get the profiling results for a dataset.
    Returns 202 if profiling is still in progress.
    Returns 404 if dataset doesn't exist.
    """
    repo = DatasetRepository()
    ds = repo.get_by_id(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    # Check if profile file exists
    profile_path = os.path.join(
        config.storage_base_path,
        f"datasets/{dataset_id}/profile.json"
    )
    
    if not os.path.exists(profile_path):
        # Profiling hasn't completed yet — return 202
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={"status": "profiling_in_progress", "dataset_id": dataset_id}
        )
    
    with open(profile_path) as f:
        import json
        profile_data = json.load(f)
    
    return DatasetProfileResponse(**profile_data)
```

**Hour 5–6: Manual testing**

Start the server: `uvicorn backend.main:app --reload`

```bash
# Upload Breast Cancer
curl -X POST http://localhost:8000/api/datasets/upload \
     -F "file=@data/demo/breast_cancer.csv"
# Expected: 201, status=REGISTERED

# List datasets
curl http://localhost:8000/api/datasets
# Expected: 200, datasets array with 1 item

# Get detail
curl http://localhost:8000/api/datasets/{dataset_id}
# Expected: 200, full metadata

# Wait a second, then get profile
curl http://localhost:8000/api/datasets/{dataset_id}/profile
# Expected: 200 with rows=569, columns=32, target.candidate=diagnosis
```

### Day 2

**Hour 1–2: Error handling polish**

```python
# Add to every endpoint — good error messages for the frontend
@router.post("/upload", ...)
async def upload_dataset(...):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Size check before reading entire file
    max_mb = config.max_file_size_mb
    # Note: reading into memory first is acceptable for MVP file sizes
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File size {size_mb:.1f}MB exceeds limit of {max_mb}MB"
        )
```

Verify these error cases produce correct HTTP codes:
| Scenario | Expected HTTP | Expected body field |
|---|---|---|
| Non-CSV file (.txt) | 400 | `detail: "Unsupported format: txt"` |
| File too large | 413 | `detail: "File size Xmb exceeds limit"` |
| Dataset not found | 404 | `detail: "Dataset DS-XXX not found"` |
| Profile not ready | 202 | `status: "profiling_in_progress"` |
| Storage failure | 500 | `detail: "Internal server error"` |

**Hour 2–3: Test all 4 datasets**

Upload all 4 demo CSVs through the API, confirm each returns:
- `status: REGISTERED`
- Different `sha256` for each
- Correct `filename` and `file_size_bytes`
- Profile endpoint returns 200 (not 202) within a few seconds

**Hour 3–4: Coordinate with Naeem**

Naeem needs stable API contracts on Day 1. Share with him:
1. Base URL: `http://localhost:8000`
2. All endpoint paths (§5 above)
3. All response shapes (§5 above)
4. CORS is already configured in `main.py` for `localhost:5173` and `localhost:3000`

Build a simple mock that returns the exact response shapes if your server isn't ready yet:
```python
# Temporary mock endpoint for Naeem to develop against
@router.get("/demo/breast-cancer", response_model=DatasetDetailResponse)
def get_demo_dataset():
    """Returns mock breast cancer dataset metadata for frontend development."""
    return DatasetDetailResponse(
        dataset_id="a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
        display_id="DS-000001",
        filename="breast_cancer.csv",
        container_type="CSV",
        file_size_bytes=125847,
        sha256="abc123...",
        status="REGISTERED",
        upload_timestamp="2026-09-10T14:23:45.123Z",
        storage_path="datasets/DS-000001/raw/original.csv",
        is_duplicate=False,
        duplicate_of=None
    )
```

**Hour 4–5: OpenAPI docs verification**

Navigate to `http://localhost:8000/docs`. Verify:
- All 4 endpoints appear under the "datasets" tag
- Upload endpoint shows file upload form
- Response schemas are correctly documented
- Example values match the contracts above

**Hour 5–6: Integration test**

Run this script end-to-end:
```python
import httpx, time

BASE = "http://localhost:8000"

# Upload
with open("data/demo/breast_cancer.csv", "rb") as f:
    resp = httpx.post(f"{BASE}/api/datasets/upload", files={"file": f})
assert resp.status_code == 201, f"Upload failed: {resp.text}"
data = resp.json()
assert data["status"] == "REGISTERED"
dataset_id = data["dataset_id"]
print(f"Uploaded: {dataset_id}")

# List
resp = httpx.get(f"{BASE}/api/datasets")
assert resp.status_code == 200
assert len(resp.json()["datasets"]) >= 1
print("List OK")

# Detail
resp = httpx.get(f"{BASE}/api/datasets/{dataset_id}")
assert resp.status_code == 200
assert resp.json()["filename"] == "breast_cancer.csv"
print("Detail OK")

# Profile (wait for background task)
time.sleep(3)
resp = httpx.get(f"{BASE}/api/datasets/{dataset_id}/profile")
assert resp.status_code == 200, f"Profile not ready: {resp.status_code}"
profile = resp.json()
assert profile["dimensions"]["rows"] == 569
assert profile["target"]["candidate"] == "diagnosis"
print("Profile OK:", profile["dimensions"])
```

---

## 7. Mock Data to Build Against on Day 1

Use **Breast Cancer Wisconsin** for all Day 1 development. The exact mock responses you should expect (and can use to build Pydantic models from) are:

**Upload response:**
```json
{
  "dataset_id":          "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "display_id":          "DS-000001",
  "status":              "REGISTERED",
  "filename":            "breast_cancer.csv",
  "container_type":      "CSV",
  "upload_timestamp":    "2026-09-10T14:23:45.123Z",
  "file_size_bytes":     125847,
  "sha256":              "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
  "storage_path":        "datasets/DS-000001/raw/original.csv",
  "is_duplicate":        false,
  "duplicate_of":        null,
  "validation_warnings": [],
  "rejection_reason":    null
}
```

**Profile response (what Jayed's profiler returns for this file):**
```json
{
  "dataset_id":   "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "profile_id":   "PROFILE-000001",
  "modality":     "TABULAR",
  "dimensions": { "rows": 569, "columns": 32 },
  "features":   { "numerical": 30, "categorical": 1 },
  "target": { "candidate": "diagnosis", "confidence": "HIGH" },
  "task": { "candidate": "BINARY_CLASSIFICATION", "confidence": "HIGH" },
  "class_distribution": { "0": 357, "1": 212 },
  "missing_values": { "total": 0, "percentage": 0.0, "by_column": {} },
  "duplicates": { "candidate_count": 0 },
  "warnings": ["Class imbalance detected: 62.7% vs 37.3%"],
  "status": "PROFILED",
  "profiled_at": "2026-09-10T14:25:12.456Z"
}
```

If Jayed hasn't finished the profiler yet, return a hardcoded mock from the profile endpoint using exactly the above — this lets Naeem build the frontend without waiting.

---

## 8. Definition of Done

- [ ] `POST /api/datasets/upload` accepts a valid CSV, returns `201` with the upload response contract shape.
- [ ] Upload endpoint returns `400` (not `500`) for unsupported file formats with a human-readable `detail` message.
- [ ] Upload endpoint returns `413` (not `500`) when file exceeds `max_file_size_mb` from config.
- [ ] Profiling is triggered automatically after upload (either sync for small files or as a BackgroundTask).
- [ ] `GET /api/datasets` returns a list with `total` count and array of dataset summaries.
- [ ] `GET /api/datasets/{id}` returns `200` with full dataset metadata for a valid ID.
- [ ] `GET /api/datasets/{id}` returns `404` with `{"detail": "Dataset <id> not found"}` for unknown IDs.
- [ ] `GET /api/datasets/{id}/profile` returns `200` with profile matching `dataset_profile.json` contract shape once profiling is complete.
- [ ] `GET /api/datasets/{id}/profile` returns `202` with `{"status": "profiling_in_progress"}` while profile is computing.
- [ ] All response models are Pydantic `BaseModel` subclasses — no bare `dict` returns.
- [ ] All 4 demo datasets (breast cancer, heart disease, Parkinson's) upload successfully through the endpoint.
- [ ] `GET /api/datasets/{breast_cancer_id}/profile` returns `rows=569`, `columns=32`, `target.candidate="diagnosis"`.
- [ ] CORS allows requests from `localhost:5173` (Naeem's Vite dev server).
- [ ] `http://localhost:8000/docs` shows all 4 endpoints with correct schemas and example values.
- [ ] Uploading the same file twice: second upload returns `is_duplicate=true` but still returns `201` (not `409`).
- [ ] No endpoint returns a raw Python traceback to the client — all errors are `HTTPException` with clear messages.
- [ ] Background profiling failure does NOT crash the upload response — errors are logged, not raised.

---

## 9. Common Failure Modes to Avoid

**From phase1.md §11 — Format validation:**
> "Do NOT rely only on `filename.endswith('.csv')`."
- **Fix:** Your route passes the file to Arzaan's ingestion service which handles content-type validation. Don't add redundant extension checks in the route handler that might conflict with the service layer.

**From phase1.md §18 — Duplicate is not an error:**
> "`duplicate ≠ invalid`. The user may intentionally want to create another project using the same dataset."
- **Fix:** Return `201 Created` even when `is_duplicate=true`. Do NOT return `409 Conflict`.

**From implementaion_plan.md §80 — Never block on long-running work:**
> "The frontend should never wait for the entire experiment in one HTTP request."
- **Fix:** Profiling runs as a `BackgroundTask`. The upload returns `201` immediately. The frontend polls `GET /api/datasets/{id}/profile` — your endpoint returns `202` until the profile is ready.

**From phase1.md §39 — Never log biomedical data:**
> "Never log sensitive biomedical data itself."
- **Fix:** Log metadata only: `logger.info(f"Upload: {filename}, {size_bytes}B, sha256={sha256[:8]}...")`. Never log file content or pandas DataFrame content.

**FastAPI `UploadFile` gotcha:**
> `await file.read()` consumes the file pointer. Reading it again returns empty bytes.
- **Fix:** Read once into `file_bytes = await file.read()`, then pass `file_bytes` to the ingestion service. Never call `file.read()` twice.

**SQLAlchemy session lifecycle:**
> FastAPI background tasks run after the response is sent. The `db` session from `Depends(get_db)` will be closed by then.
- **Fix:** For the background profiling task, create a NEW database session inside `_run_profiling_background()`, not the one from the request. Use `SessionLocal()` directly, not `Depends(get_db)`.

**Pydantic v2 serialization:**
> In Pydantic v2, `datetime` fields serialize differently than strings.
- **Fix:** Store timestamps as ISO 8601 strings in the response models, not `datetime` objects, to avoid serialization surprises. Or use `model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})`.

**HTTP 422 Unprocessable Entity:**
> FastAPI automatically returns `422` when a request body doesn't match the expected schema. This is correct but can confuse the frontend.
- **Fix:** Ensure your Pydantic models have clear field names. When testing with curl, make sure the field name is exactly `"file"` (matches `File(...)`).

---

## 10. Ready-to-Paste First Prompt

```
I am building the Dataset API layer for a Hybrid Quantum-Classical Disease Detection 
Platform called QuantWarriors. My job is to implement exactly 4 FastAPI endpoints in 
backend/api/datasets.py:

1. POST /api/datasets/upload       — receive CSV, call ingestion service, return upload result
2. GET  /api/datasets               — list all registered datasets  
3. GET  /api/datasets/{dataset_id}  — get single dataset metadata
4. GET  /api/datasets/{dataset_id}/profile — get profiling results

Tech stack: Python 3.10, FastAPI 0.104+, Pydantic 2.5, SQLAlchemy 2.0.

The file already exists in the codebase:
- backend/main.py (has app.include_router(datasets.router) already)
- backend/storage/database.py (has get_db() dependency)
- backend/storage/repositories.py (has DatasetRepository)
- backend/core/config.py (has config object with storage_base_path, max_file_size_mb)
- backend/core/exceptions.py (has UnsupportedFormatError, StorageError, etc.)

Services I call (built by teammates):
- DatasetIngestionService.ingest(filename, content_type, file_bytes) -> dict
  returns the upload response contract shape
- DatasetProfiler.profile(df, dataset_id) -> DatasetProfile with .to_dict()

UPLOAD RESPONSE CONTRACT (return this exact shape on success):
{
  "dataset_id":          "<UUID>",
  "display_id":          "DS-000001",
  "status":              "REGISTERED",
  "filename":            "breast_cancer.csv",
  "container_type":      "CSV",
  "upload_timestamp":    "2026-09-10T14:23:45.123Z",
  "file_size_bytes":     125847,
  "sha256":              "<64-char hex>",
  "storage_path":        "datasets/DS-000001/raw/original.csv",
  "is_duplicate":        false,
  "duplicate_of":        null,
  "validation_warnings": [],
  "rejection_reason":    null
}

PROFILE RESPONSE CONTRACT (match dataset_profile.json):
{
  "dataset_id": "...", "profile_id": "PROFILE-000001", "modality": "TABULAR",
  "dimensions": {"rows": 569, "columns": 32},
  "features": {"numerical": 30, "categorical": 1},
  "target": {"candidate": "diagnosis", "confidence": "HIGH"},
  "task": {"candidate": "BINARY_CLASSIFICATION", "confidence": "HIGH"},
  "class_distribution": {"0": 357, "1": 212},
  "missing_values": {"total": 0, "percentage": 0.0, "by_column": {}},
  "duplicates": {"candidate_count": 0},
  "warnings": [...], "status": "PROFILED", "profiled_at": "..."
}

CRITICAL RULES:
1. Profiling runs as BackgroundTask — upload returns 201 immediately
2. GET /profile returns 202 {"status": "profiling_in_progress"} if profile not ready yet
3. Duplicate uploads return 201 is_duplicate=true (NOT 409)
4. Background task uses its OWN db session (not the request session which closes after response)
5. Never return raw tracebacks to client — all errors are HTTPException
6. Never log file content

HTTP status codes:
- 201 on successful upload
- 400 on bad format
- 404 on dataset not found
- 202 on profile not ready
- 413 on file too large
- 500 on storage error

Build the complete datasets.py file with all 4 endpoints, Pydantic models for all responses, 
proper error handling, and a mock endpoint GET /demo/breast-cancer that returns hardcoded 
breast cancer metadata so the frontend can develop immediately.
```
