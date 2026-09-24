import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { experimentApi } from '../services/api'
import { 
  FlaskConical, 
  Plus, 
  Eye, 
  Zap, 
  CheckCircle2, 
  Clock, 
  AlertOctagon, 
  Database,
  Search,
  Filter
} from 'lucide-react'

function ExperimentsList() {
  const [experiments, setExperiments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadExperiments()
  }, [])

  const loadExperiments = async () => {
    try {
      const data = await experimentApi.list()
      setExperiments(data)
    } catch (error) {
      console.error('Failed to load experiments:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      'completed': 'badge-success',
      'failed': 'badge-error',
      'running_classical': 'badge-warning',
      'running_quantum': 'badge-warning',
      'preprocessing': 'badge-warning',
      'created': 'badge-classical'
    }
    return statusMap[status] || 'badge-classical'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div className="pipeline-icon active" style={{ margin: '0 auto 16px auto' }}>
          <Zap size={24} />
        </div>
        <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Loading experiment telemetry matrix...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cyan-primary)', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              <FlaskConical size={14} /> Experiment Execution Log
            </div>
            <h2 className="card-title" style={{ fontSize: '1.5rem' }}>
              Hybrid ML Experiments
            </h2>
          </div>
          <Link to="/datasets" className="btn btn-primary">
            <Plus size={18} />
            <span>New Experiment</span>
          </Link>
        </div>

        {experiments.length === 0 ? (
          <div style={{ textCenter: 'center', padding: '50px 20px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px dashed var(--border-color)', textAlign: 'center' }}>
            <FlaskConical size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px auto' }} />
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', fontWeight: 600 }}>No experiments created yet</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '4px', marginBottom: '20px' }}>
              Upload a biomedical dataset to launch your first hybrid Quantum vs Classical model comparison.
            </p>
            <Link to="/datasets" className="btn btn-secondary">
              <Database size={16} />
              <span>Browse Datasets</span>
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Experiment ID</th>
                  <th>Dataset Target</th>
                  <th>Execution Status</th>
                  <th>Created At</th>
                  <th>Completed At</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.id}>
                    <td>
                      <Link 
                        to={`/experiments/${exp.id}`} 
                        style={{ color: 'var(--cyan-primary)', fontWeight: 700, fontFamily: 'var(--font-mono)', textDecoration: 'none' }}
                      >
                        {exp.id}
                      </Link>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {exp.dataset_id}
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadge(exp.status)}`}>
                        {exp.status === 'completed' && <CheckCircle2 size={12} />}
                        {['running_classical', 'running_quantum', 'preprocessing'].includes(exp.status) && <Clock size={12} />}
                        {exp.status === 'failed' && <AlertOctagon size={12} />}
                        <span>{exp.status}</span>
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{formatDate(exp.created_at)}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{formatDate(exp.completed_at)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <Link 
                        to={`/experiments/${exp.id}`} 
                        className="btn btn-secondary"
                        style={{ padding: '6px 14px', fontSize: '0.825rem' }}
                      >
                        <Eye size={14} />
                        <span>View</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default ExperimentsList
