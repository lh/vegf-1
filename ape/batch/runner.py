"""
Batch simulation runner - subprocess entry point.

This script runs as a separate process to execute multiple simulations
in a batch. It updates a status file as it progresses.

Usage:
    python -m ape.batch.runner \\
        --protocol-a path/to/protocol_a.yaml \\
        --protocol-b path/to/protocol_b.yaml \\
        --n-patients 2000 \\
        --duration-years 5.0 \\
        --seed 42 \\
        --batch-id batch_20250128_120000
"""

import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ape.batch.status import BatchStatus, get_batch_dir
from ape.core.simulation_runner import SimulationRunner
from ape.core.results.factory import ResultsFactory
from ape.utils.state_helpers import save_protocol_spec, add_simulation_to_registry
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification


def run_single_simulation(
    protocol_path: str,
    protocol_name: str,
    n_patients: int,
    duration_years: float,
    seed: int,
    status_mgr: BatchStatus
) -> str:
    """
    Run a single simulation and return its ID.

    Args:
        protocol_path: Path to protocol YAML file
        protocol_name: Display name for protocol
        n_patients: Number of patients
        duration_years: Duration in years
        seed: Random seed
        status_mgr: Status manager for updates

    Returns:
        Simulation ID

    Raises:
        Exception: If simulation fails
    """
    print(f"Loading protocol: {protocol_name}")
    status_mgr.update(
        progress=f"Loading protocol: {protocol_name}"
    )

    # Load protocol specification
    protocol_path = Path(protocol_path)
    if not protocol_path.exists():
        raise FileNotFoundError(f"Protocol not found: {protocol_path}")

    # Detect protocol type from content
    import yaml
    with open(protocol_path) as f:
        protocol_data = yaml.safe_load(f)

    # Check if time-based by looking for model_type field
    model_type = protocol_data.get('model_type', '')
    is_time_based = model_type == 'time_based'

    if is_time_based:
        spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    else:
        spec = ProtocolSpecification.from_yaml(protocol_path)

    print(f"Initializing runner for {spec.name}")
    status_mgr.update(
        progress=f"Initializing simulation: {protocol_name}"
    )

    # Create runner
    runner = SimulationRunner(spec)

    print(f"Running simulation: {n_patients} patients × {duration_years} years")
    status_mgr.update(
        progress=f"Running simulation: {protocol_name} ({n_patients}p × {duration_years}y)"
    )

    # Run simulation
    start_time = time.time()
    results = runner.run(
        engine_type='abs',  # Always use agent-based simulation
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed,
        show_progress=False  # No console progress in subprocess
    )
    runtime = time.time() - start_time

    print(f"Simulation completed in {runtime:.1f}s")

    # Save results
    sim_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19] + f"_{protocol_name.replace(' ', '_').lower()}"

    save_dir = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"Saving results to {sim_id}")
    status_mgr.update(
        progress=f"Saving results: {protocol_name}"
    )

    # Save using factory
    results.save(save_dir)

    # Save protocol YAML file
    import shutil
    protocol_save_path = save_dir / "protocol.yaml"
    shutil.copy(protocol_path, protocol_save_path)

    # Save metadata
    import json
    metadata = {
        'sim_id': sim_id,  # ParquetResults.load() expects 'sim_id' not 'simulation_id'
        'simulation_id': sim_id,  # Keep for compatibility
        'timestamp': datetime.now().isoformat(),
        'protocol_name': spec.name,
        'protocol_version': spec.version,
        'protocol_path': str(protocol_path),
        'n_patients': n_patients,
        'duration_years': duration_years,
        'engine_type': 'abs',
        'seed': seed,
        'runtime_seconds': runtime,
        'storage_type': 'parquet',  # Required by ParquetResults
        'memorable_name': '',  # Required by ParquetResults
        'batch_run': True
    }

    metadata_path = save_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Simulation {sim_id} complete")

    return sim_id


def main():
    """Main entry point for batch runner."""
    parser = argparse.ArgumentParser(description="Run batch simulations")
    parser.add_argument("--protocol-a", required=True, help="Path to protocol A")
    parser.add_argument("--protocol-b", required=True, help="Path to protocol B")
    parser.add_argument("--n-patients", type=int, required=True, help="Number of patients")
    parser.add_argument("--duration-years", type=float, required=True, help="Duration in years")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--batch-id", required=True, help="Batch ID")

    args = parser.parse_args()

    # Get batch directory and initialize status
    batch_dir = get_batch_dir(args.batch_id)
    status_mgr = BatchStatus(batch_dir)

    # Get protocol names from paths
    protocol_a_name = Path(args.protocol_a).stem.replace('_', ' ').title()
    protocol_b_name = Path(args.protocol_b).stem.replace('_', ' ').title()

    protocols = [protocol_a_name, protocol_b_name]
    protocol_paths = [args.protocol_a, args.protocol_b]

    try:
        # Initialize status with current PID
        print(f"Starting batch {args.batch_id}")
        print(f"PID: {os.getpid()}")
        status_mgr.initialize(
            batch_id=args.batch_id,
            protocols=protocols,
            n_patients=args.n_patients,
            duration_years=args.duration_years,
            seed=args.seed,
            pid=os.getpid()
        )

        status_mgr.update(
            status=BatchStatus.STATUS_RUNNING,
            progress="Starting batch simulation run"
        )

        # Run each protocol
        sim_ids = []
        for i, (protocol_name, protocol_path) in enumerate(zip(protocols, protocol_paths)):
            print(f"\n{'='*60}")
            print(f"Protocol {i+1} of {len(protocols)}: {protocol_name}")
            print(f"{'='*60}")

            status_mgr.update(
                current_protocol=protocol_name,
                current_protocol_index=i,
                progress=f"Starting simulation {i+1} of {len(protocols)}: {protocol_name}"
            )

            # Run simulation
            start_time = time.time()
            sim_id = run_single_simulation(
                protocol_path=protocol_path,
                protocol_name=protocol_name,
                n_patients=args.n_patients,
                duration_years=args.duration_years,
                seed=args.seed,
                status_mgr=status_mgr
            )
            runtime = time.time() - start_time

            # Update status
            status_mgr.add_completed_simulation(
                protocol=protocol_name,
                sim_id=sim_id,
                n_patients=args.n_patients,
                runtime=runtime
            )

            sim_ids.append(sim_id)
            print(f"✓ Completed: {sim_id} ({runtime:.1f}s)")

        # Mark as completed
        print(f"\n{'='*60}")
        print("Batch completed successfully")
        print(f"{'='*60}")
        status_mgr.mark_completed()

        # Write summary
        summary = {
            "batch_id": args.batch_id,
            "completed_at": datetime.now().isoformat(),
            "protocols": protocols,
            "simulation_ids": sim_ids,
            "parameters": {
                "n_patients": args.n_patients,
                "duration_years": args.duration_years,
                "seed": args.seed
            }
        }
        status_mgr.write_summary(summary)

        print(f"Simulation IDs: {', '.join(sim_ids)}")
        return 0

    except KeyboardInterrupt:
        print("\nBatch cancelled by user")
        status_mgr.mark_cancelled()
        return 1

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        status_mgr.mark_error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
