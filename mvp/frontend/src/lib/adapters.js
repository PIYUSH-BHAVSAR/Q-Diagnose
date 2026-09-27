// src/lib/adapters.js
// Normalise every backend response into ONE shape the pages render.
// Mocks/contracts shape (guide_naeem.md §4) and mvp/backend's real shape both land here,
// so pages never read raw JSON and MOCK_MODE=false cannot break a screen.

import { pick, up, STAGE_ALIASES, METRIC_COLUMNS, decisionColor } from './fieldMap.js';

/* ── Datasets ─────────────────────────────────────────────────────────── */

// GET /api/datasets → {datasets:[…]} (no `total`, keys are id/name/rows/columns/size_mb)
// guide §4b           → {datasets:[{dataset_id, display_id, has_profile…}], total}
export const adaptDatasetList = (raw) => ({
  total: raw?.total ?? (raw?.datasets?.length ?? 0),
  datasets: (raw?.datasets ?? []).map(adaptDataset)
});

export function adaptDataset(d = {}) {
  return {
    id: pick(d, ['dataset_id', 'id', 'display_id']),
    displayId: pick(d, ['display_id', 'name', 'filename']),
    display: pick(d, ['name', 'display_id', 'filename']),
    filename: d.filename ?? null,
    rows: d.rows ?? null,
    featureCount: Array.isArray(d.columns) ? d.columns.length : pick(d, ['columns'], null),
    sizeMb: d.size_mb ?? (d.file_size_bytes ? d.file_size_bytes / 1048576 : null),
    status: up(pick(d, ['status'], 'REGISTERED')),
    hasProfile: d.has_profile ?? null,
    uploadedAt: pick(d, ['upload_timestamp', 'loaded_at'], null),
    storagePath: d.storage_path ?? d.path ?? null
  };
}

// profile: mock = nested (dimensions/features/target/missing_values) | backend = flat
export const adaptProfile = (p = {}) => {
  const columnsArr = Array.isArray(p.columns) ? p.columns : [];
  return {
    datasetId: p.dataset_id,
    name: pick(p, ['name', 'dataset_name'], p.dataset_id ?? 'Dataset'),
    rows: p.rows ?? p.dimensions?.rows ?? 0,
    featureCount: columnsArr.length || p.dimensions?.columns || 0,
    numerical: p.numerical_columns_count ?? p.features?.numerical ?? 0,
    categorical: p.categorical_columns_count ?? p.features?.categorical ?? 0,
    target: p.recommended_target ?? p.target?.candidate ?? null,
    targetCandidates: p.target_candidates ?? (p.target?.candidate ? [p.target.candidate] : []),
    task: p.is_binary_classification ? 'BINARY_CLASSIFICATION' : (p.task?.candidate ?? 'UNKNOWN'),
    missing: {
      total: p.missing_values_total ?? p.missing_values?.total ?? 0,
      pct: p.missing_percentage ?? p.missing_values?.percentage ?? 0,
      byColumn: p.missing_values?.by_column ?? {}
    },
    duplicates: p.duplicate_rows ?? p.duplicates?.candidate_count ?? 0,
    classDistribution: p.class_distribution ?? {},
    isBinary: p.is_binary_classification ?? Object.keys(p.class_distribution ?? {}).length === 2,
    imbalanceRatio: p.class_imbalance_ratio ?? null,
    warnings: p.warnings ?? [],
    status: up(pick(p, ['status'], 'PROFILED')),
    profiledAt: p.profiled_at ?? null,
    columns: columnsArr.map((c) => ({
      name: c.name,
      dtype: c.dtype ?? (c.is_numeric ? 'numeric' : 'categorical'),
      numeric: c.is_numeric ?? null,
      missing: c.missing_count ?? 0,
      unique: c.unique_count ?? null,
      isTargetCandidate: !!c.is_target_candidate
    }))
  };
};

// validate: mock = 12-section validation_report.json | backend = 6 fields
export const adaptValidation = (v = {}) => {
  const issues = v.critical_issues?.length ? v.critical_issues : (v.issues ?? []);
  const warnings = (v.warnings ?? []).map((w) => (typeof w === 'string' ? w : w?.message ?? String(w)));
  const passed = v.validation_status
    ? String(v.validation_status).startsWith('PASS')
    : (v.ready_for_ml ?? v.is_valid ?? false);
  return {
    passed,
    readyForMl: v.ready_for_ml ?? (passed && issues.length === 0),
    needsTargetSelection: v.needs_target_selection ?? (v.target_validation?.status === 'WARNING'),
    qualityScore: v.quality_score ?? null,
    targetColumn: v.target_validation?.target_column ?? null,
    imbalance: v.class_balance
      ? { ratio: v.class_balance.imbalance_ratio, minorityPct: v.class_balance.minority_percentage,
          severity: v.class_balance.severity }
      : null,
    issues: [].concat(issues).map((i) => (typeof i === 'string' ? i : i?.message ?? String(i))),
    warnings,
    details: v.details ?? {}
  };
};

/* ── Experiment status (polling) ────────────────────────────────────────── */
// mock/guide = FLAT {status:'RUNNING', stage, progress:0.67, elapsed_seconds, circuit_executions…}
// backend experiments.py:259-266 = {status:'running_quantum', progress:{stage,progress,message}}
export const adaptStatus = (raw = {}) => {
  const nested = raw.progress && typeof raw.progress === 'object' ? raw.progress : {};
  const stageRaw = String(pick(raw, ['stage'], nested.stage) ?? '');
  const startedMs = raw.started_at ? Date.parse(raw.started_at) : null;
  const completedMs = raw.completed_at ? Date.parse(raw.completed_at) : null;
  const status = up(pick(raw, ['status'], ''));
  return {
    experimentId: raw.experiment_id ?? null,
    status,
    stage: STAGE_ALIASES[stageRaw.toLowerCase()] ?? (stageRaw || status.toLowerCase()),
    progress: typeof raw.progress === 'number' ? raw.progress
      : (typeof nested.progress === 'number' ? nested.progress : 0),
    message: pick(raw, ['message'], nested.message) ?? '',
    elapsedSeconds: raw.elapsed_seconds
      ?? (startedMs ? (((completedMs ?? Date.now()) - startedMs) / 1000) : null),
    estimatedRemaining: raw.estimated_remaining_seconds ?? null,
    circuitExecutions: pick(raw, ['circuit_executions', 'circuit_executions_so_far'],
      nested.circuit_executions ?? 0) ?? 0,
    currentModel: raw.current_model ?? null,
    completedModels: raw.completed_models ?? [],
    epoch: raw.current_epoch ?? null,
    totalEpochs: raw.total_epochs ?? null,
    error: pick(raw, ['error_message', 'error'], null),
    resourceSnapshot: raw.resource_snapshot ?? null,
    startedAt: raw.started_at ?? null,
    completedAt: raw.completed_at ?? null,
    isRunning: !['COMPLETED', 'FAILED'].includes(status),
    isCompleted: status === 'COMPLETED',
    isFailed: status === 'FAILED'
  };
};

/* ── Results ────────────────────────────────────────────────────────────── */
// backend nests everything under `results`; guide §4g puts models at top level
export const adaptResults = (raw = {}) => {
  const r = raw.results ?? raw;
  const models = {};
  for (const [name, m] of Object.entries(r?.models ?? {})) {
    const mt = m.metrics ?? {};
    const ru = m.resource_usage ?? {};
    const metrics = {};
    for (const col of METRIC_COLUMNS) {
      metrics[col.key] = pick(mt, col.src, null);
    }
    models[name] = {
      key: name,
      label: m.model_name ?? name,
      modelType: up(pick(m, ['model_type'], 'UNKNOWN')),
      status: up(pick(m, ['status'], 'COMPLETED')),
      metrics,
      resources: {
        trainingTime: ru.training_time_seconds ?? m.training_time ?? null,
        inferenceTime: ru.inference_time_seconds ?? m.inference_time ?? null,
        memoryMb: ru.memory_peak_mb ?? null,
        modelSizeMb: ru.model_size_mb ?? null
      },
      confusionMatrix: m.confusion_matrix ?? mt.confusion_matrix ?? null,
      featureImportance: mt.feature_importance ?? null,
      quantum: adaptQuantum(mt.quantum_resources ?? m.quantum_metrics ?? null)
    };
  }

  const c = r?.comparison ?? {};
  const qvc = c.quantum_vs_classical ?? {};
  const ranking = c.performance_ranking ?? [];
  return {
    experimentId: raw.experiment_id ?? null,
    status: up(pick(raw, ['status'], '')),
    models,
    ranking,
    preprocessing: r?.preprocessing ?? null,
    datasetProfile: r?.dataset_profile ?? adaptProfileless(r),
    resourceUsage: r?.resource_usage ?? null,
    comparison: {
      bestModel: c.best_model ?? null,
      bestClassical: c.best_classical ?? c.classical_best?.model_name ?? null,
      bestQuantum: c.best_quantum ?? c.quantum_best?.model_name ?? null,
      metricsComparison: c.metrics_comparison ?? {},
      diff: (metric) => qvc.metrics_diff?.[metric] ?? null,
      runtimeDiff: qvc.runtime_diff ?? null,
      resourceComparison: c.resource_comparison ?? null,
      observations: c.observations ?? ranking.map(
        (row) => `${row.model} — score ${row.score}, accuracy ${row.accuracy}, ${row.training_time}s`
      ),
      recommendationText: c.recommendation_text
        ?? (typeof c.recommendation === 'string' ? c.recommendation : c.recommendation?.reasoning?.join(' ')) ?? null,
      classification: c.classification ?? null
    }
  };
};

const adaptProfileless = (r) => (r?.dataset_profile ? r.dataset_profile : null);

/* ── Quantum resources ─────────────────────────────────────────────────── */
// mock quantum_metrics: qubits/gate_count/two_qubit_gates/total_circuit_executions
// backend quantum_resources: n_qubits/n_layers/n_params/circuit_depth/n_circuit_executions
export const adaptQuantum = (q) => {
  if (!q) return null;
  return {
    qubits: q.qubits ?? q.n_qubits ?? null,
    layers: q.n_layers ?? null,
    params: q.n_params ?? null,
    depth: q.circuit_depth ?? null,
    gateCount: q.gate_count ?? q.gate_count_estimate ?? null,
    twoQubitGates: q.two_qubit_gates ?? null,
    shots: q.shots ?? q.shots_per_execution ?? null,
    executions: q.total_circuit_executions ?? q.n_circuit_executions ?? null,
    trainingTime: q.training_time ?? null,
    backendType: q.backend_type ?? 'local_simulator',
    encoding: q.encoding_method ?? 'angle_encoding',
    mapping: q.feature_to_qubit_mapping ?? null,
    measuredQubits: q.measured_qubits ?? null,
    measurement: q.measurement ?? null,
    diagram: q.circuit_diagram ?? q.circuit_diagram_url ?? null
  };
};

export const adaptResources = (raw = {}) => ({
  cpuPercent: raw.system_resources?.cpu_percent ?? null,
  memoryMb: raw.system_resources?.memory_mb ?? null,
  peakMemoryMb: raw.system_resources?.peak_memory_mb ?? null,
  elapsedTime: raw.system_resources?.elapsed_time ?? null,
  quantum: adaptQuantum(raw.quantum_resources ?? raw.system_resources?.quantum_resources ?? null)
});

/* ── Explainability ─────────────────────────────────────────────────────── */
// guide/mock: prediction + feature_importance[] + global_importance[]
// backend experiments.py:562+: models_explained + global_importance{model:[…]} + quantum_circuit_info
export const adaptExplanation = (e = {}) => {
  // per-sample list wins when present (mock contract has feature_importance + global_importance;
  // mvp/backend only returns global_importance as a dict keyed by model)
  const toArray = (x) => {
    if (Array.isArray(x)) return x;
    if (x && typeof x === 'object') {
      const first = Object.values(x).find((v) => Array.isArray(v));
      if (first) return first;
      return Object.entries(x).map(([feature_name, importance]) => ({ feature_name, importance }));
    }
    return [];
  };
  const gi = e.feature_importance?.length ? e.feature_importance : e.global_importance;
  const importance = toArray(gi);
  const circuit = e.quantum_circuit_info ?? e.quantum_circuit_explanation ?? null;
  return {
    explanationId: e.explanation_id ?? null,
    method: e.explainability_method ?? null,
    modelsExplained: e.models_explained ?? [],
    importance: importance.map((f, i) => ({
      name: f.feature_name ?? f.name ?? `feature_${i}`,
      value: f.importance ?? f.value ?? 0,
      featureValue: f.feature_value ?? null,
      effect: f.effect ?? ((f.importance ?? 0) >= 0 ? 'positive' : 'negative'),
      rank: f.rank ?? i + 1
    })),
    globalImportance: toArray(e.global_importance).map((f, i) => ({
      name: f.feature_name ?? f.name ?? `feature_${i}`,
      value: f.importance ?? f.value ?? 0,
      effect: f.effect ?? ((f.importance ?? 0) >= 0 ? 'positive' : 'negative')
    })),
    circuit: circuit ? { ...adaptQuantum(circuit), raw: circuit } : null,
    trace: (e.pipeline_trace ?? []).map((t) => ({
      phase: t.phase ?? '', component: t.component ?? '',
      detail: pick(t, ['artifact', 'dimensions', 'method', 'backend'], '')
    })),
    warnings: e.warnings ?? [],
    prediction: e.prediction ?? null,          // ⚠️ backend does not return this yet
    sampleId: e.sample_id ?? null,
    decisionReason: e.model_decision_reason ?? null,
    generatedAt: e.generated_at ?? e.explanation_timestamp ?? null,
    available: { prediction: !!e.prediction, circuit: !!circuit, importance: importance.length > 0 }
  };
};

/* ── Recommendation / QUANTUM VALUE hero ────────────────────────────────── */
// mock recommendation.json: classification + classical_best/quantum_best
// backend GET …/recommendation: {decision, best_model, reasoning[], metrics_summary, trade_offs, confidence}
export const adaptRecommendation = (rec = {}, comparison = {}) => {
  const decision = up(pick(rec, ['decision', 'classification'], comparison?.classification ?? 'UNKNOWN'));
  return {
    decision,
    color: decisionColor(decision),
    bestModel: rec.best_model ?? comparison?.bestModel ?? null,
    confidence: rec.confidence ?? null,
    reasoning: rec.reasoning ?? [],
    tradeOffs: rec.trade_offs ?? null,
    summary: rec.metrics_summary ?? null,
    text: rec.recommendation_text ?? comparison?.recommendationText ?? null,
    classical: rec.classical_best ?? null,
    quantum: rec.quantum_best ?? null
  };
};

/* ── Reports ────────────────────────────────────────────────────────────── */
export const adaptReport = (raw = {}) => ({
  reportId: raw.report_id ?? null,
  experimentId: raw.experiment_id ?? null,
  status: up(pick(raw, ['status'], 'GENERATED')),
  path: pick(raw, ['report_path', 'path', 'cost_report_path'], null),
  generatedAt: raw.generated_at ?? null
});

/* ── Errors ─────────────────────────────────────────────────────────────── */
export const adaptError = (err) => {
  const detail = err?.response?.data?.detail;
  const message = typeof detail === 'string'
    ? detail
    : detail?.message ?? err?.message ?? 'Request failed';
  return {
    status: err?.response?.status ?? 0,
    message,
    hint: err?.code === 'ERR_NETWORK'
      ? 'Backend not reachable on :8000 — start it, or run with VITE_MOCK=1'
      : null
  };
};
