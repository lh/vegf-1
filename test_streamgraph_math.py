"""
Test to verify the math in the streamgraph is correct.
"""

import pandas as pd
from streamlit_app.enhanced_streamgraph import extract_patient_states_timeline

# Create test data
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
        "total": 180,
        "unique_count": 150,
        "by_type": {
            "stable_max_interval": 120,
            "random_administrative": 20,
            "treatment_duration": 20,
            "premature": 20
        }
    }
}

# Extract timeline data
timeline_data = extract_patient_states_timeline(test_results)

# Check the math at key timepoints
print("Patient State Distribution Over Time")
print("===================================")

for month in [0, 12, 24, 36, 48, 60]:
    month_data = timeline_data[timeline_data['time_months'] == month]
    
    print(f"\nMonth {month}:")
    print("-" * 20)
    
    # Group by state type
    active = month_data[month_data['state'] == 'Active']['count'].sum()
    discontinued = month_data[month_data['state'].str.contains('Discontinued')]['count'].sum()
    retreated = month_data[month_data['state'].str.contains('Retreated')]['count'].sum()
    
    total = active + discontinued + retreated
    
    print(f"Active (never discontinued): {active}")
    print(f"Currently discontinued: {discontinued}")
    print(f"Retreated (back on treatment): {retreated}")
    print(f"Total: {total}")
    
    if total != test_results['population_size']:
        print(f"ERROR: Total ({total}) doesn't match population ({test_results['population_size']})")
    
    # Show breakdown
    if discontinued > 0 or retreated > 0:
        print("\nBreakdown:")
        for _, row in month_data.iterrows():
            if row['state'] != 'Active':
                print(f"  {row['state']}: {row['count']}")

# Final verification
print("\n\nFinal Totals (Month 60):")
print("=" * 30)
final_data = timeline_data[timeline_data['time_months'] == 60]

total_discontinued_ever = sum(test_results['discontinuation_counts'].values())
total_retreated = sum(test_results['recurrences']['by_type'].values())

print(f"Total who ever discontinued: {total_discontinued_ever}")
print(f"Total who retreated: {total_retreated}")
print(f"Expected never discontinued: {1000 - total_discontinued_ever}")
print(f"Expected currently discontinued: {total_discontinued_ever - total_retreated}")
print(f"Expected retreated: {total_retreated}")