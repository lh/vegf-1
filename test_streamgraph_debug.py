"""
Debug the streamgraph to understand why states aren't changing over time.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from streamlit_app.streamgraph_patient_states import create_streamgraph, extract_patient_states, aggregate_states_by_month
import numpy as np

# Create simple test data to debug
def create_simple_test_data():
    patient_histories = {
        # Patient 1: Active throughout
        "P001": [
            {"time": 0, "is_discontinuation_visit": False},
            {"time": 30, "is_discontinuation_visit": False},
            {"time": 60, "is_discontinuation_visit": False},
            {"time": 90, "is_discontinuation_visit": False},
        ],
        
        # Patient 2: Discontinues at month 2
        "P002": [
            {"time": 0, "is_discontinuation_visit": False},
            {"time": 30, "is_discontinuation_visit": False},
            {"time": 60, "is_discontinuation_visit": True,
             "discontinuation_reason": "premature"},
        ],
        
        # Patient 3: Discontinues at month 3, retreats at month 6
        "P003": [
            {"time": 0, "is_discontinuation_visit": False},
            {"time": 30, "is_discontinuation_visit": False},
            {"time": 90, "is_discontinuation_visit": True,
             "discontinuation_reason": "stable_max_interval"},
            {"time": 180, "is_retreatment_visit": True},
            {"time": 210, "is_discontinuation_visit": False},
        ],
    }
    
    return {
        "patient_histories": patient_histories,
        "duration_years": 1
    }

# Debug the data processing
if __name__ == "__main__":
    print("Creating simple test data...")
    results = create_simple_test_data()
    
    print("\nExtracting patient states...")
    patient_states_df = extract_patient_states(results["patient_histories"])
    print("Patient states DataFrame:")
    print(patient_states_df)
    
    print("\nAggregating by month...")
    monthly_counts = aggregate_states_by_month(patient_states_df, 12)
    
    # Print counts at key months
    for month in [0, 1, 2, 3, 6, 7]:
        month_data = monthly_counts[monthly_counts['time_months'] == month]
        print(f"\nMonth {month}:")
        for _, row in month_data.iterrows():
            if row['count'] > 0:
                print(f"  {row['state']}: {row['count']}")
        total = month_data['count'].sum()
        print(f"  Total: {total}")
    
    print("\nGenerating streamgraph...")
    fig = create_streamgraph(results)
    fig.savefig("debug_streamgraph.png", dpi=150, bbox_inches='tight')
    print("Saved to debug_streamgraph.png")