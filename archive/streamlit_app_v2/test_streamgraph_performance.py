#!/usr/bin/env python3
"""
Test and compare performance of streamgraph generation.
"""

import sys
import time
from pathlib import Path
import pandas as pd

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from core.results.factory import ResultsFactory
from components.treatment_patterns.pattern_analyzer import extract_treatment_patterns_vectorized
from components.treatment_patterns.time_series_generator import generate_patient_state_time_series
from components.treatment_patterns.time_series_generator_optimized import generate_patient_state_time_series_optimized


def test_performance():
    """Compare performance of original vs optimized time series generation."""
    print("=" * 60)
    print("Streamgraph Performance Comparison")
    print("=" * 60)
    
    # Find a large simulation
    sim_results_dir = Path("simulation_results")
    sim_dirs = sorted([d for d in sim_results_dir.iterdir() if d.is_dir() and d.name.startswith("sim_")])
    
    # Find one with 10,000 patients
    target_sim = None
    for sim_dir in reversed(sim_dirs):
        metadata_path = sim_dir / "metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path) as f:
                metadata = json.load(f)
                if metadata.get('n_patients', 0) >= 10000:
                    target_sim = sim_dir
                    print(f"\nUsing simulation: {sim_dir.name}")
                    print(f"  Patients: {metadata['n_patients']}")
                    print(f"  Duration: {metadata['duration_years']} years")
                    break
    
    if not target_sim:
        print("No simulation with 10,000+ patients found!")
        return
    
    # Load results
    results = ResultsFactory.load_results(target_sim)
    
    # Extract treatment patterns
    print("\nExtracting treatment patterns...")
    start = time.time()
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    print(f"  Extraction time: {time.time() - start:.2f}s")
    print(f"  Total visits: {len(visits_df):,}")
    
    # Get enrollment data
    enrollment_df = results.get_patients_df() if hasattr(results, 'get_patients_df') else None
    
    # Test different resolutions
    resolutions = ['month', 'week']
    
    for resolution in resolutions:
        print(f"\n\nTesting {resolution} resolution:")
        print("-" * 40)
        
        # Original implementation
        print("Original implementation...")
        start = time.time()
        result_original = generate_patient_state_time_series(
            visits_df,
            time_resolution=resolution,
            enrollment_df=enrollment_df
        )
        time_original = time.time() - start
        print(f"  Time: {time_original:.2f}s")
        print(f"  Data points: {len(result_original):,}")
        
        # Optimized implementation
        print("\nOptimized implementation...")
        start = time.time()
        result_optimized = generate_patient_state_time_series_optimized(
            visits_df,
            time_resolution=resolution,
            enrollment_df=enrollment_df
        )
        time_optimized = time.time() - start
        print(f"  Time: {time_optimized:.2f}s")
        print(f"  Data points: {len(result_optimized):,}")
        
        # Compare results
        speedup = time_original / time_optimized
        print(f"\n  Speedup: {speedup:.1f}x faster")
        
        # Verify results are similar
        if len(result_original) > 0 and len(result_optimized) > 0:
            # Check a few time points
            time_points = result_original['time_point'].unique()[:5]
            print("\n  Verification (first 5 time points):")
            for t in time_points:
                orig_total = result_original[result_original['time_point'] == t]['patient_count'].sum()
                opt_total = result_optimized[result_optimized['time_point'] == t]['patient_count'].sum()
                print(f"    t={t:.1f}: Original={orig_total}, Optimized={opt_total}")


if __name__ == "__main__":
    test_performance()