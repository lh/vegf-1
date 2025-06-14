#!/usr/bin/env python3
"""
Test script for V2 discontinuation system.

Demonstrates the new discontinuation profile system with 6 categories
and compares outcomes between Ideal and NHS_1 profiles.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.discontinuation_profile import (
    DiscontinuationProfile, 
    create_ideal_profile, 
    create_nhs1_profile
)
from simulation_v2.engines.abs_engine_v2 import ABSEngineV2


def run_simulation_with_profile(profile: DiscontinuationProfile, n_patients: int = 100):
    """Run a simulation with a specific discontinuation profile."""
    print(f"\n{'='*60}")
    print(f"Running simulation with profile: {profile.name}")
    print(f"Description: {profile.description}")
    print(f"{'='*60}\n")
    
    # Create disease model with proper transition structure
    disease_model = DiseaseModel(
        transition_probabilities={
            'NAIVE': {
                'ACTIVE': 0.8,
                'STABLE': 0.2
            },
            'STABLE': {
                'STABLE': 0.8,
                'ACTIVE': 0.2
            },
            'ACTIVE': {
                'ACTIVE': 0.6,
                'STABLE': 0.3,
                'HIGHLY_ACTIVE': 0.1
            },
            'HIGHLY_ACTIVE': {
                'HIGHLY_ACTIVE': 0.6,
                'ACTIVE': 0.4
            }
        },
        treatment_effect_multipliers={
            'ACTIVE': {
                'STABLE': 2.0,
                'HIGHLY_ACTIVE': 0.5
            },
            'STABLE': {
                'ACTIVE': 0.5
            },
            'HIGHLY_ACTIVE': {
                'ACTIVE': 1.5
            }
        },
        seed=42
    )
    
    # Create protocol
    protocol = StandardProtocol(
        min_interval_days=28,   # 4 weeks
        max_interval_days=112,  # 16 weeks
        extension_days=14,      # 2 weeks
        shortening_days=14      # 2 weeks
    )
    
    # Create engine with profile
    engine = ABSEngineV2(
        disease_model=disease_model,
        protocol=protocol,
        n_patients=n_patients,
        seed=42,
        discontinuation_profile=profile
    )
    
    # Run for 3 years
    results = engine.run(duration_years=3.0)
    
    # Print results
    print(f"Total patients: {n_patients}")
    print(f"Total injections: {results.total_injections}")
    print(f"Average injections per patient: {results.total_injections / n_patients:.1f}")
    print(f"\nVision outcomes:")
    print(f"  Mean final vision: {results.final_vision_mean:.1f} letters")
    print(f"  Std dev: {results.final_vision_std:.1f} letters")
    
    # Print discontinuation statistics
    disc_stats = results.discontinuation_stats
    print(f"\nDiscontinuation summary:")
    print(f"  Total discontinued: {disc_stats['total']} ({disc_stats['total']/n_patients*100:.1f}%)")
    
    # Detailed breakdown
    print(f"\nDiscontinuation breakdown:")
    for disc_type in ['stable_max_interval', 'poor_response', 'premature', 
                      'system_discontinuation', 'reauthorization_failure', 'mortality']:
        count = disc_stats[disc_type]
        percent = disc_stats.get(f'{disc_type}_percent', 0)
        print(f"  {disc_type:.<30} {count:3d} ({percent:4.1f}%)")
    
    print(f"\nRetreatments: {disc_stats['retreatments']}")
    
    # Sample patient stories
    print(f"\n{'='*60}")
    print("Sample patient stories:")
    print(f"{'='*60}")
    
    # Find examples of each discontinuation type
    examples = {
        'stable_max_interval': None,
        'poor_response': None,
        'premature': None,
        'system_discontinuation': None,
        'reauthorization_failure': None,
        'mortality': None
    }
    
    for patient_id, patient in results.patient_histories.items():
        if patient.is_discontinued and patient.discontinuation_type in examples:
            if examples[patient.discontinuation_type] is None:
                examples[patient.discontinuation_type] = patient
    
    for disc_type, patient in examples.items():
        if patient:
            print(f"\n{disc_type.upper()}:")
            print(f"  Patient ID: {patient.id}")
            print(f"  Baseline vision: {patient.baseline_vision} letters")
            print(f"  Pre-discontinuation vision: {patient.pre_discontinuation_vision} letters")
            print(f"  Final vision: {patient.current_vision} letters")
            print(f"  Total injections: {patient.injection_count}")
            print(f"  Discontinuation reason: {patient.discontinuation_reason}")
            if patient.retreatment_count > 0:
                print(f"  Retreatments: {patient.retreatment_count}")
    
    return results


def main():
    """Run comparison between profiles."""
    print("V2 Discontinuation System Test")
    print("==============================")
    
    # Test with Ideal profile
    ideal_profile = create_ideal_profile()
    ideal_results = run_simulation_with_profile(ideal_profile, n_patients=200)
    
    # Test with NHS_1 profile
    nhs1_profile = create_nhs1_profile()
    nhs1_results = run_simulation_with_profile(nhs1_profile, n_patients=200)
    
    # Compare results
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    print(f"\nMean final vision:")
    print(f"  Ideal: {ideal_results.final_vision_mean:.1f} letters")
    print(f"  NHS_1: {nhs1_results.final_vision_mean:.1f} letters")
    print(f"  Difference: {ideal_results.final_vision_mean - nhs1_results.final_vision_mean:.1f} letters")
    
    print(f"\nTotal discontinuations:")
    ideal_disc = ideal_results.discontinuation_stats['total']
    nhs1_disc = nhs1_results.discontinuation_stats['total']
    print(f"  Ideal: {ideal_disc} ({ideal_disc/200*100:.1f}%)")
    print(f"  NHS_1: {nhs1_disc} ({nhs1_disc/200*100:.1f}%)")
    
    print(f"\nInjections per patient:")
    print(f"  Ideal: {ideal_results.total_injections / 200:.1f}")
    print(f"  NHS_1: {nhs1_results.total_injections / 200:.1f}")
    
    # Test loading from YAML
    print(f"\n{'='*60}")
    print("Testing YAML profile loading...")
    print(f"{'='*60}")
    
    yaml_path = Path("simulation_v2/profiles/discontinuation/nhs_1.yaml")
    if yaml_path.exists():
        loaded_profile = DiscontinuationProfile.from_yaml(yaml_path)
        print(f"\nSuccessfully loaded profile: {loaded_profile.name}")
        print(f"Categories enabled: {list(loaded_profile.categories.keys())}")
        
        # Validate
        errors = loaded_profile.validate()
        if errors:
            print(f"Validation errors: {errors}")
        else:
            print("Profile validation: PASSED")
    else:
        print(f"YAML file not found at {yaml_path}")


if __name__ == "__main__":
    main()