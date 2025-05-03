"""
Analyze individual patient data from the DES simulation.

This script extracts and analyzes individual patient data from the DES simulation,
focusing on treatment patterns, phase transitions, and visit intervals.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from treat_and_extend_des import run_treat_and_extend_des
from simulation.config import SimulationConfig

def analyze_des_patients(config_name="eylea_literature_based", sample_size=10):
    """
    Analyze individual patient data from the DES simulation.
    
    Parameters
    ----------
    config_name : str, optional
        Name of the configuration file, by default "eylea_literature_based"
    sample_size : int, optional
        Number of patients to sample for detailed analysis, by default 10
    
    Returns
    -------
    tuple
        (all_patient_data, sampled_patients) - DataFrames with patient data
    """
    # Load configuration and run simulation
    config = SimulationConfig.from_yaml(config_name)
    print(f"Running DES simulation with {config_name} configuration...")
    patient_histories = run_treat_and_extend_des(config, verbose=False)
    
    # Convert patient histories to DataFrame
    all_data = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            # Extract key data from visit
            visit_data = {
                'patient_id': patient_id,
                'date': visit.get('date', ''),
                'vision': visit.get('vision', None),
                'baseline_vision': visit.get('baseline_vision', None),
                'phase': visit.get('phase', ''),
                'type': visit.get('type', ''),
                'actions': str(visit.get('actions', [])),
                'disease_state': str(visit.get('disease_state', '')),
                'treatment_status': str(visit.get('treatment_status', {}))
            }
            all_data.append(visit_data)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save all data to CSV
    df.to_csv('des_data_dump.csv', index=False)
    print(f"Saved data for {len(patient_histories)} patients to des_data_dump.csv")
    
    # Sample patients for detailed analysis
    sampled_patient_ids = np.random.choice(list(patient_histories.keys()), 
                                          min(sample_size, len(patient_histories)), 
                                          replace=False)
    
    # Filter data for sampled patients
    sampled_df = df[df['patient_id'].isin(sampled_patient_ids)]
    
    # Save sampled data to CSV
    sampled_df.to_csv('des_sampled_patients.csv', index=False)
    print(f"Saved detailed data for {len(sampled_patient_ids)} sampled patients to des_sampled_patients.csv")
    
    # Analyze treatment patterns
    analyze_treatment_patterns(df, sampled_df, sampled_patient_ids)
    
    return df, sampled_df

def analyze_treatment_patterns(df, sampled_df, sampled_patient_ids):
    """
    Analyze treatment patterns from patient data.
    
    Parameters
    ----------
    df : pd.DataFrame
        All patient data
    sampled_df : pd.DataFrame
        Data for sampled patients
    sampled_patient_ids : list
        List of sampled patient IDs
    """
    # Count visits and injections per patient
    visit_counts = df.groupby('patient_id').size().reset_index(name='visit_count')
    injection_counts = df[df['actions'].str.contains('injection')].groupby('patient_id').size().reset_index(name='injection_count')
    
    # Merge counts
    patient_counts = pd.merge(visit_counts, injection_counts, on='patient_id', how='left')
    patient_counts['injection_count'] = patient_counts['injection_count'].fillna(0)
    
    # Calculate statistics
    avg_visits = patient_counts['visit_count'].mean()
    avg_injections = patient_counts['injection_count'].mean()
    max_visits = patient_counts['visit_count'].max()
    min_visits = patient_counts['visit_count'].min()
    
    print("\nTreatment Pattern Analysis:")
    print(f"Average visits per patient: {avg_visits:.2f}")
    print(f"Average injections per patient: {avg_injections:.2f}")
    print(f"Visit range: {min_visits:.0f} to {max_visits:.0f}")
    
    # Count patients by phase
    phase_counts = df.groupby(['patient_id', 'phase']).size().reset_index(name='count')
    loading_patients = phase_counts[phase_counts['phase'] == 'loading']['patient_id'].nunique()
    maintenance_patients = phase_counts[phase_counts['phase'] == 'maintenance']['patient_id'].nunique()
    
    total_patients = df['patient_id'].nunique()
    print(f"\nPhase Transitions:")
    print(f"Patients in loading phase: {loading_patients} ({loading_patients/total_patients*100:.1f}%)")
    print(f"Patients reaching maintenance phase: {maintenance_patients} ({maintenance_patients/total_patients*100:.1f}%)")
    
    # Plot visit intervals for sampled patients
    plt.figure(figsize=(12, 8))
    
    for i, patient_id in enumerate(sampled_patient_ids[:5]):  # Limit to 5 patients for clarity
        patient_data = sampled_df[sampled_df['patient_id'] == patient_id].sort_values('date')
        
        if len(patient_data) < 2:
            continue
            
        # Calculate intervals between visits
        dates = pd.to_datetime(patient_data['date'])
        intervals = [(dates.iloc[i] - dates.iloc[i-1]).days / 7 for i in range(1, len(dates))]
        
        plt.plot(range(1, len(intervals) + 1), intervals, 'o-', label=f"Patient {patient_id}")
    
    plt.xlabel('Visit Number')
    plt.ylabel('Interval (weeks)')
    plt.title('Visit Intervals for Sampled Patients')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig('des_visit_intervals.png')
    print("Saved visit interval plot to des_visit_intervals.png")
    
    # Plot vision trajectories for sampled patients
    plt.figure(figsize=(12, 8))
    
    for i, patient_id in enumerate(sampled_patient_ids[:5]):  # Limit to 5 patients for clarity
        patient_data = sampled_df[sampled_df['patient_id'] == patient_id].sort_values('date')
        
        if len(patient_data) < 2:
            continue
            
        # Extract vision values
        vision = patient_data['vision'].astype(float)
        
        plt.plot(range(len(vision)), vision, 'o-', label=f"Patient {patient_id}")
    
    plt.xlabel('Visit Number')
    plt.ylabel('Vision (ETDRS letters)')
    plt.title('Vision Trajectories for Sampled Patients')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig('des_vision_trajectories.png')
    print("Saved vision trajectories plot to des_vision_trajectories.png")

if __name__ == "__main__":
    analyze_des_patients()
