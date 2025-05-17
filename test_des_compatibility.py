"""
Test script for DES compatibility issues with the fixed discontinuation implementation.
"""

from simulation.config import SimulationConfig
from treat_and_extend_des_fixed import TreatAndExtendDES

def test_des_compatibility():
    """Test that the DES implementation works with the fixed implementation."""
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
        
        # Try creating and running the fixed DES implementation
        print("\nRunning DES compatibility test")
        sim = TreatAndExtendDES(config)
        patient_histories = sim.run()
        print("✅ DES simulation completed successfully")
        
        # Print some stats
        print(f"Total patients: {len(sim.patients)}")
        print(f"Total visits: {sim.stats['total_visits']}")
        print(f"Unique discontinued patients: {sim.stats.get('unique_discontinuations', 0)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_des_compatibility()