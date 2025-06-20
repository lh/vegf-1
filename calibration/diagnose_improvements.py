#!/usr/bin/env python3
"""
Diagnostic script to verify clinical improvements are being applied.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements
from simulation_v2.clinical_improvements.patient_wrapper import ImprovedPatientWrapper
from simulation_v2.core.patient import Patient
from datetime import datetime


def test_clinical_improvements():
    """Test that clinical improvements are being applied."""
    print("Testing Clinical Improvements Integration\n")
    
    # Load a test protocol
    from pathlib import Path
    protocol_path = Path("calibration/test_protocols/exploration_0.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Check if clinical improvements are in the spec
    print(f"1. Protocol has clinical_improvements: {hasattr(spec, 'clinical_improvements')}")
    if hasattr(spec, 'clinical_improvements'):
        print(f"   Enabled: {spec.clinical_improvements.get('enabled', False)}")
        print(f"   Use loading phase: {spec.clinical_improvements.get('use_loading_phase', False)}")
        print(f"   Use response-based vision: {spec.clinical_improvements.get('use_response_based_vision', False)}")
    
    # Create clinical improvements config
    if spec.clinical_improvements and spec.clinical_improvements.get('enabled'):
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
        print(f"\n2. Created ClinicalImprovements config:")
        print(f"   Loading phase: {clinical_improvements.use_loading_phase}")
        print(f"   Response-based vision: {clinical_improvements.use_response_based_vision}")
        print(f"   Response types: {clinical_improvements.response_types}")
    else:
        clinical_improvements = None
        print("\n2. No clinical improvements configured")
    
    # Test patient wrapper
    if clinical_improvements:
        print("\n3. Testing Patient Wrapper:")
        
        # Create a basic patient
        patient = Patient(
            patient_id="test_001",
            baseline_vision=55
        )
        print(f"   Basic patient baseline vision: {patient.baseline_vision}")
        
        # Wrap with improvements
        wrapped_patient = ImprovedPatientWrapper(patient, clinical_improvements)
        print(f"   Wrapped patient response type: {wrapped_patient.response_type}")
        print(f"   Loading phase enabled: {wrapped_patient.config.use_loading_phase}")
        
        # Test vision calculation
        print("\n4. Testing Vision Calculation:")
        print("   Without wrapper:")
        print(f"     Current vision: {patient.current_vision}")
        
        # Simulate a visit with the wrapper
        from simulation_v2.core.disease_model import DiseaseModel
        # Create a simple disease state
        wrapped_patient.record_visit(
            date=datetime(2024, 1, 1),
            disease_state='ACTIVE',  # Use string instead of enum
            treatment_given=True,
            vision=patient.current_vision + 3  # Simulate vision improvement
        )
        print(f"   After wrapped visit:")
        print(f"     Current vision: {wrapped_patient.current_vision}")
        print(f"     Injection count: {wrapped_patient.injection_count}")
    
    # Test engine integration
    print("\n5. Testing Engine Integration:")
    
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
        n_patients=10,
        seed=42,
        clinical_improvements=clinical_improvements
    )
    
    print(f"   Engine has clinical improvements: {engine.clinical_improvements is not None}")
    
    # Run a short simulation
    print("\n6. Running short simulation (3 months):")
    results = engine.run(duration_years=0.25)  # 3 months
    
    # Check results
    print(f"   Total patients: {len(results.patient_histories)}")
    print(f"   Total injections: {results.total_injections}")
    print(f"   Mean final vision: {results.final_vision_mean:.1f}")
    
    # Check individual patients
    print("\n7. Checking individual patients:")
    for i, (pid, patient) in enumerate(list(results.patient_histories.items())[:3]):
        print(f"\n   Patient {pid}:")
        print(f"     Baseline vision: {patient.baseline_vision}")
        print(f"     Current vision: {patient.current_vision}")
        print(f"     Vision change: {patient.current_vision - patient.baseline_vision}")
        print(f"     Injections: {patient.injection_count}")
        print(f"     Visits: {len(patient.visit_history)}")
        
        # Check if it's a wrapped patient
        if hasattr(patient, 'response_type'):
            print(f"     Response type: {patient.response_type}")
        else:
            print(f"     WARNING: Patient is not wrapped!")


if __name__ == "__main__":
    test_clinical_improvements()