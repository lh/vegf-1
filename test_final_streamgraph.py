"""
Test the final streamgraph implementation with reasonable data.
"""

import matplotlib.pyplot as plt
from streamlit_app.realistic_streamgraph import generate_realistic_streamgraph

# Create more reasonable test data
test_results = {
    "simulation_type": "ABS",
    "population_size": 1000,
    "duration_years": 5,
    "discontinuation_counts": {
        "Planned": 200,
        "Administrative": 50,
        "Not Renewed": 50,
        "Premature": 100
    },
    "recurrences": {
        "total": 150,  # Total retreatments less than total discontinuations
        "unique_count": 150,
        "by_type": {
            "stable_max_interval": 80,  # 40% of planned discontinuations retreat
            "random_administrative": 20,  # 40% of administrative
            "treatment_duration": 20,     # 40% of not renewed
            "premature": 30              # 30% of premature
        }
    }
}

# Generate the streamgraph
fig = generate_realistic_streamgraph(test_results)
plt.savefig('test_final_streamgraph.png', dpi=150, bbox_inches='tight')
print("Final streamgraph saved to test_final_streamgraph.png")

# Show what the data looks like
from streamlit_app.realistic_streamgraph import extract_realistic_timeline
timeline_data = extract_realistic_timeline(test_results)

# Check totals
totals = timeline_data.groupby('time_months')['count'].sum()
print(f"\nTotal patients at start: {totals.iloc[0]:.0f}")
print(f"Total patients at end: {totals.iloc[-1]:.0f}")

# Check final state breakdown
final_month = timeline_data['time_months'].max()
final_data = timeline_data[timeline_data['time_months'] == final_month]
print("\nFinal state breakdown:")
for _, row in final_data.iterrows():
    print(f"{row['state']}: {row['count']:.0f}")

plt.close(fig)