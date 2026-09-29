import React from 'react';
import { score } from '@/lib/format.js';

/** Single metric pill: `recall 93.5%` — `best` adds the green dot highlight. */
export default function MetricsBadge({ label, value, digits, best = false, tone, hint }) {
  const shown = typeof value === 'number'
    ? (digits ? value.toFixed(digits) : value > 1 ? score(value) : `${(value * 100).toFixed(1)}%`)
    : '—';
  return (
    <span
      className={`pill ${best ? 'ok' : tone ? tone : ''}`}
      title={hint ?? `${label}: ${shown}`}
      style={{ gap: 7, padding: '4px 10px' }}
    >
      <span style={{ opacity: 0.75, fontWeight: 600 }}>{label}</span>
      <span className="num" style={{ fontWeight: 680 }}>{shown}</span>
    </span>
  );
}
