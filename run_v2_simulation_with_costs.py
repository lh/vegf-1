#!/usr/bin/env python3
"""
Run AMD simulation with cost tracking using V2 simulation infrastructure.

This demonstrates running a simulation with both clinical and financial analysis
using the V2 architecture that streamlit_app_v2 uses.

DEPRECATED: This script uses the old manual data conversion approach. For V2 simulations,
use 'run_v2_simulation_with_economics.py' which uses the EconomicsIntegration API.
"""

import warnings
warnings.warn(
    "This script is deprecated. Use run_v2_simulation_with_economics.py "
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

# Import economics components
from simulation.economics import (
    CostConfig,
    CostAnalyzer,
    CostTracker,
    SimulationCostAdapter
)


def main():
    """Run a simulation with cost analysis using V2 architecture."""
    
    print("\n" + "="*60)
    print("AMD Simulation with Clinical and Financial Analysis (V2)")
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
    output_dir = Path("output/v2_simulation_with_costs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cost configuration
    cost_config_path = Path("protocols/cost_configs/nhs_standard_2025.yaml")
    cost_config = CostConfig.from_yaml(cost_config_path)
    print(f"\nCost Configuration: {cost_config.metadata['name']}")
    
    # Load protocol specification
    print(f"\nLoading protocol from: {protocol_path}")
    try:
        protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
        print(f"Loaded: {protocol_spec.name} v{protocol_spec.version}")
        print(f"Checksum: {protocol_spec.checksum}")
    except Exception as e:
        print(f"ERROR: Failed to load protocol: {e}")
        return
    
    # Create simulation runner
    runner = SimulationRunner(protocol_spec)
    
    # Run ABS simulation
    print(f"\n{'='*40}")
    print("Running Agent-Based Simulation (V2)...")
    print("="*40)
    
    abs_results = runner.run(
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    
    print(f"\nABS Simulation complete:")
    print(f"  Total injections: {abs_results.total_injections}")
    print(f"  Mean final vision: {abs_results.final_vision_mean:.1f}")
    print(f"  Discontinuation rate: {abs_results.discontinuation_rate:.1%}")
    
    # Run DES simulation
    print(f"\n{'='*40}")
    print("Running Discrete Event Simulation (V2)...")
    print("="*40)
    
    des_results = runner.run(
        engine_type='des',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    
    print(f"\nDES Simulation complete:")
    print(f"  Total injections: {des_results.total_injections}")
    print(f"  Mean final vision: {des_results.final_vision_mean:.1f}")
    print(f"  Discontinuation rate: {des_results.discontinuation_rate:.1%}")
    
    # Process costs using the adapter
    print(f"\n{'='*40}")
    print("Analyzing Costs...")
    print("="*40)
    
    # Convert V2 results to format expected by cost adapter
    # For now, create a simple mapping
    abs_patient_data = {}
    des_patient_data = {}
    
    # Extract visit data from V2 results
    for patient_id, patient in abs_results.patient_histories.items():
        visits = []
        for i, visit in enumerate(patient.visit_history):
            # Create visit record in expected format
            visit_record = {
                'date': visit['date'],
                'vision': visit['vision'],
                'baseline_vision': patient.baseline_vision,
                'phase': 'maintenance' if i >= 3 else 'loading',
                'type': 'regular_visit',
                'actions': ['vision_test', 'oct_scan', 'injection'] if visit['treatment_given'] else ['vision_test', 'oct_scan'],
                'disease_state': visit['disease_state'].name.lower() if hasattr(visit['disease_state'], 'name') else str(visit['disease_state']).lower(),
                'interval': patient.current_interval_days  # Use patient's current interval
            }
            visits.append(visit_record)
        abs_patient_data[patient_id] = visits
    
    for patient_id, patient in des_results.patient_histories.items():
        visits = []
        for i, visit in enumerate(patient.visit_history):
            visit_record = {
                'date': visit['date'],
                'vision': visit['vision'],
                'baseline_vision': patient.baseline_vision,
                'phase': 'maintenance' if i >= 3 else 'loading',
                'type': 'regular_visit',
                'actions': ['vision_test', 'oct_scan', 'injection'] if visit['treatment_given'] else ['vision_test', 'oct_scan'],
                'disease_state': visit['disease_state'].name.lower() if hasattr(visit['disease_state'], 'name') else str(visit['disease_state']).lower(),
                'interval': patient.current_interval_days
            }
            visits.append(visit_record)
        des_patient_data[patient_id] = visits
    
    # Create cost analyzers and process
    cost_analyzer = CostAnalyzer(cost_config)
    abs_adapter = SimulationCostAdapter(cost_analyzer)
    des_adapter = SimulationCostAdapter(cost_analyzer)
    
    abs_results_with_costs = abs_adapter.process_simulation_results(abs_patient_data)
    des_results_with_costs = des_adapter.process_simulation_results(des_patient_data)
    
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
    
    # Save audit trail
    runner.save_audit_trail(output_dir / "audit_trail.json")
    
    print(f"\nResults saved to: {output_dir}")
    print(f"  - Summary report: summary_report.json")
    print(f"  - Audit trail: audit_trail.json")
    
    print(f"\n{'='*60}")
    print("SIMULATION COMPLETE")
    print("="*60)
    
    return summary


if __name__ == "__main__":
    main()