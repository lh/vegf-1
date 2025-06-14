"""
Validation script for the enhanced DES implementation.

This script tests that the enhanced DES implementation correctly loads
configuration parameters for protocols instead of using hard-coded values.
"""

from datetime import datetime, timedelta
import numpy as np
import logging
from simulation.config import SimulationConfig
from simulation.enhanced_des import EnhancedDES
from protocols.protocol_parser import ProtocolParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_enhanced_des_config():
    """Validate that EnhancedDES correctly loads protocol parameters from config."""
    logger.info("Testing EnhancedDES with configuration-driven parameters")
    
    # Load configuration
    config_name = "eylea_literature_based"  # Use a standard config
    config = SimulationConfig.from_yaml(config_name)
    
    # Add protocol parameters to the config
    logger.info("Adding test protocol parameters to config")
    
    # Add protocol type
    config.parameters["protocol_type"] = "treat_and_extend"
    
    # Create protocol config structure if not exists
    if "protocols" not in config.parameters:
        config.parameters["protocols"] = {}
    
    # Add treat-and-extend protocol configuration with non-standard parameters for testing
    config.parameters["protocols"]["treat_and_extend"] = {
        "treatment_phases": {
            "initial_loading": {
                "rules": {
                    "interval_weeks": 6,  # Non-standard to test loading
                    "injections_required": 4  # Non-standard to test completion criteria
                }
            },
            "maintenance": {
                "rules": {
                    "initial_interval_weeks": 10,  # Non-standard to test initial maintenance
                    "max_interval_weeks": 14,  # Non-standard to test max interval
                    "extension_step": 4,  # Non-standard to test extension
                    "reduction_step": 6  # Non-standard to test reduction
                }
            }
        }
    }
    
    # Initialize simulation
    sim = EnhancedDES(config)
    
    # Run simulation for a short period
    end_date = config.start_date + timedelta(days=365)  # Run for 1 year
    results = sim.run(end_date)
    
    # Analyze results to verify protocol parameters were used
    patient_histories = results.get("patient_histories", {})
    
    # Print summary statistics
    logger.info(f"Simulation completed with {len(patient_histories)} patients")
    
    # Check for expected interval patterns in a sample patient
    if patient_histories:
        sample_patient_id = next(iter(patient_histories.keys()))
        patient_visits = patient_histories[sample_patient_id]
        
        # Check loading phase interval
        loading_visits = [v for v in patient_visits if v.get("phase") == "loading"]
        if loading_visits:
            logger.info(f"Loading phase visits: {len(loading_visits)}")
            
            # Check if we can find the expected intervals
            expected_interval = config.parameters["protocols"]["treat_and_extend"]["treatment_phases"]["initial_loading"]["rules"].get("interval_weeks", 6)
            for i in range(1, len(loading_visits)):
                if i > 0:
                    # Calculate interval between visits
                    prev_date = loading_visits[i-1].get("date")
                    curr_date = loading_visits[i].get("date")
                    if prev_date and curr_date:
                        interval_days = (curr_date - prev_date).days
                        interval_weeks = interval_days / 7
                        logger.info(f"Loading visit {i} interval: {interval_weeks:.1f} weeks")
                        # Check if interval matches expected
                        if abs(interval_weeks - expected_interval) < 0.5:  # Allow some rounding
                            logger.info(f"✅ Loading phase interval matches config: {interval_weeks:.1f} weeks")
                        else:
                            logger.warning(f"❌ Loading phase interval does not match config: expected {expected_interval}, got {interval_weeks:.1f}")
        
        # Check maintenance phase interval
        maintenance_visits = [v for v in patient_visits if v.get("phase") == "maintenance"]
        if maintenance_visits:
            logger.info(f"Maintenance phase visits: {len(maintenance_visits)}")
            
            # Check initial maintenance interval
            if len(maintenance_visits) > 0:
                # Check interval from last loading to first maintenance
                loading_visits = [v for v in patient_visits if v.get("phase") == "loading"]
                if loading_visits and maintenance_visits:
                    last_loading = loading_visits[-1].get("date")
                    first_maintenance = maintenance_visits[0].get("date")
                    if last_loading and first_maintenance:
                        interval_days = (first_maintenance - last_loading).days
                        interval_weeks = interval_days / 7
                        expected_interval = config.parameters["protocols"]["treat_and_extend"]["treatment_phases"]["maintenance"]["rules"].get("initial_interval_weeks", 10)
                        logger.info(f"Initial maintenance interval: {interval_weeks:.1f} weeks")
                        # Check if interval matches expected
                        if abs(interval_weeks - expected_interval) < 0.5:  # Allow some rounding
                            logger.info(f"✅ Initial maintenance interval matches config: {interval_weeks:.1f} weeks")
                        else:
                            logger.warning(f"❌ Initial maintenance interval does not match config: expected {expected_interval}, got {interval_weeks:.1f}")
    else:
        logger.warning("No patient histories found, cannot validate intervals")
    
    # Print final validation result
    logger.info("Enhanced DES validation completed.")
    return results

if __name__ == "__main__":
    results = validate_enhanced_des_config()
    logger.info("Validation script completed successfully.")