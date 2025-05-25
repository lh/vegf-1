#!/usr/bin/env python
"""
Run V2 simulation with protocol specification.

NO DEFAULTS - all parameters must come from protocol file.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.serialization.parquet_writer import serialize_patient_visits
import pandas as pd


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run V2 AMD simulation with protocol specification"
    )
    
    # Required arguments
    parser.add_argument(
        '--protocol',
        type=str,
        required=True,
        help='Path to protocol YAML file'
    )
    
    parser.add_argument(
        '--engine',
        type=str,
        choices=['abs', 'des'],
        required=True,
        help='Simulation engine type'
    )
    
    parser.add_argument(
        '--patients',
        type=int,
        required=True,
        help='Number of patients to simulate'
    )
    
    parser.add_argument(
        '--years',
        type=float,
        required=True,
        help='Simulation duration in years'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        required=True,
        help='Random seed for reproducibility'
    )
    
    # Output arguments
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output path for simulation results (Parquet)'
    )
    
    parser.add_argument(
        '--audit',
        type=str,
        required=True,
        help='Output path for audit trail (JSON)'
    )
    
    args = parser.parse_args()
    
    # Load protocol
    print(f"Loading protocol from: {args.protocol}")
    try:
        protocol_spec = ProtocolSpecification.from_yaml(Path(args.protocol))
        print(f"Loaded: {protocol_spec.name} v{protocol_spec.version}")
        print(f"Checksum: {protocol_spec.checksum}")
    except Exception as e:
        print(f"ERROR: Failed to load protocol: {e}")
        sys.exit(1)
        
    # Create runner
    runner = SimulationRunner(protocol_spec)
    
    # Run simulation
    print(f"\nRunning {args.engine.upper()} simulation:")
    print(f"  Patients: {args.patients}")
    print(f"  Duration: {args.years} years")
    print(f"  Seed: {args.seed}")
    
    start_time = datetime.now()
    results = runner.run(
        engine_type=args.engine,
        n_patients=args.patients,
        duration_years=args.years,
        seed=args.seed
    )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\nSimulation complete in {duration:.1f} seconds")
    print(f"  Total injections: {results.total_injections}")
    print(f"  Mean final vision: {results.final_vision_mean:.1f}")
    print(f"  Discontinuation rate: {results.discontinuation_rate:.1%}")
    
    # Save results to Parquet
    print(f"\nSaving results to: {args.output}")
    save_results_to_parquet(results, Path(args.output), protocol_spec)
    
    # Save audit trail
    print(f"Saving audit trail to: {args.audit}")
    runner.save_audit_trail(Path(args.audit))
    
    print("\n✅ Simulation complete!")


def save_results_to_parquet(
    results: 'SimulationResults',
    output_path: Path,
    protocol_spec: ProtocolSpecification
) -> None:
    """Save simulation results to Parquet files."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare visit data
    all_visits = []
    for patient_id, patient in results.patient_histories.items():
        serialized = serialize_patient_visits(patient_id, patient.visit_history)
        all_visits.extend(serialized)
        
    # Create visits DataFrame
    visits_df = pd.DataFrame(all_visits)
    
    # Add simulation metadata
    visits_df['protocol_name'] = protocol_spec.name
    visits_df['protocol_version'] = protocol_spec.version
    
    # Save visits
    visits_path = output_path.with_suffix('.visits.parquet')
    visits_df.to_parquet(visits_path, index=False)
    print(f"  Saved {len(visits_df)} visits to {visits_path}")
    
    # Create patient summary
    patient_summaries = []
    for patient_id, patient in results.patient_histories.items():
        summary = {
            'patient_id': patient_id,
            'baseline_vision': patient.baseline_vision,
            'final_vision': patient.current_vision,
            'vision_change': patient.current_vision - patient.baseline_vision,
            'n_visits': len(patient.visit_history),
            'n_injections': patient.injection_count,
            'is_discontinued': patient.is_discontinued,
            'discontinuation_type': patient.discontinuation_type or 'none'
        }
        patient_summaries.append(summary)
        
    patients_df = pd.DataFrame(patient_summaries)
    
    # Save patient summary
    patients_path = output_path.with_suffix('.patients.parquet')
    patients_df.to_parquet(patients_path, index=False)
    print(f"  Saved {len(patients_df)} patient summaries to {patients_path}")
    
    # Create metadata
    metadata = {
        'protocol_name': protocol_spec.name,
        'protocol_version': protocol_spec.version,
        'protocol_checksum': protocol_spec.checksum,
        'n_patients': results.patient_count,
        'total_injections': results.total_injections,
        'mean_final_vision': results.final_vision_mean,
        'std_final_vision': results.final_vision_std,
        'discontinuation_rate': results.discontinuation_rate,
        'simulation_timestamp': datetime.now().isoformat()
    }
    
    metadata_df = pd.DataFrame([metadata])
    metadata_path = output_path.with_suffix('.metadata.parquet')
    metadata_df.to_parquet(metadata_path, index=False)
    print(f"  Saved metadata to {metadata_path}")


if __name__ == '__main__':
    main()