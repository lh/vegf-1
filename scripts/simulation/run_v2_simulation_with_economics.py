#!/usr/bin/env python3
"""
Run V2 simulation with integrated economics - simplified API demonstration.

This script shows how easy it is to run simulations with cost tracking
using the new EconomicsIntegration API.
"""

from pathlib import Path
from simulation_v2.economics import EconomicsIntegration, CostConfig
from simulation_v2.protocols.protocol_spec import ProtocolSpecification


def main():
    """Demonstrate the simplified economics API."""
    
    print("\n" + "="*60)
    print("V2 Simulation with Economics - Simplified API")
    print("="*60)
    
    # Method 1: Using file paths directly
    print("\n1. Creating engine from files...")
    engine = EconomicsIntegration.create_from_files(
        engine_type='abs',
        protocol_path='streamlit_app_v2/protocols/eylea.yaml',
        cost_config_path='protocols/cost_configs/nhs_standard_2025.yaml',
        n_patients=100,
        seed=42
    )
    
    print("   Running simulation...")
    results = engine.run(duration_years=2.0)
    
    print("   Analyzing costs...")
    cost_config = CostConfig.from_yaml(Path('protocols/cost_configs/nhs_standard_2025.yaml'))
    financial = EconomicsIntegration.analyze_results(results, cost_config)
    
    print(f"\n   Results:")
    print(f"   - Clinical: {results.patient_count} patients, {results.total_injections} injections")
    print(f"   - Financial: £{financial.cost_per_patient:,.2f} per patient")
    
    # Method 2: All-in-one execution
    print("\n2. All-in-one simulation with economics...")
    protocol = ProtocolSpecification.from_yaml(Path('streamlit_app_v2/protocols/eylea.yaml'))
    
    clinical, financial = EconomicsIntegration.run_with_economics(
        engine_type='des',
        protocol_spec=protocol,
        cost_config=cost_config,
        n_patients=50,
        duration_years=3.0,
        seed=123
    )
    
    print(f"\n   Results:")
    print(f"   - Total cost: £{financial.total_cost:,.2f}")
    print(f"   - Cost per injection: £{financial.cost_per_injection:,.2f}")
    if financial.cost_per_letter_gained:
        print(f"   - Cost per letter gained: £{financial.cost_per_letter_gained:,.2f}")
    
    # Method 3: Export results
    print("\n3. Exporting results...")
    output_paths = EconomicsIntegration.export_results(
        financial_results=financial,
        output_dir='output/v2_economics_demo',
        format='all'
    )
    
    for format_type, path in output_paths.items():
        print(f"   - {format_type}: {path}")
    
    # Show financial summary
    print("\n" + "="*60)
    print("FINANCIAL SUMMARY")
    print("="*60)
    print(financial.get_summary_text())
    
    # Compare methods
    print("\n" + "="*60)
    print("API USAGE SUMMARY")
    print("="*60)
    print("✅ Method 1: create_from_files() - Quick setup from YAML files")
    print("✅ Method 2: run_with_economics() - All-in-one simulation + analysis")
    print("✅ Method 3: export_results() - Easy data export in multiple formats")
    print("\nThe API makes it trivial to add economics to any V2 simulation!")


if __name__ == "__main__":
    main()