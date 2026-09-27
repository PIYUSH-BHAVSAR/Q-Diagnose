// src/services/api.js — the ONLY module that knows where data comes from.
// Modes (env): VITE_MOCK=1 → contract fixtures from ../../mocks (no server needed)
//             default     → real FastAPI through the Vite /api proxy, and if the
//                           server is unreachable it degrades to fixtures so the
//                           UI is never a blank screen during a demo.
// Pages never see raw JSON: every response goes through src/lib/adapters.js.

import axios from 'axios';
import { mockBackend, toBackendShape } from '@/lib/mockData.js';
import {
  adaptDatasetList, adaptProfile, adaptValidation, adaptStatus, adaptResults,
  adaptExplanation, adaptResources, adaptRecommendation, adaptReport, adaptError, adaptQuantum
} from '@/lib/adapters.js';

const API_BASE = '/api';
const wantMock = import.meta.env.VITE_MOCK === '1';
const USE_SHAPE = import.meta.env.VITE_SHAPE === 'backend' ? 'backend' : 'contract';

export const dataMode = { current: wantMock ? 'demo' : 'live' };
const listeners = new Set();
export const onDataMode = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
const setMode = (m) => { if (dataMode.current !== m) { dataMode.current = m; listeners.forEach((f) => f(m)); } };

const http = axios.create({ baseURL: API_BASE, timeout: 20000 });

async function call(kind, mockFn, liveFn, adapter) {
  if (wantMock) {
    const raw = mockFn();
    return adapter(USE_SHAPE === 'backend' ? toBackendShape(kind, raw) : raw);
  }
  try {
    const raw = await liveFn();
    return adapter(raw);
  } catch (err) {
    const e = adaptError(err);
    if (e.status === 0) {                       // network / backend down → demo data
      setMode('demo');
      try {
        const raw = mockFn();
        return adapter(USE_SHAPE === 'backend' ? toBackendShape(kind, raw) : raw);
      } catch { throw e; }
    }
    throw e;
  }
}

const passthrough = (x) => x;

/* ── system ─────────────────────────────────────────────────────────────── */
export const getHealth = () => call('health', () => mockBackend.health(), () => http.get('/health').then((r) => r.data), (d) => ({ status: d?.status ?? 'unknown', mode: dataMode.current }));
export const getConfig = () => call('config', () => mockBackend.config(), () => http.get('/config').then((r) => r.data), passthrough);

/* ── datasets ───────────────────────────────────────────────────────────── */
export const listDatasets = () => call('listDatasets', () => mockBackend.listDatasets(), () => http.get('/datasets').then((r) => r.data), adaptDatasetList);

export const getDataset = (id) => call('dataset', () => mockBackend.profile(id), () => http.get(`/datasets/${id}`).then((r) => r.data), passthrough);

export const getProfile = (id) => call('profile', () => mockBackend.profile(id), () => http.get(`/datasets/${id}/profile`).then((r) => r.data), adaptProfile);

export const validateDataset = (id, target) => call(
  'validation', () => mockBackend.validation(id),
  () => http.post(`/datasets/${id}/validate`, null, { params: { target_column: target ?? undefined } }).then((r) => r.data),
  adaptValidation
);

/** plan endpoint does not exist in the MVP backend yet → null in live mode */
export const getPlan = (datasetId) => call(
  'plan', () => mockBackend.plan(datasetId),
  () => http.get(`/datasets/${datasetId}/plan`).then((r) => r.data),
  passthrough
).catch(() => null);

export const uploadDataset = (file, name) => call(
  'upload', () => mockBackend.upload({ filename: file.name, size: file.size }),
  () => {
    const fd = new FormData();
    fd.append('file', file);
    if (name) fd.append('name', name);
    return http.post('/datasets/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data);
  },
  (d) => ({ datasetId: d.dataset_id ?? d.id, displayId: d.display_id ?? d.dataset_id, filename: d.filename, status: String(d.status ?? 'REGISTERED').toUpperCase(), warning: d.validation_warnings?.[0] ?? null })
);

/* ── experiments ────────────────────────────────────────────────────────── */
export const listExperiments = (filters = {}) => call(
  'listExperiments', () => mockBackend.listExperiments(),
  () => http.get('/experiments', { params: filters }).then((r) => r.data),
  (d) => {
    const rows = Array.isArray(d) ? d : (d.experiments ?? []);
    return rows.map((e) => ({
      id: e.experiment_id ?? e.id, datasetId: e.dataset_id ?? null, name: e.name ?? null,
      status: String(e.status ?? '').toUpperCase(), createdAt: e.created_at ?? null, completedAt: e.completed_at ?? null,
      circuitExecutions: Number.isFinite(e.circuit_executions) ? e.circuit_executions : null,
      elapsedSeconds: Number.isFinite(e.elapsed_seconds) ? e.elapsed_seconds : null,
      hasResults: !!(e.results && Object.keys(e.results).length)
    }));
  }
);

export const getExperiment = (id) => call(
  'get', () => mockBackend.get(id), () => http.get(`/experiments/${id}`).then((r) => r.data),
  (e) => ({ id: e.experiment_id ?? e.id, name: e.name ?? null, datasetId: e.dataset_id ?? null, status: String(e.status ?? '').toUpperCase(), createdAt: e.created_at ?? null, startedAt: e.started_at ?? null, config: e.configuration ?? null })
);

export const createExperiment = (datasetId, config = {}) => call(
  'create', () => mockBackend.create({ dataset_id: datasetId, name: config.name }),
  () => http.post('/experiments', { dataset_id: datasetId, ...config }).then((r) => r.data),
  (d) => ({ id: d.experiment_id ?? d.id, datasetId: d.dataset_id, status: String(d.status ?? 'CREATED').toUpperCase() })
);

export const runExperiment = (id) => call('run', () => mockBackend.run(id), () => http.post(`/experiments/${id}/run`).then((r) => r.data), passthrough);

export const getStatus = (id) => call('status', () => mockBackend.status(id), () => http.get(`/experiments/${id}/status`).then((r) => r.data), adaptStatus);

export const getResults = (id) => call('results', () => mockBackend.results(id), () => http.get(`/experiments/${id}/results`).then((r) => r.data), adaptResults);

export const getExplanation = (id) => call('explanation', () => mockBackend.explanation(id), () => http.get(`/experiments/${id}/explanation`).then((r) => r.data), adaptExplanation);

export const getResources = (id) => call('resources', () => mockBackend.resources(id), () => http.get(`/experiments/${id}/resources`).then((r) => r.data), adaptResources);

export const getRecommendation = (id, comparison) => call(
  'recommendation', () => mockBackend.recommendation(id),
  () => http.get(`/experiments/${id}/recommendation`).then((r) => r.data),
  (d) => adaptRecommendation(d, comparison)
);

export const getCost = (id) => call('cost', () => mockBackend.cost(id), async () => null, passthrough);

export const getConfusion = (id, model) => call('confusion', () => mockBackend.confusion(id, model), () => http.get(`/experiments/${id}/confusion-matrix/${model}`).then((r) => r.data), passthrough);

export const deleteExperiment = (id) => call('delete', () => mockBackend.remove(id), () => http.delete(`/experiments/${id}`).then((r) => r.data), passthrough);

export const getQuantumResources = (id) => getResources(id).then((r) => adaptQuantum(r?.quantum));

/* ── reports ────────────────────────────────────────────────────────────── */
export const generateReport = (id) => call('report', () => mockBackend.generateReport(id), () => http.post(`/reports/${id}`).then((r) => r.data), adaptReport);
export const listReports = () => call('reports', () => ({ reports: mockBackend.listReports() }), async () => ({ reports: null }), (d) => (d.reports ?? []).map((r) => adaptReport(r)));
export const reportDownloadUrl = (id) => (wantMock ? null : `${API_BASE}/reports/${id}/download`);

/* demo-only affordance: jumps the mock timeline to COMPLETED so a presentation can show
   results without sitting through 23 s of fake training. Never offered against a real run. */
export const canFastForward = () => wantMock || dataMode.current === 'demo';
export const fastForwardRun = (id) => {
  if (!canFastForward()) return Promise.reject(new Error('A real run cannot be skipped — poll /status until COMPLETED.'));
  mockBackend.complete(id);
  return Promise.resolve({ experiment_id: id, status: 'COMPLETED' });
};

export const api = {
  getHealth, getConfig, listDatasets, getDataset, getProfile, validateDataset, getPlan, uploadDataset,
  listExperiments, getExperiment, createExperiment, runExperiment, getStatus, getResults,
  getExplanation, getResources, getRecommendation, getCost, getConfusion, deleteExperiment,
  generateReport, listReports, reportDownloadUrl, canFastForward, fastForwardRun
};

export default api;
