#!/usr/bin/env python
"""
Test the protocol-based V2 simulation system.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner


def main():
    """Test protocol loading and simulation."""
    print("Testing V2 Protocol System")
    print("=" * 60)
    
    # Load protocol
    protocol_path = Path("protocols/v2/eylea_treat_and_extend_v1.0.yaml")
    print(f"\nLoading protocol: {protocol_path}")
    
    try:
        spec = ProtocolSpecification.from_yaml(protocol_path)
        print(f"✅ Successfully loaded: {spec.name} v{spec.version}")
        print(f"   Author: {spec.author}")
        print(f"   Description: {spec.description}")
        print(f"   Checksum: {spec.checksum[:16]}...")
    except Exception as e:
        print(f"❌ Failed to load protocol: {e}")
        return
        
    # Display key parameters
    print("\nProtocol Parameters:")
    print(f"  Interval: {spec.min_interval_days}-{spec.max_interval_days} days")
    print(f"  Extension/Shortening: ±{spec.extension_days} days")
    print(f"  Baseline vision: {spec.baseline_vision_mean}±{spec.baseline_vision_std}")
    
    # Run small test simulation
    print("\nRunning test simulation...")
    runner = SimulationRunner(spec)
    
    results = runner.run(
        engine_type='abs',
        n_patients=10,
        duration_years=1,
        seed=42
    )
    
    print(f"\nResults:")
    print(f"  Total injections: {results.total_injections}")
    print(f"  Mean final vision: {results.mean_final_vision:.1f}")
    print(f"  Discontinuation rate: {results.discontinuation_rate:.1%}")
    
    # Check audit trail
    print(f"\nAudit trail has {len(runner.audit_log)} entries:")
    for entry in runner.audit_log:
        print(f"  - {entry['event']} at {entry['timestamp']}")
        
    # Test parameter validation
    print("\nTesting parameter validation...")
    test_missing_params()
    test_invalid_probabilities()
    
    print("\n✅ Protocol system test complete!")


def test_missing_params():
    """Test that missing parameters cause errors."""
    print("  Testing missing parameters...")
    
    # Create a spec with missing field
    data = {
        'name': 'Test',
        'version': '1.0',
        'author': 'Test',
        'description': 'Test',
        # Missing required fields
    }
    
    import yaml
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(data, f)
        temp_path = Path(f.name)
        
    try:
        spec = ProtocolSpecification.from_yaml(temp_path)
        print("    ❌ Should have failed with missing fields!")
    except ValueError as e:
        print(f"    ✅ Correctly rejected: {e}")
    finally:
        temp_path.unlink()


def test_invalid_probabilities():
    """Test that invalid probabilities cause errors."""
    print("  Testing invalid probabilities...")
    
    # Create transitions that don't sum to 1
    from simulation_v2.core.disease_model import DiseaseModel
    
    bad_transitions = {
        'NAIVE': {
            'NAIVE': 0.1,
            'STABLE': 0.2,
            'ACTIVE': 0.3,
            'HIGHLY_ACTIVE': 0.1  # Sum = 0.7, not 1.0
        },
        'STABLE': {
            'NAIVE': 0.0,
            'STABLE': 0.7,
            'ACTIVE': 0.3,
            'HIGHLY_ACTIVE': 0.0
        },
        'ACTIVE': {
            'NAIVE': 0.0,
            'STABLE': 0.2,
            'ACTIVE': 0.7,
            'HIGHLY_ACTIVE': 0.1
        },
        'HIGHLY_ACTIVE': {
            'NAIVE': 0.0,
            'STABLE': 0.1,
            'ACTIVE': 0.2,
            'HIGHLY_ACTIVE': 0.7
        }
    }
    
    try:
        model = DiseaseModel(bad_transitions)
        print("    ❌ Should have failed with invalid probabilities!")
    except ValueError as e:
        print(f"    ✅ Correctly rejected: {e}")


if __name__ == '__main__':
    main()