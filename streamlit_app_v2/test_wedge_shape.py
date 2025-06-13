#!/usr/bin/env python3
"""
Test script to verify streamgraph shows wedge shape with staggered enrollment.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner
from components.treatment_patterns.pattern_analyzer import extract_treatment_patterns_vectorized
from components.treatment_patterns.time_series_generator import generate_patient_state_time_series


def test_wedge_shape():
    """Test that streamgraph shows wedge shape."""
    print("=" * 60)
    print("Testing Wedge Shape in Streamgraph")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    if not protocol_path.exists():
        print(f"Error: Protocol not found at {protocol_path}")
        return
        
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Run simulation
    print("\n1. Running simulation with staggered enrollment...")
    runner = SimulationRunner(protocol_spec)
    results = runner.run(
        engine_type='abs',
        n_patients=100,
        duration_years=2.0,
        seed=123,
        show_progress=True
    )
    
    print(f"\nSimulation saved to: {results.data_path}")
    
    # Get enrollment data
    print("\n2. Checking enrollment data...")
    patients_df = results.get_patients_df()
    print(f"   Enrollment columns: {list(patients_df.columns)}")
    print(f"   Enrollment range: {patients_df['enrollment_time_days'].min():.0f} to {patients_df['enrollment_time_days'].max():.0f} days")
    
    # Extract treatment patterns
    print("\n3. Extracting treatment patterns...")
    transitions_df, visits_with_state = extract_treatment_patterns_vectorized(results)
    
    # Generate time series WITH enrollment data
    print("\n4. Generating time series with enrollment data...")
    time_series_df = generate_patient_state_time_series(
        visits_with_state,
        time_resolution='month',
        enrollment_df=patients_df
    )
    
    # Check patient counts over time
    print("\n5. Patient counts over time:")
    time_points = sorted(time_series_df['time_point'].unique())
    total_counts = []
    
    for t in time_points[:10]:  # First 10 time points
        point_data = time_series_df[time_series_df['time_point'] == t]
        total = point_data['patient_count'].sum()
        total_counts.append(total)
        print(f"   Month {t:.1f}: {total} patients")
    
    # Verify wedge shape
    print("\n6. Verification:")
    is_increasing = all(total_counts[i] <= total_counts[i+1] for i in range(len(total_counts)-1))
    
    if is_increasing and total_counts[0] < total_counts[-1]:
        print("   ✅ SUCCESS: Patient count increases over time (wedge shape)")
        print(f"   Started with {total_counts[0]} patients, grew to {total_counts[-1]} patients")
    else:
        print("   ❌ FAIL: Patient count not increasing properly")
        print(f"   Counts: {total_counts}")
    
    # Create visualization
    print("\n7. Creating visualization...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot total patient count over time
    all_time_points = sorted(time_series_df['time_point'].unique())
    all_totals = []
    for t in all_time_points:
        point_data = time_series_df[time_series_df['time_point'] == t]
        total = point_data['patient_count'].sum()
        all_totals.append(total)
    
    ax.plot(all_time_points, all_totals, 'b-', linewidth=2, label='Total Enrolled Patients')
    ax.fill_between(all_time_points, 0, all_totals, alpha=0.3)
    
    ax.set_xlabel('Time (months)')
    ax.set_ylabel('Number of Patients')
    ax.set_title('Patient Enrollment Over Time (Wedge Shape)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('wedge_shape_verification.png', dpi=150)
    print("   Saved visualization to wedge_shape_verification.png")
    
    return time_series_df


if __name__ == "__main__":
    test_wedge_shape()