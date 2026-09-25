import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink, Link } from 'react-router-dom'
import { Atom, LayoutDashboard, Database, FlaskConical, Cpu } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import DatasetUpload from './pages/DatasetUpload'
import DatasetDetail from './pages/DatasetDetail'
import ExperimentCreate from './pages/ExperimentCreate'
import ExperimentDetail from './pages/ExperimentDetail'
import ExperimentsList from './pages/ExperimentsList'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="header">
          <div className="container header-content">
            <Link to="/" className="header-brand">
              <div className="brand-icon-wrapper">
                <Atom size={24} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <h1>QuantWarriors</h1>
                  <span className="header-tag">QML Core v1.0</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Hybrid Quantum-Classical Disease Detection Engine
                </span>
              </div>
            </Link>
            <nav className="nav">
              <NavLink 
                to="/" 
                end
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <LayoutDashboard size={16} />
                  <span>Dashboard</span>
                </div>
              </NavLink>
              <NavLink 
                to="/datasets" 
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Database size={16} />
                  <span>Datasets</span>
                </div>
              </NavLink>
              <NavLink 
                to="/experiments" 
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FlaskConical size={16} />
                  <span>Experiments</span>
                </div>
              </NavLink>
            </nav>
          </div>
        </header>

        <main className="container" style={{ padding: '32px 24px 60px 24px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<DatasetUpload />} />
            <Route path="/datasets/:id" element={<DatasetDetail />} />
            <Route path="/experiments" element={<ExperimentsList />} />
            <Route path="/experiments/new" element={<ExperimentCreate />} />
            <Route path="/experiments/:id" element={<ExperimentDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
