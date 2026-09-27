import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api, { reportDownloadUrl, canFastForward } from '@/services/api.js';
import { useExperiment } from '@/hooks/useExperiment.js';
import Icon from '@/components/Icon.jsx';
import StageProgress from '@/components/StageProgress.jsx';
import MetricsTable from '@/components/MetricsTable.jsx';
import FeatureImportanceBar from '@/components/FeatureImportanceBar.jsx';
import MetricsBadge from '@/components/MetricsBadge.jsx';
import ConfusionHeat from '@/components/ConfusionHeat.jsx';
import VerdictCard from '@/components/VerdictCard.jsx';
import Disclaimer from '@/components/Disclaimer.jsx';
import { Card, Btn, Empty, ErrorBanner, Note, PageSkeleton, Pill, Rail, SectionHead, StatusPill, Tabs, KV } from '@/components/ui.jsx';
import { dur, int, score, titleize, modelLabel, pct, mb, statusMeta } from '@/lib/format.js';
import { toast } from '@/lib/toast.js';

export default function ExperimentDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { exp, status, results, explanation, resources, cost, recommendation, running, loading, error, elapsed, run, reload } = useExperiment(id);
  const [tab, setTab] = useState('progress');
  const [busy, setBusy] = useState(false);
  const demo = canFastForward();          // mock data (or live backend unreachable) only


  useEffect(() => {
    if (status?.isCompleted && tab === 'progress') setTab('results');
  }, [status?.isCompleted, tab]);

  const completed = !!results || status?.isCompleted;
  // the pill already spells the status out; only show the stage when it adds information
  const stageText = status?.stage ? titleize(status.stage) : 'idle';
  const showStage = stageText !== (status?.status ? statusMeta(status.status).label : null);

  if (loading) return <PageSkeleton rows={3} />;
  if (!exp) return <ErrorBanner error={error ?? { message: 'Experiment not found' }} retry={reload} />;

  const fastForward = async () => {
    try {
      await api.fastForwardRun(id);
      toast('Demo run fast-forwarded', 'the mock timeline jumped to COMPLETED', 'success');
      await reload();
      setTab('results');
    } catch (e) { toast('Not available', e.message, 'info'); }
  };

  const generate = async () => {
    setBusy(true);
    try {
      const r = await api.generateReport(id);
      const url = reportDownloadUrl(id);
      toast('Report generated', r.path ?? r.reportId ?? id, 'success');
      if (url) window.open(url, '_blank', 'noopener');
    } catch (e) {
      toast('Report failed', e.message, 'error');
    } finally { setBusy(false); }
  };

  return (
    <>
      <SectionHead
        eyebrow={exp.datasetId ? <Link to={`/datasets/${exp.datasetId}`} className="mono-link">{exp.datasetId}</Link> : 'Phase 10 · execution'}
        title={exp.name ?? id}
        sub={<span className="mono tiny">{id}</span>}
        actions={
          <>
            <Btn icon="refresh" kind="quiet" onClick={reload}>Refresh</Btn>
            {completed && <Btn icon="file" onClick={generate} disabled={busy}>{busy ? 'Rendering…' : 'Generate report'}</Btn>}
            {!running && <Btn kind="primary" icon="play" onClick={run}>{completed ? 'Re-run' : 'Start run'}</Btn>}
            {running && <Pill tone="accent" icon="clock">polling · 2s</Pill>}
            {running && demo && (
              <Btn kind="quiet" icon="zap" onClick={fastForward}
                   title="Demo data only — jumps the mock timeline to COMPLETED">
                Skip to results
              </Btn>
            )}
          </>
        }
      />

      <Card pad={false}>
        <div style={{ padding: 'var(--s-4) var(--s-5)', display: 'grid', gap: 12 }}>
          <div className="row row-wrap" style={{ gap: 14 }}>
            <StatusPill status={status?.status ?? exp.status} />
            {showStage && <span className="tiny dim mono">{stageText}</span>}
            <span className="tiny dim mono">elapsed {dur(elapsed)}</span>
            {status?.estimatedRemaining != null && !completed && <span className="tiny dim mono">~{dur(status.estimatedRemaining)} remaining</span>}
            {Number.isFinite(status?.circuitExecutions) && status.circuitExecutions > 0 && (
              <Pill tone="quantum" icon="atom">{int(status.circuitExecutions)} circuit executions</Pill>
            )}
            <span style={{ marginLeft: 'auto' }} className="num" >
              <span style={{ fontSize: 'var(--t-xl)', fontWeight: 650 }}>{((status?.progress ?? 0) * 100).toFixed(0)}%</span>
              <span className="tiny dim"> complete</span>
            </span>
          </div>
          <Rail value={status?.progress ?? 0} striped={running} label="experiment progress" />
        </div>
      </Card>

      {error && <ErrorBanner error={error} retry={reload} />}

      <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <Tabs
          value={tab} onChange={setTab}
          items={[
            { key: 'progress', label: 'Progress', icon: 'activity', count: running ? `${Math.round((status?.progress ?? 0) * 100)}%` : null },
            { key: 'results', label: 'Results', icon: 'bar', count: completed ? Object.keys(results?.models ?? {}).length : null },
            { key: 'explain', label: 'Explainability', icon: 'sparkles' },
            { key: 'cost', label: 'Cost & resources', icon: 'wallet' }
          ]}
        />
        {running && <span className="tiny dim">Results unlock when the executor reaches <span className="mono">COMPLETED</span>.</span>}
      </div>

      {tab === 'progress' && <ProgressTab status={status} running={running} exp={exp} onRun={run} />}
      {tab === 'results' && (completed ? <ResultsTab results={results} recommendation={recommendation} id={id} /> : <NotReady what="results" running={running} />)}
      {tab === 'explain' && (completed ? <ExplainTab explanation={explanation} results={results} /> : <NotReady what="explanations" running={running} />)}
      {tab === 'cost' && <CostTab cost={cost} resources={resources} results={results} status={status} />}

      <Disclaimer />
    </>
  );
}

const NotReady = ({ what, running }) => (
  <Card><Empty icon={running ? 'clock' : 'info'} title={running ? `${what} are not ready yet` : `No ${what} for this run`}
    body={running ? 'The executor writes these as soon as the benchmark stage finishes — this tab will fill in by itself.' : 'Start the run to produce them.'} /></Card>
);

/* ── Progress ─────────────────────────────────────────────────────────────── */
function ProgressTab({ status, running, exp }) {
  const demo = canFastForward();   // fixture data on screen? say so in the Mode row
  return (
    <div className="grid g-side">
      <Card title="Stage execution" icon="activity" sub="✓ done · ● running · ○ queued">
        <StageProgress status={status ?? { status: exp.status }} />
        {status?.isFailed && (
          <Note tone="err" title="Executor failed" icon="alert">
            <span className="mono tiny">{status.error ?? 'No error_message was returned by the status endpoint.'}</span>
          </Note>
        )}
      </Card>
      <div className="stack" style={{ gap: 'var(--s-4)' }}>
        <Card title="Executor" icon="cpu">
          <KV rows={[
            // never claim "live" while fixture data is on screen
            ['Mode', running ? <Pill key="m" tone={demo ? 'warn' : 'accent'} icon="zap">{demo ? 'demo fixture' : 'live'}</Pill> : <Pill key="m">{demo ? 'demo fixture · idle' : 'idle'}</Pill>],
            ['Polling', 'every 2 s · paused when tab hidden'],
            ['Message', <span className="mono tiny" key="msg">{status?.message ?? '—'}</span>],
            ['CPU', status?.resourceSnapshot?.cpu_percent != null ? `${status.resourceSnapshot.cpu_percent.toFixed(0)}%` : '—'],
            ['RAM', mb(status?.resourceSnapshot?.memory_mb)]
          ]} />
        </Card>
        <Card title="What runs here" icon="layers" sub="identical data for both arms">
          <ul className="checks">
            {['Train/test split + scaler fitted on train only', 'PCA reduced to the qubit budget', 'LR, SVM and RandomForest on the reduced matrix', 'VQC (PennyLane default.qubit) on the same matrix', 'Metrics, runtime and circuit counts recorded per model'].map((t) => (
              <li key={t}><Icon name="check" size={13} strokeWidth={2.4} />{t}</li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

/* ── Results ──────────────────────────────────────────────────────────────── */
function ResultsTab({ results, recommendation, id }) {
  const [cmModel, setCmModel] = useState('random_forest');
  const [cm, setCm] = useState(null);
  useEffect(() => { api.getConfusion(id, cmModel).then(setCm).catch(() => setCm(null)); }, [id, cmModel]);

  const modelKeys = Object.keys(results?.models ?? {});
  const best = results?.comparison?.bestModel;

  return (
    <>
      <VerdictCard recommendation={recommendation} comparison={results?.comparison} />

      <Card title="Model comparison" icon="bar" pad={false}
        sub="click a column to sort · green dot = best in column"
        actions={<Pill icon="info">7 metrics</Pill>}>
        <MetricsTable results={results} />
      </Card>

      <div className="grid g-side">
        <Card title="Metric spread" icon="activity" sub="per model, per metric">
          <MetricBars results={results} />
        </Card>
        <Card title="Confusion matrix" icon="target"
          sub="rows actual · columns predicted"
          actions={
            <select className="select" style={{ height: 30, width: 168, fontSize: 'var(--t-sm)' }} value={cmModel} onChange={(e) => setCmModel(e.target.value)} aria-label="Model for confusion matrix">
              {modelKeys.map((k) => <option key={k} value={k}>{modelLabel(k)}</option>)}
            </select>
          }>
          <div className="row" style={{ gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
            <ConfusionHeat matrix={cm?.matrix} labels={cm?.labels} />
            <div style={{ minWidth: 150, flex: 1 }}>
              <KV rows={[
                ['Model', modelLabel(cmModel)],
                ['Support', int((cm?.matrix?.[0] ?? []).concat(cm?.matrix?.[1] ?? []).reduce((a, b) => a + (Number(b) || 0), 0))],
                ['Best overall', best ? <Pill key="b" tone="ok" icon="award">{modelLabel(best)}</Pill> : '—']
              ]} />
              <p className="tiny dim" style={{ marginTop: 10 }}>Per-model metrics come from the stored results; nothing is re-inferred in the browser.</p>
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}

function MetricBars({ results }) {
  const metrics = [['accuracy', 'Accuracy'], ['recall', 'Recall'], ['f1', 'F1 score'], ['roc_auc', 'ROC-AUC']];
  const models = Object.values(results?.models ?? {});
  return (
    <div className="stack" style={{ gap: 18 }}>
      {metrics.map(([key, label]) => (
        <div key={key}>
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 7 }}>
            <span style={{ fontSize: 'var(--t-sm)', fontWeight: 640 }}>{label}</span>
            <span className="tiny dim mono">higher is better</span>
          </div>
          <div className="stack" style={{ gap: 5 }}>
            {models.map((m) => {
              const v = m.metrics?.[key];
              const quantum = m.modelType === 'QUANTUM';
              return (
                <div key={m.key} className="bar-row" style={{ gridTemplateColumns: '150px minmax(0,1fr) 62px' }}>
                  <span className="bar-name">{modelLabel(m.key)}</span>
                  <span className="bar-track"><span className={`bar-fill ${quantum ? 'violet' : ''}`} style={{ width: `${(Number.isFinite(v) ? v : 0) * 100}%` }} /></span>
                  <span className="num tiny" style={{ textAlign: 'right', color: quantum ? 'var(--quantum)' : 'var(--text-2)' }}>{score(v)}</span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Explainability ───────────────────────────────────────────────────────── */
function ExplainTab({ explanation, results }) {
  const e = explanation ?? {};
  const [mode, setMode] = useState('sample');
  const items = mode === 'sample' && e.importance?.length ? e.importance : (e.globalImportance?.length ? e.globalImportance : e.importance);

  return (
    <>
      <div className="grid g-side">
        <Card title="Prediction trace" icon="eye" sub="one held-out sample · uncalibrated score">
          {e.prediction ? (
            <div className="stack" style={{ gap: 16 }}>
              <div className="row row-wrap" style={{ gap: 10 }}>
                <Pill tone={e.prediction.value === 1 ? 'quantum' : 'ok'} icon={e.prediction.value === 1 ? 'alert' : 'check'}>
                  {e.prediction.value === 1 ? 'POSITIVE' : 'NEGATIVE'} · model output
                </Pill>
                {e.prediction.is_correct != null && (
                  <Pill tone={e.prediction.is_correct ? 'ok' : 'err'} icon={e.prediction.is_correct ? 'check' : 'x'}>
                    {e.prediction.is_correct ? 'matches held-out label' : 'differs from held-out label'}
                  </Pill>
                )}
                {e.sampleId && <span className="tiny dim mono">{e.sampleId}</span>}
              </div>
              <div>
                <div className="row" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
                  <span className="tiny dim" style={{ textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 650 }}>Model score</span>
                  <span className="num" style={{ fontSize: 'var(--t-2xl)', fontWeight: 640 }}>{score(e.prediction.score)}</span>
                </div>
                <Rail value={e.prediction.score} />
                <p className="tiny dim" style={{ marginTop: 8 }}>Uncalibrated — not a probability of disease. AUC 0.5–0.6 models can still emit 0.9 scores.</p>
              </div>
              {e.decisionReason && <Note icon="info" title="Why the model leaned this way">{e.decisionReason}</Note>}
            </div>
          ) : (
            <Note icon="info" title="Sample-level explanation not exposed yet">
              <span className="mono tiny">GET /experiments/{'{id}'}/explanation</span> currently returns model-level feature importance and the
              circuit structure only. Per-sample attribution needs the saved <span className="mono tiny">X_test.npy</span> artifacts
              (tracked as MH-01) — until then we show global importances rather than invent numbers.
              <div style={{ marginTop: 10 }}><Btn size="sm" onClick={() => setMode('global')}>View global importances →</Btn></div>
            </Note>
          )}
        </Card>

        <Card title="Quantum circuit" icon="atom" sub="structure that produced the decision">
          {e.circuit ? (
            <div className="stack" style={{ gap: 14 }}>
              <div className="qgrid">
                {[['Qubits', e.circuit.qubits], ['Layers', e.circuit.layers], ['Parameters', e.circuit.params],
                  ['Depth', e.circuit.depth], ['Two-qubit gates', e.circuit.twoQubitGates], ['Shots', e.circuit.shots]].map(([k, v]) => (
                  <div key={k}><div className="k">{k}</div><div className="v">{v ?? '—'}</div></div>
                ))}
              </div>
              <KV rows={[
                ['Encoding', e.circuit.encoding],
                ['Backend', e.circuit.backendType],
                ['Measurement', e.circuit.measurement ?? 'PauliZ(qubit_0)']
              ]} />
              {e.circuit.mapping && (
                <div>
                  <div className="tiny dim" style={{ marginBottom: 6 }}>feature → qubit mapping</div>
                  <div className="chips">
                    {Object.entries(e.circuit.mapping).map(([f, q]) => <Pill key={f} className="mono" icon="circuit">{f} → {q}</Pill>)}
                  </div>
                </div>
              )}
              {typeof e.circuit.diagram === 'string' && e.circuit.diagram.includes('\n') && (
                <pre className="mono" style={{ margin: 0, padding: 12, borderRadius: 'var(--r)', background: 'var(--canvas)', border: '1px solid var(--line)', fontSize: '0.68rem', overflow: 'auto', maxHeight: 180, lineHeight: 1.5 }}>
{e.circuit.diagram}
                </pre>
              )}
            </div>
          ) : <Note icon="info">No circuit metadata returned for this run.</Note>}
        </Card>
      </div>

      <Card title="Feature importance" icon="sliders"
        sub="positive push · negative push — model behaviour, not medical causality"
        actions={
          <div className="tabs" role="group" aria-label="importance scope">
            <button type="button" className="tab" aria-selected={mode === 'sample'} onClick={() => setMode('sample')}>Per-sample</button>
            <button type="button" className="tab" aria-selected={mode === 'global'} onClick={() => setMode('global')}>Global</button>
          </div>
        }>
        <FeatureImportanceBar items={items ?? []} top={12} tone="accent" />
        {!items?.length && <div className="tiny dim" style={{ marginTop: 10 }}>Nothing returned for this scope.</div>}
      </Card>

      {!!e.trace?.length && (
        <Card title="Pipeline trace" icon="circuit" sub="every artifact this run touched">
          <div className="rail">
            {e.trace.map((t, i) => (
              <React.Fragment key={i}>
                <div className="rail-item done">
                  <span className="rail-dot"><Icon name="check" size={11} strokeWidth={2.4} /></span>
                  <div><div className="rail-name">{t.component}</div>{t.detail && <div className="tiny dim mono" style={{ marginTop: 2 }}>{t.detail}</div>}</div>
                  <span className="rail-meta">{t.phase}</span>
                </div>
                {i < e.trace.length - 1 && <span className="rail-line" />}
              </React.Fragment>
            ))}
          </div>
        </Card>
      )}

      {(e.warnings?.length ?? 0) > 0 && (
        <div className="stack">
          {e.warnings.map((w, i) => <Note key={i} tone="warn" icon="shield">{w}</Note>)}
        </div>
      )}
    </>
  );
}

/* ── Cost ─────────────────────────────────────────────────────────────────── */
function CostTab({ cost, resources, results, status }) {
  const q = resources?.quantum ?? Object.values(results?.models ?? {}).find((m) => m.quantum)?.quantum ?? null;
  const breakdown = cost?.pipeline_cost_breakdown;
  const total = breakdown?.total_pipeline_seconds;
  const rows = Object.values(results?.models ?? {});

  return (
    <>
      <div className="grid g-side">
        <Card title="Quantum resources" icon="atom" sub="VQC circuit cost for this run">
          {q ? (
            <div className="qgrid" style={{ gridTemplateColumns: 'repeat(3, minmax(0,1fr))' }}>
              {[['Qubits', q.qubits], ['Circuit depth', q.depth], ['Gate count', q.gateCount],
                ['Two-qubit gates', q.twoQubitGates], ['Shots / execution', q.shots], ['Circuit executions', q.executions]].map(([k, v]) => (
                <div key={k}><div className="k">{k}</div><div className="v">{v == null ? '—' : int(v)}</div></div>
              ))}
            </div>
          ) : <Note icon="info">No quantum resources recorded — the run may be classical-only.</Note>}
          {q?.totalShots == null && q?.executions && q?.shots ? (
            <div className="tiny dim" style={{ marginTop: 12 }}>
              total shots ≈ <span className="num">{int(q.executions * q.shots)}</span> (executions × shots — derived in the UI from API numbers, not measured)
            </div>
          ) : null}
        </Card>

        <Card title="Financial cost" icon="wallet">
          <div className="stat" style={{ padding: 0 }}>
            <div className="k">Cloud quantum billing</div>
            <div className="v" style={{ color: 'var(--ok)' }}>₹0</div>
            <div className="d">{cost?.financial_cost_local?.note ?? 'Local quantum simulator. No cloud quantum cost.'}</div>
          </div>
          {cost?.scalability_assessment && (
            <div style={{ marginTop: 16 }}>
              <KV rows={[
                ['Environment', titleize(cost.scalability_assessment.current_environment)],
                ['Feasibility', <Pill key="f" tone={cost.scalability_assessment.this_experiment_status === 'FEASIBLE' ? 'ok' : 'warn'}>{titleize(cost.scalability_assessment.this_experiment_status)}</Pill>],
                ['Recommended max', `${cost.scalability_assessment.recommended_max_qubits ?? '—'} qubits`]
              ]} />
              <p className="tiny dim" style={{ marginTop: 10 }}>{cost.scalability_assessment.note}</p>
            </div>
          )}
        </Card>
      </div>

      {breakdown && (
        <Card title="Where the time went" icon="clock" sub={`total pipeline ${dur(total)}`}>
          <div className="stack" style={{ gap: 6 }}>
            {[['preprocessing_seconds', 'Preprocess'], ['feature_reduction_seconds', 'Feature reduction'],
              ['quantum_training_seconds', 'Quantum training'], ['evaluation_seconds', 'Evaluation']].map(([k, label]) => {
              const v = breakdown[k] ?? 0;
              return (
                <div key={k} className="bar-row">
                  <span className="bar-name">{label}</span>
                  <span className="bar-track"><span className={`bar-fill ${k === 'quantum_training_seconds' ? 'violet' : ''}`} style={{ width: `${total ? (v / total) * 100 : 0}%` }} /></span>
                  <span className="num tiny" style={{ textAlign: 'right' }}>{dur(v)}</span>
                </div>
              );
            })}
          </div>
          {cost.comparison_classical_baseline && (
            <Note tone="warn" icon="gauge" title="Classical baseline">
              {cost.comparison_classical_baseline.verdict ?? `Classical ${cost.comparison_classical_baseline.classical_model} trained in ${dur(cost.comparison_classical_baseline.classical_training_seconds)}.`}
            </Note>
          )}
        </Card>
      )}

      <Card title="Performance vs cost" icon="bar" pad={false} sub="the honest table — accuracy is not free">
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th className="strong">Model</th><th className="r">ROC-AUC</th><th className="r">Recall</th><th className="r">Train time</th><th className="r">Inference</th><th className="r">Peak memory</th><th className="r">Circuit executions</th></tr></thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.key} style={m.modelType === 'QUANTUM' ? { background: 'color-mix(in srgb, var(--quantum) 6%, transparent)' } : undefined}>
                  <td className="strong"><span className="row" style={{ gap: 8 }}><Icon name={m.modelType === 'QUANTUM' ? 'atom' : 'cpu'} size={14} />{modelLabel(m.key)}</span></td>
                  <td className="num r">{score(m.metrics?.roc_auc)}</td>
                  <td className="num r">{score(m.metrics?.recall)}</td>
                  <td className="num r">{dur(m.resources?.trainingTime)}</td>
                  <td className="num r">{dur(m.resources?.inferenceTime)}</td>
                  <td className="num r">{mb(m.resources?.memoryMb)}</td>
                  <td className="num r">{m.quantum ? int(m.quantum.executions) : <span className="dim">n/a</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="row row-wrap" style={{ gap: 8 }}>
        {status?.resourceSnapshot && (
          <>
            <MetricsBadge label="CPU" value={status.resourceSnapshot.cpu_percent} digits={0} hint="sampled during the run" />
            <MetricsBadge label="RAM" value={status.resourceSnapshot.memory_mb} />
          </>
        )}
        {cost?.computational_cost?.training?.wall_clock_time_seconds != null && (
          <MetricsBadge label="Wall clock" value={cost.computational_cost.training.wall_clock_time_seconds} />
        )}
        {cost?.quantum_cost?.total_shots != null && <MetricsBadge label="Total shots" value={cost.quantum_cost.total_shots} />}
      </div>
    </>
  );
}
