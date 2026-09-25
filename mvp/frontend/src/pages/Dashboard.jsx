import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { datasetApi, experimentApi } from '../services/api'
import { 
  Database, 
  FlaskConical, 
  CheckCircle2, 
  Clock, 
  UploadCloud, 
  Sparkles, 
  Stethoscope, 
  FileText, 
  SlidersHorizontal, 
  Binary, 
  Cpu, 
  BarChart3, 
  Award, 
  ShieldAlert, 
  ArrowRight,
  Zap
} from 'lucide-react'

function Dashboard() {
  const [stats, setStats] = useState({
    datasets: 0,
    experiments: 0,
    completed: 0,
    running: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [datasets, experiments] = await Promise.all([
        datasetApi.list(),
        experimentApi.list()
      ])

      const completed = experiments.filter(e => e.status === 'completed').length
      const running = experiments.filter(e => 
        ['preprocessing', 'running_classical', 'running_quantum'].includes(e.status)
      ).length

      setStats({
        datasets: datasets.length,
        experiments: experiments.length,
        completed,
        running
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div className="pipeline-icon active" style={{ margin: '0 auto 16px auto' }}>
          <Zap size={24} />
        </div>
        <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Loading platform telemetry...</p>
      </div>
    )
  }

  const pipelineStages = [
    { icon: UploadCloud, label: 'Upload CSV' },
    { icon: FileText, label: 'Profile' },
    { icon: SlidersHorizontal, label: 'Preprocess' },
    { icon: Binary, label: 'PCA' },
    { icon: Cpu, label: 'Train' },
    { icon: BarChart3, label: 'Compare' },
    { icon: Award, label: 'Recommend' }
  ]

  return (
    <div>
      {/* Hero Section */}
      <div className="card" style={{ position: 'relative', overflow: 'hidden', borderLeft: '4px solid var(--cyan-primary)' }}>
        <div style={{ position: 'absolute', top: '-50px', right: '-50px', width: '200px', height: '200px', background: 'var(--gradient-glow)', borderRadius: '50%', pointerEvents: 'none' }} />
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '20px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)', color: 'var(--cyan-primary)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '14px' }}>
              <Zap size={14} /> Quantum-Classical Machine Learning Architecture
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '10px', letterSpacing: '-0.02em' }}>
              Hybrid Quantum Disease Detection
            </h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '750px', fontSize: '1rem', lineHeight: '1.6' }}>
              Benchmark classical algorithms against Variational Quantum Classifier (VQC) models on high-dimensional biomedical data for accelerated early disease diagnostics.
            </p>
          </div>
          
          <Link to="/datasets" className="btn btn-primary">
            <UploadCloud size={18} />
            <span>Upload New Dataset</span>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span className="stat-label">Active Datasets</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--cyan-primary)' }}>
              <Database size={18} />
            </div>
          </div>
          <div className="stat-value">{stats.datasets}</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span className="stat-label">Total Experiments</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(139, 92, 246, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--violet-primary)' }}>
              <FlaskConical size={18} />
            </div>
          </div>
          <div className="stat-value">{stats.experiments}</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span className="stat-label">Completed Runs</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--success-color)' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--success-color)' }}>
            {stats.completed}
          </div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span className="stat-label">Running Circuits</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--warning-color)' }}>
              <Clock size={18} />
            </div>
          </div>
          <div className="stat-value" style={{ color: 'var(--warning-color)' }}>
            {stats.running}
          </div>
        </div>
      </div>

      {/* Quick Action Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 className="card-title">
              <UploadCloud size={20} color="var(--cyan-primary)" />
              <span>Upload Biomedical CSV</span>
            </h3>
            <p style={{ color: 'var(--text-secondary)', margin: '14px 0 24px 0', fontSize: '0.925rem' }}>
              Upload raw or tabular clinical indicators CSV datasets to profile missing values, feature types, and run ML pipeline optimization.
            </p>
          </div>
          <div>
            <Link to="/datasets" className="btn btn-primary" style={{ width: '100%' }}>
              <span>Upload CSV Dataset</span>
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 className="card-title">
              <Sparkles size={20} color="var(--violet-primary)" />
              <span>Try Demo Datasets</span>
            </h3>
            <p style={{ color: 'var(--text-secondary)', margin: '14px 0 20px 0', fontSize: '0.925rem' }}>
              Select pre-validated medical benchmark datasets to immediately compare classical algorithms vs quantum variational circuits.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              className="btn btn-secondary"
              style={{ flex: '1 1 auto', fontSize: '0.85rem' }}
              onClick={() => window.alert('Demo: Breast Cancer dataset')}
            >
              <Stethoscope size={14} color="var(--cyan-primary)" />
              <span>Breast Cancer</span>
            </button>
            <button 
              className="btn btn-secondary"
              style={{ flex: '1 1 auto', fontSize: '0.85rem' }}
              onClick={() => window.alert('Demo: Heart Disease dataset')}
            >
              <Stethoscope size={14} color="var(--error-color)" />
              <span>Heart Disease</span>
            </button>
            <button 
              className="btn btn-secondary"
              style={{ flex: '1 1 auto', fontSize: '0.85rem' }}
              onClick={() => window.alert('Demo: Parkinson\'s dataset')}
            >
              <Stethoscope size={14} color="var(--violet-primary)" />
              <span>Parkinson's</span>
            </button>
          </div>
        </div>
      </div>

      {/* How It Works Pipeline Section */}
      <div className="card" style={{ marginTop: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">
            <Cpu size={20} color="var(--cyan-primary)" />
            <span>End-to-End Quantum ML Pipeline</span>
          </h3>
          <span className="badge badge-quantum">
            QML Engine Architecture
          </span>
        </div>
        <div className="pipeline">
          {pipelineStages.map((stage, idx) => {
            const Icon = stage.icon
            return (
              <React.Fragment key={idx}>
                <div className="pipeline-stage completed">
                  <div className="pipeline-icon">
                    <Icon size={22} />
                  </div>
                  <div className="pipeline-label">{stage.label}</div>
                </div>
                {idx < pipelineStages.length - 1 && (
                  <span className="pipeline-arrow">→</span>
                )}
              </React.Fragment>
            )
          })}
        </div>
      </div>

      {/* Disclaimer */}
      <div 
        className="card" 
        style={{ 
          marginTop: '24px', 
          background: 'rgba(245, 158, 11, 0.05)', 
          border: '1px solid rgba(245, 158, 11, 0.2)',
          display: 'flex',
          gap: '16px',
          alignItems: 'flex-start'
        }}
      >
        <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--warning-color)', flexShrink: 0 }}>
          <ShieldAlert size={22} />
        </div>
        <div>
          <h3 style={{ fontSize: '1rem', color: '#fef08a', marginBottom: '6px', fontWeight: 700 }}>
            Research & Benchmarking Notice
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: '1.5' }}>
            This platform is strictly engineered for hybrid quantum-classical algorithmic benchmarking and experimental disease detection research. Results generated do not constitute formal clinical medical diagnoses.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
