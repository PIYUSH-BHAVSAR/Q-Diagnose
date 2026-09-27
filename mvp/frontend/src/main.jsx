import React, { Component, Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';

class Boundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ padding: 40, fontFamily: 'system-ui' }}>
        <h2 style={{ margin: '0 0 8px' }}>The interface hit an unexpected state</h2>
        <p style={{ color: '#6b7386', margin: '0 0 16px' }}>
          Reload, or copy this message to the frontend owner — no data was lost.
        </p>
        <pre className="mono" style={{ padding: 14, borderRadius: 12, background: 'rgba(255,255,255,.05)', overflow: 'auto', fontSize: 12 }}>
          {String(this.state.error?.stack ?? this.state.error)}
        </pre>
        <button type="button" onClick={() => window.location.reload()} style={{ marginTop: 16, padding: '8px 14px', borderRadius: 10, border: '1px solid rgba(255,255,255,.16)', background: 'transparent', color: 'inherit', cursor: 'pointer' }}>
          Reload app
        </button>
      </div>
    );
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Boundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Boundary>
  </React.StrictMode>
);
