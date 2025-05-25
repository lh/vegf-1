#!/usr/bin/env python3
"""
Run a simulation with enhanced discontinuation debugging

This script runs a simulation with a higher probability of discontinuations
to help debug and verify that the discontinuation system is working correctly.
It uses a patched patient generator to create patients who are ready for
discontinuation evaluation.
"""

import sys
import os
from datetime import datetime

# Import our discontinuation patient generator to patch the regular generators
import discontinuation_ready_patients

# Configure to make 70% of patients ready for discontinuation
discontinuation_ready_patients.configure(discontinuation_ready_percent=0.7, verbose=True)

# Now import and run the simulation
from simulation.config import SimulationConfig

print("Creating configuration with high discontinuation probability")
# Create a configuration with high discontinuation probability
config = SimulationConfig.from_yaml("eylea_literature_based")
config.duration_days = 365  # 1 year
config.num_patients = 100   # 100 patients (smaller for faster testing)

# Ensure discontinuation is enabled and with high probability
if not hasattr(config, 'parameters'):
    config.parameters = {}

if 'discontinuation' not in config.parameters:
    config.parameters['discontinuation'] = {}

config.parameters['discontinuation']['enabled'] = True

if 'criteria' not in config.parameters['discontinuation']:
    config.parameters['discontinuation']['criteria'] = {}

# Set very high discontinuation probability for all types
if 'stable_max_interval' not in config.parameters['discontinuation']['criteria']:
    config.parameters['discontinuation']['criteria']['stable_max_interval'] = {}
config.parameters['discontinuation']['criteria']['stable_max_interval']['probability'] = 0.9  # 90% chance

if 'random_administrative' not in config.parameters['discontinuation']['criteria']:
    config.parameters['discontinuation']['criteria']['random_administrative'] = {}
config.parameters['discontinuation']['criteria']['random_administrative']['annual_probability'] = 0.2  # 20% annual

# Choose simulation type (ABS or DES)
sim_type = 'ABS' if len(sys.argv) < 2 else sys.argv[1].upper()

print(f"Running {sim_type} simulation with {config.num_patients} patients for {config.duration_days} days")
print(f"Discontinuation settings: stable_max_interval probability={config.parameters['discontinuation']['criteria']['stable_max_interval']['probability']}")

# Run the appropriate simulation
if sim_type == 'ABS':
    from treat_and_extend_abs import TreatAndExtendABS
    sim = TreatAndExtendABS(config)
    result = sim.run()
else:  # DES
    from treat_and_extend_des import TreatAndExtendDES
    sim = TreatAndExtendDES(config)
    result = sim.run()

# Get discontinuation statistics
disc_manager = getattr(sim, 'discontinuation_manager', None)
if disc_manager:
    stats = disc_manager.get_statistics()
    print("\nDiscontinuation Statistics:")
    print(f"Total discontinuations: {stats.get('total_discontinuations', 0)}")
    print(f"Stable max interval: {stats.get('stable_max_interval_discontinuations', 0)}")
    print(f"Random administrative: {stats.get('random_administrative_discontinuations', 0)}")
    print(f"Treatment duration: {stats.get('treatment_duration_discontinuations', 0)}")
    print(f"Premature: {stats.get('premature_discontinuations', 0)}")
    
    # Calculate discontinuation rate
    disc_rate = stats.get('total_discontinuations', 0) / config.num_patients
    print(f"Overall discontinuation rate: {disc_rate:.1%}")
else:
    print("Could not access discontinuation manager")

print("\nSimulation complete!")