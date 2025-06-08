#!/usr/bin/env python3
"""
Example of how to add cost tracking to AMD simulations.

This demonstrates the minimal hook approach for integrating
economic analysis without modifying core simulation code.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from simulation.patient_state import PatientState
from simulation.economics import (
    CostConfig,
    CostAnalyzer,
    CostTracker,
    create_cost_metadata_enhancer
)


def run_example():
    """Run a simple example with cost tracking."""
    
    # 1. Load cost configuration
    cost_config = CostConfig.from_yaml(
        Path("tests/fixtures/economics/test_cost_config.yaml")
    )
    print("Cost configuration loaded")
    print(f"  Drug costs: {list(cost_config.drug_costs.keys())}")
    print(f"  Visit types: {list(cost_config.visit_types.keys())}")
    
    # 2. Create cost analyzer and tracker
    analyzer = CostAnalyzer(cost_config)
    tracker = CostTracker(analyzer)
    
    # 3. Create patient with cost metadata enhancer
    patient = PatientState(
        patient_id="example_001",
        protocol_name="treat_and_extend",
        initial_vision=70.0,
        start_time=datetime(2025, 1, 1)
    )
    
    # Attach the cost metadata enhancer
    patient.visit_metadata_enhancer = create_cost_metadata_enhancer()
    print("\nPatient created with cost tracking enabled")
    
    # 4. Simulate some visits
    # For this example, we'll record visits directly without using ClinicalModel
    
    # Visit 1: Initial injection (loading phase)
    visit1_time = datetime(2025, 1, 1)
    visit1_actions = ['injection', 'oct_scan', 'visual_acuity_test']
    visit1_data = {
        'visit_type': 'injection_visit',
        'drug': 'eylea_2mg',
        'baseline_vision': 70.0,
        'vision': 71.0,
        'disease_state': 'ACTIVE'
    }
    patient._record_visit(visit1_time, visit1_actions, visit1_data)
    print(f"\nVisit 1 recorded:")
    print(f"  Actions: {visit1_actions}")
    print(f"  Vision: {visit1_data['vision']:.1f} letters")
    
    # Visit 2: Follow-up injection (loading phase)
    patient.state['current_phase'] = 'loading'
    patient.state['current_vision'] = 72.0
    visit2_time = datetime(2025, 2, 1)
    visit2_actions = ['injection', 'visual_acuity_test']
    visit2_data = {
        'visit_type': 'injection_visit',
        'drug': 'eylea_2mg',
        'vision': 72.0,
        'disease_state': 'STABLE'
    }
    patient._record_visit(visit2_time, visit2_actions, visit2_data)
    print(f"\nVisit 2 recorded:")
    print(f"  Actions: {visit2_actions}")
    print(f"  Vision: {visit2_data['vision']:.1f} letters")
    
    # Visit 3: Monitoring visit (maintenance phase)
    patient.state['current_phase'] = 'maintenance'
    patient.state['current_vision'] = 73.0
    visit3_time = datetime(2025, 3, 1)
    visit3_actions = ['oct_scan', 'visual_acuity_test', 'virtual_review']
    visit3_data = {
        'visit_type': 'monitoring_visit',
        'vision': 73.0,
        'disease_state': 'STABLE'
    }
    patient._record_visit(visit3_time, visit3_actions, visit3_data)
    print(f"\nVisit 3 recorded:")
    print(f"  Actions: {visit3_actions}")
    print(f"  Vision: {visit3_data['vision']:.1f} letters")
    
    # 5. Analyze costs
    print("\n" + "="*50)
    print("COST ANALYSIS")
    print("="*50)
    
    # Process the patient history
    patient_history = {
        'patient_id': patient.patient_id,
        'visit_history': patient.state['visit_history']
    }
    
    # Analyze each visit
    for i, visit in enumerate(patient.state['visit_history']):
        print(f"\nVisit {i+1} - {visit['date'].strftime('%Y-%m-%d')}:")
        print(f"  Type: {visit['type']}")
        print(f"  Phase: {visit['phase']}")
        
        # Check metadata
        if 'metadata' in visit:
            metadata = visit['metadata']
            print(f"  Cost metadata:")
            print(f"    Visit subtype: {metadata.get('visit_subtype', 'N/A')}")
            print(f"    Components: {metadata.get('components_performed', [])}")
            print(f"    Drug: {metadata.get('drug', 'None')}")
            print(f"    Days since last: {metadata.get('days_since_last', 0)}")
            
            # Calculate cost for this visit
            visit_for_analysis = visit.copy()
            visit_for_analysis['time'] = i  # Month number
            visit_for_analysis['patient_id'] = patient.patient_id
            if 'drug' in metadata:
                visit_for_analysis['drug'] = metadata['drug']
            
            cost_event = analyzer.analyze_visit(visit_for_analysis)
            if cost_event:
                print(f"    Total cost: £{cost_event.amount:.2f}")
                print(f"    Drug cost: £{cost_event.metadata['drug_cost']:.2f}")
                print(f"    Visit cost: £{cost_event.metadata['visit_cost']:.2f}")
        else:
            print("  No cost metadata (enhancer not attached)")
    
    # 6. Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Patient {patient.patient_id}:")
    print(f"  Total visits: {len(patient.state['visit_history'])}")
    print(f"  Current vision: {patient.state['current_vision']:.1f} letters")
    print(f"  Vision change: {patient.state['current_vision'] - patient.state['baseline_vision']:.1f} letters")
    
    # Calculate total costs
    total_cost = 0
    total_drug_cost = 0
    for i, visit in enumerate(patient.state['visit_history']):
        if 'metadata' in visit:
            visit_for_analysis = visit.copy()
            visit_for_analysis['time'] = i
            visit_for_analysis['patient_id'] = patient.patient_id
            if 'drug' in visit['metadata']:
                visit_for_analysis['drug'] = visit['metadata']['drug']
            
            cost_event = analyzer.analyze_visit(visit_for_analysis)
            if cost_event:
                total_cost += cost_event.amount
                total_drug_cost += cost_event.metadata['drug_cost']
    
    print(f"\nTotal treatment cost: £{total_cost:.2f}")
    print(f"  Drug costs: £{total_drug_cost:.2f}")
    print(f"  Visit costs: £{total_cost - total_drug_cost:.2f}")


if __name__ == "__main__":
    run_example()