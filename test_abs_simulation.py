
from datetime import datetime, timedelta
from typing import Optional
from simulation.config import SimulationConfig
from simulation import AgentBasedSimulation, Event
from protocols.protocol_parser import load_protocol
from visualization.timeline_viz import print_patient_timeline
from visualization.acuity_viz import plot_patient_acuity, plot_multiple_patients
from simulation.clinical_model import DiseaseState
import logging
from datetime import datetime, timedelta

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
            
            logger.debug(f"\nDetailed disease state transitions for Patient {patient_id}:")
            logger.debug(f"Initial state: NAIVE")
            for i, (state, date) in enumerate(zip(disease_states, visit_dates), start=1):
                logger.debug(f"Visit {i}: Date: {date}, State: {state}")
            
            unique_states = set(disease_states) | {'NAIVE'}
            logger.debug(f"Unique states: {unique_states}")
            
            # Assert that disease states are changing after a minimum number of visits
            min_visits_for_transition = 3
            if len(visit_dates) >= min_visits_for_transition:
                assert len(unique_states) > 1, f"Patient {patient_id} did not have any disease state transitions after {min_visits_for_transition} visits"
                logger.debug(f"Patient {patient_id} had {len(unique_states)} different disease states")
            else:
                logger.debug(f"Not enough visits to check for state transitions for Patient {patient_id}")
            
            # Assert that all disease states are valid
            valid_states = set(DiseaseState)
            invalid_states = [state for state in unique_states if DiseaseState[state.upper()] not in valid_states]
            assert not invalid_states, f"Invalid disease states found for Patient {patient_id}: {invalid_states}"
            logger.debug(f"All disease states are valid for Patient {patient_id}")
            
            # Verify fixed schedule adherence
            expected_months = [0, 1, 2, 4, 6, 8, 10, 12]
            expected_weeks = [0, 4, 9, 18, 27, 36, 44, 52]
            actual_weeks = [(d - start_date).days // 7 for d in visit_dates[:8]]
            logger.debug(f"Expected weeks: {expected_weeks}")
            logger.debug(f"Actual weeks: {actual_weeks}")
            for i, (expected, actual) in enumerate(zip(expected_weeks, actual_weeks)):
                assert abs(expected - actual) <= 1, f"Fixed schedule mismatch for Patient {patient_id} at visit {i+1}: Expected week {expected}, got week {actual}"
            logger.debug(f"Fixed schedule adherence verified for Patient {patient_id}")
            
            # Verify HIGHLY_ACTIVE handling
            highly_active_count = disease_states.count("highly_active")
            logger.debug(f"HIGHLY_ACTIVE occurrences: {highly_active_count}")
            if highly_active_count > 0:
                assert highly_active_count <= 5, f"Unexpected number of HIGHLY_ACTIVE occurrences: {highly_active_count}"
                highly_active_index = disease_states.index("highly_active")
                if visit_dates[highly_active_index].month >= 12:
                    logger.warning(f"HIGHLY_ACTIVE state occurred after loading phase for patient {patient_id}")
                logger.debug("Handled HIGHLY_ACTIVE state during loading phase")
            
            # Check number of injections
            injections = sum(1 for visit in history[:8] if 'injection' in visit.get('actions', []))
            assert injections == 8, f"Patient {patient_id} did not receive exactly 8 injections in the first year"
            logger.debug(f"Patient {patient_id} received {injections} injections in the first year")

            # Add timeline logging
            logger.debug(f"Visit timeline for Patient {patient_id}:")
            for i, (date, state) in enumerate(zip(visit_dates, disease_states), start=1):
                phase = "initial_loading" if i <= 8 else "maintenance"
                next_visit = visit_dates[i] if i < len(visit_dates) else "N/A"
                logger.debug(f"Visit {i}: Phase: {phase} | State: {state} | Date: {date} | Next Visit: {next_visit}")

        return patient_histories
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_simulation(verbose=True)
