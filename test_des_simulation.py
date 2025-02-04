from datetime import datetime, timedelta
from simulation import DiscreteEventSimulation, Event
from protocol_parser import load_protocol
from visualization.timeline_viz import print_patient_timeline
from visualization.acuity_viz import plot_patient_acuity, plot_multiple_patients
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_des_simulation(verbose: bool = False):
    try:
        # Load the Eylea treat-and-extend protocol
        if verbose:
            logger.info("Loading protocol...")
        protocol = load_protocol("eylea", "treat_and_extend")
        
        # Initialize simulation
        start_date = datetime(2023, 1, 1)
        end_date = start_date + timedelta(days=365)  # Run for one year
        
        if verbose:
            logger.info("Initializing DES simulation...")
        sim = DiscreteEventSimulation(start_date, {"treat_and_extend": protocol})
        
        # Add test patients
        initial_visit = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }

        for i in range(1, 8):  # Create patients TEST001 through TEST007
            patient_id = f"TEST{i:03d}"
            sim.add_patient(patient_id, "treat_and_extend")
            
            # Schedule initial visit with 30 minute spacing
            sim.clock.schedule_event(Event(
                time=start_date + timedelta(minutes=30*(i-1)),
                event_type="visit",
                patient_id=patient_id,
                data=initial_visit,
                priority=1
            ))
        
        # Run simulation
        if verbose:
            logger.info("Starting simulation...")
        sim.run(end_date)
        
        # Collect results
        patient_histories = {}
        for patient_id, state in sim.patient_states.items():
            patient_histories[patient_id] = state.get('visit_history', [])
            
        if verbose:
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
                
            # Print patient timelines
            print("\nPatient Timelines:")
            for patient_id, history in patient_histories.items():
                visits = [
                    {'date': visit['date'], 'actions': visit['actions']} 
                    for visit in history
                ]
                print_patient_timeline(patient_id, visits, start_date, end_date)
            
            # Print patient states
            print("\nFinal Patient States:")
            print("-" * 20)
            for patient_id, state in sim.patient_states.items():
                print(f"\nPatient {patient_id}:")
                for key, value in state.items():
                    print(f"  {key}: {value}")
        
        # Generate acuity plot (suppressed but code kept for future use)
        if False:  # Set to True to show plots
            plot_multiple_patients(patient_histories, start_date, end_date,
                                 title="Discrete Event Simulation: Visual Acuity Over Time",
                                 show=False)  # Add show=False parameter
        
        return patient_histories
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_des_simulation(verbose=False)
