from datetime import datetime, timedelta
from simulation import DiscreteEventSimulation, Event
from protocol_parser import load_protocol
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_des_simulation():
    try:
        # Load the Eylea treat-and-extend protocol
        logger.info("Loading protocol...")
        protocol = load_protocol("eylea", "treat_and_extend")
        
        # Initialize simulation
        start_date = datetime(2023, 1, 1)
        end_date = start_date + timedelta(days=365)  # Run for one year
        
        logger.info("Initializing DES simulation...")
        sim = DiscreteEventSimulation(start_date, {"treat_and_extend": protocol})
        
        # Add test patients
        sim.add_patient("TEST001", "treat_and_extend")
        sim.add_patient("TEST002", "treat_and_extend")  # Add a second patient to test resource constraints
        
        # Schedule initial visits
        initial_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        # Schedule first patient
        sim.clock.schedule_event(Event(
            time=start_date,
            event_type="visit",
            patient_id="TEST001",
            data=initial_visit,
            priority=1
        ))
        
        # Schedule second patient 30 minutes later
        sim.clock.schedule_event(Event(
            time=start_date + timedelta(minutes=30),
            event_type="visit",
            patient_id="TEST002",
            data=initial_visit,
            priority=1
        ))
        
        # Run simulation
        logger.info("Starting simulation...")
        sim.run(end_date)
        
        # Print simulation statistics
        print("\nSimulation Statistics:")
        print("-" * 20)
        for stat, value in sim.global_stats.items():
            if stat != "resource_utilization":
                print(f"{stat}: {value}")
                
        print("\nResource Utilization:")
        print("-" * 20)
        for resource, usage in sim.global_stats["resource_utilization"].items():
            print(f"{resource}: {usage}")
            
        # Print patient states
        print("\nFinal Patient States:")
        print("-" * 20)
        for patient_id, state in sim.patient_states.items():
            print(f"\nPatient {patient_id}:")
            for key, value in state.items():
                print(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_des_simulation()
