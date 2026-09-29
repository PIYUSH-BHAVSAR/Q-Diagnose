import React, { useCallback, useRef, useState } from 'react';
import Icon from './Icon.jsx';
import { bytes } from '@/lib/format.js';

const MAX_MB = 100;

/**
 * Drag-and-drop CSV uploader. Keyboard reachable (Enter/Space), validates type +
 * size client-side, and reports problems through `onError` so the page can show
 * a styled banner instead of alert()/raw JSON.
 */
export default function FileDropzone({ onFile, onError, busy = false, title = 'Drop a biomedical CSV', hint = 'or click to browse — UTF-8, one header row, no merged cells' }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const [file, setFile] = useState(null);
  const [localErr, setLocalErr] = useState(null);

  const accept = useCallback((f) => {
    setLocalErr(null);
    if (!f) return;
    if (!/\.csv$/i.test(f.name)) {
      const m = 'Only .csv files are supported by the MVP ingestor.';
      setLocalErr(m); onError?.(m); return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      const m = `File is ${bytes(f.size)} — the ingest limit is ${MAX_MB} MB.`;
      setLocalErr(m); onError?.(m); return;
    }
    setFile(f);
    onFile?.(f);
  }, [onFile, onError]);

  return (
    <div>
      <div
        className={`drop ${over ? 'on' : ''}`}
        role="button" tabIndex={0}
        aria-busy={busy} aria-label={`${title}. ${hint}`}
        onClick={() => !busy && input.current?.click()}
        onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && !busy) { e.preventDefault(); input.current?.click(); } }}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); accept(e.dataTransfer.files?.[0]); }}
      >
        <input
          ref={input} type="file" accept=".csv,text/csv" style={{ display: 'none' }}
          onChange={(e) => accept(e.target.files?.[0])}
        />
        <div className={`drop-ic ${busy ? 'spin' : ''}`} style={busy ? { animation: 'spin 1.1s linear infinite' } : undefined}>
          <Icon name={file && !busy ? 'file' : 'upload'} size={20} />
        </div>
        {file ? (
          <>
            <div>
              <div style={{ fontWeight: 680, fontSize: 'var(--t-lg)' }}>{file.name}</div>
              <div className="tiny dim mono" style={{ marginTop: 3 }}>{bytes(file.size)} · registered on upload</div>
            </div>
            <button
              type="button" className="btn btn-sm btn-quiet"
              onClick={(e) => { e.stopPropagation(); setFile(null); onFile?.(null); }}
            >
              <Icon name="x" size={12} /> Clear
            </button>
          </>
        ) : (
          <>
            <div style={{ fontWeight: 680, fontSize: 'var(--t-lg)' }}>{title}</div>
            <div className="tiny dim">{hint}</div>
          </>
        )}
      </div>
      {localErr && (
        <div className="note err" style={{ marginTop: 12 }}>
          <div className="ic"><Icon name="alert" size={15} /></div>
          <div><b>File rejected</b><div style={{ marginTop: 2 }} className="mono tiny">{localErr}</div></div>
        </div>
      )}
    </div>
  );
}
