import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '@/services/api.js';
import Icon from '@/components/Icon.jsx';
import { Card, Btn, Empty, ErrorBanner, Modal, PageSkeleton, Pill, Rail, SectionHead, StatusPill } from '@/components/ui.jsx';
import { ago, int } from '@/lib/format.js';
import { toast } from '@/lib/toast.js';

const FILTERS = [
  ['ALL', 'All'], ['RUNNING', 'In flight'], ['COMPLETED', 'Completed'], ['FAILED', 'Failed']
];

export default function ExperimentsList() {
  const nav = useNavigate();
  const [rows, setRows] = useState([]);
  const [statuses, setStatuses] = useState({});
  const [filter, setFilter] = useState('ALL');
  const [q, setQ] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirm, setConfirm] = useState(null);

  const load = useCallback(async () => {
    try {
      const list = await api.listExperiments();
      setRows(list ?? []);
      setError(null);
      const live = (list ?? []).filter((e) => !['COMPLETED', 'FAILED'].includes(e.status)).slice(0, 6);
      const st = await Promise.all(live.map((e) => api.getStatus(e.id).catch(() => null)));
      setStatuses(Object.fromEntries(st.filter(Boolean).map((s, i) => [live[i].id, s])));
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(() => {
      if (document.visibilityState === 'visible') {
        setRows((cur) => {
          if (cur.some((e) => !['COMPLETED', 'FAILED'].includes(e.status))) load();
          return cur;
        });
      }
    }, 4000);
    return () => clearInterval(t);
  }, [load]);

  const filtered = useMemo(() => rows.filter((e) => {
    const okFilter = filter === 'ALL'
      ? true
      : filter === 'RUNNING' ? !['COMPLETED', 'FAILED'].includes(e.status)
        : e.status === filter;
    const okQ = !q.trim() || `${e.name} ${e.id} ${e.datasetId}`.toLowerCase().includes(q.toLowerCase());
    return okFilter && okQ;
  }), [rows, filter, q]);

  const counts = useMemo(() => ({
    all: rows.length,
    running: rows.filter((e) => !['COMPLETED', 'FAILED'].includes(e.status)).length,
    done: rows.filter((e) => e.status === 'COMPLETED').length,
    failed: rows.filter((e) => e.status === 'FAILED').length
  }), [rows]);

  const remove = async () => {
    try {
      await api.deleteExperiment(confirm.id);
      toast('Experiment deleted', confirm.id, 'success');
      setConfirm(null);
      load();
    } catch (e) {
      toast('Delete failed', e.message, 'error');
    }
  };

  if (loading) return <PageSkeleton rows={5} />;

  return (
    <>
      <SectionHead
        eyebrow="Phase 9–11 · orchestration"
        title="Experiments"
        sub="Each row is one hybrid run: identical split, identical scaler, classical arms versus the variational quantum classifier."
        actions={
          <>
            <input className="input" style={{ width: 190, height: 34 }} placeholder="Filter by id or name…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Filter experiments" />
            <Btn kind="primary" icon="plus" to="/experiments/new">New experiment</Btn>
          </>
        }
      />

      {error && <ErrorBanner error={error} retry={load} />}

      <div className="row row-wrap" style={{ gap: 8 }}>
        {FILTERS.map(([key, label]) => {
          const n = key === 'ALL' ? counts.all : key === 'RUNNING' ? counts.running : key === 'COMPLETED' ? counts.done : counts.failed;
          return (
            <button key={key} type="button" className={`pill ${filter === key ? 'solid' : ''}`} onClick={() => setFilter(key)} aria-pressed={filter === key}>
              {label}<span style={{ opacity: 0.7 }} className="num">{n}</span>
            </button>
          );
        })}
      </div>

      <Card pad={false} title={`Runs · ${filtered.length}`} icon="flask" sub="status polled from the executor while anything is in flight">
        {filtered.length === 0 ? (
          <Empty icon="flask" title={rows.length ? 'Nothing matches those filters' : 'No experiments yet'}
            body={rows.length ? 'Widen the filter or clear the search box.' : 'Start from a registered dataset — the planner picks the split, the PCA target and both arms.'}
            action={<Btn kind="primary" icon="zap" to="/experiments/new">Run a benchmark</Btn>} />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th className="strong">Experiment</th><th>Dataset</th><th style={{ width: 190 }}>Execution</th><th>Created</th><th>Finished</th><th className="r">Actions</th></tr></thead>
              <tbody>
                {filtered.map((e) => {
                  const st = statuses[e.id];
                  return (
                    <tr key={e.id}>
                      <td className="strong">
                        <Link to={`/experiments/${e.id}`}>
                          {e.name ?? e.id}
                          <span className="tiny dim mono" style={{ display: 'block', fontWeight: 500 }}>{e.id}</span>
                        </Link>
                      </td>
                      <td className="mono tiny">{e.datasetId ?? '—'}</td>
                      <td>
                        <div className="row" style={{ gap: 8 }}>
                          <StatusPill status={e.status} />
                          {st && !st.isCompleted && (
                            <span style={{ flex: 1, minWidth: 54 }}><Rail value={st.progress} striped label={`progress ${e.id}`} /></span>
                          )}
                        </div>
                        {st?.message && <div className="tiny dim mono" style={{ marginTop: 5 }}>{st.message}</div>}
                      </td>
                      <td className="tiny">{ago(e.createdAt)}</td>
                      <td className="tiny">{ago(e.completedAt)}</td>
                      <td className="r">
                        <span className="row" style={{ justifyContent: 'flex-end', gap: 6 }}>
                          <Btn size="sm" to={`/experiments/${e.id}`} icon="eye">Open</Btn>
                          <button type="button" className="btn btn-sm btn-quiet" aria-label={`Delete ${e.id}`} title="Delete"
                            onClick={() => setConfirm({ id: e.id, name: e.name ?? e.id })}><Icon name="trash" size={13} /></button>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal open={!!confirm} title="Delete this experiment?" onClose={() => setConfirm(null)}
        actions={<><Btn kind="quiet" onClick={() => setConfirm(null)}>Keep</Btn><Btn kind="danger" icon="trash" onClick={remove}>Delete</Btn></>}>
        <p>
          <span className="mono">{confirm?.id}</span> — its stored results and any generated report stay on disk,
          but the run will disappear from this workspace.
        </p>
      </Modal>
    </>
  );
}
