#!/usr/bin/env python3
"""Debug script to understand simulation data structure for streamgraph."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
from core.results.parquet import ParquetResults

# Find a recent simulation
sim_dir = Path("simulation_results")
recent_sims = sorted([d for d in sim_dir.iterdir() if d.is_dir() and d.name.startswith("sim_")], 
                     key=lambda x: x.name, reverse=True)

if recent_sims:
    sim_path = recent_sims[0]
    print(f"Loading simulation: {sim_path.name}")
    
    # Load the simulation
    results = ParquetResults.load(sim_path)
    
    # Load patient data
    patients_df = pd.read_parquet(sim_path / 'patients.parquet')
    visits_df = pd.read_parquet(sim_path / 'visits.parquet')
    
    print("\n=== PATIENTS DATAFRAME ===")
    print(f"Shape: {patients_df.shape}")
    print(f"Columns: {list(patients_df.columns)}")
    print("\nFirst 5 rows:")
    print(patients_df.head())
    
    print("\n=== DISCONTINUATION INFO ===")
    # Check discontinuation status
    disc_count = patients_df['discontinued'].sum()
    print(f"Total discontinued: {disc_count}/{len(patients_df)}")
    
    # Check what discontinuation fields exist
    disc_fields = [col for col in patients_df.columns if 'discontinu' in col.lower()]
    print(f"Discontinuation fields: {disc_fields}")
    
    # If discontinuation_type exists, check values
    if 'discontinuation_type' in patients_df.columns:
        print("\nDiscontinuation types:")
        print(patients_df['discontinuation_type'].value_counts())
    
    # Check for retreatment info
    retreat_fields = [col for col in patients_df.columns if 'retreat' in col.lower()]
    print(f"\nRetreatment fields: {retreat_fields}")
    
    if 'retreatment_count' in patients_df.columns:
        print("\nRetreatment counts:")
        print(patients_df['retreatment_count'].value_counts())
    
    print("\n=== VISITS DATAFRAME ===")
    print(f"Shape: {visits_df.shape}")
    print(f"Columns: {list(visits_df.columns)}")
    
    # Check for visit-level discontinuation info
    if 'is_discontinuation_visit' in visits_df.columns:
        disc_visits = visits_df['is_discontinuation_visit'].sum()
        print(f"\nDiscontinuation visits: {disc_visits}")
    
    # Check summary statistics
    stats = results.get_summary_statistics()
    print("\n=== SUMMARY STATISTICS ===")
    print(f"Patient count: {stats.get('patient_count', 0)}")
    print(f"Discontinuation stats: {stats.get('discontinuation_stats', {})}")
    
    # Check how patient states change over time
    print("\n=== PATIENT STATE EVOLUTION ===")
    # Sample a few patients who discontinued
    disc_patients = patients_df[patients_df['discontinued'] == True].head(3)
    for _, patient in disc_patients.iterrows():
        pid = patient['patient_id']
        patient_visits = visits_df[visits_df['patient_id'] == pid].sort_values('time_days')
        print(f"\nPatient {pid}:")
        print(f"  Discontinued: {patient['discontinued']}")
        print(f"  Discontinuation time: {patient.get('discontinuation_time', 'N/A')}")
        print(f"  Visit count: {len(patient_visits)}")
        if len(patient_visits) > 0:
            print(f"  First visit: {patient_visits.iloc[0]['time_days']} days")
            print(f"  Last visit: {patient_visits.iloc[-1]['time_days']} days")