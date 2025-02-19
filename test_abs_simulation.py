
from datetime import datetime, timedelta
from typing import Optional
from simulation.config import SimulationConfig
from simulation import AgentBasedSimulation, Event
from protocol_parser import load_protocol
from visualization.timeline_viz import print_patient_timeline
from visualization.acuity_viz import plot_patient_acuity, plot_multiple_patients
from simulation.clinical_model import DiseaseState
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_test_simulation(config: Optional[SimulationConfig] = None, verbose: bool = False):
    try:
        # Load the Eylea treat-and-extend protocol
        if verbose:
            logger.info("Loading protocol...")
        if config is None:
            config = SimulationConfig.from_yaml("test_simulation")
            
        # Initialize simulation
        start_date = datetime(2023, 1, 1)
        end_date = start_date + timedelta(days=config.duration_days)
        
        if verbose:
            logger.info("Initializing simulation...")
        sim = AgentBasedSimulation(config, start_date)
        
        # Set end date before adding patients
        sim.clock.end_date = end_date
        
        # Add test patients
        for i in range(1, config.num_patients + 1):
            patient_id = f"TEST{i:03d}"
            sim.add_patient(patient_id, "treat_and_extend")
            
            # Log initial state (zero-time output)
            if verbose:
                print(f"\nInitial state for Patient {patient_id}:")
                print(f"Time: {start_date}")
                if patient_id in sim.agents:
                    patient_state = sim.agents[patient_id].state
                    print(f"Disease State: {patient_state.state['disease_state']}")
                    print(f"Vision: {patient_state.state['current_vision']}")
                else:
                    print("Patient state not available yet")
                print("---")
            
            # Schedule initial visit with proper data structure
            sim.clock.schedule_event(Event(
                time=start_date + timedelta(minutes=30*(i-1)),
                event_type="visit",
                patient_id=patient_id,
                data={
                    "visit_type": "injection_visit",
                    "actions": ["vision_test", "oct_scan", "injection"],
                    "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
                },
                priority=1
            ))
            
        # Run simulation
        if verbose:
            logger.info("Starting simulation...")
        sim.run(end_date)
        
        # Collect results without printing
        patient_histories = {}
        for patient_id, patient in sim.agents.items():
            if verbose:
                print(f"\nPatient {patient_id}:")
                for visit in patient.history:
                    print(f"Visit on {visit['date']}: {visit['type']}")
                    print(f"Actions: {visit.get('actions', [])}")
                    if 'vision' in visit:
                        print(f"Vision: {visit['vision']}")
                    if 'oct' in visit:
                        print(f"OCT: {visit['oct']}")
                    print("---")
            
            if verbose:
                print_patient_timeline(patient_id, patient.history, start_date, end_date)
            patient_histories[patient_id] = patient.history
            
        if verbose:
            print("\nFinal Patient States:")
            print("-----------------")
            for patient_id, patient in sim.agents.items():
                print(f"\nPatient {patient_id}:")
                for key, value in patient.get_state_dict().items():
                    print(f"{key}: {value}")
                    
        # Generate combined acuity plot (suppressed but code kept for future use)
        if False:  # Set to True to show plots
            plot_multiple_patients(patient_histories, start_date, end_date,
                                 title="Agent-Based Simulation: Visual Acuity Over Time",
                                 show=False)  # Add show=False parameter
        
        # Verify disease state transitions and visit intervals
        for patient_id, patient in sim.agents.items():
            history = patient.state.visit_history
            disease_states = [visit['disease_state'] for visit in history]
            visit_dates = [visit['date'] for visit in history]
            
            print(f"\nDetailed disease state transitions for Patient {patient_id}:")
            print(f"Initial state: NAIVE")
            for i, (state, date) in enumerate(zip(disease_states, visit_dates), start=1):
                print(f"Visit {i}: Date: {date}, State: {state}")
            
            unique_states = set(disease_states) | {'NAIVE'}
            print(f"Unique states: {unique_states}")
            
            # Assert that disease states are changing
            if len(unique_states) <= 1:
                print(f"WARNING: Patient {patient_id} did not have any disease state transitions")
            else:
                print(f"Patient {patient_id} had {len(unique_states)} different disease states")
            
            # Assert that all disease states are valid
            valid_states = set(DiseaseState)
            invalid_states = [state for state in unique_states if DiseaseState[state.upper()] not in valid_states]
            if invalid_states:
                print(f"WARNING: Invalid disease states found for Patient {patient_id}: {invalid_states}")
            else:
                print(f"All disease states are valid for Patient {patient_id}")
            
            # Check visit intervals
            for i in range(1, len(visit_dates)):
                interval = (visit_dates[i] - visit_dates[i-1]).days // 7
                assert 4 <= interval <= 12, f"Invalid visit interval for Patient {patient_id}: {interval} weeks"
            
            # Check number of injections
            injections = sum(1 for visit in history if 'injection' in visit.get('actions', []))
            assert injections > 0, f"Patient {patient_id} did not receive any injections"

        return patient_histories
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_simulation(verbose=True)
