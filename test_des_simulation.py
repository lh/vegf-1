from datetime import datetime, timedelta
from typing import Optional
from simulation.config import SimulationConfig
from simulation import DiscreteEventSimulation, Event
from protocol_parser import load_protocol
from visualization.timeline_viz import print_patient_timeline
from visualization.acuity_viz import plot_patient_acuity, plot_multiple_patients
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_des_simulation(config: Optional[SimulationConfig] = None, verbose: bool = False):
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
            logger.info("Initializing DES simulation...")
        
        # Initialize simulation and set end date before adding patients
        sim = DiscreteEventSimulation(config, start_date)
        sim.clock.end_date = end_date  # Set end date first
        
        # Add test patients after end date is set
        for i in range(1, 8):  # Create patients TEST001 through TEST007
            patient_id = f"TEST{i:03d}"
            sim.add_patient(patient_id, "test_simulation")  # Use the protocol type from YAML
        
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
                if stat == "scheduling":
                    print("\nScheduling Statistics:")
                    print("-" * 20)
                    for sched_stat, sched_value in value.items():
                        print(f"{sched_stat}: {sched_value}")
                else:
                    print(f"{stat}: {value}")
                
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
        
        # Generate acuity plot if enabled in config
        if config.get_output_params().get("plots", False):
            plot_multiple_patients(
                patient_histories, 
                start_date, 
                end_date,
                title="Discrete Event Simulation: Visual Acuity Over Time",
                show=False,
                save_path="des_acuity_plot.png"
            )
        
        return patient_histories
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_des_simulation(verbose=True)
