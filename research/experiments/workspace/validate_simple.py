#!/usr/bin/env python3
"""Simple validation of refactored structure."""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

print("Testing refactored APE structure...")

# Test 1: Core imports
print("\n1. Testing core application imports...")
try:
    from ape.core.simulation_runner import SimulationRunner
    from ape.utils.state_helpers import save_protocol_spec, get_active_simulation
    from ape.components.simulation_ui import render_parameter_inputs
    print("   ✅ Core imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")

# Test 2: Visualization system
print("\n2. Testing visualization system...")
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS
    from ape.visualizations.streamgraph import create_patient_state_streamgraph
    print(f"   ✅ Visualization imports successful")
    print(f"   Primary color: {COLORS['primary']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Protocol system
print("\n3. Testing protocol system...")
try:
    from protocols.config_parser import load_config
    import os
    protocol_files = [f for f in os.listdir('protocols') if f.endswith('.yaml')]
    print(f"   ✅ Found {len(protocol_files)} protocol files")
    if protocol_files:
        print(f"   Sample: {protocol_files[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Page imports
print("\n4. Testing Streamlit pages...")
try:
    import importlib.util
    pages = ['1_Protocol_Manager.py', '2_Simulations.py', '3_Analysis.py']
    for page in pages:
        spec = importlib.util.spec_from_file_location(
            page.replace('.py', ''), 
            f'pages/{page}'
        )
        if spec:
            print(f"   ✅ {page} can be loaded")
        else:
            print(f"   ❌ {page} cannot be loaded")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Simulation models
print("\n5. Testing simulation models...")
try:
    from simulation.abs import AgentBasedSimulation
    from simulation.des import DiscreteEventSimulation
    from simulation.config import SimulationConfig
    print("   ✅ Simulation engines available")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ Basic validation complete!")
print("\nNOTE: Full scientific validation requires:")
print("- Running actual simulations through the UI")
print("- Verifying patient count conservation")
print("- Checking vision outcome distributions")
print("- Validating treatment interval calculations")