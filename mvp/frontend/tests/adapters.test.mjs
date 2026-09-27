import { readFileSync, readdirSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const HERE = path.dirname(fileURLToPath(import.meta.url));   // mvp/frontend/tests
const REPO = path.resolve(HERE, '..', '..', '..');           // repo root
const readJson = (rel) => JSON.parse(readFileSync(path.join(REPO, rel), 'utf8'));
import {
  adaptStatus, adaptResults, adaptProfile, adaptValidation, adaptExplanation,
  adaptRecommendation, adaptQuantum, adaptDatasetList, adaptResources, adaptError
} from '../src/lib/adapters.js';

const R = (p) => readJson(p);
let fails = 0;
const ok = (name, cond, got) => {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${cond ? '' : '   → got: ' + JSON.stringify(got)}`);
  if (!cond) fails++;
};

/* ── 1. STATUS: mock (flat, UPPERCASE) vs backend (nested progress, lowercase) ── */
const mockStatus = R('mocks/breast_cancer/experiment_status.json');
const a1 = adaptStatus(mockStatus);
ok('status/mock: stage completed', a1.stage === 'completed', a1);
ok('status/mock: progress float 1.0', a1.progress === 1, a1);
ok('status/mock: circuit 20475', a1.circuitExecutions === 20475, a1);
ok('status/mock: completedModels array', Array.isArray(a1.completedModels), a1);

const beStatus = { // exactly what mvp/backend/api/experiments.py:259-266 returns
  experiment_id: 'EXP-279AE34B', status: 'running_quantum',
  progress: { stage: 'quantum', progress: 0.6, message: 'Training quantum model' },
  started_at: '2026-09-26T10:00:00Z', completed_at: null
};
const a2 = adaptStatus(beStatus);
ok('status/backend: status uppercased', a2.status === 'RUNNING_QUANTUM', a2);
ok('status/backend: executor stage "quantum" → quantum_training', a2.stage === 'quantum_training', a2);
ok('status/backend: nested progress unwrapped', a2.progress === 0.6, a2);
ok('status/backend: message from nested', a2.message === 'Training quantum model', a2);
ok('status/backend: elapsed derived from started_at', a2.elapsedSeconds > 0, a2.elapsedSeconds);
ok('status/backend: circuit fallback 0 (field absent in API)', a2.circuitExecutions === 0, a2);
ok('status/backend: isRunning true', a2.isRunning === true, a2);

/* ── 2. RESULTS: real backend file (flat f1, model-level training_time) ── */
const real = R('mvp/' + readdirSync(path.join(REPO, 'mvp')).find((f) => f.startsWith('experiment_results_')));
const r1 = adaptResults(real);
ok('results/backend: 4 models', Object.keys(r1.models).length === 4, Object.keys(r1.models));
const vqc = r1.models.vqc;
ok('results/backend: vqc qubits 8 (n_qubits→qubits)', vqc.quantum?.qubits === 8, vqc.quantum);
ok('results/backend: vqc executions 15200 (n_circuit_executions)', vqc.quantum?.executions === 15200, vqc.quantum?.executions);
ok('results/backend: gate_count absent → null (no fake number)', vqc.quantum?.gateCount === null, vqc.quantum?.gateCount);
ok('results/backend: f1 → UI f1 column', Math.abs(r1.models.svm.metrics.f1 - 0.7714) < 1e-4, r1.models.svm.metrics.f1);
ok('results/backend: pr_auc null', r1.models.svm.metrics.pr_auc === null, r1.models.svm.metrics.pr_auc);
ok('results/backend: training_time from model-level', Math.abs(r1.models.vqc.resources.trainingTime - 128.7069) < 1e-3, r1.models.vqc.resources);
ok('results/backend: memory null (backend has no per-model memory)', r1.models.vqc.resources.memoryMb === null, r1.models.vqc.resources);
ok('results/backend: ranking 4 rows', r1.ranking.length === 4, r1.ranking.length);
ok('results/backend: bestClassical random_forest', r1.comparison.bestClassical === 'random_forest', r1.comparison.bestClassical);
ok('results/backend: accuracy diff object usable', r1.comparison.diff('accuracy').difference === -0.4186, r1.comparison.diff('accuracy'));
ok('results/backend: recommendationText from comparison.recommendation', typeof r1.comparison.recommendationText === 'string' && r1.comparison.recommendationText.length > 10, r1.comparison.recommendationText);
ok('results/backend: observations synthesized from ranking', r1.comparison.observations.length === 4, r1.comparison.observations.length);

/* ── 3. RESULTS: guide §4g mock shape (nested resource_usage, f1_score, top-level models) ── */
const mockResults = {
  experiment_id: 'EXP-000001', status: 'COMPLETED',
  models: {
    random_forest: { ...R('mocks/breast_cancer/model_result_classical.json') },
    vqc: { ...R('mocks/breast_cancer/model_result_quantum.json') }
  },
  comparison: { classification: 'TRADEOFF', observations: ['a','b'], recommendation_text: 'VQC shows higher sensitivity…' }
};
const r2 = adaptResults(mockResults);
ok('results/mock: f1_score mapped', r2.models.random_forest.metrics.f1 === 0.963, r2.models.random_forest.metrics);
ok('results/mock: pr_auc present', r2.models.random_forest.metrics.pr_auc === 0.9957, r2.models.random_forest.metrics.pr_auc);
ok('results/mock: training_time_seconds mapped', r2.models.random_forest.resources.trainingTime === 0.134, r2.models.random_forest.resources);
ok('results/mock: quantum_metrics → gate_count 142', r2.models.vqc.quantum.gateCount === 142, r2.models.vqc.quantum);
ok('results/mock: classification TRADEOFF kept', r2.comparison.classification === 'TRADEOFF', r2.comparison.classification);

/* ── 4. PROFILE: nested mock vs flat backend ── */
const p1 = adaptProfile(R('mocks/breast_cancer/dataset_profile.json'));
ok('profile/mock: rows 569 from dimensions', p1.rows === 569, p1.rows);
ok('profile/mock: target from target.candidate', p1.target === 'diagnosis', p1.target);
ok('profile/mock: missing.total', p1.missing.total === 0 && p1.missing.pct === 0, p1.missing);
const p2 = adaptProfile(real.results.dataset_profile); // flat, and has class_imbalance_ratio in the stored object
ok('profile/backend: rows 303-ish numeric', typeof p2.rows === 'number' && p2.rows > 0, p2.rows);
ok('profile/backend: featureCount from columns[]', p2.featureCount === (real.results.dataset_profile.columns?.length ?? 0), p2.featureCount);
ok('profile/backend: columns[] parsed to rows', p2.columns.length > 0 && p2.columns[0].name !== undefined, p2.columns[0]);
ok('profile/backend: imbalanceRatio present in stored profile', p2.imbalanceRatio !== undefined, p2.imbalanceRatio);
ok('profile/backend: name field used (not dataset_name)', typeof p2.name === 'string' && p2.name.length > 0, p2.name);

/* ── 5. VALIDATION: 12-section mock vs 6-field backend ── */
const v1 = adaptValidation(R('mocks/breast_cancer/validation_report.json'));
ok('validation/mock: passed from PASS_WITH_WARNINGS', v1.passed === true, v1);
ok('validation/mock: qualityScore 90', v1.qualityScore === 90, v1.qualityScore);
ok('validation/mock: imbalance ratio 1.68', v1.imbalance?.ratio === 1.68, v1.imbalance);
ok('validation/mock: warnings objects → strings', v1.warnings.every(w => typeof w === 'string'), v1.warnings[0]);
const v2 = adaptValidation({ is_valid: true, issues: [], warnings: ['low rows'], ready_for_ml: true, needs_target_selection: false, details: {} });
ok('validation/backend: readyForMl true', v2.readyForMl === true, v2);
ok('validation/backend: qualityScore null (not faked)', v2.qualityScore === null, v2.qualityScore);

/* ── 6. EXPLANATION: mock array-shape vs backend dict-shape ── */
const e1 = adaptExplanation(R('mocks/breast_cancer/explanation.json'));
ok('explain/mock: per-sample feature_importance used (8, negative effect kept)', e1.importance.length === 8 && e1.importance[0].effect === 'negative', e1.importance.length);
ok('explain/mock: globalImportance separate (10 items)', e1.globalImportance.length === 10, e1.globalImportance.length);
ok('explain/mock: prediction available', e1.available.prediction === true && e1.prediction.score === 0.02, e1.prediction);
ok('explain/mock: circuit qubits', e1.circuit.qubits === 8, e1.circuit);
const beExpl = { // per experiments.py:425-586
  experiment_id: 'EXP-279AE34B', explainability_method: 'Gini importance …',
  models_explained: ['random_forest', 'vqc'],
  global_importance: { random_forest: [ { feature_name: 'PC1', feature_index: 0, importance: 0.3045, rank: 1 } ] },
  quantum_circuit_info: { qubits: 8, n_layers: 2, n_params: 32, circuit_depth: 56, encoding_method: 'angle_encoding',
    backend_type: 'local_simulator (default.qubit)', feature_to_qubit_mapping: { PC1: 'qubit_0' },
    measured_qubits: [0], measurement: 'PauliZ(qubit_0)', gate_count_estimate: 120,
    shots_per_execution: 1024, total_circuit_executions: 15200, circuit_diagram: '  Qubits: 8' },
  pipeline_trace: [ { phase: 'Phase 1', component: 'Dataset Ingestion', artifact: 'DS-1' } ],
  warnings: ['w1','w2','w3','w4','w5'], generated_at: '2026-09-27T00:00:00Z'
};
const e2 = adaptExplanation(beExpl);
ok('explain/backend: global_importance dict-of-arrays unwrapped', e2.importance.length === 1 && e2.importance[0].name === 'PC1', e2.importance);
ok('explain/backend: quantum_circuit_info normalised', e2.circuit.depth === 56 && e2.circuit.gateCount === 120 && e2.circuit.executions === 15200, e2.circuit);
ok('explain/backend: 5 warnings passed through', e2.warnings.length === 5, e2.warnings.length);
ok('explain/backend: prediction unavailable → flag false (UI shows pending chip, not fake)', e2.available.prediction === false, e2.available);
ok('explain/backend: trace mapped', e2.trace[0].detail === 'DS-1', e2.trace);

const e3 = adaptExplanation({ global_importance: { PC1: 0.4, PC2: -0.2 } });
ok('explain/alt: plain dict of numbers still maps + negative detected', e3.importance.length === 2 && e3.importance[1].effect === 'negative', e3.importance);

/* ── 7. RECOMMENDATION colors: only real backend values ── */
const rec1 = adaptRecommendation({ decision: 'QUANTUM_PARITY', best_model: 'vqc', reasoning: ['r'], confidence: 'low',
  metrics_summary: { quantum: { accuracy: 0.32 }, classical_best: { accuracy: 0.74 } }, trade_offs: { runtime: { quantum_slower: true, ratio: 1442 } } });
ok('rec/backend: QUANTUM_PARITY → cyan', rec1.color === 'var(--cyan-primary)', rec1.color);
ok('rec/backend: confidence low kept', rec1.confidence === 'low', rec1.confidence);
const rec2 = adaptRecommendation(R('mocks/breast_cancer/recommendation.json'), {});
ok('rec/mock: TRADEOFF → warning orange', rec2.color === 'var(--warning-color)', rec2.color);
const rec3 = adaptRecommendation({ decision: 'CLASSICAL_PREFERRED' }, {});
ok('rec/backend: CLASSICAL_PREFERRED → red', rec3.color === 'var(--error-color)', rec3.color);

/* ── 8. QUANTUM adapter standalone ── */
ok('quantum: shots alias shots_per_execution', adaptQuantum({ shots_per_execution: 1024 }).shots === 1024, null);
ok('quantum: null stays null', adaptQuantum(null) === null, adaptQuantum({}));

/* ── 9. DATASET LIST (backend has no total / has_profile) ── */
const dl = adaptDatasetList({ datasets: [{ id: 'DS-ABC', name: 'breast_cancer', rows: 569, columns: ['a','b'], size_mb: 0.12, loaded_at: '2026-09-26T09:00:00' }] });
ok('list: total derived from length', dl.total === 1, dl.total);
ok('list: id from `id`', dl.datasets[0].id === 'DS-ABC', dl.datasets[0]);
ok('list: featureCount from columns array', dl.datasets[0].featureCount === 2, dl.datasets[0]);
ok('list: hasProfile null (not guessed)', dl.datasets[0].hasProfile === null, dl.datasets[0]);

/* ── 10. RESOURCES + ERROR ── */
const res = adaptResources({ system_resources: { cpu_percent: 0, memory_mb: 194.5, peak_memory_mb: 191.09, elapsed_time: 130.7 }, quantum_resources: null });
ok('resources: peakMemory mapped', res.peakMemoryMb === 191.09, res);
ok('resources: quantum null kept', res.quantum === null, res.quantum);
const err = adaptError({ response: { status: 400, data: { detail: 'Experiment not completed. Current status: created' } } });
ok('error: detail string surfaced', err.status === 400 && err.message.startsWith('Experiment not completed'), err);
const err2 = adaptError({ code: 'ERR_NETWORK' });
ok('error: network hint added', err2.hint?.includes('VITE_MOCK'), err2);

console.log(fails === 0 ? '\n✅ ALL PASS' : `\n❌ ${fails} FAILED`);
process.exit(fails === 0 ? 0 : 1);
