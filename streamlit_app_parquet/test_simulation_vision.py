"""
Test script to run a small simulation and check vision data recording
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
import pandas as pd

# Create a minimal config
config = SimulationConfig()
config.population_size = 5  # Small for testing
config.simulation_duration_years = 1
config.discontinuation_enabled = True

# Create parameters
params = {
    "simulation_type": "ABS",
    "population_size": 5,
    "duration_years": 1,
    "planned_discontinue_prob": 0.2,
    "administrative_discontinue_prob": 0.05,
    "premature_discontinue_factor": 2.0,
    "protocol": "Treat and Extend"
}

# Run simulation
print("Running test simulation...")
sim = TreatAndExtendABS(config)
patient_histories = sim.run()

print(f"\nSimulation completed with {len(patient_histories)} patients")

# Check what's in patient histories
for i, (patient_id, history) in enumerate(patient_histories.items()):
    print(f"\nPatient {patient_id}:")
    print(f"  History type: {type(history)}")
    print(f"  Number of visits: {len(history)}")
    
    if history and len(history) > 0:
        first_visit = history[0]
        print(f"  First visit type: {type(first_visit)}")
        if isinstance(first_visit, dict):
            print(f"  First visit keys: {list(first_visit.keys())}")
            
            # Check for vision-related fields
            vision_fields = [k for k in first_visit.keys() if 'vision' in k.lower() or 'va' in k.lower() or 'acuity' in k.lower()]
            print(f"  Vision-related fields: {vision_fields}")
            
            if 'vision' in first_visit:
                print(f"  Vision value in first visit: {first_visit['vision']}")
            elif 'visual_acuity' in first_visit:
                print(f"  Visual acuity in first visit: {first_visit['visual_acuity']}")
            else:
                print("  No vision/visual_acuity field found!")
    
    if i >= 2:  # Just check first 3 patients
        break

# Now check what gets saved to Parquet
from streamlit_app_parquet.simulation_runner import save_results_as_parquet

print("\n\nTesting Parquet save...")
stats = sim.stats if hasattr(sim, 'stats') else {}
base_path = save_results_as_parquet(patient_histories, stats, config, params)
print(f"Saved to: {base_path}")

# Load and check the visits DataFrame
visits_df = pd.read_parquet(f"{base_path}_visits.parquet")
print(f"\nVisits DataFrame shape: {visits_df.shape}")
print(f"Columns: {list(visits_df.columns)}")

if 'vision' in visits_df.columns:
    print(f"\nVision column stats:")
    print(f"  Non-null: {visits_df['vision'].notna().sum()}")
    print(f"  Null: {visits_df['vision'].isna().sum()}")
    print(f"  Sample values: {visits_df['vision'].dropna().head()}")
else:
    print("\nNO VISION COLUMN FOUND IN VISITS DATAFRAME!")