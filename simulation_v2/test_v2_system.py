#!/usr/bin/env python
"""
Quick test of the V2 simulation system.
"""

from datetime import datetime
from simulation_v2.core.disease_model import DiseaseModel, DiseaseState
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.engines.des_engine import DESEngine
from simulation_v2.serialization.parquet_writer import serialize_patient_visits
import pandas as pd


def main():
    """Run a simple test of both engines."""
    print("Testing V2 Simulation System")
    print("=" * 50)
    
    # Setup
    disease_model = DiseaseModel(seed=42)
    protocol = StandardProtocol.from_weeks(
        min_interval_weeks=4,
        max_interval_weeks=12,
        extension_weeks=2,
        shortening_weeks=2
    )
    
    print(f"Protocol: min={protocol.min_interval_days} days, max={protocol.max_interval_days} days")
    print()
    
    # Run ABS
    print("Running ABS engine...")
    abs_engine = ABSEngine(disease_model, protocol, n_patients=10, seed=42)
    abs_results = abs_engine.run(duration_years=1)
    
    print(f"ABS Results:")
    print(f"  Total injections: {abs_results.total_injections}")
    print(f"  Mean final vision: {abs_results.mean_final_vision:.1f}")
    print(f"  Discontinuation rate: {abs_results.discontinuation_rate:.1%}")
    print()
    
    # Run DES
    print("Running DES engine...")
    des_engine = DESEngine(disease_model, protocol, n_patients=10, seed=42)
    des_results = des_engine.run(duration_years=1)
    
    print(f"DES Results:")
    print(f"  Total injections: {des_results.total_injections}")
    print(f"  Mean final vision: {des_results.mean_final_vision:.1f}")
    print(f"  Discontinuation rate: {des_results.discontinuation_rate:.1%}")
    print()
    
    # Test serialization
    print("Testing serialization...")
    patient_id = list(abs_results.patient_histories.keys())[0]
    patient = abs_results.patient_histories[patient_id]
    
    print(f"Patient {patient_id}:")
    print(f"  Baseline vision: {patient.baseline_vision}")
    print(f"  Final vision: {patient.current_vision}")
    print(f"  Visits: {len(patient.visit_history)}")
    print(f"  Injections: {patient.injection_count}")
    
    # Serialize to TOM format
    serialized = serialize_patient_visits(patient_id, patient.visit_history)
    df = pd.DataFrame(serialized)
    
    print("\nSerialized data (first 3 visits):")
    print(df.head(3))
    print()
    
    # Check FOV->TOM conversion
    print("FOV->TOM Conversion check:")
    for i, visit in enumerate(patient.visit_history[:3]):
        fov_state = visit['disease_state'].name
        tom_decision = serialized[i]['treatment_decision']
        treated = visit['treatment_given']
        print(f"  Visit {i+1}: FOV={fov_state}, Treated={treated} -> TOM={tom_decision}")
    
    print("\n✅ V2 System test complete!")


if __name__ == "__main__":
    main()