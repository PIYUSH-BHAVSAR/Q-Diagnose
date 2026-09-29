import { describe, it, expect, vi, beforeEach } from 'vitest';

/**
 * The deployed backend (the one the first frontend on main talked to) answers
 * /experiments/{id}/metrics + /experiments/{id}/comparison and has no unified /results.
 * loadResults() must therefore fill the table from those two routes when /results under-delivers
 * — and must NOT touch them when /results already carries rows.
 * axios is faked here; the module under test is the real src/services/api.js.
 */
const h = vi.hoisted(() => ({ routes: {}, calls: [] }));
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: (p) => {
        h.calls.push(p);
        const r = h.routes[p];
        if (r === undefined) return Promise.reject(Object.assign(new Error('404'), { isAxiosError: true, response: { status: 404 } }));
        return Promise.resolve({ data: r });
      },
      post: (p, b) => { h.calls.push(p); return Promise.resolve({ data: {} }); },
      delete: (p) => { h.calls.push(p); return Promise.resolve({ data: {} }); },
    }),
    isCancel: () => false,
  },
}));

const METRICS = {
  log_reg: { accuracy: 0.91, precision: 0.90, recall: 0.88, f1_score: 0.89, auc: 0.94, training_time_seconds: 1.2 },
  qvc: { accuracy: 0.93, precision: 0.92, recall: 0.95, f1_score: 0.93, auc: 0.96, training_time_seconds: 21.4 },
};
const COMPARISON = {
  best_model: 'qvc',
  classical_best: { model_name: 'log_reg', metrics: { accuracy: 0.91 }, training_time_seconds: 1.2 },
  quantum_best: { model_name: 'qvc', metrics: { accuracy: 0.93 }, training_time_seconds: 21.4 },
  recommendation: 'quantum wins on recall at 17.8x the compute',
};

let api;
beforeEach(async () => {
  h.calls.length = 0;
  vi.stubEnv('VITE_MOCK', '0');                       // force the live path, not fixtures
  vi.resetModules();
  api = (await import('@/services/api.js')).default;
});

describe('loadResults · legacy route fallback', () => {
  it('takes rows from /metrics + /comparison when /results has none', async () => {
    h.routes = {
      '/experiments/E1/results': { results: { models: {} } },
      '/experiments/E1/metrics': { metrics: METRICS },
      '/experiments/E1/comparison': COMPARISON,
    };
    const out = await api.loadResults('E1');
    expect(Object.keys(out.models).sort()).toEqual(['log_reg', 'qvc']);
    expect(out.models.qvc.metrics.accuracy).toBe(0.93);
    expect(out.models.log_reg.metrics.roc_auc).toBe(0.94);   // legacy key "auc" is aliased in fieldMap
    expect(out.comparison.bestClassical).toBe('log_reg');
    expect(out.comparison.bestQuantum).toBe('qvc');
    expect(out.comparison.recommendationText).toContain('17.8x');
    expect(+out.comparison.diff('accuracy').difference.toFixed(2)).toBe(0.02);
    expect(h.calls).toEqual(['/experiments/E1/results', '/experiments/E1/metrics', '/experiments/E1/comparison']);
  });

  it('does not make extra requests when /results already answers', async () => {
    h.routes = {
      '/experiments/E1/results': { results: { models: { qvc: { metrics: { accuracy: 0.93 } } } } },
      '/experiments/E1/metrics': { metrics: METRICS },
      '/experiments/E1/comparison': COMPARISON,
    };
    const out = await api.loadResults('E1');
    expect(out.models.qvc.metrics.accuracy).toBe(0.93);
    expect(h.calls).toEqual(['/experiments/E1/results']);
  });

  it('degrades to the empty state instead of throwing when nothing is there', async () => {
    h.routes = { '/experiments/E1/results': { results: {} } };   // metrics + comparison 404
    const out = await api.loadResults('E1');
    expect(out.models).toEqual({});
    expect(h.calls).toEqual(['/experiments/E1/results', '/experiments/E1/metrics', '/experiments/E1/comparison']);
  });
});
