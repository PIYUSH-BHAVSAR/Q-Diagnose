import React from 'react'
import { useNavigate } from 'react-router-dom'
import { FlaskConical, Database, ArrowRight, Zap } from 'lucide-react'

function ExperimentCreate() {
  const navigate = useNavigate()
  
  return (
    <div className="card" style={{ textAlign: 'center', padding: '60px 20px', maxWidth: '650px', margin: '40px auto' }}>
      <div className="upload-icon-container" style={{ margin: '0 auto 20px auto' }}>
        <FlaskConical size={36} color="var(--cyan-primary)" />
      </div>
      
      <h2 className="card-title" style={{ justifyContent: 'center', fontSize: '1.5rem', marginBottom: '10px' }}>
        Initialize Hybrid Experiment
      </h2>
      
      <p style={{ color: 'var(--text-secondary)', marginBottom: '28px', lineHeight: '1.6' }}>
        To launch a hybrid Quantum vs Classical machine learning experiment, select an ingested dataset from your library and trigger <strong>"Create Experiment"</strong>.
      </p>
      
      <button 
        className="btn btn-primary" 
        onClick={() => navigate('/datasets')}
        style={{ padding: '14px 28px' }}
      >
        <Database size={18} />
        <span>Go to Datasets Library</span>
        <ArrowRight size={16} />
      </button>
    </div>
  )
}

export default ExperimentCreate
