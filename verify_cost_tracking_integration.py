#!/usr/bin/env python3
"""
Quick verification that cost tracking is properly integrated.
"""

import sys
from pathlib import Path

def check_imports():
    """Check if all cost tracking modules can be imported."""
    print("Checking cost tracking integration...")
    print("=" * 50)
    
    modules_to_check = [
        ("Core cost config", "simulation_v2.economics.cost_config", "CostConfig"),
        ("Enhanced cost tracker", "simulation_v2.economics.enhanced_cost_tracker", "EnhancedCostTracker"),
        ("Cost-aware ABS engine", "simulation_v2.engines.abs_engine_with_enhanced_costs", "ABSEngineWithEnhancedCosts"),
        ("Cost configuration widget", "ape.components.cost_tracking.cost_configuration_widget", "CostConfigurationWidget"),
        ("Workload visualizer", "ape.components.cost_tracking.workload_visualizer", "WorkloadVisualizer"),
        ("Cost analysis dashboard", "ape.components.cost_tracking.cost_analysis_dashboard", "CostAnalysisDashboard"),
        ("Cost-aware runner", "ape.core.simulation_runner_with_costs", "SimulationRunnerWithCosts"),
        ("Cost-aware UI", "ape.components.simulation_ui_v2_with_costs", "render_enhanced_parameter_inputs_with_costs"),
    ]
    
    all_good = True
    for name, module_path, class_name in modules_to_check:
        try:
            module_parts = module_path.split('.')
            exec(f"from {module_path} import {class_name}")
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {e}")
            all_good = False
    
    return all_good

def check_files():
    """Check if key files exist."""
    print("\nChecking key files...")
    print("=" * 50)
    
    files_to_check = [
        "simulation_v2/economics/enhanced_cost_tracker.py",
        "simulation_v2/engines/abs_engine_with_enhanced_costs.py",
        "ape/components/cost_tracking/cost_configuration_widget.py",
        "ape/components/cost_tracking/workload_visualizer.py",
        "ape/components/cost_tracking/cost_analysis_dashboard.py",
        "ape/core/simulation_runner_with_costs.py",
        "ape/components/simulation_ui_v2_with_costs.py",
        "pages/5_Cost_Analysis.py",
        "protocols/cost_configs/nhs_hrg_aligned_2025.yaml",
    ]
    
    all_good = True
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            all_good = False
    
    return all_good

def check_simulations_page():
    """Check if simulations page has cost tracking support."""
    print("\nChecking Simulations page integration...")
    print("=" * 50)
    
    sim_page = Path("pages/2_Simulations.py")
    if not sim_page.exists():
        print("❌ Simulations page not found")
        return False
    
    content = sim_page.read_text()
    
    checks = [
        ("Cost tracking imports", "COST_TRACKING_AVAILABLE"),
        ("Cost config handling", "cost_config"),
        ("Cost-aware runner", "SimulationRunnerWithCosts"),
        ("Cost in simulation data", "'cost_tracking':")
    ]
    
    all_good = True
    for check_name, search_text in checks:
        if search_text in content:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name} - NOT FOUND")
            all_good = False
    
    return all_good

def main():
    """Run all checks."""
    print("COST TRACKING INTEGRATION VERIFICATION")
    print("=" * 50)
    
    # Run checks
    imports_ok = check_imports()
    files_ok = check_files()
    integration_ok = check_simulations_page()
    
    # Summary
    print("\nSUMMARY")
    print("=" * 50)
    
    if imports_ok and files_ok and integration_ok:
        print("✅ Cost tracking is fully integrated and ready to use!")
        print("\nTo use cost tracking:")
        print("1. Go to the Simulations page")
        print("2. Enable 'Cost Tracking' checkbox")
        print("3. Select drug type (default: Eylea Biosimilar £355)")
        print("4. Run simulation with T&E or T&T time-based protocol")
        print("5. View results in the Cost Analysis page")
    else:
        print("❌ Some components are missing or not properly integrated")
        print("\nIssues found:")
        if not imports_ok:
            print("- Module import errors")
        if not files_ok:
            print("- Missing files")
        if not integration_ok:
            print("- Simulations page not properly updated")

if __name__ == "__main__":
    main()