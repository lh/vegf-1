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
        ['VA outcomes', 'TBD by simulation', 'TBD by simulation', 'TBD by simulation'],
        ['Interval maintenance', 'N/A (fixed)', '~60-70%', '77-79%']
    ]
    
    print("\n📊 Clinical Characteristics:")
    # Print simple table
    for row in clinical_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<25}")
    
    # Resource utilization comparison
    resource_data = [
        ['Resource Utilization', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Annual injections', 'Fixed (~6.5)', 'Variable', 'Variable'],
        ['Drug requirements', 'Standard dose', 'Standard dose', 'Higher dose volume'],
        ['Procedure complexity', 'Standard', 'Standard + monitoring', 'Standard + monitoring'],
        ['Total visits/year', '8-9', '10-12', '8-9'],
        ['Visit predictability', 'High', 'Low', 'Low']
    ]
    
    print("\n📊 Resource Utilization:")
    # Print simple table
    for row in resource_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<25}")
    
    # Advantages/Disadvantages
    print("\n📋 Protocol Characteristics:")
    
    print("\n🔵 Treat-and-Treat 2mg:")
    print("Advantages:")
    print("  ✓ Predictable scheduling (patients know all dates)")
    print("  ✓ Lowest monitoring burden (2 visits/year)")
    print("  ✓ Can be largely nurse-led")
    print("  ✓ Potentially lower resource use")
    print("  ✓ Simplified administration")
    print("Disadvantages:")
    print("  ✗ No personalization")
    print("  ✗ May undertreat active disease (25% risk)")
    print("  ✗ May overtreat stable disease (20% risk)")
    print("  ✗ Fixed schedule may not match disease activity")
    
    print("\n🔵 Treat-and-Extend 2mg:")
    print("Advantages:")
    print("  ✓ Personalized treatment")
    print("  ✓ Treatment matches disease activity")
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
    print("  ✓ Potential for extended intervals")
    print("Disadvantages:")
    print("  ✗ Different cost structure")
    print("  ✗ Real-world IOI risk (3.7%)")
    print("  ✗ Requires stricter monitoring criteria")
    
    # Decision framework
    print("\n🎯 Decision Framework:")
    print("\nTreat-and-Treat characteristics:")
    print("  • Fixed schedule implementation")
    print("  • Predictable visit patterns")
    print("  • Minimal monitoring requirements")
    print("  • Simplified administration")
    
    print("\nTreat-and-Extend 2mg characteristics:")
    print("  • Flexible interval adjustment")
    print("  • Response-based treatment")
    print("  • Regular monitoring required")
    print("  • Standard interval range (4-16 weeks)")
    
    print("\nTreat-and-Extend 8mg characteristics:")
    print("  • Extended interval potential")
    print("  • Stricter modification criteria")
    print("  • PULSAR protocol requirements")
    print("  • Longer maximum intervals (up to 24 weeks)")
    
    # Summary
    print("\n📊 Summary:")
    print("• Different protocols suit different clinical scenarios")
    print("• Resource requirements vary by protocol type")
    print("• Clinical outcomes determined by simulation")

if __name__ == "__main__":
    # Note: This is a simplified comparison
    # Full analysis would load actual protocol data
    create_comparison_table()
    
    print("\n" + "="*80)
    print("Note: This comparison uses representative values.")
    print("Actual outcomes depend on patient population and implementation.")
    print("="*80)