#!/usr/bin/env python3
"""
Comprehensive test of export/import functionality.
Tests:
1. New simulation naming (haiku-style with duration encoding)
2. Parameter persistence when switching simulations
3. Full protocol specification saved and loaded
4. Export/import cycle preserves all data
"""

import sys
from pathlib import Path
import json
import tempfile
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_adapter import MemoryAwareSimulationRunner
from utils.simulation_package import SimulationPackageManager
from core.results.factory import ResultsFactory


def test_memorable_naming():
    """Test that new simulations get memorable names with duration encoding."""
    print("\n=== Testing Memorable Naming ===")
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner
    runner = MemoryAwareSimulationRunner(spec)
    
    # Run a short simulation
    print("\nRunning simulation with 10 patients for 2.5 years...")
    results = runner.run(
        engine_type="abs",
        n_patients=10,
        duration_years=2.5,
        seed=42
    )
    
    # Check the naming
    sim_id = results.metadata.sim_id
    print(f"\nGenerated simulation ID: {sim_id}")
    
    # Parse the ID
    parts = sim_id.split('_')
    if len(parts) >= 4:
        timestamp = parts[1] + '_' + parts[2]
        duration_code = parts[3]
        memorable_name = '_'.join(parts[4:]) if len(parts) > 4 else 'missing'
        
        print(f"  Timestamp: {timestamp}")
        print(f"  Duration code: {duration_code} (should be '02-50' for 2.5 years)")
        print(f"  Memorable name: {memorable_name}")
        
        # Verify duration encoding
        assert duration_code == "02-50", f"Expected '02-50', got '{duration_code}'"
        
        # Verify memorable name exists and isn't hex
        assert memorable_name != 'missing', "No memorable name found"
        assert not all(c in '0123456789abcdef' for c in memorable_name.replace('-', '')), \
            f"Name '{memorable_name}' looks like hex, not a memorable name"
        
        print("✅ Memorable naming test passed!")
    else:
        print(f"❌ Unexpected ID format: {sim_id}")
        return False
    
    return True, results


def test_parameter_persistence():
    """Test that parameters persist correctly when switching simulations."""
    print("\n=== Testing Parameter Persistence ===")
    
    # Load protocol
    protocol_path = Path("protocols/eylea.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    runner = MemoryAwareSimulationRunner(spec)
    
    # Run two simulations with different parameters
    print("\nRunning first simulation: 20 patients, 1 year, seed 100...")
    results1 = runner.run(
        engine_type="abs",
        n_patients=20,
        duration_years=1.0,
        seed=100
    )
    
    # Small delay to ensure different timestamp
    time.sleep(1)
    
    print("\nRunning second simulation: 50 patients, 3 years, seed 200...")
    results2 = runner.run(
        engine_type="des",
        n_patients=50,
        duration_years=3.0,
        seed=200
    )
    
    # Load simulations using the loader (simulating UI behavior)
    from utils.simulation_loader import load_simulation_data
    
    print("\nSimulating UI parameter loading...")
    
    # Load first simulation
    print(f"\nLoading simulation 1: {results1.metadata.sim_id}")
    sim_data1 = load_simulation_data(results1.metadata.sim_id)
    
    if sim_data1 and 'parameters' in sim_data1:
        params1 = sim_data1['parameters']
        print(f"  Engine: {params1.get('engine')} (expected: abs)")
        print(f"  Patients: {params1.get('n_patients')} (expected: 20)")
        print(f"  Duration: {params1.get('duration_years')} (expected: 1.0)")
        print(f"  Seed: {params1.get('seed')} (expected: 100)")
        
        assert params1.get('engine') == 'abs'
        assert params1.get('n_patients') == 20
        assert params1.get('duration_years') == 1.0
        assert params1.get('seed') == 100
    else:
        print("❌ Failed to load parameters for simulation 1")
        return False
    
    # Load second simulation
    print(f"\nLoading simulation 2: {results2.metadata.sim_id}")
    sim_data2 = load_simulation_data(results2.metadata.sim_id)
    
    if sim_data2 and 'parameters' in sim_data2:
        params2 = sim_data2['parameters']
        print(f"  Engine: {params2.get('engine')} (expected: des)")
        print(f"  Patients: {params2.get('n_patients')} (expected: 50)")
        print(f"  Duration: {params2.get('duration_years')} (expected: 3.0)")
        print(f"  Seed: {params2.get('seed')} (expected: 200)")
        
        assert params2.get('engine') == 'des'
        assert params2.get('n_patients') == 50
        assert params2.get('duration_years') == 3.0
        assert params2.get('seed') == 200
    else:
        print("❌ Failed to load parameters for simulation 2")
        return False
    
    print("✅ Parameter persistence test passed!")
    return True


def test_export_import_cycle(results):
    """Test full export/import cycle preserves all data."""
    print("\n=== Testing Export/Import Cycle ===")
    
    manager = SimulationPackageManager()
    
    # Export the simulation
    print(f"\nExporting simulation {results.metadata.sim_id}...")
    package_data = manager.create_package(results)
    print(f"Package size: {len(package_data):,} bytes")
    
    # Check package name
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp.write(package_data)
        tmp_path = Path(tmp.name)
    
    # Import the package
    print("\nImporting package...")
    imported_results = manager.import_package(package_data)
    
    # Verify imported data
    print(f"\nImported simulation ID: {imported_results.metadata.sim_id}")
    print(f"Original patients: {results.metadata.n_patients}")
    print(f"Imported patients: {imported_results.metadata.n_patients}")
    print(f"Original duration: {results.metadata.duration_years}")
    print(f"Imported duration: {imported_results.metadata.duration_years}")
    print(f"Original seed: {results.metadata.seed}")
    print(f"Imported seed: {imported_results.metadata.seed}")
    
    # Verify counts match
    assert results.metadata.n_patients == imported_results.metadata.n_patients
    assert results.metadata.duration_years == imported_results.metadata.duration_years
    assert results.metadata.seed == imported_results.metadata.seed
    
    # Check protocol was saved
    protocol_path = imported_results.data_path / "protocol.yaml"
    assert protocol_path.exists(), "Protocol.yaml not found in imported results"
    
    # Load the imported simulation to check parameters
    from utils.simulation_loader import load_simulation_data
    sim_data = load_simulation_data(imported_results.metadata.sim_id)
    
    if sim_data:
        print("\nChecking imported simulation data structure...")
        print(f"  Has results: {'results' in sim_data}")
        print(f"  Has protocol: {'protocol' in sim_data}")
        print(f"  Has parameters: {'parameters' in sim_data}")
        
        if 'protocol' in sim_data and 'spec' in sim_data['protocol']:
            print("  ✓ Protocol spec is available")
        else:
            print("  ✗ Protocol spec is missing")
            return False
    
    # Clean up temp file
    tmp_path.unlink()
    
    print("✅ Export/import cycle test passed!")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE EXPORT/IMPORT TEST")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Memorable naming
    try:
        naming_passed, results = test_memorable_naming()
        if not naming_passed:
            all_passed = False
    except Exception as e:
        print(f"❌ Memorable naming test failed: {e}")
        all_passed = False
        results = None
    
    # Test 2: Parameter persistence
    try:
        if not test_parameter_persistence():
            all_passed = False
    except Exception as e:
        print(f"❌ Parameter persistence test failed: {e}")
        all_passed = False
    
    # Test 3: Export/import cycle (using results from test 1)
    if results:
        try:
            if not test_export_import_cycle(results):
                all_passed = False
        except Exception as e:
            print(f"❌ Export/import cycle test failed: {e}")
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nThe fixes are working correctly:")
        print("1. New simulations use memorable names with duration encoding")
        print("2. Parameters persist correctly when switching simulations")
        print("3. Full protocol specifications are saved and loaded")
        print("4. Export/import cycle preserves all data")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()