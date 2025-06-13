#!/usr/bin/env python3
"""
Compare multiple protocols with economic analysis.

This script demonstrates using the EconomicsIntegration API to compare
the cost-effectiveness of different treatment protocols.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from simulation_v2.economics import EconomicsIntegration, CostConfig
from simulation_v2.protocols.protocol_spec import ProtocolSpecification


def compare_protocols(protocol_configs, cost_config, n_patients=100, duration_years=2.0):
    """
    Compare multiple protocols with economic analysis.
    
    Args:
        protocol_configs: Dict mapping names to protocol file paths
        cost_config: CostConfig instance
        n_patients: Number of patients per simulation
        duration_years: Simulation duration
        
    Returns:
        DataFrame with comparison results
    """
    results = []
    
    for name, protocol_path in protocol_configs.items():
        print(f"\nRunning {name}...")
        
        # Load protocol
        protocol = ProtocolSpecification.from_yaml(Path(protocol_path))
        
        # Run both ABS and DES for comparison
        for engine_type in ['abs', 'des']:
            print(f"  - {engine_type.upper()} simulation...")
            
            clinical, financial = EconomicsIntegration.run_with_economics(
                engine_type=engine_type,
                protocol_spec=protocol,
                cost_config=cost_config,
                n_patients=n_patients,
                duration_years=duration_years,
                seed=42  # Same seed for fair comparison
            )
            
            # Calculate VA change
            total_va_change = sum(
                p.current_vision - p.baseline_vision 
                for p in clinical.patient_histories.values()
            )
            mean_va_change = total_va_change / clinical.patient_count if clinical.patient_count > 0 else 0
            
            results.append({
                'Protocol': name,
                'Engine': engine_type.upper(),
                'Total Cost': financial.total_cost,
                'Cost per Patient': financial.cost_per_patient,
                'Total Injections': financial.total_injections,
                'Injections per Patient': financial.total_injections / clinical.patient_count,
                'Cost per Injection': financial.cost_per_injection,
                'Mean VA Change': mean_va_change,
                'Cost per Letter': financial.cost_per_letter_gained or float('inf'),
                'Loading Phase Cost': financial.cost_breakdown.by_phase.get('loading', 0),
                'Maintenance Phase Cost': financial.cost_breakdown.by_phase.get('maintenance', 0)
            })
    
    return pd.DataFrame(results)


def visualize_comparison(df):
    """Create comparison visualizations."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Protocol Economic Comparison', fontsize=16)
    
    # 1. Cost per patient by protocol
    ax = axes[0, 0]
    pivot = df.pivot(index='Protocol', columns='Engine', values='Cost per Patient')
    pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Cost per Patient (£)')
    ax.set_title('Cost per Patient Comparison')
    ax.legend(title='Engine')
    
    # 2. Cost effectiveness (cost per letter)
    ax = axes[0, 1]
    pivot = df.pivot(index='Protocol', columns='Engine', values='Cost per Letter')
    # Cap infinite values for visualization
    pivot = pivot.replace([float('inf'), -float('inf')], float('nan'))
    pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Cost per Letter Gained (£)')
    ax.set_title('Cost Effectiveness')
    ax.legend(title='Engine')
    
    # 3. Injection frequency
    ax = axes[1, 0]
    pivot = df.pivot(index='Protocol', columns='Engine', values='Injections per Patient')
    pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Injections per Patient')
    ax.set_title('Treatment Intensity')
    ax.legend(title='Engine')
    
    # 4. Phase cost breakdown (for ABS only)
    ax = axes[1, 1]
    abs_data = df[df['Engine'] == 'ABS']
    loading_costs = abs_data['Loading Phase Cost'].values
    maintenance_costs = abs_data['Maintenance Phase Cost'].values
    protocols = abs_data['Protocol'].values
    
    x = range(len(protocols))
    width = 0.35
    ax.bar(x, loading_costs, width, label='Loading Phase')
    ax.bar(x, maintenance_costs, width, bottom=loading_costs, label='Maintenance Phase')
    ax.set_ylabel('Cost (£)')
    ax.set_title('Cost by Treatment Phase (ABS)')
    ax.set_xticks(x)
    ax.set_xticklabels(protocols)
    ax.legend()
    
    plt.tight_layout()
    return fig


def main():
    """Run protocol comparison with economic analysis."""
    
    print("\n" + "="*60)
    print("Protocol Economic Comparison")
    print("="*60)
    
    # Define protocols to compare
    # For demo, we'll use the same protocol with different parameters
    protocol_configs = {
        'Standard TAE': 'streamlit_app_v2/protocols/eylea.yaml',
        # Add more protocols here as they become available
        # 'Aggressive TAE': 'protocols/eylea_aggressive.yaml',
        # 'Conservative TAE': 'protocols/eylea_conservative.yaml',
    }
    
    # Load cost configuration
    cost_config = CostConfig.from_yaml(Path('protocols/cost_configs/nhs_standard_2025.yaml'))
    print(f"\nUsing cost configuration: {cost_config.metadata['name']}")
    
    # Run comparison
    print("\nRunning simulations...")
    results_df = compare_protocols(
        protocol_configs,
        cost_config,
        n_patients=100,
        duration_years=2.0
    )
    
    # Display results
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    # Format currency columns
    currency_cols = ['Total Cost', 'Cost per Patient', 'Cost per Injection', 
                    'Cost per Letter', 'Loading Phase Cost', 'Maintenance Phase Cost']
    for col in currency_cols:
        results_df[col] = results_df[col].apply(lambda x: f"£{x:,.2f}" if x != float('inf') else 'N/A')
    
    print(results_df.to_string(index=False))
    
    # Save results
    output_dir = Path('output/protocol_comparison')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_dir / 'economic_comparison.csv', index=False)
    print(f"\nResults saved to: {output_dir / 'economic_comparison.csv'}")
    
    # Create visualizations
    print("\nCreating visualizations...")
    # Re-load for plotting (to get numeric values)
    plot_df = compare_protocols(
        protocol_configs,
        cost_config,
        n_patients=100,
        duration_years=2.0
    )
    
    fig = visualize_comparison(plot_df)
    fig.savefig(output_dir / 'economic_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Plots saved to: {output_dir / 'economic_comparison.png'}")
    
    print("\n✅ Comparison complete!")


if __name__ == "__main__":
    main()