#!/usr/bin/env python3
"""
Investigate why patients aren't receiving treatment at visits.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements


def investigate_treatment_logic():
    """Deep dive into treatment decision logic."""
    print("Investigating Treatment Decision Logic\n")
    
    # Load protocol
    protocol_path = Path("calibration/test_protocols/view_aligned.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create components
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
    
    # Run short simulation
    engine = ABSEngineWithSpecs(
        disease_model=disease_model,
        protocol=protocol,
        protocol_spec=spec,
        n_patients=10,
        seed=42,
        clinical_improvements=clinical_improvements
    )
    
    results = engine.run(duration_years=1.0)
    
    # Analyze treatment decisions for first few patients
    print("Analyzing Treatment Decisions:\n")
    
    for i, (pid, patient) in enumerate(list(results.patient_histories.items())[:3]):
        print(f"Patient {pid}:")
        print(f"  Baseline vision: {patient.baseline_vision}")
        print(f"  Response type: {getattr(patient, 'response_type', 'unknown')}")
        print(f"  Total visits: {len(patient.visit_history)}")
        print(f"  Total injections: {patient.injection_count}")
        
        print(f"\n  Visit details:")
        for j, visit in enumerate(patient.visit_history[:5]):  # First 5 visits
            days_since_enrollment = (visit['date'] - patient.enrollment_date).days
            
            # Get disease state name
            disease_state = visit.get('disease_state', 'unknown')
            if hasattr(disease_state, 'name'):
                disease_state = disease_state.name
            
            print(f"    Visit {j+1} (Day {days_since_enrollment}):")
            print(f"      Disease state: {disease_state}")
            print(f"      Vision: {visit['vision']}")
            print(f"      Treatment given: {visit['treatment_given']}")
            
            # Check protocol logic
            if j > 0:
                days_since_last_injection = days_since_enrollment
                for prev_visit in patient.visit_history[:j]:
                    if prev_visit['treatment_given']:
                        days_since_last_injection = days_since_enrollment - (prev_visit['date'] - patient.enrollment_date).days
                print(f"      Days since last injection: {days_since_last_injection}")
        
        print()
    
    # Check the protocol's should_treat logic
    print("\nChecking Protocol Logic:")
    print(f"Protocol type: {spec.protocol_type}")
    
    # Test the protocol's should_treat method directly
    print("\nTesting protocol.should_treat() directly:")
    
    # Create a test patient
    from simulation_v2.core.patient import Patient
    from datetime import datetime
    test_patient = Patient("test", baseline_vision=70)
    
    # Add some visit history
    test_patient.record_visit(
        date=datetime(2024, 1, 1),
        disease_state='ACTIVE',
        treatment_given=True,
        vision=70
    )
    
    # Test at different time points
    test_dates = [
        datetime(2024, 1, 29),  # 28 days later (min interval)
        datetime(2024, 2, 26),  # 56 days later
        datetime(2024, 3, 25),  # 84 days later
        datetime(2024, 4, 22),  # 112 days later (max interval)
    ]
    
    for test_date in test_dates:
        should_treat = protocol.should_treat(test_patient, test_date)
        days_since = (test_date - datetime(2024, 1, 1)).days
        print(f"  {days_since} days after injection: should_treat = {should_treat}")
    
    # Check if it's a treat-and-extend issue
    print("\nProtocol is treat-and-extend. Key insight:")
    print("In T&E, treatment decision depends on disease activity, not just time!")
    print("If disease is STABLE, intervals are extended.")
    print("If disease is ACTIVE/HIGHLY_ACTIVE, patient should be treated.")


if __name__ == "__main__":
    investigate_treatment_logic()