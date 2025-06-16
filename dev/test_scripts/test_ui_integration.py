#!/usr/bin/env python3
"""
Test the UI integration for time-based protocols.
"""

import streamlit as st
from pathlib import Path

print("Testing Time-Based Protocol UI Integration")
print("="*50)

# Check if protocol directories exist
standard_dir = Path("protocols/v2")
time_based_dir = Path("protocols/v2_time_based")

print(f"\nStandard protocols directory exists: {standard_dir.exists()}")
print(f"Time-based protocols directory exists: {time_based_dir.exists()}")

# List available protocols
if standard_dir.exists():
    standard_files = list(standard_dir.glob("*.yaml"))
    print(f"\nStandard protocols found: {len(standard_files)}")
    for f in standard_files[:3]:  # Show first 3
        print(f"  - {f.name}")

if time_based_dir.exists():
    time_based_files = list(time_based_dir.glob("*.yaml"))
    print(f"\nTime-based protocols found: {len(time_based_files)}")
    for f in time_based_files[:3]:  # Show first 3
        print(f"  - {f.name}")

# Check if imports work
try:
    from simulation_v2.protocols.protocol_spec import ProtocolSpecification
    from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
    print("\n✓ Protocol specification imports successful")
except Exception as e:
    print(f"\n✗ Import error: {e}")

# Test loading a time-based protocol
try:
    tb_protocol = time_based_dir / "eylea_time_based.yaml"
    if tb_protocol.exists():
        spec = TimeBasedProtocolSpecification.from_yaml(tb_protocol)
        print(f"\n✓ Successfully loaded time-based protocol: {spec.name}")
        print(f"  Model type: {spec.model_type}")
        print(f"  Update interval: {spec.update_interval_days} days")
except Exception as e:
    print(f"\n✗ Error loading time-based protocol: {e}")

print("\n" + "="*50)
print("To test the full UI integration:")
print("1. Run: streamlit run APE.py")
print("2. Go to Protocol Manager")
print("3. Select 'eylea_time_based [TIME-BASED]'")
print("4. Go to Simulations")
print("5. Run a simulation with the time-based protocol")