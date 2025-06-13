#!/usr/bin/env python3
"""
Check the format of patient data in the simulation results.

This script runs a small simulation and examines the structure
of the patient history data to help debug visualization issues.
"""

import os
import sys
import json
import argparse
from pprint import pprint

# Add the project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation modules
try:
    from simulation.config import SimulationConfig
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from streamlit_app.data_normalizer import DataNormalizer
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def run_small_simulation():
    """Run a small simulation to get sample patient data."""
    print("Running a small simulation to get sample data...")
    
    # Create a SimulationConfig with discontinuations enabled
    config = SimulationConfig.from_yaml("test_simulation")
    config.num_patients = 10
    config.duration_days = 365 * 2  # 2 years
    
    # Enable discontinuation
    if not hasattr(config, 'parameters'):
        config.parameters = {}
    
    if 'discontinuation' not in config.parameters:
        config.parameters['discontinuation'] = {
            'enabled': True,
            'criteria': {
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.2
                },
                'random_administrative': {
                    'annual_probability': 0.05
                },
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.1
                },
                'premature': {
                    'min_interval_weeks': 8,
                    'probability_factor': 1.0,
                    'target_rate': 0.145
                }
            }
        }
    else:
        config.parameters['discontinuation']['enabled'] = True
    
    # Create and run simulation
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Normalize patient histories
    normalized_histories = DataNormalizer.normalize_patient_histories(patient_histories)
    
    return sim, normalized_histories

def check_patient_data(patient_histories):
    """
    Check the structure of patient data.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary of patient histories
    """
    print("\n--- Patient Data Structure Analysis ---\n")
    
    # Get total patient count
    patient_count = len(patient_histories)
    print(f"Total patients: {patient_count}")
    
    if patient_count == 0:
        print("No patient data found!")
        return
    
    # Get first patient for structure analysis
    first_patient_id = list(patient_histories.keys())[0]
    first_patient = patient_histories[first_patient_id]
    
    print(f"\nSample patient ID: {first_patient_id}")
    
    # Check data type
    if isinstance(first_patient, list):
        print("Data format: List of visits")
        check_visit_list_format(first_patient)
    elif isinstance(first_patient, dict):
        print("Data format: Patient dictionary")
        # Detailed analysis would go here
    else:
        print(f"Unexpected data format: {type(first_patient)}")
    
    # Check for discontinuations
    print("\n--- Discontinuation Analysis ---")
    
    disc_count = 0
    retreat_count = 0
    patients_with_discontinuations = set()
    patients_with_retreatments = set()
    
    for patient_id, patient_data in patient_histories.items():
        has_disc = False
        has_retreat = False
        
        if isinstance(patient_data, list):
            # Process list of visits
            for visit in patient_data:
                if visit.get("is_discontinuation_visit", False) or visit.get("discontinued", False):
                    disc_count += 1
                    has_disc = True
                    # Check for discontinuation reason
                    reason = (visit.get("discontinuation_reason") or 
                              visit.get("reason") or 
                              visit.get("discontinuation_type") or "")
                    print(f"Patient {patient_id} discontinued: {reason}")
                
                if visit.get("is_retreatment_visit", False) or visit.get("is_retreatment", False):
                    retreat_count += 1
                    has_retreat = True
        
        if has_disc:
            patients_with_discontinuations.add(patient_id)
        if has_retreat:
            patients_with_retreatments.add(patient_id)
    
    print(f"Total discontinuation events: {disc_count}")
    print(f"Patients with discontinuations: {len(patients_with_discontinuations)} ({len(patients_with_discontinuations)/patient_count*100:.1f}%)")
    print(f"Total retreatment events: {retreat_count}")
    print(f"Patients with retreatments: {len(patients_with_retreatments)} ({len(patients_with_retreatments)/patient_count*100:.1f}%)")

def check_visit_list_format(visits):
    """
    Analyze the format of a list of visits.
    
    Parameters
    ----------
    visits : list
        List of visit dictionaries
    """
    if not visits:
        print("  No visits found!")
        return
    
    visit_count = len(visits)
    print(f"  Total visits: {visit_count}")
    
    if visit_count > 0:
        print("\n  First visit structure:")
        first_visit = visits[0]
        
        # Print each field in the visit
        for key, value in first_visit.items():
            print(f"    {key}: {value} ({type(value).__name__})")
        
        # Check for discontinuation fields
        disc_fields = ["is_discontinuation_visit", "discontinued", 
                       "discontinuation_reason", "reason", "discontinuation_type"]
        
        print("\n  Discontinuation fields:")
        for field in disc_fields:
            present_count = sum(1 for v in visits if field in v)
            if present_count > 0:
                print(f"    {field}: present in {present_count}/{visit_count} visits")
                
                # Show sample values
                sample_values = list(set(v[field] for v in visits if field in v and v[field]))[:3]
                if sample_values:
                    print(f"      Sample values: {sample_values}")
        
        # Check for retreatment fields
        retreat_fields = ["is_retreatment_visit", "is_retreatment", "retreatment_count"]
        
        print("\n  Retreatment fields:")
        for field in retreat_fields:
            present_count = sum(1 for v in visits if field in v)
            if present_count > 0:
                print(f"    {field}: present in {present_count}/{visit_count} visits")
                
                # Show sample values (for non-boolean fields)
                if field != "is_retreatment_visit" and field != "is_retreatment":
                    sample_values = list(set(v[field] for v in visits if field in v and v[field]))[:3]
                    if sample_values:
                        print(f"      Sample values: {sample_values}")
    
    # Sample a discontinued visit if any
    print("\n  Sample discontinued visit:")
    for visit in visits:
        if visit.get("is_discontinuation_visit", False) or visit.get("discontinued", False):
            print("  Found discontinued visit:")
            pprint(visit)
            break
    else:
        print("  No discontinued visits found")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Check patient data format from simulation')
    parser.add_argument('--output', '-o', type=str, default="patient_data_check.json",
                        help='Output file for sample patient data')
    args = parser.parse_args()
    
    # Run simulation and get patient data
    sim, patient_histories = run_small_simulation()
    
    # Analyze the data structure
    check_patient_data(patient_histories)
    
    # Check simulation stats
    if hasattr(sim, 'stats'):
        print("\n--- Simulation Stats ---")
        print(json.dumps(sim.stats, indent=2, default=str))
    
    # Check discontinuation manager stats
    discontinuation_manager = None
    if hasattr(sim, 'get_discontinuation_manager'):
        discontinuation_manager = sim.get_discontinuation_manager()
    elif hasattr(sim, 'discontinuation_manager'):
        discontinuation_manager = sim.discontinuation_manager
    
    if discontinuation_manager and hasattr(discontinuation_manager, 'stats'):
        print("\n--- Discontinuation Manager Stats ---")
        print(json.dumps(discontinuation_manager.stats, indent=2, default=str))
    
    # Save a sample patient to file
    try:
        first_patient_id = list(patient_histories.keys())[0]
        sample_data = {
            "patient_histories": {
                first_patient_id: patient_histories[first_patient_id]
            },
            "simulation_stats": getattr(sim, 'stats', {}),
            "discontinuation_stats": getattr(discontinuation_manager, 'stats', {}) if discontinuation_manager else {}
        }
        
        with open(args.output, 'w') as f:
            json.dump(sample_data, f, indent=2, default=str)
        print(f"\nSample patient data saved to {args.output}")
    except Exception as e:
        print(f"Error saving sample data: {e}")

if __name__ == "__main__":
    main()