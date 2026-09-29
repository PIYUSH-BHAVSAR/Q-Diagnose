import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { reportDownloadUrl } from '@/services/api.js';
import Icon from '@/components/Icon.jsx';
import Disclaimer from '@/components/Disclaimer.jsx';
import { Card, Btn, Empty, ErrorBanner, PageSkeleton, Pill, SectionHead, Note } from '@/components/ui.jsx';
import { shortTime, titleize } from '@/lib/format.js';
import { toast } from '@/lib/toast.js';

export default function Reports() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.listReports();
      let list = r?.reports;
      if (!list) {
        const exps = await api.listExperiments();
        list = (exps ?? []).filter((e) => e.status === 'COMPLETED').map((e) => ({
          experiment_id: e.id, name: e.name ?? e.id, generatedAt: e.completedAt, status: 'NOT_GENERATED', path: null
        }));
      }
      setRows(list ?? []);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const generate = async (id) => {
    setBusyId(id);
    try {
      const rep = await api.generateReport(id);
      toast('Report ready', rep.path ?? rep.reportId ?? id, 'success');
      const url = reportDownloadUrl(id);
      if (url) window.open(url, '_blank', 'noopener');
      await load();
    } catch (e) {
      toast('Generation failed', e.message, 'error');
    } finally { setBusyId(null); }
  };

  if (loading) return <PageSkeleton rows={3} />;

  return (
    <>
      <SectionHead
        eyebrow="Phase 15 · reporting"
        title="Reports"
        sub="Self-contained HTML — profile, gates, plan, both arms, benchmark, explanation and cost. Generated server-side from stored results; nothing is recomputed in the browser."
        actions={<Btn icon="refresh" kind="quiet" onClick={load}>Refresh</Btn>}
      />

      {error && <ErrorBanner error={error} retry={load} />}

      <div className="grid g-3">
        {[['file', '16 sections', 'Ingestion → profiling → gates → split → reduction → arms → benchmark → recommendation → explanation → cost.'],
          ['wallet', 'Cost included', 'Quantum circuit counts, wall-clock and the ₹0 local-simulator statement, straight from the cost report.'],
          ['shield', 'Disclaimer baked in', 'The research-system notice is printed inside the document, not only in the UI.']]
          .map(([icon, t, d]) => (
            <Card key={t} title={t} icon={icon}><p className="muted" style={{ fontSize: 'var(--t-md)' }}>{d}</p></Card>
          ))}
      </div>

      <Card title={`Artifacts · ${rows?.length ?? 0}`} icon="file" pad={false}
        actions={<Pill icon="info">POST /api/reports/{'{experiment_id}'}</Pill>}>
        {!rows?.length ? (
          <Empty icon="file" title="No reports yet"
            body="A report becomes available once an experiment reaches COMPLETED — then it can be regenerated at any time."
            action={<Btn kind="primary" icon="flask" to="/experiments">Go to experiments</Btn>} />
        ) : (
          <ul className="list" style={{ listStyle: 'none', margin: 0 }}>
            {rows.map((r) => {
              const id = r.experiment_id ?? r.id;
              const generated = (r.status ?? r.report_id ?? r.reportId) && String(r.status ?? 'GENERATED').toUpperCase() !== 'NOT_GENERATED';
              return (
                <li key={r.report_id ?? r.reportId ?? id}>
                  <span className="brand-mark" style={{ width: 28, height: 28, borderRadius: 8 }}>
                    <Icon name="file" size={14} />
                  </span>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ fontWeight: 640 }}>{r.name ?? id}</div>
                    <div className="tiny dim mono">{r.report_id ?? r.reportId ?? `RPT-${id}`} {r.path ? `· ${r.path}` : ''}</div>
                  </div>
                  <div className="row" style={{ gap: 10, marginLeft: 'auto', alignItems: 'center' }}>
                    {r.size_kb ? <Pill>{r.size_kb} KB</Pill> : null}
                    <span className="tiny dim">{generated ? `rendered ${shortTime(r.generatedAt ?? r.generated_at)}` : 'not generated'}</span>
                    {generated && reportDownloadUrl(id) && <Btn size="sm" kind="quiet" icon="download" href={reportDownloadUrl(id)}>Download</Btn>}
                    <Btn size="sm" kind={generated ? 'quiet' : 'primary'} icon={busyId === id ? 'refresh' : 'sparkles'} disabled={busyId === id} onClick={() => generate(id)}>
                      {generated ? 'Regenerate' : 'Generate'}
                    </Btn>
                    <Btn size="sm" to={`/experiments/${id}`} icon="eye">Run</Btn>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <Note icon="info" title="Two report endpoints exist in the backend">
        <span className="mono tiny">POST /api/reports/{'{id}'}</span> writes <span className="mono tiny">RPT-{'{id}'}.html</span> while
        <span className="mono tiny"> POST /api/experiments/{'{id}'}/report</span> writes <span className="mono tiny">{'{id}'}_report.html</span>
        (the 16-section generator). This UI deliberately uses the <b>reports</b> pair so generate and download always agree — worth
        deleting one of the two server-side to avoid the trap.
      </Note>

      <Disclaimer />
    </>
  );
}
