#!/usr/bin/env python3
"""Test script for StaggeredABS implementation.

This script provides a simplified version of the staggered simulation to verify
that the core functionality works correctly.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation components
from simulation.config import SimulationConfig
from simulation.staggered_abs import StaggeredABS, run_staggered_abs

def test_staggered_abs():
    """Run a simple test of the StaggeredABS class."""
    print("Testing StaggeredABS implementation...")
    
    # Load configuration
    config = SimulationConfig.from_yaml("test_simulation")
    
    # Set simulation parameters
    start_date = datetime(2023, 1, 1)
    arrival_rate = 2.0  # Low rate for faster testing
    random_seed = 42
    
    # Create output directory
    output_dir = Path("output/staggered_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run staggered simulation
    print(f"Running staggered simulation with arrival rate {arrival_rate}...")
    
    try:
        # Run simulation directly
        sim = StaggeredABS(
            config=config,
            start_date=start_date,
            patient_arrival_rate=arrival_rate,
            random_seed=random_seed
        )
        
        results = sim.run()
        
        # Check results structure
        print("\nResults Structure:")
        print(f"Type: {type(results)}")
        print(f"Keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dictionary'}")
        
        if isinstance(results, dict) and 'patient_histories' in results:
            patient_histories = results['patient_histories']
            print(f"Number of patients: {len(patient_histories)}")
            
            # Examine first patient
            if patient_histories:
                first_id = next(iter(patient_histories))
                visits = patient_histories[first_id]
                print(f"\nFirst patient ({first_id}) has {len(visits)} visits:")
                for i, visit in enumerate(visits[:3]):  # Show first 3 visits
                    print(f"  Visit {i+1}: {visit.get('date')} - {visit.get('actions', [])}")
                
                # Check for enrollment date
                if 'enrollment_dates' in results:
                    enrollment_date = results['enrollment_dates'].get(first_id)
                    print(f"Enrollment date: {enrollment_date}")
                    
                    # Check for patient time information
                    if visits and 'weeks_since_enrollment' in visits[0]:
                        print("Patient time tracking is working!")
        
        # Now try the run_staggered_abs function
        print("\nTesting run_staggered_abs function...")
        histories = run_staggered_abs(
            config=config,
            start_date=start_date,
            patient_arrival_rate=arrival_rate,
            random_seed=random_seed,
            verbose=True
        )
        
        print(f"run_staggered_abs returned {len(histories)} patient histories")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_staggered_abs()