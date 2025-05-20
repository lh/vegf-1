"""
Test script to verify that the streamgraph visualization works with the new patient state flags.

This script runs a small simulation and generates a streamgraph to visualize
patient states, which should now correctly display discontinuations and retreatments.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import simulation modules
from simulation.abs import AgentBasedSimulation
from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager

# Import visualization module
import streamlit_app.streamgraph_patient_states as streamgraph

def run_test_simulation():
    """Run a small test simulation with discontinuations and retreatments."""
    # Create a simple configuration with high discontinuation probability
    config_dict = {
        'simulation': {
            'start_date': '2025-01-01',
            'duration_days': 365,
            'num_patients': 20,
            'random_seed': 42
        },
        'parameters': {
            'discontinuation': {
                'enabled': True,
                'criteria': {
                    'stable_max_interval': {
                        'consecutive_visits': 3,
                        'probability': 0.7,  # High probability for testing
                        'interval_weeks': 16
                    },
                    'random_administrative': {
                        'annual_probability': 0.1
                    },
                    'treatment_duration': {
                        'probability': 0.0
                    },
                    'premature': {
                        'probability_factor': 0.0
                    }
                },
                'monitoring': {
                    'cessation_types': {
                        'stable_max_interval': 'planned',
                        'premature': 'unplanned',
                        'treatment_duration': 'unplanned',
                        'random_administrative': 'none'
                    },
                    'planned': {
                        'follow_up_schedule': [12, 24, 36]
                    },
                    'unplanned': {
                        'follow_up_schedule': [8, 16, 24]
                    },
                    'recurrence_detection_probability': 0.8
                },
                'recurrence': {
                    'planned': {
                        'base_annual_rate': 0.5,  # High recurrence rate for testing
                        'cumulative_rates': {
                            'year_1': 0.5,
                            'year_3': 0.7,
                            'year_5': 0.9
                        }
                    }
                },
                'retreatment': {
                    'eligibility_criteria': {
                        'detected_fluid': True,
                        'vision_loss_letters': 5
                    },
                    'probability': 0.9  # High retreatment probability for testing
                }
            }
        }
    }
    
    # Create configuration and simulation
    config = SimulationConfig.from_dict(config_dict)
    start_date = datetime.strptime(config_dict['simulation']['start_date'], '%Y-%m-%d')
    simulation = AgentBasedSimulation(config, start_date)
    
    # Add patients
    for i in range(config_dict['simulation']['num_patients']):
        patient_id = f"PATIENT{i+1:03d}"
        simulation.add_patient(patient_id, "treat_and_extend")
    
    # Run simulation
    end_date = start_date + timedelta(days=config_dict['simulation']['duration_days'])
    simulation.run(end_date)
    
    # Extract results
    results = {
        'start_date': config_dict['simulation']['start_date'],
        'duration_days': config_dict['simulation']['duration_days'],
        'simulation_type': 'ABS',
        'patient_histories': {}
    }
    
    # Convert patient visits to the format expected by visualization
    for patient_id, patient in simulation.agents.items():
        results['patient_histories'][patient_id] = []
        for visit in patient.history:
            # Convert dates to simulation time in months
            if 'date' in visit:
                visit_date = visit['date']
                visit_time = (visit_date - start_date).days / 30.0  # Convert to months
                visit_copy = visit.copy()
                visit_copy['time'] = visit_time
                results['patient_histories'][patient_id].append(visit_copy)
    
    return results

def verify_flags_present(results):
    """Verify that the required flags are present in the simulation results."""
    flag_counts = {
        'is_discontinuation_visit': 0,
        'discontinuation_reason': 0,
        'is_retreatment': 0,
        'retreatment_reason': 0
    }
    
    for patient_id, visits in results['patient_histories'].items():
        for visit in visits:
            for flag in flag_counts.keys():
                if flag in visit:
                    flag_counts[flag] += 1
    
    print("Flag presence counts:")
    for flag, count in flag_counts.items():
        print(f"  {flag}: {count}")
    
    # There should be at least some discontinuations in the simulation
    return flag_counts['is_discontinuation_visit'] > 0

def create_streamgraph(results):
    """Generate a streamgraph visualization from the simulation results."""
    # Use streamgraph_patient_states to extract patient states
    streamgraph_data = streamgraph.extract_patient_states(results)
    
    # Output some summary information
    print("Streamgraph data summary:")
    print(f"  Time points: {len(streamgraph_data['times'])}")
    print(f"  States: {list(streamgraph_data['states'].keys())}")
    
    # Save the streamgraph data for reference
    with open('streamgraph_test_output.json', 'w') as f:
        json.dump(streamgraph_data, f, indent=2)
    
    print(f"Streamgraph data saved to streamgraph_test_output.json")
    return streamgraph_data

def main():
    """Run the main test script."""
    # Run simulation
    print("Running test simulation...")
    results = run_test_simulation()
    
    # Save raw results for debugging
    with open('simulation_test_results.json', 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        results_copy = results.copy()
        for patient_id, visits in results_copy['patient_histories'].items():
            for visit in visits:
                if 'date' in visit and isinstance(visit['date'], datetime):
                    visit['date'] = visit['date'].isoformat()
        json.dump(results_copy, f, indent=2)
    
    # Verify that the flags are present
    print("\nVerifying flags in simulation results...")
    flags_present = verify_flags_present(results)
    
    if flags_present:
        print("\nSuccess: Required flags are present in the simulation results")
    else:
        print("\nError: Required flags are missing in the simulation results")
        return 1
    
    # Generate streamgraph
    print("\nGenerating streamgraph visualization...")
    try:
        streamgraph_data = create_streamgraph(results)
        print("\nSuccess: Streamgraph visualization generated successfully")
        
        # Check if active, discontinued, and retreated states are present
        states = streamgraph_data['states']
        if 'active' in states and 'discontinued' in states and 'retreated' in states:
            print("All required state categories are present in the visualization")
            
            # Check if the total patient count remains constant
            total_patients = sum(len(visits) for visits in results['patient_histories'].values())
            for t in range(len(streamgraph_data['times'])):
                state_sum = sum(states[state][t] for state in states)
                if state_sum != total_patients / len(streamgraph_data['times']):
                    print(f"Warning: Patient count inconsistency at time {t}: {state_sum} != {total_patients}")
        else:
            print("Warning: Not all required state categories are present in the visualization")
            print(f"Available states: {list(states.keys())}")
        
        return 0
    except Exception as e:
        print(f"\nError generating streamgraph: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())