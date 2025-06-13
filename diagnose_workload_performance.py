"""Diagnose specific performance issues in workload analysis visualizations.

This script identifies the actual bottlenecks users are experiencing.
"""

import time
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
import json
import psutil
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ape.components.treatment_patterns.workload_analyzer_optimized import (
    calculate_clinical_workload_attribution,
    _calculate_patient_intensity_profiles_vectorized,
    _categorize_treatment_intensity_vectorized,
    _calculate_visit_contributions_vectorized,
    _calculate_workload_summary_stats_vectorized
)
from ape.components.treatment_patterns.workload_visualizations import (
    create_dual_bar_chart,
    create_impact_pyramid,
    create_bubble_chart
)


def measure_step_performance(visits_df: pd.DataFrame) -> dict:
    """Measure performance of each step in the workload analysis pipeline."""
    results = {}
    
    # Step 0: Data preparation
    start = time.perf_counter()
    all_patients = visits_df['patient_id'].unique()
    visits_df = visits_df.sort_values(['patient_id', 'time_days'])
    visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
    visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time_days']
    valid_intervals = visits_df[visits_df['interval_days'].notna()]
    results['data_prep'] = time.perf_counter() - start
    
    # Step 1: Calculate patient profiles
    start = time.perf_counter()
    patient_profiles = _calculate_patient_intensity_profiles_vectorized(
        valid_intervals, all_patients, visits_df
    )
    results['patient_profiles'] = time.perf_counter() - start
    
    # Step 2: Categorize
    start = time.perf_counter()
    patient_profiles = _categorize_treatment_intensity_vectorized(patient_profiles)
    results['categorize'] = time.perf_counter() - start
    
    # Step 3: Visit contributions
    start = time.perf_counter()
    visit_contributions = _calculate_visit_contributions_vectorized(
        visits_df, patient_profiles
    )
    results['visit_contributions'] = time.perf_counter() - start
    
    # Step 4: Summary stats
    start = time.perf_counter()
    summary_stats = _calculate_workload_summary_stats_vectorized(
        patient_profiles, visit_contributions
    )
    results['summary_stats'] = time.perf_counter() - start
    
    # Full workload data assembly
    start = time.perf_counter()
    workload_data = {
        'patient_profiles': patient_profiles,
        'intensity_categories': patient_profiles,
        'visit_contributions': visit_contributions,
        'summary_stats': summary_stats,
        'total_patients': len(all_patients),
        'total_visits': len(visits_df),
        'category_definitions': {
            'Intensive': {'color': '#6B9DC7'},
            'Regular': {'color': '#8FC15C'},
            'Extended': {'color': '#6F9649'}
        }
    }
    results['data_assembly'] = time.perf_counter() - start
    
    return results, workload_data


def measure_visualization_performance(workload_data: dict) -> dict:
    """Measure performance of visualization creation."""
    results = {}
    
    # Dual Bar Chart
    start = time.perf_counter()
    fig1 = create_dual_bar_chart(workload_data, tufte_mode=True)
    results['dual_bar'] = time.perf_counter() - start
    results['dual_bar_size'] = len(fig1.to_json()) / 1024  # KB
    
    # Impact Pyramid
    start = time.perf_counter()
    fig2 = create_impact_pyramid(workload_data, tufte_mode=True)
    results['pyramid'] = time.perf_counter() - start
    results['pyramid_size'] = len(fig2.to_json()) / 1024  # KB
    
    # Bubble Chart
    start = time.perf_counter()
    fig3 = create_bubble_chart(workload_data, tufte_mode=True)
    results['bubble'] = time.perf_counter() - start
    results['bubble_size'] = len(fig3.to_json()) / 1024  # KB
    
    return results


def check_data_volume_scaling():
    """Test how performance scales with data volume."""
    print("\nDATA VOLUME SCALING TEST")
    print("=" * 60)
    
    test_sizes = [100, 500, 1000, 2500, 5000, 10000, 25000]
    results = []
    
    for size in test_sizes:
        # Create test data
        visits = []
        for i in range(size):
            num_visits = np.random.poisson(10)
            current_time = 0
            for j in range(num_visits):
                visits.append({
                    'patient_id': i,
                    'time_days': current_time,
                    'visit_number': j
                })
                if j < num_visits - 1:
                    current_time += np.random.normal(56, 21)
        
        visits_df = pd.DataFrame(visits)
        
        # Measure full pipeline
        start_total = time.perf_counter()
        
        # Analysis
        start = time.perf_counter()
        workload_data = calculate_clinical_workload_attribution(visits_df)
        analysis_time = time.perf_counter() - start
        
        # Visualization (just one for testing)
        start = time.perf_counter()
        fig = create_dual_bar_chart(workload_data, tufte_mode=True)
        viz_time = time.perf_counter() - start
        
        total_time = time.perf_counter() - start_total
        
        result = {
            'patients': size,
            'visits': len(visits_df),
            'analysis_time': analysis_time,
            'viz_time': viz_time,
            'total_time': total_time,
            'categories': len(workload_data['summary_stats'])
        }
        results.append(result)
        
        print(f"{size:,} patients: {total_time:.3f}s total "
              f"(analysis: {analysis_time:.3f}s, viz: {viz_time:.3f}s)")
    
    return pd.DataFrame(results)


def check_caching_overhead():
    """Check if caching adds overhead."""
    print("\nCACHING OVERHEAD TEST")
    print("=" * 60)
    
    # Create test data
    visits_df = pd.DataFrame([
        {'patient_id': i, 'time_days': j*56, 'visit_number': j}
        for i in range(1000)
        for j in range(10)
    ])
    
    # Test 1: Direct function call
    start = time.perf_counter()
    workload_data1 = calculate_clinical_workload_attribution(visits_df)
    direct_time = time.perf_counter() - start
    print(f"Direct function call: {direct_time:.3f}s")
    
    # Test 2: JSON serialization overhead
    start = time.perf_counter()
    visits_json = visits_df.to_json()
    json_time = time.perf_counter() - start
    print(f"DataFrame to JSON: {json_time:.3f}s ({len(visits_json)/1024:.1f} KB)")
    
    # Test 3: JSON deserialization
    start = time.perf_counter()
    visits_df_restored = pd.read_json(visits_json)
    restore_time = time.perf_counter() - start
    print(f"JSON to DataFrame: {restore_time:.3f}s")
    
    print(f"\nTotal caching overhead: {json_time + restore_time:.3f}s")
    print(f"Overhead percentage: {((json_time + restore_time) / direct_time * 100):.1f}%")


def identify_plotly_bottlenecks():
    """Identify specific Plotly rendering bottlenecks."""
    print("\nPLOTLY RENDERING ANALYSIS")
    print("=" * 60)
    
    # Create workload data with varying category counts
    for num_categories in [3, 6, 10, 20]:
        summary_stats = {}
        for i in range(num_categories):
            summary_stats[f'Category_{i}'] = {
                'patient_count': 100,
                'patient_percentage': 100.0 / num_categories,
                'visit_count': 500,
                'visit_percentage': 100.0 / num_categories,
                'visits_per_patient': 5.0,
                'workload_intensity': 1.0
            }
        
        workload_data = {
            'summary_stats': summary_stats,
            'total_patients': 100 * num_categories,
            'total_visits': 500 * num_categories,
            'category_definitions': {
                f'Category_{i}': {'color': f'#{i:02x}{i*2:02x}{i*3:02x}'}
                for i in range(num_categories)
            },
            'patient_profiles': pd.DataFrame(),
            'intensity_categories': pd.DataFrame(),
            'visit_contributions': pd.DataFrame()
        }
        
        # Measure each visualization
        start = time.perf_counter()
        fig = create_dual_bar_chart(workload_data, tufte_mode=True)
        bar_time = time.perf_counter() - start
        
        start = time.perf_counter()
        fig_json = fig.to_json()
        json_time = time.perf_counter() - start
        
        print(f"\n{num_categories} categories:")
        print(f"  Bar chart creation: {bar_time:.3f}s")
        print(f"  JSON serialization: {json_time:.3f}s")
        print(f"  JSON size: {len(fig_json)/1024:.1f} KB")


def main():
    """Run diagnostic tests."""
    print("WORKLOAD ANALYSIS PERFORMANCE DIAGNOSTICS")
    print("=" * 60)
    print(f"CPU cores: {psutil.cpu_count()}")
    print(f"Memory: {psutil.virtual_memory().total / 1024**3:.1f} GB")
    print(f"Available: {psutil.virtual_memory().available / 1024**3:.1f} GB")
    
    # Test 1: Component timing
    print("\n\nCOMPONENT TIMING ANALYSIS")
    print("=" * 60)
    
    # Create realistic test data
    visits_df = pd.DataFrame([
        {'patient_id': i, 'time_days': j*56 + np.random.randint(-7, 7), 'visit_number': j}
        for i in range(5000)
        for j in range(np.random.poisson(10))
    ])
    print(f"Test data: {len(visits_df['patient_id'].unique())} patients, {len(visits_df)} visits")
    
    step_times, workload_data = measure_step_performance(visits_df)
    
    print("\nAnalysis pipeline breakdown:")
    total_analysis = sum(step_times.values())
    for step, duration in step_times.items():
        pct = duration / total_analysis * 100
        print(f"  {step:20s}: {duration:.3f}s ({pct:5.1f}%)")
    print(f"  {'TOTAL':20s}: {total_analysis:.3f}s")
    
    # Visualization timing
    viz_times = measure_visualization_performance(workload_data)
    
    print("\nVisualization creation:")
    for viz, duration in viz_times.items():
        if 'size' not in viz:
            print(f"  {viz:20s}: {duration:.3f}s")
    
    print("\nVisualization sizes:")
    for viz, size in viz_times.items():
        if 'size' in viz:
            print(f"  {viz:20s}: {size:.1f} KB")
    
    # Test 2: Scaling
    scaling_df = check_data_volume_scaling()
    
    # Test 3: Caching overhead
    check_caching_overhead()
    
    # Test 4: Plotly specifics
    identify_plotly_bottlenecks()
    
    # Summary and recommendations
    print("\n\nPERFORMANCE DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    # Find bottlenecks
    total_time = total_analysis + sum(v for k, v in viz_times.items() if 'size' not in k)
    analysis_pct = total_analysis / total_time * 100
    viz_pct = 100 - analysis_pct
    
    print(f"\nTime distribution:")
    print(f"  Data analysis: {analysis_pct:.1f}%")
    print(f"  Visualization: {viz_pct:.1f}%")
    
    # Save detailed results
    with open('workload_performance_diagnosis.json', 'w') as f:
        json.dump({
            'step_times': step_times,
            'viz_times': viz_times,
            'scaling': scaling_df.to_dict(),
            'summary': {
                'total_analysis_time': total_analysis,
                'analysis_percentage': analysis_pct,
                'viz_percentage': viz_pct
            }
        }, f, indent=2)
    
    print("\nDetailed results saved to workload_performance_diagnosis.json")
    
    # Specific recommendations
    print("\nRECOMMENDATIONS:")
    print("-" * 40)
    
    if analysis_pct > 70:
        print("1. ⚠️  Data analysis is the main bottleneck")
        print("   - Consider pre-computing interval statistics")
        print("   - Cache patient profiles between runs")
    else:
        print("1. ⚠️  Visualization creation is the main bottleneck")
        print("   - Consider simpler visualizations for large datasets")
        print("   - Implement progressive rendering")
    
    if scaling_df.iloc[-1]['total_time'] > 2.0:
        print("2. ⚠️  Performance degrades with large datasets")
        print("   - Implement data sampling for previews")
        print("   - Add 'Show full data' option for detailed view")
    
    print("3. ✅ Ensure Streamlit caching is properly configured")
    print("4. ✅ Monitor browser console for rendering issues")
    print("5. ✅ Consider lazy loading for sub-tabs")


if __name__ == "__main__":
    main()