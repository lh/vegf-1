"""
Debug the streamgraph issue by examining actual simulation data.
"""

import json
import matplotlib.pyplot as plt
from streamlit_app.realistic_streamgraph import extract_realistic_timeline

# Create test data matching actual simulation results structure
test_results = {
    "simulation_type": "ABS",
    "population_size": 100,
    "duration_years": 2,
    "discontinuation_counts": {
        "Planned": 20,
        "Administrative": 5,
        "Not Renewed": 5,
        "Premature": 10
    },
    "recurrences": {
        "total": 15,
        "by_type": {
            "stable_max_interval": 10,
            "random_administrative": 2,
            "treatment_duration": 2,
            "premature": 1
        }
    }
}

print("Test results structure:")
print(json.dumps(test_results, indent=2))

# Test without patient histories (should use interpolated data)
timeline_data_interpolated = extract_realistic_timeline(test_results)
print("\nInterpolated timeline data shape:", timeline_data_interpolated.shape)
print("\nFirst few rows:")
print(timeline_data_interpolated.head(10))

# Check unique states
print("\nUnique states in interpolated data:")
print(timeline_data_interpolated['state'].unique())

# Check time range
print("\nTime range:")
print(f"Min: {timeline_data_interpolated['time_months'].min()}")
print(f"Max: {timeline_data_interpolated['time_months'].max()}")

# Create a simple plot to visualize the issue
import pandas as pd

# Pivot the data
pivot_data = timeline_data_interpolated.pivot_table(
    index='time_months',
    columns='state',
    values='count',
    fill_value=0
)

# Plot each state
plt.figure(figsize=(10, 6))
for column in pivot_data.columns:
    plt.plot(pivot_data.index, pivot_data[column], label=column)

plt.xlabel('Time (Months)')
plt.ylabel('Number of Patients')
plt.title('Patient States Over Time (Debug View)')
plt.legend()
plt.savefig('debug_streamgraph_states.png')
plt.close()

print("\nDebug plot saved to debug_streamgraph_states.png")

# Check what happens at month 0
month_0_data = timeline_data_interpolated[timeline_data_interpolated['time_months'] == 0]
print("\nMonth 0 data:")
print(month_0_data)

# Sum total patients at each time point
time_summary = timeline_data_interpolated.groupby('time_months')['count'].sum()
print("\nTotal patients at each time point:")
print(time_summary.head())
print("...")
print(time_summary.tail())