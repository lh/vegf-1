#!/usr/bin/env python3
"""
Run a real ABS simulation and save the results for streamgraph visualization.

This script runs a proper simulation using the actual ABS implementation,
collecting real patient data including discontinuations and retreatments.
"""

import sys
import os
import json
import logging
import argparse
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure we can import the simulation module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_abs_simulation(population_size=100, duration_years=5, config_path=None):
    """
    Run an actual ABS simulation with the specified parameters.
    
    Args:
        population_size: Number of patients to simulate
        duration_years: Duration of simulation in years
        config_path: Optional path to simulation config file
    
    Returns:
        Dict containing simulation results
    """
    try:
        # Import the ABS simulation module
        from simulation.abs import AgentBasedSimulation as ABSSimulation
        from simulation.config import SimulationConfig
        
        # Load configuration
        
        if config_path and os.path.exists(config_path):
            logger.info(f"Loading configuration from {config_path}")
            # Extract config name from path (remove extension)
            config_name = os.path.splitext(os.path.basename(config_path))[0]
            config = SimulationConfig.from_yaml(config_name)
        else:
            # Use default configuration
            logger.info("Using default configuration")
            config = SimulationConfig.from_yaml("eylea_literature_based")
        
        # Update configuration with specified parameters
        config.num_patients = population_size
        
        # Convert duration years to days
        config.duration_days = int(duration_years * 365)
        
        # Create and run simulation
        logger.info(f"Running ABS simulation with {population_size} patients for {duration_years} years")
        
        # Get the start date from the config or use a default
        start_date = config.start_date if hasattr(config, 'start_date') else datetime.now()
        
        # Initialize simulation with config and start date
        simulation = ABSSimulation(config, start_date)
        
        # Calculate end date based on start date and duration
        end_date = start_date + timedelta(days=config.duration_days)
        
        # Run simulation with end date
        simulation.run(end_date)
        
        logger.info("Simulation completed successfully")
        
        # Get results after running the simulation
        results = simulation.get_results()
        
        if not results or not isinstance(results, dict):
            logger.error("Simulation did not return valid results")
            return None
            
        # Process the simulation results to get patient histories
        patient_histories = {}
        
        if 'patients' in results:
            for patient_id, patient in results['patients'].items():
                # Extract patient history from the patient object
                patient_histories[patient_id] = patient.history
                
            # Add patient_histories to the results
            results['patient_histories'] = patient_histories
            
        # Verify results contain necessary data
        if "patient_histories" not in results or not results["patient_histories"]:
            logger.error("Simulation results do not contain patient histories")
            return None
        
        # Log simulation statistics
        logger.info(f"Generated data for {len(results['patient_histories'])} patients")
        logger.info(f"Discontinuation counts: {results.get('discontinuation_counts', {})}")
        
        return results
        
    except ImportError as e:
        logger.error(f"Failed to import simulation module: {e}")
        return None
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to run simulation and save results."""
    parser = argparse.ArgumentParser(description='Run ABS simulation for streamgraph visualization')
    parser.add_argument('--patients', '-p', type=int, default=100,
                        help='Number of patients to simulate (default: 100)')
    parser.add_argument('--years', '-y', type=int, default=5,
                        help='Simulation duration in years (default: 5)')
    parser.add_argument('--config', '-c', type=str, default=None,
                        help='Path to simulation configuration file')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: streamgraph_data_YYYYMMDD_HHMMSS.json)')
    args = parser.parse_args()
    
    # Run simulation
    results = run_abs_simulation(
        population_size=args.patients,
        duration_years=args.years,
        config_path=args.config
    )
    
    if results:
        # Generate output filename if not provided
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output = f"streamgraph_data_{timestamp}.json"
        
        # Save results to file
        with open(args.output, "w") as f:
            json.dump(results, f)
        
        logger.info(f"Simulation results saved to {args.output}")
        print(f"Simulation results saved to {args.output}")
        return 0
    else:
        logger.error("Simulation failed to produce valid results")
        return 1

if __name__ == "__main__":
    sys.exit(main())