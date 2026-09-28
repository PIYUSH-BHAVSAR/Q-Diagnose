// src/services/api.js
// Single module that talks to the FastAPI backend through the Vite /api proxy.
// No mock fallback — always live. All responses go through src/lib/adapters.js.

import axios from 'axios';
import {
  adaptDatasetList, adaptProfile, adaptValidation, adaptStatus, adaptResults,
  adaptExplanation, adaptResources, adaptRecommendation, adaptReport, adaptError, adaptQuantum
} from '@/lib/adapters.js';

const API_BASE = '/api';

// Always live mode
export const dataMode = { current: 'live' };
const listeners = new Set();
export const onDataMode = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };

const http = axios.create({ baseURL: API_BASE, timeout: 30000 });

// Global error handler — normalise axios errors into { status, message, hint }
http.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(adaptError(err))
);

const passthrough = (x) => x;

async function live(liveFn, adapter) {
  const raw = await liveFn();
  return adapter(raw);
}

/* ── system ─────────────────────────────────────────────────────────────── */
export const getHealth = () =>
  live(() => http.get('/health').then((r) => r.data),
    (d) => ({ status: d?.status ?? 'unknown', mode: 'live' }));

export const getConfig = () =>
  live(() => http.get('/config').then((r) => r.data), passthrough);

/* ── datasets ───────────────────────────────────────────────────────────── */
export const listDatasets = () =>
  live(() => http.get('/datasets').then((r) => r.data), adaptDatasetList);

export const getDataset = (id) =>
  live(() => http.get(`/datasets/${id}`).then((r) => r.data), passthrough);

export const getProfile = (id) =>
  live(() => http.get(`/datasets/${id}/profile`).then((r) => r.data), adaptProfile);

export const validateDataset = (id, target) =>
  live(
    () => http.post(`/datasets/${id}/validate`, null, {
      params: { target_column: target ?? undefined }
    }).then((r) => r.data),
    adaptValidation
  );

// Plan endpoint not implemented in backend — always returns null
export const getPlan = (_datasetId) => Promise.resolve(null);

export const uploadDataset = (file, name) =>
  live(
    () => {
      const fd = new FormData();
      fd.append('file', file);
      if (name) fd.append('name', name);
      return http.post('/datasets/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).then((r) => r.data);
    },
    (d) => ({
      datasetId: d.dataset_id ?? d.id,
      displayId: d.display_id ?? d.dataset_id,
      filename:  d.filename,
      status:    String(d.status ?? 'REGISTERED').toUpperCase(),
      warning:   d.validation_warnings?.[0] ?? null
    })
  );

/* ── experiments ────────────────────────────────────────────────────────── */
export const listExperiments = (filters = {}) =>
  live(
    () => http.get('/experiments', { params: filters }).then((r) => r.data),
    (d) => {
      const rows = Array.isArray(d) ? d : (d.experiments ?? []);
      return rows.map((e) => ({
        id:                e.experiment_id ?? e.id,
        datasetId:         e.dataset_id ?? null,
        name:              e.name ?? null,
        status:            String(e.status ?? '').toUpperCase(),
        createdAt:         e.created_at ?? null,
        completedAt:       e.completed_at ?? null,
        circuitExecutions: Number.isFinite(e.circuit_executions) ? e.circuit_executions : null,
        elapsedSeconds:    Number.isFinite(e.elapsed_seconds) ? e.elapsed_seconds : null,
        hasResults:        !!(e.results && Object.keys(e.results).length)
      }));
    }
  );

export const getExperiment = (id) =>
  live(
    () => http.get(`/experiments/${id}`).then((r) => r.data),
    (e) => ({
      id:        e.experiment_id ?? e.id,
      name:      e.name ?? null,
      datasetId: e.dataset_id ?? null,
      status:    String(e.status ?? '').toUpperCase(),
      createdAt: e.created_at ?? null,
      startedAt: e.started_at ?? null,
      config:    e.configuration ?? null
    })
  );

export const createExperiment = (datasetId, cfg = {}) =>
  live(
    () => http.post('/experiments', { dataset_id: datasetId, ...cfg }).then((r) => r.data),
    (d) => ({
      id:        d.experiment_id ?? d.id,
      datasetId: d.dataset_id,
      status:    String(d.status ?? 'CREATED').toUpperCase()
    })
  );

export const runExperiment = (id) =>
  live(() => http.post(`/experiments/${id}/run`).then((r) => r.data), passthrough);

export const getStatus = (id) =>
  live(() => http.get(`/experiments/${id}/status`).then((r) => r.data), adaptStatus);

export const getResults = (id) =>
  live(() => http.get(`/experiments/${id}/results`).then((r) => r.data), adaptResults);

// Legacy fallback routes (may not exist — swallowed on 404)
export const getMetrics   = (id) =>
  http.get(`/experiments/${id}/metrics`).then((r) => r.data?.metrics ?? r.data).catch(() => null);
export const getComparison = (id) =>
  http.get(`/experiments/${id}/comparison`).then((r) => r.data).catch(() => null);

export const loadResults = async (id) => {
  const results = await getResults(id);
  if (results && Object.keys(results.models ?? {}).length) return results;
  // Try legacy metric endpoints as fallback
  const [metrics, comparison] = await Promise.all([
    getMetrics(id).catch(() => null),
    getComparison(id).catch(() => null)
  ]);
  if (!metrics || !Object.keys(metrics).length) return results;
  const models = {};
  for (const [name, m] of Object.entries(metrics)) {
    models[name] = { metrics: m?.metrics ?? m, resource_usage: m?.resource_usage ?? {} };
  }
  const base     = results ?? {};
  const fallback = adaptResults({ models, comparison });
  return {
    ...fallback,
    experimentId:   base.experimentId   ?? fallback.experimentId,
    status:         base.status         || fallback.status,
    ranking:        fallback.ranking?.length ? fallback.ranking : (base.ranking ?? []),
    preprocessing:  fallback.preprocessing  ?? base.preprocessing  ?? null,
    datasetProfile: fallback.datasetProfile ?? base.datasetProfile ?? null
  };
};

export const getExplanation = (id) =>
  live(() => http.get(`/experiments/${id}/explanation`).then((r) => r.data), adaptExplanation);

export const getResources = (id) =>
  live(() => http.get(`/experiments/${id}/resources`).then((r) => r.data), adaptResources)
    .catch(() => null);

export const getRecommendation = (id, comparison) =>
  live(
    () => http.get(`/experiments/${id}/recommendation`).then((r) => r.data),
    (d) => adaptRecommendation(d, comparison)
  );

export const getCost = (_id) => Promise.resolve(null);  // not implemented in backend yet

// Demo datasets — download URL served by backend
export const listDemos    = () =>
  live(() => http.get('/demo').then((r) => r.data.demos ?? []), passthrough).catch(() => []);

export const demoCsvUrl   = (name) => `${API_BASE}/demo/${name}`;

/** Fetch the demo CSV blob so the UI can pass it straight into uploadDataset */
export const fetchDemoCsv = async (name) => {
  const res  = await fetch(`${API_BASE}/demo/${name}`);
  if (!res.ok) throw new Error(`Demo fetch failed: ${res.status}`);
  const blob = await res.blob();
  return new File([blob], `${name}.csv`, { type: 'text/csv' });
};

export const getConfusion = (id, model) =>
  http.get(`/experiments/${id}/confusion-matrix/${model}`)
    .then((r) => r.data)
    .catch(() => null);

export const deleteExperiment = (id) =>
  live(() => http.delete(`/experiments/${id}`).then((r) => r.data), passthrough);

export const getQuantumResources = (id) =>
  getResources(id).then((r) => adaptQuantum(r?.quantum));

/* ── reports ────────────────────────────────────────────────────────────── */
export const generateReport = (id) =>
  live(() => http.post(`/experiments/${id}/report`).then((r) => r.data), adaptReport);

export const listReports = () => Promise.resolve([]);  // not implemented in backend

export const reportDownloadUrl = (id) => `${API_BASE}/experiments/${id}/report`;

// Fast-forward only makes sense with mocks — always rejected in live mode
export const canFastForward  = () => false;
export const fastForwardRun  = (_id) =>
  Promise.reject(new Error('Fast-forward is not available in live mode.'));

export const api = {
  getHealth, getConfig,
  listDatasets, getDataset, getProfile, validateDataset, getPlan, uploadDataset,
  listDemos, demoCsvUrl, fetchDemoCsv,
  listExperiments, getExperiment, createExperiment, runExperiment,
  getStatus, getResults, loadResults, getMetrics, getComparison,
  getExplanation, getResources, getRecommendation, getCost, getConfusion, deleteExperiment,
  generateReport, listReports, reportDownloadUrl, canFastForward, fastForwardRun
};

export default api;
