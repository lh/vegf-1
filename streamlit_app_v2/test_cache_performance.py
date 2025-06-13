#!/usr/bin/env python3
"""
Test caching performance for streamgraph.
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from core.results.factory import ResultsFactory
from components.treatment_patterns.time_series_cache import (
    get_cached_time_series_data, compute_df_hash, should_show_week_resolution
)
from components.treatment_patterns.data_manager import get_treatment_pattern_data


def test_cache_performance():
    """Test that caching improves performance."""
    print("=" * 60)
    print("Testing Streamgraph Cache Performance")
    print("=" * 60)
    
    # Find a large simulation
    sim_results_dir = Path("simulation_results")
    sim_dirs = sorted([d for d in sim_results_dir.iterdir() if d.is_dir() and d.name.startswith("sim_")])
    
    # Find the 10,000 patient simulation
    target_sim = None
    for sim_dir in reversed(sim_dirs):
        metadata_path = sim_dir / "metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path) as f:
                metadata = json.load(f)
                if metadata.get('n_patients', 0) >= 10000:
                    target_sim = sim_dir
                    sim_id = sim_dir.name
                    n_patients = metadata['n_patients']
                    duration_years = metadata['duration_years']
                    print(f"\nUsing simulation: {sim_id}")
                    print(f"  Patients: {n_patients:,}")
                    print(f"  Duration: {duration_years} years")
                    break
    
    if not target_sim:
        print("No simulation with 10,000+ patients found!")
        return
    
    # Load results
    results = ResultsFactory.load_results(target_sim)
    
    # Get pattern data
    _, visits_df = get_treatment_pattern_data(results)
    visits_hash = compute_df_hash(visits_df)
    
    enrollment_df = results.get_patients_df() if hasattr(results, 'get_patients_df') else None
    enrollment_hash = compute_df_hash(enrollment_df) if enrollment_df is not None else None
    
    # Test week resolution availability
    print(f"\n1. Week resolution available: {should_show_week_resolution(n_patients, duration_years)}")
    print(f"   Complexity score: {n_patients * duration_years * 52:,.0f}")
    
    # Test cache performance
    print("\n2. Testing cache performance:")
    
    for resolution in ['month', 'week']:
        print(f"\n   Testing {resolution} resolution:")
        
        # First call - will compute
        start = time.time()
        result1 = get_cached_time_series_data(sim_id, visits_hash, resolution, enrollment_hash)
        time1 = time.time() - start
        print(f"     First call: {time1:.2f}s ({len(result1):,} rows)")
        
        # Second call - should be cached
        start = time.time()
        result2 = get_cached_time_series_data(sim_id, visits_hash, resolution, enrollment_hash)
        time2 = time.time() - start
        print(f"     Cached call: {time2:.2f}s")
        
        # Verify same results
        assert len(result1) == len(result2), "Cache returned different results!"
        
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"     Cache speedup: {speedup:.0f}x faster")


if __name__ == "__main__":
    test_cache_performance()