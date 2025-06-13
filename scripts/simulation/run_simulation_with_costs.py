#!/usr/bin/env python3
"""
Run a small AMD simulation with both clinical and financial analysis.

This script demonstrates:
1. Running ABS and DES simulations
2. Tracking costs using the new economics module
3. Generating clinical outcome visualizations
4. Creating financial analysis reports
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# Import simulation components
from simulation.des import DiscreteEventSimulation
from simulation.abs import AgentBasedSimulation
from simulation.config import SimulationConfig
from simulation.patient_generator import PatientGenerator

# Import economics components
from simulation.economics import (
    CostConfig,
    CostAnalyzer,
    CostTracker,
    create_cost_metadata_enhancer
)

# Import visualization components
from visualization.acuity_viz import (
    plot_individual_trajectories,
    plot_mean_acuity_comparison
)
from visualization.population_viz import (
    plot_vision_distribution,
    plot_treatment_intervals
)
from visualization.chart_templates import apply_tufte_style


def run_simulation_with_costs(config_file: str, num_patients: int = 50, 
                             simulation_years: int = 2, cost_config_file: str = None):
    """Run simulation with integrated cost tracking."""
    
    print(f"\n{'='*60}")
    print(f"AMD Simulation with Economic Analysis")
    print(f"{'='*60}")
    print(f"Configuration: {config_file}")
    print(f"Patients: {num_patients}")
    print(f"Duration: {simulation_years} years")
    
    # Load simulation config
    config = SimulationConfig.from_yaml(config_file)
    
    # Load cost config
    if cost_config_file:
        cost_config = CostConfig.from_yaml(Path(cost_config_file))
    else:
        # Use default test config
        cost_config = CostConfig.from_yaml(Path("protocols/cost_configs/nhs_standard_2025.yaml"))
    
    print(f"Cost config: {cost_config.metadata['name']}")
    
    # Create output directory
    output_dir = Path("output/simulation_with_costs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize cost tracking
    cost_analyzer = CostAnalyzer(cost_config)
    abs_cost_tracker = CostTracker(cost_analyzer)
    des_cost_tracker = CostTracker(cost_analyzer)
    
    # Generate patients
    generator = PatientGenerator(config)
    patients = generator.generate_cohort(num_patients)
    
    # Create cost metadata enhancer
    enhancer = create_cost_metadata_enhancer()
    
    # Run ABS simulation
    print(f"\nRunning Agent-Based Simulation...")
    abs_sim = AgentBasedSimulation(config, track_individual_patients=True)
    
    # Attach enhancer to all patients in ABS
    for patient in abs_sim.patients:
        if hasattr(patient, 'patient_state'):
            patient.patient_state.visit_metadata_enhancer = enhancer
    
    abs_results = abs_sim.run(patients, simulation_years)
    print(f"  Completed {len(abs_results['patient_histories'])} patients")
    
    # Run DES simulation
    print(f"\nRunning Discrete Event Simulation...")
    des_sim = DiscreteEventSimulation(config, track_individual_patients=True)
    
    # Attach enhancer to all patient states in DES
    for patient_id, patient_state in des_sim.patient_states.items():
        patient_state.visit_metadata_enhancer = enhancer
    
    des_results = des_sim.run(patients, simulation_years)
    print(f"  Completed {len(des_results['patient_histories'])} patients")
    
    # Process costs
    print(f"\nAnalyzing costs...")
    abs_cost_tracker.process_simulation_results(abs_results)
    des_cost_tracker.process_simulation_results(des_results)
    
    abs_cost_summary = abs_cost_tracker.get_summary_statistics()
    des_cost_summary = des_cost_tracker.get_summary_statistics()
    
    # Print clinical outcomes
    print(f"\n{'='*60}")
    print(f"CLINICAL OUTCOMES")
    print(f"{'='*60}")
    
    # ABS outcomes
    print(f"\nAgent-Based Simulation:")
    print(f"  Final mean VA: {abs_results['final_mean_acuity']:.1f} letters")
    print(f"  Mean VA change: {abs_results['mean_acuity_change']:.1f} letters")
    print(f"  Total injections: {abs_results['total_injections']}")
    print(f"  Mean injections/patient: {abs_results['mean_injections_per_patient']:.1f}")
    
    # DES outcomes
    print(f"\nDiscrete Event Simulation:")
    print(f"  Final mean VA: {des_results['final_mean_acuity']:.1f} letters")
    print(f"  Mean VA change: {des_results['mean_acuity_change']:.1f} letters")
    print(f"  Total injections: {des_results['total_injections']}")
    print(f"  Mean injections/patient: {des_results['mean_injections_per_patient']:.1f}")
    
    # Print financial outcomes
    print(f"\n{'='*60}")
    print(f"FINANCIAL OUTCOMES")
    print(f"{'='*60}")
    
    # ABS costs
    print(f"\nAgent-Based Simulation Costs:")
    print(f"  Total cost: £{abs_cost_summary['total_cost']:,.2f}")
    print(f"  Average cost/patient: £{abs_cost_summary['avg_cost_per_patient']:,.2f}")
    print(f"  Cost breakdown:")
    for event_type, cost in abs_cost_summary['cost_by_type'].items():
        print(f"    {event_type}: £{cost:,.2f}")
    
    # DES costs
    print(f"\nDiscrete Event Simulation Costs:")
    print(f"  Total cost: £{des_cost_summary['total_cost']:,.2f}")
    print(f"  Average cost/patient: £{des_cost_summary['avg_cost_per_patient']:,.2f}")
    print(f"  Cost breakdown:")
    for event_type, cost in des_cost_summary['cost_by_type'].items():
        print(f"    {event_type}: £{cost:,.2f}")
    
    # Generate visualizations
    print(f"\n{'='*60}")
    print(f"GENERATING VISUALIZATIONS")
    print(f"{'='*60}")
    
    # 1. Individual patient trajectories
    print("\nCreating individual patient trajectory plots...")
    fig = plot_individual_trajectories(
        abs_results['patient_histories'], 
        des_results['patient_histories'],
        max_patients=10
    )
    fig.suptitle("Individual Patient Visual Acuity Trajectories", fontsize=14)
    fig.savefig(output_dir / "individual_trajectories.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Mean acuity comparison
    print("Creating mean acuity comparison plot...")
    fig = plot_mean_acuity_comparison(abs_results, des_results)
    fig.savefig(output_dir / "mean_acuity_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Cost accumulation plot
    print("Creating cost accumulation plots...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # ABS cost accumulation
    abs_events_df = abs_cost_tracker.get_patient_costs(list(abs_results['patient_histories'].keys())[0])
    if not abs_events_df.empty:
        # Calculate cumulative costs over time
        time_points = sorted(abs_events_df['time'].unique())
        cumulative_costs = []
        for t in time_points:
            costs_up_to_t = abs_events_df[abs_events_df['time'] <= t]['amount'].sum()
            cumulative_costs.append(costs_up_to_t)
        
        ax1.plot(time_points, cumulative_costs, linewidth=2, color='#1f77b4')
        ax1.set_xlabel('Time (months)')
        ax1.set_ylabel('Cumulative Cost (£)')
        ax1.set_title('ABS: Cost Accumulation')
        ax1.grid(True, alpha=0.3)
    
    # DES cost accumulation
    des_events_df = des_cost_tracker.get_patient_costs(list(des_results['patient_histories'].keys())[0])
    if not des_events_df.empty:
        time_points = sorted(des_events_df['time'].unique())
        cumulative_costs = []
        for t in time_points:
            costs_up_to_t = des_events_df[des_events_df['time'] <= t]['amount'].sum()
            cumulative_costs.append(costs_up_to_t)
        
        ax2.plot(time_points, cumulative_costs, linewidth=2, color='#ff7f0e')
        ax2.set_xlabel('Time (months)')
        ax2.set_ylabel('Cumulative Cost (£)')
        ax2.set_title('DES: Cost Accumulation')
        ax2.grid(True, alpha=0.3)
    
    fig.suptitle('Cost Accumulation Over Time (Sample Patient)', fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / "cost_accumulation.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Cost-effectiveness scatter
    print("Creating cost-effectiveness plot...")
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Calculate per-patient outcomes
    abs_va_changes = []
    abs_costs = []
    for patient_id in abs_results['patient_histories']:
        history = abs_results['patient_histories'][patient_id]
        if 'visits' in history and len(history['visits']) > 0:
            initial_va = history['visits'][0].get('vision', 70)
            final_va = history['visits'][-1].get('vision', 70)
            abs_va_changes.append(final_va - initial_va)
            
            patient_costs = abs_cost_tracker.get_patient_costs(patient_id)
            if not patient_costs.empty:
                abs_costs.append(patient_costs['amount'].sum())
            else:
                abs_costs.append(0)
    
    des_va_changes = []
    des_costs = []
    for patient_id in des_results['patient_histories']:
        history = des_results['patient_histories'][patient_id]
        if 'visits' in history and len(history['visits']) > 0:
            initial_va = history['visits'][0].get('vision', 70)
            final_va = history['visits'][-1].get('vision', 70)
            des_va_changes.append(final_va - initial_va)
            
            patient_costs = des_cost_tracker.get_patient_costs(patient_id)
            if not patient_costs.empty:
                des_costs.append(patient_costs['amount'].sum())
            else:
                des_costs.append(0)
    
    # Plot scatter
    ax.scatter(abs_costs, abs_va_changes, alpha=0.6, label='ABS', s=50)
    ax.scatter(des_costs, des_va_changes, alpha=0.6, label='DES', s=50)
    
    ax.set_xlabel('Total Cost per Patient (£)')
    ax.set_ylabel('VA Change (ETDRS letters)')
    ax.set_title('Cost-Effectiveness: VA Change vs Total Cost')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    fig.savefig(output_dir / "cost_effectiveness.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save detailed results
    print("\nSaving detailed results...")
    
    # Save summary report
    report = {
        'simulation_parameters': {
            'config_file': config_file,
            'num_patients': num_patients,
            'simulation_years': simulation_years,
            'cost_config': cost_config.metadata['name']
        },
        'clinical_outcomes': {
            'abs': {
                'final_mean_acuity': abs_results['final_mean_acuity'],
                'mean_acuity_change': abs_results['mean_acuity_change'],
                'total_injections': abs_results['total_injections'],
                'mean_injections_per_patient': abs_results['mean_injections_per_patient']
            },
            'des': {
                'final_mean_acuity': des_results['final_mean_acuity'],
                'mean_acuity_change': des_results['mean_acuity_change'],
                'total_injections': des_results['total_injections'],
                'mean_injections_per_patient': des_results['mean_injections_per_patient']
            }
        },
        'financial_outcomes': {
            'abs': abs_cost_summary,
            'des': des_cost_summary
        },
        'cost_per_letter_gained': {
            'abs': abs_cost_summary['avg_cost_per_patient'] / max(abs_results['mean_acuity_change'], 0.1),
            'des': des_cost_summary['avg_cost_per_patient'] / max(des_results['mean_acuity_change'], 0.1)
        }
    }
    
    with open(output_dir / "simulation_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    # Export cost data to parquet
    abs_cost_tracker.export_to_parquet(output_dir / "abs_costs")
    des_cost_tracker.export_to_parquet(output_dir / "des_costs")
    
    print(f"\n{'='*60}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Results saved to: {output_dir}")
    print(f"  - Individual trajectories: individual_trajectories.png")
    print(f"  - Mean acuity comparison: mean_acuity_comparison.png")
    print(f"  - Cost accumulation: cost_accumulation.png")
    print(f"  - Cost effectiveness: cost_effectiveness.png")
    print(f"  - Detailed report: simulation_report.json")
    print(f"  - Cost data: abs_costs/ and des_costs/ (parquet format)")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Run AMD simulation with cost analysis')
    parser.add_argument('--config', type=str, default='protocols/eylea.yaml',
                       help='Path to simulation config file')
    parser.add_argument('--cost-config', type=str, 
                       default='protocols/cost_configs/nhs_standard_2025.yaml',
                       help='Path to cost config file')
    parser.add_argument('--patients', type=int, default=50,
                       help='Number of patients to simulate')
    parser.add_argument('--years', type=int, default=2,
                       help='Simulation duration in years')
    
    args = parser.parse_args()
    
    run_simulation_with_costs(
        config_file=args.config,
        cost_config_file=args.cost_config,
        num_patients=args.patients,
        simulation_years=args.years
    )


if __name__ == "__main__":
    main()