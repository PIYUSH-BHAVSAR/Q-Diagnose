// src/lib/mockData.js
// A tiny in-memory stand-in for the FastAPI backend, built from the repo's own
// contract fixtures (../../../../mocks/<dataset>/*.json). This is what makes
// `MOCK_MODE` real: every screen — including live progress polling — works with
// no server running, and with VITE_SHAPE=backend the SAME data is served in the
// mvp/backend response shape so the adapter layer is exercised end-to-end.

import { STAGE_ALIASES } from './fieldMap.js';

const files = import.meta.glob('../../../../mocks/*/*.json', { eager: true, import: 'default' });

const bundle = {};
for (const [p, json] of Object.entries(files)) {
  const m = p.match(/mocks\/([^/]+)\/([^/]+)\.json$/);
  if (!m) continue;
  (bundle[m[1]] ||= {})[m[2]] = json;
}

export const MOCK_DATASETS = ['breast_cancer', 'heart_disease', 'parkinsons', 'diabetes']
  .filter((k) => bundle[k]);

const DATASET_META = {
  breast_cancer: { label: 'Breast Cancer Wisconsin', rows: 569, size: 125204 },
  heart_disease: { label: 'Heart Disease UCI', rows: 303, size: 88120 },
  parkinsons: { label: "Parkinson's Disease", rows: 197, size: 41340 },
  diabetes: { label: 'Pima Indians Diabetes', rows: 768, size: 76210 }
};

const nowISO = (offsetMs = 0) => new Date(Date.now() + offsetMs).toISOString();
const hex = (n) => Math.abs(Math.sin(n) * 1e9).toString(16).slice(0, 8).toUpperCase();

const clone = (o) => JSON.parse(JSON.stringify(o));

/** classical metric sets for the 3 classical models, derived from the fixture */
const CLASSICAL_VARIATION = {
  logistic_regression: { accuracy: -0.031, precision: -0.028, recall: -0.047, specificity: -0.021, f1_score: -0.036, roc_auc: -0.024, pr_auc: -0.031, train: 2.3 },
  svm: { accuracy: -0.014, precision: -0.009, recall: -0.021, specificity: -0.006, f1_score: -0.017, roc_auc: -0.009, pr_auc: -0.013, train: 8.4 },
  random_forest: { accuracy: 0, precision: 0, recall: 0, specificity: 0, f1_score: 0, roc_auc: 0, pr_auc: 0, train: 42.7 }
};

const clamp01 = (v) => Math.max(0, Math.min(1, v));

function modelFor(dsKey, modelName) {
  const base = bundle[dsKey].model_result_classical;
  if (modelName === 'vqc') return { ...clone(bundle[dsKey].model_result_quantum), model_type: 'QUANTUM' };
  const v = CLASSICAL_VARIATION[modelName];
  const m = clone(base);
  m.model_name = modelName === 'svm' ? 'SVM' : modelName === 'logistic_regression' ? 'LogisticRegression' : 'RandomForest';
  for (const k of Object.keys(v)) {
    if (k === 'train') { m.resource_usage.training_time_seconds = v.train; continue; }
    m.metrics[k] = Number(clamp01((m.metrics[k] ?? 0) + v[k]).toFixed(4));
  }
  return m;
}

/* ── timeline: makes the Progress tab genuinely animate in mock mode ────── */
export const TIMELINE = [
  { stage: 'preprocessing', secs: 3 },
  { stage: 'classical_training', secs: 6 },
  { stage: 'quantum_training', secs: 9 },
  { stage: 'benchmarking', secs: 3 },
  { stage: 'explaining', secs: 2 },
  { stage: 'completed', secs: 0 }
];
const TOTAL_SECS = TIMELINE.reduce((a, s) => a + s.secs, 0);
const CLASSICAL_ORDER = ['logistic_regression', 'svm', 'random_forest'];

function statusAt(startedAt, experimentId, circuitTotal) {
  const elapsed = Math.max(0, (Date.now() - new Date(startedAt).getTime()) / 1000);
  let acc = 0;
  let current = TIMELINE[TIMELINE.length - 1];
  let doneBefore = 0;
  for (const step of TIMELINE) {
    if (elapsed < acc + step.secs || step === TIMELINE[TIMELINE.length - 1]) { current = step; break; }
    acc += step.secs;
    doneBefore += step.secs;
  }
  const progress = Math.min(1, elapsed / TOTAL_SECS);
  const done = progress >= 1;
  const inClassical = current.stage === 'classical_training';
  const classicalDone =
    current.stage === 'quantum_training' || current.stage === 'benchmarking' || current.stage === 'explaining' || done
      ? [...CLASSICAL_ORDER]
      : inClassical
        ? CLASSICAL_ORDER.slice(0, Math.min(3, Math.floor((elapsed - doneBefore) / 2) + 0))
        : [];
  return {
    experiment_id: experimentId,
    status: done ? 'COMPLETED' : current.stage === 'completed' ? 'RUNNING' : 'RUNNING',
    stage: current.stage,
    progress: Number(progress.toFixed(3)),
    message: done
      ? 'Experiment completed successfully'
      : current.stage === 'quantum_training'
        ? `Training VQC — ${Math.round(Math.min(1, (elapsed - doneBefore) / current.secs) * 30)}/30 epochs`
        : current.stage === 'classical_training'
          ? `Training ${modelLabelSafe(classicalDone[classicalDone.length - 1] ?? CLASSICAL_ORDER[0])}`
          : `${current.stage.replace(/_/g, ' ')}…`,
    started_at: startedAt,
    elapsed_seconds: Number(elapsed.toFixed(1)),
    estimated_remaining_seconds: done ? 0 : Number(Math.max(0, TOTAL_SECS - elapsed).toFixed(1)),
    current_model: done ? null : inClassical ? CLASSICAL_ORDER[classicalDone.length] ?? null : current.stage === 'quantum_training' ? 'vqc' : null,
    completed_models: classicalDone,
    circuit_executions: done ? circuitTotal : current.stage === 'quantum_training' ? Math.round((elapsed - doneBefore) / current.secs * circuitTotal) : 0,
    current_epoch: current.stage === 'quantum_training' ? Math.round(Math.min(1, (elapsed - doneBefore) / current.secs) * 30) : null,
    total_epochs: current.stage === 'quantum_training' ? 30 : null,
    error_message: null,
    resource_snapshot: { cpu_percent: 61.4 + Math.round(Math.sin(elapsed) * 9), memory_mb: 986.4 }
  };
}
const modelLabelSafe = (k) => ({ logistic_regression: 'Logistic Regression', svm: 'SVM', random_forest: 'Random Forest', vqc: 'VQC' }[k] ?? k);

/* ── the fake server ────────────────────────────────────────────────────── */
const uid = (() => { let i = 0; return (p) => `${p}-${hex(++i * 7919)}`; })();

const state = {
  datasets: MOCK_DATASETS.map((key, i) => {
    const meta = DATASET_META[key] ?? { label: key, rows: 100, size: 10000 };
    const id = `DS-${hex(i * 31 + 5)}`;
    return {
      dataset_id: id, display_id: `DS-${String(i + 1).padStart(6, '0')}`, key,
      filename: `${key}.csv`, container_type: 'CSV', file_size_bytes: meta.size,
      status: 'REGISTERED', upload_timestamp: nowISO(-(i + 1) * 3.7e6), has_profile: true,
      name: meta.label, label: meta.label, rows: meta.rows
    };
  }),
  experiments: {}
};

const resultsFor = (dsKey, experimentId) => {
  const models = {};
  for (const name of [...CLASSICAL_ORDER, 'vqc']) models[name] = modelFor(dsKey, name);
  const rec = clone(bundle[dsKey].recommendation ?? {});
  return {
    experiment_id: experimentId,
    status: 'COMPLETED',
    models,
    comparison: {
      classification: rec.classification ?? 'TRADEOFF',
      classical_best: rec.classical_best, quantum_best: rec.quantum_best,
      performance_differences: rec.performance_differences, resource_comparison: rec.resource_comparison,
      observations: rec.observations ?? [], recommendation_text: rec.recommendation_text ?? ''
    }
  };
};

export const mockBackend = {
  health: () => ({ status: 'healthy', mode: 'mock' }),
  config: () => ({ quantum: { model: 'vqc', max_qubits: 8, layers: 2, shots: 1024 }, experiment: { random_state: 42, test_size: 0.2 }, classical_models: CLASSICAL_ORDER }),

  listDatasets: () => ({ datasets: state.datasets, total: state.datasets.length }),

  upload({ filename, size }) {
    const id = uid('DS');
    const row = {
      dataset_id: id, display_id: `DS-${String(state.datasets.length + 1).padStart(6, '0')}`,
      key: 'breast_cancer', filename, container_type: 'CSV', file_size_bytes: size ?? 0,
      status: 'REGISTERED', upload_timestamp: nowISO(), has_profile: true,
      name: filename?.replace(/\.csv$/i, '') ?? id, label: filename?.replace(/\.csv$/i, '') ?? id
    };
    state.datasets.unshift(row);
    return { ...row, sha256: hex(Date.now() % 99991).toLowerCase(), storage_path: `datasets/${row.display_id}/raw/original.csv`, is_duplicate: false, duplicate_of: null, validation_warnings: [], rejection_reason: null };
  },

  profile(datasetId) {
    const ds = state.datasets.find((d) => d.dataset_id === datasetId) ?? state.datasets[0];
    const p = clone(bundle[ds.key].dataset_profile ?? {});
    p.dataset_id = datasetId;
    p.dimensions = { ...p.dimensions, rows: DATASET_META[ds.key]?.rows ?? p.dimensions?.rows };
    return p;
  },

  validation(datasetId) {
    const ds = state.datasets.find((d) => d.dataset_id === datasetId) ?? state.datasets[0];
    return clone(bundle[ds.key].validation_report ?? { validation_status: 'PASS', quality_score: 100 });
  },

  plan(datasetId) {
    const ds = state.datasets.find((d) => d.dataset_id === datasetId) ?? state.datasets[0];
    const c = clone(bundle[ds.key].experiment_config ?? {});
    c.dataset_id = datasetId;
    return c;
  },

  listExperiments: () => ({
    experiments: Object.values(state.experiments).sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
  }),

  create({ dataset_id, name }) {
    const ds = state.datasets.find((d) => d.dataset_id === dataset_id) ?? state.datasets[0];
    const id = uid('EXP');
    state.experiments[id] = {
      experiment_id: id, dataset_id: ds.dataset_id, dataset_key: ds.key,
      name: name ?? `${ds.label} · hybrid benchmark`, status: 'CREATED', stage: 'preprocessing',
      created_at: nowISO(), started_at: null, completed_at: null, error_message: null
    };
    return { experiment_id: id, dataset_id: ds.dataset_id, status: 'CREATED' };
  },

  get(id) {
    const e = state.experiments[id];
    if (!e) throw mockError(404, `Experiment not found: ${id}`);
    return e;
  },

  run(id) {
    const e = this.get(id);
    e.started_at = e.started_at ?? nowISO();
    e.status = 'RUNNING';
    return { experiment_id: id, status: 'started' };
  },

  status(id) {
    const e = this.get(id);
    if (!e.started_at) return { experiment_id: id, status: e.status, stage: e.stage, progress: 0, message: 'Queued', completed_models: [], circuit_executions: 0, error_message: null };
    const s = statusAt(e.started_at, id, bundle[e.dataset_key].model_result_quantum?.quantum_metrics?.total_circuit_executions ?? 20475);
    e.status = s.status; e.stage = s.stage;
    e.completed_at = s.status === 'COMPLETED' ? (e.completed_at ?? nowISO()) : null;
    return s;
  },

  results(id) {
    const e = this.get(id);
    if (e.status !== 'COMPLETED') throw mockError(400, 'Experiment not completed.');
    return resultsFor(e.dataset_key, id);
  },

  explanation(id) {
    const e = this.get(id);
    return clone(bundle[e.dataset_key].explanation ?? { warnings: [] });
  },

  resources(id) {
    const e = this.get(id);
    const q = bundle[e.dataset_key].model_result_quantum?.quantum_metrics ?? null;
    return {
      system_resources: { cpu_percent: 58.2, memory_mb: 1012.4, peak_memory_mb: 1247.8, elapsed_time: TOTAL_SECS },
      quantum_resources: q
    };
  },

  cost(id) {
    const e = this.get(id);
    return clone(bundle[e.dataset_key].cost_report ?? {});
  },

  recommendation(id) {
    const e = this.get(id);
    return clone(bundle[e.dataset_key].recommendation ?? {});
  },

  confusion(id, model) {
    const e = this.get(id);
    const m = modelFor(e.dataset_key, model === 'vqc' ? 'vqc' : 'random_forest');
    return { model_name: model, matrix: m.confusion_matrix ?? [[0, 0], [0, 0]], labels: ['Negative', 'Positive'] };
  },

  remove(id) { delete state.experiments[id]; return { message: `${id} deleted` }; },

  /** jumps the mock timeline to the end — used by the demo and by tests */
  complete(id) {
    const e = this.get(id);
    e.started_at = new Date(Date.now() - (TOTAL_SECS + 2) * 1000).toISOString();
    return this.status(id);
  },

  generateReport(id) {
    this.get(id);
    return { report_id: `RPT-${id}`, experiment_id: id, status: 'GENERATED', report_path: `artifacts/reports/${id}_report.html`, generated_at: nowISO() };
  },

  listReports() {
    return Object.values(state.experiments)
      .filter((e) => e.status === 'COMPLETED')
      .map((e) => ({ report_id: `RPT-${e.experiment_id}`, experiment_id: e.experiment_id, name: e.name, generated_at: e.completed_at ?? nowISO(), size_kb: 42 + (e.experiment_id.length % 7) * 3 }));
  }
};

function mockError(status, detail) {
  const err = new Error(detail);
  err.response = { status, data: { detail } };
  return err;
}

/* ── VITE_SHAPE=backend → serve mvp/backend's actual response shapes ───────
   Same data, uglier keys. If the UI still renders, adapters.js is correct. */
export function toBackendShape(kind, data) {
  switch (kind) {
    case 'listDatasets':
      return {
        datasets: data.datasets.map((d) => ({
          id: d.dataset_id, name: d.label, filename: d.filename, rows: d.__rows ?? null,
          columns: Array.from({ length: 31 }, (_, i) => `col_${i}`), loaded_at: d.upload_timestamp, size_mb: d.file_size_bytes / 1048576
        }))
      };
    case 'profile': {
      const dims = data.dimensions ?? {};
      return {
        dataset_id: data.dataset_id, name: data.dataset_id, rows: dims.rows ?? 0,
        columns: Array.from({ length: 12 }, (_, i) => ({ name: `f_${i}`, dtype: 'float64', missing_count: 0, unique_count: 300, is_numeric: true, is_target_candidate: i === 11 })),
        numerical_columns_count: data.features?.numerical ?? 0, categorical_columns_count: data.features?.categorical ?? 0,
        missing_values_total: data.missing_values?.total ?? 0, missing_percentage: data.missing_values?.percentage ?? 0,
        duplicate_rows: data.duplicates?.candidate_count ?? 0, target_candidates: [data.target?.candidate], recommended_target: data.target?.candidate,
        is_binary_classification: true, class_distribution: data.class_distribution ?? {}, warnings: data.warnings ?? []
      };
    }
    case 'validation':
      return { is_valid: true, issues: [], warnings: (data.warnings ?? []).map((w) => w?.message ?? String(w)), ready_for_ml: true, needs_target_selection: false, details: {} };
    case 'status': {
      const stage = STAGE_ALIASES[String(data.stage ?? '').toLowerCase()] ?? data.stage;
      const back = { loading: 'preprocessing', profiling: 'preprocessing', validating: 'preprocessing', classical_training: 'classical', quantum_training: 'quantum', benchmarking: 'benchmarking', explaining: 'finalizing', completed: 'completed' }[stage] ?? stage;
      return {
        experiment_id: data.experiment_id,
        status: String(data.status ?? '').toLowerCase(),
        progress: { stage: back, progress: data.progress ?? 0, message: data.message ?? '' },
        started_at: data.started_at ?? null, completed_at: data.completed_at ?? null
      };
    }
    case 'results': {
      const models = {};
      for (const [k, m] of Object.entries(data.models ?? {})) {
        models[k] = {
          model_name: m.model_name, model_type: String(m.model_type ?? '').toLowerCase(),
          metrics: {
            accuracy: m.metrics?.accuracy, precision: m.metrics?.precision, recall: m.metrics?.recall,
            f1: m.metrics?.f1_score ?? m.metrics?.f1, specificity: m.metrics?.specificity, sensitivity: m.metrics?.recall,
            roc_auc: m.metrics?.roc_auc, confusion_matrix: m.confusion_matrix,
            feature_importance: m.model_name === 'RandomForest' ? Object.fromEntries(Array.from({ length: 8 }, (_, i) => [`PC${i + 1}`, +(0.3 - i * 0.02).toFixed(4)])) : undefined,
            quantum_resources: m.quantum_metrics ? { n_qubits: m.quantum_metrics.qubits, n_layers: 2, n_params: 32, shots: m.quantum_metrics.shots, circuit_depth: m.quantum_metrics.circuit_depth, n_circuit_executions: m.quantum_metrics.total_circuit_executions } : undefined
          },
          training_time: m.resource_usage?.training_time_seconds, inference_time: m.resource_usage?.inference_time_seconds
        };
      }
      const c = data.comparison ?? {};
      const keys = Object.keys(models);
      const ranking = keys.map((k) => ({ model: k, type: models[k].model_type, score: models[k].metrics.f1, accuracy: models[k].metrics.accuracy, recall: models[k].metrics.recall, roc_auc: models[k].metrics.roc_auc, training_time: models[k].training_time }));
      const best = ranking.reduce((a, b) => (b.score > a.score ? b : a), ranking[0]);
      const qRow = ranking.find((r) => r.type === 'quantum') ?? ranking[0];
      const metrics_diff = {};
      for (const mk of ['accuracy', 'recall', 'precision', 'roc_auc']) {
        metrics_diff[mk] = { classical: best[mk] ?? 0, quantum: qRow[mk] ?? 0, difference: (qRow[mk] ?? 0) - (best[mk] ?? 0), quantum_better: (qRow[mk] ?? 0) > (best[mk] ?? 0) };
      }
      return {
        experiment_id: data.experiment_id, status: 'completed',
        results: {
          models, resource_usage: { cpu_percent: 58.2, memory_mb: 1012.4, peak_memory_mb: 1247.8, elapsed_time: TOTAL_SECS, quantum_resources: null },
          comparison: {
            best_model: best.model, best_classical: best.model, best_quantum: 'vqc', performance_ranking: ranking,
            metrics_comparison: Object.fromEntries(keys.map((k) => [k, models[k].metrics])),
            runtime_comparison: Object.fromEntries(keys.map((k) => [k, models[k].training_time])),
            quantum_vs_classical: { classical_model: best.model, quantum_model: 'vqc', metrics_diff, runtime_diff: { classical: best.training_time, quantum: qRow.training_time, ratio: 17.8 }, quantum_resources: models.vqc?.metrics.quantum_resources },
            recommendation: c.recommendation_text ?? 'Classical is cheaper here.'
          }
        }
      };
    }
    case 'explanation':
      return {
        experiment_id: data.experiment_id ?? 'EXP', explainability_method: data.explainability_method,
        models_explained: ['random_forest', 'vqc'],
        global_importance: { random_forest: (data.feature_importance ?? []).map((f, i) => ({ feature_name: f.feature_name, feature_index: f.feature_index ?? i, importance: f.importance, rank: i + 1 })) },
        quantum_circuit_info: { ...(data.quantum_circuit_explanation ?? {}), n_layers: 2, n_params: 32, gate_count_estimate: 142, shots_per_execution: 1024, total_circuit_executions: 20475, backend_type: 'local_simulator (default.qubit)' },
        pipeline_trace: data.pipeline_trace ?? [], warnings: data.warnings ?? [], generated_at: data.explanation_timestamp ?? nowISO()
      };
    default:
      return data;
  }
}
