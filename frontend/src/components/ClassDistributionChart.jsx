import React from 'react';
import { int, titleize } from '@/lib/format.js';
import { Pill } from './ui.jsx';

/** Class split as a stacked rail + per-class percentages + imbalance warning. */
export default function ClassDistributionChart({ distribution, imbalanceRatio, minorityLabel = 'minority' }) {
  const entries = Object.entries(distribution ?? {}).map(([k, v]) => [k, Number(v) || 0]);
  const total = entries.reduce((a, [, v]) => a + v, 0);
  if (!entries.length || !total) {
    return <div className="tiny dim">No target distribution returned (dataset has no detected classification target).</div>;
  }
  const colors = ['var(--cyan)', 'var(--violet)', 'var(--emerald)', 'var(--amber)'];
  const ratios = entries.map(([, v]) => v / total);
  const minority = Math.min(...ratios);
  const severe = minority < 0.3;

  return (
    <div className="stack" style={{ gap: 14 }}>
      <div style={{ display: 'flex', height: 12, borderRadius: 'var(--r-pill)', overflow: 'hidden', border: '1px solid var(--line)' }}>
        {entries.map(([k, v], i) => (
          <div
            key={k} title={`${k}: ${int(v)}`}
            style={{ width: `${(v / total) * 100}%`, background: colors[i % colors.length], opacity: 0.88, transition: 'width .5s var(--ease)' }}
          />
        ))}
      </div>
      <div className="row row-wrap" style={{ gap: 16 }}>
        {entries.map(([k, v], i) => (
          <div key={k} className="row" style={{ gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: 3, background: colors[i % colors.length] }} />
            <span style={{ fontSize: 'var(--t-sm)', color: 'var(--text-2)' }}>{titleize(k)}</span>
            <span className="num" style={{ fontSize: 'var(--t-md)', color: 'var(--text)' }}>{int(v)}</span>
            <span className="tiny dim">{((v / total) * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
      {(severe || imbalanceRatio != null) && (
        <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>
          {imbalanceRatio != null && <Pill icon="target" tone={severe ? 'warn' : ''}>imbalance {Number(imbalanceRatio).toFixed(2)}:1</Pill>}
          {severe && (
            <Pill tone="warn" icon="alert">
              {minorityLabel} class at {(minority * 100).toFixed(1)}% — class weights recommended
            </Pill>
          )}
        </div>
      )}
    </div>
  );
}
