#!/usr/bin/env python3
"""
Run AMD simulation with integrated cost tracking using V2 simulation infrastructure.

This demonstrates running a simulation with both clinical and financial analysis
using the V2 architecture with properly integrated cost tracking.

DEPRECATED: This script uses the old V1 compatibility approach. For V2 simulations,
use 'run_v2_simulation_with_costs_integrated_new.py' which uses the EconomicsIntegration API.
"""

import warnings
warnings.warn(
    "This script is deprecated. Use run_v2_simulation_with_costs_integrated_new.py "
    "which uses the new EconomicsIntegration API.",
    DeprecationWarning,
    stacklevel=2
)

import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import V2 simulation components
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol

# Import enhanced engines with cost support
from simulation_v2.engines.abs_engine_with_costs import ABSEngineWithCosts
from simulation_v2.engines.des_engine_with_costs import DESEngineWithCosts

# Import economics components
from simulation.economics import (
    CostConfig,
    CostAnalyzer,
    CostTracker,
    SimulationCostAdapter
)
from simulation.economics.cost_metadata_enhancer_v2 import create_cost_metadata_enhancer


def run_simulation_with_costs(engine_type: str, protocol_spec: ProtocolSpecification, 
                             n_patients: int, duration_years: float, seed: int,
                             cost_metadata_enhancer: callable) -> tuple:
    """
    Run a single simulation with cost tracking.
    
    Returns:
        Tuple of (results, patient_data_for_costs)
    """
    # Create disease model from protocol
    disease_model = DiseaseModel(
        transition_probabilities=protocol_spec.disease_transitions,
        treatment_effect_multipliers=protocol_spec.treatment_effect_on_transitions,
        seed=seed
    )
    
    # Create protocol
    protocol = StandardProtocol(
        min_interval_days=protocol_spec.min_interval_days,
        max_interval_days=protocol_spec.max_interval_days,
        extension_days=protocol_spec.extension_days,
        shortening_days=protocol_spec.shortening_days
    )
    # Add name attribute for cost tracking
    protocol.name = protocol_spec.name
    
    # Create engine with cost support
    if engine_type == 'abs':
        engine = ABSEngineWithCosts(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            visit_metadata_enhancer=cost_metadata_enhancer
        )
    else:  # des
        engine = DESEngineWithCosts(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            visit_metadata_enhancer=cost_metadata_enhancer
        )
    
    # Run simulation
    results = engine.run(duration_years)
    
    # Extract patient data with cost metadata in expected format
    patient_data = {}
    for patient_id, patient in results.patient_histories.items():
        # Convert visits to format expected by cost adapter
        converted_visits = []
        for visit in patient.visit_history:
            # Convert V2 visit format to expected format
            converted_visit = {
                'time': visit['date'],  # Rename 'date' to 'time'
                'vision': visit['vision'],
                'treatment_given': visit.get('treatment_given', False),
                'actions': [],  # Build from metadata
                'metadata': visit.get('metadata', {})
            }
            
            # Build actions list from metadata
            if visit.get('metadata', {}).get('components_performed'):
                converted_visit['actions'] = visit['metadata']['components_performed']
            elif visit.get('treatment_given'):
                converted_visit['actions'] = ['vision_test', 'oct_scan', 'injection']
            else:
                converted_visit['actions'] = ['vision_test', 'oct_scan']
            
            # Add other expected fields
            if 'disease_state' in visit:
                disease_state = visit['disease_state']
                if hasattr(disease_state, 'name'):
                    converted_visit['disease_state'] = disease_state.name.lower()
                else:
                    converted_visit['disease_state'] = str(disease_state).lower()
            
            # Add visit type
            converted_visit['type'] = visit.get('metadata', {}).get('visit_subtype', 'regular_visit')
            
            # Add phase from metadata
            if 'phase' in visit.get('metadata', {}):
                converted_visit['phase'] = visit['metadata']['phase']
            
            converted_visits.append(converted_visit)
        
        # Create patient data in the format expected by cost adapter
        patient_data[patient_id] = {
            'patient_id': patient_id,
            'baseline_vision': patient.baseline_vision,
            'visits': converted_visits
        }
    
    return results, patient_data


def main():
    """Run a simulation with cost analysis using V2 architecture."""
    
    print("\n" + "="*60)
    print("AMD Simulation with Integrated Clinical and Financial Analysis (V2)")
    print("="*60)
    
    # Use the V2 protocol file
    protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
    if not protocol_path.exists():
        # Try alternate path
        protocol_path = Path("protocols/v2/eylea_treat_and_extend_v1.0.yaml")
    
    # Simulation parameters
    n_patients = 100  # Reasonable size for demo
    duration_years = 2.0  # 2 years
    seed = 42
    
    print(f"\nSimulation Parameters:")
    print(f"  Protocol: {protocol_path}")
    print(f"  Patients: {n_patients}")
    print(f"  Duration: {duration_years} years")
    print(f"  Seed: {seed}")
    
    # Create output directory
    output_dir = Path("output/v2_simulation_with_costs_integrated")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cost configuration
    cost_config_path = Path("protocols/cost_configs/nhs_standard_2025.yaml")
    cost_config = CostConfig.from_yaml(cost_config_path)
    print(f"\nCost Configuration: {cost_config.metadata['name']}")
    
    # Create cost metadata enhancer
    cost_metadata_enhancer = create_cost_metadata_enhancer()
    
    # Load protocol specification
    print(f"\nLoading protocol from: {protocol_path}")
    try:
        protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
        print(f"Loaded: {protocol_spec.name} v{protocol_spec.version}")
        print(f"Checksum: {protocol_spec.checksum}")
    except Exception as e:
        print(f"ERROR: Failed to load protocol: {e}")
        return
    
    # Run ABS simulation with integrated cost tracking
    print(f"\n{'='*40}")
    print("Running Agent-Based Simulation (V2) with Cost Tracking...")
    print("="*40)
    
    abs_results, abs_patient_data = run_simulation_with_costs(
        'abs', protocol_spec, n_patients, duration_years, seed, cost_metadata_enhancer
    )
    
    print(f"\nABS Simulation complete:")
    print(f"  Total injections: {abs_results.total_injections}")
    print(f"  Mean final vision: {abs_results.final_vision_mean:.1f}")
    print(f"  Discontinuation rate: {abs_results.discontinuation_rate:.1%}")
    
    # Run DES simulation with integrated cost tracking
    print(f"\n{'='*40}")
    print("Running Discrete Event Simulation (V2) with Cost Tracking...")
    print("="*40)
    
    des_results, des_patient_data = run_simulation_with_costs(
        'des', protocol_spec, n_patients, duration_years, seed, cost_metadata_enhancer
    )
    
    print(f"\nDES Simulation complete:")
    print(f"  Total injections: {des_results.total_injections}")
    print(f"  Mean final vision: {des_results.final_vision_mean:.1f}")
    print(f"  Discontinuation rate: {des_results.discontinuation_rate:.1%}")
    
    # Process costs using the adapter
    print(f"\n{'='*40}")
    print("Analyzing Costs...")
    print("="*40)
    
    # Create cost analyzers and process
    cost_analyzer = CostAnalyzer(cost_config)
    abs_adapter = SimulationCostAdapter(cost_analyzer)
    des_adapter = SimulationCostAdapter(cost_analyzer)
    
    # Process simulation results with proper format
    abs_sim_data = {'patient_histories': abs_patient_data}
    des_sim_data = {'patient_histories': des_patient_data}
    
    abs_results_with_costs = abs_adapter.process_simulation_results(abs_sim_data)
    des_results_with_costs = des_adapter.process_simulation_results(des_sim_data)
    
    # Extract cost summaries
    abs_costs = abs_results_with_costs.get('cost_summary', {})
    des_costs = des_results_with_costs.get('cost_summary', {})
    
    # Clinical Analysis
    print(f"\n{'='*60}")
    print("CLINICAL OUTCOMES")
    print("="*60)
    
    # Calculate baseline vision means
    abs_baseline_mean = sum(p.baseline_vision for p in abs_results.patient_histories.values()) / abs_results.patient_count
    des_baseline_mean = sum(p.baseline_vision for p in des_results.patient_histories.values()) / des_results.patient_count
    
    print(f"\nAgent-Based Simulation (V2):")
    print(f"  Number of patients: {abs_results.patient_count}")
    print(f"  Mean injections/patient: {abs_results.total_injections / abs_results.patient_count:.1f}")
    print(f"  Initial mean VA: {abs_baseline_mean:.1f} letters")
    print(f"  Final mean VA: {abs_results.final_vision_mean:.1f} letters")
    print(f"  Mean VA change: {abs_results.final_vision_mean - abs_baseline_mean:.1f} letters")
    
    print(f"\nDiscrete Event Simulation (V2):")
    print(f"  Number of patients: {des_results.patient_count}")
    print(f"  Mean injections/patient: {des_results.total_injections / des_results.patient_count:.1f}")
    print(f"  Initial mean VA: {des_baseline_mean:.1f} letters")
    print(f"  Final mean VA: {des_results.final_vision_mean:.1f} letters")
    print(f"  Mean VA change: {des_results.final_vision_mean - des_baseline_mean:.1f} letters")
    
    # Financial Analysis
    print(f"\n{'='*60}")
    print("FINANCIAL OUTCOMES")
    print("="*60)
    
    if abs_costs:
        print(f"\nAgent-Based Simulation Costs:")
        print(f"  Total cost: £{abs_costs.get('total_cost', 0):,.2f}")
        print(f"  Average cost/patient: £{abs_costs.get('avg_cost_per_patient', 0):,.2f}")
        
        # Cost breakdown
        if 'cost_by_category' in abs_costs:
            print(f"\n  Cost breakdown:")
            for category, amount in abs_costs['cost_by_category'].items():
                print(f"    {category}: £{amount:,.2f}")
        
        # Cost per outcome
        va_change = abs_results.final_vision_mean - abs_baseline_mean
        if va_change > 0:
            cost_per_letter = abs_costs.get('avg_cost_per_patient', 0) / va_change
            print(f"\n  Cost per letter gained: £{cost_per_letter:,.2f}")
        
        # Additional cost metrics
        if 'patient_costs' in abs_results_with_costs:
            patient_costs = abs_results_with_costs['patient_costs']
            cost_values = [p['total_cost'] for p in patient_costs.values()]
            print(f"\n  Cost distribution:")
            print(f"    Min: £{min(cost_values):,.2f}")
            print(f"    Max: £{max(cost_values):,.2f}")
            print(f"    Std Dev: £{np.std(cost_values):,.2f}")
    
    if des_costs:
        print(f"\nDiscrete Event Simulation Costs:")
        print(f"  Total cost: £{des_costs.get('total_cost', 0):,.2f}")
        print(f"  Average cost/patient: £{des_costs.get('avg_cost_per_patient', 0):,.2f}")
        
        # Cost breakdown
        if 'cost_by_category' in des_costs:
            print(f"\n  Cost breakdown:")
            for category, amount in des_costs['cost_by_category'].items():
                print(f"    {category}: £{amount:,.2f}")
        
        # Cost per outcome
        va_change = des_results.final_vision_mean - des_baseline_mean
        if va_change > 0:
            cost_per_letter = des_costs.get('avg_cost_per_patient', 0) / va_change
            print(f"\n  Cost per letter gained: £{cost_per_letter:,.2f}")
        
        # Additional cost metrics
        if 'patient_costs' in des_results_with_costs:
            patient_costs = des_results_with_costs['patient_costs']
            cost_values = [p['total_cost'] for p in patient_costs.values()]
            print(f"\n  Cost distribution:")
            print(f"    Min: £{min(cost_values):,.2f}")
            print(f"    Max: £{max(cost_values):,.2f}")
            print(f"    Std Dev: £{np.std(cost_values):,.2f}")
    
    # Save summary report
    print(f"\n{'='*40}")
    print("Saving Results...")
    print("="*40)
    
    summary = {
        "simulation_parameters": {
            "protocol": str(protocol_path),
            "protocol_name": protocol_spec.name,
            "protocol_version": protocol_spec.version,
            "patients": n_patients,
            "duration_years": duration_years,
            "cost_config": str(cost_config_path)
        },
        "clinical_outcomes": {
            "abs": {
                "initial_va": abs_baseline_mean,
                "final_va": abs_results.final_vision_mean,
                "va_change": abs_results.final_vision_mean - abs_baseline_mean,
                "total_injections": abs_results.total_injections,
                "injections_per_patient": abs_results.total_injections / abs_results.patient_count
            },
            "des": {
                "initial_va": des_baseline_mean,
                "final_va": des_results.final_vision_mean,
                "va_change": des_results.final_vision_mean - des_baseline_mean,
                "total_injections": des_results.total_injections,
                "injections_per_patient": des_results.total_injections / des_results.patient_count
            }
        },
        "financial_outcomes": {
            "abs": abs_costs,
            "des": des_costs
        }
    }
    
    with open(output_dir / "summary_report.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save detailed patient costs
    with open(output_dir / "abs_patient_costs.json", 'w') as f:
        json.dump(abs_results_with_costs.get('patient_costs', {}), f, indent=2)
    
    with open(output_dir / "des_patient_costs.json", 'w') as f:
        json.dump(des_results_with_costs.get('patient_costs', {}), f, indent=2)
    
    print(f"\nResults saved to: {output_dir}")
    print(f"  - Summary report: summary_report.json")
    print(f"  - ABS patient costs: abs_patient_costs.json")
    print(f"  - DES patient costs: des_patient_costs.json")
    
    print(f"\n{'='*60}")
    print("SIMULATION COMPLETE - Clinical and Financial Analysis Integrated!")
    print("="*60)
    
    return summary


if __name__ == "__main__":
    main()