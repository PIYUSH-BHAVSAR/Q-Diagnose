import React from 'react';
import Icon from './Icon.jsx';

/**
 * Required on every screen that shows a model output (guide_naeem.md §8 ·
 * implementaion_plan §84). Wording is deliberate: research system, never a diagnosis.
 */
export default function Disclaimer({ compact = false, style }) {
  if (compact) {
    return (
      <div className="tiny dim row" style={{ gap: 6, ...style }}>
        <Icon name="shield" size={12} style={{ color: 'var(--warn)' }} />
        Research / benchmarking system — model outputs are not clinical diagnoses.
      </div>
    );
  }
  return (
    <aside className="disclaimer" style={style}>
      <span className="ic"><Icon name="shield" size={16} /></span>
      <div>
        <b>Research / benchmarking system</b>
        <div style={{ marginTop: 3 }}>
          Hybrid quantum-classical comparison of model behaviour on tabular clinical data.
          Scores, importances and explanations are NOT clinical diagnoses and must not be used
          for patient care. No output here is validated for clinical decision-making.
        </div>
      </div>
    </aside>
  );
}
