#!/usr/bin/env python
"""
Analyze simulation results for streamgraph visualization.

This script loads simulation results from JSON, analyzes the patient state data,
and prepares it for streamgraph visualization. It extracts the real patient state
transitions over time without using any synthetic or placeholder data.
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)


def load_simulation_results(filepath):
    """
    Load simulation results from JSON file.
    
    Parameters
    ----------
    filepath : str
        Path to simulation results JSON file
        
    Returns
    -------
    dict
        Simulation results
    """
    try:
        with open(filepath, "r") as f:
            results = json.load(f)
        
        print(f"Loaded simulation results from: {filepath}")
        print(f"Simulation type: {results.get('simulation_type', 'unknown')}")
        print(f"Patient count: {results.get('config', {}).get('patient_count', 'unknown')}")
        print(f"Duration: {results.get('config', {}).get('duration_years', 'unknown')} years")
        return results
    except Exception as e:
        print(f"Error loading simulation results: {e}")
        sys.exit(1)


def inspect_data_structure(results):
    """
    Inspect and validate the data structure in simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    dict
        Information about the data structure
    """
    print("\nInspecting data structure...")
    
    # Check if patient histories exist
    if "patient_histories" not in results:
        raise ValueError("No patient histories found in simulation results")
    
    patient_histories = results["patient_histories"]
    
    # Get first patient for structure analysis
    if isinstance(patient_histories, dict) and len(patient_histories) > 0:
        first_patient_id = next(iter(patient_histories))
        first_patient = patient_histories[first_patient_id]
    else:
        raise ValueError("Invalid patient histories format or empty patient list")
    
    # Analyze structure
    structure_info = {
        "total_patients": len(patient_histories),
        "patient_id_type": type(first_patient_id).__name__,
        "patient_type": type(first_patient).__name__,
    }
    
    # Analyze visits if present
    if isinstance(first_patient, list):
        # List of visits format
        structure_info["format"] = "list_of_visits"
        
        if len(first_patient) > 0:
            first_visit = first_patient[0]
            structure_info["visit_type"] = type(first_visit).__name__
            
            if isinstance(first_visit, dict):
                structure_info["visit_keys"] = list(first_visit.keys())
                
                # Check for state/phase information
                state_keys = [k for k in first_visit.keys() if any(
                    state_keyword in k.lower() for state_keyword in 
                    ["state", "phase", "status", "discontinue", "retreat"]
                )]
                
                structure_info["state_keys"] = state_keys
                
                # Sample visit data
                structure_info["sample_visit"] = first_visit
    elif hasattr(first_patient, "visits") and isinstance(first_patient.visits, list):
        # Object with visits attribute
        structure_info["format"] = "object_with_visits_attribute"
        
        if len(first_patient.visits) > 0:
            first_visit = first_patient.visits[0]
            structure_info["visit_type"] = type(first_visit).__name__
            
            if hasattr(first_visit, "__dict__"):
                visit_dict = first_visit.__dict__
                structure_info["visit_keys"] = list(visit_dict.keys())
                
                # Check for state/phase information
                state_keys = [k for k in visit_dict.keys() if any(
                    state_keyword in k.lower() for state_keyword in 
                    ["state", "phase", "status", "discontinue", "retreat"]
                )]
                
                structure_info["state_keys"] = state_keys
                
                # Sample visit data
                structure_info["sample_visit"] = visit_dict
    elif isinstance(first_patient, dict) and "visits" in first_patient:
        # Dictionary with visits key
        structure_info["format"] = "dict_with_visits_key"
        
        if len(first_patient["visits"]) > 0:
            first_visit = first_patient["visits"][0]
            structure_info["visit_type"] = type(first_visit).__name__
            
            if isinstance(first_visit, dict):
                structure_info["visit_keys"] = list(first_visit.keys())
                
                # Check for state/phase information
                state_keys = [k for k in first_visit.keys() if any(
                    state_keyword in k.lower() for state_keyword in 
                    ["state", "phase", "status", "discontinue", "retreat"]
                )]
                
                structure_info["state_keys"] = state_keys
                
                # Sample visit data
                structure_info["sample_visit"] = first_visit
    else:
        raise ValueError(f"Unsupported patient history format: {type(first_patient).__name__}")
    
    # Print structure information
    print(f"Data structure format: {structure_info['format']}")
    print(f"Total patients: {structure_info['total_patients']}")
    
    if "visit_keys" in structure_info:
        print(f"Visit keys: {', '.join(structure_info['visit_keys'])}")
    
    if "state_keys" in structure_info:
        print(f"Potential state keys: {', '.join(structure_info['state_keys'])}")
    
    if "sample_visit" in structure_info:
        print("\nSample visit data:")
        for k, v in structure_info["sample_visit"].items():
            print(f"  - {k}: {v}")
            
    return structure_info


def extract_patient_state_by_month(results, structure_info):
    """
    Extract patient state information by month from simulation results.
    
    Parameters
    ----------
    results : dict
        Simulation results
    structure_info : dict
        Information about the data structure
        
    Returns
    -------
    dict
        Patient state counts by month
    """
    print("\nExtracting patient state timeline data...")
    
    patient_histories = results["patient_histories"]
    duration_months = int(results.get("config", {}).get("duration_years", 5) * 12)
    
    # Initialize timeline data
    # We'll store patients in each state at each time point (month)
    state_counts = defaultdict(lambda: defaultdict(int))
    patient_states_by_month = defaultdict(lambda: defaultdict(list))
    
    # Define state categories
    state_categories = [
        "active",  # Currently receiving treatment
        "discontinued_planned",  # Stable and intentionally discontinued
        "discontinued_administrative",  # Administrative discontinuation
        "discontinued_duration",  # Treatment duration reached
        "monitoring",  # In monitoring phase after discontinuation
        "retreated"  # Retreated after discontinuation
    ]
    
    # Track total patients for conservation principle
    total_patients = len(patient_histories)
    
    # Format-specific extraction
    if structure_info["format"] == "list_of_visits":
        # Patient histories is a dict of patient_id -> list of visits
        for patient_id, visits in patient_histories.items():
            # Sort visits by time/date
            if isinstance(visits, list) and len(visits) > 0:
                # Determine sort key
                sort_key = "time"
                if "date" in visits[0]:
                    sort_key = "date"
                
                sorted_visits = sorted(visits, key=lambda v: v.get(sort_key, 0))
                
                # Track patient state over time
                current_state = "active"  # Start as active
                discontinuation_visit_index = None
                baseline_time = None
                
                for i, visit in enumerate(sorted_visits):
                    # Get visit time in months
                    if sort_key == "date" and baseline_time is None:
                        # Convert baseline_time string to datetime if needed
                        if isinstance(visit["date"], str):
                            from datetime import datetime
                            baseline_time = datetime.strptime(visit["date"], "%Y-%m-%d %H:%M:%S")
                        else:
                            baseline_time = visit["date"]
                        month = 0
                    elif sort_key == "date":
                        # Convert current time string to datetime if needed
                        if isinstance(visit["date"], str):
                            from datetime import datetime
                            current_time = datetime.strptime(visit["date"], "%Y-%m-%d %H:%M:%S")
                        else:
                            current_time = visit["date"]
                            
                        # Calculate months from baseline
                        time_diff = (current_time - baseline_time).total_seconds()
                        month = int(time_diff / (30.44 * 24 * 60 * 60))
                    else:
                        # Direct time value (assume in months)
                        month = int(visit.get("time", i))
                        
                    # Cap at simulation duration
                    if month > duration_months:
                        month = duration_months
                    
                    # Determine state from visit data
                    # Look for phase/state information
                    visit_phase = visit.get("phase", "").lower()
                    is_discontinuation = visit.get("is_discontinuation_visit", False)
                    is_retreatment = visit.get("is_retreatment_visit", False)
                    
                    # Determine state from visit data
                    if is_retreatment or "retreated" in visit_phase:
                        current_state = "retreated"
                    elif is_discontinuation:
                        # Capture discontinuation type
                        discontinuation_type = visit.get("discontinuation_type", "").lower()
                        
                        if "stable" in discontinuation_type or "planned" in discontinuation_type:
                            current_state = "discontinued_planned"
                        elif "admin" in discontinuation_type:
                            current_state = "discontinued_administrative"
                        elif "duration" in discontinuation_type:
                            current_state = "discontinued_duration"
                        else:
                            current_state = "discontinued_planned"  # Default
                            
                        # Record discontinuation visit for future reference
                        discontinuation_visit_index = i
                    elif visit_phase == "monitoring":
                        current_state = "monitoring"
                    elif discontinuation_visit_index is not None and i > discontinuation_visit_index:
                        # After discontinuation but not explicitly monitoring
                        current_state = "monitoring"
                    else:
                        current_state = "active"
                        
                    # Add patient to the appropriate state at this month
                    patient_states_by_month[month][current_state].append(patient_id)
                
                # Ensure patient has a state at every month up to duration
                last_state = current_state
                last_month = month if 'month' in locals() else 0
                
                # Fill in missing months
                for month in range(last_month + 1, duration_months + 1):
                    patient_states_by_month[month][last_state].append(patient_id)
    
    # Validate and convert to counts
    for month in range(duration_months + 1):
        month_total = 0
        
        for state in state_categories:
            patients_in_state = patient_states_by_month[month][state]
            state_counts[month][state] = len(patients_in_state)
            month_total += len(patients_in_state)
            
        # Verify conservation principle
        if month_total > 0 and month_total != total_patients:
            print(f"WARNING: Conservation principle violated at month {month}. "
                  f"Expected {total_patients}, got {month_total}")
    
    # Check overall results
    print("\nPatient state timeline extracted:")
    print(f"  - Time points: {len(state_counts)} months")
    print(f"  - State categories: {len(state_categories)}")
    
    # Print summary of states over time
    print("\nSummary of patient states over time:")
    for month in sorted(state_counts.keys()):
        if month % 12 == 0:  # Print yearly summaries
            print(f"\nMonth {month} (Year {month // 12}):")
            for state, count in state_counts[month].items():
                if count > 0:
                    print(f"  - {state}: {count} patients ({count/total_patients*100:.1f}%)")
    
    # Return count data for visualization
    return {
        "state_counts": dict(state_counts),
        "state_categories": state_categories,
        "total_patients": total_patients,
        "duration_months": duration_months
    }


def save_analysis_results(analysis_results, original_filepath):
    """
    Save analysis results to a JSON file.
    
    Parameters
    ----------
    analysis_results : dict
        Analysis results to save
    original_filepath : str
        Path to original simulation results file
        
    Returns
    -------
    str
        Path to saved file
    """
    # Create directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "output", "analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename based on original
    original_filename = os.path.basename(original_filepath)
    base_name = os.path.splitext(original_filename)[0]
    analysis_filename = f"{base_name}_analysis.json"
    
    # Full path
    filepath = os.path.join(output_dir, analysis_filename)
    
    # Save the file
    try:
        with open(filepath, "w") as f:
            json.dump(analysis_results, f, indent=2)
        print(f"\nAnalysis results saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving analysis results: {e}")
        return None


def main():
    """Main function to parse arguments and analyze simulation results."""
    parser = argparse.ArgumentParser(description="Analyze simulation results for streamgraph visualization")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to simulation results JSON file")
    
    args = parser.parse_args()
    
    # Load simulation results
    results = load_simulation_results(args.input)
    
    # Inspect data structure
    structure_info = inspect_data_structure(results)
    
    # Extract patient state timeline
    timeline_data = extract_patient_state_by_month(results, structure_info)
    
    # Combine all results
    analysis_results = {
        "data_structure": structure_info,
        "timeline_data": timeline_data,
        "original_file": args.input,
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    # Save analysis results
    save_analysis_results(analysis_results, args.input)


if __name__ == "__main__":
    main()