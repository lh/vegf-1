"""
Debug what's happening with the streamgraph in Streamlit.
This is an updated version that tests the new streamgraph_patient_states.py file.
"""

import json
import os
import matplotlib.pyplot as plt
import pandas as pd
from streamlit_app.streamgraph_patient_states import extract_patient_states, aggregate_states_by_month, create_streamgraph

# Function to load simulation results from JSON
def load_simulation_results(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading simulation results: {e}")
        return None

# Main debugging script
if __name__ == "__main__":
    # Use the latest simulation results file
    latest_results_file = "output/simulation_results/ape_simulation_ABS_20250520_101135.json"
    
    print(f"Loading simulation results from {latest_results_file}")
    results = load_simulation_results(latest_results_file)
    
    if not results:
        print("Error loading results, falling back to test data")
        # Create test data that matches what Streamlit might produce
        results = {
            "simulation_type": "ABS",
            "population_size": 1000,
            "duration_years": 5,
            "patient_histories": {
                "P001": [
                    {"time": 0, "is_discontinuation_visit": False},
                    {"time": 180, "is_discontinuation_visit": True, 
                     "discontinuation_reason": "stable_max_interval"},
                    {"time": 360, "is_retreatment_visit": True},
                    {"time": 540, "is_discontinuation_visit": True,
                     "discontinuation_reason": "premature"}
                ],
                "P002": [
                    {"time": 0, "is_discontinuation_visit": False},
                    {"time": 90, "is_discontinuation_visit": True,
                     "discontinuation_reason": "random_administrative"}
                ]
            }
        }
    
    # Basic details
    print(f"Simulation duration: {results.get('duration_years', 5)} years")
    print(f"Population size: {results.get('population_size', 0)}")
    
    # Check patient_histories
    if "patient_histories" not in results or not results["patient_histories"]:
        print("ERROR: No patient_histories found in results!")
        # Try to find an alternative patient data structure
        if "patient_data" in results:
            print("Found 'patient_data' instead, using that")
            results["patient_histories"] = results["patient_data"]
    
    patient_histories = results.get("patient_histories", {})
    print(f"Found {len(patient_histories)} patient histories")
    
    # For validation, inspect a sample patient
    if patient_histories:
        sample_id = next(iter(patient_histories))
        sample_patient = patient_histories[sample_id]
        print(f"\nSample patient {sample_id} has {len(sample_patient)} visits")
        
        # Analyze visit structure
        visit_keys = set()
        discontinuation_reasons = set()
        has_discontinuation_visits = False
        has_retreatment_visits = False
        
        for visit in sample_patient:
            visit_keys.update(visit.keys())
            if visit.get('is_discontinuation_visit', False):
                has_discontinuation_visits = True
                reason = visit.get('discontinuation_reason', 'unknown')
                discontinuation_reasons.add(reason)
            if visit.get('is_retreatment_visit', False):
                has_retreatment_visits = True
        
        print(f"Visit keys found: {sorted(list(visit_keys))}")
        print(f"Has discontinuation visits: {has_discontinuation_visits}")
        print(f"Discontinuation reasons found: {discontinuation_reasons}")
        print(f"Has retreatment visits: {has_retreatment_visits}")
        
        # Print first few visits to verify structure
        print("\nFirst 3 visits:")
        for i, visit in enumerate(sample_patient[:3]):
            print(f"Visit {i}: {visit}")
    
    # Step 1: Extract patient states
    print("\nStep 1: Extracting patient states")
    try:
        # Extract patient states
        patient_states_df = extract_patient_states(patient_histories)
        print(f"Extracted {len(patient_states_df)} patient state records")
        print("\nSample states:")
        print(patient_states_df.head())
        
        # Verify all expected states are present
        print("\nState value counts:")
        print(patient_states_df['state'].value_counts())
        
    except Exception as e:
        print(f"Error in step 1: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
    
    # Step 2: Aggregate states by month
    print("\nStep 2: Aggregating states by month")
    try:
        duration_years = results.get("duration_years", 5)
        duration_months = int(duration_years * 12)
        print(f"Simulation duration: {duration_years} years ({duration_months} months)")
        
        monthly_counts = aggregate_states_by_month(patient_states_df, duration_months)
        print(f"Generated {len(monthly_counts)} monthly count records")
        print("\nSample monthly counts:")
        print(monthly_counts.head())
        
        # Verify time range
        time_range = monthly_counts['time_months'].unique()
        print(f"\nTime range: {min(time_range)} to {max(time_range)} months")
        
        # Verify patient count conservation
        for month in range(0, duration_months + 1, duration_months // 5):  # Check a few months
            month_data = monthly_counts[monthly_counts['time_months'] == month]
            total_patients = month_data['count'].sum()
            print(f"Month {month}: {total_patients} total patients")
        
        # Check final state distribution
        final_month = max(time_range)
        final_data = monthly_counts[monthly_counts['time_months'] == final_month]
        print("\nFinal month state distribution:")
        for _, row in final_data.iterrows():
            print(f"{row['state']}: {row['count']:.0f}")
        
    except Exception as e:
        print(f"Error in step 2: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
    
    # Step 3: Create and display streamgraph
    print("\nStep 3: Creating streamgraph")
    try:
        fig = create_streamgraph(results)
        print("Streamgraph created successfully")
        
        # Save the figure for inspection
        output_file = "debug_streamgraph_output.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Streamgraph saved to {output_file}")
        
        # Display interactively if possible
        try:
            plt.show()
        except:
            pass
        
    except Exception as e:
        print(f"Error in step 3: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)