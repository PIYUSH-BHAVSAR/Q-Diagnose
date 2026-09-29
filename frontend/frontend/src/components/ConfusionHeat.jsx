import React from 'react';
import { int } from '@/lib/format.js';

/** 2×2 heat grid: rows = actual class, columns = predicted class. */
export default function ConfusionHeat({ matrix, labels = ['Negative', 'Positive'], cell = 74 }) {
  const m = Array.isArray(matrix) && matrix.length === 2 ? matrix : null;
  if (!m) return <div className="tiny dim">Confusion matrix not exposed for this model by the API.</div>;
  const max = Math.max(1, ...(m[0] ?? []).concat(m[1] ?? []));
  const rows = [
    [0, [['TN', m[0]?.[0], 'var(--ok)'], ['FP', m[0]?.[1], 'var(--err)']]],
    [1, [['FN', m[1]?.[0], 'var(--err)'], ['TP', m[1]?.[1], 'var(--ok)']]]
  ];
  return (
    <div>
      <div className="tiny dim" style={{ marginBottom: 6 }}>actual ↓ / predicted →</div>
      <div style={{ display: 'grid', gridTemplateColumns: `72px repeat(2, ${cell}px)`, gap: 4, alignItems: 'center', justifyItems: 'stretch' }}>
        <span />
        <span className="dim tiny" style={{ textAlign: 'center' }}>pred {labels[0]}</span>
        <span className="dim tiny" style={{ textAlign: 'center' }}>pred {labels[1]}</span>
        {rows.map(([ri, cells]) => (
          <React.Fragment key={ri}>
            <span className="dim tiny" style={{ textAlign: 'right', paddingRight: 6 }}>actual {labels[ri]}</span>
            {cells.map(([tag, v, color]) => (
              <div
                key={tag}
                title={`${tag}: ${int(v)}`}
                style={{
                  height: cell - 14, borderRadius: 9, display: 'grid', placeItems: 'center',
                  background: `color-mix(in srgb, ${color} ${Math.round(((v ?? 0) / max) * 58 + 6)}%, var(--surface))`,
                  border: '1px solid var(--line)'
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div className="num" style={{ fontSize: 'var(--t-lg)', fontWeight: 650 }}>{int(v)}</div>
                  <div className="dim" style={{ fontSize: '0.64rem', letterSpacing: '0.06em' }}>{tag}</div>
                </div>
              </div>
            ))}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
