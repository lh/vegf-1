"""
Debug why the streamgraph is showing only active patients as a solid block.
"""

import matplotlib.pyplot as plt
from streamlit_app.realistic_streamgraph import extract_realistic_timeline, create_realistic_streamgraph

# Create test data with actual discontinuations
test_results = {
    "simulation_type": "ABS",
    "population_size": 1000,
    "duration_years": 5,
    "discontinuation_counts": {
        "Planned": 842,  # From the user's screenshot
        "Administrative": 100,
        "Not Renewed": 100,
        "Premature": 200
    },
    "recurrences": {
        "total": 2354,  # From the user's screenshot
        "unique_count": 2000,
        "by_type": {
            "stable_max_interval": 1500,
            "random_administrative": 300,
            "treatment_duration": 300,
            "premature": 254
        }
    }
}

# Extract timeline data
timeline_data = extract_realistic_timeline(test_results)

print("Timeline data shape:", timeline_data.shape)
print("\nUnique states in data:")
print(timeline_data['state'].unique())
print("\nValue counts by state:")
print(timeline_data['state'].value_counts())

# Check data at specific time points
print("\nData at month 0:")
print(timeline_data[timeline_data['time_months'] == 0])

print("\nData at month 30:")
print(timeline_data[timeline_data['time_months'] == 30])

print("\nData at month 60:")
print(timeline_data[timeline_data['time_months'] == 60])

# Let's look at the actual data being plotted
pivot_data = timeline_data.pivot_table(
    index="time_months",
    columns="state", 
    values="count",
    fill_value=0
)

print("\nPivot data shape:", pivot_data.shape)
print("\nPivot data columns:")
print(pivot_data.columns.tolist())

print("\nFirst few rows of pivot data:")
print(pivot_data.head())

# Check if the issue is with the interpolation
print("\nTotal patients at each time:")
totals = timeline_data.groupby('time_months')['count'].sum()
print(totals.head())

# Create the streamgraph to see what's happening
fig, ax = create_realistic_streamgraph(timeline_data)
plt.savefig('debug_streamgraph_output.png')
plt.close()

print("\nStreamgraph saved to debug_streamgraph_output.png")