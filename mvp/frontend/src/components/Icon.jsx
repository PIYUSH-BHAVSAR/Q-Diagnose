/* Inline icon set — one 24-grid, 1.5px stroke. No icon dependency, ~1 kB total. */
import React from 'react';

const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round' };

const PATHS = {
  dashboard: <><rect x="3.5" y="3.5" width="7" height="7" rx="2" /><rect x="13.5" y="3.5" width="7" height="7" rx="2" /><rect x="3.5" y="13.5" width="7" height="7" rx="2" /><rect x="13.5" y="13.5" width="7" height="7" rx="2" /></>,
  database: <><ellipse cx="12" cy="5.5" rx="7.5" ry="3" /><path d="M4.5 5.5v13c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-13" /><path d="M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3" /></>,
  flask: <><path d="M9 3h6M10 3v5.2L5.2 17.6A2.4 2.4 0 0 0 7.3 21h9.4a2.4 2.4 0 0 0 2.1-3.4L14 8.2V3" /><path d="M7.5 15h9" /></>,
  atom: <><circle cx="12" cy="12" r="2.2" /><ellipse cx="12" cy="12" rx="9.5" ry="4.2" /><ellipse cx="12" cy="12" rx="9.5" ry="4.2" transform="rotate(60 12 12)" /><ellipse cx="12" cy="12" rx="9.5" ry="4.2" transform="rotate(120 12 12)" /></>,
  upload: <><path d="M12 16V4m0 0L8 8m4-4 4 4" /><path d="M4 15v3a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-3" /></>,
  download: <><path d="M12 4v12m0 0 4-4m-4 4-4-4" /><path d="M4 16v2a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-2" /></>,
  play: <path d="M8 5.5 18 12 8 18.5z" />,
  plus: <path d="M12 5v14M5 12h14" />,
  check: <path d="m4.5 12.5 5 5 10-11" />,
  x: <path d="m6 6 12 12M18 6 6 18" />,
  search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></>,
  arrowRight: <path d="M4 12h15m0 0-5-5m5 5-5 5" />,
  chevronRight: <path d="m9.5 5 7 7-7 7" />,
  chevronDown: <path d="m5 9.5 7 7 7-7" />,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
  alert: <><path d="M12 3.8 2.8 20h18.4z" /><path d="M12 9.5v4.5M12 17h.01" /></>,
  shield: <><path d="M12 3 4.5 6v6c0 4.4 3.2 7.5 7.5 9 4.3-1.5 7.5-4.6 7.5-9V6z" /><path d="M9.5 12.5 11 14l3.8-4" /></>,
  sparkles: <><path d="M12 3.5l1.7 4.3 4.3 1.7-4.3 1.7L12 15.5l-1.7-4.3L6 9.5l4.3-1.7z" /><path d="M18.5 15.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9z" /></>,
  cpu: <><rect x="7" y="7" width="10" height="10" rx="2.5" /><path d="M10 3.5v3m4-3v3m-4 11v3m4-3v3M3.5 10h3m-3 4h3m11-4h3m-3 4h3" /></>,
  bar: <path d="M4.5 20V12m5.5 8V5.5m5 14.5v-6m5.5 6V9" />,
  pie: <><circle cx="12" cy="12" r="8.5" /><path d="M12 3.5V12l8 3" /></>,
  layers: <><path d="m12 3.5 8.5 4.5L12 12.5 3.5 8z" /><path d="m3.5 12.5 8.5 4.5 8.5-4.5" /><path d="m3.5 16.5 8.5 4.5 8.5-4.5" /></>,
  gauge: <><path d="M3.5 17.5a9 9 0 1 1 17 0" /><path d="M12 12.5 16 9" /><circle cx="12" cy="13.5" r="1.4" /></>,
  trash: <><path d="M4.5 7h15M9.5 7V4.5h5V7m-8 0 .8 12.5a2 2 0 0 0 2 1.9h5.4a2 2 0 0 0 2-1.9L19 7" /></>,
  refresh: <><path d="M20 5.5V10h-4.5" /><path d="M19.2 10A7.6 7.6 0 1 0 19 15" /></>,
  sun: <><circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2m0 15v2m9.5-9.5h-2m-15 0h-2m15.6-6.6-1.4 1.4m-11.4 11.4-1.4 1.4m0-14.2 1.4 1.4m11.4 11.4 1.4 1.4" /></>,
  moon: <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5" />,
  command: <path d="M8.5 5.5a2.5 2.5 0 1 0 0 5h7a2.5 2.5 0 1 0 0-5v13a2.5 2.5 0 1 0 0-5h-7a2.5 2.5 0 1 0 0 5z" />,
  eye: <><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12" /><circle cx="12" cy="12" r="2.8" /></>,
  filter: <path d="M4 6h16l-6 7v6l-4-2v-4z" />,
  zap: <path d="M13.5 3 5.5 13.5H11l-.5 7.5 8-10.5H13z" />,
  table: <><rect x="3.5" y="4.5" width="17" height="15" rx="2.5" /><path d="M3.5 10h17M9.5 10v9.5" /></>,
  target: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.5" /><circle cx="12" cy="12" r="1" /></>,
  wallet: <><rect x="3.5" y="6" width="17" height="13" rx="3" /><path d="M3.5 10.5h17M16 14.5h1.5" /></>,
  file: <><path d="M14 3.5H7a2.5 2.5 0 0 0-2.5 2.5v12A2.5 2.5 0 0 0 7 20.5h10a2.5 2.5 0 0 0 2.5-2.5V9z" /><path d="M14 3.5V9h5.5" /></>,
  activity: <path d="M2.5 12.5h4l2.5-6 3.5 12 3-6h6" />,
  sliders: <><path d="M4 8h11m3 0h2M4 16h3m3 0h10" /><circle cx="17" cy="8" r="2" /><circle cx="9" cy="16" r="2" /></>,
  circuit: <><circle cx="6" cy="6" r="2" /><circle cx="6" cy="18" r="2" /><circle cx="18" cy="12" r="2" /><path d="M8 6h4a4 4 0 0 1 4 4v.5M8 18h4a4 4 0 0 0 4-4V13.5" /></>,
  rocket: <><path d="M14.5 4.5c3 1 5 3.5 5 5-2 5.5-6 8-8.5 9.5L7 15l1-5c1.5-2.5 4-4.5 6.5-5.5" /><circle cx="14" cy="10" r="1.6" /><path d="M7 15l-2.5 1M10.5 18.5 9.5 21" /></>,
  info: <><circle cx="12" cy="12" r="8.5" /><path d="M12 11v6M12 7.6h.01" /></>,
  dots: <><circle cx="6" cy="12" r="1.4" /><circle cx="12" cy="12" r="1.4" /><circle cx="18" cy="12" r="1.4" /></>,
  award: <><circle cx="12" cy="9.5" r="5.5" /><path d="M8.6 14.2 7 21l5-2.4 5 2.4-1.6-6.8" /></>
};

export default function Icon({ name, size = 16, strokeWidth, className, style, ...rest }) {
  const g = PATHS[name] ?? PATHS.info;
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" className={className} style={style}
      stroke={S.stroke} strokeWidth={strokeWidth ?? S.strokeWidth} strokeLinecap="round" strokeLinejoin="round" fill="none"
      aria-hidden="true" focusable="false" {...rest}
    >
      {g}
    </svg>
  );
}
