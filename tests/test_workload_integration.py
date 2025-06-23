"""
Integration test for workload analysis functionality.

This test mimics exactly what the UI does when running simulations
with resource tracking, ensuring the workload analysis logic works
correctly end-to-end.

Run with: pytest tests/test_workload_integration.py -v
or directly: python tests/test_workload_integration.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from ape.core.simulation_runner import SimulationRunner
from ape.utils.state_helpers import add_simulation_to_registry


def run_simulation_with_resources(protocol_name: str, n_patients: int, duration_years: float, seed: int):
    """Run a simulation with resource tracking enabled - mimicking UI behavior."""
    print(f"\n{'='*60}")
    print(f"Running simulation: {protocol_name}")
    print(f"Parameters: {n_patients} patients, {duration_years} years, seed={seed}")
    print(f"{'='*60}")
    
    # Step 1: Load protocol (as UI does)
    print("\n1. Loading protocol...")
    project_root = Path(__file__).parent.parent
    protocol_dir = project_root / "protocols" / "v2_time_based"
    protocol_file = protocol_dir / f"{protocol_name}.yaml"
    
    if not protocol_file.exists():
        print(f"ERROR: Protocol file '{protocol_file}' not found!")
        return None
    
    try:
        # UI loads TimeBasedProtocolSpecification for time-based protocols
        protocol_spec = TimeBasedProtocolSpecification.from_yaml(protocol_file)
        print(f"✓ Protocol loaded: {protocol_spec.name}")
    except Exception as e:
        print(f"ERROR loading protocol: {e}")
        return None
    
    # Step 2: Create runner with resource tracking (as UI does)
    print("\n2. Creating simulation runner with resource tracking...")
    try:
        # This is exactly how UI creates the runner
        runner = SimulationRunner(protocol_spec, enable_resource_tracking=True)
        print("✓ Runner created with resource tracking enabled")
    except Exception as e:
        print(f"ERROR creating runner: {e}")
        return None
    
    # Step 3: Run simulation (as UI does)
    print(f"\n3. Running simulation for {duration_years} years...")
    try:
        # UI calls runner.run with these parameters
        results = runner.run(
            engine_type='abs',
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            show_progress=True,
            recruitment_mode="Fixed Total"
        )
        print(f"✓ Simulation complete!")
        print(f"  - Type: {type(results)}")
        print(f"  - Has resource tracker: {hasattr(results, 'resource_tracker') and results.resource_tracker is not None}")
    except Exception as e:
        print(f"ERROR running simulation: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 4: Add to registry (as UI does)
    print("\n4. Adding to simulation registry...")
    try:
        sim_id = add_simulation_to_registry(
            protocol_name=protocol_spec.name,
            n_patients=n_patients,
            duration_years=duration_years,
            engine_type='abs',
            seed=seed,
            results_path=str(results.data_path)
        )
        print(f"✓ Added to registry with ID: {sim_id}")
    except Exception as e:
        print(f"ERROR adding to registry: {e}")
    
    return results


def test_workload_analysis(results):
    """Test the workload analysis logic as called from the UI."""
    print("\n" + "="*60)
    print("Testing Workload Analysis Logic")
    print("="*60)
    
    if not hasattr(results, 'resource_tracker') or not results.resource_tracker:
        print("ERROR: No resource tracker available!")
        print(f"Results type: {type(results)}")
        print(f"Results attributes: {dir(results)}")
        return False
    
    resource_tracker = results.resource_tracker
    
    # Test 1: Get workload summary
    print("\n1. Getting workload summary...")
    try:
        workload_summary = resource_tracker.get_workload_summary()
        print("✓ Workload summary retrieved:")
        print(f"  - Total visits: {workload_summary['total_visits']:,}")
        print(f"  - Roles tracked: {list(workload_summary['average_daily_demand'].keys())}")
        for role, demand in workload_summary['average_daily_demand'].items():
            print(f"    - {role}: avg {demand:.1f} procedures/day")
    except Exception as e:
        print(f"ERROR getting workload summary: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Get total costs
    print("\n2. Getting total costs...")
    try:
        total_costs = resource_tracker.get_total_costs()
        print("✓ Total costs retrieved:")
        print(f"  - Total: £{total_costs['total']:,.0f}")
        for category, cost in total_costs.items():
            if category != 'total':
                print(f"  - {category}: £{cost:,.0f}")
    except Exception as e:
        print(f"ERROR getting total costs: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Get daily usage patterns
    print("\n3. Getting daily usage patterns...")
    try:
        all_dates = resource_tracker.get_all_dates_with_visits()
        print(f"✓ Found {len(all_dates)} days with visits")
        
        # Sample first few days
        for date in list(all_dates)[:5]:
            daily_usage = resource_tracker.daily_usage[date]
            print(f"  - {date}: {dict(daily_usage)}")
    except Exception as e:
        print(f"ERROR getting daily usage: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Calculate sessions needed
    print("\n4. Testing session calculations...")
    try:
        if all_dates:
            sample_date = all_dates[0]
            for role in resource_tracker.roles:
                sessions = resource_tracker.calculate_sessions_needed(sample_date, role)
                print(f"  - {role} on {sample_date}: {sessions:.2f} sessions needed")
    except Exception as e:
        print(f"ERROR calculating sessions: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Identify bottlenecks
    print("\n5. Identifying bottlenecks...")
    try:
        bottlenecks = resource_tracker.identify_bottlenecks()
        print(f"✓ Found {len(bottlenecks)} bottleneck days")
        if bottlenecks:
            # Show first few
            for b in bottlenecks[:3]:
                print(f"  - {b['date']}: {b['role']} needed {b['sessions_needed']:.1f} sessions")
    except Exception as e:
        print(f"ERROR identifying bottlenecks: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_workload_with_smaller_dataset():
    """Test with smaller dataset for faster CI/CD runs."""
    protocol_name = "aflibercept_tae_8week_min_time_based"
    
    # Smaller parameters for quick testing
    n_patients = 100
    duration_years = 1
    seed = 42
    
    # Run simulation
    results = run_simulation_with_resources(protocol_name, n_patients, duration_years, seed)
    assert results is not None, "Simulation failed"
    
    # Test workload analysis
    success = test_workload_analysis(results)
    assert success, "Workload analysis tests failed"


def main():
    """Run the full test for both protocols."""
    protocols = [
        "aflibercept_tae_8week_min_time_based",  # TAE not TAU
        "aflibercept_treat_and_treat_time_based"
    ]
    
    # Full parameters to match UI test
    n_patients = 2000
    duration_years = 5
    seed = 42
    
    all_success = True
    
    for protocol_name in protocols:
        # Run simulation
        results = run_simulation_with_resources(protocol_name, n_patients, duration_years, seed)
        
        if results:
            # Test workload analysis
            success = test_workload_analysis(results)
            if success:
                print(f"\n✅ All tests passed for {protocol_name}!")
            else:
                print(f"\n❌ Some tests failed for {protocol_name}")
                all_success = False
        else:
            print(f"\n❌ Simulation failed for {protocol_name}")
            all_success = False
    
    print("\n" + "="*60)
    if all_success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60)


if __name__ == "__main__":
    main()