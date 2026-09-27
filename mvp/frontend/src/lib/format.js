// src/lib/format.js — display formatting only (no ML logic anywhere in React)

export const nf = (v, digits = 0) =>
  Number.isFinite(v)
    ? v.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
    : '—';

export const int = (v) => (Number.isFinite(+v) ? (+v).toLocaleString('en-US') : '—');

export const score = (v) => (Number.isFinite(v) ? v.toFixed(4) : '—');

export const pct = (v, digits = 1) => (Number.isFinite(v) ? `${(v * 100).toFixed(digits)}%` : '—');

export const pctRaw = (v, digits = 1) => (Number.isFinite(v) ? `${v.toFixed(digits)}%` : '—');

export const dur = (sec) => {
  if (!Number.isFinite(sec)) return '—';
  if (sec < 1) return `${(sec * 1000).toFixed(0)} ms`;
  if (sec < 60) return `${sec.toFixed(1)} s`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  if (m < 60) return `${m}m ${String(s).padStart(2, '0')}s`;
  return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`;
};

export const mb = (v) => (Number.isFinite(v) ? `${v < 1024 ? v.toFixed(1) : (v / 1024).toFixed(2)} ${v < 1024 ? 'MB' : 'GB'}` : '—');

export const bytes = (n) => {
  if (!Number.isFinite(n)) return '—';
  const u = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i += 1; }
  return `${v.toFixed(v < 10 && i > 0 ? 2 : 0)} ${u[i]}`;
};

export const shortTime = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(+d)) return '—';
  return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

export const ago = (iso) => {
  if (!iso) return '—';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (!Number.isFinite(diff)) return '—';
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

export const titleize = (s) =>
  String(s ?? '')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

/** status → { label, kind } where kind maps to .pill.ok/.warn/.err/… */
export const statusMeta = (status) => {
  const s = String(status ?? '').toUpperCase();
  if (s === 'COMPLETED' || s === 'REGISTERED' || s === 'PASS') return { label: 'Completed', kind: 'ok', tone: 'ok' };
  if (s === 'FAILED' || s === 'REJECTED') return { label: 'Failed', kind: 'err', tone: 'err' };
  if (s.includes('QUANTUM')) return { label: 'Running circuits', kind: 'quantum', tone: 'quantum' };
  if (s) return { label: titleize(s), kind: 'warn', tone: 'warn' };
  return { label: 'Unknown', kind: '', tone: 'muted' };
};

export const modelLabel = (key) =>
  ({
    logistic_regression: 'Logistic Regression',
    svm: 'SVM (RBF)',
    random_forest: 'Random Forest',
    vqc: 'VQC (quantum)'
  }[key] || titleize(key));

export const isQuantumModel = (m) => String(m?.modelType ?? '').toUpperCase() === 'QUANTUM' || m?.key === 'vqc';

export const safeSlice = (s, n = 64) => (s && s.length > n ? `${s.slice(0, n - 1)}…` : s || '');
