#!/usr/bin/env python3
"""
Test script to validate improved phase tracking for all discontinuation types.
This script runs a simulation with forced discontinuation types and validates
that the phase transition analysis correctly identifies them.
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta

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

def create_test_visits(include_types=None):
    """
    Create a set of test visits with different discontinuation types.
    
    Parameters
    ----------
    include_types : list or None
        List of discontinuation types to include, or None for all types
        
    Returns
    -------
    dict
        Dictionary of patient visits with various discontinuation types
    """
    if include_types is None:
        include_types = ["planned", "administrative", "not_renewed", "premature"]
    
    # Base time
    base_time = datetime.now()
    
    # Create patient dictionary
    patients = {}
    
    # Patient 1: Planned discontinuation
    if "planned" in include_types:
        patients["patient_1"] = [
            {
                "time": base_time,
                "phase": "loading",
                "visit_type": "initial",
                "date": base_time
            },
            {
                "time": base_time + timedelta(weeks=4),
                "phase": "loading",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=4)
            },
            {
                "time": base_time + timedelta(weeks=8),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=8)
            },
            {
                "time": base_time + timedelta(weeks=24),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=24)
            },
            {
                "time": base_time + timedelta(weeks=48),
                "phase": "monitoring",
                "visit_type": "discontinuation",
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval",
                "cessation_type": "stable_max_interval",
                "date": base_time + timedelta(weeks=48)
            },
            {
                "time": base_time + timedelta(weeks=60),
                "phase": "monitoring",
                "visit_type": "monitoring",
                "date": base_time + timedelta(weeks=60)
            }
        ]
    
    # Patient 2: Administrative discontinuation
    if "administrative" in include_types:
        patients["patient_2"] = [
            {
                "time": base_time,
                "phase": "loading",
                "visit_type": "initial",
                "date": base_time
            },
            {
                "time": base_time + timedelta(weeks=4),
                "phase": "loading",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=4)
            },
            {
                "time": base_time + timedelta(weeks=8),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=8)
            },
            {
                "time": base_time + timedelta(weeks=24),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=24)
            },
            {
                "time": base_time + timedelta(weeks=40),
                "phase": "monitoring",
                "visit_type": "discontinuation",
                "is_discontinuation_visit": True,
                "discontinuation_reason": "random_administrative",
                "cessation_type": "random_administrative",
                "date": base_time + timedelta(weeks=40)
            }
        ]
    
    # Patient 3: Not renewed discontinuation
    if "not_renewed" in include_types:
        patients["patient_3"] = [
            {
                "time": base_time,
                "phase": "loading",
                "visit_type": "initial",
                "date": base_time
            },
            {
                "time": base_time + timedelta(weeks=4),
                "phase": "loading",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=4)
            },
            {
                "time": base_time + timedelta(weeks=8),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=8)
            },
            {
                "time": base_time + timedelta(weeks=52),
                "phase": "monitoring",
                "visit_type": "discontinuation",
                "is_discontinuation_visit": True,
                "discontinuation_reason": "course_complete_but_not_renewed",
                "cessation_type": "course_complete_but_not_renewed",
                "date": base_time + timedelta(weeks=52)
            }
        ]
    
    # Patient 4: Premature discontinuation
    if "premature" in include_types:
        patients["patient_4"] = [
            {
                "time": base_time,
                "phase": "loading",
                "visit_type": "initial",
                "date": base_time
            },
            {
                "time": base_time + timedelta(weeks=4),
                "phase": "loading",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=4)
            },
            {
                "time": base_time + timedelta(weeks=8),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=8)
            },
            {
                "time": base_time + timedelta(weeks=16),
                "phase": "monitoring",
                "visit_type": "discontinuation",
                "is_discontinuation_visit": True,
                "discontinuation_reason": "premature",
                "cessation_type": "premature",
                "date": base_time + timedelta(weeks=16)
            }
        ]
    
    # Patient 5: Retreated patient (previously discontinued for planned reason)
    if "retreated" in include_types or "planned" in include_types:
        patients["patient_5"] = [
            {
                "time": base_time,
                "phase": "loading",
                "visit_type": "initial",
                "date": base_time
            },
            {
                "time": base_time + timedelta(weeks=4),
                "phase": "loading",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=4)
            },
            {
                "time": base_time + timedelta(weeks=8),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=8)
            },
            {
                "time": base_time + timedelta(weeks=24),
                "phase": "monitoring",
                "visit_type": "discontinuation",
                "is_discontinuation_visit": True,
                "discontinuation_reason": "stable_max_interval",
                "cessation_type": "stable_max_interval",
                "date": base_time + timedelta(weeks=24)
            },
            {
                "time": base_time + timedelta(weeks=36),
                "phase": "monitoring",
                "visit_type": "monitoring",
                "date": base_time + timedelta(weeks=36),
                "disease_activity": {"fluid_detected": True}
            },
            {
                "time": base_time + timedelta(weeks=40),
                "phase": "loading",
                "visit_type": "retreatment",
                "date": base_time + timedelta(weeks=40)
            },
            {
                "time": base_time + timedelta(weeks=44),
                "phase": "loading",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=44)
            },
            {
                "time": base_time + timedelta(weeks=48),
                "phase": "maintenance",
                "visit_type": "follow_up",
                "date": base_time + timedelta(weeks=48)
            }
        ]
    
    return patients

def test_with_synthetic_data():
    """
    Test phase tracking with synthetic data for all discontinuation types.
    """
    print("=== Testing Phase Tracking with Synthetic Data ===\n")
    
    # Create test data with all discontinuation types
    patient_histories = create_test_visits()
    
    # Expected states for each patient
    expected_states = {
        "patient_1": "discontinued_planned",
        "patient_2": "discontinued_administrative",
        "patient_3": "discontinued_not_renewed",
        "patient_4": "discontinued_premature",
        "patient_5": "active_retreated"
    }
    
    # Test each patient
    for patient_id, visits in patient_histories.items():
        print(f"Testing {patient_id}...")
        
        # Analyze phase transitions
        analysis = analyze_phase_transitions(visits)
        
        # Determine patient state
        state = determine_patient_state(analysis)
        
        # Check if it matches expected state
        expected = expected_states.get(patient_id, "unknown")
        
        print(f"  Expected state: {expected}")
        print(f"  Actual state:   {state}")
        print(f"  Discontinuation type: {analysis['discontinuation_type']}")
        
        # Print detailed analysis info
        print(f"  Analysis details:")
        print(f"    Has discontinued: {analysis['has_discontinued']}")
        print(f"    Has retreated: {analysis['has_retreated']}")
        print(f"    Phase transitions: {len(analysis['phase_transitions'])}")
        
        # Print all phase transitions
        for i, transition in enumerate(analysis["phase_transitions"]):
            print(f"    Transition {i+1}: {transition['from_phase']} → {transition['to_phase']}")
        
        # Show pass/fail
        if state == expected:
            print(f"  PASS: State matches expected value")
        else:
            print(f"  FAIL: State does not match expected value")
        
        print()
    
    # Prepare data for visualization
    results = {
        "simulation_type": "TEST",
        "population_size": len(patient_histories),
        "duration_years": 5,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_count": len(patient_histories),
        "patient_histories": patient_histories
    }
    
    # Generate streamgraph
    print("Generating phase tracking streamgraph...")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save the visualization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_phase_tracking_{timestamp}.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Saved streamgraph to {output_file}\n")
    
    # Display the plot
    plt.show()

def run_test_simulation():
    """
    Run a small simulation with enhanced discontinuation settings
    to test correct identification of all discontinuation types.
    """
    print("=== Running Test Simulation ===\n")
    
    # Create config with enhanced discontinuation settings
    config = SimulationConfig.from_yaml("test_simulation")
    config.num_patients = 100
    config.duration_days = 5 * 365
    
    # Configure discontinuation with balanced probabilities for all types
    config.parameters = {
        'discontinuation': {
            'enabled': True,
            'criteria': {
                # Planned discontinuations
                'stable_max_interval': {
                    'consecutive_visits': 3,
                    'probability': 0.25  # Higher probability to ensure they appear
                },
                # Administrative discontinuations
                'random_administrative': {
                    'annual_probability': 0.1  # Higher probability to ensure they appear
                },
                # Not renewed discontinuations
                'treatment_duration': {
                    'threshold_weeks': 52,
                    'probability': 0.2  # Higher probability to ensure they appear
                },
                # Premature discontinuations
                'premature': {
                    'min_interval_weeks': 8,
                    'probability_factor': 1.0,
                    'target_rate': 0.2
                }
            }
        }
    }
    
    # Run simulation
    print("Running simulation...")
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Process results
    results = {
        "simulation_type": "ABS",
        "population_size": config.num_patients,
        "duration_years": config.duration_days / 365,
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
    
    # Normalize data
    print("Normalizing patient histories...")
    normalized_histories = DataNormalizer.normalize_patient_histories(patient_histories)
    results["patient_histories"] = normalized_histories
    
    # Analyze patient states
    analyze_simulation_results(results)
    
    # Generate visualization
    print("\nGenerating phase tracking streamgraph...")
    fig = generate_phase_tracking_streamgraph(results)
    
    # Save the visualization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_sim_phase_tracking_{timestamp}.png"
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Saved streamgraph to {output_file}\n")
    
    # Display the plot
    plt.show()

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
    
    # Count final states
    state_counts = defaultdict(int)
    for patient_id, visits in patient_histories.items():
        # Analyze the full patient history
        analysis = analyze_phase_transitions(visits)
        final_state = determine_patient_state(analysis)
        state_counts[final_state] += 1
    
    # Print state counts
    print("\nFinal patient states from phase tracking:")
    total_patients = sum(state_counts.values())
    for state, count in sorted(state_counts.items()):
        percent = (count / total_patients) * 100 if total_patients > 0 else 0
        print(f"  {state}: {count} ({percent:.1f}%)")
    
    # Compare discontinuation counts with state counts
    print("\nComparing discontinuation manager counts vs. phase analysis counts:")
    
    # Expected mapping to states
    map_to_state = {
        "Planned": "discontinued_planned",
        "Administrative": "discontinued_administrative",
        "Not Renewed": "discontinued_not_renewed",
        "Premature": "discontinued_premature"
    }
    
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

def main():
    """Run all tests."""
    # Test with synthetic data
    test_with_synthetic_data()
    
    # Run test simulation
    run_test_simulation()

if __name__ == "__main__":
    main()