1# Phase 1 — Dataset Ingestion & Registration

## 1. Phase Overview

### Phase Name

**Phase 1 — Dataset Ingestion & Registration**

### Purpose

Phase 1 is the **entry point of the entire Hybrid Quantum-Classical Disease Detection Platform**.

Its responsibility is deliberately limited:

> **Receive a biomedical dataset/package, verify that it is an acceptable and safe input, preserve the original data, generate a unique dataset identity, and register it for subsequent processing.**

Phase 1 **does not attempt to understand the ML problem**.

It does not decide whether the dataset is:

* tabular
* image
* multimodal
* classification
* regression
* cancer detection
* cardiovascular detection
* etc.

Those decisions belong to **Phase 2 — Dataset Profiling & Discovery**.

---

# 2. Position in the Overall System

```text
                    USER
                     |
                     v
       ┌────────────────────────────┐
       │ PHASE 1                    │
       │ Dataset Ingestion          │
       │ & Registration             │
       └─────────────┬──────────────┘
                     |
                     v
       ┌────────────────────────────┐
       │ PHASE 2                    │
       │ Dataset Profiling          │
       │ & Discovery                │
       └─────────────┬──────────────┘
                     |
                     v
       ┌────────────────────────────┐
       │ PHASE 3                    │
       │ Dataset Validation          │
       └─────────────┬──────────────┘
                     |
                     v
                  ...
```

Phase 1 creates the **clean input contract** for Phase 2.

---

# 3. Core Principle

The most important architectural rule for Phase 1 is:

> **Never modify the user's original dataset.**

The original uploaded file/package becomes an immutable source artifact.

All future processing creates derived versions.

```text
Original Dataset
      |
      +----> Profile
      |
      +----> Validation
      |
      +----> Preprocessed Version
      |
      +----> Feature-Selected Version
      |
      +----> Experiment Versions
```

This gives us:

* reproducibility
* traceability
* experiment comparison
* rollback
* debugging
* protection against accidental data modification

---

# 4. Supported Input Types

## Initial implementation

Phase 1 should support:

```text
CSV
XLSX
ZIP
```

These are sufficient for the first platform version.

---

## Future formats

Depending on the final biomedical problem, support can later be expanded to:

```text
PNG
JPG / JPEG
TIFF
DICOM
Parquet
other biomedical formats
```

These should not be implemented merely for the sake of having many formats.

The final supported formats should be driven by the selected disease/dataset modality.

---

# 5. Why ZIP Must Be Supported

ZIP is particularly important for biomedical imaging datasets.

For example:

```text
skin_cancer_dataset.zip
```

could contain:

```text
skin_cancer_dataset/
│
├── images/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   ├── image_003.jpg
│   └── ...
│
├── labels.csv
│
└── metadata.csv
```

Uploading thousands of images individually would be impractical.

Therefore:

> **ZIP is treated as a dataset package/container rather than as the actual ML modality.**

This distinction is important.

---

# 6. Two Different Meanings of "Type"

The system needs to distinguish between **file/container type** and **dataset/ML type**.

## Phase 1 — Container Type

Example:

```text
CSV
ZIP
XLSX
```

This answers:

> **What did the user upload?**

---

## Phase 2 — Dataset Type

Example:

```text
TABULAR
IMAGE
MULTIMODAL
```

This answers:

> **What kind of dataset is actually inside the uploaded package?**

---

## Example

User uploads:

```text
skin_cancer.zip
```

### Phase 1

```text
container_type = ZIP
```

### Phase 2

After inspecting the contents:

```text
dataset_modality = IMAGE
task = BINARY_CLASSIFICATION
```

Phase 1 must **not duplicate Phase 2's responsibility**.

---

# 7. Phase 1 Input Contract

The frontend provides:

```text
Dataset file/package
```

Example:

```text
heart_disease.csv
```

or:

```text
heart_dataset.zip
```

or:

```text
skin_cancer.zip
```

The backend receives the file through:

```http
POST /api/v1/datasets
```

---

# 8. Phase 1 High-Level Flow

```text
                    USER
                     |
                     | Upload
                     v
          ┌──────────────────────┐
          │ File Receiver        │
          └──────────┬───────────┘
                     |
                     v
          ┌──────────────────────┐
          │ Format Validator     │
          └──────────┬───────────┘
                     |
                     v
          ┌──────────────────────┐
          │ Security Validator   │
          └──────────┬───────────┘
                     |
                     v
          ┌──────────────────────┐
          │ Hash Generator       │
          └──────────┬───────────┘
                     |
                     v
          ┌──────────────────────┐
          │ Dataset ID Generator │
          └──────────┬───────────┘
                     |
                     v
          ┌──────────────────────┐
          │ Raw Dataset Storage  │
          └──────────┬───────────┘
                     |
                     v
          ┌──────────────────────┐
          │ Dataset Registry     │
          └──────────┬───────────┘
                     |
                     v
               REGISTERED
```

---

# 9. Module 1 — File Receiver

## Responsibility

Receive the uploaded file/package from the frontend.

## Input

```text
multipart/form-data
```

Example:

```text
file = heart_disease.csv
```

## Work

1. Receive request.
2. Create temporary upload location.
3. Stream/write uploaded file.
4. Record basic upload metadata.
5. Pass the file to the validator.

## Output

```text
Temporary uploaded artifact
```

Example:

```text
/tmp/upload_8af91c
```

The temporary path is internal and should not become the permanent dataset identity.

---

# 10. Module 2 — Format Validator

## Responsibility

Determine whether the uploaded file/package is an allowed **input container**.

## Input

```text
Temporary uploaded artifact
```

## Work

Check:

* extension
* detected MIME/file signature where appropriate
* supported format
* file size
* basic readability

## Example

```text
heart.csv
```

Result:

```text
SUPPORTED
```

Another:

```text
dataset.zip
```

Result:

```text
SUPPORTED
```

Another:

```text
malware.exe
```

Result:

```text
REJECTED
```

---

# 11. Do Not Trust File Extensions Alone

A user could rename:

```text
malware.exe
```

to:

```text
dataset.csv
```

Therefore the system should not rely only on:

```text
filename.endswith(".csv")
```

It should use appropriate file-signature/content validation where practical.

---

# 12. Format Validation Output

Example:

```json
{
  "format": "csv",
  "supported": true,
  "status": "VALID_FORMAT"
}
```

For ZIP:

```json
{
  "format": "zip",
  "supported": true,
  "status": "VALID_FORMAT"
}
```

---

# 13. Module 3 — ZIP Package Security Validation

This module is only activated for ZIP inputs.

## Responsibility

Determine whether the archive can safely enter the platform.

It should check:

### 1. Archive validity

Can the ZIP actually be opened?

### 2. Entry count

Example:

```text
12,421 files
```

### 3. Compressed size

Example:

```text
1.8 GB
```

### 4. Estimated extracted size

Example:

```text
2.4 GB
```

### 5. Path safety

Reject suspicious paths such as:

```text
../../file
```

### 6. Resource limits

Prevent extremely large or malicious archives from exhausting system resources.

---

# 14. ZIP Should NOT Be Fully Processed in Phase 1

Phase 1 can inspect archive metadata.

It should **not** perform deep dataset discovery.

For example, it can determine:

```text
ZIP valid
10,421 entries
estimated size = 2.4 GB
```

But it should not conclude:

```text
10,000 images
labels.csv
task = classification
```

That belongs to Phase 2.

---

# 15. ZIP Validation Output

Example:

```json
{
  "archive_valid": true,
  "entry_count": 10421,
  "compressed_size_bytes": 1932735283,
  "estimated_uncompressed_size_bytes": 2576348921,
  "security_status": "SAFE_FOR_REGISTRATION"
}
```

---

# 16. Module 4 — File Hashing

## Responsibility

Create a cryptographic identity for the uploaded source.

Recommended:

```text
SHA-256
```

Example:

```text
sha256 =
8b7c4a9e........
```

---

# 17. Why Hashing Matters

Suppose today:

```text
heart_disease.csv
```

is uploaded.

Tomorrow the user uploads another file with the same name:

```text
heart_disease.csv
```

The filename is identical, but the contents may differ.

The hash lets us detect that.

```text
Dataset A
SHA256 = ABC123

Dataset B
SHA256 = XYZ789
```

Therefore:

```text
different source versions
```

---

# 18. Duplicate Detection

The system can check:

```text
Does this SHA-256 already exist?
```

### If yes

We can report:

```text
IDENTICAL DATASET ALREADY REGISTERED
```

But we should **not necessarily reject it**.

The user may intentionally want to create another project/experiment using the same dataset.

Therefore:

```text
duplicate ≠ invalid
```

It is metadata.

---

# 19. Module 5 — Dataset ID Generation

Every accepted upload receives a unique internal ID.

Example:

```text
DS_20260825_000001
```

Or UUID:

```text
550e8400-e29b-41d4-a716-446655440000
```

I recommend using a UUID internally and optionally displaying a human-readable ID.

Example:

```text
Internal ID:
550e8400-e29b-41d4-a716-446655440000

Display ID:
DS-000001
```

---

# 20. Why Dataset ID Is Important

Every future object refers to the dataset through this ID.

```text
Dataset
   |
   +---- Profile
   |
   +---- Validation
   |
   +---- Preprocessing
   |
   +---- Feature Set
   |
   +---- Experiment
   |
   +---- Model Run
   |
   +---- Report
```

This creates lineage.

---

# 21. Module 6 — Raw Dataset Storage

The original dataset must be stored unchanged.

Example structure:

```text
storage/
│
└── datasets/
    │
    └── DS-000001/
        │
        └── raw/
            │
            └── original.csv
```

For ZIP:

```text
storage/
│
└── datasets/
    │
    └── DS-000002/
        │
        └── raw/
            │
            └── original.zip
```

---

# 22. Storage Rule

### Never do this:

```text
original.csv
 ↓
cleaned.csv
 ↓
overwrite original.csv
```

Instead:

```text
raw/
    original.csv

processed/
    version_001/
        processed.csv
```

Later:

```text
features/
    version_001/
        selected_features.parquet
```

This gives us reproducibility.

---

# 23. Local Storage vs Future Cloud Storage

Currently we are developing locally.

That's okay.

But the application should not have code like:

```python
save_to_C_drive()
```

throughout the project.

Instead define a storage abstraction:

```text
StorageBackend
      |
      +── LocalStorage
      |
      +── S3Storage
      |
      +── MinIOStorage
```

Today:

```text
StorageBackend
      ↓
LocalStorage
```

Later:

```text
StorageBackend
      ↓
S3 / MinIO / Cloud
```

The rest of the application doesn't need to know.

---

# 24. Module 7 — Dataset Registry

After successful ingestion, metadata is stored in the database.

Suggested table:

```text
datasets
------------------------------------------------
id
display_id
original_filename
container_type
file_size_bytes
sha256
raw_storage_path
upload_timestamp
status
created_by
```

---

# 25. Example Database Record

For:

```text
heart_disease.csv
```

we could have:

```text
id:
550e8400-e29b-41d4-a716-446655440000

display_id:
DS-000001

original_filename:
heart_disease.csv

container_type:
CSV

file_size_bytes:
2512487

sha256:
8b7c....

raw_storage_path:
datasets/DS-000001/raw/original.csv

status:
REGISTERED
```

Notice what is **not** there:

```text
task
modality
target
feature count
class balance
```

Those belong to Phase 2.

---

# 26. Dataset Status Lifecycle

Phase 1 should introduce a controlled status.

```text
RECEIVING
    ↓
VALIDATING
    ↓
REGISTERING
    ↓
REGISTERED
```

Failure:

```text
RECEIVING
    ↓
VALIDATING
    ↓
REJECTED
```

Later phases will extend the lifecycle:

```text
REGISTERED
    ↓
PROFILING
    ↓
PROFILED
    ↓
VALIDATING
    ↓
VALIDATED
```

---

# 27. Error States

We should explicitly define them.

## Unsupported format

```text
UNSUPPORTED_FORMAT
```

Example:

```text
.exe
```

---

## Invalid file

```text
INVALID_FILE
```

Example:

```text
corrupted.csv
```

---

## Invalid ZIP

```text
INVALID_ARCHIVE
```

---

## Unsafe ZIP

```text
UNSAFE_ARCHIVE
```

---

## Size exceeded

```text
SIZE_LIMIT_EXCEEDED
```

---

## Storage failure

```text
STORAGE_ERROR
```

---

## Registration failure

```text
REGISTRATION_ERROR
```

---

# 28. API Design

## Upload

```http
POST /api/v1/datasets
```

### Request

```text
multipart/form-data

file = <dataset>
```

### Success response

```json
{
  "dataset_id": "550e8400-e29b-41d4-a716-446655440000",
  "display_id": "DS-000001",
  "status": "REGISTERED",
  "filename": "heart_disease.csv",
  "container_type": "CSV"
}
```

---

# 29. Get Dataset

```http
GET /api/v1/datasets/{dataset_id}
```

Response:

```json
{
  "dataset_id": "550e8400-e29b-41d4-a716-446655440000",
  "display_id": "DS-000001",
  "filename": "heart_disease.csv",
  "container_type": "CSV",
  "size_bytes": 2512487,
  "sha256": "8b7c...",
  "status": "REGISTERED"
}
```

---

# 30. List Datasets

```http
GET /api/v1/datasets
```

This allows the UI to show:

```text
My Datasets

DS-000001
heart_disease.csv
CSV
Registered
25 Aug 2026

DS-000002
skin_cancer.zip
ZIP
Registered
25 Aug 2026
```

---

# 31. Frontend Flow

## Initial state

```text
┌─────────────────────────────────────┐
│       CREATE EXPERIMENT              │
│                                     │
│  Upload Dataset                     │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ Drag & Drop Dataset            │  │
│  │                               │  │
│  │ CSV / XLSX / ZIP              │  │
│  │                               │  │
│  │         Browse Files          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

# 32. Uploading

Show:

```text
Uploading...

██████████████████░░░░ 78%
```

Then:

```text
Validating...

✓ File format
✓ File integrity
✓ Security checks
✓ Hash generated
✓ Dataset registered
```

---

# 33. After Registration

Show:

```text
┌─────────────────────────────────────┐
│ Dataset Registered ✓                 │
│                                     │
│ Name: heart_disease.csv             │
│ ID: DS-000001                       │
│ Type: CSV                           │
│ Size: 2.4 MB                        │
│                                     │
│ Status: REGISTERED                  │
│                                     │
│        [ Profile Dataset → ]        │
└─────────────────────────────────────┘
```

The **Profile Dataset** button starts Phase 2.

---

# 34. Phase 1 Internal Architecture

```text
backend/
│
├── api/
│   └── datasets.py
│
├── ingestion/
│   ├── receiver.py
│   ├── format_validator.py
│   ├── archive_validator.py
│   ├── hasher.py
│   ├── id_generator.py
│   └── ingestion_service.py
│
├── storage/
│   ├── interface.py
│   └── local_storage.py
│
├── database/
│   ├── models.py
│   └── repositories.py
│
└── core/
    └── config.py
```

---

# 35. Main Service

The overall Phase 1 service should conceptually perform:

```text
DatasetIngestionService
        |
        +── receive()
        |
        +── validate_format()
        |
        +── validate_security()
        |
        +── calculate_hash()
        |
        +── generate_id()
        |
        +── store_raw()
        |
        +── register()
        |
        └── return_registration()
```

---

# 36. Important Separation

Don't create one huge function:

```python
upload_dataset()
```

that does 1,000 things.

Instead:

```text
Receiver
   ↓
Validator
   ↓
Security
   ↓
Hasher
   ↓
Storage
   ↓
Registry
```

This makes testing and future changes much easier.

---

# 37. Configuration

Phase 1 should have configuration such as:

```yaml
storage:
  backend: local
  base_path: ./storage

upload:
  max_file_size_mb: 2048

archive:
  max_entries: 100000
  max_uncompressed_size_gb: 10

supported_formats:
  - csv
  - xlsx
  - zip
```

Exact limits should be finalized based on our deployment environment.

---

# 38. Environment Awareness

The system can expose:

```yaml
environment:
  mode: development
```

and:

```yaml
storage:
  backend: local
```

But **business logic must not depend on "local".**

The code should depend on:

```text
StorageBackend
```

not:

```text
LocalStorage
```

directly.

---

# 39. Logging

Every ingestion should generate structured logs.

Example:

```text
INFO  Dataset upload started
INFO  Format validation passed
INFO  Archive validation passed
INFO  SHA256 generated
INFO  Dataset ID generated
INFO  Raw dataset stored
INFO  Dataset registered
INFO  Dataset ingestion completed
```

If something fails:

```text
ERROR Dataset ingestion failed
ERROR Reason: UNSAFE_ARCHIVE
```

Never log sensitive biomedical data itself.

---

# 40. Security Considerations

Because this is a biomedical platform, Phase 1 should be conservative.

We should eventually consider:

* file size limits
* archive extraction limits
* path traversal protection
* malicious file detection
* access control
* dataset ownership
* encryption at rest
* encryption in transit
* audit logging
* deletion lifecycle

For the SIH prototype, implement the practical subset first.

---

# 41. Privacy Consideration

Phase 1 should not assume uploaded data is safe to expose.

The system should eventually support:

```text
Dataset ownership
       ↓
Project access
       ↓
Authorized users
```

For the SIH prototype, we can work primarily with public/benchmark datasets, but the architecture should not make privacy impossible later.

---

# 42. Testing Plan

Before declaring Phase 1 complete, we need tests for:

### Valid CSV

```text
heart.csv
→ REGISTERED
```

### Valid XLSX

```text
heart.xlsx
→ REGISTERED
```

### Valid ZIP

```text
skin_dataset.zip
→ REGISTERED
```

### Corrupted ZIP

```text
broken.zip
→ INVALID_ARCHIVE
```

### Unsupported format

```text
program.exe
→ UNSUPPORTED_FORMAT
```

### Oversized file

```text
huge.zip
→ SIZE_LIMIT_EXCEEDED
```

### Unsafe archive

```text
malicious.zip
→ UNSAFE_ARCHIVE
```

### Duplicate content

```text
same dataset
→ detected as duplicate
```

but not necessarily rejected.

---

# 43. Phase 1 Acceptance Criteria

Phase 1 is complete only when all of these work.

## Input

* [ ] CSV accepted
* [ ] XLSX accepted
* [ ] ZIP accepted

## Validation

* [ ] File format validated
* [ ] Invalid files rejected
* [ ] ZIP integrity checked
* [ ] ZIP path safety checked
* [ ] ZIP resource limits checked

## Identity

* [ ] SHA-256 generated
* [ ] Dataset ID generated
* [ ] Duplicate detection implemented

## Storage

* [ ] Original file preserved
* [ ] Original file not modified
* [ ] Local storage abstraction implemented

## Database

* [ ] Dataset metadata registered
* [ ] Dataset status stored
* [ ] Dataset retrievable by ID

## API

* [ ] Upload endpoint
* [ ] Get dataset endpoint
* [ ] List dataset endpoint

## Frontend

* [ ] Upload UI
* [ ] Progress state
* [ ] Validation state
* [ ] Registration result
* [ ] Dataset ID displayed
* [ ] "Profile Dataset" action

---

# 44. Phase 1 Final Input → Output Contract

## INPUT

```text
User
  ↓
CSV / XLSX / ZIP
```

---

## PROCESS

```text
Receive
   ↓
Format validation
   ↓
Security validation
   ↓
Hash
   ↓
Generate identity
   ↓
Store immutable original
   ↓
Register metadata
```

---

## OUTPUT

```json
{
  "dataset_id": "UUID",
  "display_id": "DS-000001",
  "filename": "heart_disease.csv",
  "container_type": "CSV",
  "sha256": "...",
  "storage_reference": "...",
  "status": "REGISTERED"
}
```

---

# 45. What Phase 1 Explicitly Does NOT Output

It should **not** output:

```text
dataset_modality
task
target
feature_count
class_distribution
missing_value_analysis
recommended_model
quantum_qubit_count
preprocessing strategy
```

Those belong to later phases.

---

# 46. Handoff to Phase 2

The only thing Phase 2 really needs from Phase 1 is:

```text
dataset_id
```

For example:

```text
DS-000001
```

Phase 2 can then retrieve:

```text
DS-000001
      ↓
raw/original.csv
```

and begin:

> **Dataset Profiling & Discovery**

---

# 47. Phase 1 in One Diagram

```text
                         PHASE 1
               DATASET INGESTION & REGISTRATION

                            USER
                             |
                             v
                   Upload CSV/XLSX/ZIP
                             |
                             v
                  ┌──────────────────┐
                  │ File Receiver    │
                  └────────┬─────────┘
                           |
                           v
                  ┌──────────────────┐
                  │ Format Validator │
                  └────────┬─────────┘
                           |
                    ┌──────┴──────┐
                    │             │
                  ZIP?           Other
                    │             │
                    v             │
            ┌──────────────┐      │
            │ ZIP Security │      │
            │ Validation   │      │
            └──────┬───────┘      │
                   │              │
                   └──────┬───────┘
                          v
                   ┌────────────┐
                   │ SHA-256    │
                   └─────┬──────┘
                         |
                         v
                   ┌────────────┐
                   │ Dataset ID │
                   └─────┬──────┘
                         |
                         v
                ┌─────────────────┐
                │ Immutable Raw   │
                │ Storage         │
                └────────┬────────┘
                         |
                         v
                ┌─────────────────┐
                │ Dataset Registry│
                └────────┬────────┘
                         |
                         v
                   REGISTERED
                         |
                         v
                       PHASE 2
```

---

# 48. Final Phase 1 Definition

> **Phase 1 is the controlled entry gate of the platform. It accepts a dataset package, verifies its basic validity and safety, creates a reproducible identity, preserves the original source, and registers it without making any ML-related assumptions.**

The key boundary is:

```text
                 PHASE 1
             "WHAT DID YOU GIVE ME?"
                       ↓
                 PHASE 2
             "WHAT IS IT ACTUALLY?"
```

That boundary should stay strict. It will prevent the later pipeline from becoming one giant module where ingestion, profiling, preprocessing, model selection, and QML decisions are mixed together.
