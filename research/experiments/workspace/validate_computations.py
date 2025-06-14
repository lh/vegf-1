#!/usr/bin/env python3
"""Quick validation of scientific computations after refactoring."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation.base import SimulationEnvironment
from simulation.config import SimulationConfig
from simulation.patient_generator import generate_patients

print("Testing scientific computation modules...")

# Test 1: Patient generation
print("\n1. Testing patient generation...")
try:
    patients = generate_patients(10, seed=42)
    print(f"   ✅ Generated {len(patients)} patients")
    print(f"   Sample patient age: {patients[0].age}")
    print(f"   Sample baseline VA: {patients[0].baseline_vision}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Simulation config
print("\n2. Testing simulation configuration...")
try:
    config = SimulationConfig(
        n_patients=10,
        duration_years=2.0,
        seed=42
    )
    print(f"   ✅ Created config: {config.n_patients} patients, {config.duration_years} years")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Core imports
print("\n3. Testing core imports...")
try:
    from ape.core.simulation_runner import SimulationRunner
    from ape.utils.state_helpers import save_protocol_spec
    from visualization.color_system import AcuityColors
    print("   ✅ All core imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")

# Test 4: Vision models
print("\n4. Testing vision models...")
try:
    from simulation.vision_models import calculate_vision_change
    # Test a simple vision change calculation
    change = calculate_vision_change(
        current_vision=70,
        time_since_last_injection=4,
        injection_count=3,
        patient_age=75
    )
    print(f"   ✅ Vision change calculation: {change:.2f} letters")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Protocol loading
print("\n5. Testing protocol loading...")
try:
    from protocols.config_parser import load_config
    protocol_path = Path("protocols/aflibercept_2mg_treat_and_extend.yaml")
    if protocol_path.exists():
        protocol = load_config(str(protocol_path))
        print(f"   ✅ Loaded protocol: {protocol['metadata']['name']}")
    else:
        print(f"   ⚠️  Protocol file not found: {protocol_path}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ Basic validation complete!")
print("Note: Full validation requires running actual simulations through the UI.")