"""
Test script for the treat-and-extend ABS implementation.

This script runs the treat-and-extend ABS implementation and verifies that it's
following the protocol correctly by analyzing patient visit patterns, intervals,
and vision outcomes.

Usage:
    python test_abs_implementation.py

Output:
    - Console output with test results
    - Visualization of patient visit patterns
    - Visualization of vision outcomes
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from simulation.config import SimulationConfig
from treat_and_extend_abs import run_treat_and_extend_abs

def analyze_patient_intervals(patient_histories):
    """
    Analyze patient visit intervals to verify protocol compliance.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary mapping patient IDs to their visit histories
        
    Returns
    -------
    dict
        Dictionary containing interval analysis results
    """
    # Initialize counters
    loading_phase_visits = 0
    maintenance_phase_visits = 0
    loading_phase_intervals = []
    maintenance_phase_intervals = []
    
    # Analyze each patient's visit history
    for patient_id, visits in patient_histories.items():
        # Sort visits by date
        sorted_visits = sorted(visits, key=lambda v: v['date'])
        
        # Skip patients with fewer than 2 visits
        if len(sorted_visits) < 2:
            continue
        
        # Analyze intervals between visits
        for i in range(1, len(sorted_visits)):
            prev_visit = sorted_visits[i-1]
            curr_visit = sorted_visits[i]
            
            # Calculate interval in weeks
            interval_days = (curr_visit['date'] - prev_visit['date']).days
            interval_weeks = interval_days / 7.0
            
            # Categorize by phase
            if curr_visit['phase'] == 'loading':
                loading_phase_visits += 1
                loading_phase_intervals.append(interval_weeks)
            elif curr_visit['phase'] == 'maintenance':
                maintenance_phase_visits += 1
                maintenance_phase_intervals.append(interval_weeks)
    
    # Calculate statistics
    results = {
        'loading_phase_visits': loading_phase_visits,
        'maintenance_phase_visits': maintenance_phase_visits,
        'loading_phase_mean_interval': np.mean(loading_phase_intervals) if loading_phase_intervals else 0,
        'maintenance_phase_mean_interval': np.mean(maintenance_phase_intervals) if maintenance_phase_intervals else 0,
        'loading_phase_intervals': loading_phase_intervals,
        'maintenance_phase_intervals': maintenance_phase_intervals
    }
    
    return results

def analyze_phase_transitions(patient_histories):
    """
    Analyze phase transitions to verify protocol compliance.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary mapping patient IDs to their visit histories
        
    Returns
    -------
    dict
        Dictionary containing phase transition analysis results
    """
    # Initialize counters
    total_patients = len(patient_histories)
    patients_with_loading_phase = 0
    patients_completing_loading_phase = 0
    loading_phase_injection_count = []
    
    # Analyze each patient's visit history
    for patient_id, visits in patient_histories.items():
        # Count loading phase visits
        loading_visits = [v for v in visits if v['phase'] == 'loading']
        maintenance_visits = [v for v in visits if v['phase'] == 'maintenance']
        
        if loading_visits:
            patients_with_loading_phase += 1
            loading_phase_injection_count.append(len(loading_visits))
        
        if maintenance_visits:
            patients_completing_loading_phase += 1
    
    # Calculate statistics
    results = {
        'total_patients': total_patients,
        'patients_with_loading_phase': patients_with_loading_phase,
        'patients_completing_loading_phase': patients_completing_loading_phase,
        'loading_phase_completion_rate': (patients_completing_loading_phase / total_patients) * 100 if total_patients > 0 else 0,
        'mean_loading_phase_injections': np.mean(loading_phase_injection_count) if loading_phase_injection_count else 0
    }
    
    return results

def analyze_vision_outcomes(patient_histories):
    """
    Analyze vision outcomes to verify treatment effectiveness.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary mapping patient IDs to their visit histories
        
    Returns
    -------
    dict
        Dictionary containing vision outcome analysis results
    """
    # Initialize lists for vision data
    baseline_vision = []
    final_vision = []
    vision_change = []
    
    # Analyze each patient's visit history
    for patient_id, visits in patient_histories.items():
        # Skip patients with no visits
        if not visits:
            continue
        
        # Sort visits by date
        sorted_visits = sorted(visits, key=lambda v: v['date'])
        
        # Get baseline and final vision
        first_visit = sorted_visits[0]
        last_visit = sorted_visits[-1]
        
        baseline = first_visit['baseline_vision']
        final = last_visit['vision']
        
        baseline_vision.append(baseline)
        final_vision.append(final)
        vision_change.append(final - baseline)
    
    # Calculate statistics
    results = {
        'mean_baseline_vision': np.mean(baseline_vision) if baseline_vision else 0,
        'mean_final_vision': np.mean(final_vision) if final_vision else 0,
        'mean_vision_change': np.mean(vision_change) if vision_change else 0,
        'vision_improved_percent': (np.sum(np.array(vision_change) > 0) / len(vision_change)) * 100 if vision_change else 0,
        'vision_stable_percent': (np.sum(np.array(vision_change) == 0) / len(vision_change)) * 100 if vision_change else 0,
        'vision_declined_percent': (np.sum(np.array(vision_change) < 0) / len(vision_change)) * 100 if vision_change else 0
    }
    
    return results

def plot_interval_distribution(interval_results):
    """
    Plot the distribution of visit intervals.
    
    Parameters
    ----------
    interval_results : dict
        Dictionary containing interval analysis results
    """
    plt.figure(figsize=(12, 6))
    
    # Plot loading phase intervals
    if interval_results['loading_phase_intervals']:
        plt.subplot(1, 2, 1)
        plt.hist(interval_results['loading_phase_intervals'], bins=10, alpha=0.7)
        plt.axvline(x=4, color='r', linestyle='--', label='Target (4 weeks)')
        plt.title('Loading Phase Intervals')
        plt.xlabel('Interval (weeks)')
        plt.ylabel('Frequency')
        plt.legend()
    
    # Plot maintenance phase intervals
    if interval_results['maintenance_phase_intervals']:
        plt.subplot(1, 2, 2)
        plt.hist(interval_results['maintenance_phase_intervals'], bins=10, alpha=0.7)
        plt.axvline(x=8, color='r', linestyle='--', label='Min (8 weeks)')
        plt.axvline(x=16, color='g', linestyle='--', label='Max (16 weeks)')
        plt.title('Maintenance Phase Intervals')
        plt.xlabel('Interval (weeks)')
        plt.ylabel('Frequency')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig('abs_interval_distribution.png')
    print("Saved interval distribution plot to abs_interval_distribution.png")

def plot_patient_trajectories(patient_histories, max_patients=10):
    """
    Plot individual patient visit trajectories.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary mapping patient IDs to their visit histories
    max_patients : int, optional
        Maximum number of patients to plot, by default 10
    """
    plt.figure(figsize=(12, 8))
    
    # Select a subset of patients
    patient_ids = list(patient_histories.keys())
    if len(patient_ids) > max_patients:
        patient_ids = np.random.choice(patient_ids, max_patients, replace=False)
    
    # Plot each patient's trajectory
    for i, patient_id in enumerate(patient_ids):
        visits = patient_histories[patient_id]
        sorted_visits = sorted(visits, key=lambda v: v['date'])
        
        # Skip patients with fewer than 2 visits
        if len(sorted_visits) < 2:
            continue
        
        # Extract dates and intervals
        dates = [v['date'] for v in sorted_visits]
        intervals = []
        
        for j in range(1, len(dates)):
            interval_days = (dates[j] - dates[j-1]).days
            intervals.append(interval_days / 7.0)
        
        # Plot intervals
        plt.plot(range(1, len(intervals) + 1), intervals, 'o-', label=f'Patient {patient_id}')
    
    plt.axhline(y=4, color='r', linestyle='--', label='Loading Phase (4 weeks)')
    plt.axhline(y=8, color='g', linestyle='--', label='Initial Maintenance (8 weeks)')
    plt.axhline(y=16, color='b', linestyle='--', label='Maximum Interval (16 weeks)')
    
    plt.title('Patient Visit Intervals')
    plt.xlabel('Visit Number')
    plt.ylabel('Interval (weeks)')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('abs_patient_trajectories.png')
    print("Saved patient trajectories plot to abs_patient_trajectories.png")

def plot_vision_outcomes(vision_results, patient_histories, max_patients=10):
    """
    Plot vision outcomes.
    
    Parameters
    ----------
    vision_results : dict
        Dictionary containing vision outcome analysis results
    patient_histories : dict
        Dictionary mapping patient IDs to their visit histories
    max_patients : int, optional
        Maximum number of patients to plot, by default 10
    """
    plt.figure(figsize=(12, 8))
    
    # Plot mean vision change
    plt.subplot(2, 1, 1)
    plt.bar(['Baseline', 'Final'], 
            [vision_results['mean_baseline_vision'], vision_results['mean_final_vision']], 
            alpha=0.7)
    plt.title('Mean Vision (ETDRS Letters)')
    plt.ylabel('Vision (ETDRS Letters)')
    plt.grid(True, axis='y')
    
    # Plot individual patient trajectories
    plt.subplot(2, 1, 2)
    
    # Select a subset of patients
    patient_ids = list(patient_histories.keys())
    if len(patient_ids) > max_patients:
        patient_ids = np.random.choice(patient_ids, max_patients, replace=False)
    
    # Plot each patient's vision trajectory
    for patient_id in patient_ids:
        visits = patient_histories[patient_id]
        sorted_visits = sorted(visits, key=lambda v: v['date'])
        
        # Skip patients with fewer than 2 visits
        if len(sorted_visits) < 2:
            continue
        
        # Extract dates and vision
        dates = [(v['date'] - sorted_visits[0]['date']).days / 7.0 for v in sorted_visits]  # Convert to weeks
        vision = [v['vision'] for v in sorted_visits]
        
        # Plot vision trajectory
        plt.plot(dates, vision, 'o-', label=f'Patient {patient_id}')
    
    plt.title('Individual Patient Vision Trajectories')
    plt.xlabel('Weeks from First Visit')
    plt.ylabel('Vision (ETDRS Letters)')
    plt.grid(True)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    
    plt.tight_layout()
    plt.savefig('abs_vision_outcomes.png')
    print("Saved vision outcomes plot to abs_vision_outcomes.png")

def run_tests():
    """
    Run tests on the treat-and-extend ABS implementation.
    """
    print("Running tests on treat-and-extend ABS implementation...")
    
    # Load configuration
    config = SimulationConfig.from_yaml("eylea_literature_based")
    
    # Set a smaller number of patients for testing
    config.num_patients = 100
    
    # Run simulation
    patient_histories = run_treat_and_extend_abs(config, verbose=True)
    
    # Analyze results
    interval_results = analyze_patient_intervals(patient_histories)
    phase_results = analyze_phase_transitions(patient_histories)
    vision_results = analyze_vision_outcomes(patient_histories)
    
    # Print results
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    
    print("\nInterval Analysis:")
    print(f"Loading Phase Mean Interval: {interval_results['loading_phase_mean_interval']:.2f} weeks")
    print(f"Maintenance Phase Mean Interval: {interval_results['maintenance_phase_mean_interval']:.2f} weeks")
    
    print("\nPhase Transition Analysis:")
    print(f"Total Patients: {phase_results['total_patients']}")
    print(f"Patients with Loading Phase: {phase_results['patients_with_loading_phase']}")
    print(f"Patients Completing Loading Phase: {phase_results['patients_completing_loading_phase']}")
    print(f"Loading Phase Completion Rate: {phase_results['loading_phase_completion_rate']:.1f}%")
    print(f"Mean Loading Phase Injections: {phase_results['mean_loading_phase_injections']:.1f}")
    
    print("\nVision Outcome Analysis:")
    print(f"Mean Baseline Vision: {vision_results['mean_baseline_vision']:.1f} letters")
    print(f"Mean Final Vision: {vision_results['mean_final_vision']:.1f} letters")
    print(f"Mean Vision Change: {vision_results['mean_vision_change']:.1f} letters")
    print(f"Vision Improved: {vision_results['vision_improved_percent']:.1f}%")
    print(f"Vision Stable: {vision_results['vision_stable_percent']:.1f}%")
    print(f"Vision Declined: {vision_results['vision_declined_percent']:.1f}%")
    
    # Generate plots
    plot_interval_distribution(interval_results)
    plot_patient_trajectories(patient_histories)
    plot_vision_outcomes(vision_results, patient_histories)
    
    # Verify protocol compliance
    print("\n" + "="*50)
    print("PROTOCOL COMPLIANCE VERIFICATION")
    print("="*50)
    
    # Check loading phase interval
    loading_interval_ok = 3.5 <= interval_results['loading_phase_mean_interval'] <= 4.5
    print(f"Loading Phase Interval (~4 weeks): {'PASS' if loading_interval_ok else 'FAIL'}")
    
    # Check maintenance phase interval
    maintenance_interval_ok = 8.0 <= interval_results['maintenance_phase_mean_interval'] <= 16.0
    print(f"Maintenance Phase Interval (8-16 weeks): {'PASS' if maintenance_interval_ok else 'FAIL'}")
    
    # Check loading phase completion
    loading_completion_ok = phase_results['loading_phase_completion_rate'] >= 95.0
    print(f"Loading Phase Completion (≥95%): {'PASS' if loading_completion_ok else 'FAIL'}")
    
    # Check vision improvement
    vision_improvement_ok = vision_results['mean_vision_change'] >= 10.0
    print(f"Vision Improvement (≥10 letters): {'PASS' if vision_improvement_ok else 'FAIL'}")
    
    # Overall assessment
    all_tests_passed = loading_interval_ok and maintenance_interval_ok and loading_completion_ok and vision_improvement_ok
    print("\nOverall Assessment: " + ("PASS" if all_tests_passed else "FAIL"))
    
    return all_tests_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
