#!/usr/bin/env python3
"""
Test script to verify the VA visualization fix is working.
This script simulates what happens when you click "Run Simulation" in the UI.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_app_parquet.simulation_runner import run_simulation

def test_va_fix():
    """Test if VA data is properly processed after Parquet restructuring."""
    
    print("Testing VA visualization fix...")
    print("=" * 50)
    
    # Simulate UI parameters
    params = {
        "simulation_type": "ABS",
        "duration_years": 1,
        "population_size": 100,
        "enable_clinician_variation": True,
        "planned_discontinue_prob": 0.2,
        "admin_discontinue_prob": 0.05,
        "premature_discontinue_prob": 2.0,
        "consecutive_stable_visits": 3,
        "monitoring_schedule": [12, 24, 36],
        "no_monitoring_for_admin": True,
        "recurrence_risk_multiplier": 1.0
    }
    
    print(f"Running {params['simulation_type']} simulation with {params['population_size']} patients...")
    
    # Run the simulation
    results = run_simulation(params)
    
    # Check results
    print("\nResults summary:")
    print(f"  Simulation completed: {'error' not in results}")
    print(f"  Has visits_df: {'visits_df' in results}")
    print(f"  Has mean_va_data: {'mean_va_data' in results}")
    
    if 'visits_df' in results:
        print(f"  Visits shape: {results['visits_df'].shape}")
        print(f"  Vision column exists: {'vision' in results['visits_df'].columns}")
        
    if 'mean_va_data' in results:
        print(f"  VA data points: {len(results['mean_va_data'])}")
        if results['mean_va_data']:
            print(f"  First VA point: time={results['mean_va_data'][0]['time']:.1f}, va={results['mean_va_data'][0]['visual_acuity']:.1f}")
            print(f"  Last VA point: time={results['mean_va_data'][-1]['time']:.1f}, va={results['mean_va_data'][-1]['visual_acuity']:.1f}")
    
    if 'va_data_summary' in results:
        print("\nVA Data Summary:")
        for key, value in results['va_data_summary'].items():
            print(f"  {key}: {value}")
    
    # Check if fix worked
    if 'mean_va_data' in results and results['mean_va_data']:
        print("\n✅ SUCCESS: VA visualization fix is working!")
        return True
    else:
        print("\n❌ FAILED: VA data still not being processed")
        if 'va_data_summary' in results and 'error' in results['va_data_summary']:
            print(f"  Error: {results['va_data_summary']['error']}")
        return False

if __name__ == "__main__":
    # Set up minimal Streamlit-like environment
    import streamlit as st
    if not hasattr(st, '_is_running_with_streamlit'):
        # Mock Streamlit functions for testing
        st.info = lambda x: print(f"[INFO] {x}")
        st.error = lambda x: print(f"[ERROR] {x}")
        st.warning = lambda x: print(f"[WARNING] {x}")
        st.spinner = lambda x: type('obj', (object,), {'__enter__': lambda self: None, '__exit__': lambda self, *args: None})()
    
    success = test_va_fix()
    sys.exit(0 if success else 1)