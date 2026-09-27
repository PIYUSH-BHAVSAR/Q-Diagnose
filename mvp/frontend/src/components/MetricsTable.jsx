import React, { useMemo, useState } from 'react';
import Icon from './Icon.jsx';
import { METRIC_COLUMNS } from '@/lib/fieldMap.js';
import { score, dur, isQuantumModel, modelLabel } from '@/lib/format.js';
import { Pill } from './ui.jsx';

/**
 * Model comparison matrix. 7 metrics — including `precision`, which the guide's
 * version of this table omitted (ISSUES.md B-02). Missing metrics render "—"
 * instead of being dropped, so a contract gap is visible rather than silent.
 */
export default function MetricsTable({ results, highlight = true }) {
  const [sort, setSort] = useState({ key: 'f1', dir: -1 });
  const rows = useMemo(() => Object.values(results?.models ?? {}), [results]);

  const best = useMemo(() => {
    const out = {};
    for (const col of METRIC_COLUMNS) {
      const vals = rows.map((r) => r.metrics?.[col.key]).filter((v) => Number.isFinite(v));
      out[col.key] = vals.length ? Math.max(...vals) : null;
    }
    for (const key of ['trainingTime']) {
      const vals = rows.map((r) => r.resources?.[key]).filter((v) => Number.isFinite(v));
      out[key] = vals.length ? Math.min(...vals) : null;   // lower is better
    }
    return out;
  }, [rows]);

  const sorted = useMemo(() => {
    const v = [...rows];
    v.sort((a, b) => {
      const av = sort.key === 'model' ? a.label : a.metrics?.[sort.key];
      const bv = sort.key === 'model' ? b.label : b.metrics?.[sort.key];
      if (av == null) return 1;
      if (bv == null) return -1;
      return sort.dir * (av > bv ? 1 : av < bv ? -1 : 0);
    });
    return v;
  }, [rows, sort]);

  if (!rows.length) return null;
  const head = (label, key, align) => (
    <th
      key={key} className={`${align === 'r' ? 'r' : ''} ${sort.key === key ? 'strong' : ''}`}
      style={{ cursor: 'pointer', userSelect: 'none' }}
      onClick={() => setSort((s) => ({ key, dir: s.key === key ? -s.dir : -1 }))}
      aria-sort={sort.key === key ? (sort.dir === 1 ? 'ascending' : 'descending') : 'none'}
    >
      {label}{sort.key === key && <span style={{ opacity: 0.7, marginLeft: 4 }}>{sort.dir === 1 ? '↑' : '↓'}</span>}
    </th>
  );

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>{head('Model', 'model')}{METRIC_COLUMNS.map((c) => head(c.label, c.key, 'r'))}{head('Train', 'trainingTime', 'r')}</tr>
        </thead>
        <tbody>
          {sorted.map((m) => {
            const quantum = isQuantumModel(m);
            return (
              <tr key={m.key} style={quantum ? { background: 'color-mix(in srgb, var(--quantum) 6%, transparent)' } : undefined}>
                <td className="strong">
                  <span className="row" style={{ gap: 8 }}>
                    <Icon name={quantum ? 'atom' : 'cpu'} size={14} style={{ color: quantum ? 'var(--quantum)' : 'var(--text-3)' }} />
                    {modelLabel(m.key)}
                    {quantum && <Pill tone="quantum">VQC</Pill>}
                  </span>
                </td>
                {METRIC_COLUMNS.map((c) => {
                  const v = m.metrics?.[c.key];
                  const isBest = highlight && Number.isFinite(v) && best[c.key] != null && Math.abs(v - best[c.key]) < 1e-9;
                  return <td key={c.key} className={`num r ${isBest ? 'best' : ''}`}>{score(v)}</td>;
                })}
                <td className="num r">{Number.isFinite(m.resources?.trainingTime) ? dur(m.resources.trainingTime) : '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
