#!/usr/bin/env python3
"""Test the Protocol Manager with a time-based protocol in temp directory."""

import sys
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test loading the protocol
try:
    from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
    from simulation_v2.protocols.protocol_spec import ProtocolSpecification
    
    temp_protocol = Path('protocols/temp/test_time_based_protocol.yaml')
    
    # Load YAML to check model_type
    with open(temp_protocol) as f:
        data = yaml.safe_load(f)
    
    print(f"Protocol: {temp_protocol.name}")
    print(f"Model type in YAML: {data.get('model_type')}")
    
    # Determine if it's time-based
    is_time_based = data.get('model_type') == 'time_based'
    print(f"Is time-based: {is_time_based}")
    
    # Load with correct class
    if is_time_based:
        print("\nLoading as TimeBasedProtocolSpecification...")
        spec = TimeBasedProtocolSpecification.from_yaml(temp_protocol)
        print(f"✓ Successfully loaded")
        print(f"Has disease_transitions: {hasattr(spec, 'disease_transitions')}")
        print(f"Has disease_transitions_file: {hasattr(spec, 'disease_transitions_file')}")
        print(f"Protocol type: {spec.protocol_type}")
        print(f"Model type: {getattr(spec, 'model_type', 'not found')}")
    else:
        print("\nLoading as standard ProtocolSpecification...")
        spec = ProtocolSpecification.from_yaml(temp_protocol)
        print(f"✓ Successfully loaded")
        print(f"Has disease_transitions: {hasattr(spec, 'disease_transitions')}")
    
    print("\nProtocol Manager should now work correctly with this protocol!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()