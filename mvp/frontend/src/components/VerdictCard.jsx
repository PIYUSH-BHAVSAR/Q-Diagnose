import React from 'react';
import Icon from './Icon.jsx';
import { score, titleize, dur } from '@/lib/format.js';
import { Pill } from './ui.jsx';

const VERDICT = {
  QUANTUM_ADVANTAGE: { icon: 'sparkles', blurb: 'Quantum beats the classical baseline on the primary metric at acceptable cost.' },
  QUANTUM_PARITY: { icon: 'activity', blurb: 'Quantum matches classical within noise — the benchmark is inconclusive on performance, cost decides.' },
  PARITY: { icon: 'activity', blurb: 'Both families perform comparably.' },
  TRADEOFF: { icon: 'sliders', blurb: 'Quantum wins on sensitivity, loses on compute — a genuine trade-off, not an advantage.' },
  CLASSICAL_PREFERRED: { icon: 'cpu', blurb: 'Classical is better or far cheaper here — VQC is not justified on this dataset.' },
  CLASSICAL_ADVANTAGE: { icon: 'cpu', blurb: 'Classical outperforms the quantum model on this run.' }
};

/**
 * The "wow" screen (implementaion_plan §83-84): classification in large type,
 * colour-coded, then the evidence that produced it.
 * decision colour comes from DECISION_COLORS so unknown/backend-drifted values
 * degrade to neutral instead of crashing the hero.
 */
export default function VerdictCard({ recommendation, comparison, status }) {
  const rec = recommendation ?? {};
  const decision = rec.decision ?? comparison?.classification ?? null;
  const meta = VERDICT[decision] ?? { icon: 'info', blurb: 'Recommendation engine did not return a classification for this run.' };
  const diffOf = (m) => comparison?.diff?.(m) ?? null;

  return (
    <section className="card">
      <div className="card-hd">
        <Icon name="gauge" size={17} style={{ color: 'var(--accent)' }} />
        <div>
          <h3>Quantum value assessment</h3>
          <div className="sub">Evidence-based classification from the benchmark engine</div>
        </div>
        <div className="card-hd-right">
          {rec.confidence && <Pill icon="target">confidence {rec.confidence}</Pill>}
          {status?.isRunning && <Pill tone="accent" icon="clock">computing</Pill>}
        </div>
      </div>

      <div className="verdict" style={{ '--vc': rec.color ?? 'var(--accent)', border: 0, borderRadius: 0, padding: 'var(--s-6) var(--s-5)' }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}><i className="dot" />Classification</div>
        <div className="word">{decision ? titleize(decision).replace(/Quantum |Classical /, (m) => m.trim() + ' ') : 'Awaiting benchmark'}</div>
        <div className="why">{meta.blurb}</div>

        {rec.text && (
          <p style={{ marginTop: 14, color: 'var(--text-2)', fontSize: 'var(--t-md)', maxWidth: '78ch', lineHeight: 1.6 }}>{rec.text}</p>
        )}

        {decision && (
          <div className="grid g-4" style={{ marginTop: 22, gap: 12 }}>
            {['accuracy', 'recall', 'roc_auc'].map((m) => {
              const d = diffOf(m);
              const cls = comparison?.metricsComparison?.[comparison.bestClassical]?.[m];
              const q = comparison?.metricsComparison?.[comparison.bestQuantum]?.[m === 'roc_auc' ? 'roc_auc' : m];
              return (
                <div key={m} className="cell" style={{ padding: '12px 14px', border: '1px solid var(--line)', borderRadius: 'var(--r)', background: 'var(--surface)' }}>
                  <div className="tiny dim">{titleize(m)} · quantum − classical</div>
                  <div className="num" style={{ fontSize: 'var(--t-xl)', marginTop: 4, color: d?.quantum_better ? 'var(--ok)' : 'var(--err)' }}>
                    {d ? `${d.difference > 0 ? '+' : '−'}${Math.abs(d.difference).toFixed(4)}` : '—'}
                  </div>
                  <div className="tiny dim mono" style={{ marginTop: 2 }}>{score(q)} vs {score(cls)}</div>
                </div>
              );
            })}
            <div className="cell" style={{ padding: '12px 14px', border: '1px solid var(--line)', borderRadius: 'var(--r)', background: 'var(--surface)' }}>
              <div className="tiny dim">Runtime ratio</div>
              <div className="num" style={{ fontSize: 'var(--t-xl)', marginTop: 4, color: 'var(--quantum)' }}>
                {comparison?.runtimeDiff?.ratio ? `${comparison.runtimeDiff.ratio.toFixed(1)}×` : '—'}
              </div>
              <div className="tiny dim mono" style={{ marginTop: 2 }}>
                {dur(comparison?.runtimeDiff?.classical)} vs {dur(comparison?.runtimeDiff?.quantum)}
              </div>
            </div>
          </div>
        )}
      </div>

      {(rec.reasoning?.length || comparison?.observations?.length) && (
        <ul className="checks" style={{ padding: 'var(--s-5)', borderTop: '1px solid var(--line)' }}>
          {(rec.reasoning?.length ? rec.reasoning : comparison.observations).slice(0, 5).map((r, i) => (
            <li key={i}><Icon name="check" size={13} strokeWidth={2.4} /><span>{r}</span></li>
          ))}
        </ul>
      )}
    </section>
  );
}
