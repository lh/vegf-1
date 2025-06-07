#!/usr/bin/env python3
"""Debug script to test import functionality"""

import sys
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent))

from utils.simulation_package import SimulationPackageManager
from core.results.factory import ResultsFactory

def test_export_import():
    """Test exporting and then importing a package"""
    # First, get a recent simulation to export
    results_dir = ResultsFactory.DEFAULT_RESULTS_DIR
    if not results_dir.exists():
        print("No simulation results directory")
        return
        
    sim_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('sim_')])
    if not sim_dirs:
        print("No simulations found")
        return
    
    # Use the most recent simulation
    sim_path = sim_dirs[-1]
    print(f"Loading simulation: {sim_path.name}")
    
    # Load the simulation
    try:
        results = ResultsFactory.load_results(sim_path)
        print(f"Loaded simulation with {results.get_patient_count()} patients")
    except Exception as e:
        print(f"Failed to load simulation: {e}")
        return
    
    # Export it
    manager = SimulationPackageManager()
    try:
        print("\nExporting package...")
        package_data = manager.create_package(results)
        print(f"Package created, size: {len(package_data):,} bytes")
        
        # Save it temporarily
        temp_package = Path("test_package.zip")
        with open(temp_package, 'wb') as f:
            f.write(package_data)
        print(f"Saved to {temp_package}")
        
    except Exception as e:
        print(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Now try to import it back
    try:
        print("\nImporting package...")
        imported_results = manager.import_package(package_data)
        print(f"Import successful! New sim_id: {imported_results.metadata.sim_id}")
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_export_import()