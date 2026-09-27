import React from 'react';
import Icon from './Icon.jsx';
import { STAGES } from '@/lib/fieldMap.js';
import { int, dur, modelLabel } from '@/lib/format.js';

const HUMAN = {
  preprocessing: 'Preprocess & split',
  classical_training: 'Classical training',
  quantum_training: 'VQC circuit training',
  benchmarking: 'Benchmark & compare',
  explaining: 'Explainability',
  completed: 'Complete'
};

/**
 * ✓ / ● / ○ stage indicator.
 * `status` is the ADAPTED status object (see src/lib/adapters.js#adaptStatus) so it
 * works whether the backend sends the contract's flat shape or its own nested one.
 */
export default function StageProgress({ status, compact = false }) {
  if (!status) return null;
  const raw = status.stage ?? '';
  const current = STAGES.indexOf(raw);
  const idx = current >= 0 ? current : (status.isCompleted ? STAGES.length - 1 : Math.min(STAGES.length - 1, Math.floor((status.progress ?? 0) * (STAGES.length - 1))));
  const done = status.isCompleted;
  const failed = status.isFailed;
  const completed = new Set(status.completedModels ?? []);

  return (
    <div className="rail" role="status" aria-live="polite" aria-label="experiment execution progress">
      {STAGES.map((stage, i) => {
        const state = done || i < idx ? 'done' : i === idx ? (failed ? 'failed' : 'active') : 'todo';
        const isTrain = stage === 'classical_training';
        const shown = isTrain ? ['logistic_regression', 'svm', 'random_forest'].map((m) => ({ m, ok: completed.has(m) })) : null;
        return (
          <React.Fragment key={stage}>
            <div className={`rail-item ${state}`}>
              <span className="rail-dot" style={state === 'failed' ? { borderColor: 'var(--err)', color: 'var(--err)' } : undefined}>
                {state === 'done' ? <Icon name="check" size={12} strokeWidth={2.4} /> : state === 'failed' ? <Icon name="x" size={12} strokeWidth={2.4} /> : null}
              </span>
              <div style={{ minWidth: 0 }}>
                <div className="rail-name">{HUMAN[stage] ?? stage}</div>
                {!compact && isTrain && (
                  <div className="row" style={{ gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                    {shown.map(({ m, ok }) => (
                      <span key={m} className={`pill ${ok ? 'ok' : ''}`} style={{ fontSize: '0.66rem', padding: '1px 7px' }}>
                        {ok && <Icon name="check" size={10} strokeWidth={2.6} />}{modelLabel(m)}
                      </span>
                    ))}
                  </div>
                )}
                {!compact && stage === 'quantum_training' && (
                  <div className="tiny dim" style={{ marginTop: 4 }}>
                    {status.currentEpoch != null && status.totalEpochs
                      ? `epoch ${status.currentEpoch}/${status.totalEpochs} · ` : ''}
                    circuits executed <span className="num" style={{ color: 'var(--quantum)' }}>{int(status.circuitExecutions ?? 0)}</span>
                  </div>
                )}
              </div>
              <span className="rail-meta">
                {state === 'done' ? 'done' : state === 'active' ? (status.currentModel ? modelLabel(status.currentModel) : 'running') : '—'}
              </span>
            </div>
            {i < STAGES.length - 1 && <span className="rail-line" />}
          </React.Fragment>
        );
      })}

      {!compact && (
        <div className="row" style={{ justifyContent: 'space-between', marginTop: 4, fontSize: 'var(--t-xs)', color: 'var(--text-3)' }}>
          <span className="mono">{status.message || (done ? 'completed' : 'waiting for executor')}</span>
          <span className="mono">elapsed {dur(status.elapsedSeconds)}{status.estimatedRemainingSeconds ? ` · ~${dur(status.estimatedRemainingSeconds)} left` : ''}</span>
        </div>
      )}
    </div>
  );
}
