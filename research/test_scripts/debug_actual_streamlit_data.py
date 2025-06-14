"""
Debug the actual data structure from Streamlit simulation results.
"""

import json
import numpy as np
from datetime import datetime, timedelta
from streamlit_app.realistic_streamgraph import extract_realistic_timeline

# Create mock simulation results that match what Streamlit produces
# Based on the user's screenshot showing 802 discontinuations and 2166 retreatments

mock_patient_histories = {}

# Create simplified patient histories for debugging
base_time = datetime(2020, 1, 1)  # Fixed start date

for i in range(100):  # 100 patients for easier debugging
    history = []
    
    # Each patient has visits over 2 years
    for week in range(0, 104, 4):  # Every 4 weeks
        visit = {
            'time': base_time + timedelta(weeks=week),  # Proper time progression
            'time_weeks': week,
            'treatment_status': {'active': True}
        }
        
        # Simulate some discontinuations
        if i < 10 and week > 52:  # 10% discontinue after 1 year
            visit['treatment_status'] = {
                'active': False,
                'discontinuation_reason': 'stable_max_interval',
                'retreated': False
            }
        
        history.append(visit)
    
    mock_patient_histories[f'patient_{i}'] = history

# Create results with this patient history
test_results = {
    "simulation_type": "ABS",
    "population_size": 100,
    "duration_years": 2,
    "discontinuation_counts": {
        "Planned": 10,
        "Administrative": 2,
        "Not Renewed": 2,
        "Premature": 5
    },
    "recurrences": {
        "total": 8,
        "by_type": {
            "stable_max_interval": 5,
            "random_administrative": 1,
            "treatment_duration": 1,
            "premature": 1
        }
    },
    "patient_histories": mock_patient_histories
}

print("Processing with patient histories...")
timeline_data = extract_realistic_timeline(test_results)

print(f"\nTimeline data shape: {timeline_data.shape}")
print("\nFirst few rows:")
print(timeline_data.head(10))

# Check if the issue is with the datetime handling
print("\nChecking time data in first patient:")
first_patient = list(mock_patient_histories.values())[0]
print(f"First visit time field: {first_patient[0].get('time')}")
print(f"Type: {type(first_patient[0].get('time'))}")

# Now let's see what happens if we have all patients at time 0
all_at_zero = timeline_data[timeline_data['time_months'] == 0]
print(f"\nPatients at month 0: {all_at_zero['count'].sum()}")

# Check if the issue is that all visits are being collapsed to month 0
unique_months = timeline_data['time_months'].unique()
print(f"\nUnique months in data: {sorted(unique_months)}")

# Group by month and sum to see pattern
monthly_totals = timeline_data.groupby('time_months')['count'].sum()
print("\nMonthly totals:")
print(monthly_totals)