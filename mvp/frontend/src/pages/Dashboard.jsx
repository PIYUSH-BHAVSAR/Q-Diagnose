import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/services/api.js';
import Icon from '@/components/Icon.jsx';
import Disclaimer from '@/components/Disclaimer.jsx';
import { Card, Btn, Empty, PageSkeleton, Rail, StatusPill, StatCard, Pill, CountUp } from '@/components/ui.jsx';
import { int, ago, score, titleize, dur } from '@/lib/format.js';
import { STAGES } from '@/lib/fieldMap.js';

const PIPELINE = [
  ['upload', 'Ingest CSV'], ['profile', 'Profile & target'], ['validate', 'Quality gates'],
  ['preprocess', 'Leak-safe split'], ['reduce', 'PCA → qubits'], ['train', 'VQC vs classical'],
  ['compare', 'Benchmark & recommend']
];

import { useGlow } from '@/hooks/useGlow.js';

export default function Dashboard() {
  const glow = useGlow();
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [progress, setProgress] = useState({});
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([api.listDatasets().catch(() => null), api.listExperiments().catch(() => [])])
      .then(async ([d, e]) => {
        if (!alive) return;
        setDatasets(d?.datasets ?? []);
        setExperiments(e ?? []);
        const live = (e ?? []).filter((x) => !['COMPLETED', 'FAILED'].includes(x.status)).slice(0, 4);
        const p = await Promise.all(live.map((x) => api.getStatus(x.id).catch(() => null)));
        if (!alive) return;
        setProgress(Object.fromEntries(p.filter(Boolean).map((s, i) => [live[i].id, s])));
        setLoading(false);
      })
      .catch(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [tick]);

  useEffect(() => {
    const onVis = () => document.visibilityState === 'visible' && setTick((t) => t + 1);
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  const stats = useMemo(() => {
    const done = experiments.filter((e) => e.status === 'COMPLETED');
    const running = experiments.filter((e) => !['COMPLETED', 'FAILED'].includes(e.status));
    // polled value wins; otherwise the list row's own count (live backend omits it → 0, not a guess)
    const circuits = experiments.reduce((a, e) => a + (progress[e.id]?.circuitExecutions ?? e.circuitExecutions ?? 0), 0);
    // the KPI row must not repeat the hero, so these measure the *queue*, not the totals
    const failed = experiments.filter((e) => e.status === 'FAILED').length;
    const idle = datasets.filter((d) => !experiments.some((e) => e.datasetId === d.id)).length;
    const queued = running.filter((e) => ['QUEUED', 'CREATED', 'PENDING', 'VALIDATING', 'CREATING', 'PREPROCESSING', 'PROFILING'].includes(String(progress[e.id]?.stage || e.status).toUpperCase())).length;
    return {
      datasets: datasets.length, total: experiments.length, done: done.length, running: running.length, circuits,
      failed, idle, queued, avgCircuits: done.length ? Math.round(circuits / done.length) : 0,
    };
  }, [datasets, experiments, progress]);

  if (loading) return <PageSkeleton rows={3} />;

  return (
    <>
      <section className="hero" ref={glow}>
        <div>
          <div className="row" style={{ gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
            <span className="eyebrow"><i className="dot" />Hybrid quantum-classical benchmark engine</span>
          </div>
          <h1>
            Quantum vs classical,<br />
            <span className="grad-text">measured on clinical tables.</span>
          </h1>
          <p className="lede">
            Upload a tabular dataset, get an automatic profile, then run Logistic Regression, SVM and Random
            Forest against a Variational Quantum Classifier on the exact same leak-safe split — with cost,
            explainability and a recommendation attached.
          </p>
          <div className="hero-cta">
            <Btn to="/experiments/new" kind="primary" size="lg" icon="zap">Run a benchmark</Btn>
            <Btn to="/datasets" size="lg" icon="database">Browse datasets</Btn>
            <span className="row" style={{ gap: 6, marginLeft: 6, fontSize: 'var(--t-xs)', color: 'var(--text-3)' }}>
              or press <span className="kbd">⌘K</span>
            </span>
          </div>
          <div className="hero-stack">
            {['FastAPI + PennyLane', 'leak-safe stratified 80/20', 'SHAP explanations', 'uncalibrated scores, labelled as such'].map((t) => (
              <span key={t} className="pill">{t}</span>
            ))}
          </div>

          <div className="hero-stats">
            {[['Datasets', stats.datasets], ['Experiments', stats.total], ['Completed', stats.done], ['Circuits executed', stats.circuits]].map(([k, v]) => (
              <div key={k}>
                <div className="k">{k}</div>
                <div className="v"><CountUp value={v} format={(x) => int(Math.round(x))} /></div>
              </div>
            ))}
          </div>
        </div>

        <CircuitVisual />
      </section>

      <div className="grid g-4">
        <StatCard icon="clock" label="In flight" value={stats.running} hint={stats.running ? `polling every 2s · ${stats.queued} not started yet` : 'nothing running'} tone={stats.running ? 'var(--amber)' : 'var(--text)'} />
        <StatCard icon="database" label="Datasets without a run" value={stats.idle} hint={stats.idle ? 'ready to benchmark' : 'every dataset has been used'} tone="var(--cyan)" />
        <StatCard icon="check" label="Reports ready" value={stats.done} hint="results + explanation attached" tone="var(--emerald)" />
        <StatCard icon="alert" label="Needs attention" value={stats.failed} hint={stats.failed ? 'runs that errored' : 'no failures — clean board'} tone={stats.failed ? 'var(--rose)' : 'var(--text)'} />
      </div>

      <div className="grid g-side">
        <Card
          title="Recent runs" icon="activity" sub="Live status from GET /experiments/{id}/status"
          actions={<Btn size="sm" kind="quiet" icon="arrowRight" to="/experiments">All experiments</Btn>}
          pad={false}
        >
          {experiments.length === 0 ? (
            <Empty
              icon="flask" title="No experiments yet"
              body="Pick a dataset and start your first hybrid benchmark — the whole pipeline runs unattended and you can leave the tab."
              action={<Btn kind="primary" icon="plus" to="/experiments/new">New experiment</Btn>}
            />
          ) : (
            <ul className="list" style={{ listStyle: 'none', margin: 0 }}>
              {experiments.slice(0, 5).map((e) => {
                const st = progress[e.id];
                return (
                  <li key={e.id} className={st && !st.isCompleted && !st.isFailed ? 'is-live' : undefined}>
                    <Link to={`/experiments/${e.id}`} className="row" style={{ gap: 14, minWidth: 0, flex: 1 }}>
                      <span className="brand-mark" style={{ width: 26, height: 26, borderRadius: 8 }}>
                        <Icon name={e.status === 'COMPLETED' ? 'check' : 'atom'} size={13} />
                      </span>
                      <span style={{ minWidth: 0, flex: '1 1 160px' }}>
                        <span className="ellip" style={{ display: 'block', fontWeight: 620 }}>
                          {e.name ?? e.id}
                        </span>
                        <span className="tiny dim mono">{e.id} · {ago(e.createdAt ?? e.completedAt)}</span>
                      </span>
                    </Link>
                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
                      {st && !st.isCompleted && (
                        <span className="mini-rail" style={{ width: 92 }}>
                          <Rail value={st.progress} striped />
                        </span>
                      )}
                      {st?.isCompleted && Number.isFinite(st.elapsedSeconds) && <span className="tiny dim mono">{dur(st.elapsedSeconds)}</span>}
                      <StatusPill status={e.status} />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card title="Pipeline" icon="circuit" sub="Every run walks these seven stages">
          <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 2 }}>
            {PIPELINE.map(([icon, label], i) => (
              <li key={label} className="row" style={{ gap: 11, padding: '7px 0', borderBottom: i < PIPELINE.length - 1 ? '1px solid var(--line)' : 0 }}>
                <span className="rail-dot" style={{ width: 20, height: 20 }}><Icon name={icon} size={11} /></span>
                <span style={{ fontSize: 'var(--t-md)', color: 'var(--text-2)' }}>{label}</span>
                <span className="tiny dim mono" style={{ marginLeft: 'auto' }}>0{i + 1}</span>
              </li>
            ))}
          </ol>
          <div className="row" style={{ marginTop: 16, gap: 8, flexWrap: 'wrap' }}>
            <Pill icon="cpu">LR · SVM · RF</Pill>
            <Pill icon="atom" tone="quantum">VQC · 8 qubits</Pill>
            <Pill icon="gauge">PennyLane simulator</Pill>
          </div>
        </Card>
      </div>

      <Card
        title="Demo datasets" icon="sparkles" sub="Pre-validated clinical benchmarks already registered by the loader"
        actions={<Btn size="sm" kind="quiet" icon="upload" to="/datasets?upload=1">Add your own</Btn>}
        pad={false}
      >
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', padding: 'var(--s-4) var(--s-5)', gap: 12 }}>
          {datasets.length === 0 && <Empty icon="database" title="Nothing registered" body="Upload a CSV to get started." />}
          {datasets.map((d) => (
            <Link key={d.id} to={`/datasets/${d.id}`} className="card card-hover" style={{ padding: 14, display: 'grid', gap: 8 }}>
              <div className="row" style={{ gap: 8 }}>
                <Icon name="table" size={15} style={{ color: 'var(--accent)' }} />
                <span style={{ fontWeight: 660, fontSize: 'var(--t-md)' }}>{d.display ?? d.filename}</span>
              </div>
              <div className="tiny dim mono">{int(d.rows)} rows · {d.featureCount ?? '—'} cols</div>
              <div className="row" style={{ gap: 6, marginTop: 2 }}>
                <Pill icon="check" tone="ok">profiled</Pill>
                {d.sizeMb ? <Pill>{d.sizeMb.toFixed(1)} MB</Pill> : null}
              </div>
            </Link>
          ))}
        </div>
      </Card>

      <Disclaimer />
    </>
  );
}

function CircuitVisual() {
  return (
    <div className="circuit-visual" aria-hidden="true">
      <svg viewBox="0 0 200 200">
        <defs>
          <radialGradient id="core"><stop offset="0%" stopColor="var(--cyan)" stopOpacity="0.9" /><stop offset="100%" stopColor="var(--violet)" stopOpacity="0.15" /></radialGradient>
        </defs>
        {[76, 58, 40].map((r, i) => (
          <g key={r} className={`orbit ${i % 2 ? 'rev' : ''}`}>
            <ellipse cx="100" cy="100" rx={r} ry={r * 0.42} fill="none" stroke="var(--line-2)" strokeWidth="1"
              transform={`rotate(${i * 60} 100 100)`} />
            <circle className="node" cx={100 + r} cy="100" r="3.2" fill="var(--cyan)" transform={`rotate(${i * 60} 100 100)`}
              style={{ animationDelay: `${i * 0.5}s` }} />
          </g>
        ))}
        <circle cx="100" cy="100" r="26" fill="url(#core)" opacity="0.5" />
        <circle cx="100" cy="100" r="7" fill="var(--cyan)" />
        {Array.from({ length: 8 }).map((_, i) => {
          const a = (i / 8) * Math.PI * 2;
          return <circle key={i} cx={100 + Math.cos(a) * 90} cy={100 + Math.sin(a) * 90} r="1.6" fill="var(--text-3)" opacity="0.8" />;
        })}
      </svg>
      <div className="card" style={{ position: 'absolute', left: 0, bottom: 6, padding: '8px 11px', display: 'grid', gap: 3 }}>
        <span className="tiny dim" style={{ letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 650 }}>Ansatz</span>
        <span className="mono" style={{ fontSize: 'var(--t-sm)' }}>8 qubits · 2 layers · 1024 shots</span>
      </div>
    </div>
  );
}
