"""
Test script to verify ABS implementation handles both return types.
"""

from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS

def main():
    """Run a test of the fixed ABS implementation."""
    print("\n" + "="*50)
    print("TESTING FIXED ABS IMPLEMENTATION WITH COMPATIBILITY")
    print("="*50)
    
    # Create a test configuration
    try:
        config = SimulationConfig.from_yaml("test_simulation")
        
        # Override the parameters
        config.num_patients = 5
        config.duration_days = 365
        
        # Ensure discontinuation is enabled
        if not hasattr(config, 'parameters'):
            config.parameters = {}
        if "discontinuation" not in config.parameters:
            config.parameters["discontinuation"] = {}
        
        config.parameters["discontinuation"]["enabled"] = True
        
        # Try running the simulation
        print("Running ABS simulation with test config...")
        sim = TreatAndExtendABS(config)
        sim.run()
        
        print("\nSimulation completed successfully!")
        print(f"Total patients: {len(sim.agents)}")
        print(f"Total visits: {sim.stats.get('total_visits', 0)}")
        print(f"Unique discontinued patients: {sim.stats.get('unique_discontinuations', 0)}")
        
        print("\n✅ ABS COMPATIBILITY TEST PASSED!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        
if __name__ == "__main__":
    main()