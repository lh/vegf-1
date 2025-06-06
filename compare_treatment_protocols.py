#!/usr/bin/env python3
"""
Compare Treatment Protocols: Treat-and-Treat vs Treat-and-Extend vs Eylea 8mg

This script compares the clinical and economic outcomes of different treatment protocols.
"""

import yaml
from pathlib import Path

def load_protocol_data():
    """Load all protocol files and their associated costs."""
    protocols = {
        'Treat-and-Treat 2mg': {
            'protocol': 'protocols/eylea_2mg_treat_and_treat.yaml',
            'costs': 'protocols/parameter_sets/eylea_2mg_treat_and_treat/nhs_costs.yaml'
        },
        'Treat-and-Extend 2mg': {
            'protocol': 'protocols/eylea.yaml',  # Assuming this exists
            'costs': 'protocols/parameter_sets/eylea/nhs_costs.yaml'  # May need to create
        },
        'Treat-and-Extend 8mg': {
            'protocol': 'protocols/eylea_8mg_v2_revised.yaml',
            'costs': 'protocols/parameter_sets/eylea_8mg/nhs_costs.yaml'
        }
    }
    
    data = {}
    for name, paths in protocols.items():
        protocol_path = Path(paths['protocol'])
        cost_path = Path(paths['costs'])
        
        if protocol_path.exists():
            with open(protocol_path, 'r') as f:
                protocol_data = yaml.safe_load(f)
        else:
            protocol_data = None
            
        if cost_path.exists():
            with open(cost_path, 'r') as f:
                cost_data = yaml.safe_load(f)
        else:
            cost_data = None
            
        data[name] = {
            'protocol': protocol_data,
            'costs': cost_data
        }
    
    return data

def create_comparison_table():
    """Create a comprehensive comparison table."""
    
    print("\n" + "="*80)
    print("TREATMENT PROTOCOL COMPARISON")
    print("="*80)
    
    # Clinical comparison
    clinical_data = [
        ['Protocol', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Type', 'Fixed intervals', 'Flexible intervals', 'Flexible intervals'],
        ['Loading phase', '3 × monthly (4-5 wks)', '3 × monthly', '3 × monthly'],
        ['Maintenance', 'Fixed q8-9 weeks', 'q4-16 weeks', 'q8-24 weeks'],
        ['Dose modification', 'None', 'Based on activity', 'Stricter criteria'],
        ['Monitoring frequency', 'Low (2/year)', 'High (8-12/year)', 'Medium (6-8/year)'],
        ['Expected VA gain Y1', '~5.5 letters', '~7-8 letters', '~6.7 letters'],
        ['Interval maintenance', 'N/A (fixed)', '~60-70%', '77-79%']
    ]
    
    print("\n📊 Clinical Characteristics:")
    # Print simple table
    for row in clinical_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<25}")
    
    # Economic comparison (Year 1)
    economic_data = [
        ['Cost Component', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Annual injections', '6.5', '6.9', '6.1'],
        ['Drug cost/year', '£3,088', '£3,278', '£10,675'],
        ['Procedure costs/year', '£3,113', '£3,429', '£3,032'],
        ['Total NHS cost/year', '£6,201', '£6,707', '£13,707'],
        ['Total visits/year', '8.5', '10-12', '8-9'],
        ['Patient travel cost', '£56', '£80-96', '£64-72']
    ]
    
    print("\n💰 Economic Comparison (Year 1):")
    # Print simple table
    for row in economic_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<25}")
    
    # Advantages/Disadvantages
    print("\n📋 Protocol Characteristics:")
    
    print("\n🔵 Treat-and-Treat 2mg:")
    print("Advantages:")
    print("  ✓ Predictable scheduling (patients know all dates)")
    print("  ✓ Lowest monitoring burden (2 visits/year)")
    print("  ✓ Can be largely nurse-led")
    print("  ✓ Lowest total cost (£6,201/year)")
    print("  ✓ Simplified administration")
    print("Disadvantages:")
    print("  ✗ No personalization")
    print("  ✗ May undertreat active disease (25% risk)")
    print("  ✗ May overtreat stable disease (20% risk)")
    print("  ✗ Lower expected vision gains")
    
    print("\n🔵 Treat-and-Extend 2mg:")
    print("Advantages:")
    print("  ✓ Personalized treatment")
    print("  ✓ Better vision outcomes")
    print("  ✓ Can extend intervals when stable")
    print("  ✓ Responsive to disease activity")
    print("Disadvantages:")
    print("  ✗ High monitoring burden")
    print("  ✗ Unpredictable scheduling")
    print("  ✗ More complex administration")
    print("  ✗ Higher visit count")
    
    print("\n🔵 Treat-and-Extend 8mg:")
    print("Advantages:")
    print("  ✓ Extended intervals (77-79% maintain)")
    print("  ✓ Fewer injections (6.1/year)")
    print("  ✓ Superior anatomic outcomes")
    print("  ✓ Good vision gains")
    print("Disadvantages:")
    print("  ✗ Highest drug cost (£10,675/year)")
    print("  ✗ Exceeds NICE threshold without QALY gains")
    print("  ✗ Real-world IOI risk (3.7%)")
    print("  ✗ Requires stricter monitoring criteria")
    
    # Decision framework
    print("\n🎯 Decision Framework:")
    print("\nChoose Treat-and-Treat when:")
    print("  • NHS capacity is constrained")
    print("  • Patient compliance is a concern")
    print("  • Predictability is valued")
    print("  • Cost minimization is priority")
    
    print("\nChoose Treat-and-Extend 2mg when:")
    print("  • Optimizing vision outcomes")
    print("  • Adequate monitoring capacity")
    print("  • Standard of care required")
    print("  • Cost-effectiveness acceptable")
    
    print("\nChoose Treat-and-Extend 8mg when:")
    print("  • Reducing injection burden critical")
    print("  • Patient convenience paramount")
    print("  • Budget allows premium pricing")
    print("  • Extended intervals achievable")
    
    # Cost-effectiveness summary
    print("\n📊 Cost-Effectiveness Summary:")
    print("• Treat-and-Treat: Lowest cost, acceptable outcomes")
    print("• T&E 2mg: Standard cost-effectiveness")
    print("• T&E 8mg: Requires >0.23 QALY gain for NICE threshold")

if __name__ == "__main__":
    # Note: This is a simplified comparison
    # Full analysis would load actual protocol data
    create_comparison_table()
    
    print("\n" + "="*80)
    print("Note: This comparison uses representative values.")
    print("Actual outcomes depend on patient population and implementation.")
    print("="*80)