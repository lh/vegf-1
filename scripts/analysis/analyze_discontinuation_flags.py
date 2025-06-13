#!/usr/bin/env python3
"""
Script to analyze patient visit data in a simulation output file to check for discontinuation flags.
Identifies if discontinuation flags and types are properly set in the visit records.
"""

import os
import sys
import json
import pandas as pd
import argparse
from collections import defaultdict

def load_simulation_data(file_path):
    """
    Load simulation data from a JSON file.
    
    Parameters
    ----------
    file_path : str
        Path to simulation data JSON file
        
    Returns
    -------
    dict
        Simulation results dictionary
    """
    print(f"Loading data from: {file_path}")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def analyze_visit_data(results):
    """
    Analyze visit data to check for discontinuation flags.
    
    Parameters
    ----------
    results : dict
        Simulation results dictionary
        
    Returns
    -------
    dict
        Analysis results
    """
    # Extract patient histories
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("Error: No patient history data found")
        return {}
    
    print(f"Found {len(patient_histories)} patient histories")
    
    # Prepare analysis stats
    analysis = {
        "total_patients": len(patient_histories),
        "total_visits": 0,
        "discontinuation_flags": {
            "visits_with_flag": 0,
            "patients_with_flag": 0,
            "missing_type": 0
        },
        "discontinuation_types": defaultdict(int),
        "phase_info": {
            "visits_with_phase": 0,
            "unique_phases": set()
        },
        "states": defaultdict(int),
        "patient_examples": {}
    }
    
    # Sample patients for detailed examination
    sample_patients = list(patient_histories.keys())[:5]
    
    # Analyze each patient's visits
    patients_with_disc_flag = set()
    
    for patient_id, visits in patient_histories.items():
        analysis["total_visits"] += len(visits)
        
        # Track patient-level info
        patient_info = {
            "has_discontinuation_flag": False,
            "discontinuation_types": set(),
            "phases": set(),
            "visit_count": len(visits)
        }
        
        # Examine each visit
        for visit in visits:
            # Check for discontinuation flag
            is_discontinuation = visit.get("is_discontinuation_visit", False)
            if is_discontinuation:
                analysis["discontinuation_flags"]["visits_with_flag"] += 1
                patients_with_disc_flag.add(patient_id)
                patient_info["has_discontinuation_flag"] = True
                
                # Check discontinuation type
                disc_type = visit.get("discontinuation_type", "missing")
                if disc_type == "missing":
                    analysis["discontinuation_flags"]["missing_type"] += 1
                else:
                    analysis["discontinuation_types"][disc_type] += 1
                    patient_info["discontinuation_types"].add(disc_type)
            
            # Check for phase info
            phase = visit.get("phase", None)
            if phase:
                analysis["phase_info"]["visits_with_phase"] += 1
                analysis["phase_info"]["unique_phases"].add(phase)
                patient_info["phases"].add(phase)
            
            # Analyze potential state based on visit data
            state = determine_state(visit)
            analysis["states"][state] += 1
        
        # Save detailed info for sample patients
        if patient_id in sample_patients:
            analysis["patient_examples"][patient_id] = {
                "visits": visits,
                "info": patient_info
            }
    
    analysis["discontinuation_flags"]["patients_with_flag"] = len(patients_with_disc_flag)
    analysis["phase_info"]["unique_phases"] = list(analysis["phase_info"]["unique_phases"])
    
    return analysis

def determine_state(visit):
    """
    Determine the patient state from a single visit record.
    This replicates the logic used in the streamgraph visualization.
    
    Parameters
    ----------
    visit : dict
        Visit record
        
    Returns
    -------
    str
        Patient state
    """
    if visit.get("is_retreatment_visit", False):
        return "retreated"
    elif visit.get("is_discontinuation_visit", False):
        # Get discontinuation type
        disc_type = visit.get("discontinuation_type", "").lower()
        if "stable" in disc_type or "planned" in disc_type or "max_interval" in disc_type:
            return "discontinued_planned"
        elif "admin" in disc_type:
            return "discontinued_administrative"
        elif "duration" in disc_type or "course" in disc_type:
            return "discontinued_duration"
        else:
            return "discontinued_planned"  # Default
    elif visit.get("phase", "").lower() == "monitoring":
        return "monitoring"
    else:
        return "active"

def print_analysis(analysis):
    """
    Print analysis results in a readable format.
    
    Parameters
    ----------
    analysis : dict
        Analysis results
    """
    print("\n=== Visit Data Analysis ===")
    print(f"Total patients: {analysis['total_patients']}")
    print(f"Total visits: {analysis['total_visits']}")
    
    # Discontinuation flags
    print("\n--- Discontinuation Flags ---")
    print(f"Visits with discontinuation flag: {analysis['discontinuation_flags']['visits_with_flag']}")
    print(f"Patients with discontinuation flag: {analysis['discontinuation_flags']['patients_with_flag']} " +
          f"({analysis['discontinuation_flags']['patients_with_flag']/analysis['total_patients']*100:.1f}%)")
    print(f"Visits missing discontinuation type: {analysis['discontinuation_flags']['missing_type']}")
    
    # Discontinuation types
    if analysis['discontinuation_types']:
        print("\n--- Discontinuation Types ---")
        for disc_type, count in sorted(analysis['discontinuation_types'].items(), key=lambda x: -x[1]):
            print(f"  {disc_type}: {count}")
    
    # Phase info
    print("\n--- Phase Information ---")
    print(f"Visits with phase information: {analysis['phase_info']['visits_with_phase']}")
    print(f"Unique phases found: {', '.join(analysis['phase_info']['unique_phases'])}")
    
    # State distribution
    print("\n--- State Distribution ---")
    for state, count in sorted(analysis['states'].items(), key=lambda x: -x[1]):
        print(f"  {state}: {count} ({count/analysis['total_visits']*100:.1f}%)")
    
    # Sample patient examples
    print("\n=== Sample Patient Analysis ===")
    for patient_id, data in analysis["patient_examples"].items():
        info = data["info"]
        print(f"\nPatient {patient_id}:")
        print(f"  Visits: {info['visit_count']}")
        print(f"  Has discontinuation flag: {info['has_discontinuation_flag']}")
        if info["discontinuation_types"]:
            print(f"  Discontinuation types: {', '.join(info['discontinuation_types'])}")
        if info["phases"]:
            print(f"  Phases: {', '.join(info['phases'])}")
        
        # Print first and last visits
        visits = data["visits"]
        if visits:
            print("\n  First visit:")
            for key, value in visits[0].items():
                print(f"    {key}: {value}")
            
            if len(visits) > 1:
                print("\n  Last visit:")
                for key, value in visits[-1].items():
                    print(f"    {key}: {value}")
    
    # Check if discontinuation flags are present but not being used in visualization
    print("\n=== Flag Usage Analysis ===")
    if analysis['discontinuation_flags']['visits_with_flag'] > 0:
        print("✅ Discontinuation flags are present in the data")
        
        # Check if discontinued states are being detected
        disc_states_count = sum(count for state, count in analysis['states'].items() 
                            if state.startswith('discontinued_'))
        
        if disc_states_count == 0:
            print("❌ No discontinued states detected despite discontinuation flags being present")
            print("   This indicates the visualization is not correctly using the discontinuation flags")
        else:
            print(f"✅ Discontinued states are being detected ({disc_states_count} instances)")
    else:
        print("❌ No discontinuation flags found in any visits")
        print("   This is likely the root cause of why only active patients are shown in the visualization")

def main():
    parser = argparse.ArgumentParser(description="Analyze simulation output for discontinuation flags")
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Path to simulation JSON output file")
    args = parser.parse_args()
    
    # Load data
    results = load_simulation_data(args.input)
    
    # Analyze data
    analysis = analyze_visit_data(results)
    
    # Print results
    print_analysis(analysis)
    
    # Save analysis to file
    output_file = os.path.splitext(args.input)[0] + "_flag_analysis.json"
    print(f"\nSaving analysis to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(analysis, f, default=str)

if __name__ == "__main__":
    main()