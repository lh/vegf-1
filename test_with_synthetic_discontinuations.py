"""
Test the fixed streamgraph implementation using synthetic discontinuation data.
"""

import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import sys

# Import the fixed module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from streamlit_app.streamgraph_patient_states_fixed import extract_patient_states, aggregate_states_by_month, create_streamgraph

def create_test_data():
    """Create a test dataset with explicit discontinuation flags"""
    # Create a basic structure
    results = {
        "simulation_type": "ABS",
        "duration_years": 5,
        "population_size": 200,
        "discontinuation_counts": {
            "stable_max_interval": 50,
            "random_administrative": 20,
            "course_complete_but_not_renewed": 30, 
            "premature": 40
        },
        "patient_histories": {}
    }
    
    # Create patient histories with different patterns
    # Group 1: Never discontinued (50 patients)
    for i in range(1, 51):
        pid = f"ACTIVE_{i:03d}"
        
        # Regular visits every 2 months for 5 years
        visits = []
        for month in range(0, 61, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        results["patient_histories"][pid] = visits
    
    # Group 2: Planned discontinuation (50 patients)
    for i in range(1, 51):
        pid = f"PLANNED_{i:03d}"
        
        # Regular visits, then discontinuation at year 2
        visits = []
        for month in range(0, 24, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        # Add discontinuation visit
        disc_date = datetime(2023, 1, 1) + pd.DateOffset(months=24)
        visits.append({
            "time": disc_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_discontinuation_visit": True,
            "discontinuation_reason": "stable_max_interval",
            "discontinuation_type": "stable_max_interval" 
        })
        
        # Add monitoring visits
        for month in range(30, 61, 6):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        results["patient_histories"][pid] = visits
    
    # Group 3: Administrative discontinuation (20 patients)
    for i in range(1, 21):
        pid = f"ADMIN_{i:03d}"
        
        # Regular visits, then administrative discontinuation at random point
        visits = []
        disc_month = 12 + i  # Spread between months 13-32
        
        for month in range(0, disc_month, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        # Add discontinuation visit
        disc_date = datetime(2023, 1, 1) + pd.DateOffset(months=disc_month)
        visits.append({
            "time": disc_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_discontinuation_visit": True,
            "discontinuation_reason": "random_administrative",
            "discontinuation_type": "random_administrative"
        })
        
        results["patient_histories"][pid] = visits
    
    # Group 4: Treatment duration (30 patients)
    for i in range(1, 31):
        pid = f"DURATION_{i:03d}"
        
        # Regular visits for 3 years, then treatment completed
        visits = []
        for month in range(0, 36, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        # Add discontinuation visit
        disc_date = datetime(2023, 1, 1) + pd.DateOffset(months=36)
        visits.append({
            "time": disc_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_discontinuation_visit": True,
            "discontinuation_reason": "course_complete_but_not_renewed",
            "discontinuation_type": "treatment_duration"
        })
        
        results["patient_histories"][pid] = visits
    
    # Group 5: Premature discontinuation (40 patients) with some retreatments
    for i in range(1, 41):
        pid = f"PREMATURE_{i:03d}"
        
        # Regular visits, then premature discontinuation
        visits = []
        disc_month = 6 + i % 12  # Between months 6-17
        
        for month in range(0, disc_month, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        # Add discontinuation visit
        disc_date = datetime(2023, 1, 1) + pd.DateOffset(months=disc_month)
        visits.append({
            "time": disc_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_discontinuation_visit": True,
            "discontinuation_reason": "premature",
            "discontinuation_type": "premature"
        })
        
        # For half of these patients, add retreatment after 6-10 months
        if i <= 20:
            retreat_month = disc_month + 6 + i % 5
            retreat_date = datetime(2023, 1, 1) + pd.DateOffset(months=retreat_month)
            
            visits.append({
                "time": retreat_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_retreatment_visit": True,
                "is_discontinuation_visit": False
            })
            
            # Continue treatment for a while
            for month in range(retreat_month + 2, min(retreat_month + 12, 60), 2):
                visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
                visits.append({
                    "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "is_discontinuation_visit": False
                })
        
        results["patient_histories"][pid] = visits
    
    # Group 6: Retreatment from planned discontinuation (10 patients)
    for i in range(1, 11):
        pid = f"RETREAT_PLANNED_{i:03d}"
        
        # Regular visits, then planned discontinuation, then retreatment
        visits = []
        disc_month = 18
        retreat_month = 30
        
        for month in range(0, disc_month, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        # Add discontinuation visit
        disc_date = datetime(2023, 1, 1) + pd.DateOffset(months=disc_month)
        visits.append({
            "time": disc_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_discontinuation_visit": True,
            "discontinuation_reason": "stable_max_interval",
            "discontinuation_type": "stable_max_interval"
        })
        
        # Add retreatment visit
        retreat_date = datetime(2023, 1, 1) + pd.DateOffset(months=retreat_month)
        visits.append({
            "time": retreat_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_retreatment_visit": True,
            "is_discontinuation_visit": False
        })
        
        # Continue treatment
        for month in range(retreat_month + 2, 60, 2):
            visit_date = datetime(2023, 1, 1) + pd.DateOffset(months=month)
            visits.append({
                "time": visit_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "is_discontinuation_visit": False
            })
        
        results["patient_histories"][pid] = visits
    
    return results

def run_test():
    """Run a test of the fixed streamgraph implementation"""
    # Create synthetic test data
    print("Creating synthetic test data with explicit discontinuation flags...")
    results = create_test_data()
    
    # Display summary of the test data
    patient_count = len(results["patient_histories"])
    print(f"Created test data with {patient_count} patients")
    
    # Save test data for inspection
    test_data_file = "test_discontinuation_data.json"
    with open(test_data_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Test data saved to {test_data_file}")
    
    # Create streamgraph with the fixed implementation
    try:
        print("\nCreating streamgraph with fixed implementation...")
        fig = create_streamgraph(results)
        
        # Save the figure
        output_file = "test_discontinuation_streamgraph.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Fixed streamgraph saved to {output_file}")
        
        # Display interactively if possible
        try:
            plt.show()
        except Exception as e:
            print(f"Could not display plot: {e}")
        
        return True
    except Exception as e:
        print(f"Error creating streamgraph: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    if success:
        print("Success! Test of fixed implementation with synthetic data complete.")
    else:
        print("Test failed.")