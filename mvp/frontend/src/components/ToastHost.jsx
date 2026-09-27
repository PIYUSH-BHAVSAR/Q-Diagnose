import React, { useEffect, useState } from 'react';
import { subscribe, dismiss } from '@/lib/toast.js';
import Icon from './Icon.jsx';

export default function ToastHost() {
  const [items, setItems] = useState([]);
  useEffect(() => subscribe(setItems), []);
  if (!items.length) return null;
  return (
    <div className="toast-host" role="status" aria-live="polite">
      {items.map((t) => (
        <div key={t.id} className={`toast ${t.kind === 'error' ? 'err' : t.kind === 'success' ? 'ok' : ''}`}>
          <Icon name={t.kind === 'error' ? 'alert' : t.kind === 'success' ? 'check' : 'info'} size={15}
            style={{ color: t.kind === 'error' ? 'var(--err)' : t.kind === 'success' ? 'var(--ok)' : 'var(--accent)', marginTop: 1 }} />
          <div style={{ minWidth: 0 }}>
            <div><b>{t.title}</b></div>
            {t.body && <div style={{ marginTop: 2 }}>{t.body}</div>}
          </div>
          <button type="button" className="btn btn-icon btn-quiet" style={{ marginLeft: 'auto', width: 26, height: 26 }}
            aria-label="Dismiss" onClick={() => dismiss(t.id)}><Icon name="x" size={13} /></button>
        </div>
      ))}
    </div>
  );
}
