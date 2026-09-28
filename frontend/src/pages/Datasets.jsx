import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import api from '@/services/api.js';
import { fetchDemoCsv, demoCsvUrl } from '@/services/api.js';
import Icon from '@/components/Icon.jsx';
import FileDropzone from '@/components/FileDropzone.jsx';
import { Card, Btn, Empty, ErrorBanner, PageSkeleton, Pill, SectionHead, StatusPill } from '@/components/ui.jsx';
import { fmtSize, int, ago } from '@/lib/format.js';
import { toast } from '@/lib/toast.js';

export default function Datasets() {
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [q, setQ] = useState('');
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const open = params.get('upload') === '1';

  const load = () => {
    setLoading(true);
    api.listDatasets()
      .then((d) => { setRows(d.datasets ?? []); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.uploadDataset(file, name || undefined);
      toast('Dataset registered', `${res.filename} → ${res.datasetId}`, 'success');
      nav(`/datasets/${res.datasetId}`);
    } catch (e) {
      setError(e);
      toast('Upload rejected', e.message, 'error');
    } finally {
      setBusy(false);
      setFile(null);
    }
  };

  // Download demo CSV from backend then immediately upload + navigate to profile
  const tryDemo = async () => {
    setDemoLoading(true);
    setError(null);
    try {
      toast('Fetching demo', 'Downloading breast_cancer.csv from server…', 'info');
      const demoFile = await fetchDemoCsv('breast-cancer');
      const res = await api.uploadDataset(demoFile, 'breast_cancer_demo');
      toast('Demo uploaded', `${res.filename} registered — taking you to the profile.`, 'success');
      nav(`/datasets/${res.datasetId}`);
    } catch (e) {
      setError(e);
      toast('Demo failed', e.message, 'error');
    } finally {
      setDemoLoading(false);
    }
  };

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((d) => `${d.display} ${d.filename} ${d.id}`.toLowerCase().includes(needle));
  }, [rows, q]);

  if (loading) return <PageSkeleton rows={4} />;

  return (
    <>
      <SectionHead
        eyebrow="Phase 1 · ingestion"
        title="Datasets"
        sub="Everything registered by the loader — uploaded CSVs plus the bundled demo tables. Profile, validate, then design an experiment."
        actions={
          <>
            <input className="input" placeholder="Filter by name or id…" value={q} onChange={(e) => setQ(e.target.value)}
              style={{ width: 220, height: 34 }} aria-label="Filter datasets" />
            <Btn kind={open ? '' : 'primary'} icon={open ? 'x' : 'upload'}
              onClick={() => (open ? setParams({}) : setParams({ upload: '1' }))}>
              {open ? 'Close uploader' : 'Upload CSV'}
            </Btn>
          </>
        }
      />

      {error && <ErrorBanner error={error} retry={load} />}

      {/* ── Demo banner — shown when library is empty or always ── */}
      {rows.length === 0 && !open && (
        <Card style={{ background: 'color-mix(in srgb, var(--accent) 6%, var(--surface))', border: '1px solid color-mix(in srgb, var(--accent) 25%, transparent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 6 }}>
                <Icon name="zap" size={13} /> Quick start · demo dataset
              </div>
              <h3 style={{ fontSize: 'var(--t-lg)', fontWeight: 700, marginBottom: 6 }}>
                Breast Cancer Wisconsin Diagnostic
              </h3>
              <p className="muted" style={{ fontSize: 'var(--t-md)', maxWidth: '52ch' }}>
                569 patients · 30 numeric features · binary classification (malignant / benign).
                Click <strong>Try demo</strong> to auto-upload it and jump straight to profiling,
                or <strong>Download CSV</strong> to inspect it first.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10, flexShrink: 0 }}>
              {/* Plain anchor download — no JS required */}
              <a
                href={demoCsvUrl('breast-cancer')}
                download="breast_cancer.csv"
                className="btn"
                aria-label="Download demo CSV"
              >
                <Icon name="download" size={15} />
                <span>Download CSV</span>
              </a>
              <Btn
                kind="primary"
                icon={demoLoading ? 'refresh' : 'zap'}
                onClick={tryDemo}
                disabled={demoLoading}
                aria-label="Upload demo dataset and open profile"
              >
                {demoLoading ? 'Loading…' : 'Try demo'}
              </Btn>
            </div>
          </div>
        </Card>
      )}

      {/* ── Demo banner compact — shown when library already has datasets ── */}
      {rows.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 'var(--r)', background: 'var(--surface-2)', border: '1px solid var(--line)', marginBottom: 4 }}>
          <Icon name="zap" size={15} style={{ color: 'var(--accent)', flexShrink: 0 }} />
          <span className="tiny" style={{ color: 'var(--text-2)', flex: 1 }}>
            No dataset yet? Try the bundled <strong style={{ color: 'var(--text)' }}>Breast Cancer Wisconsin</strong> demo.
          </span>
          <a href={demoCsvUrl('breast-cancer')} download="breast_cancer.csv" className="btn btn-sm" style={{ flexShrink: 0 }}>
            <Icon name="download" size={13} />
            <span>Download CSV</span>
          </a>
          <Btn size="sm" kind="primary" icon={demoLoading ? 'refresh' : 'zap'} onClick={tryDemo} disabled={demoLoading}>
            {demoLoading ? 'Loading…' : 'Try demo'}
          </Btn>
        </div>
      )}

      {open && (
        <Card title="Ingest a new table" icon="upload" sub="The response is the Phase 1 registration receipt — profiling runs on the next request">
          <div className="grid g-side">
            <FileDropzone onFile={(f) => { setFile(f); if (f && !name) setName(f.name.replace(/\.csv$/i, '')); }} busy={busy} />
            <div className="stack" style={{ gap: 14 }}>
              <div className="field">
                <label htmlFor="ds-name">Display name <span className="dim">(optional)</span></label>
                <input id="ds-name" className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="breast_cancer_wisconsin" />
              </div>
              <Btn kind="primary" icon={busy ? 'refresh' : 'upload'} onClick={upload} disabled={!file || busy} style={{ width: '100%' }}>
                {busy ? 'Uploading and analysing…' : 'Upload & profile'}
              </Btn>
              <div className="eyebrow" style={{ marginBottom: -4 }}>Biomedical dataset requirements</div>
              <ul className="checks" style={{ marginTop: 4 }}>
                {[
                  ['UTF-8 CSV with one header row', true],
                  ['Numeric features preferred (PCA target)', true],
                  ['Binary classification column detectable', true],
                  ['≤ 100 MB per file', true]
                ].map(([t, okk]) => (
                  <li key={t} className={okk ? '' : 'no'}><Icon name={okk ? 'check' : 'x'} size={13} strokeWidth={2.4} />{t}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      <Card
        title={`Library · ${rows.length}`} icon="database" pad={false}
        actions={<Pill icon="filter">{filtered.length === rows.length ? 'all' : `${filtered.length} of ${rows.length}`}</Pill>}
      >
        {filtered.length === 0 ? (
          <Empty icon="database" title={rows.length ? 'No dataset matches that filter' : 'No datasets registered yet'}
            body={rows.length ? 'Clear the filter to see the full library.' : 'Upload a CSV above, or click Try demo to use the bundled breast cancer dataset.'}
            action={<Btn kind="primary" icon="upload" onClick={() => setParams({ upload: '1' })}>Upload CSV</Btn>} />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th className="strong">Dataset</th><th>Rows</th><th>Features</th><th>Size</th><th>Added</th><th>Status</th>
                  <th className="r" style={{ width: 210 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  <tr key={d.id} className="clickrow" onClick={(e) => {
                    if (e.target.closest('a,button')) return;
                    nav(`/datasets/${d.id}`);
                  }}>
                    <td className="strong">
                      <Link to={`/datasets/${d.id}`} style={{ display: 'block' }}>
                        {d.display ?? d.filename}
                        <span className="tiny dim mono" style={{ display: 'block', fontWeight: 500 }}>{d.id}</span>
                      </Link>
                    </td>
                    <td className="num">{int(d.rows)}</td>
                    <td className="num">{d.featureCount ?? '—'}</td>
                    <td className="num">{fmtSize(d.sizeMb)}</td>
                    <td className="tiny">{ago(d.uploadedAt)}</td>
                    <td><StatusPill status={d.status} /></td>
                    <td className="r">
                      <span className="row" style={{ justifyContent: 'flex-end', gap: 6 }}>
                        <Btn size="sm" to={`/datasets/${d.id}`} icon="eye">Profile</Btn>
                        <Btn size="sm" kind="quiet" to={`/experiments/new/${d.id}`} icon="zap">Benchmark</Btn>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
import FileDropzone from '@/components/FileDropzone.jsx';
import { Card, Btn, Empty, ErrorBanner, PageSkeleton, Pill, SectionHead, StatusPill } from '@/components/ui.jsx';
import { fmtSize, int, ago } from '@/lib/format.js';
import { toast } from '@/lib/toast.js';

export default function Datasets() {
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [q, setQ] = useState('');
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const open = params.get('upload') === '1';

  const load = () => {
    setLoading(true);
    api.listDatasets()
      .then((d) => { setRows(d.datasets ?? []); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.uploadDataset(file, name || undefined);
      toast('Dataset registered', `${res.filename} → ${res.datasetId}`, 'success');
      nav(`/datasets/${res.datasetId}`);
    } catch (e) {
      setError(e);
      toast('Upload rejected', e.message, 'error');
    } finally {
      setBusy(false);
      setFile(null);
    }
  };

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((d) => `${d.display} ${d.filename} ${d.id}`.toLowerCase().includes(needle));
  }, [rows, q]);

  if (loading) return <PageSkeleton rows={4} />;

  return (
    <>
      <SectionHead
        eyebrow="Phase 1 · ingestion"
        title="Datasets"
        sub="Everything registered by the loader — uploaded CSVs plus the bundled demo tables. Profile, validate, then design an experiment."
        actions={
          <>
            <input className="input" placeholder="Filter by name or id…" value={q} onChange={(e) => setQ(e.target.value)}
              style={{ width: 220, height: 34 }} aria-label="Filter datasets" />
            <Btn kind={open ? '' : 'primary'} icon={open ? 'x' : 'upload'}
              onClick={() => (open ? setParams({}) : setParams({ upload: '1' }))}>
              {open ? 'Close uploader' : 'Upload CSV'}
            </Btn>
          </>
        }
      />

      {error && <ErrorBanner error={error} retry={load} />}

      {open && (
        <Card title="Ingest a new table" icon="upload" sub="The response is the Phase 1 registration receipt — profiling runs on the next request">
          <div className="grid g-side">
            <FileDropzone onFile={(f) => { setFile(f); if (f && !name) setName(f.name.replace(/\.csv$/i, '')); }} busy={busy} />
            <div className="stack" style={{ gap: 14 }}>
              <div className="field">
                <label htmlFor="ds-name">Display name <span className="dim">(optional)</span></label>
                <input id="ds-name" className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="breast_cancer_wisconsin" />
              </div>
              <Btn kind="primary" icon={busy ? 'refresh' : 'upload'} onClick={upload} disabled={!file || busy} style={{ width: '100%' }}>
                {busy ? 'Uploading and analysing…' : 'Upload & profile'}
              </Btn>
              <div className="eyebrow" style={{ marginBottom: -4 }}>Biomedical dataset requirements</div>
              <ul className="checks" style={{ marginTop: 4 }}>
                {[
                  ['UTF-8 CSV with one header row', true],
                  ['Numeric features preferred (PCA target)', true],
                  ['Binary classification column detectable', true],
                  ['≤ 100 MB per file', true]
                ].map(([t, okk]) => (
                  <li key={t} className={okk ? '' : 'no'}><Icon name={okk ? 'check' : 'x'} size={13} strokeWidth={2.4} />{t}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      <Card
        title={`Library · ${rows.length}`} icon="database" pad={false}
        actions={<Pill icon="filter">{filtered.length === rows.length ? 'all' : `${filtered.length} of ${rows.length}`}</Pill>}
      >
        {filtered.length === 0 ? (
          <Empty icon="database" title={rows.length ? 'No dataset matches that filter' : 'No datasets registered yet'}
            body={rows.length ? 'Clear the filter to see the full library.' : 'Upload a CSV — the loader will register it, profile it and suggest a target column.'}
            action={<Btn kind="primary" icon="upload" onClick={() => setParams({ upload: '1' })}>Upload CSV</Btn>} />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th className="strong">Dataset</th><th>Rows</th><th>Features</th><th>Size</th><th>Added</th><th>Status</th>
                  <th className="r" style={{ width: 210 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  // the whole row is the affordance (Linear/Stripe tables do this); the
                  // explicit link and buttons stay clickable for keyboard and mid-click
                  <tr key={d.id} className="clickrow" onClick={(e) => {
                    if (e.target.closest('a,button')) return;
                    nav(`/datasets/${d.id}`);
                  }}>
                    <td className="strong">
                      <Link to={`/datasets/${d.id}`} style={{ display: 'block' }}>
                        {d.display ?? d.filename}
                        <span className="tiny dim mono" style={{ display: 'block', fontWeight: 500 }}>{d.id}</span>
                      </Link>
                    </td>
                    <td className="num">{int(d.rows)}</td>
                    <td className="num">{d.featureCount ?? '—'}</td>
                    <td className="num">{fmtSize(d.sizeMb)}</td>
                    <td className="tiny">{ago(d.uploadedAt)}</td>
                    <td><StatusPill status={d.status} /></td>
                    <td className="r">
                      <span className="row" style={{ justifyContent: 'flex-end', gap: 6 }}>
                        <Btn size="sm" to={`/datasets/${d.id}`} icon="eye">Profile</Btn>
                        <Btn size="sm" kind="quiet" to={`/experiments/new/${d.id}`} icon="zap">Benchmark</Btn>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
