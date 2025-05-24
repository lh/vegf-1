#!/usr/bin/env python3
"""
Test the actual data streamgraph visualization without synthetic data.
"""

import json
import os
import sys
import matplotlib.pyplot as plt
import importlib

# Import our actual data streamgraph module
import streamlit_app.actual_data_streamgraph
importlib.reload(streamlit_app.actual_data_streamgraph)
from streamlit_app.actual_data_streamgraph import visualize_patient_flow

# Load test data
def load_test_data():
    """Try to load simulation results from various possible locations."""
    # Possible data file locations in order of preference
    data_files = [
        "deep_debug_output.json",
        "streamgraph_debug_data.json"
    ]
    
    # Also try to find the most recent simulation file
    simulations_dir = "output/simulation_results"
    if os.path.exists(simulations_dir):
        sim_files = [
            os.path.join(simulations_dir, f) 
            for f in os.listdir(simulations_dir) 
            if f.endswith('.json')
        ]
        
        if sim_files:
            sim_files.sort(key=os.path.getmtime, reverse=True)
            data_files.insert(0, sim_files[0])
    
    # Try each file in order
    for file_path in data_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"Successfully loaded data from {file_path}")
                return data
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return None

def main():
    """Main test function."""
    # Load test data
    results = load_test_data()
    
    if not results:
        print("ERROR: Could not load any test data.")
        return
    
    # Check for patient histories
    if "patient_histories" not in results or not results["patient_histories"]:
        print("ERROR: No patient histories available in test data.")
        return
    
    # Print basic data info
    patient_count = len(results.get("patient_histories", {}))
    duration_years = results.get("duration_years", 5)
    print(f"Test data: {patient_count} patients, {duration_years} years")
    
    # Verify discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        print("Discontinuation counts:")
        for reason, count in disc_counts.items():
            print(f"  {reason}: {count}")
        print(f"  Total: {sum(disc_counts.values())}")
    
    # Verify retreatment counts
    recurrences = results.get("recurrences", {})
    if recurrences:
        print(f"Retreatments: {recurrences.get('total', 0)}")
    
    # Create the streamgraph using actual patient data
    try:
        print("\nCreating streamgraph with ACTUAL patient data...")
        # Add debugging to understand the data 
        patient_histories = results.get("patient_histories", {})
        print(f"Found {len(patient_histories)} patients")
        
        # Check the first patient
        sample_id = list(patient_histories.keys())[0]
        sample_patient = patient_histories[sample_id]
        print(f"Sample patient {sample_id} data type: {type(sample_patient)}")
        
        if isinstance(sample_patient, list):
            print(f"Patient has {len(sample_patient)} visits")
            if sample_patient:
                print(f"First visit keys: {list(sample_patient[0].keys())}")
        elif isinstance(sample_patient, dict):
            print(f"Patient keys: {list(sample_patient.keys())}")
            if "visits" in sample_patient:
                print(f"Patient has {len(sample_patient['visits'])} visits")
                if sample_patient["visits"]:
                    print(f"First visit keys: {list(sample_patient['visits'][0].keys())}")
                    
        # Create a debug version of the timeline data
        timeline_data = streamlit_app.actual_data_streamgraph.extract_patient_data(patient_histories)
        print(f"Generated timeline with {len(timeline_data)} records")
        
        # Check if we have data for multiple time points
        time_points = timeline_data["time_months"].unique()
        print(f"Time points: {sorted(time_points)[:10]}...")
        if len(time_points) <= 1:
            print("ERROR: Only found data for one time point!")
            
        # Create the visualization
        fig = visualize_patient_flow(results)
        
        # Save the figure
        output_file = "actual_data_streamgraph_test.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Streamgraph saved to {output_file}")
        print(f"View the visualization by opening: {output_file}")
        
        # Don't show the figure automatically to avoid blocking the script
        # plt.show()
    except Exception as e:
        import traceback
        print(f"ERROR creating streamgraph: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()