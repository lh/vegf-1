#!/usr/bin/env python3
"""
Test the fixed streamgraph implementation with real simulation data.

This script connects to the Streamlit app or other simulation outputs to 
test the visualizations with real patient data.
"""

import sys
import os
import json
import glob
import matplotlib.pyplot as plt
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our fixed implementation
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fixed_streamgraph import (
    extract_patient_states, 
    aggregate_states_by_month,
    create_streamgraph,
    PATIENT_STATES
)

def find_simulation_data():
    """Find real simulation data files."""
    # List of potential locations to check
    locations = [
        "deep_debug_output.json",
        "streamlit_debug_data.json",
        "output/simulation_results/*.json",
        "output/staggered_comparison/*.json",
        "*.json"
    ]
    
    # Search for files
    potential_files = []
    for pattern in locations:
        found = glob.glob(pattern)
        potential_files.extend(found)
    
    # Filter to keep only json files larger than 100KB (likely to contain patient data)
    data_files = []
    for file_path in potential_files:
        size = os.path.getsize(file_path)
        if size > 100000:  # Larger than 100KB
            data_files.append((file_path, size))
    
    # Sort by size (largest first)
    data_files.sort(key=lambda x: x[1], reverse=True)
    
    return [path for path, _ in data_files]

def validate_patient_data(data):
    """Validate if the data contains patient histories."""
    if not isinstance(data, dict):
        return False
    
    if "patient_histories" not in data:
        return False
    
    histories = data.get("patient_histories", {})
    if not histories or not isinstance(histories, dict):
        return False
    
    # Check if we have at least one patient
    if len(histories) == 0:
        return False
    
    # Check a sample patient
    sample_patient_id = next(iter(histories))
    visits = histories[sample_patient_id]
    
    if not visits or not isinstance(visits, list):
        return False
    
    return True

def analyze_patient_data(patient_histories):
    """Analyze patient histories to understand the data structure."""
    patient_count = len(patient_histories)
    
    # Count visits and transitions
    visit_count = sum(len(visits) for visits in patient_histories.values())
    disc_count = 0
    disc_types = {}
    retreat_count = 0
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            if visit.get("is_discontinuation_visit", False):
                disc_count += 1
                disc_type = visit.get("discontinuation_reason", "unknown")
                disc_types[disc_type] = disc_types.get(disc_type, 0) + 1
            if visit.get("is_retreatment_visit", False):
                retreat_count += 1
    
    print(f"Found {patient_count} patients with {visit_count} visits")
    print(f"Discontinuations: {disc_count} by type: {disc_types}")
    print(f"Retreatments: {retreat_count}")
    
    return {
        "patient_count": patient_count,
        "visit_count": visit_count,
        "discontinuations": disc_count,
        "discontinuation_types": disc_types,
        "retreatments": retreat_count
    }

def validate_state_conservation(monthly_counts):
    """Validate population conservation in aggregated data."""
    # Check if population is conserved across months
    total_by_month = monthly_counts.groupby('time_months')['count'].sum()
    
    if len(total_by_month) == 0:
        print("No monthly data available")
        return False
    
    first_month_total = total_by_month.iloc[0]
    is_conserved = (total_by_month == first_month_total).all()
    
    print(f"Population conservation: {is_conserved}")
    print(f"Total patients: {first_month_total}")
    
    # Check for any variations
    if not is_conserved:
        min_total = total_by_month.min()
        max_total = total_by_month.max()
        print(f"Patient count varies from {min_total} to {max_total}")
        
        # Print months with incorrect counts
        for month, total in total_by_month.items():
            if total != first_month_total:
                print(f"Month {month}: {total} patients (expected: {first_month_total})")
    
    return is_conserved

def main():
    """Main test function."""
    # Find simulation data files
    data_files = find_simulation_data()
    
    if not data_files:
        print("No suitable data files found.")
        return
    
    print(f"Found {len(data_files)} potential data files:")
    for i, file_path in enumerate(data_files):
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"{i+1}. {file_path} ({size_mb:.2f} MB)")
    
    # Try each file until we find one with valid patient data
    for file_path in data_files:
        print(f"\nTrying file: {file_path}")
        
        try:
            # Load the data
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate the data structure
            if not validate_patient_data(data):
                print("File does not contain valid patient histories. Skipping.")
                continue
            
            # Analyze the patient data
            patient_histories = data.get("patient_histories", {})
            stats = analyze_patient_data(patient_histories)
            
            # If we don't have enough patients or data, try next file
            if stats["patient_count"] < 10 or stats["visit_count"] < 100:
                print("Not enough patient data. Skipping.")
                continue
            
            # Extract patient states
            print("\nProcessing data for visualization...")
            patient_states_df = extract_patient_states(patient_histories)
            
            # Check if we have state data
            if len(patient_states_df) == 0:
                print("No state data extracted. Skipping.")
                continue
            
            # Aggregate by month
            duration_years = data.get("duration_years", 5)
            duration_months = int(duration_years * 12)
            monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
            
            # Validate population conservation
            validate_state_conservation(monthly_counts)
            
            # Create streamgraph
            print("\nCreating streamgraph visualization...")
            fig = create_streamgraph(data)
            
            # Save the visualization
            output_path = Path(file_path).stem + "_streamgraph.png"
            fig.savefig(output_path, dpi=100, bbox_inches="tight")
            print(f"Saved streamgraph to {output_path}")
            
            # Show the visualization
            plt.show()
            
            # No need to check more files if we successfully visualized one
            break
            
        except Exception as e:
            print(f"Error processing file: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()