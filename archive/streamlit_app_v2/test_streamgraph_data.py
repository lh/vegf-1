#!/usr/bin/env python3
"""
Test script to examine streamgraph data and identify what needs to be fixed.
"""

import sys
import pandas as pd
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner
from components.treatment_patterns.pattern_analyzer import extract_treatment_patterns_vectorized
from components.treatment_patterns.time_series_generator import generate_patient_state_time_series


def test_streamgraph_data():
    """Test streamgraph data to see enrollment information."""
    print("=" * 60)
    print("Testing Streamgraph Data")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    if not protocol_path.exists():
        print(f"Error: Protocol not found at {protocol_path}")
        return
        
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Run small simulation
    print("\n1. Running small simulation...")
    runner = SimulationRunner(protocol_spec)
    results = runner.run(
        engine_type='abs',
        n_patients=20,
        duration_years=1.0,
        seed=42,
        show_progress=True
    )
    
    print(f"\nSimulation saved to: {results.data_path}")
    
    # Check available data
    print("\n2. Checking available data methods...")
    print(f"   Has get_visits_df: {hasattr(results, 'get_visits_df')}")
    print(f"   Has get_patients_df: {hasattr(results, 'get_patients_df')}")
    
    # Get patient data
    print("\n3. Checking patient enrollment data...")
    if hasattr(results, 'get_patients_df'):
        patients_df = results.get_patients_df()
        print(f"   Patients columns: {list(patients_df.columns)}")
        if 'enrollment_time_days' in patients_df.columns:
            print(f"   ✅ Found enrollment_time_days!")
            print(f"   Enrollment range: {patients_df['enrollment_time_days'].min()} to {patients_df['enrollment_time_days'].max()} days")
    
    # Get visits data
    print("\n4. Checking visits data...")
    visits_df = results.get_visits_df()
    print(f"   Visits columns: {list(visits_df.columns)}")
    
    # Extract treatment patterns
    print("\n5. Extracting treatment patterns...")
    transitions_df, visits_with_state = extract_treatment_patterns_vectorized(results)
    print(f"   Visits with state columns: {list(visits_with_state.columns)}")
    
    # Generate time series
    print("\n6. Generating time series...")
    time_series_df = generate_patient_state_time_series(visits_with_state)
    
    # Check patient counts at different time points
    print("\n7. Patient counts at different time points:")
    for t in [0, 30, 60, 90, 180, 365]:
        if t <= time_series_df['time_point'].max() * 30.44:  # Convert months to days
            t_months = t / 30.44
            point_data = time_series_df[time_series_df['time_point'] == time_series_df['time_point'].iloc[0]]
            total = point_data['patient_count'].sum()
            print(f"   Day {t} ({t_months:.1f} months): {total} patients")
    
    # Show the problem
    print("\n8. The Problem:")
    print("   The time series generator assumes all patients exist from the start.")
    print("   It needs to check enrollment_time_days to know when patients actually joined.")
    
    return results, visits_with_state, time_series_df


if __name__ == "__main__":
    test_streamgraph_data()