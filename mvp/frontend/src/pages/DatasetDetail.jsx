import React, { useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDataset } from '@/hooks/useDataset.js';
import api from '@/services/api.js';
import Icon from '@/components/Icon.jsx';
import Disclaimer from '@/components/Disclaimer.jsx';
import ClassDistributionChart from '@/components/ClassDistributionChart.jsx';
import { Card, Btn, ErrorBanner, KV, Note, PageSkeleton, Pill, Ring, SectionHead, StatusPill } from '@/components/ui.jsx';
import { int, pctRaw, ago, titleize } from '@/lib/format.js';

export default function DatasetDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { profile, validation, loading, error, profiling, reload: load } = useDataset(id);
  const [filter, setFilter] = useState('');

  const columns = useMemo(() => {
    const rows = profile?.columns ?? [];
    const needle = filter.trim().toLowerCase();
    return needle ? rows.filter((c) => c.name.toLowerCase().includes(needle)) : rows;
  }, [profile, filter]);

  if (loading && !profile) return <PageSkeleton rows={5} />;
  if (profiling) return <PageSkeleton rows={5} />;

  return (
    <>
      <SectionHead
        eyebrow={profile ? `Phase 2 · profile · ${profile.datasetId ?? id}` : 'Phase 2 · profile'}
        title={profile?.name ?? id}
        sub={profile ? `${int(profile.rows)} samples · ${profile.featureCount} columns · ${profile.numerical} numeric · ${profile.categorical} categorical · loaded ${ago(profile.profiledAt ?? null)}` : 'Reading profile from the data engine'}
        actions={
          <>
            <Btn icon="refresh" kind="quiet" onClick={load}>Re-profile</Btn>
            <Btn kind="primary" icon="flask" to={`/experiments/new/${id}`}>Design experiment</Btn>
          </>
        }
      />

      {error && <ErrorBanner error={error} retry={load} />}

      <div className="grid g-4">
        <Card pad={false}><div className="stat"><div className="k"><Icon name="table" size={14} />Samples</div><div className="v">{int(profile?.rows)}</div><div className="d">{profile?.duplicates ? `${profile.duplicates} duplicate rows` : 'no duplicates detected'}</div></div></Card>
        <Card pad={false}><div className="stat"><div className="k"><Icon name="layers" size={14} style={{ color: 'var(--accent)' }} />Features</div><div className="v" style={{ color: 'var(--accent)' }}>{int(profile?.featureCount)}</div><div className="d">{profile?.numerical ?? 0} numeric · {profile?.categorical ?? 0} categorical</div></div></Card>
        <Card pad={false}><div className="stat"><div className="k"><Icon name="alert" size={14} style={{ color: (profile?.missing?.pct ?? 0) > 5 ? 'var(--warn)' : 'var(--ok)' }} />Missing values</div><div className="v" style={{ color: (profile?.missing?.pct ?? 0) > 5 ? 'var(--warn)' : 'var(--ok)' }}>{pctRaw(profile?.missing?.pct ?? 0)}<small>{int(profile?.missing?.total)} cells</small></div><div className="d">median / mode imputation upstream</div></div></Card>
        <Card pad={false}>
          <div className="stat">
            <div className="k"><Icon name="target" size={14} style={{ color: 'var(--violet)' }} />Target detected</div>
            <div className="v" style={{ fontSize: 'var(--t-xl)', color: profile?.target ? 'var(--violet)' : 'var(--err)' }}>{profile?.target ?? 'none'}</div>
            <div className="d">{profile?.task ? titleize(profile.task) : 'task not classified'}</div>
          </div>
        </Card>
      </div>

      <div className="grid g-side">
        <Card
          title="Feature schema" icon="table" pad={false}
          sub={`${profile?.columns?.length ?? 0} columns · click a column name to reuse it as target`}
          actions={
            <>
              <input className="input" style={{ width: 180, height: 32, fontSize: 'var(--t-sm)' }} placeholder="Find column…"
                value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter columns" />
            </>
          }
        >
          {columns.length === 0 ? (
            <div style={{ padding: 'var(--s-5)' }}><Note icon="info" title="No column breakdown returned">The profile endpoint reported summary stats only for this dataset.</Note></div>
          ) : (
            <div className="table-wrap" style={{ maxHeight: 470 }}>
              <table className="data">
                <thead><tr><th className="strong">Column</th><th>Type</th><th className="r">Missing</th><th className="r">Unique</th><th className="r">Role</th></tr></thead>
                <tbody>
                  {columns.map((c) => (
                    <tr key={c.name}>
                      <td>
                        <button type="button" className="mono" onClick={() => setFilter(c.name)}
                          style={{ background: 'none', border: 0, padding: 0, color: 'var(--text)', fontWeight: 620, cursor: 'pointer' }}>
                          {c.name}
                        </button>
                      </td>
                      <td><Pill tone={c.numeric === false ? 'warn' : 'classical'}>{c.numeric === false ? 'categorical' : (c.dtype ?? 'numeric')}</Pill></td>
                      <td className="num r" style={{ color: c.missing ? 'var(--warn)' : 'var(--text-3)' }}>{int(c.missing ?? 0)}</td>
                      <td className="num r">{int(c.unique ?? 0)}</td>
                      <td className="r">
                        {c.isTargetCandidate ? <Pill tone="accent" icon="target">target candidate</Pill> : <span className="tiny dim">feature</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <div className="stack" style={{ gap: 'var(--s-4)' }}>
          <Card title="Target & class balance" icon="pie">
            <div className="row row-wrap" style={{ gap: 12, marginBottom: 14 }}>
              <Pill icon="target" tone="accent">{profile?.target ?? 'no target'}</Pill>
              <Pill icon="table">{titleize(profile?.task ?? 'unknown')}</Pill>
              {profile?.targetCandidates?.length > 1 && <Pill icon="info">{profile.targetCandidates.length} candidates</Pill>}
            </div>
            <ClassDistributionChart distribution={profile?.classDistribution} imbalanceRatio={profile?.imbalanceRatio} />
            {profile?.warnings?.length > 0 && (
              <ul className="checks" style={{ marginTop: 14 }}>
                {profile.warnings.map((w, i) => (
                  <li key={i} className="no"><Icon name="alert" size={13} style={{ color: 'var(--warn)' }} /><span>{typeof w === 'string' ? w : w?.message}</span></li>
                ))}
              </ul>
            )}
          </Card>

          {validation && (
            <Card title="Quality gates" icon="shield" sub={validation.qualityScore != null ? 'Phase 3 validation report' : 'Phase 3 — summary only'}>
              <div className="row" style={{ gap: 18, alignItems: 'center' }}>
                {validation.qualityScore != null
                  ? <Ring value={validation.qualityScore / 100} label="quality" sub="quality score" />
                  : (
                    <div style={{ display: 'grid', placeItems: 'center', width: 92, height: 92, borderRadius: '50%', border: '1px dashed var(--line-2)' }}>
                      <span className="tiny dim" style={{ textAlign: 'center', padding: '0 12px' }}>score not exposed by API</span>
                    </div>
                  )}
                <div style={{ minWidth: 0, flex: 1 }}>
                  <KV rows={[
                    ['Status', <StatusPill key="s" status={validation.passed ? 'PASS' : 'FAILED'} />],
                    ['ML ready', validation.readyForMl ? <Pill key="r" tone="ok" icon="check">yes</Pill> : <Pill key="r" tone="err" icon="x">no</Pill>],
                    ['Issues', int(validation.issues.length)],
                    ['Warnings', int(validation.warnings.length)]
                  ]} />
                </div>
              </div>
              {(validation.issues.length > 0 || validation.warnings.length > 0) && (
                <div className="stack" style={{ gap: 8, marginTop: 14 }}>
                  {validation.issues.slice(0, 4).map((m, i) => <Note key={`i${i}`} tone="err" icon="alert">{m}</Note>)}
                  {validation.warnings.slice(0, 4).map((m, i) => <Note key={`w${i}`} tone="warn" icon="shield">{m}</Note>)}
                </div>
              )}
            </Card>
          )}

          <Card title="Next" icon="arrowRight" pad={false}>
            <div style={{ padding: 'var(--s-4) var(--s-5)' }}>
              <p className="muted" style={{ fontSize: 'var(--t-md)', marginBottom: 14 }}>
                {validation?.readyForMl === false
                  ? 'The validator wants attention before training. Fix the listed issues, or pick a different target column.'
                  : 'This table passes ingestion gates. Design a run to lock the split, the PCA target and the model arms.'}
              </p>
              <Btn kind="primary" icon="flask" to={`/experiments/new/${id}`}>Design experiment</Btn>
            </div>
          </Card>

          <Disclaimer />
        </div>
      </div>
    </>
  );
}
