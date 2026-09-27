import { useCallback, useEffect, useRef, useState } from 'react';
import api from '@/services/api.js';

export const POLL_MS = 2000;

/**
 * Loads one experiment and polls `GET /status` every 2s while it runs
 * (never blocks on a single long request — implementaion_plan §79/§80).
 * Polling pauses when the tab is hidden and is always cleaned up.
 */
export function useExperiment(id) {
  const [exp, setExp] = useState(null);
  const [status, setStatus] = useState(null);
  const [bundle, setBundle] = useState({ results: null, explanation: null, resources: null, cost: null, recommendation: null });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [startedAt, setStartedAt] = useState(null);

  const timer = useRef(null);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; clearTimeout(timer.current); }, []);

  const loadCompleted = useCallback(async (experimentId, comparisonHint) => {
    const [results, explanation, resources, cost, recommendation] = await Promise.all([
      api.getResults(experimentId).catch(() => null),
      api.getExplanation(experimentId).catch(() => null),
      api.getResources(experimentId).catch(() => null),
      api.getCost(experimentId).catch(() => null),
      api.getRecommendation(experimentId, comparisonHint).catch(() => null)
    ]);
    if (!alive.current) return null;
    setBundle({ results, explanation, resources, cost, recommendation });
    return results;
  }, []);

  const refresh = useCallback(async () => {
    if (!id) return;
    try {
      const meta = await api.getExperiment(id);
      if (!alive.current) return;
      setExp(meta);
      setStartedAt(meta.startedAt);

      const st = await api.getStatus(id);
      if (!alive.current) return;
      setStatus(st);
      setError(st.error ? { status: 500, message: st.error } : null);

      if (st.isRunning) {
        setRunning(true);
      } else {
        setRunning(false);
        if (st.isCompleted) await loadCompleted(id, null);
      }
      setLoading(false);
    } catch (e) {
      if (!alive.current) return;
      setError(e);
      setLoading(false);
    }
  }, [id, loadCompleted]);

  useEffect(() => {
    alive.current = true;
    setBundle({ results: null, explanation: null, resources: null, cost: null, recommendation: null });
    setStatus(null);
    setLoading(true);
    refresh();
    return () => { alive.current = false; };
  }, [refresh]);

  // self-rescheduling poll (no interval stacking)
  useEffect(() => {
    clearTimeout(timer.current);
    if (!running || !id) return undefined;
    const tick = () => {
      timer.current = setTimeout(async () => {
        if (document.visibilityState === 'visible' && alive.current) await refresh();
        tick();
      }, POLL_MS);
    };
    tick();
    return () => clearTimeout(timer.current);
  }, [running, id, refresh]);

  // live elapsed clock between polls
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running || !startedAt) { setElapsed(status?.elapsedSeconds ?? 0); return undefined; }
    const base = new Date(startedAt).getTime();
    const t = setInterval(() => setElapsed(Math.max(0, (Date.now() - base) / 1000)), 250);
    return () => clearInterval(t);
  }, [running, startedAt, status?.elapsedSeconds]);

  const run = useCallback(async () => {
    setError(null);
    try {
      await api.runExperiment(id);
      setRunning(true);
      await refresh();
    } catch (e) {
      setError(e);
    }
  }, [id, refresh]);

  return {
    exp, status, running, loading, error, elapsed,
    results: bundle.results,
    explanation: bundle.explanation,
    resources: bundle.resources,
    cost: bundle.cost,
    recommendation: bundle.recommendation,
    run, reload: refresh
  };
}

export default useExperiment;
