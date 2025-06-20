#!/usr/bin/env python3
"""
Investigate why injection counts are so low despite reasonable intervals.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import pandas as pd
import numpy as np
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements


def investigate_injections():
    """Deep dive into injection patterns."""
    print("Investigating Low Injection Counts\n")
    
    # Load protocol
    protocol_path = Path("calibration/test_protocols/view_aligned.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    print(f"Protocol interval settings:")
    print(f"  Min interval: {spec.min_interval_days} days")
    print(f"  Max interval: {spec.max_interval_days} days")
    print(f"  Extension: {spec.extension_days} days")
    print(f"  Shortening: {spec.shortening_days} days")
    
    # Create clinical improvements
    improvements_config = spec.clinical_improvements.copy()
    improvements_config.pop('enabled', None)
    
    config_data = {
        'use_loading_phase': improvements_config.get('use_loading_phase', False),
        'use_time_based_discontinuation': improvements_config.get('use_time_based_discontinuation', False),
        'use_response_based_vision': improvements_config.get('use_response_based_vision', False),
        'use_baseline_distribution': improvements_config.get('use_baseline_distribution', False),
        'use_response_heterogeneity': improvements_config.get('use_response_heterogeneity', False)
    }
    
    if 'response_types' in improvements_config:
        config_data['response_types'] = improvements_config['response_types']
    if 'discontinuation_probabilities' in improvements_config:
        config_data['discontinuation_probabilities'] = improvements_config['discontinuation_probabilities']
        
    clinical_improvements = ClinicalImprovements(**config_data)
    
    # Create engine
    disease_model = DiseaseModel(
        transition_probabilities=spec.disease_transitions,
        treatment_effect_multipliers=spec.treatment_effect_on_transitions
    )
    protocol = StandardProtocol(
        min_interval_days=spec.min_interval_days,
        max_interval_days=spec.max_interval_days,
        extension_days=spec.extension_days,
        shortening_days=spec.shortening_days
    )
    
    engine = ABSEngineWithSpecs(
        disease_model=disease_model,
        protocol=protocol,
        protocol_spec=spec,
        n_patients=50,
        seed=42,
        clinical_improvements=clinical_improvements
    )
    
    # Run 2-year simulation
    results = engine.run(duration_years=2.0)
    
    print(f"\nSimulation Results (2 years, {len(results.patient_histories)} patients):")
    
    # Analyze each patient
    patient_details = []
    for pid, patient in results.patient_histories.items():
        visits = patient.visit_history
        injections = sum(1 for v in visits if v['treatment_given'])
        
        # Calculate actual time in study
        if visits:
            first_visit = visits[0]['date']
            last_visit = visits[-1]['date']
            months_in_study = (last_visit - first_visit).days / 30.44
        else:
            months_in_study = 0
        
        # Calculate intervals between visits
        intervals = []
        for i in range(1, len(visits)):
            interval = (visits[i]['date'] - visits[i-1]['date']).days
            intervals.append(interval)
        
        patient_details.append({
            'patient_id': pid,
            'total_visits': len(visits),
            'total_injections': injections,
            'months_in_study': months_in_study,
            'is_discontinued': patient.is_discontinued,
            'avg_interval': np.mean(intervals) if intervals else 0,
            'min_interval': min(intervals) if intervals else 0,
            'max_interval': max(intervals) if intervals else 0,
            'enrollment_month': (patient.enrollment_date - engine.patient_arrival_schedule[0][0]).days / 30.44 if hasattr(patient, 'enrollment_date') else 0
        })
    
    df = pd.DataFrame(patient_details)
    
    # Overall statistics
    print(f"\nOverall Statistics:")
    print(f"  Average visits per patient: {df['total_visits'].mean():.1f}")
    print(f"  Average injections per patient: {df['total_injections'].mean():.1f}")
    print(f"  Average months in study: {df['months_in_study'].mean():.1f}")
    print(f"  Discontinuation rate: {df['is_discontinued'].mean():.1%}")
    
    # Group by enrollment time
    print(f"\nEnrollment Pattern Analysis:")
    print(f"  Total enrollment period: {df['enrollment_month'].max():.1f} months")
    print(f"  Patients enrolled in month 0-6: {len(df[df['enrollment_month'] <= 6])}")
    print(f"  Patients enrolled in month 6-12: {len(df[(df['enrollment_month'] > 6) & (df['enrollment_month'] <= 12)])}")
    print(f"  Patients enrolled after month 12: {len(df[df['enrollment_month'] > 12])}")
    
    # Injection rate by time in study
    print(f"\nInjection Rate Analysis:")
    # Group patients by months in study
    df['study_time_group'] = pd.cut(df['months_in_study'], bins=[0, 6, 12, 18, 24], labels=['0-6mo', '6-12mo', '12-18mo', '18-24mo'])
    by_time = df.groupby('study_time_group')[['total_injections', 'months_in_study']].mean()
    print("\n  Average injections by time in study:")
    for group, data in by_time.iterrows():
        if data['months_in_study'] > 0:
            annual_rate = data['total_injections'] / data['months_in_study'] * 12
            print(f"    {group}: {data['total_injections']:.1f} injections over {data['months_in_study']:.1f} months = {annual_rate:.1f}/year")
    
    # Look at specific patient examples
    print(f"\nDetailed Patient Examples:")
    
    # Early enrollee
    early_patient = df[df['enrollment_month'] < 1].iloc[0]
    pid = early_patient['patient_id']
    patient = results.patient_histories[pid]
    print(f"\n  Early Enrollee (Patient {pid}):")
    print(f"    Enrolled: Month {early_patient['enrollment_month']:.1f}")
    print(f"    Total visits: {len(patient.visit_history)}")
    print(f"    Total injections: {patient.injection_count}")
    print(f"    Months in study: {early_patient['months_in_study']:.1f}")
    print(f"    Annual injection rate: {patient.injection_count / early_patient['months_in_study'] * 12:.1f}")
    
    # Late enrollee
    late_patients = df[df['enrollment_month'] > 12]
    if not late_patients.empty:
        late_patient = late_patients.iloc[0]
        pid = late_patient['patient_id']
        patient = results.patient_histories[pid]
        print(f"\n  Late Enrollee (Patient {pid}):")
        print(f"    Enrolled: Month {late_patient['enrollment_month']:.1f}")
        print(f"    Total visits: {len(patient.visit_history)}")
        print(f"    Total injections: {patient.injection_count}")
        print(f"    Months in study: {late_patient['months_in_study']:.1f}")
        if late_patient['months_in_study'] > 0:
            print(f"    Annual injection rate: {patient.injection_count / late_patient['months_in_study'] * 12:.1f}")
    
    # Check loading phase
    print(f"\nLoading Phase Analysis:")
    loading_counts = []
    for pid, patient in results.patient_histories.items():
        # Count injections in first 3 months
        early_injections = 0
        for visit in patient.visit_history:
            if (visit['date'] - patient.enrollment_date).days <= 90:  # First 3 months
                if visit['treatment_given']:
                    early_injections += 1
        loading_counts.append(early_injections)
    
    print(f"  Average injections in first 3 months: {np.mean(loading_counts):.1f}")
    print(f"  Expected with loading phase: 3")
    
    # Check if loading phase is working
    print(f"\nChecking if loading phase is applied:")
    sample_patient = list(results.patient_histories.values())[0]
    print(f"  Sample patient has loading phase flag: {hasattr(sample_patient, 'loading_phase_injections')}")
    if hasattr(sample_patient, 'config'):
        print(f"  Config use_loading_phase: {sample_patient.config.use_loading_phase}")


if __name__ == "__main__":
    investigate_injections()