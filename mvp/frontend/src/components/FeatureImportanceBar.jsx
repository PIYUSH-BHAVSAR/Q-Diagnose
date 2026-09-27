import React from 'react';
import { nf } from '@/lib/format.js';

/**
 * Horizontal importance bars. Positive push = green/cyan, negative push = rose.
 * `items`: [{ name, value, effect, featureValue }] — already normalised upstream.
 */
export default function FeatureImportanceBar({ items = [], max, top = 10, tone = 'accent', onSelect }) {
  const rows = items.slice(0, top);
  const bound = max ?? Math.max(1e-6, ...rows.map((r) => Math.abs(r.value ?? 0)));
  if (!rows.length) {
    return <div className="tiny dim" style={{ padding: '10px 0' }}>No importance data returned by the API for this model.</div>;
  }
  return (
    <div>
      {rows.map((f, i) => {
        const negative = f.effect === 'negative' || (f.effect == null && (f.value ?? 0) < 0);
        const w = Math.max(1.5, (Math.abs(f.value ?? 0) / bound) * 100);
        return (
          <button
            type="button" key={`${f.name}-${i}`} onClick={onSelect ? () => onSelect(f) : undefined}
            className="bar-row" title={`${f.name} · ${nf(f.value, 4)}${f.featureValue != null ? ` (feature value ${nf(f.featureValue, 3)})` : ''}`}
            style={{ background: 'transparent', border: 0, textAlign: 'left', width: '100%', cursor: onSelect ? 'pointer' : 'default', animationDelay: `${i * 24}ms` }}
          >
            <span className="bar-name mono">{f.name}</span>
            <span className="bar-track">
              <span className={`bar-fill ${negative ? 'neg' : tone === 'quantum' ? 'violet' : ''}`} style={{ width: `${w}%`, animationDelay: `${i * 24}ms` }} />
            </span>
            <span className="num r tiny" style={{ textAlign: 'right', color: negative ? 'var(--err)' : 'var(--text-2)' }}>
              {negative ? '−' : '+'}{nf(Math.abs(f.value ?? 0), 3)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
