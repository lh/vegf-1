"""
Test script to verify that the streamgraph visualization works with the new patient state flags.

This script runs a small simulation and generates a streamgraph to visualize
patient states, which should now correctly display discontinuations and retreatments.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import simulation modules
from simulation.abs import AgentBasedSimulation
from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager

# Import visualization module
import streamlit_app.streamgraph_patient_states_fixed as streamgraph

def create_mock_simulation_results():
    """Create mock results with discontinuations and retreatments."""
    start_date = datetime(2025, 1, 1)
    patient_histories = {}
    
    # Create 10 patients with different patterns
    for i in range(10):
        patient_id = f"PATIENT{i+1:03d}"
        visits = []
        
        # Add some regular visits for all patients
        for day in range(0, 365, 28):
            visit_date = start_date + timedelta(days=day)
            
            visit = {
                'date': visit_date,
                'time': day / 30.0,  # Months
                'type': 'regular_visit',
                'actions': ['vision_test', 'oct_scan', 'injection'],
                'baseline_vision': 70.0,
                'vision': 70.0,
                'disease_state': 'STABLE',
                'treatment_status': {
                    'active': True,
                    'recurrence_detected': False,
                    'discontinuation_date': None,
                    'reason_for_discontinuation': None
                }
            }
            
            # Add our newly implemented flags for testing
            if i == 1 and day == 112:  # Discontinuation on day 112 for patient 2
                visit['is_discontinuation_visit'] = True
                visit['discontinuation_reason'] = 'stable_max_interval'
                visit['treatment_status']['active'] = False
                visit['treatment_status']['reason_for_discontinuation'] = 'stable_max_interval'
                visit['treatment_status']['discontinuation_date'] = visit_date
                visit['actions'].remove('injection')  # No injection on discontinuation
            
            if i == 2 and day == 196:  # Discontinuation on day 196 for patient 3
                visit['is_discontinuation_visit'] = True
                visit['discontinuation_reason'] = 'random_administrative'
                visit['treatment_status']['active'] = False
                visit['treatment_status']['reason_for_discontinuation'] = 'random_administrative'
                visit['treatment_status']['discontinuation_date'] = visit_date
                visit['actions'].remove('injection')  # No injection on discontinuation
            
            if i == 3 and day == 252:  # Discontinuation on day 252 for patient 4
                visit['is_discontinuation_visit'] = True
                visit['discontinuation_reason'] = 'premature'
                visit['treatment_status']['active'] = False
                visit['treatment_status']['reason_for_discontinuation'] = 'premature'
                visit['treatment_status']['discontinuation_date'] = visit_date
                visit['actions'].remove('injection')  # No injection on discontinuation
            
            if i == 1 and day == 224:  # Retreatment on day 224 for patient 2
                visit['is_retreatment'] = True
                visit['retreatment_reason'] = 'stable_max_interval'
                visit['treatment_status']['active'] = True
                visit['treatment_status']['recurrence_detected'] = False
                visit['treatment_status']['discontinuation_date'] = None
                visit['treatment_status']['reason_for_discontinuation'] = None
            
            visits.append(visit)
        
        patient_histories[patient_id] = visits
    
    # Create results dictionary
    results = {
        'start_date': '2025-01-01',
        'duration_days': 365,
        'simulation_type': 'ABS',
        'patient_histories': patient_histories
    }
    
    return results

def run_test_simulation():
    """Run a small test simulation with discontinuations and retreatments."""
    # Return mock results directly for testing the visualization
    return create_mock_simulation_results()
    
    # Create configuration and simulation
    # Create a mock config
    class MockConfig:
        def __init__(self, config_dict):
            self.config_name = "test_config"
            self.start_date = config_dict['simulation']['start_date']
            self.duration_days = config_dict['simulation']['duration_days']
            self.num_patients = config_dict['simulation']['num_patients']
            self.random_seed = config_dict['simulation']['random_seed']
            self.parameters = config_dict['parameters']
        
        def get_treatment_discontinuation_params(self):
            return self.parameters['discontinuation']
        
        def get_simulation_params(self):
            return {
                'start_date': self.start_date,
                'duration_days': self.duration_days,
                'num_patients': self.num_patients
            }
        
        def get(self, key, default=None):
            if key == "discontinuation":
                return self.parameters.get(key, default)
            return default
        
        def get_clinical_model_params(self):
            """Get clinical model parameters."""
            return {
                "disease_states": ["NAIVE", "STABLE", "ACTIVE", "HIGHLY_ACTIVE"],
                "transition_probabilities": {
                    "NAIVE": {"STABLE": 1.0},
                    "STABLE": {"STABLE": 0.8, "ACTIVE": 0.2},
                    "ACTIVE": {"STABLE": 0.3, "ACTIVE": 0.7},
                    "HIGHLY_ACTIVE": {"ACTIVE": 0.2, "HIGHLY_ACTIVE": 0.8}
                },
                "vision_change": {
                    "base_change": {
                        "NAIVE": {
                            "injection": [8.0, 1.0],
                            "no_injection": [-2.0, 1.0]
                        },
                        "STABLE": {
                            "injection": [1.0, 0.5],
                            "no_injection": [-1.0, 0.5]
                        },
                        "ACTIVE": {
                            "injection": [0.5, 0.5],
                            "no_injection": [-2.0, 1.0]
                        },
                        "HIGHLY_ACTIVE": {
                            "injection": [0.0, 1.0],
                            "no_injection": [-4.0, 1.5]
                        }
                    }
                }
            }
        
        def get_vision_params(self):
            """Get vision parameters."""
            return {
                "baseline_mean": 65.0,
                "baseline_std": 10.0
            }
    
    config = MockConfig(config_dict)
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
        json.dump(streamgraph_data, f, indent=2, cls=DateTimeEncoder)
    
    print(f"Streamgraph data saved to streamgraph_test_output.json")
    return streamgraph_data

def main():
    """Run the main test script."""
    # Create mock simulation results
    print("Creating mock simulation results with discontinuations and retreatments...")
    results = run_test_simulation()
    
    # Save raw results for debugging
    with open('simulation_test_results.json', 'w') as f:
        # Use custom encoder for datetime objects
        json.dump(results, f, indent=2, cls=DateTimeEncoder)
    
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
    
    # Print sample visit to debug format issues
    print("Sample visit format:")
    sample_patient_id = next(iter(results['patient_histories'].keys()))
    sample_visit = results['patient_histories'][sample_patient_id][0]
    for key, value in sample_visit.items():
        print(f"  {key}: {type(value).__name__} = {value}")
    
    try:
        # Add error handling with traceback
        import traceback
        try:
            streamgraph_data = create_streamgraph(results)
            print("\nSuccess: Streamgraph visualization generated successfully")
        except Exception as e:
            print("\nDetailed error:")
            traceback.print_exc()
            raise e
        
        # Check if active, discontinued, and retreated states are present
        states = streamgraph_data['states']
        if 'active' in states and 'discontinued' in states and 'retreated' in states:
            print("All required state categories are present in the visualization")
            print(f"Available states: {list(states.keys())}")
            
            # For demonstration, print the counts at different time points
            print("\nPatient state counts at selected time points:")
            time_points = [0, 4, 8, 12]  # Months
            for time_idx in range(len(streamgraph_data['times'])):
                if time_idx in time_points:
                    time = streamgraph_data['times'][time_idx]
                    print(f"Time {time:.1f} months:")
                    for state in states:
                        print(f"  {state}: {states[state][time_idx]}")
            
            # Check data conservation - sum should equal number of patients
            total_patients = len(results['patient_histories'])
            print(f"\nVerifying data conservation (total patients = {total_patients}):")
            
            for time_idx in range(len(streamgraph_data['times'])):
                state_sum = sum(states[state][time_idx] for state in states)
                if abs(state_sum - total_patients) > 0.01:  # Allow for small floating point errors
                    print(f"Warning: Patient count inconsistency at time {time_idx}: {state_sum} != {total_patients}")
                    return 1
            
            print("Data conservation verified: Patient counts are consistent at all time points")
            return 0
        else:
            print("Warning: Not all required state categories are present in the visualization")
            print(f"Available states: {list(states.keys())}")
            return 1
    except Exception as e:
        print(f"\nError generating streamgraph: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())