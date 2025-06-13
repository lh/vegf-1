#!/usr/bin/env python3
"""
Run V2 simulation with integrated cost tracking - simplified using new API.

This demonstrates the new EconomicsIntegration API for adding costs to V2 simulations.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import V2 simulation components
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.economics import EconomicsIntegration, CostConfig


def main():
    """Run V2 simulation with economics using the new simplified API."""
    
    print("=== V2 Simulation with Economics (New API) ===")
    print(f"Started at: {datetime.now()}")
    
    # Load configurations
    print("\n1. Loading configurations...")
    protocol = ProtocolSpecification.from_yaml(Path("protocols/eylea.yaml"))
    cost_config = CostConfig.from_yaml(Path("costs/nhs_standard.yaml"))
    
    print(f"   Protocol: {protocol.name}")
    print(f"   Cost Config: {cost_config.metadata.get('name', 'Unknown')}")
    
    # Simulation parameters
    n_patients = 50
    duration_years = 2.0
    seed = 42
    
    print(f"\n2. Simulation parameters:")
    print(f"   Patients: {n_patients}")
    print(f"   Duration: {duration_years} years")
    print(f"   Seed: {seed}")
    
    # Run both ABS and DES for comparison
    results = {}
    
    for engine_type in ['abs', 'des']:
        print(f"\n3. Running {engine_type.upper()} simulation with economics...")
        
        # Use the new EconomicsIntegration API - this is the main improvement!
        clinical_results, financial_results = EconomicsIntegration.run_with_economics(
            engine_type=engine_type,
            protocol_spec=protocol,
            cost_config=cost_config,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed
        )
        
        results[engine_type] = {
            'clinical': clinical_results,
            'financial': financial_results
        }
        
        # Display results
        print(f"   Clinical Results:")
        print(f"     Mean VA change: {clinical_results.mean_va_change:.1f} letters")
        print(f"     Simulation duration: {clinical_results.duration_years:.1f} years")
        print(f"     Total patients: {len(clinical_results.patient_histories)}")
        
        print(f"   Financial Results:")
        print(f"     Total cost: £{financial_results.total_cost:,.2f}")
        print(f"     Cost per patient: £{financial_results.cost_per_patient:,.2f}")
        print(f"     Total injections: {financial_results.total_injections}")
        print(f"     Cost per injection: £{financial_results.cost_per_injection:,.2f}")
        if financial_results.cost_per_letter_gained:
            print(f"     Cost per letter gained: £{financial_results.cost_per_letter_gained:,.2f}")
    
    # Export results
    print(f"\n4. Exporting results...")
    output_dir = Path("output/v2_economics_simplified")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for engine_type, result_data in results.items():
        # Export financial summary
        financial_summary = {
            'summary': {
                'total_cost': result_data['financial'].total_cost,
                'total_patients': result_data['financial'].total_patients,
                'cost_per_patient': result_data['financial'].cost_per_patient,
                'total_injections': result_data['financial'].total_injections,
                'cost_per_injection': result_data['financial'].cost_per_injection,
                'total_va_change': result_data['financial'].total_va_change,
                'cost_per_letter_gained': result_data['financial'].cost_per_letter_gained
            },
            'breakdown': result_data['financial'].cost_breakdown.to_dict(),
            'metadata': {
                'engine_type': engine_type,
                'analysis_date': datetime.now().isoformat(),
                'currency': 'GBP',
                'cost_config_name': result_data['financial'].cost_config_name
            }
        }
        
        # Save JSON
        with open(output_dir / f'{engine_type}_financial_results.json', 'w') as f:
            json.dump(financial_summary, f, indent=2, default=str)
    
    # Create comparison
    print(f"\n5. Creating comparison...")
    comparison = {
        'abs_cost_per_patient': results['abs']['financial'].cost_per_patient,
        'des_cost_per_patient': results['des']['financial'].cost_per_patient,
        'abs_cost_per_injection': results['abs']['financial'].cost_per_injection,
        'des_cost_per_injection': results['des']['financial'].cost_per_injection,
        'abs_va_change': results['abs']['clinical'].mean_va_change,
        'des_va_change': results['des']['clinical'].mean_va_change,
        'abs_cost_per_letter': results['abs']['financial'].cost_per_letter_gained,
        'des_cost_per_letter': results['des']['financial'].cost_per_letter_gained
    }
    
    with open(output_dir / 'engine_comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2, default=str)
    
    print(f"   Results exported to: {output_dir}")
    
    print(f"\n=== Completed at: {datetime.now()} ===")
    
    # Summary comparison
    print(f"\n=== Engine Comparison ===")
    print(f"ABS: £{results['abs']['financial'].cost_per_patient:,.2f} per patient")
    print(f"DES: £{results['des']['financial'].cost_per_patient:,.2f} per patient")
    
    if results['abs']['financial'].cost_per_letter_gained and results['des']['financial'].cost_per_letter_gained:
        print(f"ABS: £{results['abs']['financial'].cost_per_letter_gained:,.2f} per letter gained")
        print(f"DES: £{results['des']['financial'].cost_per_letter_gained:,.2f} per letter gained")


if __name__ == "__main__":
    main()