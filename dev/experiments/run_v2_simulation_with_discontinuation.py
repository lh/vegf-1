#!/usr/bin/env python3
"""
Run a simulation using the V2 discontinuation system to get realistic patient pathways.
"""

import sys
from pathlib import Path
import yaml

sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.core.discontinuation_profile import DiscontinuationProfile
from simulation_v2.engines.abs_engine_v2 import ABSEngineV2
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from streamlit_app_v2.core.results.factory import ResultsFactory


def run_simulation_with_discontinuation():
    """Run simulation with proper V2 discontinuation handling."""
    
    # Load discontinuation profile - use NHS realistic for variety
    profile_path = Path(__file__).parent.parent.parent / 'simulation_v2' / 'profiles' / 'discontinuation' / 'nhs_1.yaml'
    print(f"Loading discontinuation profile from: {profile_path}")
    
    discontinuation_profile = DiscontinuationProfile.from_yaml(str(profile_path))
    print(f"Profile loaded: {discontinuation_profile.name}")
    
    # Create protocol - use standard Eylea TAT
    protocol_config = {
        'name': 'Eylea Treat and Extend',
        'initial_interval_weeks': 4,
        'loading_doses': 3,
        'min_interval_weeks': 4,
        'max_interval_weeks': 16,
        'extension_weeks': 2,
        'reduction_weeks': 2,
        'stable_criteria': {
            'consecutive_visits': 2,
            'no_disease_activity': True
        }
    }
    
    protocol = StandardProtocol(protocol_config)
    
    # Create disease model
    disease_model = DiseaseModel()
    
    # Initialize engine with discontinuation profile
    engine = ABSEngineV2(
        protocol=protocol,
        disease_model=disease_model,
        discontinuation_profile=discontinuation_profile
    )
    
    # Run simulation
    print("\nRunning simulation...")
    print("- Patients: 1000")
    print("- Duration: 5 years") 
    print("- Discontinuation profile: NHS realistic")
    
    results = engine.run(
        n_patients=1000,
        simulation_months=60,  # 5 years
        n_iterations=1,
        show_progress=True
    )
    
    # Get the first (only) iteration results
    raw_results = results[0]
    
    # Create results using factory
    print("\nSaving results...")
    sim_results = ResultsFactory.create_results(
        raw_results=raw_results,
        protocol_name=protocol_config['name'],
        protocol_version='2.0',
        engine_type='abs_v2',
        n_patients=1000,
        duration_years=5.0,
        seed=42,
        runtime_seconds=0.0
    )
    
    print(f"\nSimulation complete!")
    print(f"Results saved to: {sim_results.metadata.sim_id}")
    
    # Quick analysis of discontinuation types
    if hasattr(sim_results, 'get_discontinuation_summary'):
        disc_summary = sim_results.get_discontinuation_summary()
        print("\nDiscontinuation summary:")
        for disc_type, count in disc_summary.items():
            print(f"  {disc_type}: {count}")
    
    return sim_results


if __name__ == "__main__":
    run_simulation_with_discontinuation()