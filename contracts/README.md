# Contract Specifications for Hybrid QML Disease Detection Platform

This directory contains frozen JSON/Markdown contracts defining exact input/output shapes for every phase-to-phase and person-to-person handoff in the project.

## Status: ALL CORE CONTRACTS COMPLETE ✅

**10 contracts fully specified:**
- 4 core data contracts (Phase 1-4)
- 3 experiment/execution contracts (Phase 9-10)
- 3 analysis/output contracts (Phase 11-13)

**Ready for parallel development:** Frontend, backend, ML engineers can now build against stable interfaces.

## Purpose

These contracts enable:
- **Team coordination:** Frontend, backend, ML engineers work in parallel using agreed interfaces
- **Mock data generation:** Developers can build UI/tests without waiting for backend completion
- **API stability:** Changes require explicit contract updates, preventing breakage
- **Type safety:** Clear field types, enums, and constraints reduce integration bugs
- **Documentation:** Contracts serve as authoritative interface documentation

## Contract Files

### Core Data Contracts

| File | Producer | Consumers | Description |
|------|----------|-----------|-------------|
| `dataset_upload_response.json` ✅ | Phase 1 Ingestion | Phase 2 Profiler, Frontend, Experiment Manager | Dataset registration result after upload |
| `dataset_profile.json` ✅ | Phase 2 Profiler | Phase 3 Validator, Phase 4 Preprocessing, Phase 9 Planner | Complete dataset understanding including modality, target, features, statistics |
| `validation_report.json` ✅ | Phase 3 Validator | Phase 4 Preprocessing, Phase 9 Planner, Frontend | Dataset quality assessment with warnings/blockers |
| `processed_data_schema.md` ✅ | Phase 4 Preprocessing | Phase 5/6/7/8 Model Training | NumPy array shapes for train/validation/test splits |

### Experiment & Execution Contracts

| File | Producer | Consumers | Description |
|------|----------|-----------|-------------|
| `experiment_config.json` ✅ | Phase 9 Planner | Phase 10 Executor | Complete immutable experiment configuration |
| `experiment_status.json` ✅ | Phase 10 Executor (streaming) | Frontend Progress UI, Job Scheduler | Real-time execution status updates |
| `model_result.json` ✅ | Phase 10 Executor | Phase 11 Benchmark, Phase 12 Explainability, Phase 13 Cost | Unified result schema for classical/quantum models |

### Analysis & Output Contracts

| File | Producer | Consumers | Description |
|------|----------|-----------|-------------|
| `recommendation.json` ✅ | Phase 11 Benchmark | Frontend Summary, Phase 15 Report | Final quantum-vs-classical comparison and recommendation |
| `explanation.json` ✅ | Phase 12 Explainability | Frontend Explanation UI, Audit Logs | Prediction explanation with feature importance and pipeline trace |
| `cost_report.json` ✅ | Phase 13 Cost Analysis | Frontend Cost Dashboard, Phase 15 Report | Resource usage and scalability analysis |

## Reference Datasets

All contracts include realistic populated examples from these 4 reference datasets:

### 1. Breast Cancer Wisconsin Diagnostic
- **Samples:** 569 (357 benign, 212 malignant)
- **Features:** 30 numerical features (mean, SE, worst values for 10 measurements)
- **Target:** `diagnosis` (M/B → 1/0)
- **Use case:** Binary classification, moderate imbalance (62.7% / 37.3%)

### 2. Heart Disease UCI
- **Samples:** 303 (138 no disease, 165 disease)
- **Features:** 13 mixed (age, sex, chest pain type, blood pressure, cholesterol, etc.)
- **Target:** `target` (0/1)
- **Use case:** Binary classification, near-balanced classes (45.5% / 54.5%)

### 3. Pima Indians Diabetes
- **Samples:** 768 (500 no diabetes, 268 diabetes)
- **Features:** 8 numerical (pregnancies, glucose, blood pressure, BMI, etc.)
- **Target:** `Outcome` (0/1)
- **Use case:** Binary classification, significant imbalance (65.1% / 34.9%)

### 4. Parkinson's Disease (UCI)
- **Samples:** 195 (48 healthy, 147 Parkinson's)
- **Features:** 22 numerical voice measurements
- **Target:** `status` (0/1)
- **Use case:** Binary classification, severe imbalance (24.6% / 75.4%)

## Field Naming Conventions

### Required Fields
- Every contract has `_comment` and `_description` explaining producer/consumer
- Primary keys end with `_id` (e.g., `dataset_id`, `experiment_id`)
- Timestamps use ISO 8601 format with `_at` suffix (e.g., `uploaded_at`, `completed_at`)
- Boolean flags use `is_` prefix (e.g., `is_duplicate`, `is_calibrated`)

### Type Annotations
- `_type`: JSON type or specialized type (e.g., "float [0-1]", "ISO 8601 datetime")
- `_example`: Single example value
- `_example_{dataset}`: Dataset-specific example (e.g., `_example_breast_cancer`)
- `_values`: Enum possible values
- `_nullable_for_X`: Field only present for certain model types

### Metric Naming
- Rates/percentages: `[0-1]` float (e.g., `0.953` = 95.3%)
- Times: `_seconds` or `_milliseconds` suffix
- Sizes: `_bytes`, `_mb`, `_gb` suffix
- Counts: plain integer (e.g., `qubits`, `samples`, `circuit_executions`)

## Data Flow Visualization

```
┌─────────────┐
│   Phase 1   │  dataset_upload_response.json
│  Ingestion  │────────────────────────────────┐
└─────────────┘                                │
                                               ▼
┌─────────────┐                        ┌─────────────┐
│   Phase 2   │  dataset_profile.json  │             │
│  Profiling  │───────────────────────▶│  Frontend   │
└─────────────┘                        │  Dashboard  │
       │                               │             │
       ▼                               └─────────────┘
┌─────────────┐  validation_report.json
│   Phase 3   │────────────────────────────────────┐
│ Validation  │                                    │
└─────────────┘                                    │
       │                                           │
       ▼                                           ▼
┌─────────────┐  processed_data_schema.md   ┌─────────────┐
│   Phase 4   │─────────────────────────────▶│  Phase 5-8  │
│Preprocessing│                              │   Models    │
└─────────────┘                              └─────────────┘
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │   Phase 9   │
                                             │   Planner   │
                                             └─────────────┘
                                                    │
                                                    ▼
                                      experiment_config.json
                                                    │
                                                    ▼
┌─────────────┐  experiment_status.json     ┌─────────────┐
│  Frontend   │◀────────────────────────────│  Phase 10   │
│  Progress   │   (streaming updates)       │  Executor   │
└─────────────┘                             └─────────────┘
                                                    │
                                                    ▼
                                            model_result.json
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                             ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                             │  Phase 11   │ │  Phase 12   │ │  Phase 13   │
                             │ Benchmark   │ │Explainability│ │Cost Analysis│
                             └─────────────┘ └─────────────┘ └─────────────┘
                                    │               │               │
                                    ▼               ▼               ▼
                          recommendation.json  explanation.json  cost_report.json
                                    │               │               │
                                    └───────────────┼───────────────┘
                                                    ▼
                                           ┌─────────────┐
                                           │  Phase 15   │
                                           │Final Report │
                                           └─────────────┘
```

## Usage Examples

### Frontend Mock Data
```typescript
// Use contracts to generate TypeScript interfaces
interface DatasetUploadResponse {
  dataset_id: string;
  display_id: string;
  status: 'REGISTERED' | 'REJECTED' | 'INVALID_FORMAT';
  filename: string;
  // ... see dataset_upload_response.json
}

// Mock for development
const mockResponse: DatasetUploadResponse = {
  dataset_id: "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  display_id: "DS-000001",
  status: "REGISTERED",
  filename: "breast_cancer.csv",
  // ... use example values from contract
};
```

### Backend Validation
```python
# Use contracts to validate API responses
from jsonschema import validate

def validate_model_result(result: dict):
    # Load schema from model_result.json contract
    with open('contracts/model_result.json') as f:
        schema = json.load(f)
    
    # Validate structure
    validate(instance=result, schema=schema)
```

### Testing
```python
# Use contract examples as test fixtures
def test_phase11_benchmark():
    # Load example from recommendation.json
    with open('contracts/recommendation.json') as f:
        contract = json.load(f)
        example = contract['_example_breast_cancer']
    
    result = benchmark_engine.compare(
        classical_result=example['classical_best'],
        quantum_result=example['quantum_best']
    )
    
    assert result['classification'] in ['QUANTUM_ADVANTAGE', 'PERFORMANCE_PARITY', 'TRADEOFF', 'CLASSICAL_ADVANTAGE']
```

## Known Issues & Ambiguities

See `NOTES.md` for 15 documented ambiguities requiring team resolution, including:

**High Priority:**
- Target column name confirmation for reference datasets
- Train/validation/test split ratio standardization
- Backend type enum value consistency
- Circuit execution count semantics for cost analysis

**Action Required:** Review NOTES.md and resolve issues before Phase 4 implementation begins.

## Contract Update Process

### Adding New Fields
1. Update relevant contract file with new field definition
2. Add `_description`, `_type`, and `_example` annotations
3. Update this README if new contract file added
4. Increment contract version if breaking change
5. Notify all teams consuming the contract

### Breaking Changes
Breaking changes require:
- Major version increment (e.g., v1 → v2)
- Deprecation notice in previous version
- Migration guide for consumers
- Team approval in architecture review

### Non-Breaking Changes
- Adding optional fields (with default values)
- Adding new enum values (if code handles unknown values gracefully)
- Documentation improvements
- Example value updates

## Validation

All contracts should be validated before Phase 10 execution begins:

```bash
# Validate JSON structure
python scripts/validate_contracts.py

# Check for missing required fields
python scripts/check_contract_completeness.py

# Verify example values match schemas
python scripts/verify_examples.py
```

## Version

**Contract Version:** v1.0  
**Last Updated:** 2026-09-10  
**Status:** DRAFT - Awaiting team review and NOTES.md issue resolution

## Questions or Issues?

- For contract clarifications: See NOTES.md or contact architecture team
- For missing contracts: Check if handoff is internal to single phase (may not need external contract)
- For field ambiguities: Flag in NOTES.md for team discussion
