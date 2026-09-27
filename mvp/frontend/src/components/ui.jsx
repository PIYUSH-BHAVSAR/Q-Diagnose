import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from './Icon.jsx';
import { statusMeta } from '@/lib/format.js';

/* ── surfaces ───────────────────────────────────────────────────────────── */
export function Card({ title, sub, icon, actions, foot, pad = true, className = '', children, hover = false }) {
  return (
    <section className={`card ${hover ? 'card-hover' : ''} ${className}`}>
      {(title || actions) && (
        <header className="card-hd">
          {icon && <Icon name={icon} size={17} style={{ color: 'var(--accent)' }} />}
          <div>
            <h3>{title}</h3>
            {sub && <div className="sub">{sub}</div>}
          </div>
          {actions && <div className="card-hd-right">{actions}</div>}
        </header>
      )}
      <div className={pad ? 'card-pad' : ''}>{children}</div>
      {foot && <footer className="card-hd" style={{ borderBottom: 0, borderTop: '1px solid var(--line)' }}>{foot}</footer>}
    </section>
  );
}

export function SectionHead({ eyebrow, title, sub, actions }) {
  return (
    <div className="page-head">
      <div>
        {eyebrow && <div className="eyebrow" style={{ marginBottom: 8 }}><i className="dot" />{eyebrow}</div>}
        <h1 className={title.length > 26 ? 'page-title' : ''} style={title.length > 26 ? {} : { fontSize: 'var(--t-2xl)' }}>{title}</h1>
        {sub && <p className="page-sub">{sub}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

/* ── atoms ────────────────────────────────────────────────────────────────── */
export function Pill({ tone, children, icon }) {
  return <span className={`pill ${tone ? tone : ''}`}>{icon && <Icon name={icon} size={12} />}{children}</span>;
}

export function StatusPill({ status, withIcon = true }) {
  const m = statusMeta(status);
  const icon = withIcon ? (m.tone === 'ok' ? 'check' : m.tone === 'err' ? 'alert' : m.tone === 'quantum' ? 'atom' : 'clock') : null;
  return <Pill tone={m.kind} icon={icon}>{m.label}</Pill>;
}

export function Btn({ to, href, kind = '', size = '', icon, iconRight, children, onClick, type = 'button', disabled, title, ariaLabel, ...rest }) {
  const cls = `btn ${kind ? `btn-${kind}` : ''} ${size ? `btn-${size}` : ''}`.trim();
  const inner = (
    <>
      {icon && <Icon name={icon} size={size === 'lg' ? 18 : 15} />}
      {children}
      {iconRight && <Icon name={iconRight} size={14} />}
    </>
  );
  if (to) return <Link to={to} className={cls} title={title} onClick={onClick}>{inner}</Link>;
  if (href) return <a href={href} target="_blank" rel="noreferrer" className={cls} title={title} onClick={onClick}>{inner}</a>;
  return (
    <button type={type} className={cls} onClick={onClick} disabled={disabled} title={title} aria-label={ariaLabel} {...rest}>
      {inner}
    </button>
  );
}

export function IconBtn({ name, label, onClick, kind = '' }) {
  return (
    <button type="button" className={`btn btn-icon ${kind}`} onClick={onClick} title={label} aria-label={label}>
      <Icon name={name} size={16} />
    </button>
  );
}

export function CountUp({ value, format = (v) => v, ms = 750 }) {
  const [shown, setShown] = useState(() => (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? value : 0));
  const raf = useRef(0);
  useEffect(() => {
    if (!Number.isFinite(value)) { setShown(value); return undefined; }
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduce) { setShown(value); return undefined; }
    const t0 = performance.now();
    const step = (t) => {
      const k = Math.min(1, (t - t0) / ms);
      setShown(value * (1 - (1 - k) ** 3));
      if (k < 1) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [value, ms]);
  return <span className="num">{format(shown)}</span>;
}

export function StatCard({ label, value, unit, hint, tone = 'var(--text)', icon, delta }) {
  return (
    <div className="card stat card-hover">
      <div className="k">
        {icon && <Icon name={icon} size={14} style={{ color: tone }} />}
        {label}
      </div>
      <div className="v" style={{ color: tone }}>
        <CountUp value={typeof value === 'number' ? value : NaN} format={(v) => (Number.isFinite(v) ? formatMaybe(v, value) : String(value ?? '—'))} />
        {unit && <small>{unit}</small>}
      </div>
      {(hint || delta) && (
        <div className="d">
          {delta != null && <span className={`delta ${delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat'}`}>{delta > 0 ? '+' : ''}{delta}</span>}
          {hint}
        </div>
      )}
    </div>
  );
}

const formatMaybe = (v, target) => {
  const t = String(target);
  if (t.includes('.')) return v.toFixed(t.split('.')[1]?.length ?? 2);
  return Math.round(v).toLocaleString('en-US');
};

/** thin animated progress rail; `striped` while a job is running */
export function Rail({ value = 0, striped = false, label, style }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div style={style}>
      <div className={`progress ${striped ? 'striped' : ''}`} role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label ?? 'progress'}>
        <i style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function KV({ rows }) {
  return (
    <dl className="kv" style={{ gridTemplateColumns: `minmax(92px, auto) minmax(0,1fr)` }}>
      {rows.filter(Boolean).map(([k, v], i) => (
        <React.Fragment key={i}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </React.Fragment>
      ))}
    </dl>
  );
}

export function Ring({ value = 0, size = 92, label, sub }) {
  const r = (size - 12) / 2;
  const c = 2 * Math.PI * r;
  const dash = c * (1 - Math.max(0, Math.min(1, value)));
  return (
    <div style={{ display: 'grid', placeItems: 'center', gap: 6 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${label ?? 'score'} ${Math.round(value * 100)}%`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-3)" strokeWidth="7" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--accent)" strokeWidth="7" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={dash} transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset .8s var(--ease)', filter: 'drop-shadow(0 0 8px var(--glow-accent))' }}
        />
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central" className="num"
          style={{ fill: 'var(--text)', fontSize: size * 0.24, fontWeight: 600 }}>
          {Math.round(value * 100)}
        </text>
      </svg>
      {sub && <div className="tiny dim">{sub}</div>}
    </div>
  );
}

/* ── states ───────────────────────────────────────────────────────────────── */
export function Empty({ icon = 'sparkles', title, body, action }) {
  return (
    <div className="empty">
      <div className="ic"><Icon name={icon} size={22} /></div>
      <div>
        <h3 style={{ fontSize: 'var(--t-lg)' }}>{title}</h3>
        {body && <p className="muted" style={{ marginTop: 6, maxWidth: '46ch' }}>{body}</p>}
      </div>
      {action}
    </div>
  );
}

export function Note({ tone = '', icon, title, children, actions }) {
  return (
    <div className={`note ${tone}`}>
      <div className="ic"><Icon name={icon ?? (tone === 'err' ? 'alert' : tone === 'warn' ? 'shield' : 'info')} size={16} /></div>
      <div style={{ minWidth: 0 }}>
        {title && <div style={{ marginBottom: 2 }}><b>{title}</b></div>}
        <div>{children}</div>
      </div>
      {actions && <div style={{ marginLeft: 'auto' }}>{actions}</div>}
    </div>
  );
}

export function ErrorBanner({ error, retry }) {
  if (!error) return null;
  const message = typeof error === 'string' ? error : error.message ?? String(error);
  return (
    <Note tone="err" title={error.status ? `Request failed (${error.status})` : 'Something went wrong'}
      actions={retry && <Btn size="sm" kind="quiet" icon="refresh" onClick={retry}>Retry</Btn>}>
      <span className="mono" style={{ fontSize: 'var(--t-sm)' }}>{message}</span>
    </Note>
  );
}

export function Skeleton({ h = 14, w = '100', radius = 8, style }) {
  return <div className="skel" style={{ height: h, width: `${w}%`, borderRadius: radius, ...style }} />;
}

export function PageSkeleton({ rows = 4 }) {
  return (
    <div className="grid g-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div className="card stat" key={i}><Skeleton h={12} w="45" /><div style={{ height: 10 }} /><Skeleton h={30} w="70" /></div>
      ))}
      <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
        <div className="grid" style={{ gap: 12 }}>
          {Array.from({ length: rows }).map((_, i) => <Skeleton key={i} h={38} radius={10} />)}
        </div>
      </div>
    </div>
  );
}

/* ── tabs ─────────────────────────────────────────────────────────────────── */
export function Tabs({ items, value, onChange, id = 'tabs' }) {
  const refs = useRef([]);
  const move = (dir) => {
    const i = items.findIndex((t) => t.key === value);
    const next = items[(i + dir + items.length) % items.length];
    onChange(next.key);
    refs.current[items.findIndex((t) => t.key === next.key)]?.focus();
  };
  return (
    <div className="tabs" role="tablist" aria-label="sections" onKeyDown={(e) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); move(1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); move(-1); }
    }}>
      {items.map((t, i) => (
        <button
          key={t.key} ref={(el) => { refs.current[i] = el; }} role="tab" id={`${id}-t-${t.key}`}
          aria-selected={value === t.key} aria-controls={`${id}-p-${t.key}`} tabIndex={value === t.key ? 0 : -1}
          className="tab" onClick={() => onChange(t.key)}
        >
          {t.icon && <Icon name={t.icon} size={13} style={{ marginRight: 6, verticalAlign: '-2px' }} />}
          {t.label}
          {t.count != null && <span className="count">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

/* ── modal ────────────────────────────────────────────────────────────────── */
export function Modal({ open, title, children, onClose, actions }) {
  useEffect(() => {
    if (!open) return undefined;
    const h = (e) => e.key === 'Escape' && onClose?.();
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="scrim" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.target === e.currentTarget && onClose?.()}>
      <div className="modal">
        <div className="spread" style={{ marginBottom: 10 }}>
          <h3 style={{ fontSize: 'var(--t-lg)' }}>{title}</h3>
          <IconBtn name="x" label="Close" onClick={onClose} kind="quiet" />
        </div>
        <div className="muted" style={{ fontSize: 'var(--t-md)' }}>{children}</div>
        {actions && <div className="row" style={{ justifyContent: 'flex-end', marginTop: 20 }}>{actions}</div>}
      </div>
    </div>
  );
}
