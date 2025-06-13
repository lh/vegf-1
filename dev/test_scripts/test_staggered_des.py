"""
Test script for the staggered DES implementation.

This script verifies the functionality of the staggered DES implementation by:
1. Running a staggered simulation
2. Analyzing the temporal distribution of patient arrivals
3. Checking patient visit histories and timelines
4. Generating visualizations to verify proper staggered enrollment
5. Comparing results with standard DES implementation
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

from simulation.config import SimulationConfig
from treat_and_extend_des_fixed import TreatAndExtendDES, run_treat_and_extend_des
from staggered_treat_and_extend_des import StaggeredTreatAndExtendDES, run_staggered_treat_and_extend_des

def create_test_config():
    """Create a test configuration for comparing simulations."""
    # Create test configuration
    config = SimulationConfig(
        config_name="des_comparison_test",
        num_patients=100,
        duration_days=365,
        start_date="2023-01-01",
        random_seed=42,
        parameters={
            "vision_model_type": "realistic",
            "vision": {
                "baseline_mean": 65,
                "baseline_std": 10,
                "max_letters": 85,
                "min_letters": 0,
                "headroom_factor": 0.5
            },
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": 0.2,
                        "consecutive_visits": 3,
                        "interval_weeks": 16
                    }
                }
            }
        }
    )
    
    return config

def run_standard_des(config):
    """Run standard DES simulation."""
    print("\n===== Running Standard DES Simulation =====")
    patient_histories = run_treat_and_extend_des(config)
    print(f"Simulation completed with {len(patient_histories)} patients")
    return patient_histories

def run_staggered_des(config):
    """Run staggered DES simulation."""
    print("\n===== Running Staggered DES Simulation =====")
    results = run_staggered_treat_and_extend_des(
        config=config,
        patient_arrival_rate=5.0,  # ~5 new patients per week
        verbose=True
    )
    patient_histories = results['patient_histories']
    enrollment_dates = results['enrollment_dates']
    print(f"Simulation completed with {len(patient_histories)} patients")
    return patient_histories, enrollment_dates

def compare_enrollment_timelines(standard_histories, staggered_histories, enrollment_dates):
    """Compare enrollment timelines between standard and staggered."""
    # Extract standard enrollment date (first visit date for each patient)
    standard_enrollment = {}
    for patient_id, visits in standard_histories.items():
        if visits:
            standard_enrollment[patient_id] = visits[0].get('date')
    
    # Extract staggered enrollment date from enrollment_dates
    staggered_enrollment = enrollment_dates
    
    # Convert to lists for plotting
    standard_dates = list(standard_enrollment.values())
    staggered_dates = list(staggered_enrollment.values())
    
    # Create comparison plot
    plt.figure(figsize=(12, 6))
    
    # Plot standard enrollment (should be all on the same day)
    plt.subplot(1, 2, 1)
    plt.hist(standard_dates, bins=20, alpha=0.7, color='blue')
    plt.title('Standard DES Patient Enrollment')
    plt.xlabel('Date')
    plt.ylabel('Number of Patients')
    plt.xticks(rotation=45)
    
    # Plot staggered enrollment (should be spread over time)
    plt.subplot(1, 2, 2)
    plt.hist(staggered_dates, bins=20, alpha=0.7, color='green')
    plt.title('Staggered DES Patient Enrollment')
    plt.xlabel('Date')
    plt.ylabel('Number of Patients')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('enrollment_comparison.png')
    plt.close()
    print("Saved enrollment comparison to enrollment_comparison.png")
    
    # Return enrollment statistics
    return {
        'standard': {
            'start': min(standard_dates),
            'end': max(standard_dates),
            'count': len(standard_dates)
        },
        'staggered': {
            'start': min(staggered_dates),
            'end': max(staggered_dates),
            'count': len(staggered_dates)
        }
    }

def analyze_resource_utilization(standard_histories, staggered_histories):
    """Analyze resource utilization patterns between standard and staggered."""
    # Function to count visits and actions by week
    def count_by_week(histories):
        weekly_counts = defaultdict(lambda: defaultdict(int))
        
        for patient_id, visits in histories.items():
            for visit in visits:
                visit_date = visit.get('date')
                if not visit_date:
                    continue
                
                # Get week number relative to simulation start
                week_num = int((visit_date - datetime(2023, 1, 1)).days / 7)
                
                # Count visit
                weekly_counts[week_num]['visits'] += 1
                
                # Count actions
                actions = visit.get('actions', [])
                if isinstance(actions, str):
                    try:
                        actions = eval(actions)
                    except:
                        actions = [actions]
                
                if 'injection' in actions:
                    weekly_counts[week_num]['injections'] += 1
                if 'oct_scan' in actions:
                    weekly_counts[week_num]['oct_scans'] += 1
                if 'vision_test' in actions:
                    weekly_counts[week_num]['vision_tests'] += 1
        
        return weekly_counts
    
    # Count resources for both simulations
    standard_counts = count_by_week(standard_histories)
    staggered_counts = count_by_week(staggered_histories)
    
    # Convert to DataFrame for plotting
    standard_df = pd.DataFrame([
        {'week': week, 'resource': resource, 'count': count}
        for week, resources in standard_counts.items()
        for resource, count in resources.items()
    ])
    
    staggered_df = pd.DataFrame([
        {'week': week, 'resource': resource, 'count': count}
        for week, resources in staggered_counts.items()
        for resource, count in resources.items()
    ])
    
    # Pivot for easier plotting
    standard_pivot = standard_df.pivot(index='week', columns='resource', values='count').fillna(0)
    staggered_pivot = staggered_df.pivot(index='week', columns='resource', values='count').fillna(0)
    
    # Ensure all weeks are represented
    all_weeks = sorted(set(standard_pivot.index) | set(staggered_pivot.index))
    
    # Create resource utilization comparison plot
    plt.figure(figsize=(15, 10))
    
    resources = ['visits', 'injections', 'oct_scans', 'vision_tests']
    titles = ['Total Visits', 'Injections', 'OCT Scans', 'Vision Tests']
    
    for i, (resource, title) in enumerate(zip(resources, titles)):
        plt.subplot(2, 2, i+1)
        
        # Create series with all weeks
        standard_series = pd.Series(index=all_weeks, name='standard')
        staggered_series = pd.Series(index=all_weeks, name='staggered')
        
        # Fill with data
        for week in all_weeks:
            if week in standard_pivot.index and resource in standard_pivot.columns:
                standard_series[week] = standard_pivot.loc[week, resource]
            else:
                standard_series[week] = 0
                
            if week in staggered_pivot.index and resource in staggered_pivot.columns:
                staggered_series[week] = staggered_pivot.loc[week, resource]
            else:
                staggered_series[week] = 0
        
        # Plot
        plt.plot(standard_series.index, standard_series.values, label='Standard DES', color='blue')
        plt.plot(staggered_series.index, staggered_series.values, label='Staggered DES', color='green')
        
        plt.title(title)
        plt.xlabel('Week')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('resource_utilization_comparison.png')
    plt.close()
    print("Saved resource utilization comparison to resource_utilization_comparison.png")
    
    # Return resource statistics
    return {
        'standard': {
            'total_visits': standard_pivot['visits'].sum() if 'visits' in standard_pivot.columns else 0,
            'total_injections': standard_pivot['injections'].sum() if 'injections' in standard_pivot.columns else 0,
            'peak_visits': standard_pivot['visits'].max() if 'visits' in standard_pivot.columns else 0
        },
        'staggered': {
            'total_visits': staggered_pivot['visits'].sum() if 'visits' in staggered_pivot.columns else 0,
            'total_injections': staggered_pivot['injections'].sum() if 'injections' in staggered_pivot.columns else 0,
            'peak_visits': staggered_pivot['visits'].max() if 'visits' in staggered_pivot.columns else 0
        }
    }

def plot_vision_outcomes(standard_histories, staggered_histories, enrollment_dates):
    """Plot vision outcomes between standard and staggered simulations."""
    # Function to calculate average vision over time
    def calculate_vision_by_time(histories, enrollment_dates=None, time_type='calendar'):
        """Calculate mean vision by time."""
        all_data = []
        
        for patient_id, visits in histories.items():
            for visit in visits:
                vision = visit.get('vision')
                date = visit.get('date')
                
                if vision is None or date is None:
                    continue
                
                # Determine time point based on time type
                if time_type == 'patient' and enrollment_dates and patient_id in enrollment_dates:
                    # Calculate weeks since enrollment
                    enrollment = enrollment_dates[patient_id]
                    weeks_since_enrollment = (date - enrollment).days / 7
                    time_point = weeks_since_enrollment
                else:
                    # Use calendar time (weeks since simulation start)
                    weeks_since_start = (date - datetime(2023, 1, 1)).days / 7
                    time_point = weeks_since_start
                
                all_data.append({
                    'patient_id': patient_id,
                    'time_point': time_point,
                    'vision': vision
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        # Group by time point and calculate mean, count, and confidence interval
        if len(df) > 0:
            # Round time points to nearest week
            df['time_point_rounded'] = df['time_point'].round()
            
            # Group and calculate statistics
            grouped = df.groupby('time_point_rounded').agg(
                mean_vision=('vision', 'mean'),
                count=('vision', 'count'),
                std=('vision', 'std')
            ).reset_index()
            
            # Calculate confidence interval
            grouped['ci'] = 1.96 * grouped['std'] / np.sqrt(grouped['count'])
            
            return grouped
        else:
            return pd.DataFrame(columns=['time_point_rounded', 'mean_vision', 'count', 'std', 'ci'])
    
    # Calculate vision stats for both simulations
    standard_vision = calculate_vision_by_time(standard_histories)
    staggered_calendar_vision = calculate_vision_by_time(staggered_histories)
    staggered_patient_vision = calculate_vision_by_time(staggered_histories, enrollment_dates, 'patient')
    
    # Create vision outcome plots
    plt.figure(figsize=(15, 10))
    
    # Plot calendar time comparison
    plt.subplot(2, 1, 1)
    plt.plot(standard_vision['time_point_rounded'], standard_vision['mean_vision'], 
             label='Standard DES', marker='o', color='blue')
    plt.fill_between(
        standard_vision['time_point_rounded'],
        standard_vision['mean_vision'] - standard_vision['ci'],
        standard_vision['mean_vision'] + standard_vision['ci'],
        alpha=0.2, color='blue'
    )
    
    plt.plot(staggered_calendar_vision['time_point_rounded'], staggered_calendar_vision['mean_vision'], 
             label='Staggered DES (Calendar Time)', marker='s', color='green')
    plt.fill_between(
        staggered_calendar_vision['time_point_rounded'],
        staggered_calendar_vision['mean_vision'] - staggered_calendar_vision['ci'],
        staggered_calendar_vision['mean_vision'] + staggered_calendar_vision['ci'],
        alpha=0.2, color='green'
    )
    
    plt.title('Mean Visual Acuity by Calendar Time')
    plt.xlabel('Weeks Since Simulation Start')
    plt.ylabel('Visual Acuity (ETDRS Letters)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot patient time (staggered only)
    plt.subplot(2, 1, 2)
    plt.plot(staggered_patient_vision['time_point_rounded'], staggered_patient_vision['mean_vision'], 
             label='Staggered DES (Patient Time)', marker='D', color='purple')
    plt.fill_between(
        staggered_patient_vision['time_point_rounded'],
        staggered_patient_vision['mean_vision'] - staggered_patient_vision['ci'],
        staggered_patient_vision['mean_vision'] + staggered_patient_vision['ci'],
        alpha=0.2, color='purple'
    )
    
    # Add sample size information as a bar chart
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    ax2.bar(staggered_patient_vision['time_point_rounded'], staggered_patient_vision['count'], 
            alpha=0.2, color='gray', width=1.0)
    ax2.set_ylabel('Number of Patients')
    
    plt.title('Mean Visual Acuity by Patient Time (Staggered DES)')
    plt.xlabel('Weeks Since Enrollment')
    plt.ylabel('Visual Acuity (ETDRS Letters)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('vision_outcomes_comparison.png')
    plt.close()
    print("Saved vision outcomes comparison to vision_outcomes_comparison.png")

def main():
    """Main test function."""
    print("Testing Staggered DES Implementation")
    
    # Create test configuration
    config = create_test_config()
    
    # Run standard DES
    standard_histories = run_standard_des(config)
    
    # Run staggered DES
    staggered_histories, enrollment_dates = run_staggered_des(config)
    
    # Compare enrollment timelines
    enrollment_stats = compare_enrollment_timelines(standard_histories, staggered_histories, enrollment_dates)
    print("\nEnrollment Statistics:")
    print(f"Standard: {enrollment_stats['standard']['count']} patients enrolled between {enrollment_stats['standard']['start']} and {enrollment_stats['standard']['end']}")
    print(f"Staggered: {enrollment_stats['staggered']['count']} patients enrolled between {enrollment_stats['staggered']['start']} and {enrollment_stats['staggered']['end']}")
    
    # Analyze resource utilization
    resource_stats = analyze_resource_utilization(standard_histories, staggered_histories)
    print("\nResource Utilization Statistics:")
    print(f"Standard: {resource_stats['standard']['total_visits']} total visits, {resource_stats['standard']['total_injections']} injections, peak of {resource_stats['standard']['peak_visits']} visits in a week")
    print(f"Staggered: {resource_stats['staggered']['total_visits']} total visits, {resource_stats['staggered']['total_injections']} injections, peak of {resource_stats['staggered']['peak_visits']} visits in a week")
    
    # Plot vision outcomes
    plot_vision_outcomes(standard_histories, staggered_histories, enrollment_dates)
    
    print("\nTest completed successfully!")
    print("Generated visualizations:")
    print("1. enrollment_comparison.png - Patient enrollment distribution")
    print("2. resource_utilization_comparison.png - Resource utilization patterns")
    print("3. vision_outcomes_comparison.png - Vision outcomes by calendar and patient time")

if __name__ == "__main__":
    main()