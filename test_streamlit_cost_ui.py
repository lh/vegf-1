#!/usr/bin/env python
"""
Test script to verify cost tracking UI integration in Streamlit.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_cost_tracking_ui():
    """Test that cost tracking components can be imported and used."""
    
    print("Testing Cost Tracking UI Integration")
    print("=" * 60)
    
    # Test 1: Import the simulation UI with costs
    try:
        from ape.components.simulation_ui_v2_with_costs import SimulationUIV2WithCosts
        print("✅ SimulationUIV2WithCosts imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SimulationUIV2WithCosts: {e}")
        return False
    
    # Test 2: Import cost tracking components
    try:
        from ape.components.cost_tracking.cost_configuration_widget import CostConfigurationWidget
        from ape.components.cost_tracking.workload_visualizer import WorkloadVisualizerWidget
        from ape.components.cost_tracking.cost_analysis_dashboard import CostAnalysisDashboard
        print("✅ All cost tracking widgets imported successfully")
    except Exception as e:
        print(f"❌ Failed to import cost tracking widgets: {e}")
        return False
    
    # Test 3: Check if the main Simulations page has cost tracking
    try:
        # Read the simulations page to check for cost tracking
        sim_page = Path("pages/2_Simulations.py").read_text()
        if "COST_TRACKING_AVAILABLE" in sim_page and "SimulationUIV2WithCosts" in sim_page:
            print("✅ Simulations page has cost tracking integrated")
        else:
            print("❌ Simulations page missing cost tracking integration")
            return False
    except Exception as e:
        print(f"❌ Failed to check Simulations page: {e}")
        return False
    
    # Test 4: Verify Cost Analysis page exists
    try:
        cost_analysis_page = Path("pages/5_Cost_Analysis.py")
        if cost_analysis_page.exists():
            print("✅ Cost Analysis page exists")
        else:
            print("❌ Cost Analysis page not found")
            return False
    except Exception as e:
        print(f"❌ Failed to check Cost Analysis page: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All UI integration tests passed!")
    print("\nTo test the full functionality:")
    print("1. Run: streamlit run app.py")
    print("2. Go to the Simulations page")
    print("3. Enable 'Cost Tracking' checkbox")
    print("4. Run a simulation with T&E or T&T protocol")
    print("5. Check the Cost Analysis page for results")
    
    return True

if __name__ == "__main__":
    success = test_cost_tracking_ui()
    sys.exit(0 if success else 1)