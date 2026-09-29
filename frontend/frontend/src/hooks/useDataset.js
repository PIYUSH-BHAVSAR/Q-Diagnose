import { useCallback, useEffect, useRef, useState } from 'react';
import api from '@/services/api.js';

const POLL_MS = 2000;

/**
 * Loads a dataset's profile + validation report and keeps polling while the
 * backend is still profiling (contract 202 / status=PROFILING). Cleanup always.
 */
export function useDataset(datasetId) {
  const [profile, setProfile] = useState(null);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profiling, setProfiling] = useState(false);
  const timer = useRef(null);
  const alive = useRef(true);

  useEffect(() => () => { alive.current = false; clearTimeout(timer.current); }, []);

  const load = useCallback(async () => {
    try {
      const [p, v] = await Promise.all([
        api.getProfile(datasetId),
        api.validateDataset(datasetId).catch(() => null)   // validator may 400 — profile still useful
      ]);
      if (!alive.current) return;
      setProfile(p);
      setValidation(v);
      setError(null);
      const stillBusy = /PROFILING|PENDING|IN_PROGRESS/i.test(String(p.status ?? ''));
      setProfiling(stillBusy);
      clearTimeout(timer.current);
      if (stillBusy) timer.current = setTimeout(load, POLL_MS);
    } catch (e) {
      if (alive.current) { setError(e); setProfiling(false); }
    } finally {
      if (alive.current) setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => { alive.current = true; setLoading(true); load(); }, [load]);

  return { profile, validation, loading, error, profiling, reload: load };
}

export default useDataset;
