#!/usr/bin/env python3
"""Quick check of disease states in the data."""

import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from core.results.factory import ResultsFactory

# Load the simulation
sim_path = Path(__file__).parent.parent / "simulation_results" / "sim_20250527_220446_bc6fdd90"
results = ResultsFactory.load_results(sim_path)

# Get visits data
visits_df = results.get_visits_df()

print("Disease states in visits:")
print(visits_df['disease_state'].value_counts())

print("\nSample transitions:")
# Look at a few patients
sample_patient = visits_df['patient_id'].iloc[0]
patient_visits = visits_df[visits_df['patient_id'] == sample_patient].sort_values('time_days')
print(f"\nPatient {sample_patient} disease state progression:")
for _, visit in patient_visits.iterrows():
    print(f"  Day {visit['time_days']:4.0f}: {visit['disease_state']}")