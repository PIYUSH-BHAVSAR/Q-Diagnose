# Naeem — Guide × Mocks × Contracts × Real Backend (data-layer spec)
**Companion to:** `FRONTEND_TASKS.md` (page/component gap list)
**Yeh file sirf ek sawaal ka jawab hai:** *guide jo JSON dikha rahi hai, mocks wahi JSON hain kya, aur backend actually kya bhejta hai — to React me kaunsa shape code karoon?*

Sources verified in this pass (27 Sep 2026, `main` = `c264169`):
- `guide_naeem.md` (1813 lines) — §4a–§4j contracts, §6 Hour 1→Day 2 build order, §8 DoD
- `mocks/{breast_cancer,heart_disease,parkinsons,diabetes}/` — 11 files × 4 datasets = 44 JSON
- `contracts/*.json` — 10 contract definitions (v1.0–v1.1)
- `mvp/backend/api/{datasets,experiments,results,reports}.py` + `mvp/backend/experiments/manager.py` + `mvp/data/{loader,profiler}.py` + real run output `mvp/experiment_results_EXP-279AE34B.json`

---

## PART A — Guide §6 ka poora kaam vs repo me aaj kya hai

Guide §6 hour-by-hour **16 files** banane ko kehti hai. Repo me status:

| Guide step | File (guide §3/§6 path) | Repo me status | Kya bacha hai |
|---|---|---|---|
| Hour 1 | `src/services/api.js` + `MOCK_MODE` | ⚠️ **PARTIAL** — file hai (116 lines) par `MOCK_MODE` kahin nahi, `BASE_URL='http://localhost:8000'` hardcode nahi (vite proxy `/api` use ho raha hai — **ye better hai, wahi rakho**) | mock imports + `MOCK_MODE` flag + 4 missing endpoints (D-section me list) |
| Hour 2 | `src/main.jsx` | ✅ exists | — |
| Hour 2 | `src/App.jsx` (layout shell + nav) | ✅ exists, 6 routes | ❌ `/reports` route nahi, ❌ `Cpu` import unused |
| Hour 2–3 | `src/components/StageProgress.jsx` | ❌ **MISSING** (folder hi nahi) | poora banana hai — `STAGES` keys contract wale stage names pe |
| Hour 2–3 | `src/components/MetricsTable.jsx` | ❌ MISSING | guide 6 metrics dikhata hai, `precision` chhootta hai — 7 rakho |
| Hour 2–3 | `src/components/FeatureImportanceBar.jsx` | ❌ MISSING | mock/contract me array hai, backend me dict |
| Hour 2–3 | `src/components/ClassDistributionChart.jsx` | ❌ MISSING | |
| Hour 2–3 | `src/components/MetricsBadge.jsx` | ❌ MISSING | |
| Hour 2–3 | `src/components/FileDropzone.jsx` | ❌ MISSING | logic aaj `DatasetUpload.jsx:82-124` me inline hai → nikaalo |
| Hour 2–3 | `src/components/Disclaimer.jsx` | ❌ MISSING | text aaj `Dashboard.jsx:245-268` me hardcoded |
| Hour 3–5 | `src/pages/Dashboard.jsx` | ✅ exists (273 L) | health badge ❌, demo buttons = `window.alert` (`:189,197,205`) ❌ |
| Hour 3–5 | `src/pages/Datasets.jsx` (list + dropzone) | ❌ **MISSING** | route `/datasets` → `DatasetUpload` (sirf upload). DoD ka dataset list = 0% |
| Hour 3–5 | `src/pages/DatasetDetail.jsx` | ✅ exists (266 L) | **galat field names** (D-section table) + 202 polling ❌ + Disclaimer ❌ |
| Hour 5–6 | `src/pages/ExperimentNew.jsx` | ❌ **STUB** | repo me `ExperimentCreate.jsx` = 35 lines ka sirf "Go to Datasets" card. Plan preview + "WHY THIS PIPELINE?" + Run button = 0% |
| Day 2 H1–4 | `src/pages/ExperimentDetail.jsx` (4 tabs) | ⚠️ **PARTIAL (~35%)** | exists 409 L par tabs ❌, `/status` polling ❌ (abhi `/experiments/{id}` pe 3s poll), QUANTUM VALUE hero ❌, Explaination tab ❌, Cost tab ❌, Report flow ❌ |
| Day 2 H4–5 | `src/pages/Reports.jsx` | ❌ **MISSING** | page + nav link + `/reports` route |
| Day 2 H4–5 | global CSS | ✅ 632 lines | ❌ `.tabs`/`.error-box`/`.importance-bar` classes nahi (guide wale CSS me the) |
| — | `src/hooks/useDataset.js` | ❌ MISSING | guide §3 me listed |
| — | `src/hooks/useExperiment.js` | ❌ MISSING | guide §3 me listed |
| — | `src/lib/statusMap.js` | ❌ MISSING | **ye guide me nahi hai par lagna zaroori hai** (C-section dekho) |

**Score: 16 me se 4 sahi se done, 2 partial, 10 missing.** `src/components/` aur `src/hooks/` folder aaj bhi create nahi hue (`find` se verified — frontend me total 10 source files).

Guide DoD (§8) ka honest snapshot: **~25%**.

---

## PART B — `mocks/` folder me exactly kya hai (44 files)

4 datasets × same 11 files. Har file ke upar 2 metadata keys hain — chhodo mat, UI me render mat karo: `_contract` (kaunsa contract version), `_dataset`.

| Mock file | Ye kis screen ka data hai | Top-level shape (breast_cancer se verified) |
|---|---|---|
| `dataset_upload_response.json` | Upload success toast | `dataset_id` (UUID), `display_id: "DS-000001"`, `status:"REGISTERED"`, `filename`, `container_type`, `upload_timestamp`, `file_size_bytes`, `sha256`, `storage_path`, `is_duplicate`, `duplicate_of`, `validation_warnings[]`, `rejection_reason` |
| `dataset_profile.json` | DatasetDetail — 4 stat cards | **nested:** `dimensions.{rows:569,columns:33}`, `features.{numerical:30,categorical:2}`, `target.{candidate:'diagnosis',confidence:'HIGH'}`, `task.{candidate:'BINARY_CLASSIFICATION'}`, `class_distribution.{'0':357,'1':212}`, `missing_values.{total,percentage,by_column}`, `duplicates.candidate_count`, `warnings[]`, `status:'PROFILED'`, `profiled_at`, `profile_id`, `modality` |
| `validation_report.json` | DatasetDetail — validation card (v1.1) | **12 sections:** `validation_status:'PASS_WITH_WARNINGS'`, `quality_score:90`, `next_phase`, `target_validation{}`, `schema_validation{}`, `missing_values{}`, `duplicates{}`, `class_balance{imbalance_ratio:1.68, minority_percentage:37.3, severity:'MODERATE'}`, `value_validation{}`, `outliers{}`, `leakage{}`, `patient_level_split_risk{}`, `image_label_validation{}`, `critical_issues[]`, `warnings[]`(objects!), `info_messages[]`, `recommended_preprocessing_steps[]` |
| `experiment_config.json` | **ExperimentNew ka plan + "WHY THIS PIPELINE?"** | `plan_id`, `status:'READY_FOR_EXECUTION'`, `task`, `quantum_enabled`, `use_class_weight`, `preprocessing[]`, `reduction.{method:'PCA',components:8,variance_retained:0.9276}`, `classical_models[]`, `quantum_models[]`, `evaluation.{split,test_size,random_state}`, `experiments[]`, **`decision_trace.{rules_applied[], reason}`** ← ye wo cheez hai jo UI me dikhani hai |
| `experiment_status.json` | Progress tab (polling) | **flat:** `status:'COMPLETED'` (UPPERCASE), `stage:'completed'`, `progress:1.0` (float!), `message`, `started_at`, `elapsed_seconds`, `estimated_remaining_seconds`, `current_model`, `completed_models[]`, `circuit_executions:20475`, `current_epoch`, `total_epochs`, `error_message`, `resource_snapshot.{cpu_percent,memory_mb}` |
| `model_result_classical.json` | Results tab (per model) | `model_type:'CLASSICAL'`, `model_name:'RandomForest'`, `status`, `metrics.{accuracy,precision,recall,specificity,`**`f1_score`**`,roc_auc,`**`pr_auc`**`}`, `confusion_matrix[[4]]`, `resource_usage.{training_time_seconds,inference_time_seconds,memory_peak_mb,model_size_mb}`, `quantum_metrics:null`, `model_artifact_path`, `hyperparameters{}`, `random_seed`, `execution_timestamp`, `error_message` |
| `model_result_quantum.json` | Results + Cost tab (VQC) | same + `quantum_metrics.{qubits:8,circuit_depth:17,gate_count:142,two_qubit_gates:14,shots:1024,total_circuit_executions:20475,backend_type:'LOCAL_SIMULATOR',encoding_method:'angle_encoding'}`, `hyperparameters.{n_qubits,n_layers,shots,epochs,learning_rate}` |
| `explanation.json` | Explainability tab | `explanation_id`, `sample_id`, `prediction.{value,score,actual_label,is_correct}`, `feature_importance[{feature_name,importance,effect}]`, `global_importance[{feature_name,importance}]`, `quantum_circuit_explanation.{qubits,circuit_depth,encoding_method,feature_to_qubit_mapping{},measured_qubits[],circuit_diagram_url:null}`, `pipeline_trace[{phase,component,artifact|dimensions}]`, `model_decision_reason` (sentence!), `warnings[3 strings]`, `explainability_method:'feature_perturbation'`, `explanation_timestamp` |
| `recommendation.json` | **QUANTUM VALUE ASSESSMENT hero** | `benchmark_id`, `classical_best.{model_name,metrics{},training_time_seconds}`, `quantum_best.{model_name,qubits,metrics{},training_time_seconds,total_circuit_executions}`, `performance_differences.{accuracy_delta,recall_delta,auc_delta,f1_delta}`, `resource_comparison.{training_time_ratio:17.8,inference_time_ratio:1199.9,memory_ratio}`, **`classification:'TRADEOFF'`**, `observations[]`, `recommendation_text` |
| `cost_report.json` | Cost tab | `performance_summary{}`, `computational_cost.{training.{wall_clock_time_seconds,ram_peak_gb,cpu_utilization_avg_percent},inference.avg_time_ms}`, `quantum_cost.{qubits,circuit_depth,gate_count,two_qubit_gates,shots_per_execution,total_circuit_executions,total_shots:20966400}`, `pipeline_cost_breakdown.{preprocessing_seconds,...,quantum_percentage:92.3}`, `comparison_classical_baseline.{classical_model,`**`classical_training_seconds`**`,quantum_training_seconds,speedup_classical:17.8,verdict}`, `scalability_assessment.{current_environment:'LOCAL_LAPTOP',this_experiment_status:'FEASIBLE',recommended_max_qubits:8,note}`, **`financial_cost_local.{estimate:0,note:'Local quantum simulator. No cloud quantum cost.'}`** ← "₹0" card ka data |
| `processed_data_schema.json` | (optional) DatasetDetail bottom | feature arrays |

**Mocks kis kaam ke:** Ye **contract-shape** hain (nested, UPPERCASE status, `f1_score`, `pr_auc`) — aur ye real pipeline se generate hue hain (`generate_mocks.py` + real experiment IDs jaise `EXP-0850F91D`, `EXP-EC590B9D`). Matlab guide kehti hai: *inhi shapes pe UI banao*. Problem ye hai ki **tumhara actual backend in shapes me response nahi bhejta.** Dekho ↓

---

## PART C — ⚠️ 3-way shape conflict (yahi tumhara asli kaam hai)

`mocks/` + `contracts/` aapas me **agree** karte hain. `mvp/backend/` **nahi** karta. Isliye: **mock pe UI banegi → `MOCK_MODE=false` karte hi har screen `undefined` dikha degi.** Ye already ISSUES.md me documented hai (B-01, B-02, M-01, M-08, M-10, MH-03) par kisi ne fix nahi kiya.

### Endpoint-wise: guide/mock/contract vs backend actual (har cell code se verify)

| # | Endpoint | Mock/Contract kehta hai | `mvp/backend` **actually** bhejta hai | Tumhe kya karna hai |
|---|---|---|---|---|
| 1 | `POST /api/datasets/upload` | 13 fields, `status:'REGISTERED'`, `display_id` | `datasets.py:101-104` → **sirf 3:** `{dataset_id, filename, status:'uploaded'}` | UI me `display_id`/`sha256`/`is_duplicate` optional chhodo; `??` fallback do |
| 2 | `GET /api/datasets` | `{datasets:[{dataset_id, display_id, has_profile, status…}], total}` | `loader.py:97-107` → `{datasets:[{`**`id`**`, name, filename, path, hash, rows, columns:`**List[str]**`, loaded_at, size_mb}]}` — **`total` nahi, `has_profile` nahi** | List table inhi keys pe banao (`d.id`, `d.name`, `d.rows`, `d.columns.length`, `d.size_mb`). `has_profile` ke liye profile fetch karke badge dikhao |
| 3 | `GET /api/datasets/{id}/profile` | nested `dimensions.rows`, `features.numerical`, `target.candidate`, `missing_values.total`, `status:'PROFILED'`, 202 flow | **flat** (`datasets.py:29-50`): `rows`, `columns:`**`List[dict]`**, `numerical_columns_count`, `categorical_columns_count`, `missing_values_total`, `missing_percentage`, `duplicate_rows`, `target_candidates[]`, `recommended_target`, `is_binary_classification`, `class_distribution`, `name`, `dataset_id` | Adapter: `dimensions.rows` → `rows`, `features.numerical` → `numerical_columns_count`, `target.candidate` → `recommended_target`, `missing_values.total` → `missing_values_total`. ⚠️ `class_imbalance_ratio` backend response model me **hai hi nahi** → validation report se lo ya Piyush se bulwao |
| 4 | `GET /api/datasets/{id}/validate` | 12-section `validation_report.json` (v1.1) with `quality_score`, `class_balance.imbalance_ratio`, `severity` | `ValidationResponse` = **sirf** `{is_valid, issues[], warnings[], ready_for_ml, needs_target_selection, details{}}` (`datasets.py:52-59`; bade sections sirf profiler/contract me hain) | Quality-score ring / class_balance card tab tak **mock-only** rakho, ya Piyush se bolo profile+validate merge karke `validation_report` jaisa return kare |
| 5 | `POST /api/experiments` | `{experiment_id, status:'CREATED'}` | `{experiment_id, dataset_id, status:'created'}` (lowercase) | `.toUpperCase()` normalize karo |
| 6 | `POST /api/experiments/{id}/run` | `{status:'started'}` | `experiments.py:228-232` → `{experiment_id, dataset_id, status:'started'}` ✅ | same. 400 aata hai agar already running (`:186-190`) → toast dikhao, error nahi |
| 7 | `GET /api/experiments/{id}/status` | **flat**: `status:'RUNNING'`, `stage`, `progress:0.67`(float), `elapsed_seconds`, `circuit_executions`, `current_model`, `completed_models[]`, `error_message`, `resource_snapshot` | `:259-266` → `{experiment_id, status, progress:`**`{stage, progress, message}` (nested dict!)**`, started_at, completed_at}`. `elapsed_seconds`/`circuit_executions`/`current_model`/`completed_models`/`error_message` **koi nahi** | ⚠️ SABSE ZYADA TODO YAHAN. `const p = raw.progress?.stage ? raw.progress : raw;` type unwrap karo + `raw.progress ?? p.progress` (nested `progress.progress` float hota hai, top-level float mock me). `elapsed_seconds` khud nikaalo `Date.now() - new Date(started_at)` se |
| 8 | status enum | `CREATED…FAILED` **UPPERCASE** (`contracts/experiment_status.json:_values`) | `manager.py:16-24` **lowercase** values (`'running_classical'`…) | `const s = (raw.status||'').toUpperCase()` → phir map |
| 9 | stage enum | contract: `preprocessing, classical_training, quantum_training, benchmarking, explaining, completed` | `executor.py:115-264` `_update_progress(...)`: `loading, profiling, validating, preprocessing, classical, quantum, benchmarking, finalizing, completed` — **do enum ka mix, 3 stage strings contract se alag** | Alias table lagaao (D-section me code hai). Ye **Piyush ko bhi bolo** ki stage strings contract wale kare (1-line har `_update_progress` call) |
| 10 | `GET …/results` | `{experiment_id, status, models:{…}, comparison:{…}}` — models **top-level** | `:295-300` → `{experiment_id, status, results:{`**`dataset_profile, validation, preprocessing, models, comparison, resource_usage`**`}}` — models `data.results.models` ke andar | `const r = raw.results ?? raw;` (api.js me abhi `response.data.results` hai ✅ sahi hai — par pages ko is adapter se hi feed karo) |
| 11 | model metrics keys | `f1_score`, `pr_auc`, `resource_usage.{training_time_seconds,inference_time_seconds,memory_peak_mb}`, `confusion_matrix` at model level, `quantum_metrics.{qubits,gate_count,two_qubit_gates,…}`, `model_type:'CLASSICAL'` | real run (`experiment_results_EXP-279AE34B.json`): `metrics.{accuracy,precision,recall,f1,specificity,sensitivity,roc_auc}` → **`f1` not `f1_score`, `pr_auc` NAHI, `sensitivity` extra**, `training_time`/`inference_time` **model-level** (not `resource_usage`), `confusion_matrix` metrics ke andar, VQC me `metrics.quantum_resources.{n_qubits,n_layers,n_params,shots,circuit_depth,n_circuit_executions,training_time}` → **`n_qubits`/`n_circuit_executions`, `gate_count`/`two_qubit_gates` NAHI**, `model_type:'classical'` lowercase | Metric map object banaao (`f1_score ⇄ f1`), aur Cost tab me `gate_count ?? circuit_depth*2` type graceful fallback + "N/A" chip. `pr_auc` ke liye Piyush se bolo `average_precision` add kare |
| 12 | `comparison` | `classification:'TRADEOFF'`, `classical_best{}`, `quantum_best{}`, `performance_differences{}`, `resource_comparison{}`, `observations[]`, `recommendation_text` | real: `best_model`, `best_classical`, `best_quantum`, `performance_ranking[]`, `metrics_comparison{}`, `runtime_comparison{}`, `quantum_vs_classical.{classical_model,quantum_model,metrics_diff.<k>.{classical,quantum,difference,quantum_better},runtime_diff.{classical,quantum,ratio},quantum_resources{}}`, `recommendation` (**string**, object nahi) | Hero card: `classification` real me **nahi** → `recommendation.decision` se lo. `observations[]` → `performance_ranking` se bana lo (already sorted ✅). `classical_best.metrics` → `metrics_comparison[best_classical]` |
| 13 | recommendation | mock file `classification:'TRADEOFF'` | `experiments.py:302` + `recommendation.py:23-31` → `{decision, best_model, reasoning[], metrics_summary.{quantum,classical_best}.{accuracy,race…}, trade_offs.{runtime:{quantum_slower,ratio}}, confidence:'high|medium|low'}` | `decision` values **only**: `QUANTUM_ADVANTAGE`, `QUANTUM_PARITY`, `CLASSICAL_PREFERRED` (`:177-199`). ⚠️ Guide §8 DoD jo `TRADEOFF`/`CLASSICAL_ADVANTAGE` kehta hai — **wo backend me exist hi nahi karte.** Color map me 5 names rakho (guide wale 2 alias ke taur pe) |
| 14 | `GET …/explanation` | full `explanation.json`: `prediction{}`, `feature_importance[]`, `global_importance[]` (array), `quantum_circuit_explanation{}`, `pipeline_trace[]`, `warnings[3]` | `experiments.py:562-586` → `{experiment_id, explainability_method:'Gini importance…', models_explained[], global_importance:`**`{ 'random_forest': [{feature_name,feature_index,importance,rank}] }` (dict of arrays!)**`, quantum_circuit_info:{qubits,n_layers,n_params,circuit_depth,encoding_method,backend_type:'local_simulator (default.qubit)',feature_to_qubit_mapping,measured_qubits,measurement,gate_count_estimate,shots_per_execution,total_circuit_executions,circuit_diagram(TEXT, url nahi)}, pipeline_trace:[{phase,component,artifact,…}], warnings:[`**5**` strings], generated_at}` — **`prediction{}`, `feature_importance[]`, `sample_id`, `model_decision_reason` KAHI NAHI** | Per-sample prediction card → **abhi impossible**. Ya to mock-only rakho + "sample-level SHAP pending (Radha MH-01)" chip, ya Radha se `X_train.npy` artifacts maangno (ISSUES.md MH-01 exactly ye kehta hai). Global importance ke liye: `Array.isArray(gi) ? gi : Object.values(gi)[0] ?? []` |
| 15 | `GET …/cost` / cost_report | `cost_report.json` (11 blocks, `financial_cost_local`, `pipeline_cost_breakdown`) | **koi cost endpoint nahi** 😬 — sirf `GET …/resources` → `{system_resources:{cpu_percent,memory_mb,peak_memory_mb,elapsed_time,quantum_resources}, quantum_resources}` | Cost tab = `resources` + `models.vqc.metrics.quantum_resources` se banaao. ₹0 card hardcoded ho sakta hai (backend `financial_cost` kehta hi nahi, isliye static "₹0 — local simulator" safe hai) |
| 16 | `GET /api/experiments/{id}/plan` | `experiment_config.json` (plan + `decision_trace.rules_applied`) | **ENDPOINT HI NAHI HAI** (saare routes check kiye: datasets 5, experiments 9, results 4, reports 3, main 3 — plan kahin nahi) | ExperimentNew ka "plan" aaj: `GET /api/config` (`main.py:59-64` → `{quantum, experiment, classical_models}`) + profile se derive karo, ya `mocks/*/experiment_config.json` pe demo chalao. **Piyush se maangno: `GET /api/datasets/{id}/plan`** |
| 17 | reports | guide `POST /api/experiments/{id}/report` → `{report_path}`; `GET …/report` → HTML | **do systems:** `reports.py:56-62` `POST /api/reports/{id}` → `artifacts/reports/RPT-<exp>.html`; `experiments.py:605-680` `POST /api/experiments/{id}/report` → `<exp>_report.html` + `_cost_report.json`. `GET /api/reports/{id}/download` sirf `RPT-<exp>.html` dhoondhta hai (`:110-135`) | Ek pair use karo: `POST /api/reports/{id}` + `GET /api/reports/{id}/download`. Radha ke 16-section report chahiye to `GET /api/experiments/{id}/report` se HTML directly fetch karke blob me download karo |
| 18 | `GET /api/health`, `GET /api/config` | `→ {status:'healthy'}` | ✅ dono maujood hain (`main.py:53-64`) | Dashboard pe green/red dot badge — 20 line ka kaam, DoD item free me clear |

**Verdict:** guide §4 = contracts = mocks (teeno ek jaise), aur **real MVP backend teeno se alag**. To tumhara "karna kya hai" ka 60% hissa UI banana nahi, **ek normalization/adapter layer banana** hai jo dono shapes kha sake.

---

## PART D — Data layer: **ye maine likh ke test kar diya hai** (copy-paste ready)

Do files repo me already ban gayi hain (is clone me), aur 67 assertions pe pass hui hain:

| File | Kaam |
|---|---|
| `mvp/frontend/src/lib/fieldMap.js` | `STAGE_ALIASES` (3-way stage drift), `STAGES` (StageProgress ke 6 keys), `RUNNING_STATES`, `METRIC_COLUMNS` (7 metrics + `f1_score ⇄ f1` alias), `DECISION_COLORS` (backend ke 3 real values + guide ke 2 aliases), `up()`, `pick()` |
| `mvp/frontend/src/lib/adapters.js` | `adaptDatasetList`, `adaptDataset`, `adaptProfile`, `adaptValidation`, `adaptStatus`, `adaptResults`, `adaptQuantum`, `adaptResources`, `adaptExplanation`, `adaptRecommendation`, `adaptReport`, `adaptError` |
| `mvp/frontend/tests/adapters.test.mjs` + `npm run test:adapters` | Har adapter **dono shapes** pe test hota hai: `mocks/breast_cancer/*.json` (guide/contract shape) aur `mvp/experiment_results_EXP-*.json` + hand-built backend responses (`experiments.py:259-266`, `:562-586`) |

```bash
cd mvp/frontend
npm run test:adapters     # → ✅ ALL PASS  (67 assertions)
npm run build             # → ✓ built (abhi bhi clean)
```

Jo cheezein test ne already pakdi (ye tumhare UI ke liye decision hain, bug nahi):
- `status` → mock flat/UPPERCASE aur backend nested/lowercase — `adaptStatus` dono se `{status, stage, progress, message, elapsedSeconds, circuitExecutions, completedModels, error, isRunning}` nikalta hai. `elapsedSeconds` backend me na milne pe `started_at` se derive hota hai. `circuitExecutions` backend me **nahi** milta → `0`, UI me "not reported by backend" chip dikhao (fake number nahi).
- `results` → `models.vqc.quantum.gateCount = null` (backend `gate_count_estimate` deta hai **sirf explanation** me, results me nahi) → Cost tab me us cell pe "—" lagao.
- `metrics.pr_auc = null` dono shapes me (backend `sensitivity` deta hai) → column rakho, value "—" — guide ke DoD wale 6 metrics me `precision` missing tha, isliye 7 rakhe hain.
- `adaptValidation` par real backend me `qualityScore = null` → Dashboard/DatasetDetail pe quality ring mock-only hai, real pe hide karo.
- `adaptExplanation().available.prediction === false` real backend pe → sample-level card "pending" state me render karo, blank nahi.

### D3. Abhi bhi karna hai: `src/services/api.js` (is file ko maine chhua nahi — integration decision tumhara hai)
```js
export const MOCK_MODE = import.meta.env.VITE_MOCK === '1';
// ❌ add these 4 — endpoints exist in backend, api.js me function nahi:
getExplanation:  (id)        => axios.get(`${API_BASE}/experiments/${id}/explanation`).then(r => r.data),
getConfusionMatrix: (id,m)   => axios.get(`${API_BASE}/experiments/${id}/confusion-matrix/${m}`).then(r => r.data),
deleteExperiment:(id)        => axios.delete(`${API_BASE}/experiments/${id}`).then(r => r.data),
system: { health: () => axios.get('/api/health').then(r=>r.data),
          config: () => axios.get('/api/config').then(r=>r.data) }
```
**Rule jo ab force karo:** har function ka return value **turant adapter** se jaaye — `return adaptStatus(await …)`. Koi page raw `response.data` na padhe. Tabhi `MOCK_MODE` flip safe hai.

### D4. Mocks ko app me laana (Vite)
`mocks/` repo root pe hai, frontend se bahar → `vite.config.js` me alias sabse clean (copy karoge to stale ho jayega jab `generate_mocks.py` phir chalega):
```js
resolve: { alias: { '@mocks': path.resolve(__dirname, '../../mocks') } }
// usage: import { dataset_profile, experiment_status } from '@mocks/breast_cancer/index.js'
```
⚠️ `mocks/*/experiment_status.json` me **sirf final snapshot** hai (`status:'COMPLETED'`, `progress:1.0`) → polling UI test karne ke liye guide §6 ka `MOCK_STATUS_SEQUENCE` (6 entries, `classical_training → quantum_training → benchmarking`) wala array chhota sa banao, warna progress bar kabhi animate nahi karega aur tumhe lagega backend kharab hai.

## PART E — Backend walon se ye maanglo (ye tumhara kaam nahi, par tumhare bina blocked hai)
| Kaun | Kya | Kyun |
|---|---|---|
| **Piyush** | `GET /status` me flat fields: `elapsed_seconds`, `circuit_executions`, `completed_models[]`, `current_model`, `error_message` (contract v1.1 me already promised, code me nahi) | Progress tab ka 90% data isi pe hai |
| **Piyush** | stage strings ko contract values pe laao (`classical_training`, `quantum_training`) aur executor ke 9 stages → contract ke 6 | StageProgress ✓/●/○ nahi banega warna |
| **Piyush** | `f1_score` (+ ideally `pr_auc`) alias results me, `training_time_seconds` `resource_usage` ke andar | MetricsTable + Cost table |
| **Piyush** | `GET /api/datasets/{id}/plan` → `experiment_config.json` shape (`decision_trace.rules_applied[]`) | ExperimentNew ka "WHY THIS PIPELINE?" — aaj koi source nahi |
| **Shweta** | profile response me `class_imbalance_ratio` + duplicate `columns` declaration fix (`datasets.py:36` vs `:51`) | DatasetDetail imbalance card |
| **Radha** | `prediction` + `feature_importance[]` in explanation (MH-01 ke liye `X_train.npy` artifacts save karo) **ya** clearly bolo ki sample-level explanation Phase-2 me aayega | Explainability tab ka hero card |
| **Radha** | report ka ek canonical pair decide (`RPT-` vs `_report`) | Generate → Download 404 |

---

## PART F — Aaj se kaam ka order (guide §6 ke hisaab se, par data-layer pehle)
1. **(2h)** `lib/fieldMap.js` + `lib/adapters.js` + `api.js` me `MOCK_MODE`/`VITE_MOCK` + 5 new endpoints + mock import alias → `VITE_MOCK=1 npm run dev` pe Dashboard + Datasets dikhein (real API se bhi). **Test both flags — yahi do baar chalao.**
2. **(2h)** 7 components (`StageProgress`, `MetricsTable`, `FeatureImportanceBar`, `ClassDistributionChart`, `MetricsBadge`, `FileDropzone`, `Disclaimer`) — sab **adapted shape** pe, raw JSON pe nahi. CSS me `.tabs`, `.error-box`, `.bar-row` classes add karo (aaj `index.css` me nahi hain).
3. **(1.5h)** `hooks/useDataset.js` + `hooks/useExperiment.js` — `setInterval` 2000ms, `useRef`, cleanup mandatory, `MOCK_STATUS_SEQUENCE` jaisa sequence mock me chale.
4. **(2h)** `Datasets.jsx` (list + dropzone) + `DatasetDetail` ke field names adapter pe migrate + 202 polling + Disclaimer.
5. **(2h)** `ExperimentNew.jsx` (plan + rules + Run → create+run+navigate) — mock plan se UI ready rakho, real 404 pe `GET /api/config` fallback.
6. **(3h)** `ExperimentDetail.jsx` → 4 tabs (Progress / Results / Explain / Cost) + QUANTUM VALUE hero (`adaptRecommendation().color`) + Generate Report flow.
7. **(1h)** `Reports.jsx` + nav link + health badge on Dashboard + saare `alert()` → `<ErrorBanner/>`.
8. **(0.5h)** `npm run build` + `VITE_MOCK=1`/`0` dono pe smoke test, PR bhejo (`naeem/*` branch, repo pattern follow karo).

**Ek line me scene:** UI ka 40% ban gaya hai (aur build clean pass hota hai), par baaki 60% me se aadha kaam **screens banana nahi, backend ke real JSON shapes ke saath unhe wire karna** hai — kyunki mocks/contracts jo promise karte hain, `mvp/backend` aaj uska 60% hi deta hai.

---

## PART G — Live backend run (27 Sep 2026, `:8000` actually booted)

Maine FastAPI + pandas + scikit-learn + pennylane install karke server **chalaya** aur uske
 asli responses UI ke adapters pe chalaye — `mvp/frontend/tests/live-backend.test.mjs`
(`npm run test:live`, server na mile khud skip ho jata hai). Results:

**Chalta hai ✅**
- `GET /api/health` → `{status:'healthy'}`; Vite proxy `:5173/api/...` → `:8000` 200 (browser ka actual rasta verify)
- `GET /api/datasets` → 3 demo tables; `display` name se aata hai, `featureCount` = `columns.length` (breast_cancer = **32**, kyu ki loader ne all-empty column `Unnamed: 32` gira diya — jabki `/profile` me **33** columns hain; ye 1 ka farak backend ka apna inconsistency hai, UI donu handle karti hai)
- `GET /api/datasets/{id}/profile` → flat shape, 33 column rows, `class_distribution` 2 keys, `target=diagnosis` ✅
- `GET …/validate` → `{is_valid:false, issues:['Columns with all missing values: [\'Unnamed: 32\']'], …}` → UI me quality ring **hide** hota hai (score nahi hai), issue list dikhta hai

**Backend ke 4 gaps jo live run ne dikhaaye (frontend inhe crash nahi hone deti, par ye fix hone chahiye):**
1. `POST /run` ke baad run **FAILED** ho jata hai stage `validating` pe: `Dataset validation failed: ["Columns with all missing values: ['Unnamed: 32']"]`. Matlab `loader.load_csv` empty column **drop** karta hai, par executor ka validator raw frame/profile se check karta hai → `mvp/data/demo/breast_cancer.csv` ka trailing comma column pipeline ko block karta hai. **Piyush/Jayed ka fix** (validator ko wahi cleaned frame do, ya CSV clean karo).
2. `status` payload me `started_at: null` → elapsed UI khud nikaal leti hai, par timer `—` dikhta hai. `manager.update_status` ko `started_at` set karna chahiye.
3. `status.error_message` ** absent ** — failure ka reason sirf server log me hai. UI generic "no error_message returned" dikhati hai; `experiments.py:259-266` me `error_message` bharo to asli message screen pe aayega.
4. `resources` → `{system_resources:{}, quantum_resources:null}` (empty) → Cost tab me values `—`/note dikhte hain, fake number nahi.

**Iska matlab tumhare liye:** adapter layer live data pe bhi total hai (koi crash nahi, "—" + explanation dikhta hai). Aur demo ke liye `VITE_MOCK=1` use karo jab tak backend ka validation bug fix nahi hota — mock me poora 23s timeline chalta hai (Progress tab live animate hoga, phir results).
