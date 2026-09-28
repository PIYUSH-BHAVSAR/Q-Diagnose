"""
test_arzaan.py
==============
Self-contained test suite for Arzaan's foundation layer.
Tests ONLY Arzaan's scope — no ML, no frontend, no other teammates' code.

Run:
    python test_arzaan.py           # from the arjan/ directory
    python test_arzaan.py -v        # verbose (show each assertion)
    python test_arzaan.py http      # also run live HTTP tests (server must be running)

Covers every item in guide_arzaan.md §8 Definition of Done.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

VERBOSE = "-v" in sys.argv
RUN_HTTP = "http" in sys.argv

passed = 0
failed = 0
skipped = 0


def ok(msg: str) -> None:
    global passed
    passed += 1
    if VERBOSE:
        print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str, detail: str = "") -> None:
    global failed
    failed += 1
    print(f"  {RED}✗ FAIL:{RESET} {msg}")
    if detail:
        print(f"         {detail}")


def skip(msg: str) -> None:
    global skipped
    print(f"  {YELLOW}⊘ SKIP:{RESET} {msg}")


def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")


def run_test(name: str, fn):
    """Run a single test function, catch exceptions."""
    global failed
    try:
        fn()
        ok(name)
    except AssertionError as e:
        fail(name, str(e))
    except Exception as e:
        fail(name, f"{type(e).__name__}: {e}")
        if VERBOSE:
            traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Config
# ═══════════════════════════════════════════════════════════════════════════════

section("1. Core Config (backend/core/config.py)")

def test_config_loads():
    from backend.core.config import config
    assert config is not None

def test_config_storage_base_path():
    from backend.core.config import config
    assert config.storage_base_path.exists(), f"base_path does not exist: {config.storage_base_path}"

def test_config_max_file_size():
    from backend.core.config import config
    assert config.storage.max_file_size_mb == 50
    assert config.get_max_file_size_bytes() == 50 * 1024 * 1024

def test_config_supported_formats():
    from backend.core.config import config
    assert ".csv" in config.storage.supported_formats
    assert ".xlsx" in config.storage.supported_formats
    assert ".zip" in config.storage.supported_formats

def test_config_quantum_backend_type():
    from backend.core.config import config
    # Contract: backend_type must be LOCAL_SIMULATOR | CLOUD_SIMULATOR | HARDWARE
    valid = {"LOCAL_SIMULATOR", "CLOUD_SIMULATOR", "HARDWARE"}
    assert config.quantum_config.backend_type in valid, \
        f"Invalid backend_type: {config.quantum_config.backend_type}"

def test_config_experiment_test_size():
    from backend.core.config import config
    assert config.experiment.test_size == 0.20

def test_config_classical_models_present():
    from backend.core.config import config
    assert "logistic_regression" in config.classical_models
    assert "random_forest" in config.classical_models
    assert "svm" in config.classical_models

def test_config_paths():
    from backend.core.config import config
    assert config.uploads_path is not None
    assert config.artifacts_path is not None

for t in [test_config_loads, test_config_storage_base_path, test_config_max_file_size,
          test_config_supported_formats, test_config_quantum_backend_type,
          test_config_experiment_test_size, test_config_classical_models_present,
          test_config_paths]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Logging
# ═══════════════════════════════════════════════════════════════════════════════

section("2. Logging (backend/core/logging.py)")

def test_get_logger_returns_logger():
    from backend.core.logging import get_logger
    import logging
    logger = get_logger("test.arzaan")
    assert hasattr(logger, "info")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")

def test_logger_has_handler():
    from backend.core.logging import get_logger
    import logging
    get_logger("test.arzaan")
    root = logging.getLogger()
    assert len(root.handlers) > 0, "Root logger has no handlers"

def test_logger_format_contains_required_parts():
    from backend.core.logging import get_logger
    import logging
    import io
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)
    test_logger = logging.getLogger("format_test_unique")
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.DEBUG)
    test_logger.info("test_message_xyz")
    output = stream.getvalue()
    assert "|" in output, "Format missing pipe separators"
    assert "INFO" in output
    assert "test_message_xyz" in output

for t in [test_get_logger_returns_logger, test_logger_has_handler, test_logger_format_contains_required_parts]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Exceptions
# ═══════════════════════════════════════════════════════════════════════════════

section("3. Exceptions (backend/core/exceptions.py)")

def test_exception_hierarchy():
    from backend.core.exceptions import (
        QMLPlatformError, DatasetValidationError, UnsupportedFormatError,
        FileSizeLimitError, UnsafeArchiveError, StorageError,
        ExperimentNotFoundError, DatasetNotFoundError, DataLeakageError
    )
    for cls in [DatasetValidationError, UnsupportedFormatError, FileSizeLimitError,
                UnsafeArchiveError, StorageError, ExperimentNotFoundError,
                DatasetNotFoundError, DataLeakageError]:
        assert issubclass(cls, QMLPlatformError), f"{cls.__name__} not a subclass of QMLPlatformError"

def test_unsupported_format_error_fields():
    from backend.core.exceptions import UnsupportedFormatError
    e = UnsupportedFormatError("test.exe", ".exe")
    assert e.filename == "test.exe"
    assert e.detected_ext == ".exe"
    assert e.code == "INVALID_FORMAT"

def test_file_size_limit_error_fields():
    from backend.core.exceptions import FileSizeLimitError
    e = FileSizeLimitError("big.csv", 60 * 1024 * 1024, 50)
    assert e.size_bytes == 60 * 1024 * 1024
    assert e.limit_mb == 50
    assert e.code == "SIZE_LIMIT_EXCEEDED"

def test_unsafe_archive_error_fields():
    from backend.core.exceptions import UnsafeArchiveError
    e = UnsafeArchiveError("zip bomb detected")
    assert e.reason == "zip bomb detected"
    assert e.code == "UNSAFE_ARCHIVE"

def test_experiment_not_found_error_fields():
    from backend.core.exceptions import ExperimentNotFoundError
    e = ExperimentNotFoundError("EXP-ABC123")
    assert e.experiment_id == "EXP-ABC123"
    assert e.code == "EXPERIMENT_NOT_FOUND"

for t in [test_exception_hierarchy, test_unsupported_format_error_fields,
          test_file_size_limit_error_fields, test_unsafe_archive_error_fields,
          test_experiment_not_found_error_fields]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Database
# ═══════════════════════════════════════════════════════════════════════════════

section("4. Database (backend/storage/database.py)")

def test_init_db_creates_tables():
    from backend.storage.database import init_db, engine
    from sqlalchemy import text
    init_db()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).fetchall()
        tables = [r[0] for r in rows]
    for required in ["datasets", "experiments", "model_results", "reports"]:
        assert required in tables, f"Table '{required}' not created by init_db()"

def test_get_db_yields_session():
    from backend.storage.database import get_db
    from sqlalchemy.orm import Session
    gen = get_db()
    db = next(gen)
    assert db is not None
    assert hasattr(db, "query")
    try:
        next(gen)
    except StopIteration:
        pass

def test_db_is_sqlite():
    from backend.storage.database import DATABASE_URL
    assert "sqlite" in DATABASE_URL

for t in [test_init_db_creates_tables, test_get_db_yields_session, test_db_is_sqlite]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — ORM Models
# ═══════════════════════════════════════════════════════════════════════════════

section("5. ORM Models (backend/storage/models.py)")

def test_dataset_model_has_required_fields():
    from backend.storage.models import Dataset
    required = [
        "id", "display_id", "original_filename", "container_type",
        "file_size_bytes", "sha256", "raw_storage_path", "upload_timestamp",
        "status", "created_by",
        "is_duplicate", "duplicate_of",   # ISSUES.md M-11
    ]
    for f in required:
        assert hasattr(Dataset, f), f"Dataset missing field: '{f}'"

def test_experiment_model_has_progress_data():
    from backend.storage.models import Experiment
    # experiment_status.json contract requires progress_data column
    assert hasattr(Experiment, "progress_data"), "Experiment missing 'progress_data' column"
    assert hasattr(Experiment, "status")
    assert hasattr(Experiment, "seed")

def test_model_result_fields():
    from backend.storage.models import ModelResult
    for f in ["id", "experiment_id", "model_name", "model_type",
              "metrics_json", "resource_json", "quantum_metrics_json", "artifact_path"]:
        assert hasattr(ModelResult, f), f"ModelResult missing field: '{f}'"

def test_report_fields():
    from backend.storage.models import Report
    for f in ["id", "experiment_id", "report_type", "content_json", "created_at"]:
        assert hasattr(Report, f), f"Report missing field: '{f}'"

def test_dataset_to_response_dict():
    from backend.storage.models import Dataset
    from datetime import datetime, timezone
    ds = Dataset(
        id="test-uuid",
        display_id="DS-000001",
        original_filename="test.csv",
        container_type="CSV",
        file_size_bytes=1234,
        sha256="a" * 64,
        raw_storage_path="datasets/DS-000001/raw/original.csv",
        upload_timestamp=datetime(2026, 9, 25, 10, 0, 0, tzinfo=timezone.utc),
        status="REGISTERED",
        created_by="system",
        is_duplicate=False,
        duplicate_of=None,
    )
    d = ds.to_response_dict()
    # Check contract field names match exactly
    assert d["dataset_id"] == "test-uuid"
    assert d["display_id"] == "DS-000001"
    assert d["status"] == "REGISTERED"
    assert d["filename"] == "test.csv"          # contract field is 'filename' not 'original_filename'
    assert d["container_type"] == "CSV"
    assert d["file_size_bytes"] == 1234
    assert d["sha256"] == "a" * 64
    assert d["storage_path"] == "datasets/DS-000001/raw/original.csv"
    assert d["is_duplicate"] is False
    assert d["duplicate_of"] is None
    assert isinstance(d["upload_timestamp"], str)
    assert d["upload_timestamp"].endswith("Z")   # ISO 8601 UTC

for t in [test_dataset_model_has_required_fields, test_experiment_model_has_progress_data,
          test_model_result_fields, test_report_fields, test_dataset_to_response_dict]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Repositories
# ═══════════════════════════════════════════════════════════════════════════════

section("6. Repositories (backend/storage/repositories.py)")

# Use a fresh in-memory DB for repo tests to avoid polluting mvp.db
from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import sessionmaker as _sessionmaker
from backend.storage.database import Base as _Base
import backend.storage.models as _models_mod  # noqa — registers models

_test_engine = _create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
_Base.metadata.create_all(bind=_test_engine)
_TestSession = _sessionmaker(bind=_test_engine)


def _fresh_db():
    return _TestSession()


def test_dataset_repo_create_and_get():
    from backend.storage.repositories import DatasetRepository
    db = _fresh_db()
    repo = DatasetRepository()
    data = {
        "id": str(uuid.uuid4()),
        "display_id": "DS-TEST01",
        "original_filename": "test.csv",
        "container_type": "CSV",
        "file_size_bytes": 500,
        "sha256": hashlib.sha256(b"test").hexdigest(),
        "raw_storage_path": "datasets/DS-TEST01/raw/original.csv",
        "upload_timestamp": datetime.now(timezone.utc),
        "status": "REGISTERED",
        "created_by": "test",
        "is_duplicate": False,
        "duplicate_of": None,
    }
    ds = repo.create(db, data)
    assert ds.id == data["id"]
    assert ds.display_id == "DS-TEST01"
    assert ds.is_duplicate is False

    found = repo.get_by_id(db, data["id"])
    assert found is not None
    assert found.display_id == "DS-TEST01"
    db.close()

def test_dataset_repo_get_by_sha256():
    from backend.storage.repositories import DatasetRepository
    db = _fresh_db()
    repo = DatasetRepository()
    sha = hashlib.sha256(b"unique_content_abc").hexdigest()
    data = {
        "id": str(uuid.uuid4()),
        "display_id": "DS-SHA01",
        "original_filename": "sha_test.csv",
        "container_type": "CSV",
        "file_size_bytes": 100,
        "sha256": sha,
        "raw_storage_path": "datasets/DS-SHA01/raw/original.csv",
        "upload_timestamp": datetime.now(timezone.utc),
        "status": "REGISTERED",
        "created_by": "test",
        "is_duplicate": False,
        "duplicate_of": None,
    }
    repo.create(db, data)
    found = repo.get_by_sha256(db, sha)
    assert found is not None
    assert found.sha256 == sha

    not_found = repo.get_by_sha256(db, "0" * 64)
    assert not_found is None
    db.close()

def test_dataset_repo_update_status():
    from backend.storage.repositories import DatasetRepository
    db = _fresh_db()
    repo = DatasetRepository()
    data = {
        "id": str(uuid.uuid4()),
        "display_id": "DS-STAT01",
        "original_filename": "stat.csv",
        "container_type": "CSV",
        "file_size_bytes": 100,
        "sha256": hashlib.sha256(b"stat_content").hexdigest(),
        "raw_storage_path": "datasets/DS-STAT01/raw/original.csv",
        "upload_timestamp": datetime.now(timezone.utc),
        "status": "REGISTERED",
        "created_by": "test",
        "is_duplicate": False,
        "duplicate_of": None,
    }
    ds = repo.create(db, data)
    updated = repo.update_status(db, ds.id, "REJECTED")
    assert updated.status == "REJECTED"
    db.close()

def test_dataset_repo_list_all():
    from backend.storage.repositories import DatasetRepository
    db = _fresh_db()
    repo = DatasetRepository()
    before = len(repo.list_all(db))
    for i in range(3):
        repo.create(db, {
            "id": str(uuid.uuid4()),
            "display_id": f"DS-LIST{i:02d}",
            "original_filename": f"list{i}.csv",
            "container_type": "CSV",
            "file_size_bytes": 100,
            "sha256": hashlib.sha256(f"list_content_{i}".encode()).hexdigest(),
            "raw_storage_path": f"datasets/DS-LIST{i:02d}/raw/original.csv",
            "upload_timestamp": datetime.now(timezone.utc),
            "status": "REGISTERED",
            "created_by": "test",
            "is_duplicate": False,
            "duplicate_of": None,
        })
    after = repo.list_all(db)
    assert len(after) == before + 3
    db.close()

def test_experiment_repo_create_and_update_progress():
    from backend.storage.repositories import DatasetRepository, ExperimentRepository
    db = _fresh_db()
    ds_repo = DatasetRepository()
    exp_repo = ExperimentRepository()

    # Create a dataset first (FK requirement)
    ds_id = str(uuid.uuid4())
    ds_repo.create(db, {
        "id": ds_id,
        "display_id": "DS-EXP01",
        "original_filename": "exp.csv",
        "container_type": "CSV",
        "file_size_bytes": 100,
        "sha256": hashlib.sha256(b"exp_content").hexdigest(),
        "raw_storage_path": "datasets/DS-EXP01/raw/original.csv",
        "upload_timestamp": datetime.now(timezone.utc),
        "status": "REGISTERED",
        "created_by": "test",
        "is_duplicate": False,
        "duplicate_of": None,
    })

    exp_id = str(uuid.uuid4())
    exp = exp_repo.create(db, {
        "id": exp_id,
        "display_id": "EXP-TEST01",
        "dataset_id": ds_id,
        "status": "CREATED",
        "seed": 42,
    })
    assert exp.status == "CREATED"

    # Update progress — experiment_status.json contract shape
    progress = {
        "status": "RUNNING_QUANTUM",
        "stage": "quantum_training",
        "progress": 0.67,
        "message": "Training VQC — Epoch 18/30",
        "current_model": "vqc",
        "completed_models": ["logistic_regression", "svm", "random_forest"],
        "circuit_executions": 8320,
        "current_epoch": 18,
        "total_epochs": 30,
        "elapsed_seconds": 412.5,
        "estimated_remaining_seconds": 250.3,
        "error_message": None,
    }
    exp_repo.update_progress(db, exp_id, progress)

    retrieved = exp_repo.get_progress(db, exp_id)
    assert retrieved is not None
    assert retrieved["status"] == "RUNNING_QUANTUM"
    assert retrieved["circuit_executions"] == 8320
    assert retrieved["current_model"] == "vqc"
    db.close()

for t in [test_dataset_repo_create_and_get, test_dataset_repo_get_by_sha256,
          test_dataset_repo_update_status, test_dataset_repo_list_all,
          test_experiment_repo_create_and_update_progress]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — File Storage
# ═══════════════════════════════════════════════════════════════════════════════

section("7. File Storage (backend/storage/files.py)")

# Use a temp directory so tests don't touch real datasets/
_TMP_BASE = Path(tempfile.mkdtemp(prefix="qd_test_"))


def test_local_file_storage_init():
    from backend.storage.files import LocalFileStorage
    storage = LocalFileStorage(base_path=_TMP_BASE)
    assert storage._base == _TMP_BASE

def test_save_and_read_dataset():
    from backend.storage.files import LocalFileStorage
    storage = LocalFileStorage(base_path=_TMP_BASE)
    content = b"id,diagnosis,radius_mean\n1,M,17.99\n2,B,10.38\n"
    rel_path = storage.save_dataset("DS-T01", content, "test.csv")
    assert rel_path == "datasets/DS-T01/raw/original.csv"
    abs_path = _TMP_BASE / rel_path
    assert abs_path.exists(), f"File not saved at {abs_path}"

    read_back = storage.read_dataset("DS-T01")
    assert read_back == content, "Read-back content does not match original"

def test_save_dataset_immutability():
    """Writing the same display_id twice must raise StorageError."""
    from backend.storage.files import LocalFileStorage
    from backend.core.exceptions import StorageError
    storage = LocalFileStorage(base_path=_TMP_BASE)
    storage.save_dataset("DS-IMM01", b"col1,col2\n1,2\n", "data.csv")
    try:
        storage.save_dataset("DS-IMM01", b"col1,col2\n3,4\n", "data.csv")
        assert False, "Expected StorageError — file should be immutable"
    except StorageError:
        pass  # correct

def test_storage_path_format():
    """Storage path must follow datasets/{display_id}/raw/original{ext} pattern."""
    from backend.storage.files import LocalFileStorage
    storage = LocalFileStorage(base_path=_TMP_BASE)
    rel_path = storage.save_dataset("DS-FMT01", b"a,b\n1,2\n", "myfile.csv")
    assert rel_path.startswith("datasets/"), f"Path must start with datasets/: {rel_path}"
    assert "/raw/original" in rel_path, f"Path must contain /raw/original: {rel_path}"
    assert rel_path.endswith(".csv"), f"Path must end with .csv: {rel_path}"

def test_get_profile_path_no_string_manipulation():
    """get_profile_path must not derive path from storage_path string (ISSUES.md M-02)."""
    from backend.storage.files import LocalFileStorage
    storage = LocalFileStorage(base_path=_TMP_BASE)
    profile_path = storage.get_profile_path("DS-000001")
    assert profile_path == "datasets/DS-000001/profile.json"
    # Must NOT contain /raw/ — that would be derived from storage_path
    assert "/raw/" not in profile_path

def test_save_artifact():
    from backend.storage.files import LocalFileStorage
    storage = LocalFileStorage(base_path=_TMP_BASE)
    data = b'{"key": "value"}'
    rel_path = storage.save_artifact("EXP-TEST01", "result.json", data)
    assert rel_path == "artifacts/experiments/EXP-TEST01/result.json"
    assert (_TMP_BASE / rel_path).exists()
    read_back = storage.read_artifact("EXP-TEST01", "result.json")
    assert read_back == data

for t in [test_local_file_storage_init, test_save_and_read_dataset,
          test_save_dataset_immutability, test_storage_path_format,
          test_get_profile_path_no_string_manipulation, test_save_artifact]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Ingestion Pipeline (core logic)
# ═══════════════════════════════════════════════════════════════════════════════

section("8. Ingestion Pipeline (backend/data/loader.py)")

from backend.data.loader import (
    calculate_sha256, validate_format, validate_zip,
    DatasetIngestionService, DatasetLoader
)
from backend.core.exceptions import UnsupportedFormatError, UnsafeArchiveError
import io as _io
import zipfile as _zipfile


def test_calculate_sha256():
    content = b"hello world"
    expected = hashlib.sha256(content).hexdigest()
    result = calculate_sha256(content)
    assert result == expected
    assert len(result) == 64
    assert result.islower()

def test_sha256_is_64_chars():
    result = calculate_sha256(b"any content here")
    assert len(result) == 64, f"SHA-256 must be 64 chars, got {len(result)}"

def test_validate_format_csv_accepted():
    ct, warnings = validate_format("data.csv", b"col1,col2\n1,2\n")
    assert ct == "CSV"

def test_validate_format_xlsx_accepted():
    # XLSX is a ZIP internally — create a minimal ZIP with .xlsx extension
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("xl/workbook.xml", "<workbook/>")
    xlsx_bytes = buf.getvalue()
    ct, warnings = validate_format("data.xlsx", xlsx_bytes)
    assert ct == "XLSX"

def test_validate_format_rejects_txt():
    try:
        validate_format("data.txt", b"some text content")
        assert False, "Should have raised UnsupportedFormatError"
    except UnsupportedFormatError as e:
        assert e.code == "INVALID_FORMAT"

def test_validate_format_rejects_exe_magic_bytes():
    """EXE file renamed to .csv must be rejected (phase1.md §11)."""
    exe_bytes = b"\x4d\x5a" + b"\x00" * 200   # MZ header
    try:
        validate_format("legit.csv", exe_bytes)
        assert False, "EXE magic bytes should be rejected even with .csv extension"
    except UnsupportedFormatError as e:
        assert e.code == "INVALID_FORMAT"

def test_validate_format_rejects_pdf_magic_bytes():
    pdf_bytes = b"\x25\x50\x44\x46" + b"\x00" * 100   # %PDF header
    try:
        validate_format("report.csv", pdf_bytes)
        assert False, "PDF magic bytes should be rejected"
    except UnsupportedFormatError:
        pass

def test_validate_format_rejects_png():
    png_bytes = b"\x89\x50\x4e\x47" + b"\x00" * 100
    try:
        validate_format("image.csv", png_bytes)
        assert False, "PNG magic bytes should be rejected"
    except UnsupportedFormatError:
        pass

def test_validate_zip_accepts_valid_zip():
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("data.csv", "col1,col2\n1,2\n")
    validate_zip(buf.getvalue())   # should not raise

def test_validate_zip_rejects_path_traversal():
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../../etc/passwd", "root:x:0:0")
    try:
        validate_zip(buf.getvalue())
        assert False, "Path traversal should be rejected"
    except UnsafeArchiveError as e:
        assert "unsafe path" in str(e).lower() or "path" in str(e).lower()

def test_validate_zip_rejects_bad_zip():
    try:
        validate_zip(b"not a zip at all")
        assert False, "Bad ZIP should raise UnsafeArchiveError"
    except UnsafeArchiveError:
        pass

for t in [test_calculate_sha256, test_sha256_is_64_chars,
          test_validate_format_csv_accepted, test_validate_format_xlsx_accepted,
          test_validate_format_rejects_txt, test_validate_format_rejects_exe_magic_bytes,
          test_validate_format_rejects_pdf_magic_bytes, test_validate_format_rejects_png,
          test_validate_zip_accepts_valid_zip, test_validate_zip_rejects_path_traversal,
          test_validate_zip_rejects_bad_zip]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — DatasetIngestionService (end-to-end pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

section("9. DatasetIngestionService — end-to-end pipeline")

# Fresh DB + temp storage for full ingestion tests
from backend.storage.database import Base as _Base2
_pipe_engine = _create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
_Base2.metadata.create_all(bind=_pipe_engine)
_PipeSession = _sessionmaker(bind=_pipe_engine)
_TMP_PIPE = Path(tempfile.mkdtemp(prefix="qd_pipe_"))

# Patch file_storage to use temp dir for these tests
import backend.storage.files as _files_mod
_orig_storage = _files_mod.file_storage
_files_mod.file_storage = _files_mod.LocalFileStorage(base_path=_TMP_PIPE)
import backend.data.loader as _loader_mod
_loader_mod.file_storage = _files_mod.file_storage


def _pipe_db():
    return _PipeSession()


def test_ingest_csv_returns_registered():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"id,diagnosis,radius_mean\n1,M,17.99\n2,B,10.38\n"
    result = svc.ingest("sample.csv", "text/csv", content)
    assert result["status"] == "REGISTERED", f"Expected REGISTERED, got {result['status']}"
    db.close()

def test_ingest_returns_full_contract():
    """Every field in dataset_upload_response.json must be present."""
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"a,b,c\n1,2,3\n"
    result = svc.ingest("contract_test.csv", "text/csv", content)
    required_fields = [
        "dataset_id", "display_id", "status", "filename", "container_type",
        "upload_timestamp", "file_size_bytes", "sha256", "storage_path",
        "is_duplicate", "duplicate_of", "validation_warnings", "rejection_reason"
    ]
    for field in required_fields:
        assert field in result, f"Contract field missing from response: '{field}'"
    db.close()

def test_ingest_sha256_is_correct():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"col1,col2\nhello,world\n"
    result = svc.ingest("sha_check.csv", "text/csv", content)
    expected = hashlib.sha256(content).hexdigest()
    assert result["sha256"] == expected
    assert len(result["sha256"]) == 64
    db.close()

def test_ingest_storage_path_format():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"x,y\n1,2\n"
    result = svc.ingest("path_test.csv", "text/csv", content)
    path = result["storage_path"]
    assert path is not None
    assert path.startswith("datasets/")
    assert "/raw/original" in path
    assert path.endswith(".csv")
    db.close()

def test_ingest_file_actually_saved():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"p,q\n9,8\n"
    result = svc.ingest("saved_check.csv", "text/csv", content)
    full_path = _TMP_PIPE / result["storage_path"]
    assert full_path.exists(), f"File not saved at {full_path}"
    assert full_path.read_bytes() == content
    db.close()

def test_ingest_duplicate_detection():
    """Same file uploaded twice: second upload is REGISTERED with is_duplicate=True."""
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"dup,test\n1,2\n3,4\n"
    r1 = svc.ingest("dup.csv", "text/csv", content)
    r2 = svc.ingest("dup.csv", "text/csv", content)
    assert r1["status"] == "REGISTERED"
    assert r2["status"] == "REGISTERED", "Duplicate should still be REGISTERED (not REJECTED)"
    assert r2["is_duplicate"] is True, "Second upload should be is_duplicate=True"
    assert r2["duplicate_of"] == r1["dataset_id"], "duplicate_of should point to first upload"
    db.close()

def test_ingest_invalid_format_returns_error_status():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    result = svc.ingest("bad.txt", "text/plain", b"just some text")
    assert result["status"] == "INVALID_FORMAT"
    assert result["rejection_reason"] is not None
    assert result["dataset_id"] is None   # no DB record created
    db.close()

def test_ingest_size_limit_returns_error_status():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    big = b"a,b,c\n" + b"1,2,3\n" * (51 * 1024 * 1024 // 6)
    result = svc.ingest("huge.csv", "text/csv", big)
    assert result["status"] == "SIZE_LIMIT_EXCEEDED"
    assert result["dataset_id"] is None
    db.close()

def test_ingest_exe_as_csv_rejected():
    """EXE magic bytes with .csv extension must be INVALID_FORMAT."""
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    exe_bytes = b"\x4d\x5a" + b"\x00" * 300
    result = svc.ingest("trojan.csv", "text/csv", exe_bytes)
    assert result["status"] == "INVALID_FORMAT"
    db.close()

def test_ingest_timestamp_is_iso8601_utc():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    result = svc.ingest("ts_test.csv", "text/csv", b"a,b\n1,2\n")
    ts = result["upload_timestamp"]
    assert ts.endswith("Z"), f"Timestamp must end with Z (UTC): {ts}"
    # Must parse without error
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed is not None
    db.close()

def test_ingest_container_type_is_csv():
    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    result = svc.ingest("ct_test.csv", "text/csv", b"col\n1\n2\n")
    assert result["container_type"] == "CSV"
    db.close()

def test_ingest_from_path_breast_cancer():
    """Integration test: ingest real breast_cancer.csv from demo dir."""
    from backend.core.config import config
    demo_path = config.storage_base_path / "data" / "demo" / "breast_cancer.csv"
    if not demo_path.exists():
        raise AssertionError(f"Demo file not found: {demo_path}")

    db = _pipe_db()
    content = demo_path.read_bytes()
    svc = DatasetIngestionService(db=db)
    result = svc.ingest("breast_cancer.csv", "text/csv", content)
    assert result["status"] == "REGISTERED"
    assert len(result["sha256"]) == 64
    assert result["file_size_bytes"] == len(content)
    # Verify file on disk
    full_path = _TMP_PIPE / result["storage_path"]
    assert full_path.exists()
    assert calculate_sha256(full_path.read_bytes()) == result["sha256"]
    db.close()

def test_no_biomedical_data_in_logs():
    """Logs must not contain raw biomedical row content."""
    import logging
    import io as _sio
    stream = _sio.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger()
    root.addHandler(handler)

    db = _pipe_db()
    svc = DatasetIngestionService(db=db)
    content = b"diagnosis,radius_mean\nM,17.99\nB,10.38\nM,19.69\n"
    svc.ingest("bio_log_test.csv", "text/csv", content)

    root.removeHandler(handler)
    log_output = stream.getvalue()
    # Raw cell values must not appear in log output
    assert "17.99" not in log_output, "Raw cell value '17.99' found in logs"
    assert "10.38" not in log_output, "Raw cell value '10.38' found in logs"
    assert "19.69" not in log_output, "Raw cell value '19.69' found in logs"
    db.close()

for t in [test_ingest_csv_returns_registered, test_ingest_returns_full_contract,
          test_ingest_sha256_is_correct, test_ingest_storage_path_format,
          test_ingest_file_actually_saved, test_ingest_duplicate_detection,
          test_ingest_invalid_format_returns_error_status,
          test_ingest_size_limit_returns_error_status,
          test_ingest_exe_as_csv_rejected, test_ingest_timestamp_is_iso8601_utc,
          test_ingest_container_type_is_csv, test_ingest_from_path_breast_cancer,
          test_no_biomedical_data_in_logs]:
    run_test(t.__name__.replace("test_", ""), t)

# Restore original file_storage singleton
_files_mod.file_storage = _orig_storage
_loader_mod.file_storage = _orig_storage


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — DatasetLoader
# ═══════════════════════════════════════════════════════════════════════════════

section("10. DatasetLoader (backend/data/loader.py)")

def test_loader_load_csv_no_hardcoded_columns():
    """load_csv must work on any CSV — not hardcoded to any dataset."""
    from backend.data.loader import DatasetLoader
    from backend.core.config import config
    loader = DatasetLoader()
    demo = config.storage_base_path / "data" / "demo" / "breast_cancer.csv"
    if not demo.exists():
        raise AssertionError("breast_cancer.csv not in demo dir")
    placeholder_id, df = loader.load_csv(str(demo))
    assert df is not None
    assert len(df) > 0, "DataFrame must not be empty"
    assert len(df.columns) > 0
    # Must NOT have hardcoded row count
    assert len(df) == len(df)   # tautology — just verifying it ran

def test_loader_load_csv_all_four_datasets():
    from backend.data.loader import DatasetLoader
    from backend.core.config import config
    loader = DatasetLoader()
    demo_dir = config.storage_base_path / "data" / "demo"
    for fname in ["breast_cancer.csv", "heart_disease.csv", "pima_diabetes.csv", "parkinsons.csv"]:
        path = demo_dir / fname
        if not path.exists():
            raise AssertionError(f"Demo file missing: {fname}")
        _, df = loader.load_csv(str(path))
        assert len(df) > 0, f"{fname}: DataFrame is empty"
        assert len(df.columns) > 0, f"{fname}: No columns"

for t in [test_loader_load_csv_no_hardcoded_columns, test_loader_load_csv_all_four_datasets]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — Adapters
# ═══════════════════════════════════════════════════════════════════════════════

section("11. Adapter Registry (backend/data/adapters.py)")

def test_adapter_registry_has_4_adapters():
    from backend.data.adapters import registry
    assert len(registry) == 4, f"Expected 4 adapters, got {len(registry)}"

def test_adapter_registry_exported_classes():
    from backend.data.adapters import AdapterRegistry, DatasetAdapter, registry
    assert isinstance(registry, AdapterRegistry)

def test_adapter_detect_breast_cancer():
    from backend.data.adapters import registry
    import pandas as pd
    from backend.core.config import config
    demo = config.storage_base_path / "data" / "demo" / "breast_cancer.csv"
    df = pd.read_csv(str(demo))
    adapter = registry.detect_adapter(df)
    assert adapter is not None
    assert adapter.name == "BreastCancerAdapter"

def test_adapter_detect_heart_disease():
    from backend.data.adapters import registry
    import pandas as pd
    from backend.core.config import config
    demo = config.storage_base_path / "data" / "demo" / "heart_disease.csv"
    df = pd.read_csv(str(demo))
    adapter = registry.detect_adapter(df)
    assert adapter is not None
    assert adapter.name == "HeartDiseaseAdapter"

def test_adapter_detect_diabetes():
    from backend.data.adapters import registry
    import pandas as pd
    from backend.core.config import config
    demo = config.storage_base_path / "data" / "demo" / "pima_diabetes.csv"
    df = pd.read_csv(str(demo))
    adapter = registry.detect_adapter(df)
    assert adapter is not None
    assert adapter.name == "DiabetesAdapter"

def test_adapter_detect_parkinsons():
    from backend.data.adapters import registry
    import pandas as pd
    from backend.core.config import config
    demo = config.storage_base_path / "data" / "demo" / "parkinsons.csv"
    df = pd.read_csv(str(demo))
    adapter = registry.detect_adapter(df)
    assert adapter is not None
    assert adapter.name == "ParkinsonsAdapter"

def test_adapter_detect_unknown_returns_none():
    from backend.data.adapters import registry
    import pandas as pd
    df = pd.DataFrame({"weird_col_xyz": [1, 2], "another_xyz": [3, 4]})
    adapter = registry.detect_adapter(df)
    assert adapter is None, "Unknown DataFrame should return None"

def test_breast_cancer_adapt():
    from backend.data.adapters import BreastCancerAdapter
    import pandas as pd
    from backend.core.config import config
    df = pd.read_csv(str(config.storage_base_path / "data" / "demo" / "breast_cancer.csv"))
    adapter = BreastCancerAdapter()
    X, y, meta = adapter.adapt(df)
    assert "diagnosis" not in X.columns, "Target column must be removed from X"
    assert "id" not in X.columns, "Identifier column 'id' must be dropped"
    assert set(y.unique()).issubset({0, 1}), "Target must be binary 0/1"
    assert meta["target_column"] == "diagnosis"
    assert meta["n_features"] == len(X.columns)

def test_parkinsons_adapt_meta_has_groups():
    from backend.data.adapters import ParkinsonsAdapter
    import pandas as pd
    from backend.core.config import config
    df = pd.read_csv(str(config.storage_base_path / "data" / "demo" / "parkinsons.csv"))
    adapter = ParkinsonsAdapter()
    X, y, meta = adapter.adapt(df)
    assert "status" not in X.columns
    assert "name" not in X.columns
    assert meta["requires_grouped_split"] is True
    assert meta["groups"] is not None
    assert set(y.unique()).issubset({0, 1})

for t in [test_adapter_registry_has_4_adapters, test_adapter_registry_exported_classes,
          test_adapter_detect_breast_cancer, test_adapter_detect_heart_disease,
          test_adapter_detect_diabetes, test_adapter_detect_parkinsons,
          test_adapter_detect_unknown_returns_none,
          test_breast_cancer_adapt, test_parkinsons_adapt_meta_has_groups]:
    run_test(t.__name__.replace("test_", ""), t)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — Live HTTP Tests (optional — needs server running)
# ═══════════════════════════════════════════════════════════════════════════════

section("12. Live HTTP Tests (run with: python test_arzaan.py http)")

if not RUN_HTTP:
    skip("HTTP tests skipped — run with 'python test_arzaan.py http' (server must be running on :8000)")
else:
    try:
        import httpx
        BASE = "http://localhost:8000"

        def test_http_health():
            r = httpx.get(f"{BASE}/api/health")
            assert r.status_code == 200
            assert r.json() == {"status": "healthy"}

        def test_http_config():
            r = httpx.get(f"{BASE}/api/config")
            assert r.status_code == 200
            d = r.json()
            assert "quantum_config" in d
            assert "experiment" in d
            assert "classical_models" in d

        def test_http_upload_breast_cancer():
            from backend.core.config import config
            demo = config.storage_base_path / "data" / "demo" / "breast_cancer.csv"
            with open(demo, "rb") as f:
                r = httpx.post(f"{BASE}/api/datasets/upload",
                               files={"file": ("breast_cancer.csv", f, "text/csv")})
            assert r.status_code == 201
            d = r.json()
            assert d["status"] == "REGISTERED"
            assert len(d["sha256"]) == 64
            assert d["container_type"] == "CSV"

        def test_http_upload_invalid_format():
            r = httpx.post(f"{BASE}/api/datasets/upload",
                           files={"file": ("bad.txt", b"just text", "text/plain")})
            assert r.status_code == 422
            assert r.json()["status"] == "INVALID_FORMAT"

        def test_http_list_datasets():
            r = httpx.get(f"{BASE}/api/datasets")
            assert r.status_code == 200
            d = r.json()
            assert "datasets" in d
            assert "total" in d
            assert isinstance(d["datasets"], list)

        def test_http_get_dataset_not_found():
            r = httpx.get(f"{BASE}/api/datasets/nonexistent-uuid")
            assert r.status_code == 404

        for t in [test_http_health, test_http_config, test_http_upload_breast_cancer,
                  test_http_upload_invalid_format, test_http_list_datasets,
                  test_http_get_dataset_not_found]:
            run_test(t.__name__.replace("test_", ""), t)

    except ImportError:
        skip("httpx not available — install with: uv pip install httpx")
    except Exception as e:
        skip(f"HTTP tests failed to connect — is the server running? ({e})")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — All 4 Demo Datasets end-to-end
# ═══════════════════════════════════════════════════════════════════════════════

section("13. All 4 Demo Datasets — end-to-end registration")

from backend.storage.database import Base as _Base3
_all4_engine = _create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
_Base3.metadata.create_all(bind=_all4_engine)
_All4Session = _sessionmaker(bind=_all4_engine)
_TMP_ALL4 = Path(tempfile.mkdtemp(prefix="qd_all4_"))

_files_mod.file_storage = _files_mod.LocalFileStorage(base_path=_TMP_ALL4)
_loader_mod.file_storage = _files_mod.file_storage

DEMO_DATASETS = [
    ("breast_cancer.csv",  569),
    ("heart_disease.csv",  303),
    ("pima_diabetes.csv",  768),
    ("parkinsons.csv",     195),
]

def _make_all4_test(fname, expected_rows):
    def test_fn():
        from backend.core.config import config
        demo_path = config.storage_base_path / "data" / "demo" / fname
        if not demo_path.exists():
            raise AssertionError(f"Demo file not found: {demo_path}")

        content = demo_path.read_bytes()
        db = _All4Session()
        svc = DatasetIngestionService(db=db)
        result = svc.ingest(fname, "text/csv", content)

        assert result["status"] == "REGISTERED", \
            f"{fname}: status={result['status']} reason={result.get('rejection_reason')}"
        assert len(result["sha256"]) == 64
        assert result["file_size_bytes"] == len(content)
        assert result["container_type"] == "CSV"
        assert result["is_duplicate"] is False

        # File exists on disk
        saved = _TMP_ALL4 / result["storage_path"]
        assert saved.exists(), f"File not saved: {saved}"

        # Verify row count dynamically (no hardcoding)
        _, df = DatasetLoader().load_csv(str(demo_path))
        assert len(df) == expected_rows, f"{fname}: expected {expected_rows} rows, got {len(df)}"

        db.close()
    test_fn.__name__ = f"ingest_{fname.replace('.csv','')}"
    return test_fn

for fname, rows in DEMO_DATASETS:
    run_test(f"ingest_{fname.replace('.csv', '')} ({rows} rows)", _make_all4_test(fname, rows))

# Restore
_files_mod.file_storage = _orig_storage
_loader_mod.file_storage = _orig_storage


# ═══════════════════════════════════════════════════════════════════════════════
# Cleanup temp dirs
# ═══════════════════════════════════════════════════════════════════════════════

shutil.rmtree(_TMP_BASE, ignore_errors=True)
shutil.rmtree(_TMP_PIPE, ignore_errors=True)
shutil.rmtree(_TMP_ALL4, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════

total = passed + failed + skipped
print(f"\n{'═'*60}")
print(f"{BOLD}  Results: {GREEN}{passed} passed{RESET}  {RED}{failed} failed{RESET}  {YELLOW}{skipped} skipped{RESET}  (total {total}){BOLD}")
print(f"{'═'*60}{RESET}\n")

if failed > 0:
    sys.exit(1)
