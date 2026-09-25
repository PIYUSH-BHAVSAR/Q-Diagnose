import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { datasetApi, experimentApi } from '../services/api'
import { 
  Database, 
  FlaskConical, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  PieChart, 
  Table, 
  Layers, 
  Zap, 
  FileSpreadsheet,
  Target,
  ArrowRight,
  ShieldCheck
} from 'lucide-react'

function DatasetDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [validation, setValidation] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      const [profileData, validationData] = await Promise.all([
        datasetApi.getProfile(id),
        datasetApi.validate(id)
      ])
      setProfile(profileData)
      setValidation(validationData)
    } catch (error) {
      console.error('Failed to load dataset:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateExperiment = async () => {
    try {
      const experiment = await experimentApi.create(id)
      navigate(`/experiments/${experiment.experiment_id}`)
    } catch (error) {
      console.error('Failed to create experiment:', error)
      alert('Failed to create experiment')
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div className="pipeline-icon active" style={{ margin: '0 auto 16px auto' }}>
          <Zap size={24} />
        </div>
        <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Profiling biomedical dataset dimensions...</p>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
        <XCircle size={36} color="var(--error-color)" style={{ margin: '0 auto 12px auto' }} />
        <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Dataset Not Found</h3>
        <p style={{ color: 'var(--text-secondary)' }}>The requested dataset ID could not be loaded from storage.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Header Profile Summary */}
      <div className="card">
        <div className="card-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cyan-primary)', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              <FileSpreadsheet size={14} /> Dataset Profile & Diagnostics
            </div>
            <h2 className="card-title" style={{ fontSize: '1.5rem' }}>
              {profile.dataset_name || `Dataset: ${id}`}
            </h2>
          </div>
          {validation?.ready_for_ml && (
            <button className="btn btn-primary" onClick={handleCreateExperiment}>
              <FlaskConical size={18} />
              <span>Create Experiment</span>
            </button>
          )}
        </div>

        {/* Dimension Stats */}
        <div className="stats-grid" style={{ marginBottom: 0 }}>
          <div className="stat-card">
            <div className="stat-label">Total Samples</div>
            <div className="stat-value">{profile.rows}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Features</div>
            <div className="stat-value">{profile.columns?.length || profile.columns}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Numerical Features</div>
            <div className="stat-value" style={{ color: 'var(--cyan-primary)' }}>
              {profile.numerical_columns_count}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Missing Values</div>
            <div className="stat-value" style={{ color: profile.missing_percentage > 5 ? 'var(--warning-color)' : 'var(--success-color)' }}>
              {profile.missing_percentage?.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Validation Status Card */}
      {validation && (
        <div className="card">
          <h3 className="card-title">
            <ShieldCheck size={20} color="var(--cyan-primary)" />
            <span>Validation & Pipeline Compatibility</span>
          </h3>
          
          <div style={{ marginTop: '20px' }}>
            {validation.issues && validation.issues.length > 0 && (
              <div style={{ marginBottom: '18px', background: 'rgba(239, 68, 68, 0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--error-color)', fontWeight: 700, marginBottom: '10px' }}>
                  <XCircle size={18} />
                  <span>Validation Issues Found</span>
                </div>
                <ul style={{ paddingLeft: '24px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  {validation.issues.map((issue, i) => (
                    <li key={i} style={{ color: 'var(--error-color)', marginBottom: '4px' }}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {validation.warnings && validation.warnings.length > 0 && (
              <div style={{ marginBottom: '18px', background: 'rgba(245, 158, 11, 0.08)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--warning-color)', fontWeight: 700, marginBottom: '10px' }}>
                  <AlertTriangle size={18} />
                  <span>Optimization Warnings</span>
                </div>
                <ul style={{ paddingLeft: '24px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  {validation.warnings.map((warning, i) => (
                    <li key={i} style={{ color: 'var(--warning-color)', marginBottom: '4px' }}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ 
              padding: '16px 20px', 
              borderRadius: '12px', 
              background: validation.ready_for_ml ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
              border: validation.ready_for_ml ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
              color: validation.ready_for_ml ? 'var(--success-color)' : 'var(--error-color)',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {validation.ready_for_ml ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                <span>{validation.ready_for_ml ? 'Dataset Verified Ready for Hybrid ML Pipeline' : 'Dataset Requires Cleansing Before Pipeline Execution'}</span>
              </div>
              {validation.ready_for_ml && (
                <span className="badge badge-success">ML Ready</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Target Distribution Card */}
      {profile.is_binary_classification && profile.class_distribution && (
        <div className="card">
          <h3 className="card-title">
            <PieChart size={20} color="var(--violet-primary)" />
            <span>Target Class Distribution</span>
          </h3>
          <div style={{ marginTop: '18px' }}>
            <p style={{ fontSize: '0.925rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Target Column:</strong>{' '}
              <span className="badge badge-quantum" style={{ marginLeft: '6px' }}>{profile.recommended_target}</span>
            </p>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              {Object.entries(profile.class_distribution).map(([cls, count]) => (
                <div key={cls} className="stat-card" style={{ flex: 1, minWidth: '180px' }}>
                  <div className="stat-label">Class {cls} Count</div>
                  <div className="stat-value" style={{ color: cls === '1' ? 'var(--cyan-primary)' : 'var(--violet-primary)' }}>
                    {count}
                  </div>
                </div>
              ))}
            </div>
            {profile.class_imbalance_ratio && (
              <div style={{ marginTop: '16px', background: 'rgba(15, 23, 42, 0.5)', padding: '12px 16px', borderRadius: '10px', border: '1px solid var(--border-color)', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                <Target size={16} color="var(--cyan-primary)" />
                <span>Class Imbalance Ratio: <strong style={{ color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{profile.class_imbalance_ratio.toFixed(2)}</strong></span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Columns Schema Table */}
      <div className="card">
        <h3 className="card-title">
          <Table size={20} color="var(--cyan-primary)" />
          <span>Feature Columns Schema</span>
        </h3>
        
        <div className="table-container" style={{ marginTop: '20px' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Column Name</th>
                <th>Data Type</th>
                <th>Missing Values</th>
                <th>Unique Values</th>
                <th>Target Candidate</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(profile.columns) && profile.columns.slice(0, 20).map((col, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{col.name}</td>
                  <td>
                    <span className={`badge ${col.is_numeric ? 'badge-classical' : 'badge-warning'}`}>
                      {col.is_numeric ? 'Numerical' : 'Categorical'}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{col.missing_count}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{col.unique_count}</td>
                  <td>
                    {col.is_target_candidate ? (
                      <span className="badge badge-success">Candidate Target</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {Array.isArray(profile.columns) && profile.columns.length > 20 && (
          <p style={{ color: 'var(--text-secondary)', marginTop: '14px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>
            Showing top 20 features of {profile.columns.length} total columns
          </p>
        )}
      </div>
    </div>
  )
}

export default DatasetDetail
