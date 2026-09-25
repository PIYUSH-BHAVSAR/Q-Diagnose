"""Reports API endpoints."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from backend.experiments.manager import ExperimentManager
from backend.core.logging import logger


router = APIRouter(prefix="/api/reports", tags=["reports"])

manager = ExperimentManager()
reports_dir = Path("./artifacts/reports")
reports_dir.mkdir(parents=True, exist_ok=True)


class ReportResponse(BaseModel):
    """Response for report generation."""
    report_id: str
    experiment_id: str
    status: str
    path: Optional[str]


@router.post("/{experiment_id}", response_model=ReportResponse)
async def generate_report(experiment_id: str):
    """Generate experiment report.
    
    Creates a comprehensive HTML report with all experiment results.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Report ID and status
    """
    try:
        experiment = manager.get_experiment(experiment_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    if experiment['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail="Experiment not completed"
        )
    
    results = experiment.get('results', {})
    
    # Generate HTML report
    report_id = f"RPT-{experiment_id}"
    report_path = reports_dir / f"{report_id}.html"
    
    html_content = _generate_html_report(experiment_id, experiment, results)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Generated report: {report_id}")
    
    return ReportResponse(
        report_id=report_id,
        experiment_id=experiment_id,
        status="generated",
        path=str(report_path)
    )


@router.get("/{experiment_id}")
async def get_report(experiment_id: str):
    """Get experiment report.
    
    Returns the HTML report for an experiment.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        HTML report content
    """
    report_id = f"RPT-{experiment_id}"
    report_path = reports_dir / f"{report_id}.html"
    
    if not report_path.exists():
        # Try to generate if not exists
        try:
            return await generate_report(experiment_id)
        except Exception:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
    
    return FileResponse(
        report_path,
        media_type='text/html',
        filename=f"{report_id}.html"
    )


@router.get("/{experiment_id}/download")
async def download_report(experiment_id: str):
    """Download experiment report.
    
    Downloads the report as an HTML file.
    
    Args:
        experiment_id: Experiment identifier
    
    Returns:
        Report file download
    """
    report_id = f"RPT-{experiment_id}"
    report_path = reports_dir / f"{report_id}.html"
    
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )
    
    return FileResponse(
        report_path,
        media_type='text/html',
        filename=f"{report_id}.html"
    )


def _generate_html_report(experiment_id: str, experiment: dict, results: dict) -> str:
    """Generate HTML report content."""
    
    dataset_profile = results.get('dataset_profile', {})
    comparison = results.get('comparison', {})
    models = results.get('models', {})
    resources = results.get('resource_usage', {})
    
    # Extract profile summary - handle list of dicts as "columns" field
    profile_name = dataset_profile.get('name', 'Unknown')
    profile_rows = dataset_profile.get('rows', 0)
    
    # Count actual columns (exclude the detailed list)
    columns_detailed = dataset_profile.get('columns', [])
    if isinstance(columns_detailed, list) and len(columns_detailed) > 0 and isinstance(columns_detailed[0], dict):
        profile_cols = len(columns_detailed)
    else:
        profile_cols = dataset_profile.get('columns', 0)
    
    profile_features = dataset_profile.get('numerical_columns_count', dataset_profile.get('n_numerical', 0))
    profile_target = dataset_profile.get('recommended_target', 'N/A')
    profile_missing = dataset_profile.get('missing_values_total', 0)
    profile_missing_pct = dataset_profile.get('missing_percentage', 0.0)
    profile_is_binary = dataset_profile.get('is_binary_classification', False)
    
    # Build model results table
    model_rows = ""
    best_classical_acc = 0
    best_quantum_acc = 0
    
    for name, data in models.items():
        metrics = data.get('metrics', {})
        acc = metrics.get('accuracy', 0)
        model_type = data.get('model_type', 'unknown')
        
        if model_type == 'classical' and acc > best_classical_acc:
            best_classical_acc = acc
        if model_type == 'quantum' and acc > best_quantum_acc:
            best_quantum_acc = acc
        
        # Highlight best model
        highlight = "background-color: #e8f5e9; font-weight: bold;" if (model_type == 'classical' and acc == best_classical_acc) or (model_type == 'quantum' and acc == best_quantum_acc) else ""
        
        badge = '<span style="background-color: #9c27b0; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 5px;">Quantum</span>' if model_type == 'quantum' else '<span style="background-color: #2196f3; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 5px;">Classical</span>'
        
        model_rows += f"""
        <tr style="{highlight}">
            <td><strong>{name}</strong> {badge}</td>
            <td>{metrics.get('accuracy', 0):.1%}</td>
            <td>{metrics.get('recall', 0):.1%}</td>
            <td>{metrics.get('f1', 0):.1%}</td>
            <td>{data.get('training_time', 0):.2f}s</td>
        </tr>
        """
    
    # Build comparison section
    qvc = comparison.get('quantum_vs_classical', {})
    recommendation = comparison.get('recommendation', 'N/A')
    best_model = comparison.get('best_model', 'N/A')
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Experiment Report - {experiment_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }}
        .header h2 {{
            font-size: 1.3em;
            font-weight: 300;
            opacity: 0.95;
            margin-bottom: 20px;
        }}
        .header-meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            font-size: 0.95em;
            opacity: 0.9;
        }}
        .header-meta div {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: inline-block;
        }}
        .section h3 {{
            font-size: 1.2em;
            color: #555;
            margin-top: 25px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .card-label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        .card-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-top: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            border-radius: 6px;
            overflow: hidden;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 16px;
            text-align: left;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
        .recommendation-box {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-left: 5px solid #667eea;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .recommendation-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .recommendation-text {{
            color: #555;
            line-height: 1.8;
            font-size: 1.05em;
        }}
        .metric-badge {{
            display: inline-block;
            background-color: #e8f5e9;
            color: #2e7d32;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            margin-left: 8px;
        }}
        .advantage {{
            color: #2e7d32;
            font-weight: bold;
        }}
        .disadvantage {{
            color: #c62828;
            font-weight: bold;
        }}
        .disclaimer {{
            background-color: #fff3e0;
            border-left: 4px solid #f57c00;
            padding: 20px;
            border-radius: 6px;
            margin-top: 30px;
        }}
        .disclaimer-title {{
            font-weight: bold;
            color: #e65100;
            margin-bottom: 8px;
        }}
        .disclaimer-text {{
            color: #666;
            font-size: 0.95em;
        }}
        footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #999;
            border-top: 1px solid #e0e0e0;
        }}
        .metric-comparison {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .comparison-item {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}
        .comparison-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}
        .comparison-values {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
        }}
        .comparison-values div {{
            flex: 1;
        }}
        .comparison-label-small {{
            font-size: 0.8em;
            color: #999;
            margin-bottom: 3px;
        }}
        .comparison-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 QuantWarriors QML Platform</h1>
            <h2>Hybrid Quantum-Classical Experiment Report</h2>
            <div class="header-meta">
                <div>📋 Experiment: <strong>{experiment_id}</strong></div>
                <div>🕐 Generated: <strong>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</strong></div>
            </div>
        </div>
        
        <div class="content">
            <!-- Dataset Profile Section -->
            <div class="section">
                <h2>📊 Dataset Profile</h2>
                <div class="grid">
                    <div class="card">
                        <div class="card-label">Samples</div>
                        <div class="card-value">{profile_rows}</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Total Columns</div>
                        <div class="card-value">{profile_cols}</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Features</div>
                        <div class="card-value">{profile_features}</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Target</div>
                        <div class="card-value" style="font-size: 1.3em;">{profile_target}</div>
                    </div>
                </div>
                <table>
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td><strong>Dataset Name</strong></td>
                        <td>{profile_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Task Type</strong></td>
                        <td>{'Binary Classification' if profile_is_binary else 'Multi-class Classification'}</td>
                    </tr>
                    <tr>
                        <td><strong>Missing Values</strong></td>
                        <td>{profile_missing} values ({profile_missing_pct:.1f}%)</td>
                    </tr>
                </table>
            </div>
            
            <!-- Model Results Section -->
            <div class="section">
                <h2>📈 Model Comparison Results</h2>
                <table>
                    <tr>
                        <th>Model</th>
                        <th>Accuracy</th>
                        <th>Recall</th>
                        <th>F1 Score</th>
                        <th>Training Time</th>
                    </tr>
                    {model_rows}
                </table>
                <p style="color: #666; font-size: 0.9em; margin-top: 10px;">
                    <em>✓ Highlighted rows indicate best performers in their category (Classical vs Quantum)</em>
                </p>
            </div>
            
            <!-- Quantum vs Classical -->
            <div class="section">
                <h2>⚛️ Quantum vs Classical Analysis</h2>
                <p style="margin-bottom: 15px;">Performance comparison between best quantum and best classical models:</p>
                
                <div class="metric-comparison">
                    <div class="comparison-item">
                        <div class="comparison-label">Best Classical</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #2196f3;">{comparison.get('best_classical', 'N/A')}</div>
                    </div>
                    <div class="comparison-item">
                        <div class="comparison-label">Best Quantum</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #9c27b0;">{comparison.get('best_quantum', 'N/A')}</div>
                    </div>
                    <div class="comparison-item">
                        <div class="comparison-label">Runtime Ratio</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #ff9800;">{qvc.get('runtime_diff', {}).get('ratio', 1):.1f}x</div>
                    </div>
                </div>
                
                <h3>Performance Metrics Comparison</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Classical</th>
                        <th>Quantum</th>
                        <th>Difference</th>
                    </tr>
"""
    
    metrics_diff = qvc.get('metrics_diff', {})
    for metric, values in metrics_diff.items():
        classical_val = values.get('classical', 0)
        quantum_val = values.get('quantum', 0)
        diff = values.get('difference', 0)
        is_quantum_better = values.get('quantum_better', False)
        
        # Format values
        if isinstance(classical_val, float):
            classical_str = f"{classical_val:.1%}"
        else:
            classical_str = str(classical_val)
            
        if isinstance(quantum_val, float):
            quantum_str = f"{quantum_val:.1%}"
        else:
            quantum_str = str(quantum_val)
            
        if isinstance(diff, float):
            diff_str = f"{diff:+.1%}"
        else:
            diff_str = str(diff)
        
        diff_class = "advantage" if is_quantum_better else "disadvantage"
        
        html += f"""
                    <tr>
                        <td><strong>{metric.replace('_', ' ').title()}</strong></td>
                        <td>{classical_str}</td>
                        <td>{quantum_str}</td>
                        <td class="{diff_class}">{diff_str}</td>
                    </tr>
"""
    
    html += f"""
                </table>
            </div>
            
            <!-- Recommendation Section -->
            <div class="section">
                <h2>📋 Final Recommendation</h2>
                <div class="recommendation-box">
                    <div class="recommendation-title">Preferred Model: <span style="color: #667eea;">{best_model.replace('_', ' ').title()}</span></div>
                    <div class="recommendation-text">
                        {recommendation}
                    </div>
                </div>
            </div>
            
            <!-- Resource Usage -->
            <div class="section">
                <h2>💻 Resource Usage</h2>
                <div class="grid">
                    <div class="card">
                        <div class="card-label">Peak Memory</div>
                        <div class="card-value">{resources.get('peak_memory_mb', 0):.1f} MB</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Total Time</div>
                        <div class="card-value">{resources.get('elapsed_time', 0):.1f}s</div>
                    </div>
                </div>
            </div>
            
            <!-- Disclaimer -->
            <div class="disclaimer">
                <div class="disclaimer-title">⚠️ Medical Disclaimer</div>
                <div class="disclaimer-text">
                    This platform is for research and benchmarking purposes only. Predictions generated by this system 
                    are <strong>not clinical diagnoses</strong>. All results should be validated by medical professionals 
                    before any clinical application. This system should not be used as a substitute for professional medical advice.
                </div>
            </div>
        </div>
        
        <footer>
            <p>Generated by QuantWarriors Hybrid Quantum Machine Learning Platform</p>
            <p style="margin-top: 8px; font-size: 0.9em;">© 2024 QuantWarriors Team - SIH 2026</p>
        </footer>
    </div>
</body>
</html>
"""
    
    return html
