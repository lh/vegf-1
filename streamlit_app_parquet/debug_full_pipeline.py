"""
Comprehensive debug script to trace vision data through the entire pipeline
"""
import sys
import os
sys.path.append(os.getcwd())

from datetime import datetime
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
from streamlit_app_parquet.simulation_runner import save_results_as_parquet
import pandas as pd

print("=== STEP 1: Create and run minimal simulation ===")
# Create config with required arguments
config = SimulationConfig(
    parameters={
        "population_size": 3,
        "simulation_duration_years": 0.5,
        "discontinuation_enabled": True,
        "planned_discontinuation_prob": 0.2,
        "administrative_discontinuation_annual_prob": 0.05,
        "premature_discontinuation_factor": 2.0
    },
    protocol="treat_and_extend",
    simulation_type="ABS",
    num_patients=3,
    duration_days=int(0.5 * 365),
    random_seed=42,
    verbose=True,
    start_date=datetime.now()
)

params = {
    "simulation_type": "ABS",
    "population_size": 3,
    "duration_years": 0.5,
    "planned_discontinue_prob": 0.2,
    "administrative_discontinue_prob": 0.05,
    "premature_discontinue_factor": 2.0,
    "protocol": "Treat and Extend"
}

# Run simulation
sim = TreatAndExtendABS(config)
patient_histories = sim.run()

print(f"\nSimulation completed with {len(patient_histories)} patients")

# Check patient data structure
print("\n=== STEP 2: Check patient histories structure ===")
for patient_id, history in list(patient_histories.items())[:1]:  # Just first patient
    print(f"\nPatient {patient_id}:")
    print(f"  History length: {len(history)}")
    
    if history:
        print(f"\n  First visit:")
        first_visit = history[0]
        for key, value in first_visit.items():
            print(f"    {key}: {value}")
            
        print(f"\n  Last visit:")
        last_visit = history[-1]
        for key, value in last_visit.items():
            print(f"    {key}: {value}")

# Save to Parquet
print("\n=== STEP 3: Save to Parquet ===")
stats = sim.stats if hasattr(sim, 'stats') else {}
base_path = save_results_as_parquet(patient_histories, stats, config, params)
print(f"Saved to: {base_path}")

# Load and check visits DataFrame
print("\n=== STEP 4: Check Parquet data ===")
visits_df = pd.read_parquet(f"{base_path}_visits.parquet")
print(f"DataFrame shape: {visits_df.shape}")
print(f"Columns: {list(visits_df.columns)}")

# Check vision column specifically
print("\n=== STEP 5: Vision column analysis ===")
if 'vision' in visits_df.columns:
    print("✓ Vision column EXISTS")
    print(f"  Data type: {visits_df['vision'].dtype}")
    print(f"  Non-null count: {visits_df['vision'].notna().sum()}")
    print(f"  Null count: {visits_df['vision'].isna().sum()}")
    
    # Sample data
    print("\n  Sample vision values:")
    sample = visits_df[visits_df['vision'].notna()].head(5)
    for idx, row in sample.iterrows():
        print(f"    Patient {row['patient_id']}, Time {row['time']}: {row['vision']}")
        
    # Check if all values are the same (might indicate initialization issue)
    unique_values = visits_df['vision'].dropna().unique()
    print(f"\n  Unique vision values: {len(unique_values)}")
    if len(unique_values) < 10:
        print(f"  Values: {unique_values}")
else:
    print("✗ Vision column NOT FOUND!")
    
# Test VA processing
print("\n=== STEP 6: Test VA data processing ===")
from streamlit_app_parquet.simulation_runner import process_results

# Create a mock results dict
results = {
    "visits_df": visits_df,
    "simulation_type": "ABS",
    "population_size": 3,
    "duration_years": 0.5
}

# This should process the VA data
process_results(sim, results, patient_histories, {})

if "mean_va_data" in results:
    print("✓ mean_va_data created")
    print(f"  Length: {len(results['mean_va_data'])}")
    if results['mean_va_data']:
        print(f"  First entry: {results['mean_va_data'][0]}")
else:
    print("✗ mean_va_data NOT created")
    
if "va_data_summary" in results:
    print("\nVA data summary:")
    for key, value in results['va_data_summary'].items():
        print(f"  {key}: {value}")