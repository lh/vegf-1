
from datetime import datetime, timedelta
from simulation import AgentBasedSimulation, Event
from protocol_parser import load_protocol
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_simulation():
    try:
        # Load the Eylea treat-and-extend protocol
        logger.info("Loading protocol...")
        protocol = load_protocol("eylea", "treat_and_extend")
        
        # Initialize simulation
        start_date = datetime(2023, 1, 1)
        end_date = start_date + timedelta(days=365)  # Run for one year
        
        logger.info("Initializing simulation...")
        sim = AgentBasedSimulation(start_date, {"treat_and_extend": protocol})
        
        # Add a test patient
        sim.add_patient("TEST001", "treat_and_extend")
        
        # Schedule initial visit
        initial_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        sim.clock.schedule_event(Event(
            time=start_date,
            event_type="visit",
            patient_id="TEST001",
            data={"visit_type": initial_visit},
            priority=1
        ))
        
        # Run simulation
        logger.info("Starting simulation...")
        sim.run(end_date)
        
        # Print patient history
        patient = sim.agents["TEST001"]
        print("\nPatient History:")
        print("--------------")
        for visit in patient.history:
            print(f"Visit on {visit['date']}: {visit['type']}")
            print(f"Actions: {visit.get('actions', [])}")
            if 'vision' in visit:
                print(f"Vision: {visit['vision']}")
            if 'oct' in visit:
                print(f"OCT: {visit['oct']}")
            print("---")
        
        # Print final patient state
        print("\nFinal Patient State:")
        print("-----------------")
        for key, value in patient.state.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_simulation()
