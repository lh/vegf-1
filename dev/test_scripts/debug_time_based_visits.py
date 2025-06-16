#!/usr/bin/env python3
"""
Debug the visit data structure from time-based simulations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner

def main():
    """Debug visit data structure."""
    
    # Load time-based protocol
    protocol_path = Path("protocols/v2_time_based/eylea_time_based.yaml")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner directly
    runner = TimeBasedSimulationRunner(spec)
    
    # Run tiny simulation
    print("Running small time-based simulation...")
    results = runner.run(
        engine_type='abs',
        n_patients=2,
        duration_years=0.5,
        seed=42
    )
    
    print(f"\nTotal patients: {len(results.patient_histories)}")
    
    # Examine first patient's visit structure
    first_patient_id = list(results.patient_histories.keys())[0]
    first_patient = results.patient_histories[first_patient_id]
    
    print(f"\nFirst patient ID: {first_patient_id}")
    print(f"Enrollment date: {first_patient.enrollment_date}")
    print(f"Number of visits: {len(first_patient.visit_history)}")
    
    # Check first few visits
    print("\nFirst 3 visits:")
    for i, visit in enumerate(first_patient.visit_history[:3]):
        print(f"\nVisit {i}:")
        for key, value in visit.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()