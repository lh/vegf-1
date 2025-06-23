#!/usr/bin/env python3
"""Test if the Protocol Manager can handle time-based protocols in temp directory."""

import yaml
from pathlib import Path
import shutil

# Create temp directory if it doesn't exist
temp_dir = Path('protocols/temp')
temp_dir.mkdir(exist_ok=True)

# Copy a time-based protocol to temp directory
source_protocol = Path('protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml')
if source_protocol.exists():
    dest_protocol = temp_dir / 'test_time_based_protocol.yaml'
    shutil.copy(source_protocol, dest_protocol)
    print(f"Copied {source_protocol} to {dest_protocol}")
    
    # Load and verify it's time-based
    with open(dest_protocol) as f:
        data = yaml.safe_load(f)
    
    print(f"Model type: {data.get('model_type')}")
    print(f"Is time-based: {data.get('model_type') == 'time_based'}")
    
    # Test loading the protocol specification
    try:
        from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
        spec = TimeBasedProtocolSpecification.from_yaml(dest_protocol)
        print(f"Successfully loaded as TimeBasedProtocolSpecification")
        print(f"Has disease_transitions attribute: {hasattr(spec, 'disease_transitions')}")
        print(f"Protocol type from spec: {getattr(spec, 'model_type', 'not found')}")
    except Exception as e:
        print(f"Error loading protocol: {e}")
else:
    print(f"Source protocol not found: {source_protocol}")

print("\nTest complete. The temp protocol should now be loadable in Protocol Manager.")