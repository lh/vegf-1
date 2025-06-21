#!/usr/bin/env python3
"""
Test the balanced VIEW 2q8 protocol with patient-time analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from analyze_patient_time_outcomes import analyze_patient_time_outcomes
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements
from calibration.fixed_interval_protocol import FixedIntervalProtocol
import numpy as np


def test_protocol(protocol_path, protocol_name, n_patients=500, simulation_years=3.0):
    """Test a protocol and return patient-time results."""
    
    spec = ProtocolSpecification.from_yaml(Path(protocol_path))
    
    disease_model = DiseaseModel(
        transition_probabilities=spec.disease_transitions,
        treatment_effect_multipliers=spec.treatment_effect_on_transitions
    )
    
    loading_config = spec.to_yaml_dict().get('loading_phase', {})
    protocol = FixedIntervalProtocol(
        loading_doses=loading_config.get('doses', 3),
        loading_interval_days=loading_config.get('interval_days', 28),
        maintenance_interval_days=spec.min_interval_days
    )
    
    # Setup clinical improvements
    clinical_improvements = None
    if hasattr(spec, 'clinical_improvements') and spec.clinical_improvements:
        improvements_config = spec.clinical_improvements
        if improvements_config.get('enabled', False):
            config_data = {
                'use_loading_phase': improvements_config.get('use_loading_phase', False),
                'use_time_based_discontinuation': improvements_config.get('use_time_based_discontinuation', False),
                'use_response_based_vision': improvements_config.get('use_response_based_vision', False),
                'use_baseline_distribution': improvements_config.get('use_baseline_distribution', False),
                'use_response_heterogeneity': improvements_config.get('use_response_heterogeneity', False)
            }
            
            if 'response_types' in improvements_config:
                config_data['response_types'] = improvements_config['response_types']
            if 'vision_response_params' in improvements_config:
                config_data['vision_response_params'] = improvements_config['vision_response_params']
            
            clinical_improvements = ClinicalImprovements(**config_data)
    
    engine = ABSEngineWithSpecs(
        disease_model=disease_model,
        protocol=protocol,
        protocol_spec=spec,
        n_patients=n_patients,
        seed=42,
        clinical_improvements=clinical_improvements
    )
    
    print(f"\nRunning {protocol_name} simulation with {n_patients} patients for {simulation_years} years...")
    results = engine.run(duration_years=simulation_years)
    
    year1_results, year2_results = analyze_patient_time_outcomes(results, protocol_name)
    
    return year1_results, year2_results


def main():
    """Test all VIEW 2q8 protocol versions."""
    print("Testing VIEW 2q8 Protocol Versions")
    print("="*60)
    
    # Test all three versions
    protocols = [
        ("protocols/v2/view_2q8.yaml", "Original VIEW 2q8"),
        ("protocols/v2/view_2q8_improved.yaml", "Improved VIEW 2q8"),
        ("protocols/v2/view_2q8_balanced.yaml", "Balanced VIEW 2q8")
    ]
    
    results_summary = []
    
    for protocol_path, protocol_name in protocols:
        year1, year2 = test_protocol(protocol_path, protocol_name)
        
        if year1:
            mean_injections = np.mean([p['injections'] for p in year1])
            mean_vision = np.mean([p['vision_change'] for p in year1])
            results_summary.append({
                'name': protocol_name,
                'injections': mean_injections,
                'vision': mean_vision,
                'n_patients': len(year1)
            })
    
    # Summary comparison
    print(f"\n{'='*60}")
    print("SUMMARY COMPARISON")
    print(f"{'='*60}")
    print(f"\nProtocol               Injections  Vision   Patients")
    print("-" * 52)
    
    for result in results_summary:
        print(f"{result['name']:<22} {result['injections']:>5.1f}    {result['vision']:>+6.1f}    {result['n_patients']:>4}")
    
    print(f"\nTARGET (VIEW trials):      7.5     +8.4")
    
    # Find best match
    print(f"\n{'='*60}")
    print("CALIBRATION ASSESSMENT")
    print(f"{'='*60}")
    
    for result in results_summary:
        vision_error = abs(result['vision'] - 8.4)
        injection_error = abs(result['injections'] - 7.5)
        
        print(f"\n{result['name']}:")
        print(f"  Vision error: {vision_error:.1f} letters")
        print(f"  Injection error: {injection_error:.1f}")
        print(f"  Combined error: {vision_error + injection_error:.1f}")
        
        if vision_error < 1.0 and injection_error < 1.0:
            print("  ✓ Meets calibration targets!")
        else:
            if result['vision'] > 9.4:
                print("  → Vision too high, reduce vision parameters")
            elif result['vision'] < 7.4:
                print("  → Vision too low, increase vision parameters")


if __name__ == "__main__":
    main()