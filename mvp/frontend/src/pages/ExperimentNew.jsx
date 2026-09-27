import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '@/services/api.js';
import Icon from '@/components/Icon.jsx';
import Disclaimer from '@/components/Disclaimer.jsx';
import { Card, Btn, ErrorBanner, Note, PageSkeleton, Pill, SectionHead, KV } from '@/components/ui.jsx';
import { int, titleize } from '@/lib/format.js';
import { toast } from '@/lib/toast.js';

const DEFAULT_RULES = [
  ['Stratified 80/20 split', 'Keeps class ratio identical in both arms — no leakage from the test set.'],
  ['Scaler fitted on train only', 'StandardScaler is .fit(train) then .transform(test) — the test split never influences the mean/variance.'],
  ['PCA to qubit-count budget', '8 components ≈ 8 qubits; variance retained is reported instead of guessed.'],
  ['Class weights on imbalanced targets', 'Minority class gets inverse-frequency weight so recall is not dominated by the majority.'],
  ['Identical split for classical and quantum', 'Both arms see the exact same rows — the comparison is apples-to-apples.']
];

export default function ExperimentNew() {
  const { datasetId } = useParams();
  const nav = useNavigate();
  const [datasets, setDatasets] = useState([]);
  const [profile, setProfile] = useState(null);
  const [plan, setPlan] = useState(null);
  const [config, setConfig] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ name: '', target: null, n_components: 8, use_class_weight: true });

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([api.listDatasets(), api.getConfig().catch(() => null)])
      .then(([d, cfg]) => {
        if (!alive) return;
        setDatasets(d.datasets ?? []);
        setConfig(cfg);
        return d.datasets?.[0]?.id && !datasetId ? d : d;
      })
      .catch((e) => alive && setError(e))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [datasetId]);

  useEffect(() => {
    if (!datasetId) return undefined;
    let alive = true;
    Promise.all([api.getProfile(datasetId).catch(() => null), api.getPlan(datasetId).catch(() => null)])
      .then(([p, pl]) => {
        if (!alive) return;
        setProfile(p);
        setPlan(pl);
        setForm((f) => ({ ...f, target: f.target ?? p?.target ?? null }));
      });
    return () => { alive = false; };
  }, [datasetId]);

  const derived = useMemo(() => {
    const q = config?.quantum ?? {};
    return {
      task: profile?.task ?? 'BINARY_CLASSIFICATION',
      split: plan?.evaluation?.split ?? 'stratified',
      testSize: plan?.evaluation?.test_size ?? config?.experiment?.test_size ?? 0.2,
      scaler: 'StandardScaler (train-fit)',
      method: plan?.reduction?.method ?? 'PCA',
      components: plan?.reduction?.components ?? q.max_qubits ?? 8,
      variance: plan?.reduction?.variance_retained ?? null,
      classical: plan?.classical_models ?? config?.classical_models ?? ['logistic_regression', 'svm', 'random_forest'],
      quantum: plan?.quantum_models ?? [q.model ?? 'vqc'],
      qubits: q.max_qubits ?? 8,
      layers: q.layers ?? 2,
      shots: q.shots ?? 1024,
      randomState: plan?.evaluation?.random_state ?? config?.experiment?.random_state ?? 42
    };
  }, [config, plan, profile]);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const created = await api.createExperiment(datasetId, {
        name: form.name || undefined,
        target_column: form.target || undefined,
        n_components: Number(form.n_components),
        quantum_config: { use_class_weight: form.use_class_weight }
      });
      try { await api.runExperiment(created.id); } catch (e) {
        if (e.status !== 400) throw e;                      // already started server-side
      }
      toast('Experiment started', `${created.id} — you can leave this tab, the executor keeps running.`, 'success');
      nav(`/experiments/${created.id}`, { replace: true });
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  if (loading) return <PageSkeleton rows={3} />;

  if (!datasetId) {
    return (
      <>
        <SectionHead eyebrow="Phase 9 · planning" title="Pick a dataset to benchmark"
          sub="A plan is generated from the profile — target, split, reduction and both model arms — before anything trains." />
        {error && <ErrorBanner error={error} retry={() => nav(0)} />}
        <div className="grid g-3">
          {datasets.map((d) => (
            <Card key={d.id} hover className="card-pad" title={undefined}>
              <div className="row" style={{ gap: 10, marginBottom: 10 }}>
                <span className="brand-mark" style={{ width: 28, height: 28 }}><Icon name="table" size={14} /></span>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 680 }}>{d.display ?? d.filename}</div>
                  <div className="tiny dim mono">{d.id}</div>
                </div>
              </div>
              <div className="row row-wrap" style={{ gap: 6, marginBottom: 14 }}>
                <Pill icon="table">{int(d.rows)} rows</Pill>
                <Pill icon="layers">{d.featureCount ?? '—'} cols</Pill>
              </div>
              <Btn kind="primary" iconRight="arrowRight" to={`/experiments/new/${d.id}`} style={{ width: '100%' }}>Design run</Btn>
            </Card>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <SectionHead
        eyebrow="Phase 9 · planning"
        title="Experiment plan"
        sub={profile ? `${profile.name} — ${int(profile.rows)} rows, target "${profile.target ?? 'auto'}". Deterministic defaults, editable below.` : 'Deterministic defaults derived from the dataset profile.'}
        actions={<Btn icon="x" kind="quiet" onClick={() => nav('/experiments')}>Cancel</Btn>}
      />

      {error && <ErrorBanner error={error} />}

      {!plan && (
        <Note icon="info" title="Plan endpoint not exposed yet">
          <span className="mono tiny">GET /api/datasets/{'{id}'}/plan</span> is not implemented in the MVP backend,
          so these defaults are derived client-side from <span className="mono tiny">GET /api/config</span> and the profile. Nothing is guessed about the data itself.
        </Note>
      )}

      <div className="grid g-side">
        <Card title="Pipeline configuration" icon="sliders" sub="what the executor will run">
          <KV rows={[
            ['Task', <Pill key="t" tone="accent" icon="target">{titleize(derived.task)}</Pill>],
            ['Split', `${derived.split} · ${(derived.testSize * 100).toFixed(0)}% test · seed ${derived.randomState}`],
            ['Preprocessing', derived.scaler],
            ['Reduction', `${derived.method} → ${derived.components} components${derived.variance != null ? ` · ${(derived.variance * 100).toFixed(1)}% variance` : ''}`],
            ['Classical arms', <span key="c" className="chips">{derived.classical.map((m) => <Pill key={m} icon="cpu">{titleize(m)}</Pill>)}</span>],
            ['Quantum arm', <span key="q" className="chips">{derived.quantum.map((m) => <Pill key={m} tone="quantum" icon="atom">{titleize(m)}</Pill>)}</span>],
            ['Circuit', `${derived.qubits} qubits · ${derived.layers} entangling layers · ${derived.shots} shots · angle encoding`]
          ]} />
        </Card>

        <div className="stack" style={{ gap: 'var(--s-4)' }}>
          <Card title="Why this pipeline?" icon="sparkles" sub={plan?.decision_trace?.reason ?? 'Rule-based deterministic planning'}>
            {!!plan?.decision_trace?.rules_applied?.length && (
              <div className="chips" style={{ marginBottom: 14 }}>
                {plan.decision_trace.rules_applied.map((r, i) => <Pill key={i} tone="accent" icon="check">{String(r)}</Pill>)}
              </div>
            )}
            <ul className="checks">
              {DEFAULT_RULES.map(([t, d]) => (
                <li key={t}><Icon name="check" size={13} strokeWidth={2.4} /><span><b style={{ color: 'var(--text)' }}>{t}</b> — {d}</span></li>
              ))}
            </ul>
          </Card>

          <Card title="Overrides" icon="sliders" sub="optional — leave empty for the generated plan">
            <div className="stack" style={{ gap: 14 }}>
              <div className="field">
                <label htmlFor="exp-name">Run name</label>
                <input id="exp-name" className="input" value={form.name} placeholder={`${profile?.name ?? 'dataset'} · hybrid benchmark`}
                  onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="grid g-2">
                <div className="field">
                  <label htmlFor="exp-target">Target column</label>
                  <select id="exp-target" className="select" value={form.target ?? ''} onChange={(e) => setForm({ ...form, target: e.target.value || null })}>
                    <option value="">auto ({profile?.target ?? 'detect'})</option>
                    {(profile?.targetCandidates?.length ? profile.targetCandidates : [profile?.target].filter(Boolean)).map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="exp-pca">PCA components</label>
                  <select id="exp-pca" className="select" value={form.n_components} onChange={(e) => setForm({ ...form, n_components: Number(e.target.value) })}>
                    {[2, 4, 6, 8, 10, 12].map((n) => <option key={n} value={n}>{n} {n === derived.components ? '· planned' : ''}</option>)}
                  </select>
                </div>
              </div>
              <label className="switch">
                <input type="checkbox" checked={form.use_class_weight} onChange={(e) => setForm({ ...form, use_class_weight: e.target.checked })} />
                Weight the minority class (recommended when imbalanced)
              </label>
              <Btn kind="primary" size="lg" icon={busy ? 'refresh' : 'play'} onClick={run} disabled={busy} style={{ marginTop: 4 }}>
                {busy ? 'Starting executor…' : `Run benchmark · ${derived.classical.length} classical + 1 quantum`}
              </Btn>
              <p className="tiny dim">Training the VQC can take minutes on a laptop simulator. <span className="mono">POST /run</span> returns immediately and the UI polls status every 2s.</p>
            </div>
          </Card>

          <Disclaimer />
        </div>
      </div>
    </>
  );
}
