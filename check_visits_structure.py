#!/usr/bin/env python3
"""Check the structure of visits dataframe."""
from pathlib import Path
from ape.core.results.factory import ResultsFactory

results_dir = Path("simulation_results")
super_pine = None
for sim in results_dir.glob("*super-pine*"):
    if sim.is_dir():
        super_pine = sim
        break

if super_pine:
    results = ResultsFactory.load_results(super_pine)
    visits_df = results.get_visits_df()
    print("Visits dataframe columns:")
    print(visits_df.columns.tolist())
    print(f"\nShape: {visits_df.shape}")
    print(f"\nFirst few rows:")
    print(visits_df.head())