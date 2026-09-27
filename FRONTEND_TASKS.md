# Q-Diagnose — Frontend (React) Status Audit + Task List
**Repo:** `PIYUSH-BHAVSAR/Q-Diagnose` @ `main` = `c264169` (merge of PR #2, radha-explainability-reports)
**Audit scope:** `mvp/frontend/` + jo APIs backend actually expose karta hai (`mvp/backend/`)
**Date:** 27 Sep 2026

> Neeche har claim repo ke actual code se verify kiya gaya hai (line/path ke saath). Guess kuch bhi nahi.

---

## 0. Aaj frontend kya-kya hai (verified)

```
mvp/frontend/
├── index.html            ✅ (Google Fonts: JetBrains Mono + Plus Jakarta Sans)
├── package.json          ✅ react 18 + vite 5 + react-router-dom 6 + axios + chart.js + lucide-react
├── vite.config.js        ✅ proxy /api → http://localhost:8000
└── src/ (2166 lines total)
    ├── main.jsx          ✅
    ├── App.jsx           ✅ header + nav + 6 routes (79 lines)
    ├── index.css         ✅ 632 lines — dark cyan/violet theme
    ├── services/api.js    ✅ 116 lines — datasetApi / experimentApi / reportApi
    └── pages/
        ├── Dashboard.jsx        273 lines
        ├── DatasetUpload.jsx   194 lines
        ├── DatasetDetail.jsx   266 lines
        ├── ExperimentsList.jsx 152 lines
        ├── ExperimentDetail.jsx 409 lines
        └── ExperimentCreate.jsx  35 lines  ⚠️ sirf ek placeholder card hai
```

**Build check (maine chalake dekha):**
```
npm install  → added 98 packages, exit 0
npm run build → ✓ 1892 modules transformed, 428.86 kB JS, exit 0
```
Matlab code chalta hai, compile clean hai. Problem **feature + integration** me hai, build me nahi.

**Yaad rakhne jaisi baat:** guide_naeem.md §3 jo maangta hai usme se `src/components/` (7 files), `src/hooks/` (2 files) aur `pages/Reports.jsx` — **teeno aaj bhi exist hi nahi karte.** `find` se confirm: frontend me total 10 source files hi hain, koi `components/` ya `hooks/` folder nahi.

---

## 1. P0 — Integration bugs (pehle ye fix karo, 1 din me)

### 1.1 Status/stage strings 3 jagah 3 alag hain ⚠️ SABSE BADA BUG
- `ExperimentDetail.jsx` polling loop karta hai: `['running_classical','running_quantum','preprocessing']`
- Backend `manager.py:16-24` enum (lowercase values): `created, validating, preprocessing, running_classical, running_quantum, benchmarking, explaining, completed, failed`
  → **`validating`, `benchmarking`, `explaining` frontend ki list me nahi** → beech me polling ruk jayegi, UI atka hua dikhega.
- Backend `executor.py:115-264` progress stage: `loading, profiling, validating, preprocessing, classical, quantum, benchmarking, finalizing, completed`
- `contracts/experiment_status.json` stage: `preprocessing, classical_training, quantum_training, benchmarking, explaining, completed` (aur status UPPERCASE me)

**Fix (React side):** ek `src/lib/statusMap.js` banao jo teeno variants normalize kare:
```js
export const RUNNING_STATES = new Set([
  'validating','preprocessing','running_classical','running_quantum',
  'benchmarking','explaining','classical','quantum','loading','profiling','finalizing'
]);
export const STAGE_ALIASES = {
  loading:'preprocessing', profiling:'preprocessing', validating:'preprocessing',
  preprocessing:'preprocessing',
  classical:'classical_training', running_classical:'classical_training', classical_training:'classical_training',
  quantum:'quantum_training', running_quantum:'quantum_training', quantum_training:'quantum_training',
  benchmarking:'benchmarking', explaining:'explaining', finalizing:'benchmarking', completed:'completed'
};
```
Aur ye **Piyush + Radha ke saath 5 min me lock karo** ki canonical kaun (mere hisaab se: backend ke actual lowercase status + contract ke stage names). ISSUES.md B-01/M-01 exactly ye hi highlight karta hai — abhi unresolved hai.

### 1.2 `/api/datasets` ka list UI kahin bhi nahi
`App.jsx` me `route /datasets → DatasetUpload` only. DoD maangta hai: *"Lists all registered datasets with profiling status badge."*
**Fix:** `DatasetUpload.jsx` ke neeche dataset table add karo (ya `Datasets.jsx` banao jisme dropzone + list ho). Fields jo backend deta hai (`loader.py:97-107`): `id, name, filename, rows, columns (array!), loaded_at, size_mb, hash`.
- ⚠️ list me `dataset_id` **nahi**, `id` hai — `DatasetDetail` ko navigate karte waqt `d.id` use karo.
- `columns` yahan **array of names** hai, `profile` me **array of dicts** → count chahiye to `columns.length`.

### 1.3 `ExperimentCreate.jsx` = stub (35 lines)
Abhi sirf "Go to Datasets Library" button. DoD ke hisaab se ye **plan preview screen** honi chahiye: saare pipeline config items + "WHY THIS PIPELINE?" rules + **Run Experiment** button jo create → run → detail pe bheje.
Route bhi badlo: guide kehti hai `/experiments/new/:datasetId` — abhi `/experiments/new` hai aur datasetId pahunch hi nahi raha.

### 1.4 Explainability + Cost + Report — backend ready, frontend blind
PR #2 (Radha, 5 ghante pehle) ne ye endpoints de diye, **api.js me inka koi function hi nahi**:
| Backend endpoint (verified) | api.js me? |
|---|---|
| `GET /api/experiments/{id}/explanation` (`experiments.py:378`) | ❌ nahi |
| `GET /api/experiments/{id}/recommendation` (`experiments.py:302`) | ⚠️ function hai par koi page call nahi karta |
| `GET /api/experiments/{id}/resources` (`results.py:103`) | ⚠️ same |
| `GET /api/experiments/{id}/metrics` (`results.py:35`) | ⚠️ same |
| `GET /api/experiments/{id}/confusion-matrix/{model}` (`results.py:137`) | ❌ nahi |
| `DELETE /api/experiments/{id}` (`experiments.py:342`) | ❌ nahi |
| `GET /api/health`, `GET /api/config` (`main.py`) | ❌ nahi |

### 1.5 Report generate/download pair tutega
- `api.js` → `POST /api/reports/{id}` → `reports.py:56-62` file likhta hai `artifacts/reports/RPT-<exp>.html`
- `experiments.py:605` (`POST /api/experiments/{id}/report`) → likhta hai `artifacts/reports/<exp>_report.html` (`reports/generator` wala 16-section report)
→ Do baaton me se dusra wala generate karo aur download pehle wale se maango = **404**.
**Fix:** ek hi pair use karo — `POST /api/reports/{id}` + `GET /api/reports/{id}/download`. Radha ke 16-section report ke liye `GET /api/experiments/{id}/report` ka response se path uthao. (Ye pair **Radha se confirm karo** — backend me ye inconsistency hai, frontend side se consistent pair hi safe hai.)

### 1.6 `DatasetDetail.jsx` field mismatches
| Frontend padhta hai | Backend actually bhejta hai | Result |
|---|---|---|
| `profile.dataset_name` | `name` (`datasets.py:38`) | header hamesha "Dataset: DS-XXXX" |
| `profile.class_imbalance_ratio` | response model me **nahi** (profiler compute karta hai, API leak nahi karta) | imbalance warning kabhi render nahi hogi |
| `profile.columns?.length \|\| profile.columns` | `columns` = `List[dict]` | accidentally theek, par fragile |
| 4 stat cards (Samples/Features/Classes/Missing) | `rows`, `columns`, `class_distribution`, `missing_values_total` | abhi galat cards hain: Total/Numerical/Missing% |

**Action:** Shweta/Piyush se bolo `class_imbalance_ratio` + `target_candidates[0]` profile response me add karein (2-line change, `DatasetProfileResponse`), tab tak frontend me fallback rakho.

### 1.7 Dashboard ke fake actions
`Dashboard.jsx:189,197,205` me teeno demo buttons = `window.alert('Demo: ... dataset')`. Aaj bhi stub.
**Fix:** `POST /api/experiments` with `dataset_id` of demo set (backend `loader._scan_uploads_dir` `mvp/data/demo/*.csv` ko auto-register karta hai → breast_cancer / heart_disease / parkinsons already list me aate hain). Ya simplest: demo card ko `<Link to="/datasets/DS-<demo-id>">` bana do.
Plus DoD: Dashboard pe **backend health badge** chahiye — `GET /api/health` → `src/services/api.js` me `systemApi.health()` add karo.

### 1.8 UX polish bugs (chhote par dikhenge)
- `ExperimentDetail.jsx:85` `alert('Failed to start experiment')` aur `DatasetDetail`/`DatasetUpload` me `alert(...)` → DoD kehta hai styled error box, raw `alert` nahi. Ek `<ErrorBanner/>` component banao, `error.response.data.detail` dikhao.
- `index.html:5` `/vite.svg` refer karta hai par `frontend/public/` folder hi nahi hai → favicon 404.
- Poll interval 3000ms hai (`ExperimentDetail.jsx:53`); DoD 2000ms kehta hai, aur wo `GET /status` ki jagah `GET /experiments/{id}` poll kar raha hai.
- `results` fetch sirf `status==='completed'` par hota hai — agar user refresh kare to ek extra round-trip theek hai, par **error 400** (result not completed) handle karo.

---

## 2. P1 — Jo files banana ZAROORI hai (guide §3 ka backlog, aaj 0/9 bani hain)

### `src/hooks/` (naya folder)
1. `useDataset(datasetId)` — `getProfile` + `validate` + 202/`profiling` state pe auto-poll
2. `useExperiment(experimentId)` — create/run/**poll `/status` every 2s**/results/explanation/recommendation, `useRef` + `clearInterval` cleanup (DoD ka "polling memory leak" item)

```js
// skeleton — cleanup math bhoolta hai log, ye zaroori hai
useEffect(() => {
  if (!isRunning) return;
  const t = setInterval(tick, 2000);
  return () => clearInterval(t);
}, [isRunning]);
```

### `src/components/` (naya folder)
3. `StageProgress.jsx` — ✓/●/○ 5-stage (uses `STAGE_ALIASES`)
4. `MetricsTable.jsx` — 4 models × 7 metrics (**precision column add karo** — ISSUES.md B-02 kehta hai guide wala table `precision` chhod deta hai; data backend me `precision` key se aata hai, `f1_score` nahi — backend `f1` deta hai, aur `roc_auc`/`pr_auc` VQC me nahi → `?? '—'`)
5. `FeatureImportanceBar.jsx` — horizontal bars, positive green / negative red
6. `ClassDistributionChart.jsx` — bars with percentages (DoD "class distribution bars with percentages")
7. `MetricsBadge.jsx` — single pill, best-value highlight
8. `FileDropzone.jsx` — `DatasetUpload.jsx` ke andar ka drag-drop logic nikaal ke reusable banao (abhi inline hai, reuse nahi ho sakta)
9. `Disclaimer.jsx` — "RESEARCH / BENCHMARKING SYSTEM — not clinical diagnoses" (abhi Dashboard me hardcoded banner hai, kahin reuse nahi) + `ConfusionMatrix.jsx` (chart.js already installed hai, free win)

### `src/pages/Reports.jsx` + route `/reports` (nav me "Reports" link)
DoD/plan §52 kehta hai pages: `/`, `/datasets`, `/datasets/:id`, `/experiments`, `/experiments/new`, `/experiments/:id`, `/reports` — **abhi 6/7 bani hain**.

### `src/services/api.js` me `MOCK_MODE`
DoD: *"MOCK_MODE = true mode works completely without a running backend."* Abhi file me `MOCK_MODE` string kahin nahi (verify kiya).
`src/mocks/*.json` = repo ke `mvp/../mocks/{breast_cancer,heart_disease,parkinsons,diabetes}/*.json` — **ye already committed hain** (11 files per dataset: dataset_profile, validation_report, experiment_status, model_result_classical, model_result_quantum, explanation, recommendation, cost_report…). Bas `import` karke `if (MOCK_MODE) return MOCK_X;` lagao — 30 min ka kaam, poora UI bina backend chalega.

---

## 3. P2 — `ExperimentDetail.jsx` ko 4-tab screen banao (sabse zyada "wow" yahi hai)

Abhi page linear hai: header → pipeline → results table → chart → recommendation → quantum telemetry → error. DoD maangta hai 4 tabs:

**Tab 1 — Progress:** `<StageProgress/>`, live message (`progress.message`), circuit-execution count (`progress.circuit_executions ?? progress.completed_models?.length ?? 0` — ISSUES.md M-10 wala fallback), completed hone pe auto-switch to Results.

**Tab 2 — Results:** "QUANTUM VALUE ASSESSMENT" hero.
⚠️ **Naming trap:** guide_naeem.md kehta hai `QUANTUM_ADVANTAGE / TRADEOFF / PARITY / CLASSICAL_ADVANTAGE`, par `benchmarking/recommendation.py:177-199` **actually** ye return karta hai:
```
QUANTUM_ADVANTAGE   → green
QUANTUM_PARITY      → blue
CLASSICAL_PREFERRED → red
```
`TRADEOFF` aur `CLASSICAL_ADVANTAGE` backend me exist hi nahi karte. Map me teeno real values + do alias rakho.
Hero ke neeche: best classical vs best quantum side-by-side (data: `results.comparison.best_classical`, `best_quantum`, `metrics_comparison`, `quantum_vs_classical.metrics_diff.{accuracy,recall,...}.difference`), full `MetricsTable`, best recall/AUC green highlight.
`results.comparison.recommendation` **available hai** (sample JSON me confirm) → abhi jo callout hai wo chalega. ✅

**Tab 3 — Explainability** (`GET /experiments/{id}/explanation`, response model verified `experiments.py:366-374`):
`explainability_method`, `models_explained[]`, `global_importance{}`, `quantum_circuit_info{}` (qubits/depth/encoding/mapping), `pipeline_trace[]`, `warnings[]` (5 warnings hain — teeno disclaimer cards inhi se banao).
Score ke neeche line: "Uncalibrated — not a probability" (plan §12, ISSUES N-03).

**Tab 4 — Cost** (`GET /experiments/{id}/resources` → `{system_resources, quantum_resources}`; VQC keys verified from `experiment_results_EXP-279AE34B.json`: `n_qubits:8, n_layers:2, n_params:32, shots:1024, circuit_depth:56, n_circuit_executions:15200, training_time`):
grid + "Financial Cost: ₹0 — local simulator, no hardware billed" + performance-vs-cost table for 4 models.

Bottom: **Generate Report** button → `POST /api/reports/{id}` → phir "Open Report →" (`/api/reports/{id}/download`).

---

## 4. Cross-team lock-in (aaj hi 3 decisions, code se pehle)
1. **Status/stage enum** — §1.1 (Piyush): actual backend lowercase `status` + contract ke `stage` names? Ya contract uppercase?
2. **Dataset profile me `class_imbalance_ratio` + `missing_values_total`** return hona (Shweta) — DoD ke 4 cards ke liye. Also `DatasetProfileResponse` me `columns` **do baar declare hai** (`datasets.py:36` `columns: int` aur `:51` `columns: List[dict]`) → Pydantic me second wins, int count kho jata hai. Ye 1-line backend fix hai; tab tak `columns.length` use karo.
3. **Report endpoints** kaunsa pair canonical (Radha) — §1.5.

---

## 5. Suggested order (2 days, PR-wise)
| PR | Content | Files |
|---|---|---|
| PR1 `naeem/fix-status-and-api-layer` | `lib/statusMap.js`, api.js me `systemApi`/`explanation`/`confusionMatrix`/`delete` + `MOCK_MODE` + `src/mocks/` | 3 files |
| PR2 `naeem/components` | 9 components + `<ErrorBanner/>` | 10 new files |
| PR3 `naeem/hooks` | `useDataset`, `useExperiment` (2s poll, cleanup) | 2 new files |
| PR4 `naeem/datasets-list-experiment-plan` | `/datasets` list + `ExperimentCreate` real plan/run screen | 2 pages + `App.jsx` route |
| PR5 `naeem/tabs-results-explain-cost` | `ExperimentDetail` 4 tabs + QUANTUM VALUE hero | 1 page (split into 4 tab components) |
| PR6 `naeem/reports-page` | `Reports.jsx` + nav link + generate/download flow | 2 files |
| PR7 `naeem/polish` | alerts → ErrorBanner, Dashboard demo buttons + health badge, favicon, a11y/keyboard dropzone | misc |

**Branch/PR convention jo repo me already chal raha hai:** `name/topic` (jaise `radha-explainability-reports`, `jayed/data-pipeline`) + PR → `main` → merge. Naeem bhi isi pattern pe rahe, `main` pe direct push na kare.

---

## 6. Har PR se pehle ye chalao
```bash
cd mvp/frontend
npm run build                    # abhi PASS hai — break na ho
# backend ke saath:
cd .. && python -m backend.main  # :8000
cd frontend && npm run dev       # :5173 (proxy already configured ✅)
```
Manual smoke: upload CSV → profile → create experiment → poll → results → explanation → cost → report download. Browser console me koi `alert()` nahi, koi `[object Object]` nahi, koi raw Python traceback nahi.

## 7. DoD score aaj (guide_naeem.md §8 ke against)
- Setup: `npm run dev`/`build` ✅, CORS ✅ (proxy use ho raha hai, hardcoded URL nahi)
- API layer: single source ✅, user-friendly errors ❌ (alert use ho raha hai), MOCK_MODE ❌
- Dashboard: ❌ (health badge nahi, demo buttons stub)
- Datasets: list ❌, dropzone ✅
- DatasetDetail: 4 cards ❌ (fields galat), class % bars ❌, polling ❌, "Design Experiment" flow ❌ (seedha create kar deta hai)
- ExperimentNew: ❌ (page exist hi nahi karta properly)
- Progress tab: stage indicators ⚠️ (inline, galat enum), 2s poll ❌ (3s + galat endpoint `/status` use hi nahi ho raha), circuit count ❌, auto-switch ⚠️
- Results tab: hero ❌, 4-model table ⚠️ (inline, precision missing), highlights ❌
- Explainability tab: ❌ 0% (endpoint ready hai!)
- Cost tab: ❌ 0% (data ready hai!)
- Disclaimer: ❌ component nahi, text hardcoded 1 jagah
**Overall ≈ 25% of §8 DoD.** Base achha hai — missing cheez integration hai, redesign nahi.
