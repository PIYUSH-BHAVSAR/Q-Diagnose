import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { datasetApi } from '../services/api'
import { 
  UploadCloud, 
  FileSpreadsheet, 
  CheckCircle2, 
  X, 
  ArrowLeft, 
  ShieldCheck, 
  Info,
  Zap,
  FileCheck
} from 'lucide-react'

function DatasetUpload() {
  const [file, setFile] = useState(null)
  const [name, setName] = useState('')
  const [uploading, setUploading] = useState(false)
  const [dragover, setDragover] = useState(false)
  const navigate = useNavigate()

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragover(true)
  }

  const handleDragLeave = () => {
    setDragover(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragover(false)
    const files = e.dataTransfer.files
    if (files.length > 0 && files[0].name.endsWith('.csv')) {
      setFile(files[0])
      setName(files[0].name.replace('.csv', ''))
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setName(selectedFile.name.replace('.csv', ''))
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    try {
      const result = await datasetApi.upload(file, name)
      navigate(`/datasets/${result.dataset_id}`)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <div className="card">
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cyan-primary)', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            <Zap size={14} /> Dataset Ingestion Module
          </div>
          <h2 className="card-title" style={{ fontSize: '1.5rem' }}>
            Upload Biomedical Dataset
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '6px', fontSize: '0.925rem' }}>
            Upload a clinical CSV dataset to analyze feature vectors and execute hybrid Quantum-Classical preprocessing.
          </p>
        </div>

        {/* Drag and Drop Zone */}
        <div
          className={`upload-area ${dragover ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('fileInput').click()}
        >
          <input
            id="fileInput"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          {file ? (
            <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
              <div className="upload-icon-container" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.4)', color: 'var(--success-color)' }}>
                <FileCheck size={36} />
              </div>
              <p style={{ fontWeight: 700, fontSize: '1.1rem', color: '#ffffff' }}>{file.name}</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                Size: {(file.size / 1024).toFixed(2)} KB • Ready for processing
              </p>
              <div style={{ marginTop: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--cyan-primary)', background: 'rgba(6, 182, 212, 0.1)', padding: '4px 12px', borderRadius: '20px' }}>
                <CheckCircle2 size={14} /> Click to choose a different CSV file
              </div>
            </div>
          ) : (
            <div>
              <div className="upload-icon-container">
                <UploadCloud size={36} color="var(--cyan-primary)" />
              </div>
              <p style={{ fontWeight: 700, fontSize: '1.1rem', color: '#ffffff' }}>Drag and drop your biomedical CSV here</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '6px' }}>
                or click anywhere inside this box to browse local storage
              </p>
            </div>
          )}
        </div>

        {/* Dataset Name Input Field */}
        {file && (
          <div style={{ marginTop: '24px', animation: 'fadeIn 0.3s ease-out' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Dataset Name (Optional Identifier)
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: '100%' }}
              placeholder="e.g. Breast_Cancer_Diagnostic_2026"
            />
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ marginTop: '32px', display: 'flex', gap: '14px', alignItems: 'center' }}>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!file || uploading}
            style={{ padding: '14px 28px' }}
          >
            {uploading ? (
              <>
                <Zap size={18} className="pipeline-icon active" style={{ width: '18px', height: '18px', border: 'none', background: 'transparent' }} />
                <span>Ingesting Dataset...</span>
              </>
            ) : (
              <>
                <UploadCloud size={18} />
                <span>Upload & Analyze Dataset</span>
              </>
            )}
          </button>
          
          <button className="btn btn-secondary" onClick={() => navigate('/')} style={{ padding: '14px 22px' }}>
            <ArrowLeft size={16} />
            <span>Cancel</span>
          </button>
        </div>
      </div>

      {/* Dataset Requirements Guidelines */}
      <div className="card" style={{ marginTop: '24px' }}>
        <h3 className="card-title" style={{ fontSize: '1.1rem', marginBottom: '16px' }}>
          <ShieldCheck size={18} color="var(--cyan-primary)" />
          <span>Biomedical Dataset Requirements</span>
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-color)', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <CheckCircle2 size={18} color="var(--success-color)" />
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>CSV format with clean column headers</span>
          </div>
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-color)', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <CheckCircle2 size={18} color="var(--success-color)" />
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Binary classification target column</span>
          </div>
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-color)', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <CheckCircle2 size={18} color="var(--success-color)" />
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Numerical features preferred for PCA</span>
          </div>
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-color)', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <CheckCircle2 size={18} color="var(--success-color)" />
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Maximum file size: 100 MB</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DatasetUpload
