#!/usr/bin/env python3
"""
Analyze simulation outcomes using patient-time (time since enrollment) rather than calendar-time.
This gives accurate per-patient year outcomes regardless of enrollment timing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements
from calibration.fixed_interval_protocol import FixedIntervalProtocol
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def analyze_patient_time_outcomes(results, protocol_name="Protocol"):
    """
    Analyze outcomes based on patient-time (time since enrollment).
    
    Returns metrics for patients who completed full years of follow-up.
    """
    print(f"\n{'='*60}")
    print(f"PATIENT-TIME ANALYSIS: {protocol_name}")
    print(f"{'='*60}")
    
    # Collect data for each patient
    year1_complete = []
    year2_complete = []
    
    for patient_id, patient in results.patient_histories.items():
        if not patient.visit_history:
            continue
            
        # Get enrollment date (first visit)
        enrollment_date = patient.visit_history[0]['date']
        baseline_vision = patient.visit_history[0]['vision']
        
        # Track metrics by patient year
        year1_injections = 0
        year1_final_vision = None
        year1_discontinued = False
        
        year2_injections = 0
        year2_final_vision = None
        year2_discontinued = False
        
        for visit in patient.visit_history:
            # Calculate months since enrollment
            months_since_enrollment = (visit['date'] - enrollment_date).days / 30.44
            
            # Year 1 (0-12 months)
            if months_since_enrollment <= 12:
                if visit['treatment_given']:
                    year1_injections += 1
                year1_final_vision = visit['vision']
                if visit.get('discontinuation_type'):
                    year1_discontinued = True
            
            # Year 2 (12-24 months)
            elif months_since_enrollment <= 24:
                if visit['treatment_given']:
                    year2_injections += 1
                year2_final_vision = visit['vision']
                if visit.get('discontinuation_type'):
                    year2_discontinued = True
        
        # Check if patient completed full years
        last_visit_months = (patient.visit_history[-1]['date'] - enrollment_date).days / 30.44
        
        if last_visit_months >= 12 and year1_final_vision is not None:
            year1_complete.append({
                'patient_id': patient_id,
                'injections': year1_injections,
                'vision_change': year1_final_vision - baseline_vision,
                'discontinued': year1_discontinued
            })
        
        if last_visit_months >= 24 and year2_final_vision is not None:
            year2_complete.append({
                'patient_id': patient_id,
                'injections': year2_injections,
                'vision_change': year2_final_vision - baseline_vision,
                'discontinued': year2_discontinued
            })
    
    # Calculate statistics
    print(f"\nPatients with complete follow-up:")
    print(f"  Year 1: {len(year1_complete)} patients")
    print(f"  Year 2: {len(year2_complete)} patients")
    
    if year1_complete:
        print(f"\nYear 1 Results (patient-time):")
        injections = [p['injections'] for p in year1_complete]
        vision_changes = [p['vision_change'] for p in year1_complete]
        discontinued = sum(p['discontinued'] for p in year1_complete)
        
        print(f"  Mean injections: {np.mean(injections):.1f}")
        print(f"  Mean vision change: {np.mean(vision_changes):.1f} letters")
        print(f"  Discontinuation rate: {discontinued/len(year1_complete)*100:.1f}%")
        
        # Injection distribution
        print(f"\n  Injection distribution:")
        unique, counts = np.unique(injections, return_counts=True)
        for inj, count in zip(unique, counts):
            print(f"    {inj} injections: {count} patients ({count/len(injections)*100:.1f}%)")
    
    if year2_complete:
        print(f"\nYear 2 Results (patient-time):")
        injections = [p['injections'] for p in year2_complete]
        vision_changes = [p['vision_change'] for p in year2_complete]
        discontinued = sum(p['discontinued'] for p in year2_complete)
        
        print(f"  Mean injections: {np.mean(injections):.1f}")
        print(f"  Mean vision change: {np.mean(vision_changes):.1f} letters")
        print(f"  Discontinuation rate: {discontinued/len(year2_complete)*100:.1f}%")
    
    return year1_complete, year2_complete


def main():
    """Test VIEW 2q8 with proper patient-time analysis."""
    print("Testing VIEW 2q8 Protocol with Patient-Time Analysis")
    
    # Load improved protocol
    spec = ProtocolSpecification.from_yaml(Path("protocols/v2/view_2q8_improved.yaml"))
    
    # Create components
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
            
            clinical_improvements = ClinicalImprovements(**config_data)
    
    print("\nRunning 3-year simulation to ensure 1 year follow-up for all patients...")
    print("(This accounts for recruitment period)")
    
    # Run longer simulation to ensure all patients get full follow-up
    engine = ABSEngineWithSpecs(
        disease_model=disease_model,
        protocol=protocol,
        protocol_spec=spec,
        n_patients=200,
        seed=42,
        clinical_improvements=clinical_improvements
    )
    
    results = engine.run(duration_years=3.0)  # 3 years to ensure 1-year follow-up
    
    # Analyze using patient-time
    year1_results, year2_results = analyze_patient_time_outcomes(results, "VIEW 2q8 Improved")
    
    # Compare to targets
    print(f"\n{'='*60}")
    print("COMPARISON TO VIEW TRIAL TARGETS")
    print(f"{'='*60}")
    
    if year1_results:
        mean_injections = np.mean([p['injections'] for p in year1_results])
        mean_vision = np.mean([p['vision_change'] for p in year1_results])
        
        print(f"\nYear 1 Comparison:")
        print(f"  Injections:")
        print(f"    Target: 7.5 (allowing for some missed visits)")
        print(f"    Theoretical: 7 (3 loading + 4 maintenance)")
        print(f"    Actual: {mean_injections:.1f}")
        print(f"  Vision change:")
        print(f"    Target: 8.4 letters")
        print(f"    Actual: {mean_vision:.1f} letters")
    
    # Test standard T&E protocol for comparison
    print(f"\n{'='*60}")
    print("Running standard Eylea T&E for comparison...")
    
    spec_te = ProtocolSpecification.from_yaml(Path("protocols/v2/eylea_treat_and_extend_v1.0.yaml"))
    disease_model_te = DiseaseModel(
        transition_probabilities=spec_te.disease_transitions,
        treatment_effect_multipliers=spec_te.treatment_effect_on_transitions
    )
    
    from simulation_v2.core.protocol import StandardProtocol
    protocol_te = StandardProtocol(
        min_interval_days=spec_te.min_interval_days,
        max_interval_days=spec_te.max_interval_days,
        extension_days=spec_te.extension_days,
        shortening_days=spec_te.shortening_days
    )
    
    engine_te = ABSEngineWithSpecs(
        disease_model=disease_model_te,
        protocol=protocol_te,
        protocol_spec=spec_te,
        n_patients=200,
        seed=42
    )
    
    results_te = engine_te.run(duration_years=3.0)
    year1_te, year2_te = analyze_patient_time_outcomes(results_te, "Eylea T&E")
    
    # Final comparison
    print(f"\n{'='*60}")
    print("PROTOCOL COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    if year1_results and year1_te:
        view_injections = np.mean([p['injections'] for p in year1_results])
        view_vision = np.mean([p['vision_change'] for p in year1_results])
        te_injections = np.mean([p['injections'] for p in year1_te])
        te_vision = np.mean([p['vision_change'] for p in year1_te])
        
        print(f"\n                    VIEW 2q8    T&E")
        print(f"Year 1 Injections:    {view_injections:.1f}      {te_injections:.1f}")
        print(f"Year 1 Vision:       {view_vision:+.1f}     {te_vision:+.1f}")


if __name__ == "__main__":
    main()