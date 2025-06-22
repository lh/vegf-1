#!/usr/bin/env python3
"""
Test script for cost tracking functionality.

This script verifies that:
1. Cost configuration loads correctly
2. Enhanced cost tracker works with simulations
3. Task-based workload tracking functions properly
4. Results include cost data
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.economics.cost_config import CostConfig
from simulation_v2.economics.enhanced_cost_tracker import EnhancedCostTracker
from simulation_v2.engines.abs_engine_with_enhanced_costs import ABSEngineWithEnhancedCosts
from simulation_v2.core.disease_model import MarkovDiseaseModel
from simulation_v2.core.protocol import TimeBasedProtocol
from simulation_v2.clinical_improvements import ClinicalImprovements


def test_cost_configuration():
    """Test loading cost configuration."""
    print("\n1. Testing Cost Configuration Loading...")
    
    # Load NHS cost configuration
    cost_config_path = Path("protocols/cost_configs/nhs_hrg_aligned_2025.yaml")
    
    if not cost_config_path.exists():
        print(f"❌ Cost configuration not found: {cost_config_path}")
        return None
        
    try:
        cost_config = CostConfig.from_yaml(cost_config_path)
        print(f"✅ Loaded cost configuration: {cost_config.metadata['name']}")
        
        # Test drug costs
        biosimilar_cost = cost_config.get_drug_cost("eylea_2mg_biosimilar")
        originator_cost = cost_config.get_drug_cost("eylea_2mg_originator")
        
        print(f"   - Biosimilar cost: £{biosimilar_cost}")
        print(f"   - Originator cost: £{originator_cost}")
        print(f"   - Cost reduction: {(1 - biosimilar_cost/originator_cost)*100:.0f}%")
        
        # Test visit costs
        tae_cost = cost_config.get_visit_cost("tae_assessment")
        tnt_cost = cost_config.get_visit_cost("tnt_injection_only")
        
        print(f"   - T&E assessment cost: £{tae_cost}")
        print(f"   - T&T injection cost: £{tnt_cost}")
        
        return cost_config
        
    except Exception as e:
        print(f"❌ Failed to load cost configuration: {e}")
        return None


def test_enhanced_cost_tracker():
    """Test enhanced cost tracker functionality."""
    print("\n2. Testing Enhanced Cost Tracker...")
    
    # Load cost configuration
    cost_config = CostConfig.from_yaml("protocols/cost_configs/nhs_hrg_aligned_2025.yaml")
    
    # Create trackers for both protocols
    tae_tracker = EnhancedCostTracker(cost_config, "treat_and_extend")
    tnt_tracker = EnhancedCostTracker(cost_config, "fixed")
    
    print("✅ Created cost trackers for T&E and T&T protocols")
    
    # Test visit type determination
    from types import SimpleNamespace
    mock_patient = SimpleNamespace(id="P001", enrollment_date=None)
    
    # Test T&E visit types
    tae_initial = tae_tracker.determine_visit_type(mock_patient, 0)
    tae_loading = tae_tracker.determine_visit_type(mock_patient, 1)
    tae_loading_final = tae_tracker.determine_visit_type(mock_patient, 2)
    tae_maintenance = tae_tracker.determine_visit_type(mock_patient, 5)
    
    print(f"\n   T&E Visit Types:")
    print(f"   - Visit 0: {tae_initial.value}")
    print(f"   - Visit 1: {tae_loading.value}")
    print(f"   - Visit 2: {tae_loading_final.value}")
    print(f"   - Visit 5: {tae_maintenance.value}")
    
    # Test T&T visit types
    tnt_initial = tnt_tracker.determine_visit_type(mock_patient, 0)
    tnt_regular = tnt_tracker.determine_visit_type(mock_patient, 5, is_annual_assessment=False)
    tnt_annual = tnt_tracker.determine_visit_type(mock_patient, 5, is_annual_assessment=True)
    
    print(f"\n   T&T Visit Types:")
    print(f"   - Visit 0: {tnt_initial.value}")
    print(f"   - Regular visit: {tnt_regular.value}")
    print(f"   - Annual assessment: {tnt_annual.value}")
    
    # Test cost calculations
    tae_cost = tae_tracker.calculate_visit_cost(tae_maintenance, injection_given=True)
    tnt_inj_cost = tnt_tracker.calculate_visit_cost(tnt_regular, injection_given=True)
    tnt_assess_cost = tnt_tracker.calculate_visit_cost(tnt_annual, injection_given=False)
    
    print(f"\n   Cost Calculations:")
    print(f"   - T&E assessment with injection: £{tae_cost.total_cost}")
    print(f"   - T&T injection only: £{tnt_inj_cost.total_cost}")
    print(f"   - T&T annual assessment: £{tnt_assess_cost.total_cost}")
    
    return tae_tracker, tnt_tracker


def test_mini_simulation():
    """Test running a small simulation with cost tracking."""
    print("\n3. Testing Mini Simulation with Cost Tracking...")
    
    try:
        # Load T&E protocol
        protocol_path = Path("protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml")
        protocol_spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
        
        # Create disease model and protocol
        disease_model = MarkovDiseaseModel.from_spec(protocol_spec.disease_model)
        protocol = TimeBasedProtocol(protocol_spec)
        
        # Load clinical improvements
        improvements_config = Path("protocols/clinical_improvements/calibrated_tae_improvements.yaml")
        clinical_improvements = ClinicalImprovements.from_yaml(improvements_config)
        
        # Load cost configuration
        cost_config = CostConfig.from_yaml("protocols/cost_configs/nhs_hrg_aligned_2025.yaml")
        
        # Create enhanced engine
        engine = ABSEngineWithEnhancedCosts(
            disease_model=disease_model,
            protocol=protocol,
            protocol_spec=protocol_spec,
            n_patients=10,  # Small test
            seed=42,
            clinical_improvements=clinical_improvements,
            cost_config=cost_config,
            drug_type="eylea_2mg_biosimilar"
        )
        
        print("✅ Created enhanced ABS engine with cost tracking")
        
        # Run mini simulation
        results = engine.run(duration_years=1.0)
        
        print(f"✅ Simulation completed with {len(results.patient_histories)} patients")
        
        # Check cost tracking results
        if hasattr(results, 'cost_tracker') and results.cost_tracker:
            ce_metrics = results.cost_effectiveness
            workload_df = results.cost_tracker.get_workload_summary()
            
            print(f"\n   Cost Effectiveness Metrics:")
            print(f"   - Total cost: £{ce_metrics['total_cost']:,.0f}")
            print(f"   - Cost per patient: £{ce_metrics['cost_per_patient']:,.0f}")
            print(f"   - Total injections: {ce_metrics['total_injections']}")
            print(f"   - Cost per injection: £{ce_metrics['cost_per_injection']:,.0f}")
            
            if not workload_df.empty:
                print(f"\n   Workload Summary:")
                print(f"   - Months tracked: {len(workload_df)}")
                print(f"   - Total visits: {workload_df['total_visits'].sum()}")
                print(f"   - Total injection tasks: {workload_df['injections'].sum()}")
                print(f"   - Total decision tasks: {workload_df['decision_visits'].sum()}")
                
            # Test cost breakdown
            breakdown = results.cost_tracker.get_cost_breakdown()
            print(f"\n   Cost Breakdown:")
            for component, cost in breakdown.items():
                if component != 'total_costs':
                    pct = (cost / breakdown['total_costs'] * 100) if breakdown['total_costs'] > 0 else 0
                    print(f"   - {component}: £{cost:,.0f} ({pct:.1f}%)")
                    
        else:
            print("❌ No cost tracking data in results")
            
        return results
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_workload_visualization():
    """Test workload visualization components."""
    print("\n4. Testing Workload Visualization Components...")
    
    try:
        from ape.components.cost_tracking.workload_visualizer import WorkloadVisualizer, TaskType
        
        print("✅ Imported workload visualizer")
        
        # Test task time estimates
        print("\n   Task Duration Estimates:")
        for task_type in TaskType:
            duration = WorkloadVisualizer.TASK_DURATIONS[task_type]
            print(f"   - {task_type.value}: {duration} minutes")
            
        # Create visualizer (without data for now)
        viz = WorkloadVisualizer()
        print("✅ Created workload visualizer instance")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test workload visualization: {e}")
        return False


def test_cost_configuration_widget():
    """Test cost configuration UI widget."""
    print("\n5. Testing Cost Configuration Widget...")
    
    try:
        from ape.components.cost_tracking.cost_configuration_widget import CostConfigurationWidget
        
        widget = CostConfigurationWidget()
        print("✅ Created cost configuration widget")
        
        # Test loading default configuration
        if widget.default_config:
            print(f"✅ Loaded default config: {widget.default_config.metadata['name']}")
            
            # Test getting custom config
            custom_config = widget.get_custom_config("eylea_2mg_biosimilar", 400.0)
            if custom_config:
                print("✅ Created custom configuration with adjusted drug price")
                print(f"   - Original price: £{widget.default_config.get_drug_cost('eylea_2mg_biosimilar')}")
                print(f"   - Custom price: £{custom_config.get_drug_cost('eylea_2mg_biosimilar')}")
        else:
            print("❌ Failed to load default configuration")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to test cost configuration widget: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("COST TRACKING FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test 1: Cost Configuration
    cost_config = test_cost_configuration()
    
    # Test 2: Enhanced Cost Tracker
    if cost_config:
        tae_tracker, tnt_tracker = test_enhanced_cost_tracker()
    
    # Test 3: Mini Simulation
    results = test_mini_simulation()
    
    # Test 4: Workload Visualization
    test_workload_visualization()
    
    # Test 5: Cost Configuration Widget
    test_cost_configuration_widget()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if cost_config and results:
        print("✅ All core functionality tests passed!")
        print("\nNext steps:")
        print("1. Test with full T&E and T&T simulations")
        print("2. Create cost analysis page in Streamlit")
        print("3. Validate against NHS cost calculator targets")
    else:
        print("❌ Some tests failed - check output above")


if __name__ == "__main__":
    main()