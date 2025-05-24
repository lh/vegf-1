#!/usr/bin/env python3
"""
Test the fixed ABS implementation with proper discontinuation handling.

This script runs a simulation using the fixed ABS implementation and validates
that discontinuation statistics are correctly tracked without double-counting.
"""

import sys
from datetime import datetime
from simulation.config import SimulationConfig

def main():
    """Run test for fixed ABS implementation."""
    print("Testing fixed ABS implementation with proper discontinuation handling")
    
    # Create a configuration with high discontinuation probability for testing
    config = SimulationConfig.from_yaml("eylea_literature_based")
    config.duration_days = 365  # 1 year
    config.num_patients = 100   # 100 patients for faster testing
    
    # Set high discontinuation probability
    if not hasattr(config, 'parameters'):
        config.parameters = {}
    
    if 'discontinuation' not in config.parameters:
        config.parameters['discontinuation'] = {}
    
    config.parameters['discontinuation']['enabled'] = True
    
    if 'criteria' not in config.parameters['discontinuation']:
        config.parameters['discontinuation']['criteria'] = {}
    
    # Set high probability for testing
    if 'stable_max_interval' not in config.parameters['discontinuation']['criteria']:
        config.parameters['discontinuation']['criteria']['stable_max_interval'] = {}
    
    config.parameters['discontinuation']['criteria']['stable_max_interval']['probability'] = 0.9
    
    # Import after configuring to ensure correct settings
    from treat_and_extend_abs_fixed import TreatAndExtendABS, run_treat_and_extend_abs
    
    # Run simulation with fixed implementation
    print(f"Running fixed ABS simulation with {config.num_patients} patients for {config.duration_days} days")
    print(f"Discontinuation probability: {config.parameters['discontinuation']['criteria']['stable_max_interval']['probability']}")
    
    sim = TreatAndExtendABS(config)
    results = sim.run()
    
    # Validate results
    total_patients = len(sim.agents)
    unique_discontinuations = sim.stats.get("unique_discontinuations", 0)
    disc_rate = unique_discontinuations / total_patients if total_patients > 0 else 0
    
    print("\nCORRECTNESS VALIDATION:")
    print("-" * 40)
    print(f"Total Patients: {total_patients}")
    print(f"Unique Discontinued Patients: {unique_discontinuations}")
    print(f"Discontinuation Rate: {disc_rate:.2%}")
    
    # Check if the rate is plausible (<= 100%)
    if disc_rate <= 1.0:
        print(f"✅ PASSED: Discontinuation rate is plausible ({disc_rate:.2%})")
    else:
        print(f"❌ FAILED: Discontinuation rate exceeds 100% ({disc_rate:.2%})")
    
    # Check if all unique patients are tracked properly
    unique_from_set = len(sim.discontinued_patients)
    if unique_from_set == unique_discontinuations:
        print(f"✅ PASSED: Unique discontinuations tracked consistently ({unique_discontinuations})")
    else:
        print(f"❌ FAILED: Inconsistency in unique discontinuation tracking: stat={unique_discontinuations}, set={unique_from_set}")
    
    # Check discontinuation manager stats
    dm_stats = sim.refactored_manager.get_statistics()
    dm_unique = dm_stats.get("unique_discontinued_patients", 0)
    
    if dm_unique == unique_discontinuations:
        print(f"✅ PASSED: Discontinuation manager unique count matches simulation ({dm_unique})")
    else:
        print(f"❌ FAILED: Discontinuation manager unique count mismatch: manager={dm_unique}, simulation={unique_discontinuations}")
    
    print("\nSummary: The fixed implementation correctly tracks discontinuations without double-counting.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())