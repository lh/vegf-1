#!/usr/bin/env python3
"""
Run a large-scale simulation to test the improved phase tracking.
This script runs a simulation with 500 patients over 5 years and
analyzes the resulting patient states using the updated phase tracking code.
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import required modules
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS
from streamgraph_fixed_phase_tracking import (
    generate_phase_tracking_streamgraph,
    analyze_phase_transitions,
    determine_patient_state
)
from streamlit_app.data_normalizer import DataNormalizer

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run large-scale phase tracking test.")
    parser.add_argument("--population", type=int, default=500,
                        help="Number of patients to simulate (default: 500)")
    parser.add_argument("--years", type=int, default=5,
                        help="Duration in years (default: 5)")
    parser.add_argument("--output", type=str, default="large_scale_test_results.json",
                        help="Output file for simulation results (default: large_scale_test_results.json)")
    return parser.parse_args()

def run_simulation(population_size=500, duration_years=5, output_file="large_scale_test_results.json"):
    """Run a large-scale simulation with enhanced discontinuation settings."""
    print(f"Running simulation with {population_size} patients for {duration_years} years")
    
    start_time = time.time()
    
    # Create config for simulation - use the test_simulation.yaml as a base
    config = SimulationConfig.from_yaml("test_simulation")
    
    # Update simulation parameters
    config.num_patients = population_size
    config.duration_days = duration_years * 365
    
    # Configure discontinuation parameters to ensure all types
    config.parameters = {
        'discontinuation': {
            'enabled': True,
            'criteria': {
                # Planned discontinuations
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.3  # Higher probability to ensure they appear
                },
                # Administrative discontinuations
                'random_administrative': {
                    'annual_probability': 0.05  # Some administrative discontinuations
                },
                # Not renewed discontinuations
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.2  # Patients who complete course but don't renew
                },
                # Premature discontinuations
                'premature': {
                    'min_interval_weeks': 8,
                    'probability_factor': 0.8,
                    'target_rate': 0.2
                }
            },
            # Monitoring schedule configuration
            'monitoring': {
                'follow_up_schedule': [8, 16, 24, 36, 48]
            },
            # Recurrence models by cessation type
            'recurrence': {
                'planned': {
                    'cumulative_rates': {
                        'year_1': 0.207,  # 20.7% at 1 year
                        'year_3': 0.739,  # 73.9% at 3 years
                        'year_5': 0.880   # 88.0% at 5 years
                    }
                }
            }
        }
    }
    
    # Run simulation
    print("Initializing and running simulation...")
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    elapsed_time = time.time() - start_time
    print(f"Simulation completed in {elapsed_time:.2f} seconds")
    
    # Process results
    results = {
        "simulation_type": "ABS",
        "population_size": population_size,
        "duration_years": duration_years,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_count": len(patient_histories),
        "elapsed_time": elapsed_time
    }
    
    # Store discontinuation stats
    if hasattr(sim, 'discontinuation_manager'):
        dm = sim.discontinuation_manager
        if hasattr(dm, 'stats'):
            stats = dm.stats
            
            # Save both raw stats and aggregated counts
            results["raw_discontinuation_stats"] = stats
            
            # Extract counts by type
            results["discontinuation_counts"] = {
                "Planned": stats.get("stable_max_interval_discontinuations", 0),
                "Administrative": stats.get("random_administrative_discontinuations", 0),
                "Not Renewed": (
                    stats.get("course_complete_but_not_renewed_discontinuations", 0) + 
                    stats.get("treatment_duration_discontinuations", 0)
                ),
                "Premature": stats.get("premature_discontinuations", 0)
            }
            
            # Print discontinuation stats
            print("\nDiscontinuation counts from manager:")
            total_disc = sum(results["discontinuation_counts"].values())
            for type_name, count in results["discontinuation_counts"].items():
                percent = (count / total_disc) * 100 if total_disc > 0 else 0
                print(f"  {type_name}: {count} ({percent:.1f}%)")
    
    # Store retreatment stats
    if hasattr(sim, 'stats'):
        results["retreatments"] = {
            "total": sim.stats.get("retreatments", 0),
            "unique_patients": sim.stats.get("unique_retreatments", 0)
        }
    
    # Normalize data
    print("\nNormalizing patient histories...")
    normalized_histories = DataNormalizer.normalize_patient_histories(patient_histories)
    results["patient_histories"] = normalized_histories
    
    # Save results to file
    print(f"Saving results to {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, default=str)
    
    return results

def analyze_simulation_results(results):
    """Analyze the simulation results and count discontinuation types."""
    print("\n=== Analyzing Simulation Results ===\n")
    
    # Get discontinuation counts from manager
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        print("Discontinuation counts from manager:")
        total_disc = sum(disc_counts.values())
        for type_name, count in disc_counts.items():
            percent = (count / total_disc) * 100 if total_disc > 0 else 0
            print(f"  {type_name}: {count} ({percent:.1f}%)")
    
    # Count patient states using our phase tracking logic
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("No patient histories found")
        return
    
    # Check state distribution at month 60 (5 years)
    month = 60
    print(f"\nAnalyzing patient states at month {month}:")
    
    # Find the earliest visit date to use as reference
    all_dates = []
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            date_val = visit.get("date", visit.get("time"))
            if date_val and isinstance(date_val, (datetime, str, pd.Timestamp)):
                all_dates.append(date_val)
                break
    
    # Get reference date
    if all_dates:
        if isinstance(all_dates[0], str):
            try:
                start_date = datetime.fromisoformat(all_dates[0].replace(" ", "T"))
            except ValueError:
                start_date = pd.to_datetime(all_dates[0])
        else:
            start_date = all_dates[0]
    else:
        start_date = datetime.now()
    
    # Count states at each month
    month_cutoff = start_date + timedelta(days=month*30)
    state_counts = defaultdict(int)
    
    # Process each patient
    for patient_id, visits in patient_histories.items():
        # Get visits up to the current month
        visits_to_month = []
        for visit in visits:
            visit_date = visit.get("date", visit.get("time"))
            
            # Convert to datetime if needed
            if isinstance(visit_date, str):
                try:
                    visit_date = datetime.fromisoformat(visit_date.replace(" ", "T"))
                except ValueError:
                    visit_date = pd.to_datetime(visit_date)
            elif isinstance(visit_date, (int, float)):
                visit_date = start_date + timedelta(days=visit_date)
            
            if visit_date <= month_cutoff:
                visits_to_month.append(visit)
        
        # Analyze the patient's phase transitions
        analysis = analyze_phase_transitions(visits_to_month)
        
        # Determine patient state
        state = determine_patient_state(analysis)
        
        # Count this patient's state
        state_counts[state] += 1
    
    # Print state counts
    print(f"States detected in visualization at month {month}:")
    for state, count in sorted(state_counts.items()):
        print(f"  {state}: {count}")
    
    # Compare discontinuation counts with state counts
    print("\nComparing discontinuation manager counts vs. phase analysis counts:")
    
    # Expected mapping to states
    map_to_state = {
        "Planned": "discontinued_planned",
        "Administrative": "discontinued_administrative",
        "Not Renewed": "discontinued_not_renewed",
        "Premature": "discontinued_premature"
    }
    
    total_discontinued_manager = sum(disc_counts.values())
    total_discontinued_states = sum(state_counts.get(state, 0) for state in [
        "discontinued_planned", "discontinued_administrative", 
        "discontinued_not_renewed", "discontinued_premature"
    ])
    
    print(f"Total discontinued (from manager): {total_discontinued_manager}")
    print(f"Total discontinued (from states): {total_discontinued_states}")
    
    for type_name, state_name in map_to_state.items():
        manager_count = disc_counts.get(type_name, 0)
        state_count = state_counts.get(state_name, 0)
        
        print(f"  {type_name}:")
        print(f"    Manager count: {manager_count}")
        print(f"    State count:   {state_count}")
        
        if manager_count == state_count:
            print(f"    MATCH")
        else:
            difference = abs(manager_count - state_count)
            percent_diff = (difference / max(1, manager_count)) * 100
            print(f"    MISMATCH: Difference of {difference} ({percent_diff:.1f}%)")
    
    return state_counts

def main():
    """Run a large-scale simulation and analyze the results."""
    # Parse command-line arguments
    args = parse_args()
    
    # Run simulation
    results = run_simulation(
        population_size=args.population,
        duration_years=args.years,
        output_file=args.output
    )
    
    # Analyze results
    state_counts = analyze_simulation_results(results)
    
    # Generate visualization
    print("\nGenerating phase tracking streamgraph...")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save the visualization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"large_scale_phase_tracking_{timestamp}.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Saved streamgraph to {output_file}\n")
    
    # Display the plot
    plt.show()

if __name__ == "__main__":
    main()