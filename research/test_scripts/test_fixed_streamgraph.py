#!/usr/bin/env python3
"""
Test script to verify the fixed streamgraph visualization without synthetic data.
"""

import json
import os
import sys
import matplotlib.pyplot as plt
import importlib

# Import the fixed module 
from streamlit_app.streamgraph_patient_states_fixed import extract_patient_states, aggregate_states_by_month, create_streamgraph

# Load test data
def load_test_data():
    """Try to load simulation results from various possible locations."""
    # Possible data file locations in order of preference
    data_files = [
        "full_streamgraph_test_data.json",
        "deep_debug_output.json",
        "streamgraph_debug_data.json",
        "output/simulation_results/latest.json"
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
    
    # Create the streamgraph using the fixed implementation
    try:
        print("\nCreating streamgraph with fixed implementation...")
        
        # Use the fixed streamgraph implementation
        fig = create_streamgraph(results)
        
        # Save the figure
        output_file = "fixed_streamgraph_test.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Streamgraph saved to {output_file}")
        
        # Try to display interactively
        try:
            plt.show()
        except:
            print("Could not display plot interactively")
        
        print("Success! Test of fixed implementation complete.")
    except Exception as e:
        import traceback
        print(f"ERROR creating streamgraph: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()