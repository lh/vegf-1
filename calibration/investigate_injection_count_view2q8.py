#!/usr/bin/env python3
"""
Investigate why VIEW 2q8 fixed protocol is giving fewer injections than expected.
Should be exactly 7.5 injections in Year 1 (3 loading + 4.5 maintenance).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from calibration.fixed_interval_protocol import FixedIntervalProtocol
import pandas as pd
import numpy as np


def main():
    """Investigate injection patterns in VIEW 2q8 protocol."""
    print("Investigating VIEW 2q8 Injection Count\n")
    
    # Load protocol
    spec = ProtocolSpecification.from_yaml(Path("protocols/v2/view_2q8_improved.yaml"))
    
    # Create disease model
    disease_model = DiseaseModel(
        transition_probabilities=spec.disease_transitions,
        treatment_effect_multipliers=spec.treatment_effect_on_transitions
    )
    
    # Create fixed interval protocol
    loading_config = spec.to_yaml_dict().get('loading_phase', {})
    protocol = FixedIntervalProtocol(
        loading_doses=loading_config.get('doses', 3),
        loading_interval_days=loading_config.get('interval_days', 28),
        maintenance_interval_days=spec.min_interval_days
    )
    
    print(f"Protocol Configuration:")
    print(f"  Loading doses: {protocol.loading_doses}")
    print(f"  Loading interval: {protocol.loading_interval_days} days")
    print(f"  Maintenance interval: {protocol.maintenance_interval_days} days")
    print()
    
    # Create and run small simulation
    engine = ABSEngineWithSpecs(
        disease_model=disease_model,
        protocol=protocol,
        protocol_spec=spec,
        n_patients=50,
        seed=42
    )
    
    results = engine.run(duration_years=1.0)
    
    # Analyze injection patterns
    injection_counts = []
    visit_counts = []
    enrollment_months = []
    
    patient_counter = 0
    for patient_id, patient in results.patient_histories.items():
        # Count injections and visits
        injections = sum(1 for visit in patient.visit_history if visit['treatment_given'])
        visits = len(patient.visit_history)
        
        injection_counts.append(injections)
        visit_counts.append(visits)
        
        # Check enrollment timing
        if hasattr(patient, 'enrollment_date') and patient.enrollment_date:
            enrollment_date = patient.enrollment_date
        else:
            enrollment_date = patient.visit_history[0]['date'] if patient.visit_history else None
        
        if enrollment_date:
            # Calculate months from start of simulation
            sim_start = min(p.visit_history[0]['date'] for p in results.patient_histories.values() if p.visit_history)
            months_from_start = (enrollment_date - sim_start).days / 30.44
            enrollment_months.append(months_from_start)
        
        # Print first few patients in detail
        if patient_counter < 5:
            print(f"\nPatient {patient_id}:")
            print(f"  Total visits: {visits}")
            print(f"  Total injections: {injections}")
            print(f"  Discontinued: {patient.is_discontinued}")
            
            # Show visit schedule
            print("  Visit schedule:")
            for i, visit in enumerate(patient.visit_history[:10]):  # First 10 visits
                days_from_first = (visit['date'] - patient.visit_history[0]['date']).days
                print(f"    Visit {i+1}: Day {days_from_first}, "
                      f"Treated: {visit['treatment_given']}, "
                      f"Disease: {visit.get('disease_state', 'N/A')}")
        
        patient_counter += 1
    
    # Summary statistics
    print(f"\n{'='*60}")
    print("INJECTION COUNT ANALYSIS")
    print(f"{'='*60}")
    
    print(f"\nInjection Distribution:")
    unique, counts = np.unique(injection_counts, return_counts=True)
    for inj, count in zip(unique, counts):
        print(f"  {inj} injections: {count} patients ({count/len(injection_counts)*100:.1f}%)")
    
    print(f"\nStatistics:")
    print(f"  Mean injections: {np.mean(injection_counts):.2f}")
    print(f"  Median injections: {np.median(injection_counts):.1f}")
    print(f"  Min injections: {min(injection_counts)}")
    print(f"  Max injections: {max(injection_counts)}")
    
    print(f"\nVisit Statistics:")
    print(f"  Mean visits: {np.mean(visit_counts):.2f}")
    print(f"  Expected visits in Year 1:")
    print(f"    - 3 loading visits (months 0, 1, 2)")
    print(f"    - Then every 2 months: months 4, 6, 8, 10")
    print(f"    - Total: 7 visits in first year")
    
    print(f"\nEnrollment Analysis:")
    if enrollment_months:
        print(f"  Mean enrollment month: {np.mean(enrollment_months):.2f}")
        print(f"  Max enrollment month: {max(enrollment_months):.2f}")
        print(f"  Enrollment window: {max(enrollment_months):.1f} months")
    
    # Calculate expected injections based on enrollment
    print(f"\n{'='*60}")
    print("EXPECTED VS ACTUAL INJECTIONS")
    print(f"{'='*60}")
    
    print("\nFor 12-month follow-up from enrollment:")
    print("  Loading: 3 injections (months 0, 1, 2)")
    print("  Maintenance: months 4, 6, 8, 10")
    print("  Total expected: 7 injections")
    print(f"  Actual mean: {np.mean(injection_counts):.2f}")
    
    # Check if it's an enrollment window issue
    if max(enrollment_months) > 0:
        print(f"\n⚠ WARNING: Patients enrolled over {max(enrollment_months):.1f} months")
        print("  This reduces follow-up time for later enrollees")
        print("  Consider using calendar-time analysis for accurate injection counts")


if __name__ == "__main__":
    main()