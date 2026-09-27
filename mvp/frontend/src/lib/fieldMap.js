// src/lib/fieldMap.js
// Single place where guide/mock shapes and the real MVP backend shapes meet.
// Do NOT put ML logic here — only field-name normalisation.

export const up = (s) => String(s ?? '').toUpperCase();

export const pick = (obj, keys, fallback = null) => {
  for (const k of [].concat(keys)) {
    const v = obj?.[k];
    if (v !== undefined && v !== null) return v;
  }
  return fallback;
};

// stage drift: contracts/experiment_status.json v1.1  vs  executor.py:115-264  vs  guide_naeem.md §4f
export const STAGE_ALIASES = {
  not_started: 'preprocessing',
  loading: 'preprocessing',
  profiling: 'preprocessing',
  validating: 'preprocessing',
  preprocessing: 'preprocessing',
  classical: 'classical_training',
  classical_training: 'classical_training',
  running_classical: 'classical_training',
  quantum: 'quantum_training',
  quantum_training: 'quantum_training',
  running_quantum: 'quantum_training',
  benchmarking: 'benchmarking',
  finalizing: 'benchmarking',
  explaining: 'explaining',
  completed: 'completed'
};

export const STAGES = [
  'preprocessing',
  'classical_training',
  'quantum_training',
  'benchmarking',
  'explaining',
  'completed'
];

// contracts use UPPERCASE, mvp/backend/experiments/manager.py:16-24 uses lowercase values
export const RUNNING_STATES = new Set([
  'CREATED', 'VALIDATING', 'PREPROCESSING',
  'RUNNING_CLASSICAL', 'RUNNING_QUANTUM',
  'BENCHMARKING', 'EXPLAINING'
]);

// [display key used by UI, label, candidate source keys (mock first, then backend)]
export const METRIC_COLUMNS = [
  { key: 'accuracy',    label: 'Accuracy',    src: ['accuracy'] },
  { key: 'precision',   label: 'Precision',   src: ['precision'] },
  { key: 'recall',      label: 'Recall',      src: ['recall'] },
  { key: 'specificity', label: 'Specificity', src: ['specificity'] },
  { key: 'f1',          label: 'F1 Score',    src: ['f1_score', 'f1'] },
  { key: 'roc_auc',     label: 'ROC-AUC',     src: ['roc_auc', 'auc', 'roc_auc_score'] },   // legacy /metrics says "auc" 
  { key: 'pr_auc',      label: 'PR-AUC',      src: ['pr_auc', 'average_precision'] } // ⚠️ absent in both today → renders '—'
];

// decision labels actually produced by mvp/backend/benchmarking/recommendation.py:177-199
// (guide §8 also names TRADEOFF / CLASSICAL_ADVANTAGE — those strings do not exist in the backend)
export const DECISION_COLORS = {
  QUANTUM_ADVANTAGE:  'var(--success-color)',
  QUANTUM_PARITY:     'var(--cyan-primary)',
  PARITY:             'var(--cyan-primary)',
  TRADEOFF:           'var(--warning-color)',
  CLASSICAL_PREFERRED:'var(--error-color)',
  CLASSICAL_ADVANTAGE:'var(--error-color)'
};

export const decisionColor = (d) =>
  DECISION_COLORS[up(d)] ?? 'var(--text-secondary)';
