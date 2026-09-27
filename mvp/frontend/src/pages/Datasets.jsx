import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import api from '@/services/api.js';
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
