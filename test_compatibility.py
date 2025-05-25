"""
Test script for compatibility issues with the fixed discontinuation implementation.
"""

from simulation.config import SimulationConfig
from simulation.refactored_discontinuation_manager import CompatibilityDiscontinuationManager
from treat_and_extend_abs_fixed import TreatAndExtendABS
from datetime import datetime, timedelta

def test_compatibility():
    """Test that the CompatibilityDiscontinuationManager works with the fixed implementation."""
    # Create a test configuration
    try:
        config = SimulationConfig.from_yaml("test_simulation")
        
        # Override the parameters
        config.num_patients = 10
        config.duration_days = 365
        
        # Make sure discontinuation is enabled
        if not hasattr(config, 'parameters'):
            config.parameters = {}
        if "discontinuation" not in config.parameters:
            config.parameters["discontinuation"] = {}
        
        config.parameters["discontinuation"]["enabled"] = True
        
        # Set criteria if not present
        if "criteria" not in config.parameters["discontinuation"]:
            config.parameters["discontinuation"]["criteria"] = {}
        
        # Set stable_max_interval if not present
        if "stable_max_interval" not in config.parameters["discontinuation"]["criteria"]:
            config.parameters["discontinuation"]["criteria"]["stable_max_interval"] = {}
            
        # Set probability to 0.9
        config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["probability"] = 0.9
        config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["consecutive_visits"] = 3
        config.parameters["discontinuation"]["criteria"]["stable_max_interval"]["interval_weeks"] = 16
    except Exception as e:
        print(f"Error creating configuration: {e}")
        # Create a minimal config
        config = SimulationConfig()
        config.num_patients = 10
        config.duration_days = 365
        config.parameters = {
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": 0.9,
                        "consecutive_visits": 3,
                        "interval_weeks": 16
                    }
                }
            }
        }
    
    # Create a test discontinuation manager
    manager = CompatibilityDiscontinuationManager({"discontinuation": {"enabled": True}})
    
    # Test evaluate_discontinuation with patient_id
    patient_state = {
        "disease_activity": {"fluid_detected": False, "consecutive_stable_visits": 3, "max_interval_reached": True, "current_interval": 16},
        "treatment_status": {"active": True}
    }
    
    # Test with patient_id explicitly provided
    result = manager.evaluate_discontinuation(
        patient_state=patient_state,
        current_time=datetime.now(),
        patient_id="test_patient",
        clinician_id=None,
        treatment_start_time=datetime.now() - timedelta(days=100)
    )
    
    print("Test 1 - Evaluate with patient_id:")
    print(f"Result: {result}")
    
    # Test evaluate_retreatment with patient_id
    result2 = manager.evaluate_retreatment(
        patient_state=patient_state,
        patient_id="test_patient"
    )
    
    print("\nTest 2 - Evaluate retreatment with patient_id:")
    print(f"Result: {result2}")
    
    # Try creating and running the fixed ABS implementation
    try:
        print("\nTest 3 - Create and run fixed ABS:")
        sim = TreatAndExtendABS(config)
        sim.run()
        print("✅ ABS simulation completed successfully")
    except Exception as e:
        print(f"❌ Error running ABS simulation: {e}")
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    test_compatibility()