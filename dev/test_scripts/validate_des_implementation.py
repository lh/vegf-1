"""
Comprehensive validation script for the DES implementation.

This script validates the current treat_and_extend_des_fixed.py implementation
by running a simulation and checking key metrics against expected values:

1. Loading phase completion (all patients should complete loading)
2. Maintenance phase interval progression (8→10→12→14→16 weeks)  
3. Vision outcomes (should match literature values)
4. Discontinuation rates and statistics
5. Treatment frequency patterns
6. Patient state progression

Usage:
    python validate_des_implementation.py
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

from simulation.config import SimulationConfig
from simulation.vision_models import RealisticVisionModel
from treat_and_extend_des_fixed import TreatAndExtendDES, run_treat_and_extend_des

def run_validation_simulation(num_patients=100, duration_days=365*2, random_seed=42):
    """
    Run a DES simulation with controlled parameters for validation.
    
    Parameters
    ----------
    num_patients : int
        Number of patients to simulate
    duration_days : int
        Duration of simulation in days
    random_seed : int
        Random seed for reproducibility
        
    Returns
    -------
    dict
        Dictionary of patient histories
    TreatAndExtendDES
        The simulation object for accessing statistics
    """
    print(f"Running validation simulation with {num_patients} patients for {duration_days/365:.1f} years...")
    
    # Create test configuration
    config = SimulationConfig(
        config_name="des_validation_test",
        num_patients=num_patients,
        duration_days=duration_days,
        start_date="2023-01-01",
        random_seed=random_seed,
        parameters={
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": 0.2,  # 20% chance when eligible
                        "consecutive_visits": 3,
                        "interval_weeks": 16
                    },
                    "random_administrative": {
                        "annual_probability": 0.05  # 5% annual probability
                    },
                    "treatment_duration": {
                        "threshold_weeks": 52,  # 1 year threshold
                        "probability": 0.1  # 10% chance when threshold reached
                    },
                    "premature": {
                        "probability_factor": 0.0  # Disable premature for validation
                    }
                },
                "monitoring": {
                    "planned": {
                        "follow_up_schedule": [12, 24, 36]
                    },
                    "unplanned": {
                        "follow_up_schedule": [8, 16, 24]
                    }
                },
                "retreatment": {
                    "probability": 0.95
                }
            },
            "vision_model_type": "realistic",
            "clinicians": {
                "enabled": True
            }
        }
    )
    
    # Run simulation
    sim = TreatAndExtendDES(config)
    patient_histories = sim.run()
    
    return patient_histories, sim

def validate_loading_phase(patient_histories):
    """
    Validate that patients correctly complete the loading phase.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    bool
        True if validation passes, False otherwise
    """
    print("\nValidating loading phase completion...")
    
    # Extract loading phase statistics
    loading_stats = {
        "total_patients": len(patient_histories),
        "patients_with_visits": 0,
        "loading_visits_count": defaultdict(int),
        "loading_completion": 0
    }
    
    for patient_id, visits in patient_histories.items():
        if not visits:
            continue
            
        loading_stats["patients_with_visits"] += 1
        
        # Count loading phase visits
        loading_visits = [v for v in visits if v.get('phase') == 'loading']
        loading_stats["loading_visits_count"][len(loading_visits)] += 1
        
        # Check for loading phase completion
        maintenance_visits = [v for v in visits if v.get('phase') == 'maintenance']
        if maintenance_visits:
            loading_stats["loading_completion"] += 1
    
    # Calculate loading completion rate
    completion_rate = (loading_stats["loading_completion"] / loading_stats["patients_with_visits"]) * 100
    
    # Print statistics
    print(f"Total patients: {loading_stats['total_patients']}")
    print(f"Patients with visits: {loading_stats['patients_with_visits']}")
    print("Loading visits distribution:")
    for count, patients in sorted(loading_stats["loading_visits_count"].items()):
        print(f"  {count} loading visits: {patients} patients ({(patients/loading_stats['patients_with_visits'])*100:.1f}%)")
    print(f"Loading phase completion rate: {completion_rate:.1f}%")
    
    # Check if loading completion rate is sufficient
    # In a realistic scenario, not all patients may complete loading due to simulation
    # end date or discontinuations, so we check for > 95% instead of 100%
    validation_passed = completion_rate > 95.0
    
    if validation_passed:
        print("✅ Loading phase validation PASSED!")
    else:
        print("❌ Loading phase validation FAILED! Completion rate should be >95%")
    
    return validation_passed

def validate_maintenance_intervals(patient_histories):
    """
    Validate that maintenance phase intervals follow the expected 8→10→12→14→16 pattern.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    bool
        True if validation passes, False otherwise
    """
    print("\nValidating maintenance phase intervals...")
    
    # Extract interval information
    interval_sequence = []
    
    for patient_id, visits in patient_histories.items():
        # Get maintenance visits only
        maintenance_visits = [v for v in visits if v.get('phase') == 'maintenance']
        
        # Need at least 2 visits to calculate intervals
        if len(maintenance_visits) < 2:
            continue
            
        # Calculate intervals between consecutive visits
        for i in range(1, len(maintenance_visits)):
            prev_date = maintenance_visits[i-1].get('date')
            curr_date = maintenance_visits[i].get('date')
            
            if prev_date and curr_date:
                interval_days = (curr_date - prev_date).days
                interval_weeks = round(interval_days / 7.0)
                
                # Only consider realistic intervals (4-20 weeks)
                if 4 <= interval_weeks <= 20:
                    interval_sequence.append(interval_weeks)
    
    # Analyze interval distribution
    if not interval_sequence:
        print("No valid intervals found - possibly no patients reached maintenance phase")
        return False
        
    interval_counts = Counter(interval_sequence)
    expected_intervals = [8, 10, 12, 14, 16]
    
    # Print distribution
    print("Maintenance interval distribution:")
    for interval in sorted(interval_counts.keys()):
        count = interval_counts[interval]
        percentage = (count / len(interval_sequence)) * 100
        marker = "✓" if interval in expected_intervals else "❌"
        print(f"  {interval} weeks: {count} ({percentage:.1f}%) {marker}")
    
    # Check if expected intervals constitute the majority of observations
    expected_count = sum(interval_counts[interval] for interval in expected_intervals)
    expected_percentage = (expected_count / len(interval_sequence)) * 100
    
    print(f"Expected intervals (8,10,12,14,16): {expected_count}/{len(interval_sequence)} ({expected_percentage:.1f}%)")
    
    # Validation passes if expected intervals constitute at least 90% of observations
    validation_passed = expected_percentage >= 90.0
    
    if validation_passed:
        print("✅ Maintenance interval validation PASSED!")
    else:
        print("❌ Maintenance interval validation FAILED! Expected intervals should be ≥90%")
    
    return validation_passed

def validate_vision_outcomes(patient_histories):
    """
    Validate that vision outcomes align with literature expectations.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    bool
        True if validation passes, False otherwise
    """
    print("\nValidating vision outcomes...")
    
    # Extract vision data
    vision_changes = []
    baseline_visions = []
    final_visions = []
    
    for patient_id, visits in patient_histories.items():
        if not visits:
            continue
            
        # Get baseline vision from first visit
        baseline = visits[0].get('vision', None)
        if baseline is None:
            continue
            
        baseline_visions.append(baseline)
        
        # Get final vision from last visit
        final = visits[-1].get('vision', None)
        if final is None:
            continue
            
        final_visions.append(final)
        
        # Calculate change
        change = final - baseline
        vision_changes.append(change)
    
    # Analyze vision changes
    if not vision_changes:
        print("No valid vision data found")
        return False
        
    mean_change = np.mean(vision_changes)
    median_change = np.median(vision_changes)
    std_change = np.std(vision_changes)
    
    # Calculate proportions of improvement, stability, and decline
    improved = sum(1 for change in vision_changes if change > 0)
    stable = sum(1 for change in vision_changes if change == 0)
    declined = sum(1 for change in vision_changes if change < 0)
    
    total = len(vision_changes)
    improved_percent = (improved / total) * 100
    stable_percent = (stable / total) * 100
    declined_percent = (declined / total) * 100
    
    # Print statistics
    print(f"Total patients with vision data: {total}")
    print(f"Mean vision change: {mean_change:.1f} letters")
    print(f"Median vision change: {median_change:.1f} letters")
    print(f"Standard deviation: {std_change:.1f} letters")
    print(f"Patients with improved vision: {improved} ({improved_percent:.1f}%)")
    print(f"Patients with stable vision: {stable} ({stable_percent:.1f}%)")
    print(f"Patients with declined vision: {declined} ({declined_percent:.1f}%)")
    
    # From literature, anticVafte ~7-11 letters improvement after 1 year
    # and majority of patients should improve or maintain vision
    validation_passed = (mean_change >= 7.0 and 
                          improved_percent + stable_percent >= 75.0)
    
    if validation_passed:
        print("✅ Vision outcomes validation PASSED!")
    else:
        print("❌ Vision outcomes validation FAILED! Mean improvement should be ≥7.0 letters")
        print("  and ≥75% of patients should maintain or improve vision")
    
    # Plot vision distribution
    plt.figure(figsize=(10, 6))
    
    # Plot vision change histogram
    plt.subplot(1, 2, 1)
    plt.hist(vision_changes, bins=20, color='skyblue', edgecolor='black')
    plt.axvline(mean_change, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_change:.1f}')
    plt.axvline(median_change, color='green', linestyle='dashed', linewidth=2, label=f'Median: {median_change:.1f}')
    plt.xlabel('Vision Change (ETDRS Letters)')
    plt.ylabel('Number of Patients')
    plt.title('Distribution of Vision Changes')
    plt.legend()
    
    # Plot baseline vs final scatter
    plt.subplot(1, 2, 2)
    plt.scatter(baseline_visions, final_visions, alpha=0.6)
    plt.plot([0, 85], [0, 85], 'r--', label='No Change')
    plt.xlabel('Baseline Vision (ETDRS Letters)')
    plt.ylabel('Final Vision (ETDRS Letters)')
    plt.title('Baseline vs. Final Vision')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('des_vision_validation.png', dpi=300)
    print("Vision validation plot saved to des_vision_validation.png")
    
    return validation_passed

def validate_discontinuation(patient_histories, sim):
    """
    Validate discontinuation rates and patterns.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
    sim : TreatAndExtendDES
        Simulation object with statistics
        
    Returns
    -------
    bool
        True if validation passes, False otherwise
    """
    print("\nValidating discontinuation statistics...")
    
    # Get statistics from simulation
    total_patients = len(patient_histories)
    unique_discontinued = sim.stats.get("unique_discontinuations", 0)
    disc_rate = (unique_discontinued / total_patients) * 100
    
    # Get discontinuation types
    cessation_types = defaultdict(int)
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            treatment_status = visit.get('treatment_status', {})
            cessation_type = treatment_status.get('cessation_type', None)
            
            if cessation_type and cessation_type not in cessation_types:
                cessation_types[cessation_type] = 1
    
    # Get manager statistics
    dm_stats = sim.refactored_manager.get_statistics()
    dm_unique = dm_stats.get("unique_discontinued_patients", 0)
    
    # Print statistics
    print(f"Total patients: {total_patients}")
    print(f"Unique discontinued patients: {unique_discontinued} ({disc_rate:.1f}%)")
    print(f"Discontinuation manager unique discontinued: {dm_unique}")
    
    if cessation_types:
        print("Discontinuation types:")
        for cessation_type in cessation_types:
            print(f"  - {cessation_type}")
    
    # Discontinuation rate should be plausible (5-30%)
    validation_passed = (5.0 <= disc_rate <= 30.0 and 
                          unique_discontinued == dm_unique)
    
    if validation_passed:
        print("✅ Discontinuation validation PASSED!")
    else:
        print("❌ Discontinuation validation FAILED!")
        print("  Discontinuation rate should be 5-30%")
        print("  Simulation and manager counts should match")
    
    return validation_passed

def validate_treatment_frequency(patient_histories):
    """
    Validate treatment frequency patterns.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    bool
        True if validation passes, False otherwise
    """
    print("\nValidating treatment frequency patterns...")
    
    # Calculate visits and injections per patient
    visits_per_patient = []
    injections_per_patient = []
    injection_ratio = []
    
    for patient_id, visits in patient_histories.items():
        if not visits:
            continue
            
        # Count visits
        visit_count = len(visits)
        visits_per_patient.append(visit_count)
        
        # Count injections
        injection_count = 0
        for visit in visits:
            actions = visit.get('actions', [])
            if isinstance(actions, str):
                try:
                    actions = eval(actions)
                except:
                    actions = [actions]
                    
            if 'injection' in actions:
                injection_count += 1
                
        injections_per_patient.append(injection_count)
        
        # Calculate ratio
        if visit_count > 0:
            injection_ratio.append(injection_count / visit_count)
    
    # Analyze statistics
    mean_visits = np.mean(visits_per_patient)
    mean_injections = np.mean(injections_per_patient)
    mean_ratio = np.mean(injection_ratio)
    
    # Print statistics
    print(f"Mean visits per patient: {mean_visits:.1f}")
    print(f"Mean injections per patient: {mean_injections:.1f}")
    print(f"Mean injection/visit ratio: {mean_ratio:.2f}")
    
    # In treat-and-extend, all visits should include injections
    # So ratio should be close to 1.0
    validation_passed = mean_ratio >= 0.95  # Allow for small tolerance
    
    if validation_passed:
        print("✅ Treatment frequency validation PASSED!")
    else:
        print("❌ Treatment frequency validation FAILED!")
        print("  Injection/visit ratio should be ≥0.95")
    
    return validation_passed

def validate_patient_progression(patient_histories):
    """
    Validate patient state progression through protocol phases.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
        
    Returns
    -------
    bool
        True if validation passes, False otherwise
    """
    print("\nValidating patient state progression...")
    
    # Check patient progression through protocol phases
    valid_progressions = 0
    total_progressions = 0
    phase_sequences = []
    
    for patient_id, visits in patient_histories.items():
        if len(visits) <= 1:
            continue
            
        # Extract phase sequence
        phases = [visit.get('phase', '') for visit in visits]
        phase_sequences.append(phases)
        
        # Check if sequence starts with loading
        if phases[0] != 'loading':
            continue
            
        # Check if progression is valid
        # Loading → Loading → Loading → Maintenance is valid
        # Loading → Maintenance is valid
        # Loading → Loading → Discontinued is valid
        # etc.
        
        valid_sequence = True
        loading_seen = False
        maintenance_seen = False
        monitoring_seen = False
        
        for i, phase in enumerate(phases):
            if phase == 'loading':
                loading_seen = True
                # Once we've seen maintenance, we shouldn't go back to loading
                # unless there was monitoring (retreatment)
                if maintenance_seen and not monitoring_seen:
                    valid_sequence = False
                    break
                    
            elif phase == 'maintenance':
                maintenance_seen = True
                # Maintenance should only come after loading
                if not loading_seen:
                    valid_sequence = False
                    break
                    
            elif phase == 'monitoring':
                monitoring_seen = True
                # Monitoring should only come after maintenance
                if not maintenance_seen:
                    valid_sequence = False
                    break
        
        total_progressions += 1
        if valid_sequence:
            valid_progressions += 1
    
    # Calculate valid progression rate
    valid_rate = (valid_progressions / total_progressions) * 100 if total_progressions > 0 else 0
    
    # Print statistics
    print(f"Total patients with multiple visits: {total_progressions}")
    print(f"Patients with valid phase progression: {valid_progressions} ({valid_rate:.1f}%)")
    
    # Sample a few sequences for inspection
    if phase_sequences:
        print("Sample phase sequences:")
        for i, sequence in enumerate(phase_sequences[:3]):
            print(f"  Patient {i+1}: {' → '.join(sequence)}")
    
    # Validation passes if most progressions are valid
    validation_passed = valid_rate >= 95.0
    
    if validation_passed:
        print("✅ Patient progression validation PASSED!")
    else:
        print("❌ Patient progression validation FAILED!")
        print("  Valid progression rate should be ≥95%")
    
    return validation_passed

def plot_visit_intervals(patient_histories):
    """
    Plot visit intervals to visualize the maintenance phase pattern.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
    """
    # Extract intervals by phase
    loading_intervals = []
    maintenance_intervals = []
    
    for patient_id, visits in patient_histories.items():
        if len(visits) < 2:
            continue
            
        for i in range(1, len(visits)):
            prev_phase = visits[i-1].get('phase', '')
            curr_phase = visits[i].get('phase', '')
            
            prev_date = visits[i-1].get('date')
            curr_date = visits[i].get('date')
            
            if prev_date and curr_date:
                interval_days = (curr_date - prev_date).days
                interval_weeks = interval_days / 7.0
                
                # Only consider realistic intervals (2-20 weeks)
                if 2 <= interval_weeks <= 20:
                    if prev_phase == 'loading' and curr_phase == 'loading':
                        loading_intervals.append(interval_weeks)
                    elif prev_phase == 'maintenance' and curr_phase == 'maintenance':
                        maintenance_intervals.append(interval_weeks)
    
    # Create plot
    plt.figure(figsize=(12, 6))
    
    # Plot loading intervals
    plt.subplot(1, 2, 1)
    plt.hist(loading_intervals, bins=np.arange(2, 21, 1), alpha=0.7, color='blue')
    plt.axvline(4, color='red', linestyle='--', label='Expected (4 weeks)')
    plt.xlabel('Interval (weeks)')
    plt.ylabel('Frequency')
    plt.title('Loading Phase Intervals')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Plot maintenance intervals
    plt.subplot(1, 2, 2)
    plt.hist(maintenance_intervals, bins=np.arange(2, 21, 1), alpha=0.7, color='green')
    for expected in [8, 10, 12, 14, 16]:
        plt.axvline(expected, color='red', linestyle='--')
    plt.text(10, plt.ylim()[1]*0.95, 'Expected: 8, 10, 12, 14, 16 weeks', ha='center')
    plt.xlabel('Interval (weeks)')
    plt.ylabel('Frequency')
    plt.title('Maintenance Phase Intervals')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('des_intervals_validation.png', dpi=300)
    print("Interval validation plot saved to des_intervals_validation.png")

def main():
    """Main validation function."""
    # Run validation simulation
    patient_histories, sim = run_validation_simulation()
    
    # Create a simple DataFrame for analysis
    all_visits = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            visit_data = {
                'patient_id': patient_id,
                'date': visit.get('date'),
                'phase': visit.get('phase'),
                'vision': visit.get('vision'),
                'type': visit.get('type')
            }
            all_visits.append(visit_data)
    
    df = pd.DataFrame(all_visits)
    if len(df) > 0:
        df['date'] = pd.to_datetime(df['date'])
        df.to_csv('des_validation_data.csv', index=False)
        print(f"Saved {len(df)} visits to des_validation_data.csv")
    
    # Create validation plots
    plot_visit_intervals(patient_histories)
    
    # Run validation tests
    validation_tests = [
        validate_loading_phase(patient_histories),
        validate_maintenance_intervals(patient_histories),
        validate_vision_outcomes(patient_histories),
        validate_discontinuation(patient_histories, sim),
        validate_treatment_frequency(patient_histories),
        validate_patient_progression(patient_histories)
    ]
    
    # Print overall validation result
    total_tests = len(validation_tests)
    passed_tests = sum(validation_tests)
    
    print(f"\nValidation Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n✅ ALL TESTS PASSED - DES implementation is working correctly!")
    else:
        print(f"\n❌ {total_tests - passed_tests} TESTS FAILED - See details above")

if __name__ == "__main__":
    main()