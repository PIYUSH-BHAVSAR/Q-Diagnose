import React, { Suspense, lazy, useCallback, useEffect, useState, useMemo } from 'react';
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import Icon from '@/components/Icon.jsx';
import CommandPalette from '@/components/CommandPalette.jsx';
import ToastHost from '@/components/ToastHost.jsx';
import api, { dataMode, onDataMode } from '@/services/api.js';
import { PageSkeleton } from '@/components/ui.jsx';

const Dashboard = lazy(() => import('@/pages/Dashboard.jsx'));
const Datasets = lazy(() => import('@/pages/Datasets.jsx'));
const DatasetDetail = lazy(() => import('@/pages/DatasetDetail.jsx'));
const ExperimentsList = lazy(() => import('@/pages/ExperimentsList.jsx'));
const ExperimentNew = lazy(() => import('@/pages/ExperimentNew.jsx'));
const ExperimentDetail = lazy(() => import('@/pages/ExperimentDetail.jsx'));
const Reports = lazy(() => import('@/pages/Reports.jsx'));

const NAV = [
  { to: '/', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/datasets', label: 'Datasets', icon: 'database' },
  { to: '/experiments', label: 'Experiments', icon: 'flask' },
  { to: '/reports', label: 'Reports', icon: 'file' }
];

const CRUMB = {
  datasets: 'Datasets', experiments: 'Experiments', reports: 'Reports', new: 'New experiment'
};

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('qw.theme') ?? 'dark');
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('qw.theme', theme);
    // keep the browser chrome / OS accent strip in sync with the canvas
    const meta = document.querySelector('meta[name=theme-color]');
    if (meta) meta.setAttribute('content', theme === 'light' ? '#f7f8fa' : '#06070a');
  }, [theme]);
  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))];
}

export default function App() {
  const loc = useLocation();
  const [theme, toggleTheme] = useTheme();
  const [palette, setPalette] = useState(false);
  const [health, setHealth] = useState({ status: 'checking', mode: dataMode.current });
  const [counts, setCounts] = useState({ datasets: null, experiments: null });

  useEffect(() => {
    let alive = true;
    const ping = () => api.getHealth().then((h) => alive && setHealth(h)).catch(() => alive && setHealth({ status: 'unreachable', mode: dataMode.current }));
    ping();
    const t = setInterval(ping, 20000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  useEffect(() => onDataMode((m) => setHealth((h) => ({ ...h, mode: m }))), []);

  useEffect(() => {
    let alive = true;
    const load = () => Promise.all([api.listDatasets().catch(() => null), api.listExperiments().catch(() => null)])
      .then(([d, e]) => { if (alive) setCounts({ datasets: d?.datasets?.length ?? null, experiments: e?.length ?? null }); });
    load();
    const onVis = () => document.visibilityState === 'visible' && load();
    document.addEventListener('visibilitychange', onVis);
    return () => { alive = false; document.removeEventListener('visibilitychange', onVis); };
  }, [loc.pathname]);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette((p) => !p); }
      if (e.key === 'Escape') setPalette(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const segs = loc.pathname.split('/').filter(Boolean);
  const crumbs = [
    { label: 'Overview', to: '/' },
    ...segs.map((s, i) => ({
      label: CRUMB[s] ?? (/^(DS|EXP)-/.test(s) ? s : s.replace(/-/g, ' ')),
      mono: /^(DS|EXP)-/.test(s),
      to: '/' + segs.slice(0, i + 1).join('/')
    }))
  ];

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <div className="ambient" aria-hidden="true">
        <i className="a" /><i className="b" /><i className="c" /><i className="d" /><span className="horizon" />
      </div>
      <div className="shell">
        <aside className="nav" aria-label="Primary">
          <Link to="/" className="brand">
            <span className="brand-mark"><Icon name="atom" size={17} /></span>
            <span>
              <span className="brand-name">QuantWarriors</span>
              <span className="brand-sub" style={{ display: 'block' }}>Q-Diagnose</span>
            </span>
          </Link>

          <nav className="nav-group" aria-label="Sections">
            <div className="nav-label">Workspace</div>
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.end} className="nav-item">
                <Icon name={n.icon} size={16} />
                <span>{n.label}</span>
                {n.label === 'Datasets' && counts.datasets != null && <span className="nav-count">{counts.datasets}</span>}
                {n.label === 'Experiments' && counts.experiments != null && <span className="nav-count">{counts.experiments}</span>}
              </NavLink>
            ))}
            <div className="nav-label" style={{ marginTop: 14 }}>Actions</div>
            <Link to="/datasets?upload=1" className="nav-item"><Icon name="upload" size={16} />Upload CSV</Link>
            <Link to="/experiments/new" className="nav-item"><Icon name="zap" size={16} />Run benchmark</Link>
          </nav>

          <div className="nav-foot">
            <div className="health" title="Backend health — polled every 20s">
              <span className={`pulse ${health.status === 'healthy' ? 'on' : health.status === 'checking' ? '' : 'off'}`} />
              <span>{health.mode === 'demo' ? 'Data' : 'Engine'}{' '}
                <b className="mono">
                  {health.mode === 'demo'
                    ? 'fixtures'
                    : health.status === 'healthy' ? 'live · /api'
                    : health.status === 'checking' ? 'checking…' : 'unreachable'}
                </b>
              </span>
              {health.mode === 'demo' && <span className="pill warn" style={{ marginLeft: 'auto', padding: '1px 6px' }}>demo</span>}
            </div>
          </div>
        </aside>

        <div className="main">
          <header className="topbar">
            <div className="crumbs">
              {crumbs.map((c, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <span className="sep">/</span>}
                  {i === crumbs.length - 1
                    ? <b className={c.mono ? 'mono' : ''}>{c.label}</b>
                    : <Link to={c.to} className={c.mono ? 'mono' : ''}>{c.label}</Link>}
                </React.Fragment>
              ))}
            </div>
            <div className="topbar-actions">
              <button type="button" className="search-trigger" onClick={() => setPalette(true)} aria-label="Open command palette">
                <Icon name="search" size={14} />
                <span className="txt">Search datasets, experiments…</span>
                <span className="kbd">⌘K</span>
              </button>
              <button type="button" className="btn btn-icon btn-quiet" onClick={toggleTheme} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`} title="Toggle theme">
                <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={16} />
              </button>
              <Link to="/experiments/new" className="btn btn-primary" aria-label="New experiment">
                <Icon name="plus" size={15} /><span className="btn-label">New experiment</span>
              </Link>
            </div>
          </header>

          <main className="content" id="main">
            <Suspense fallback={<PageSkeleton />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/datasets" element={<Datasets />} />
                <Route path="/datasets/:id" element={<DatasetDetail />} />
                <Route path="/experiments" element={<ExperimentsList />} />
                <Route path="/experiments/new" element={<ExperimentNew />} />
                <Route path="/experiments/new/:datasetId" element={<ExperimentNew />} />
                <Route path="/experiments/:id" element={<ExperimentDetail />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </main>
        </div>
      </div>

      <CommandPalette open={palette} onClose={() => setPalette(false)} onToggleTheme={toggleTheme} />
      <ToastHost />
    </>
  );
}

function NotFound() {
  return (
    <div className="card card-pad" style={{ textAlign: 'center', padding: 'var(--s-8)' }}>
      <div className="eyebrow" style={{ justifyContent: 'center', marginBottom: 10 }}><i className="dot" />404</div>
      <h2 style={{ fontSize: 'var(--t-2xl)' }}>That route does not exist</h2>
      <p className="muted" style={{ margin: '10px auto 20px', maxWidth: '44ch' }}>
        The page you asked for is not part of the Q-Diagnose shell. Try the workspace nav or ⌘K.
      </p>
      <Link to="/" className="btn btn-primary"><Icon name="dashboard" size={15} />Back to dashboard</Link>
    </div>
  );
}
