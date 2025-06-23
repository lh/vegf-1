#!/usr/bin/env python
"""
Test script to verify economic analysis integration.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner_with_resources import TimeBasedSimulationRunnerWithResources


def main():
    """Run test simulation with economic tracking."""
    # Load protocol
    protocol_path = Path("protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml")
    if not protocol_path.exists():
        print(f"Protocol not found: {protocol_path}")
        return
    
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_path)
    
    # Create runner with resource tracking
    runner = TimeBasedSimulationRunnerWithResources(spec)
    
    # Run simulation
    print("Running simulation with economic tracking...")
    results = runner.run(
        engine_type='abs',
        n_patients=500,
        duration_years=2,
        seed=12345
    )
    
    # Display basic results
    print("\n=== SIMULATION RESULTS ===")
    print(f"Total patients: {results.patient_count}")
    print(f"Total injections: {results.total_injections}")
    print(f"Final vision (mean ± std): {results.final_vision_mean:.1f} ± {results.final_vision_std:.1f}")
    print(f"Discontinuation rate: {results.discontinuation_rate:.1%}")
    
    # Display economic results
    if hasattr(results, 'total_costs'):
        print("\n=== ECONOMIC ANALYSIS ===")
        costs = results.total_costs
        print(f"Total drug costs: £{costs.get('drug', 0):,.2f}")
        print(f"Total procedure costs: £{costs.get('injection_procedure', 0):,.2f}")
        print(f"Total OCT costs: £{costs.get('oct_scan', 0):,.2f}")
        print(f"Total consultation costs: £{costs.get('consultation', 0):,.2f}")
        print(f"TOTAL COSTS: £{costs.get('total', 0):,.2f}")
        
        if hasattr(results, 'average_cost_per_patient_year'):
            print(f"\nAverage cost per patient-year: £{results.average_cost_per_patient_year:,.2f}")
    
    # Display workload summary
    if hasattr(results, 'workload_summary'):
        print("\n=== WORKLOAD ANALYSIS ===")
        workload = results.workload_summary
        print(f"Total visits: {workload.get('total_visits', 0)}")
        
        # Visits by type
        print("\nVisits by type:")
        for visit_type, count in workload.get('visits_by_type', {}).items():
            print(f"  {visit_type}: {count}")
        
        # Peak daily demand
        print("\nPeak daily demand by role:")
        for role, demand in workload.get('peak_daily_demand', {}).items():
            print(f"  {role}: {demand} patients/day")
        
        # Average utilization
        print("\nAverage utilization by role:")
        for role, util in workload.get('average_utilization', {}).items():
            print(f"  {role}: {util:.1%}")
    
    # Check for bottlenecks
    if hasattr(results, 'bottlenecks') and results.bottlenecks:
        print(f"\n⚠️  BOTTLENECKS DETECTED: {len(results.bottlenecks)} days with capacity issues")
        # Show first few bottlenecks
        for bottleneck in results.bottlenecks[:5]:
            print(f"  {bottleneck['date']}: {bottleneck['role']} - {bottleneck['patients_affected']} patients affected")
    
    # Create workload visualization
    if hasattr(results, 'resource_usage') and results.resource_usage:
        print("\n=== CREATING WORKLOAD VISUALIZATION ===")
        
        # Convert to DataFrame
        workload_data = []
        for date, roles in results.resource_usage.items():
            for role, count in roles.items():
                workload_data.append({
                    'date': date,
                    'role': role,
                    'count': count
                })
        
        if workload_data:
            df = pd.DataFrame(workload_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Plot daily workload for key roles
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for role in ['injector', 'decision_maker']:
                role_data = df[df['role'] == role].copy()
                if not role_data.empty:
                    # Resample to weekly for smoother visualization
                    role_data.set_index('date', inplace=True)
                    weekly = role_data.resample('W')['count'].sum()
                    ax.plot(weekly.index, weekly.values, label=role.replace('_', ' ').title(), linewidth=2)
            
            ax.set_xlabel('Date')
            ax.set_ylabel('Patients per Week')
            ax.set_title('Weekly Workload by Role')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Save plot
            output_path = Path('output/economic_test_workload.png')
            output_path.parent.mkdir(exist_ok=True)
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            print(f"Workload visualization saved to: {output_path}")
            plt.close()
    
    print("\n✅ Economic analysis integration test complete!")
    
    # Save detailed results
    output_file = Path('output/economic_test_results.txt')
    with open(output_file, 'w') as f:
        f.write("ECONOMIC ANALYSIS TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Protocol: {spec.name}\n")
        f.write(f"Simulation date: {datetime.now()}\n")
        f.write(f"Patients: {results.patient_count}\n")
        f.write(f"Duration: 2 years\n\n")
        
        if hasattr(results, 'total_costs'):
            f.write("COST BREAKDOWN\n")
            f.write("-" * 30 + "\n")
            for category, amount in results.total_costs.items():
                if category != 'total':
                    f.write(f"{category}: £{amount:,.2f}\n")
            f.write(f"\nTOTAL: £{results.total_costs.get('total', 0):,.2f}\n")
            f.write(f"Average per patient-year: £{getattr(results, 'average_cost_per_patient_year', 0):,.2f}\n")
    
    print(f"Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()