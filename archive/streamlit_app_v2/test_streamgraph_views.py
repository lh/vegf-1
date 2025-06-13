#!/usr/bin/env python3
"""
Test streamgraph with different time views and capture results.
"""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner
from components.treatment_patterns.pattern_analyzer import extract_treatment_patterns_vectorized
from components.treatment_patterns.time_series_generator import generate_patient_state_time_series


def test_different_views():
    """Test streamgraph with different time resolutions."""
    print("=" * 60)
    print("Testing Streamgraph with Different Views")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Run simulation
    print("\n1. Running simulation...")
    runner = SimulationRunner(protocol_spec)
    results = runner.run(
        engine_type='abs',
        n_patients=200,
        duration_years=3.0,
        seed=789,
        show_progress=True
    )
    
    # Get data
    patients_df = results.get_patients_df()
    transitions_df, visits_with_state = extract_treatment_patterns_vectorized(results)
    
    # Test different time resolutions
    resolutions = ['week', 'month', 'quarter']
    fig, axes = plt.subplots(3, 1, figsize=(12, 15))
    
    for idx, resolution in enumerate(resolutions):
        print(f"\n2. Testing {resolution} resolution...")
        
        # Generate time series
        time_series_df = generate_patient_state_time_series(
            visits_with_state,
            time_resolution=resolution,
            enrollment_df=patients_df
        )
        
        # Calculate total patients over time
        time_points = sorted(time_series_df['time_point'].unique())
        totals = []
        
        for t in time_points:
            point_data = time_series_df[time_series_df['time_point'] == t]
            total = point_data['patient_count'].sum()
            totals.append(total)
        
        # Plot
        ax = axes[idx]
        ax.plot(time_points, totals, 'b-', linewidth=2)
        ax.fill_between(time_points, 0, totals, alpha=0.3)
        ax.set_title(f'Patient Enrollment - {resolution.capitalize()} Resolution')
        ax.set_xlabel('Time (months)')
        ax.set_ylabel('Number of Patients')
        ax.grid(True, alpha=0.3)
        
        # Print stats
        print(f"   Time points: {len(time_points)}")
        print(f"   Initial patients: {totals[0] if totals else 0}")
        print(f"   Final patients: {totals[-1] if totals else 0}")
        print(f"   Max enrollment time: {patients_df['enrollment_time_days'].max() / 30.44:.1f} months")
    
    plt.tight_layout()
    plt.savefig('streamgraph_views_test.png', dpi=150)
    print("\n3. Saved visualization to streamgraph_views_test.png")
    
    # Test normalized view
    print("\n4. Testing normalized (percentage) view...")
    time_series_df = generate_patient_state_time_series(
        visits_with_state,
        time_resolution='month',
        enrollment_df=patients_df
    )
    
    # Calculate percentages
    pivot_df = time_series_df.pivot(
        index='time_point',
        columns='state',
        values='patient_count'
    ).fillna(0)
    
    # Normalize to percentages
    totals = pivot_df.sum(axis=1)
    percentage_df = pivot_df.div(totals, axis=0) * 100
    
    # Check that percentages maintain wedge shape
    print("\n5. Verification:")
    print(f"   Total patients at month 0: {totals.iloc[0]:.0f}")
    print(f"   Total patients at month 12: {totals.iloc[12] if len(totals) > 12 else totals.iloc[-1]:.0f}")
    print(f"   Total patients at end: {totals.iloc[-1]:.0f}")
    
    if totals.iloc[0] < totals.iloc[-1]:
        print("   ✅ SUCCESS: Wedge shape maintained in all views")
    else:
        print("   ❌ FAIL: Wedge shape not maintained")


if __name__ == "__main__":
    test_different_views()