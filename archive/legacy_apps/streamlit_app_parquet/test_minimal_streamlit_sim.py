"""
Test script that mimics what happens when you click Run Simulation in Streamlit
"""
import sys
import os
sys.path.append(os.getcwd())

# Import exactly what the Streamlit app imports
from streamlit_app_parquet.simulation_runner import run_simulation

# Create minimal parameters like the UI would
params = {
    "simulation_type": "ABS",
    "population_size": 10,
    "duration_years": 1,
    "planned_discontinue_prob": 0.2,
    "administrative_discontinue_prob": 0.05, 
    "premature_discontinue_factor": 2.0,
    "protocol": "Treat and Extend",
    "discontinuation_probability": 0.2,  # This is what the UI calls it
    "administrative_discontinuation_rate": 0.05,  # This is what the UI calls it
    "enable_retreatment": True,
    "retreatment_probability": {
        "stable_max_interval": 0.3,
        "random_administrative": 0.5,
        "course_complete": 0.2,
        "premature": 0.7
    }
}

print("Running simulation with parameters:")
for key, value in params.items():
    print(f"  {key}: {value}")

# Run the simulation
results = run_simulation(params)

print(f"\n\nSimulation completed!")
print(f"Results keys: {list(results.keys())}")

# Check for VA data
if "mean_va_data" in results:
    print(f"\n✓ mean_va_data exists with {len(results['mean_va_data'])} entries")
else:
    print("\n✗ mean_va_data is missing!")
    
if "va_data_summary" in results:
    print("\nVA data summary:")
    for key, value in results['va_data_summary'].items():
        print(f"  {key}: {value}")
        
if "visits_df" in results:
    visits_df = results["visits_df"]
    print(f"\nVisits DataFrame: {visits_df.shape}")
    print(f"Columns: {list(visits_df.columns)}")
    
    if 'vision' in visits_df.columns:
        print(f"\nVision column non-null values: {visits_df['vision'].notna().sum()}")
        
# Check if simulation failed
if results.get("failed"):
    print(f"\n❌ SIMULATION FAILED: {results.get('error')}")