import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { experimentApi, reportApi } from '../services/api'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { 
  Play, 
  Download, 
  CheckCircle2, 
  Clock, 
  AlertOctagon, 
  Atom, 
  Bot, 
  BarChart3, 
  Award, 
  Zap, 
  Cpu, 
  SlidersHorizontal,
  FileText,
  Activity
} from 'lucide-react'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

function ExperimentDetail() {
  const { id } = useParams()
  const [experiment, setExperiment] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [polling, setPolling] = useState(false)

  useEffect(() => {
    loadExperiment()
  }, [id])

  useEffect(() => {
    if (polling) {
      const interval = setInterval(loadExperiment, 3000)
      return () => clearInterval(interval)
    }
  }, [polling])

  const loadExperiment = async () => {
    try {
      const data = await experimentApi.get(id)
      setExperiment(data)

      if (data.status === 'completed') {
        setPolling(false)
        const resultsData = await experimentApi.getResults(id)
        setResults(resultsData)
      } else if (['running_classical', 'running_quantum', 'preprocessing'].includes(data.status)) {
        setPolling(true)
      }

      setLoading(false)
    } catch (error) {
      console.error('Failed to load experiment:', error)
      setLoading(false)
    }
  }

  const handleRun = async () => {
    try {
      await experimentApi.run(id)
      setPolling(true)
      loadExperiment()
    } catch (error) {
      console.error('Failed to run experiment:', error)
      alert('Failed to start experiment')
    }
  }

  const handleDownloadReport = () => {
    reportApi.download(id)
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div className="pipeline-icon active" style={{ margin: '0 auto 16px auto' }}>
          <Zap size={24} />
        </div>
        <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Reading experiment state & execution logs...</p>
      </div>
    )
  }

  if (!experiment) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
        <AlertOctagon size={36} color="var(--error-color)" style={{ margin: '0 auto 12px auto' }} />
        <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Experiment Not Found</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Unable to retrieve experiment ID from database.</p>
      </div>
    )
  }

  const isRunning = ['running_classical', 'running_quantum', 'preprocessing'].includes(experiment.status)
  const isCompleted = experiment.status === 'completed'

  const stagesList = ['created', 'preprocessing', 'running_classical', 'running_quantum', 'completed']

  return (
    <div>
      {/* Experiment Header */}
      <div className="card">
        <div className="card-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cyan-primary)', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              <Activity size={14} /> Experiment Controller
            </div>
            <h2 className="card-title" style={{ fontSize: '1.5rem', fontFamily: 'var(--font-mono)' }}>
              {experiment.name || experiment.id}
            </h2>
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className={`badge ${experiment.status === 'completed' ? 'badge-success' : experiment.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                {experiment.status === 'completed' && <CheckCircle2 size={12} />}
                {isRunning && <Clock size={12} />}
                {experiment.status === 'failed' && <AlertOctagon size={12} />}
                <span>{experiment.status}</span>
              </span>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                Target Dataset: <strong style={{ color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{experiment.dataset_id}</strong>
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            {experiment.status === 'created' && (
              <button className="btn btn-primary" onClick={handleRun}>
                <Play size={18} />
                <span>Run Experiment</span>
              </button>
            )}
            {isCompleted && (
              <button className="btn btn-secondary" onClick={handleDownloadReport}>
                <Download size={18} />
                <span>Download Report</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress Pipeline Stepper */}
      {(isRunning || experiment.status === 'created') && (
        <div className="card">
          <h3 className="card-title">
            <Zap size={20} color="var(--cyan-primary)" />
            <span>Execution Telemetry Pipeline</span>
          </h3>
          <div className="pipeline" style={{ marginTop: '10px' }}>
            {stagesList.map((stage, i) => {
              const isStageActive = experiment.status === stage
              const isStageCompleted = ['completed'].includes(experiment.status) || 
                (experiment.status === 'running_quantum' && i < 3) ||
                (experiment.status === 'running_classical' && i < 2)

              return (
                <React.Fragment key={stage}>
                  <div className={`pipeline-stage ${isStageActive ? 'active' : isStageCompleted ? 'completed' : ''}`}>
                    <div className="pipeline-icon">
                      {stage === 'created' && <FileText size={20} />}
                      {stage === 'preprocessing' && <SlidersHorizontal size={20} />}
                      {stage === 'running_classical' && <Bot size={20} />}
                      {stage === 'running_quantum' && <Atom size={20} />}
                      {stage === 'completed' && <CheckCircle2 size={20} />}
                    </div>
                    <div className="pipeline-label">
                      {stage.replace('_', ' ').toUpperCase()}
                    </div>
                  </div>
                  {i < stagesList.length - 1 && <span className="pipeline-arrow">→</span>}
                </React.Fragment>
              )
            })}
          </div>
        </div>
      )}

      {/* Results Dashboard */}
      {isCompleted && results && (
        <>
          {/* Model Metrics Table */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <BarChart3 size={20} color="var(--cyan-primary)" />
                <span>Classical vs Quantum Performance Matrix</span>
              </h3>
              <span className="badge badge-quantum">Benchmark Final</span>
            </div>
            
            <div className="table-container" style={{ marginTop: '10px' }}>
              {results.models && (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Model Name</th>
                      <th>Architecture</th>
                      <th>Accuracy</th>
                      <th>Recall</th>
                      <th>F1 Score</th>
                      <th>ROC-AUC</th>
                      <th>Execution Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(results.models).map(([name, data]) => (
                      <tr key={name}>
                        <td style={{ fontWeight: 700, color: '#ffffff' }}>{name.toUpperCase()}</td>
                        <td>
                          <span className={`badge ${data.model_type === 'quantum' ? 'badge-quantum' : 'badge-classical'}`}>
                            {data.model_type === 'quantum' ? <Atom size={12} /> : <Bot size={12} />}
                            <span>{data.model_type}</span>
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--cyan-primary)' }}>
                          {data.metrics?.accuracy !== undefined ? data.metrics.accuracy.toFixed(4) : 'N/A'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          {data.metrics?.recall !== undefined ? data.metrics.recall.toFixed(4) : 'N/A'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          {data.metrics?.f1 !== undefined ? data.metrics.f1.toFixed(4) : 'N/A'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          {data.metrics?.roc_auc !== undefined ? data.metrics.roc_auc.toFixed(4) : 'N/A'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          {data.training_time !== undefined ? `${data.training_time.toFixed(2)}s` : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Performance Bar Chart Visualization */}
          {results.models && (
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: '20px' }}>
                <Activity size={20} color="var(--violet-primary)" />
                <span>Model Metric Comparison Chart</span>
              </h3>
              <div style={{ height: '380px', width: '100%' }}>
                <Bar
                  data={{
                    labels: Object.keys(results.models).map(m => m.toUpperCase()),
                    datasets: [
                      {
                        label: 'Accuracy',
                        data: Object.values(results.models).map(m => m.metrics?.accuracy || 0),
                        backgroundColor: 'rgba(6, 182, 212, 0.85)',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        borderRadius: 6,
                      },
                      {
                        label: 'Recall',
                        data: Object.values(results.models).map(m => m.metrics?.recall || 0),
                        backgroundColor: 'rgba(139, 92, 246, 0.85)',
                        borderColor: '#8b5cf6',
                        borderWidth: 1,
                        borderRadius: 6,
                      },
                      {
                        label: 'F1 Score',
                        data: Object.values(results.models).map(m => m.metrics?.f1 || 0),
                        backgroundColor: 'rgba(52, 211, 153, 0.85)',
                        borderColor: '#34d399',
                        borderWidth: 1,
                        borderRadius: 6,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'top',
                        labels: {
                          color: '#cbd5e1',
                          font: { family: 'Plus Jakarta Sans', weight: 600 }
                        }
                      },
                      tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#ffffff',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12
                      }
                    },
                    scales: {
                      x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono' } }
                      },
                      y: {
                        beginAtZero: true,
                        max: 1,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono' } }
                      },
                    },
                  }}
                />
              </div>
            </div>
          )}

          {/* AI Recommendation Callout */}
          {results.comparison?.recommendation && (
            <div className="card recommendation">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Award size={24} color="var(--cyan-primary)" />
                <h3 style={{ margin: 0 }}>Optimal Model Recommendation</h3>
              </div>
              
              <div className="decision" style={{ margin: '16px 0 10px 0' }}>
                {results.comparison.best_model}
              </div>
              
              <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6', fontSize: '0.95rem' }}>
                {results.comparison.recommendation}
              </p>
            </div>
          )}

          {/* Quantum Resources Dashboard */}
          {results.models?.vqc?.metrics?.quantum_resources && (
            <div className="card">
              <h3 className="card-title">
                <Atom size={20} color="var(--violet-primary)" />
                <span>Quantum Hardware & Circuit Telemetry</span>
              </h3>
              
              <div className="stats-grid" style={{ marginTop: '20px', marginBottom: 0 }}>
                <div className="stat-card">
                  <div className="stat-label">Allocated Qubits</div>
                  <div className="stat-value" style={{ color: 'var(--cyan-primary)' }}>
                    {results.models.vqc.metrics.quantum_resources.n_qubits}
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Ansatz Circuit Layers</div>
                  <div className="stat-value" style={{ color: 'var(--violet-primary)' }}>
                    {results.models.vqc.metrics.quantum_resources.n_layers}
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Circuit Executions</div>
                  <div className="stat-value">
                    {results.models.vqc.metrics.quantum_resources.n_circuit_executions}
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-label">Training Latency</div>
                  <div className="stat-value" style={{ color: 'var(--success-color)' }}>
                    {results.models.vqc.metrics.quantum_resources.training_time?.toFixed(1)}s
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Error State */}
      {experiment.status === 'failed' && (
        <div className="card" style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--error-color)', marginBottom: '10px' }}>
            <AlertOctagon size={24} />
            <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Execution Failure</h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
            {experiment.error || 'Quantum simulator or classical preprocessor returned an unhandled exception.'}
          </p>
        </div>
      )}
    </div>
  )
}

export default ExperimentDetail
