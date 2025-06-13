#!/usr/bin/env python3
"""
Test how the real simulation is called and what data it produces.
"""

import os
import sys
import yaml
import tempfile
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/rose/Code/CC')

from simulation.config import SimulationConfig
from treat_and_extend_abs import TreatAndExtendABS

# Create a minimal config
test_config = {
    'name': 'Test Simulation',
    'protocol': {
        'agent': 'eylea',
        'type': 'treat_and_extend',
        'parameter_set': 'standard'
    },
    'simulation': {
        'type': 'agent_based',
        'duration_days': 365,
        'num_patients': 10,
        'random_seed': 42,
        'start_date': '2024-01-01'
    },
    'parameters': {},
    'output': {
        'save_results': False,
        'plots': False
    }
}

# Write config to a temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
    yaml.dump(test_config, f)
    config_path = f.name

try:
    # Load config using from_yaml method
    config = SimulationConfig.from_yaml("test_simulation")
    print(f"Config loaded: {config}")
    
    # Override for quick test
    config.num_patients = 5
    config.duration_days = 180
    
    # Create and run simulation
    sim = TreatAndExtendABS(config)
    print(f"Simulation created: {sim}")
    
    # Run simulation
    patient_histories = sim.run()
    print(f"Simulation run, got {len(patient_histories)} patient histories")
    
    # Check if we can get results
    if hasattr(sim, 'get_results'):
        results = sim.get_results()
        print(f"Results structure: {list(results.keys())}")
        
        if 'mean_va_data' in results:
            print(f"mean_va_data sample: {results['mean_va_data'][:3]}")
        
finally:
    # Clean up
    os.unlink(config_path)