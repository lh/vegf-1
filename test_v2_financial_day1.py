#!/usr/bin/env python3
"""Test Day 1 V2 financial implementation."""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from simulation_v2.economics import (
    CostConfig, CostAnalyzerV2, CostTrackerV2,
    FinancialResults, CostBreakdown, CostEvent
)
from simulation_v2.core.disease_model import DiseaseState


def test_cost_analyzer_v2():
    """Test V2 cost analyzer with V2 visit format."""
    
    print("\n=== Testing V2 Cost Analyzer ===")
    
    # Load cost config
    cost_config = CostConfig.from_yaml(Path("protocols/cost_configs/nhs_standard_2025.yaml"))
    analyzer = CostAnalyzerV2(cost_config)
    
    # Create a V2-format visit
    v2_visit = {
        'date': datetime(2024, 1, 15),  # V2 uses datetime
        'disease_state': DiseaseState.ACTIVE,  # V2 uses enum
        'treatment_given': True,
        'vision': 65,
        'metadata': {
            'phase': 'loading',
            'components_performed': ['injection', 'vision_test', 'oct_scan'],
            'drug': 'eylea_2mg',
            'visit_subtype': 'loading_regular_visit'
        }
    }
    
    # Analyze visit
    cost_event = analyzer.analyze_visit(v2_visit)
    
    print(f"Visit date: {cost_event.date}")
    print(f"Total cost: £{cost_event.amount:,.2f}")
    print(f"Drug cost: £{cost_event.metadata['drug_cost']:,.2f}")
    print(f"Visit cost: £{cost_event.metadata['visit_cost']:,.2f}")
    print(f"Disease state: {cost_event.metadata['disease_state']}")
    
    return cost_event


def test_financial_results():
    """Test FinancialResults data structure."""
    
    print("\n=== Testing Financial Results ===")
    
    # Create sample results
    results = FinancialResults(
        total_cost=250000.0,
        total_patients=100,
        cost_per_patient=2500.0,
        total_injections=900,
        cost_per_injection=277.78,
        total_va_change=150.0,
        cost_per_letter_gained=1666.67,
        cost_breakdown=CostBreakdown(
            by_type={'visit': 200000.0, 'drug': 50000.0},
            by_phase={'loading': 100000.0, 'maintenance': 150000.0}
        ),
        patient_costs={},
        cost_config_name="NHS Standard 2025"
    )
    
    print(results.get_summary_text())
    
    # Test serialization
    results_dict = results.to_dict()
    print(f"\nSerialized keys: {list(results_dict.keys())}")
    
    return results


def test_cost_tracker_v2():
    """Test minimal cost tracker functionality."""
    
    print("\n=== Testing Cost Tracker V2 ===")
    
    # Create analyzer and tracker
    cost_config = CostConfig.from_yaml(Path("protocols/cost_configs/nhs_standard_2025.yaml"))
    analyzer = CostAnalyzerV2(cost_config)
    tracker = CostTrackerV2(analyzer)
    
    # Manually add some test events
    test_event = CostEvent(
        date=datetime(2024, 1, 15),
        patient_id='P0001',
        event_type='visit',
        category='loading_regular_visit',
        amount=900.0,
        components={'injection': 150.0, 'vision_test': 25.0, 'oct_scan': 75.0},
        metadata={'drug_cost': 800.0, 'visit_cost': 100.0, 'phase': 'loading'}
    )
    
    tracker.events['P0001'] = [test_event]
    
    # Get financial results
    results = tracker.get_financial_results("NHS Standard 2025")
    
    print(f"Total cost: £{results.total_cost:,.2f}")
    print(f"Total patients: {results.total_patients}")
    print(f"Cost breakdown by type: {results.cost_breakdown.by_type}")
    
    return results


def main():
    """Run all Day 1 tests."""
    
    print("="*60)
    print("Day 1: Core V2 Compatibility Tests")
    print("="*60)
    
    try:
        # Test analyzer
        cost_event = test_cost_analyzer_v2()
        
        # Test results
        results = test_financial_results()
        
        # Test tracker
        tracker_results = test_cost_tracker_v2()
        
        print("\n✅ All Day 1 tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()