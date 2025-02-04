
from datetime import datetime, timedelta
from typing import Optional
from simulation.config import SimulationConfig
from simulation import AgentBasedSimulation, Event
from protocol_parser import load_protocol
from visualization.timeline_viz import print_patient_timeline
from visualization.acuity_viz import plot_patient_acuity, plot_multiple_patients
import logging

logging.basicConfig(level=logging.INFO)
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
        
        # Add test patients
        initial_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }

        for i in range(1, 8):  # Create patients TEST001 through TEST007
            patient_id = f"TEST{i:03d}"
            sim.add_patient(patient_id, "treat_and_extend")
            
            # Schedule initial visit
            sim.clock.schedule_event(Event(
                time=start_date + timedelta(minutes=30*(i-1)),
                event_type="visit",
                patient_id=patient_id,
                data={"visit_type": initial_visit},
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
                for key, value in patient.state.items():
                    print(f"{key}: {value}")
                    
        # Generate combined acuity plot (suppressed but code kept for future use)
        if False:  # Set to True to show plots
            plot_multiple_patients(patient_histories, start_date, end_date,
                                 title="Agent-Based Simulation: Visual Acuity Over Time",
                                 show=False)  # Add show=False parameter
        
        return patient_histories
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_simulation()
