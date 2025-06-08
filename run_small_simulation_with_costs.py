#!/usr/bin/env python3
"""
Run a small AMD simulation with cost tracking using V2 simulation infrastructure.

This demonstrates running a quick simulation with both clinical and financial analysis
using the modern V2 architecture that streamlit_app_v2 uses.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt

# Add path for simulation_v2
sys.path.append(str(Path(__file__).parent))

# Import V2 simulation components
from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

# Import economics components
from simulation.economics import (
    CostConfig,
    CostAnalyzer,
    CostTracker,
    SimulationCostAdapter
)

# Import visualization
from analysis.simulation_results import SimulationResults
from visualization.comparison_viz import plot_mean_acuity_comparison


def main():
    """Run a small simulation with cost analysis."""
    
    print("\n" + "="*60)
    print("AMD Simulation with Clinical and Financial Analysis")
    print("="*60)
    
    # Simulation parameters
    config_file = "test_simulation"  # Just the name, not the full path
    num_patients = 20  # Small cohort for quick results
    simulation_months = 24  # 2 years
    
    print(f"\nSimulation Parameters:")
    print(f"  Config: {config_file}")
    print(f"  Note: Using config defaults (50 patients, 365 days)")
    
    # Create output directory
    output_dir = Path("output/quick_simulation_with_costs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cost configuration
    cost_config_path = Path("protocols/cost_configs/nhs_standard_2025.yaml")
    if not cost_config_path.exists():
        cost_config_path = Path("tests/fixtures/economics/test_cost_config.yaml")
    
    cost_config = CostConfig.from_yaml(cost_config_path)
    print(f"\nCost Configuration: {cost_config.metadata['name']}")
    
    # Load configuration
    from simulation.config import SimulationConfig
    config = SimulationConfig.from_yaml(config_file)
    
    # Note: Using config defaults for now
    # TODO: Add ability to override patient count and duration
    
    # Run ABS simulation
    print(f"\n{'='*40}")
    print("Running Agent-Based Simulation...")
    print("="*40)
    
    abs_results = run_abs(
        config=config_file,  # Pass the config name string, not the object
        verbose=True
    )
    
    # Run DES simulation
    print(f"\n{'='*40}")
    print("Running Discrete Event Simulation...")
    print("="*40)
    
    des_results = run_des(
        config=config_file,  # Pass the config name string, not the object
        verbose=True
    )
    
    # Process costs using the adapter
    print(f"\n{'='*40}")
    print("Analyzing Costs...")
    print("="*40)
    
    # Create cost adapters
    cost_analyzer = CostAnalyzer(cost_config)
    abs_adapter = SimulationCostAdapter(cost_analyzer)
    des_adapter = SimulationCostAdapter(cost_analyzer)
    
    # Process simulation results to add costs
    abs_results_with_costs = abs_adapter.process_simulation_results(abs_results)
    des_results_with_costs = des_adapter.process_simulation_results(des_results)
    
    # Extract cost summaries
    abs_costs = abs_results_with_costs.get('cost_summary', {})
    des_costs = des_results_with_costs.get('cost_summary', {})
    
    # Clinical Analysis
    print(f"\n{'='*60}")
    print("CLINICAL OUTCOMES")
    print("="*60)
    
    # Process with SimulationResults for statistics
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=simulation_months * 30)
    
    abs_sim_results = SimulationResults(
        start_date=start_date,
        end_date=end_date,
        patient_histories=abs_results
    )
    
    des_sim_results = SimulationResults(
        start_date=start_date,
        end_date=end_date,
        patient_histories=des_results
    )
    
    # Get summary statistics
    abs_stats = abs_sim_results.get_summary_statistics()
    des_stats = des_sim_results.get_summary_statistics()
    
    print(f"\nAgent-Based Simulation:")
    print(f"  Number of patients: {abs_stats['num_patients']}")
    print(f"  Mean visits/patient: {abs_stats['mean_visits_per_patient']:.1f}")
    print(f"  Mean injections/patient: {abs_stats['mean_injections_per_patient']:.1f}")
    print(f"  Initial mean VA: {abs_stats['vision_baseline_mean']:.1f} letters")
    print(f"  Final mean VA: {abs_stats['vision_final_mean']:.1f} letters")
    print(f"  Mean VA change: {abs_stats['mean_vision_change']:.1f} letters")
    
    print(f"\nDiscrete Event Simulation:")
    print(f"  Number of patients: {des_stats['num_patients']}")
    print(f"  Mean visits/patient: {des_stats['mean_visits_per_patient']:.1f}")
    print(f"  Mean injections/patient: {des_stats['mean_injections_per_patient']:.1f}")
    print(f"  Initial mean VA: {des_stats['vision_baseline_mean']:.1f} letters")
    print(f"  Final mean VA: {des_stats['vision_final_mean']:.1f} letters")
    print(f"  Mean VA change: {des_stats['mean_vision_change']:.1f} letters")
    
    # Financial Analysis
    print(f"\n{'='*60}")
    print("FINANCIAL OUTCOMES")
    print("="*60)
    
    if abs_costs:
        print(f"\nAgent-Based Simulation Costs:")
        print(f"  Total cost: £{abs_costs.get('total_cost', 0):,.2f}")
        print(f"  Average cost/patient: £{abs_costs.get('avg_cost_per_patient', 0):,.2f}")
        print(f"  Drug costs: £{sum(abs_costs.get('cost_by_category', {}).get(k, 0) for k in abs_costs.get('cost_by_category', {}) if 'injection' in k):,.2f}")
        print(f"  Monitoring costs: £{sum(abs_costs.get('cost_by_category', {}).get(k, 0) for k in abs_costs.get('cost_by_category', {}) if 'monitoring' in k):,.2f}")
        
        # Cost per outcome
        if abs_stats['mean_vision_change'] > 0:
            cost_per_letter = abs_costs.get('avg_cost_per_patient', 0) / abs_stats['mean_vision_change']
            print(f"  Cost per letter gained: £{cost_per_letter:,.2f}")
    
    if des_costs:
        print(f"\nDiscrete Event Simulation Costs:")
        print(f"  Total cost: £{des_costs.get('total_cost', 0):,.2f}")
        print(f"  Average cost/patient: £{des_costs.get('avg_cost_per_patient', 0):,.2f}")
        print(f"  Drug costs: £{sum(des_costs.get('cost_by_category', {}).get(k, 0) for k in des_costs.get('cost_by_category', {}) if 'injection' in k):,.2f}")
        print(f"  Monitoring costs: £{sum(des_costs.get('cost_by_category', {}).get(k, 0) for k in des_costs.get('cost_by_category', {}) if 'monitoring' in k):,.2f}")
        
        # Cost per outcome
        if des_stats['mean_vision_change'] > 0:
            cost_per_letter = des_costs.get('avg_cost_per_patient', 0) / des_stats['mean_vision_change']
            print(f"  Cost per letter gained: £{cost_per_letter:,.2f}")
    
    # Generate visualizations
    print(f"\n{'='*60}")
    print("GENERATING VISUALIZATIONS")
    print("="*60)
    
    # 1. Clinical outcomes comparison
    print("\nCreating clinical outcomes visualization...")
    # Get mean vision data over time
    des_means = des_sim_results.get_mean_vision_over_time()
    abs_means = abs_sim_results.get_mean_vision_over_time()
    
    # Create time points (weeks)
    time_points = list(range(0, min(53, max(len(des_means), len(abs_means)))))
    
    # Format data for comparison plot
    des_data = {"All Patients": des_means}
    abs_data = {"All Patients": abs_means}
    
    # Create comparison plot
    plot_mean_acuity_comparison(des_data, abs_data, time_points)
    plt.savefig(output_dir / "clinical_outcomes_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Cost breakdown comparison
    if abs_costs and des_costs:
        print("Creating cost breakdown visualization...")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # ABS cost breakdown
        if 'cost_by_category' in abs_costs:
            categories = list(abs_costs['cost_by_category'].keys())
            values = list(abs_costs['cost_by_category'].values())
            ax1.pie(values, labels=categories, autopct='%1.1f%%', startangle=90)
            ax1.set_title(f'ABS Cost Breakdown\nTotal: £{abs_costs["total_cost"]:,.0f}')
        
        # DES cost breakdown
        if 'cost_by_category' in des_costs:
            categories = list(des_costs['cost_by_category'].keys())
            values = list(des_costs['cost_by_category'].values())
            ax2.pie(values, labels=categories, autopct='%1.1f%%', startangle=90)
            ax2.set_title(f'DES Cost Breakdown\nTotal: £{des_costs["total_cost"]:,.0f}')
        
        fig.suptitle('Cost Distribution by Visit Type', fontsize=14)
        fig.tight_layout()
        fig.savefig(output_dir / "cost_breakdown.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    # 3. Simple cost-effectiveness comparison
    print("Creating cost-effectiveness comparison...")
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if abs_costs and des_costs:
        # Plot points for each simulation type
        abs_cost_pp = abs_costs.get('avg_cost_per_patient', 0)
        des_cost_pp = des_costs.get('avg_cost_per_patient', 0)
        
        ax.scatter([abs_cost_pp], [abs_stats['mean_vision_change']], 
                  s=200, label='ABS', alpha=0.7, edgecolors='black')
        ax.scatter([des_cost_pp], [des_stats['mean_vision_change']], 
                  s=200, label='DES', alpha=0.7, edgecolors='black')
        
        # Add labels
        ax.text(abs_cost_pp, abs_stats['mean_vision_change'] + 0.2, 'ABS', 
               ha='center', va='bottom')
        ax.text(des_cost_pp, des_stats['mean_vision_change'] + 0.2, 'DES', 
               ha='center', va='bottom')
        
        ax.set_xlabel('Average Cost per Patient (£)')
        ax.set_ylabel('Mean VA Change (ETDRS letters)')
        ax.set_title('Cost-Effectiveness Comparison')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Add diagonal lines for cost per letter gained
        xlim = ax.get_xlim()
        for cost_per_letter in [500, 1000, 2000]:
            x_vals = np.array(xlim)
            y_vals = x_vals / cost_per_letter
            ax.plot(x_vals, y_vals, '--', alpha=0.3, 
                   label=f'£{cost_per_letter}/letter')
        
        ax.legend()
        ax.set_xlim(xlim)
        
    fig.savefig(output_dir / "cost_effectiveness.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save summary report
    print("\nSaving summary report...")
    summary = {
        "simulation_parameters": {
            "config": config_file,
            "patients": num_patients,
            "duration_months": simulation_months,
            "cost_config": str(cost_config_path)
        },
        "clinical_outcomes": {
            "abs": {
                "initial_va": abs_stats['vision_baseline_mean'],
                "final_va": abs_stats['vision_final_mean'],
                "va_change": abs_stats['mean_vision_change'],
                "mean_visits_per_patient": abs_stats['mean_visits_per_patient'],
                "injections_per_patient": abs_stats['mean_injections_per_patient']
            },
            "des": {
                "initial_va": des_stats['vision_baseline_mean'],
                "final_va": des_stats['vision_final_mean'],
                "va_change": des_stats['mean_vision_change'],
                "mean_visits_per_patient": des_stats['mean_visits_per_patient'],
                "injections_per_patient": des_stats['mean_injections_per_patient']
            }
        },
        "financial_outcomes": {
            "abs": abs_costs,
            "des": des_costs
        }
    }
    
    with open(output_dir / "summary_report.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Export detailed cost data
    if abs_adapter.tracker.cost_events:
        abs_adapter.tracker.export_to_parquet(output_dir / "abs_costs")
    if des_adapter.tracker.cost_events:
        des_adapter.tracker.export_to_parquet(output_dir / "des_costs")
    
    print(f"\n{'='*60}")
    print("SIMULATION COMPLETE")
    print("="*60)
    print(f"\nResults saved to: {output_dir}")
    print(f"  - Clinical comparison: clinical_outcomes_comparison.png")
    print(f"  - Cost breakdown: cost_breakdown.png")
    print(f"  - Cost effectiveness: cost_effectiveness.png")
    print(f"  - Summary report: summary_report.json")
    print(f"  - Detailed cost data: abs_costs/ and des_costs/")
    
    return summary


if __name__ == "__main__":
    main()