"""
Test that protocols with clinical improvements work correctly.
"""

import sys
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner


def test_protocol_loads_with_improvements():
    """Test that a protocol with improvements can be loaded."""
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea.yaml"
    
    # Load protocol
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Check that clinical improvements exist but are disabled
    assert hasattr(spec, 'clinical_improvements')
    assert spec.clinical_improvements is not None
    assert spec.clinical_improvements['enabled'] is False
    
    print("✅ Protocol loaded successfully with clinical improvements (disabled)")


def test_simulation_with_improvements_disabled():
    """Test running simulation with improvements disabled."""
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea.yaml"
    
    # Load protocol
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = SimulationRunner(spec)
    
    # Verify improvements are not active
    assert runner.clinical_improvements is None
    
    # Run small simulation
    results = runner.run(
        engine_type='abs',
        n_patients=10,
        duration_years=1.0,
        seed=42
    )
    
    print(f"✅ Simulation ran with improvements disabled")
    print(f"   Total injections: {results.total_injections}")
    print(f"   Final vision mean: {results.final_vision_mean:.1f}")


def test_simulation_with_improvements_enabled():
    """Test running simulation with improvements enabled."""
    # Create a temporary protocol with improvements enabled
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea.yaml"
    
    # Load and modify protocol
    with open(protocol_path) as f:
        data = yaml.safe_load(f)
    
    # Enable improvements
    data['clinical_improvements']['enabled'] = True
    
    # Save to temporary file
    temp_path = Path(__file__).parent / "test_protocol_with_improvements.yaml"
    with open(temp_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)
    
    try:
        # Load modified protocol
        spec = ProtocolSpecification.from_yaml(temp_path)
        
        # Create runner
        runner = SimulationRunner(spec)
        
        # Verify improvements are active
        assert runner.clinical_improvements is not None
        
        # Run small simulation
        results = runner.run(
            engine_type='abs',
            n_patients=10,
            duration_years=1.0,
            seed=42
        )
        
        print(f"✅ Simulation ran with improvements enabled")
        print(f"   Total injections: {results.total_injections}")
        print(f"   Final vision mean: {results.final_vision_mean:.1f}")
        
        # Check that some improvements were logged
        improvement_logs = [log for log in runner.audit_log 
                          if log['event'] == 'clinical_improvements_enabled']
        assert len(improvement_logs) > 0
        print(f"   Clinical improvements were logged in audit trail")
        
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def main():
    """Run all tests."""
    print("Testing Protocol Clinical Improvements Integration")
    print("=" * 50)
    
    test_protocol_loads_with_improvements()
    test_simulation_with_improvements_disabled()
    test_simulation_with_improvements_enabled()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()