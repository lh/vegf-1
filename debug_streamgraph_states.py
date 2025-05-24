#!/usr/bin/env python3
"""
Debug script to analyze why only 4 states are visible in the streamgraph.
This script runs a simulation and logs detailed information about patient states.
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import required modules
try:
    from simulation.config import SimulationConfig
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    from streamgraph_fixed_phase_tracking import (
        generate_phase_tracking_streamgraph, 
        analyze_phase_transitions,
        determine_patient_state
    )
    from streamlit_app.data_normalizer import DataNormalizer
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

def run_simulation(population_size=100, duration_years=5):
    """Run a simulation with enhanced discontinuation settings."""
    print(f"Running simulation with {population_size} patients for {duration_years} years")
    
    # Create config with enhanced discontinuation settings
    config = SimulationConfig.from_yaml("test_simulation")
    config.num_patients = population_size
    config.duration_days = duration_years * 365
    
    # Important: Configure discontinuation with balanced probabilities for all types
    config.parameters = {
        'discontinuation': {
            'enabled': True,
            'criteria': {
                # Planned discontinuations
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.2  # Higher probability to ensure they appear
                },
                # Administrative discontinuations
                'random_administrative': {
                    'annual_probability': 0.1  # Higher probability to ensure they appear
                },
                # Not renewed discontinuations
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.15  # Higher probability to ensure they appear
                },
                # Premature discontinuations
                'premature': {
                    'min_interval_weeks': 8,
                    'probability_factor': 1.0,
                    'target_rate': 0.15
                }
            }
        }
    }
    
    # Run simulation
    print("Initializing and running simulation...")
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Process results
    results = {
        "simulation_type": "ABS",
        "population_size": population_size,
        "duration_years": duration_years,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_count": len(patient_histories)
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

    # Store retreatment stats
    if hasattr(sim, 'stats'):
        results["retreatments"] = {
            "total": sim.stats.get("retreatments", 0),
            "unique_patients": sim.stats.get("unique_retreatments", 0)
        }
    
    # Normalize data
    normalized_histories = DataNormalizer.normalize_patient_histories(patient_histories)
    results["patient_histories"] = normalized_histories
    
    return results

def analyze_patient_states(results):
    """Detailed analysis of patient states to debug visualization issues."""
    print("\n=== Patient State Analysis ===")
    
    # Extract patient histories
    patient_histories = results.get("patient_histories", {})
    if not patient_histories:
        print("Error: No patient history data in results")
        return
        
    # Count of states seen in the data
    state_counts = defaultdict(int)
    
    # Detailed analysis for first 5 patients
    sample_patients = list(patient_histories.keys())[:5]
    
    for patient_id in sample_patients:
        visits = patient_histories[patient_id]
        print(f"\nPatient {patient_id} has {len(visits)} visits")
        
        # Analyze the full patient history
        analysis = analyze_phase_transitions(visits)
        final_state = determine_patient_state(analysis)
        
        print(f"  Final state: {final_state}")
        print(f"  Has discontinued: {analysis['has_discontinued']}")
        print(f"  Has retreated: {analysis['has_retreated']}")
        print(f"  Discontinuation type: {analysis['discontinuation_type']}")
        
        # Debug phase transitions
        print(f"  Phase transitions:")
        for i, transition in enumerate(analysis['phase_transitions']):
            print(f"    {i+1}. {transition['from_phase']} → {transition['to_phase']}")
            
        # If we have explicit discontinuation info, print it
        for i, visit in enumerate(visits):
            if visit.get("is_discontinuation_visit", False):
                reason = visit.get("discontinuation_reason", "unknown")
                print(f"  Visit {i+1} has explicit discontinuation, reason: {reason}")
        
    # Now analyze all patients to get state counts
    print("\n=== Overall State Distribution ===")
    
    # Track counts at month 24 (2 years)
    month = 24
    month_state_counts = defaultdict(int)
    
    for patient_id, visits in patient_histories.items():
        # Get visits up to the target month
        visits_to_month = []
        for visit in visits:
            visit_time = visit.get("time", visit.get("date", 0))
            # Convert to months
            if isinstance(visit_time, (int, float)):
                months = visit_time / 30
                if months <= month:
                    visits_to_month.append(visit)
            else:
                # Skip datetime handling for simplicity
                visits_to_month.append(visit)
        
        # Analyze the patient's state
        analysis = analyze_phase_transitions(visits_to_month)
        state = determine_patient_state(analysis)
        
        # Count this state
        state_counts[state] += 1
        month_state_counts[state] += 1
    
    # Print counts for all states
    print(f"\nFinal state counts (all patients):")
    for state, count in sorted(state_counts.items()):
        print(f"  {state}: {count}")
    
    print(f"\nState counts at month {month}:")
    for state, count in sorted(month_state_counts.items()):
        print(f"  {state}: {count}")
    
    # Check for expected states that are missing or have zero counts
    expected_states = [
        'active',
        'active_retreated',
        'discontinued_planned',
        'discontinued_administrative',
        'discontinued_not_renewed',
        'discontinued_premature'
    ]
    
    missing_states = set(expected_states) - set(state_counts.keys())
    zero_count_states = [state for state in expected_states if state in state_counts and state_counts[state] == 0]
    
    print("\n=== State Check ===")
    if missing_states:
        print(f"Missing states (not detected at all): {missing_states}")
    else:
        print("All expected states were detected")
        
    if zero_count_states:
        print(f"Zero-count states: {zero_count_states}")
    
    # Validate discontinuation counts match aggregate stats
    disc_counts = results.get("discontinuation_counts", {})
    print("\n=== Discontinuation Stats vs State Counts ===")
    
    if disc_counts:
        print("Stats from discontinuation manager:")
        for type_name, count in disc_counts.items():
            print(f"  {type_name}: {count}")
            
        # Expected mapping to states
        map_to_state = {
            "Planned": "discontinued_planned",
            "Administrative": "discontinued_administrative",
            "Not Renewed": "discontinued_not_renewed",
            "Premature": "discontinued_premature"
        }
        
        # Check for discrepancies
        print("\nComparing with state detection:")
        total_disc_from_stats = sum(disc_counts.values())
        total_disc_from_states = sum(state_counts.get(state, 0) for state in [
            "discontinued_planned", "discontinued_administrative", 
            "discontinued_not_renewed", "discontinued_premature"
        ])
        
        print(f"Total discontinued (from stats): {total_disc_from_stats}")
        print(f"Total discontinued (from states): {total_disc_from_states}")
        
        for type_name, state_name in map_to_state.items():
            print(f"  {type_name}: {disc_counts.get(type_name, 0)} vs. {state_name}: {state_counts.get(state_name, 0)}")
    
    return state_counts

def main():
    """Run simulation and analyze results."""
    # Run a larger simulation to get more representative data
    population_size = 500
    duration_years = 5
    
    results = run_simulation(
        population_size=population_size, 
        duration_years=duration_years
    )
    
    # Print basic simulation stats
    print("\n=== Simulation Results ===")
    print(f"Population size: {results['population_size']}")
    print(f"Duration: {results['duration_years']} years")
    print(f"Patient count: {results['patient_count']}")
    
    # Discontinuation counts
    disc_counts = results.get("discontinuation_counts", {})
    if disc_counts:
        print("\nDiscontinuation counts:")
        for type_name, count in disc_counts.items():
            print(f"  {type_name}: {count}")
    
    # Retreatment stats
    retreatments = results.get("retreatments", {})
    if retreatments:
        print("\nRetreatment stats:")
        for key, value in retreatments.items():
            print(f"  {key}: {value}")
    
    # Analyze patient states
    state_counts = analyze_patient_states(results)
    
    # Generate visualization
    print("\n=== Generating Streamgraph ===")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"debug_streamgraph_states_{timestamp}.json"
    
    print(f"\nSaving simulation data to {output_file}")
    with open(output_file, "w") as f:
        json.dump(results, f, default=str)
    
    # Save visualization
    plot_file = f"debug_streamgraph_states_{timestamp}.png"
    print(f"Saving streamgraph to {plot_file}")
    fig.savefig(plot_file, dpi=300, bbox_inches="tight")
    
    # Display plot for 20 seconds
    from matplotlib.animation import FuncAnimation
    
    # Set up timer to close the figure after 20 seconds
    def close_figure(frame):
        plt.close()
    
    # Create animation to trigger closing
    ani = FuncAnimation(fig, close_figure, frames=[0], interval=20000, repeat=False)
    
    print("Showing figure (will automatically close after 20 seconds)...")
    plt.show()

if __name__ == "__main__":
    main()