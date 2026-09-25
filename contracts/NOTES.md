# Contract Issues and Ambiguities

This document flags fields that are described inconsistently or ambiguously across the 15 phase documents and MVP implementation plan, requiring team resolution before implementation.

---

## 1. **Target Column Name Ambiguity**

**Issue:** Phase documents don't specify exact target column names for the 4 reference datasets.

**Phase 2 says:** "Candidate target columns might be named: target, label, class, diagnosis, disease, outcome, y"

**Resolution needed:**
- Breast Cancer Wisconsin: Likely `diagnosis` (M/B encoded as 1/0)
- Heart Disease UCI: Likely `target` or `num` (0-4 or binary 0/1)
- Pima Indians Diabetes: Likely `Outcome` (0/1)
- Parkinson's: Likely `status` (0/1)

**Action:** Team must confirm actual column names in datasets before finalizing dataset_profile.json contract.

---

## 2. **Train/Validation/Test Split Ratios**

**Phase 4 mentions:** "70% train, 15% validation, 15% test" OR "80% train, 20% test"

**Phase 10 says:** "Training / Validation / Test" but doesn't mandate specific ratios

**MVP implementation plan says:** "test_size=config.experiment['test_size']" suggesting configurable splits

**Resolution needed:** 
- Is validation set mandatory or optional?
- Are splits fixed at 70/15/15 or configurable?
- Does validation set get used for hyperparameter tuning or only for early stopping?

**Contract impact:** `processed_data_schema.md` shows all three splits, but if validation is optional, contracts need nullable validation arrays.

**Action:** Decide whether validation set is required for all experiments or only certain model types.

---

## 3. **Feature Count After Encoding**

**Phase 4:** "One-hot encoding expands categorical features"

**Phase 2 profile:** Shows "categorical: 1" for Breast Cancer

**Issue:** Profile reports 32 total columns, but after one-hot encoding a categorical with N classes, feature count becomes 31 + N features.

**Example:** If `diagnosis` is target (removed) and one categorical has 3 classes:
- Original: 32 columns
- After removing target: 31
- After one-hot encoding (3 classes): 33 features

**Resolution needed:** Should `dataset_profile.json` report pre-encoding or post-encoding feature counts?

**Action:** Clarify whether "columns" in profile means raw columns or processed features. Update processed_data_schema.md with actual post-encoding counts.

---

## 4. **Quantum Circuit Execution Count Semantics**

**Phase 10:** "Total circuit executions = training steps × batches × parameter evaluations × shots"

**Phase 13:** "Circuit executions during training + inference"

**Ambiguity:** Are `shots` included in the count or separate?

**Example interpretation A:** 
- 1 circuit execution = running circuit 1 time
- If shots=1024, then 1 circuit execution involves 1024 measurements
- Total executions = optimizer steps × forward/backward passes

**Example interpretation B:**
- 1 circuit execution = 1 shot
- Total executions = optimizer steps × shots

**Resolution needed:** Clarify circuit execution count definition for Phase 13 cost analysis.

**Contract impact:** `model_result.json` field `total_circuit_executions` and `shots` need clear relationship documented.

**Action:** Define whether shots are multiplicative or included in execution count. Update quantum_metrics documentation.

---

## 5. **PCA Component Count Selection**

**Phase 6:** "Candidate dimensions: 4, 8, 12, 16" for quantum representation

**Phase 8 config:** "n_components = q_config.get('candidate_dimensions', [8])[0]" suggests 8 is default

**MVP config.yaml:** Shows `candidate_dimensions: [8]` as single value, not list

**Ambiguity:** Should Phase 6 produce multiple candidate representations (QREP-001 with 8 features, QREP-002 with 16 features) or just one?

**Resolution needed:**
- Does Phase 9 planner select best dimension, or does Phase 6 produce all candidates?
- Are multiple quantum representations evaluated per experiment or only one?

**Action:** Clarify representation generation strategy. If multiple candidates, update contracts to handle arrays of representations.

---

## 6. **Imbalance Class Weighting vs Resampling**

**Phase 4:** "Class weighting should be preferred as low-risk baseline"

**Phase 9:** "Planner can decide: class weights, oversampling, undersampling, SMOTE"

**Ambiguity:** Is class weighting mandatory for Phase 4 preprocessing or optional strategy selected by Phase 9?

**Resolution needed:**
- Is `class_weights: balanced` applied automatically in Phase 4 for all imbalanced datasets?
- Or is this a strategy selected per experiment in Phase 9?

**Contract impact:** `processed_data_schema.md` metadata shows `class_weights: balanced`, but if this is experiment-specific, it shouldn't be in preprocessing metadata.

**Action:** Decide if class weighting is preprocessing default or experiment configuration. Update contracts accordingly.

---

## 7. **Calibrated vs Uncalibrated Probabilities**

**Phase 12:** "Raw model score vs calibrated probability must be distinguished"

**Phase 10:** Stores `prediction_scores` in model results

**Ambiguity:** Are `prediction_scores` in model_result.json calibrated or uncalibrated?

**Resolution needed:**
- Does Phase 10 output raw model scores only?
- Does Phase 12 generate calibrated probabilities as separate field?
- Who is responsible for calibration (Phase 10, Phase 11, or Phase 12)?

**Contract impact:** 
- `model_result.json` has `prediction_scores` but doesn't specify calibration status
- `explanation.json` has both `raw_score` and `calibrated_probability` fields

**Action:** Clarify calibration responsibility. Add explicit `is_calibrated` boolean to model_result.json if scores may be calibrated.

---

## 8. **Backend Type Consistency**

**Phase 8:** "LOCAL_SIMULATOR, REMOTE_SIMULATOR, REAL_QUANTUM_HARDWARE"

**Phase 13:** "LOCAL_SIMULATOR, CLOUD_SIMULATOR, HARDWARE"

**Phase 15:** "Local Simulator, Cloud Simulator, Real Hardware"

**Issue:** Inconsistent naming across phases. Are REMOTE_SIMULATOR and CLOUD_SIMULATOR the same?

**Resolution needed:** Standardize backend type enum values.

**Contract impact:** `model_result.json` quantum_metrics.backend_type field

**Recommended fix:** Use `["LOCAL_SIMULATOR", "CLOUD_SIMULATOR", "QUANTUM_HARDWARE"]` consistently across all contracts.

---

## 9. **Experiment ID Prefixes**

**Phase 7:** "EXP-C-000001" for classical

**Phase 8:** "EXP-Q-000001" for quantum

**Phase 9:** "Experiment IDs: EXP-001, EXP-002" (no prefix)

**Phase 10:** "EXP-C-000001, EXP-Q-000001"

**Resolution needed:** Are experiment IDs prefixed with type (C/Q) or sequential?

**Contract impact:** All contracts reference experiment_id but don't specify format.

**Action:** Standardize experiment ID format. Recommended: `EXP-{TYPE}-{SEQUENCE}` where TYPE ∈ {C, Q, H} for Classical, Quantum, Hybrid.

---

## 10. **Resource Monitoring Granularity**

**Phase 10:** "Measure CPU, RAM, GPU during execution"

**Phase 13:** "Track CPU time, RAM, training time, inference time"

**Ambiguity:** Is resource usage tracked as:
- Peak values only?
- Time-series samples during execution?
- Averages?

**Resolution needed:** How are resources measured?

**Contract impact:** `model_result.json` has `memory_peak_mb` (peak) but `training_time_seconds` (total). Is this inconsistent?

**Action:** Define whether resource metrics are peaks, totals, or averages. Add explicit `_peak`, `_total`, or `_avg` suffixes to field names.

---

## 11. **Explainability Method Selection**

**Phase 12:** "Use SHAP for compatible classical models, perturbation for quantum"

**Ambiguity:** 
- What defines "compatible" for SHAP? (Tree-based models only? Linear models?)
- Is perturbation analysis always used for quantum or only as fallback?
- Are multiple explainability methods run per model or just one?

**Resolution needed:** Create decision matrix: which explainability method for which model type?

**Contract impact:** `explanation.json` has `explainability_method` field but doesn't specify selection logic.

**Action:** Document explainability method selection rules in Phase 12 implementation guide.

---

## 12. **Demo Mode vs Benchmark Mode Distinction**

**Phase 15:** "DEMO, DEVELOPMENT, BENCHMARK, HARDWARE execution modes"

**Phase 10:** "Development mode vs benchmark mode"

**Ambiguity:** Are these the same modes or different categories?

**Resolution needed:**
- Is DEMO mode a separate mode or subset of DEVELOPMENT?
- Can DEMO mode use precomputed results? How is this flagged in contracts?

**Contract impact:** Should `model_result.json` have `execution_mode` field? Should results have `is_cached` boolean?

**Action:** Define execution mode taxonomy. Add `execution_mode` enum to experiment configuration contracts.

---

## 13. **Statistical Significance Testing**

**Phase 11:** "Compare repeated runs, calculate confidence intervals, perform statistical tests"

**Ambiguity:** 
- Which statistical tests? (t-test, bootstrap, permutation test?)
- How many repeated runs are required for statistical claims?
- Are confidence intervals computed for all metrics or only primary metrics?

**Resolution needed:** Define statistical testing methodology.

**Contract impact:** `recommendation.json` has `statistical_confidence` section but minimal fields.

**Action:** Specify statistical methods in Phase 11 documentation. Expand `statistical_confidence` contract if needed.

---

## 14. **Quantum Encoding Parameter Ranges**

**Phase 8:** "Features scaled to quantum angle range, e.g., [-π, π] or [0, π]"

**Ambiguity:** Which range is used? Is this configurable or fixed?

**Resolution needed:** Standardize quantum encoding parameter range.

**Contract impact:** This affects feature preprocessing for quantum branch but isn't in any contract.

**Action:** Add `encoding_parameter_range` field to quantum model configuration. Clarify if Phase 4 general scaling is sufficient or if Phase 8 applies additional quantum-specific scaling.

---

## 15. **Quantum vs Hybrid Model Classification**

**Phase 8:** Defines "VQC" as quantum model

**Also Phase 8:** Defines "Quantum Kernel + Classical SVM" as hybrid model

**model_result.json contract:** Uses `model_type` enum with values `["CLASSICAL", "QUANTUM", "HYBRID"]`

**Ambiguity:** Is VQC classified as QUANTUM or HYBRID?

**Resolution needed:** 
- Definition: Pure quantum = entire model runs on quantum hardware/simulator
- Definition: Hybrid = quantum component + classical component
- VQC has classical optimizer → is this HYBRID or still QUANTUM?

**Current interpretation:** VQC = QUANTUM (quantum circuit with classical optimization loop), Quantum Kernel = HYBRID (quantum kernel + classical SVM)

**Action:** Document clear definitions for CLASSICAL/QUANTUM/HYBRID categories. Ensure all models in registry have explicit `model_type` field.

---

## Summary of Required Actions

**High Priority:**
1. ✅ Confirm target column names for 4 reference datasets
2. ✅ Standardize backend type enum values across all phases
3. ✅ Clarify train/validation/test split requirements
4. ✅ Define circuit execution count semantics for cost analysis

**Medium Priority:**
5. ⚠️ Decide class weighting strategy (preprocessing vs experiment config)
6. ⚠️ Clarify calibration responsibility and add fields if needed
7. ⚠️ Standardize experiment ID format with type prefixes
8. ⚠️ Define resource monitoring granularity (peak/total/avg)

**Low Priority:**
9. ⚠️ Expand statistical testing specification in Phase 11
10. ⚠️ Document explainability method selection rules
11. ⚠️ Add execution_mode field to contracts
12. ⚠️ Clarify quantum encoding parameter ranges
13. ⚠️ Update feature count documentation for encoded features
14. ⚠️ Define QUANTUM vs HYBRID model taxonomy
15. ⚠️ Decide PCA candidate generation strategy

**Recommendation:** Resolve High Priority items before starting Phase 4 implementation. Medium Priority items should be resolved before Phase 10. Low Priority items can be clarified during implementation.


---

## STATUS UPDATE (Latest)

**All core contracts now COMPLETE:**

✅ `dataset_upload_response.json` - Phase 1 output  
✅ `dataset_profile.json` - Phase 2 output  
✅ `validation_report.json` - **NEW** Phase 3 output  
✅ `processed_data_schema.md` - Phase 4 output  
✅ `experiment_config.json` - **NEW** Phase 9 output  
✅ `model_result.json` - Phase 10 output  
✅ `experiment_status.json` - Phase 10 real-time status  
✅ `recommendation.json` - Phase 11 benchmark output  
✅ `explanation.json` - Phase 12 explainability output  
✅ `cost_report.json` - **NEW** Phase 13 cost/scalability report  

**Remaining optional contracts:**
- `feature_engineering_result.json` (Phase 5 → Phase 6) - optional intermediate artifact
- `representation_metadata.json` (Phase 6 → Phase 9/10) - optional detailed feature info
- `quantum_backend_config.json` (Phase 8 → Phase 10) - optional backend-specific settings

**Three contracts added in this session:**

1. **validation_report.json** (Phase 3 → Phase 4)
   - Quality assessment, missing values, duplicates, class balance, leakage detection
   - Distinguishes PASS / PASS_WITH_WARNINGS / BLOCKED
   - Phase 3 detects problems, Phase 4 fixes them

2. **experiment_config.json** (Phase 9 → Phase 10)
   - Complete immutable experiment configuration
   - Includes dataset, representation, model, backend, evaluation protocol, budget, reproducibility
   - decision_trace provides explainable experiment selection
   - comparison_group enables fair quantum vs classical benchmarking
   - Supports READY, DEFERRED, REJECTED statuses

3. **cost_report.json** (Phase 13 → Reports/Frontend)
   - Computational cost (CPU, RAM, training time, inference time)
   - Quantum cost (qubits, circuit depth, gate count, shots, circuit executions)
   - Scalability analysis (dataset size, features, circuit depth, shots scaling)
   - Performance vs cost Pareto frontier
   - Honest classical vs quantum comparison (classical may be superior)
   - deployment_recommendation (may say "use classical")

**Key insights from contract generation:**
- Feature reduction (Phase 6) is NOT optional - it makes quantum branch computationally feasible
- Platform must honestly report when classical outperforms quantum
- Backend abstraction allows same experiment_config to target local_sim/cloud_sim/hardware
- decision_trace in experiment_config provides auditable scientific reproducibility
- Phase 13 feedback loop to Phase 9 improves future resource estimates
