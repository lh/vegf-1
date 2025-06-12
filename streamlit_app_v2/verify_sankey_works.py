#!/usr/bin/env python3
"""Verify Sankey functionality before making changes."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Load latest simulation from disk
from core.storage.registry import SimulationRegistry
from core.results.factory import ResultsFactory
from components.treatment_patterns import extract_treatment_patterns_vectorized

# Get the latest simulation
registry = SimulationRegistry(Path("simulation_results"))
entries = registry.list_simulations()

if not entries:
    print("❌ No simulations found")
    sys.exit(1)

# Load the most recent simulation
latest_entry = entries[0]  # They're sorted by date, newest first
memorable_name = latest_entry.get('memorable_name', 'No name')
print(f"Loading simulation: {latest_entry['sim_id']} ({memorable_name})")

# Load the results
results_path = Path("simulation_results") / latest_entry['sim_id']
results = ResultsFactory.load_results(results_path)

if results:
    transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
    print(f"✓ Simulation ID: {results.metadata.sim_id}")
    print(f"✓ Transitions found: {len(transitions_df)}")
    print(f"✓ Visits with states: {len(visits_df)}")
    print(f"✓ Unique states: {visits_df['treatment_state'].nunique()}")
    print(f"✓ State list: {sorted(visits_df['treatment_state'].unique())}")
    
    # Test other components
    from components.treatment_patterns.interval_analyzer import calculate_interval_statistics
    stats = calculate_interval_statistics(visits_df)
    print(f"✓ Interval stats: median={stats['median']:.1f} days")
    
    # Save reference data
    import json
    reference = {
        'sim_id': results.metadata.sim_id,
        'transition_count': len(transitions_df),
        'visit_count': len(visits_df),
        'states': sorted(visits_df['treatment_state'].unique()),
        'median_interval': stats['median']
    }
    with open('sankey_reference_data.json', 'w') as f:
        json.dump(reference, f, indent=2)
    print("✓ Reference data saved to sankey_reference_data.json")
else:
    print("❌ No simulation found")