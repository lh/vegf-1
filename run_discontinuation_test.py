#!/usr/bin/env python3
"""
Run a test simulation with the fixed TreatAndExtendABS implementation.

This script runs a small test simulation with the fixed TreatAndExtendABS implementation
to verify that discontinuation flags are properly set in the visit records.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation modules
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS

def run_test_simulation(num_patients=20, duration_years=3):
    """
    Run a test simulation with the fixed TreatAndExtendABS implementation.
    
    Parameters
    ----------
    num_patients : int, optional
        Number of patients to simulate, by default 20
    duration_years : int, optional
        Duration of simulation in years, by default 3
        
    Returns
    -------
    dict
        Simulation results
    """
    print(f"Running test simulation with {num_patients} patients for {duration_years} years")
    
    # Create configuration for the simulation
    config = SimulationConfig.from_yaml("test_simulation")
    config.num_patients = num_patients
    config.duration_days = duration_years * 365
    
    # Keep existing clinical model parameters
    existing_params = config.parameters.copy() if hasattr(config, 'parameters') else {}
    
    # Add our test parameters
    config.parameters = {
        # Keep any existing clinical model parameters
        'clinical_model': existing_params.get('clinical_model', {
            'disease_states': ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE'],
            'initial_phase_transitions': {'HIGHLY_ACTIVE': 0.01},
            'transition_probabilities': {
                'NAIVE': {'NAIVE': 0.0, 'STABLE': 0.35, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.05},
                'STABLE': {'STABLE': 0.88, 'ACTIVE': 0.12, 'HIGHLY_ACTIVE': 0.0},
                'ACTIVE': {'STABLE': 0.2, 'ACTIVE': 0.75, 'HIGHLY_ACTIVE': 0.05},
                'HIGHLY_ACTIVE': {'STABLE': 0.1, 'ACTIVE': 0.3, 'HIGHLY_ACTIVE': 0.6}
            },
            'vision_change': {
                'base_change': {
                    'NAIVE': {'injection': [5, 1], 'no_injection': [0, 0.5]},
                    'STABLE': {'injection': [1, 0.5], 'no_injection': [-0.5, 0.5]},
                    'ACTIVE': {'injection': [3, 1], 'no_injection': [-2, 1]},
                    'HIGHLY_ACTIVE': {'injection': [2, 1], 'no_injection': [-3, 1]}
                },
                'time_factor': {'max_weeks': 52},
                'ceiling_factor': {'max_vision': 100},
                'measurement_noise': [0, 0.5]
            }
        }),
        
        # Add vision model parameters
        'vision_model_type': 'realistic',
        'vision_model': {
            'loading_phase': {'mean': 5.0, 'std': 2.5},
            'maintenance_phase': {'mean': 1.2, 'std': 1.5},
            'non_responder_probability': 0.15,
            'natural_decline_rate': 0.15,
            'vision_fluctuation': 1.0,
            'ceiling_vision': 85.0,
            'fluid_detection_probability': 0.3
        },
        
        # Add discontinuation parameters
        'discontinuation': {
            'enabled': True,
            'criteria': {
                # Planned discontinuations
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.8  # High probability to ensure they appear
                },
                # Administrative discontinuations
                'random_administrative': {
                    'annual_probability': 0.2  # Higher probability to ensure they appear
                },
                # Course completion
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.5
                }
            },
            # Retreatment settings
            'retreatment': {
                'probability': 0.7
            },
            # Monitoring settings
            'monitoring': {
                'visit_interval_weeks': 12,
                'cessation_types': ['stable_max_interval', 'random_administrative']
            }
        }
    }
    
    # Run simulation
    print("Initializing and running simulation...")
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Process results
    results = {
        "simulation_type": "ABS",
        "config": {
            "patient_count": num_patients,
            "duration_years": duration_years,
            "start_date": datetime.now().strftime("%Y-%m-%d")
        },
        "statistics": sim.stats,
        "patient_histories": patient_histories,
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    return results

def analyze_discontinuation_flags(results):
    """
    Analyze the simulation results to verify discontinuation flags.
    
    Parameters
    ----------
    results : dict
        Simulation results
        
    Returns
    -------
    dict
        Analysis results
    """
    print("\nAnalyzing discontinuation flags in simulation results...")
    
    # Extract patient histories
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("No patient histories found in results")
        return None
    
    # Prepare analysis results
    analysis = {
        "total_patients": len(patient_histories),
        "total_visits": 0,
        "patients_with_discontinuation_flag": 0,
        "visits_with_discontinuation_flag": 0,
        "discontinuation_types": {},
        "sample_discontinuation_visits": []
    }
    
    # Analyze each patient's history
    for patient_id, visits in patient_histories.items():
        analysis["total_visits"] += len(visits)
        
        patient_has_discontinuation = False
        
        # Check each visit for discontinuation flags
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                analysis["visits_with_discontinuation_flag"] += 1
                patient_has_discontinuation = True
                
                # Count discontinuation types
                disc_type = visit.get("discontinuation_type", "unknown")
                if disc_type not in analysis["discontinuation_types"]:
                    analysis["discontinuation_types"][disc_type] = 0
                analysis["discontinuation_types"][disc_type] += 1
                
                # Save sample discontinuation visits (up to 5)
                if len(analysis["sample_discontinuation_visits"]) < 5:
                    sample = {
                        "patient_id": patient_id,
                        "visit": visit
                    }
                    analysis["sample_discontinuation_visits"].append(sample)
        
        if patient_has_discontinuation:
            analysis["patients_with_discontinuation_flag"] += 1
    
    # Calculate percentages
    if analysis["total_patients"] > 0:
        analysis["pct_patients_with_discontinuation"] = (
            (analysis["patients_with_discontinuation_flag"] / analysis["total_patients"]) * 100
        )
    
    if analysis["total_visits"] > 0:
        analysis["pct_visits_with_discontinuation"] = (
            (analysis["visits_with_discontinuation_flag"] / analysis["total_visits"]) * 100
        )
    
    return analysis

def save_results(results, filename=None):
    """
    Save simulation results to a JSON file.
    
    Parameters
    ----------
    results : dict
        Simulation results
    filename : str, optional
        Filename to save results to, by default None
        
    Returns
    -------
    str
        Path to saved file
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(root_dir, "output", "simulation_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"discontinuation_test_{timestamp}.json"
    
    # Full path
    file_path = os.path.join(output_dir, filename)
    
    # Save the file
    try:
        with open(file_path, "w") as f:
            json.dump(results, f, default=str)
        
        print(f"\nSimulation results saved to: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

def print_analysis(analysis):
    """
    Print analysis results in a readable format.
    
    Parameters
    ----------
    analysis : dict
        Analysis results
    """
    print("\n=== Discontinuation Flag Analysis ===")
    print(f"Total patients: {analysis['total_patients']}")
    print(f"Total visits: {analysis['total_visits']}")
    print(f"Patients with discontinuation flag: {analysis['patients_with_discontinuation_flag']} "
          f"({analysis['pct_patients_with_discontinuation']:.1f}%)")
    print(f"Visits with discontinuation flag: {analysis['visits_with_discontinuation_flag']} "
          f"({analysis['pct_visits_with_discontinuation']:.1f}%)")
    
    print("\nDiscontinuation types:")
    for disc_type, count in sorted(analysis["discontinuation_types"].items(), key=lambda x: -x[1]):
        print(f"  {disc_type}: {count}")
    
    print("\nSample discontinuation visits:")
    for i, sample in enumerate(analysis["sample_discontinuation_visits"]):
        print(f"\nPatient {sample['patient_id']} - Discontinuation visit:")
        for key, value in sample["visit"].items():
            # Format the output for readability
            if key in ["actions", "baseline_vision", "vision", "date"]:
                continue
            print(f"  {key}: {value}")

def main():
    """Main function to run the test simulation and analyze the results."""
    # Run simulation
    results = run_test_simulation()
    
    # Save results
    filepath = save_results(results)
    
    # Analyze discontinuation flags
    analysis = analyze_discontinuation_flags(results)
    
    # Print analysis
    if analysis:
        print_analysis(analysis)
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()