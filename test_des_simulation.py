from datetime import datetime, timedelta
from typing import Optional
from simulation.config import SimulationConfig
from simulation import DiscreteEventSimulation, Event
from protocols.protocol_parser import load_protocol
from visualization.timeline_viz import print_patient_timeline
from visualization.outcome_viz import OutcomeVisualizer
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
        
        # Initialize simulation
        sim = DiscreteEventSimulation(config, start_date)
        
        # Set end date and initialize patient generation
        sim.clock.end_date = end_date
        if verbose:
            logger.info("Patient generation configured for 3 patients per week on average")
        sim._schedule_patient_arrivals()  # Schedule patients after end date is set
        
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
                
            # Print summary statistics
            print("\nPatient Summary:")
            print("-" * 20)
            total_patients = len(patient_histories)
            total_visits = sum(len(history) for history in patient_histories.values())
            avg_visits = total_visits / total_patients
            print(f"Total Patients: {total_patients}")
            print(f"Total Visits: {total_visits}")
            print(f"Average Visits per Patient: {avg_visits:.1f}")
        
        # Generate acuity plots if enabled in config
        if config.get_output_params().get("plots", False):
            # Create visualizer
            viz = OutcomeVisualizer()
            
            # Plot mean acuity with confidence intervals
            viz.plot_mean_acuity(
                patient_histories,
                title="Discrete Event Simulation: Mean Visual Acuity",
                show=False,
                save_path="des_mean_acuity.png"
            )
            
            # Plot patient retention
            viz.plot_patient_retention(
                patient_histories,
                title="Discrete Event Simulation: Patient Retention",
                show=False,
                save_path="des_patient_retention.png"
            )
        
        return patient_histories
            
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        raise

if __name__ == "__main__":
    run_test_des_simulation(verbose=True)
