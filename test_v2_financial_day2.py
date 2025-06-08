#!/usr/bin/env python3
"""Test Day 2 V2 financial implementation - Native V2 Integration."""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.engines.des_engine import DESEngine
from simulation_v2.economics import (
    CostConfig, CostAnalyzerV2, CostTrackerV2,
    create_v2_cost_enhancer
)


def test_patient_with_enhancer():
    """Test Patient class with cost metadata enhancer."""
    
    print("\n=== Testing Patient with Cost Enhancer ===")
    
    # Create cost enhancer
    cost_config = CostConfig.from_yaml(Path("protocols/cost_configs/nhs_standard_2025.yaml"))
    enhancer = create_v2_cost_enhancer(cost_config, "Eylea Treat and Extend")
    
    # Import Patient directly to test
    from simulation_v2.core.patient import Patient
    from simulation_v2.core.disease_model import DiseaseState
    
    # Create patient with enhancer
    patient = Patient("P0001", baseline_vision=70, visit_metadata_enhancer=enhancer)
    
    # Record a visit
    patient.record_visit(
        date=datetime(2024, 1, 15),
        disease_state=DiseaseState.ACTIVE,
        treatment_given=True,
        vision=68
    )
    
    # Check the visit was enhanced
    visit = patient.visit_history[0]
    print(f"Visit date: {visit['date']}")
    print(f"Treatment given: {visit['treatment_given']}")
    print(f"Metadata keys: {list(visit.get('metadata', {}).keys())}")
    
    if 'metadata' in visit:
        metadata = visit['metadata']
        print(f"Phase: {metadata.get('phase')}")
        print(f"Components: {metadata.get('components_performed')}")
        print(f"Drug: {metadata.get('drug')}")
        print(f"Visit subtype: {metadata.get('visit_subtype')}")
    
    return patient


def test_engine_with_enhancer(engine_type='abs'):
    """Test engine with cost enhancer integration."""
    
    print(f"\n=== Testing {engine_type.upper()} Engine with Cost Enhancer ===")
    
    # Load protocol
    protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Create disease model
    disease_model = DiseaseModel(
        transition_probabilities=protocol_spec.disease_transitions,
        treatment_effect_multipliers=protocol_spec.treatment_effect_on_transitions,
        seed=42
    )
    
    # Create protocol
    protocol = StandardProtocol(
        min_interval_days=protocol_spec.min_interval_days,
        max_interval_days=protocol_spec.max_interval_days,
        extension_days=protocol_spec.extension_days,
        shortening_days=protocol_spec.shortening_days
    )
    
    # Create cost enhancer
    cost_config = CostConfig.from_yaml(Path("protocols/cost_configs/nhs_standard_2025.yaml"))
    enhancer = create_v2_cost_enhancer(cost_config, protocol_spec.name)
    
    # Create engine with enhancer
    if engine_type == 'abs':
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=5,  # Small test
            seed=42,
            visit_metadata_enhancer=enhancer
        )
    else:
        engine = DESEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=5,
            seed=42,
            visit_metadata_enhancer=enhancer
        )
    
    # Run short simulation
    results = engine.run(duration_years=0.5)  # 6 months
    
    print(f"Simulation complete: {results.patient_count} patients")
    
    # Check a patient's visits
    first_patient = list(results.patient_histories.values())[0]
    print(f"\nFirst patient ({first_patient.id}) visits: {len(first_patient.visit_history)}")
    
    if first_patient.visit_history:
        first_visit = first_patient.visit_history[0]
        print(f"First visit has metadata: {'metadata' in first_visit}")
        if 'metadata' in first_visit:
            print(f"Metadata keys: {list(first_visit['metadata'].keys())[:5]}...")
    
    return results


def test_end_to_end_cost_analysis():
    """Test complete end-to-end cost analysis with V2."""
    
    print("\n=== Testing End-to-End Cost Analysis ===")
    
    # Load protocol and cost config
    protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
    protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
    cost_config = CostConfig.from_yaml(Path("protocols/cost_configs/nhs_standard_2025.yaml"))
    
    # Create components
    disease_model = DiseaseModel(
        transition_probabilities=protocol_spec.disease_transitions,
        treatment_effect_multipliers=protocol_spec.treatment_effect_on_transitions,
        seed=42
    )
    
    protocol = StandardProtocol(
        min_interval_days=protocol_spec.min_interval_days,
        max_interval_days=protocol_spec.max_interval_days,
        extension_days=protocol_spec.extension_days,
        shortening_days=protocol_spec.shortening_days
    )
    
    enhancer = create_v2_cost_enhancer(cost_config, protocol_spec.name)
    
    # Run simulation with cost tracking
    engine = ABSEngine(
        disease_model=disease_model,
        protocol=protocol,
        n_patients=10,
        seed=42,
        visit_metadata_enhancer=enhancer
    )
    
    results = engine.run(duration_years=1.0)
    
    # Analyze costs
    analyzer = CostAnalyzerV2(cost_config)
    tracker = CostTrackerV2(analyzer)
    tracker.process_v2_results(results)
    
    # Get financial results
    financial_results = tracker.get_financial_results(cost_config.metadata['name'])
    
    print(f"\nFinancial Analysis:")
    print(f"Total cost: £{financial_results.total_cost:,.2f}")
    print(f"Cost per patient: £{financial_results.cost_per_patient:,.2f}")
    print(f"Total injections: {financial_results.total_injections}")
    print(f"Cost per injection: £{financial_results.cost_per_injection:,.2f}")
    
    if financial_results.cost_breakdown.by_phase:
        print(f"\nCost by phase:")
        for phase, cost in financial_results.cost_breakdown.by_phase.items():
            print(f"  {phase}: £{cost:,.2f}")
    
    return financial_results


def main():
    """Run all Day 2 tests."""
    
    print("="*60)
    print("Day 2: Native V2 Integration Tests")
    print("="*60)
    
    try:
        # Test patient enhancement
        patient = test_patient_with_enhancer()
        
        # Test ABS engine
        abs_results = test_engine_with_enhancer('abs')
        
        # Test DES engine
        des_results = test_engine_with_enhancer('des')
        
        # Test end-to-end
        financial_results = test_end_to_end_cost_analysis()
        
        print("\n✅ All Day 2 tests passed!")
        print("\nKey achievements:")
        print("- Patient class extended with visit_metadata_enhancer")
        print("- Both engines support cost enhancement")
        print("- End-to-end cost analysis working with native V2")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()