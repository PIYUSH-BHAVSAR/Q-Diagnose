# run_pipeline.py
# End-to-end demo of the full Q-Diagnose data pipeline (Phases 2-6)
# Run with: Q-Diagnose/venv/Scripts/python Q-Diagnose/run_pipeline.py

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np

from data.adapters      import DataAdapter
from data.profiler      import DataProfiler
from data.validator     import DataValidator
from data.preprocessing import DataPreprocessor
from features.pipeline  import FeaturePipeline
from features.reducer   import DimensionalityReducer

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def separator(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def subsection(title):
    print(f"\n── {title} ──")

def ok(msg):
    print(f"  ✅  {msg}")

def info(msg):
    print(f"  ℹ️   {msg}")

def warn(msg):
    print(f"  ⚠️   {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Run pipeline for one dataset
# ─────────────────────────────────────────────────────────────────────────────

def run_for_dataset(dataset_name: str, experiment_id: str):

    separator(f"DATASET: {dataset_name.upper()}")

    # ── PHASE 2: Adapter ─────────────────────────────────────────────────────
    subsection("PHASE 2 — Data Adapter")
    adapter = DataAdapter(dataset_name=dataset_name)
    df = adapter.load(os.path.join(FIXTURES, f"{dataset_name}.csv"))

    ok(f"Loaded {len(df)} rows × {len(df.columns)} columns")
    info(f"Columns: {list(df.columns)}")
    info(f"Sample:\n{df.head(3).to_string(index=False)}")

    # ── PHASE 3: Profiler ─────────────────────────────────────────────────────
    subsection("PHASE 3 — Data Profiler")
    profiler = DataProfiler()
    profile  = profiler.profile(df, dataset_id=f"DS-{dataset_name}")

    ok(f"Profile ID    : {profile['profile_id']}")
    ok(f"Modality      : {profile['modality']}")
    ok(f"Rows          : {profile['dimensions']['rows']}")
    ok(f"Columns       : {profile['dimensions']['columns']}")
    ok(f"Numerical     : {profile['features']['numerical']}")
    ok(f"Categorical   : {profile['features']['categorical']}")
    ok(f"Missing total : {profile['missing_values']['total']}")
    ok(f"Duplicates    : {profile['duplicates']['candidate_count']}")
    ok(f"Target        : {profile['target']['candidate']}  (confidence: {profile['target']['confidence']})")
    ok(f"Task          : {profile['task']['candidate']}  (confidence: {profile['task']['confidence']})")
    ok(f"Class dist.   : {profile['class_distribution']}")
    if profile["warnings"]:
        for w in profile["warnings"]:
            warn(f"Profile warning: {w}")

    # ── PHASE 4: Validator ────────────────────────────────────────────────────
    subsection("PHASE 4 — Data Validator")
    validator = DataValidator()
    report    = validator.validate(df, profile, dataset_id=f"DS-{dataset_name}")

    ok(f"Validation Status : {report['validation_status']}")
    ok(f"Quality Score     : {report['quality_score']} / 100")
    ok(f"Next Phase        : {report['next_phase']}")
    ok(f"Missing severity  : {report['missing_values']['severity']}")
    ok(f"Duplicate count   : {report['duplicates']['exact_duplicates']}")
    ok(f"Class balance     : {report['class_balance'].get('severity', 'N/A')}  (ratio: {report['class_balance'].get('imbalance_ratio', 'N/A')})")
    ok(f"Leakage IDs found : {report['leakage']['identifier_candidates']}")
    ok(f"Patient split risk: {report['patient_level_split_risk']['detected']}")

    if report["critical_issues"]:
        for issue in report["critical_issues"]:
            print(f"  🚨  CRITICAL: {issue['message']}")

    if report["warnings"]:
        for w in report["warnings"]:
            warn(f"Warning [{w['severity']}]: {w['message']}")

    info("Recommended preprocessing steps:")
    for step in report["recommended_preprocessing_steps"]:
        info(f"  → {step}")

    if report["validation_status"] == "BLOCKED":
        print(f"\n  🚫  Pipeline BLOCKED for {dataset_name}. Skipping remaining phases.")
        return

    # ── PHASE 5: Preprocessing ────────────────────────────────────────────────
    subsection("PHASE 5 — Data Preprocessing")
    preprocessor = DataPreprocessor(dataset_name=dataset_name)
    clean_df, summary = preprocessor.preprocess(df, report)

    ok(f"Rows before cleaning : {summary['rows_before']}")
    ok(f"Rows after cleaning  : {summary['rows_after']}")
    ok(f"Duplicates removed   : {summary['duplicates_removed']}")
    ok(f"Missing before       : {summary['missing_values_before']}")
    ok(f"Missing after        : {summary['missing_values_after']}")
    info("Transformations applied:")
    for t in summary["transformations"]:
        info(f"  → {t}")

    # ── PHASE 6A: Feature Pipeline ────────────────────────────────────────────
    subsection("PHASE 6A — Feature Engineering + Split + Scaling")

    # For Parkinson's: pass original_df for grouped split
    original_df = None
    if dataset_name == "parkinsons":
        original_df = pd.read_csv(os.path.join(FIXTURES, "parkinsons.csv"))
        original_df = original_df.loc[clean_df.index].reset_index(drop=True)
        clean_df    = clean_df.reset_index(drop=True)

    pipeline = FeaturePipeline(dataset_name=dataset_name)
    result   = pipeline.fit_transform(
        clean_df,
        experiment_id=experiment_id,
        original_df=original_df,
    )

    ok(f"Preprocessing ID  : {result.preprocessing_id}")
    ok(f"Split strategy    : {result.split_strategy}")
    ok(f"Test size         : {result.test_size}")
    ok(f"Random state      : {result.random_state}")
    ok(f"X_train shape     : {result.X_train.shape}  (float64: {result.X_train.dtype == np.float64})")
    ok(f"X_test  shape     : {result.X_test.shape}")
    ok(f"y_train shape     : {result.y_train.shape}  (int64: {result.y_train.dtype == np.int64})")
    ok(f"y_test  shape     : {result.y_test.shape}")
    ok(f"Feature names     : {result.feature_names[:5]}{'...' if len(result.feature_names) > 5 else ''}")
    ok(f"Class weights     : {result.class_weights}")
    ok(f"Train class dist  : {dict(zip(*np.unique(result.y_train, return_counts=True)))}")
    ok(f"Test  class dist  : {dict(zip(*np.unique(result.y_test,  return_counts=True)))}")

    # ── PHASE 6B: PCA / Dimensionality Reduction ──────────────────────────────
    subsection("PHASE 6B — PCA / Dimensionality Reduction")
    ok(f"X_train_reduced shape : {result.X_train_reduced.shape}")
    ok(f"X_test_reduced  shape : {result.X_test_reduced.shape}")
    ok(f"PCA components        : {result.n_components}")
    ok(f"Variance retained     : {result.variance_retained:.4f} ({result.variance_retained*100:.1f}%)")
    ok(f"PC names              : {result.reduced_feature_names}")

    # ── Artifact check ─────────────────────────────────────────────────────────
    subsection("Artifacts saved to disk")
    data_dir = os.path.join("artifacts", "experiments", experiment_id, "data")
    expected_files = [
        "X_train.npy", "X_test.npy",
        "X_train_reduced.npy", "X_test_reduced.npy",
        "y_train.npy", "y_test.npy",
        "feature_names.json", "pipeline_metadata.json",
    ]
    for fname in expected_files:
        fpath = os.path.join(data_dir, fname)
        exists = os.path.exists(fpath)
        size   = os.path.getsize(fpath) if exists else 0
        ok(f"{fname:35s} {'✅ saved' if exists else '❌ MISSING'}  ({size} bytes)")

    # ── Contract JSON preview ─────────────────────────────────────────────────
    subsection("Contract JSON preview (pipeline_metadata.json)")
    meta_path = os.path.join(data_dir, "pipeline_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        print(json.dumps(meta, indent=4))

    print(f"\n  🎉  Pipeline complete for {dataset_name.upper()}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "█" * 60)
    print("  Q-DIAGNOSE — Data Pipeline (Phases 2-6)")
    print("  Owner: Jayed")
    print("█" * 60)

    datasets = [
        ("diabetes",      "EXP-DEMO-DIABETES"),
        ("heart_disease", "EXP-DEMO-HEART"),
        ("breast_cancer", "EXP-DEMO-BREAST"),
        ("parkinsons",    "EXP-DEMO-PARK"),
    ]

    for name, exp_id in datasets:
        try:
            run_for_dataset(name, exp_id)
        except Exception as e:
            print(f"\n  ❌  ERROR for {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "█" * 60)
    print("  ALL DATASETS PROCESSED")
    print("  Run tests anytime:")
    print("  Q-Diagnose/venv/Scripts/python -m pytest Q-Diagnose/tests/ -v")
    print("█" * 60 + "\n")
