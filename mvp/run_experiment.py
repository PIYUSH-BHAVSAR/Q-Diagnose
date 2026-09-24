#!/usr/bin/env python
"""
Direct experiment runner for testing the pipeline.

Usage:
    python run_experiment.py <dataset_path>

Example:
    python run_experiment.py data/demo/breast_cancer.csv
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.experiments.executor import ExperimentExecutor
from backend.experiments.manager import ExperimentManager
from backend.data.loader import DatasetLoader
from backend.core.logging import logger


def main():
    """Run an experiment from command line."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable demo datasets:")
        demo_dir = Path("data/demo")
        if demo_dir.exists():
            for f in demo_dir.glob("*.csv"):
                print(f"  - {f}")
        sys.exit(1)
    
    dataset_path = sys.argv[1]
    
    # Verify file exists
    if not Path(dataset_path).exists():
        print(f"Error: File not found: {dataset_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("QuantWarriors Hybrid QML Platform - Experiment Runner")
    print("=" * 70)
    print(f"\nDataset: {dataset_path}")
    print()
    
    # Create executor
    loader = DatasetLoader()
    manager = ExperimentManager()
    executor = ExperimentExecutor(
        experiment_manager=manager,
        dataset_loader=loader,
        random_state=42
    )
    
    try:
        # Run experiment
        result = executor.run(
            dataset_path=dataset_path,
            n_components=8  # Can override with smaller (4) for faster testing
        )
        
        print("\n" + "=" * 70)
        print("EXPERIMENT COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
        # Print summary
        print(f"\nExperiment ID: {result['experiment_id']}")
        
        results = result['results']
        comparison_obj = results.get('comparison', {})
        if hasattr(comparison_obj, 'to_dict'):
            comparison = comparison_obj.to_dict()
        elif isinstance(comparison_obj, dict):
            comparison = comparison_obj
        else:
            comparison = {}
        
        # Model results
        print("\n📊 Model Results:")
        print("-" * 70)
        print(f"{'Model':<25} {'Type':<12} {'Accuracy':<10} {'Recall':<10} {'F1':<10} {'Time':<10}")
        print("-" * 70)
        
        for name, data in results.get('models', {}).items():
            metrics = data.get('metrics', {})
            print(
                f"{name:<25} "
                f"{data.get('model_type', 'unknown'):<12} "
                f"{metrics.get('accuracy', 0):<10.4f} "
                f"{metrics.get('recall', 0):<10.4f} "
                f"{metrics.get('f1', 0):<10.4f} "
                f"{data.get('training_time', 0):<10.2f}s"
            )
        
        # Best models
        print("\n🏆 Best Models:")
        print(f"  Best Classical: {comparison.get('best_classical', 'N/A')}")
        print(f"  Best Quantum:   {comparison.get('best_quantum', 'N/A')}")
        print(f"  Overall Best:   {comparison.get('best_model', 'N/A')}")
        
        # Recommendation
        print("\n📋 Recommendation:")
        print("-" * 70)
        print(comparison.get('recommendation', 'N/A'))
        
        # Resources
        resources_obj = results.get('resource_usage', {})
        if hasattr(resources_obj, 'to_dict'):
            resources = resources_obj.to_dict()
        elif isinstance(resources_obj, dict):
            resources = resources_obj
        else:
            resources = {}
            
        print(f"\n💻 Resources:")
        print(f"  Peak Memory: {resources.get('peak_memory_mb', 0):.2f} MB")
        print(f"  Total Time:  {resources.get('elapsed_time', 0):.2f} s")
        
        # Quantum resources
        models_dict = results.get('models', {})
        if 'vqc' in models_dict:
            vqc_item = models_dict['vqc']
            vqc_data = vqc_item.to_dict() if hasattr(vqc_item, 'to_dict') else vqc_item if isinstance(vqc_item, dict) else {}
            metrics = vqc_data.get('metrics', {})
            qr_raw = metrics.get('quantum_resources', {}) if isinstance(metrics, dict) else {}
            qr = qr_raw.to_dict() if hasattr(qr_raw, 'to_dict') else qr_raw if isinstance(qr_raw, dict) else {}
            if qr:
                print(f"\n⚛️ Quantum Resources:")
                print(f"  Qubits:      {qr.get('n_qubits', 'N/A')}")
                print(f"  Layers:      {qr.get('n_layers', 'N/A')}")
                print(f"  Executions:  {qr.get('n_circuit_executions', 'N/A')}")
        
        print("\n" + "=" * 70)
        
        # Save results to file
        output_file = f"experiment_results_{result['experiment_id']}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Experiment failed: {str(e)}", exc_info=True)
        print(f"\n❌ Experiment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
