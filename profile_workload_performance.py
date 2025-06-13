"""Performance profiling script for clinical workload analysis visualizations.

This script profiles the workload analysis pipeline to identify performance bottlenecks.
It tests both data processing and visualization rendering stages.
"""

import time
import cProfile
import pstats
import io
import pandas as pd
import numpy as np
from contextlib import contextmanager
from typing import Dict, Any, Tuple
import psutil
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the components we want to profile
try:
    from ape.components.treatment_patterns.workload_analyzer_optimized import (
        calculate_clinical_workload_attribution as calc_workload_optimized
    )
    optimized_available = True
except ImportError:
    optimized_available = False
    print("WARNING: Optimized workload analyzer not available")

try:
    from ape.components.treatment_patterns.workload_analyzer import (
        calculate_clinical_workload_attribution as calc_workload_original
    )
    original_available = True
except ImportError:
    original_available = False
    print("WARNING: Original workload analyzer not available")

from ape.components.treatment_patterns.workload_visualizations import (
    create_dual_bar_chart,
    create_impact_pyramid,
    create_bubble_chart
)


@contextmanager
def timer(name: str):
    """Context manager for timing code blocks."""
    start = time.perf_counter()
    start_cpu = time.process_time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    print(f"\n{'='*60}")
    print(f"Starting: {name}")
    print(f"{'='*60}")
    
    yield
    
    end = time.perf_counter()
    end_cpu = time.process_time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    wall_time = end - start
    cpu_time = end_cpu - start_cpu
    memory_delta = end_memory - start_memory
    
    print(f"Completed: {name}")
    print(f"  Wall time: {wall_time:.3f} seconds")
    print(f"  CPU time: {cpu_time:.3f} seconds")
    print(f"  Memory delta: {memory_delta:+.1f} MB (current: {end_memory:.1f} MB)")
    print(f"  CPU efficiency: {(cpu_time/wall_time*100):.1f}%")
    print(f"{'='*60}\n")


def create_test_data(num_patients: int = 1000, avg_visits_per_patient: int = 10) -> pd.DataFrame:
    """Create realistic test data for profiling."""
    print(f"Creating test data: {num_patients} patients, ~{avg_visits_per_patient} visits each...")
    
    visits = []
    patient_id = 0
    
    # Create visits for each patient
    for i in range(num_patients):
        # Random number of visits per patient (Poisson distribution)
        num_visits = max(1, np.random.poisson(avg_visits_per_patient))
        
        # Generate visit times with realistic intervals
        current_time = 0
        for j in range(num_visits):
            visits.append({
                'patient_id': patient_id,
                'time_days': current_time,
                'visit_number': j
            })
            
            # Add interval (normal distribution around 56 days = 8 weeks)
            if j < num_visits - 1:
                interval = max(21, np.random.normal(56, 21))  # Min 3 weeks
                current_time += interval
        
        patient_id += 1
    
    visits_df = pd.DataFrame(visits)
    print(f"Created {len(visits_df)} total visits")
    return visits_df


def profile_function(func, *args, **kwargs):
    """Profile a function and return results."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    
    # Get stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    return result, s.getvalue()


def analyze_workload_data_structure(workload_data: Dict[str, Any]):
    """Analyze the structure and size of workload data."""
    print("\nWorkload Data Structure Analysis:")
    print("-" * 40)
    
    for key, value in workload_data.items():
        if isinstance(value, pd.DataFrame):
            print(f"  {key}: DataFrame with {len(value)} rows, {len(value.columns)} columns")
            print(f"    Memory usage: {value.memory_usage(deep=True).sum() / 1024:.1f} KB")
        elif isinstance(value, dict):
            print(f"  {key}: Dict with {len(value)} keys")
            if key == 'summary_stats':
                for cat, stats in value.items():
                    print(f"    - {cat}: {stats.get('patient_count', 0)} patients, "
                          f"{stats.get('visit_count', 0)} visits")
        else:
            print(f"  {key}: {type(value).__name__} = {value}")


def run_performance_tests():
    """Run comprehensive performance tests."""
    print("Clinical Workload Analysis Performance Profiling")
    print("=" * 60)
    
    # Test with different data sizes
    test_sizes = [
        (100, 10, "Small"),
        (1000, 10, "Medium"),
        (5000, 10, "Large"),
        (10000, 10, "Extra Large")
    ]
    
    results = {}
    
    for num_patients, avg_visits, label in test_sizes:
        print(f"\n\n{'#'*60}")
        print(f"Testing with {label} dataset: {num_patients} patients")
        print(f"{'#'*60}")
        
        # Create test data
        with timer(f"Data creation ({label})"):
            visits_df = create_test_data(num_patients, avg_visits)
        
        # Test optimized version if available
        if optimized_available:
            with timer(f"Optimized workload calculation ({label})"):
                workload_data_opt, profile_opt = profile_function(
                    calc_workload_optimized, visits_df
                )
            
            analyze_workload_data_structure(workload_data_opt)
            
            # Save profiling results
            with open(f'profile_optimized_{label.lower().replace(" ", "_")}.txt', 'w') as f:
                f.write(profile_opt)
        
        # Test original version if available
        if original_available:
            with timer(f"Original workload calculation ({label})"):
                workload_data_orig, profile_orig = profile_function(
                    calc_workload_original, visits_df
                )
            
            # Save profiling results
            with open(f'profile_original_{label.lower().replace(" ", "_")}.txt', 'w') as f:
                f.write(profile_orig)
        
        # Use whichever version we have for visualization tests
        workload_data = workload_data_opt if optimized_available else workload_data_orig
        
        # Test each visualization
        viz_tests = [
            ("Dual Bar Chart", create_dual_bar_chart),
            ("Impact Pyramid", create_impact_pyramid),
            ("Bubble Chart", create_bubble_chart)
        ]
        
        for viz_name, viz_func in viz_tests:
            with timer(f"{viz_name} creation ({label})"):
                fig, profile_viz = profile_function(viz_func, workload_data, True)
            
            # Analyze figure size
            fig_json = fig.to_json()
            print(f"  Figure JSON size: {len(fig_json) / 1024:.1f} KB")
            
            # Save profiling results
            with open(f'profile_{viz_name.lower().replace(" ", "_")}_{label.lower().replace(" ", "_")}.txt', 'w') as f:
                f.write(profile_viz)
        
        # Store results
        results[label] = {
            'num_patients': num_patients,
            'num_visits': len(visits_df),
            'workload_data': workload_data
        }
    
    return results


def check_caching_effectiveness():
    """Test if caching is working properly in the deployed version."""
    print("\n\nChecking Caching Effectiveness")
    print("=" * 60)
    
    # Create test data
    visits_df = create_test_data(1000, 10)
    
    if optimized_available:
        # First call - should be slow
        with timer("First workload calculation"):
            workload_data1 = calc_workload_optimized(visits_df)
        
        # Second call with same data - should be fast if cached
        with timer("Second workload calculation (should be cached)"):
            workload_data2 = calc_workload_optimized(visits_df)
        
        # Modify data slightly
        visits_df_modified = visits_df.copy()
        visits_df_modified.loc[0, 'time_days'] += 1
        
        with timer("Third workload calculation (modified data)"):
            workload_data3 = calc_workload_optimized(visits_df_modified)
    
    # Test visualization caching
    print("\nTesting visualization caching...")
    workload_data = workload_data1 if optimized_available else create_test_data(100, 10)
    
    with timer("First visualization creation"):
        fig1 = create_dual_bar_chart(workload_data, True)
    
    with timer("Second visualization creation (same data)"):
        fig2 = create_dual_bar_chart(workload_data, True)


def identify_bottlenecks():
    """Identify specific bottlenecks in the code."""
    print("\n\nDetailed Bottleneck Analysis")
    print("=" * 60)
    
    # Create large dataset
    visits_df = create_test_data(5000, 10)
    
    if optimized_available:
        # Profile specific functions
        from ape.components.treatment_patterns.workload_analyzer_optimized import (
            _calculate_patient_intensity_profiles_vectorized,
            _categorize_treatment_intensity_vectorized,
            _calculate_visit_contributions_vectorized,
            _calculate_workload_summary_stats_vectorized
        )
        
        # Prepare data
        all_patients = visits_df['patient_id'].unique()
        
        # Add intervals
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time_days']
        valid_intervals = visits_df[visits_df['interval_days'].notna()]
        
        # Profile each step
        with timer("Step 1: Calculate patient profiles"):
            patient_profiles, _ = profile_function(
                _calculate_patient_intensity_profiles_vectorized,
                valid_intervals, all_patients, visits_df
            )
        
        with timer("Step 2: Categorize treatment intensity"):
            patient_profiles, _ = profile_function(
                _categorize_treatment_intensity_vectorized,
                patient_profiles
            )
        
        with timer("Step 3: Calculate visit contributions"):
            visit_contributions, _ = profile_function(
                _calculate_visit_contributions_vectorized,
                visits_df, patient_profiles
            )
        
        with timer("Step 4: Calculate summary stats"):
            summary_stats, _ = profile_function(
                _calculate_workload_summary_stats_vectorized,
                patient_profiles, visit_contributions
            )


def main():
    """Main profiling execution."""
    # System info
    print("System Information:")
    print(f"  Python: {sys.version}")
    print(f"  CPU count: {psutil.cpu_count()}")
    print(f"  Total memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
    print(f"  Available memory: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
    print()
    
    # Run tests
    results = run_performance_tests()
    
    # Check caching
    check_caching_effectiveness()
    
    # Detailed bottleneck analysis
    identify_bottlenecks()
    
    # Summary
    print("\n\nPERFORMANCE SUMMARY")
    print("=" * 60)
    print("\nKey findings will be written to performance_summary.txt")
    
    with open('performance_summary.txt', 'w') as f:
        f.write("Clinical Workload Analysis Performance Summary\n")
        f.write("=" * 60 + "\n\n")
        
        if optimized_available:
            f.write("✓ Optimized version is available and was tested\n")
        else:
            f.write("✗ Optimized version not available - only original tested\n")
        
        f.write("\nDataset sizes tested:\n")
        for label, data in results.items():
            f.write(f"  - {label}: {data['num_patients']} patients, {data['num_visits']} visits\n")
        
        f.write("\nRecommendations:\n")
        f.write("1. Check if optimized version is being used in production\n")
        f.write("2. Verify Streamlit caching is properly configured\n")
        f.write("3. Consider implementing visualization-level caching\n")
        f.write("4. Monitor Plotly rendering performance for large datasets\n")
        f.write("5. Consider pagination or progressive loading for very large datasets\n")
    
    print("\nProfile files generated:")
    for file in os.listdir('.'):
        if file.startswith('profile_') and file.endswith('.txt'):
            print(f"  - {file}")
    
    print("\nDone! Check performance_summary.txt for recommendations.")


if __name__ == "__main__":
    main()