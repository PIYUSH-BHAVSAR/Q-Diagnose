import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api.js';
import Icon from './Icon.jsx';

/** ⌘K / Ctrl+K jump list — navigation, datasets, experiments. Keyboard only. */
export default function CommandPalette({ open, onClose, onToggleTheme }) {
  const nav = useNavigate();
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(0);
  const [rows, setRows] = useState({ datasets: [], experiments: [] });
  const inputRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    let alive = true;
    setQ('');
    setSel(0);
    Promise.all([api.listDatasets(), api.listExperiments()])
      .then(([d, e]) => alive && setRows({ datasets: d.datasets ?? [], experiments: e ?? [] }))
      .catch(() => {});
    const t = setTimeout(() => inputRef.current?.focus(), 30);
    return () => { alive = false; clearTimeout(t); };
  }, [open]);

  const items = useMemo(() => {
    const base = [
      { kind: 'Go', label: 'Dashboard', icon: 'dashboard', run: () => nav('/') },
      { kind: 'Go', label: 'Datasets', icon: 'database', run: () => nav('/datasets') },
      { kind: 'Go', label: 'Experiments', icon: 'flask', run: () => nav('/experiments') },
      { kind: 'Go', label: 'Reports', icon: 'file', run: () => nav('/reports') },
      { kind: 'Run', label: 'New experiment', icon: 'plus', run: () => nav('/experiments/new') },
      { kind: 'Run', label: 'Upload CSV dataset', icon: 'upload', run: () => nav('/datasets?upload=1') },
      { kind: 'View', label: 'Toggle light / dark theme', icon: 'sun', run: () => onToggleTheme?.() }
    ];
    const ds = rows.datasets.map((d) => ({ kind: 'Dataset', label: d.display ?? d.filename ?? d.id, meta: d.id, icon: 'table', run: () => nav(`/datasets/${d.id}`) }));
    const ex = rows.experiments.map((e) => ({ kind: 'Experiment', label: e.name ?? e.id, meta: e.status, icon: 'activity', run: () => nav(`/experiments/${e.id}`) }));
    const all = [...base, ...ds, ...ex];
    if (!q.trim()) return all;
    const needle = q.toLowerCase();
    return all.filter((i) => `${i.label} ${i.kind} ${i.meta ?? ''}`.toLowerCase().includes(needle));
  }, [q, rows, nav, onToggleTheme]);

  useEffect(() => { setSel(0); }, [q]);

  if (!open) return null;
  const go = (i) => { i?.run?.(); onClose(); };

  return (
    <div className="palette-scrim" role="dialog" aria-modal="true" aria-label="Command palette"
      onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="palette">
        <div className="row" style={{ padding: '0 14px', borderBottom: '1px solid var(--line)' }}>
          <Icon name="search" size={16} style={{ color: 'var(--text-3)' }} />
          <input
            ref={inputRef} value={q} placeholder="Jump to a page, dataset or experiment…" aria-label="Search"
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'ArrowDown') { e.preventDefault(); setSel((s) => Math.min(items.length - 1, s + 1)); }
              if (e.key === 'ArrowUp') { e.preventDefault(); setSel((s) => Math.max(0, s - 1)); }
              if (e.key === 'Enter') { e.preventDefault(); go(items[sel]); }
              if (e.key === 'Escape') { e.preventDefault(); onClose(); }
            }}
          />
          <span className="kbd">esc</span>
        </div>
        <ul role="listbox" aria-label="Results">
          {items.length === 0 && <li className="dim">No matches</li>}
          {items.map((i, idx) => (
            <li
              key={`${i.kind}-${i.label}-${idx}`} role="option" aria-selected={idx === sel}
              onMouseEnter={() => setSel(idx)} onClick={() => go(i)}
            >
              <Icon name={i.icon} size={14} /> {i.label}
              <span className="kind">{i.meta ? `${i.meta} · ` : ''}{i.kind}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
