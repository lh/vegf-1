#!/usr/bin/env python3
"""
Compare Treatment Protocols: Structure and Economics Only

This script compares the STRUCTURAL differences between protocols.
Clinical outcomes will be determined by simulation.
"""

import yaml
from pathlib import Path

def create_comparison_table():
    """Create a comparison of protocol structures and known economic factors."""
    
    print("\n" + "="*80)
    print("TREATMENT PROTOCOL STRUCTURAL COMPARISON")
    print("="*80)
    
    # Protocol structure comparison
    protocol_data = [
        ['Feature', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Protocol Type', 'Fixed intervals', 'Flexible intervals', 'Flexible intervals'],
        ['Loading phase', '3 × monthly (4-5 wks)', '3 × monthly', '3 × monthly'],
        ['Maintenance intervals', 'Fixed q8-9 weeks', 'q4-16 weeks', 'q8-24 weeks'],
        ['Dose modification', 'None', 'Based on disease activity', 'Stricter criteria (PULSAR)'],
        ['Interval adjustment', 'Not allowed', '±4 weeks', '±4 weeks'],
        ['Decision points', 'Annual review only', 'Every visit', 'Every visit']
    ]
    
    print("\n📋 Protocol Structure:")
    for row in protocol_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<30}")
    
    # Monitoring structure
    monitoring_data = [
        ['Monitoring Type', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Clinical assessment', '1× (post-loading)', 'Every injection visit', 'Every injection visit'],
        ['Annual review', 'Yes', 'Yes', 'Yes'],
        ['OCT frequency', '2/year', 'Every visit', 'Every visit'],
        ['Total monitoring/year', '2', '8-12 (varies)', '6-8 (varies)']
    ]
    
    print("\n🔍 Monitoring Requirements:")
    for row in monitoring_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<30}")
    
    # Known economic factors (costs only, not outcomes)
    economic_data = [
        ['Cost Component', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Drug cost/injection', '£457', '£457', '£339'],
        ['Injection procedure', '£354', '£497', '£497'],
        ['Monitoring visit', '£306', 'Included above', 'Included above'],
        ['Annual review', '£506', '£506', '£506'],
        ['Predictable costs', 'Yes', 'No', 'No'],
        ['Note', 'Updated pricing', 'Updated pricing', '66% discount - CHEAPER!']
    ]
    
    print("\n💰 Known Cost Components (NHS):")
    for row in economic_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<30}")
    
    # Visit calculations (structural, not outcome-based)
    visit_data = [
        ['Visit Calculations', 'Treat-and-Treat 2mg', 'Treat-and-Extend 2mg', 'Treat-and-Extend 8mg'],
        ['Year 1 loading', '3 injections', '3 injections', '3 injections'],
        ['Year 1 maintenance', '3-4 injections', 'Variable', 'Variable'],
        ['Year 1 total (calc)', '6-7 injections', 'TBD by simulation', 'TBD by simulation'],
        ['Year 2+ (calc)', '6 injections', 'TBD by simulation', 'TBD by simulation']
    ]
    
    print("\n📅 Visit Frequency (Structural):")
    for row in visit_data:
        print(f"{row[0]:<25} {row[1]:<25} {row[2]:<25} {row[3]:<30}")
    
    # Implementation considerations (factual only)
    print("\n🏥 Implementation Characteristics:")
    
    print("\n🔵 Treat-and-Treat 2mg:")
    print("Structure:")
    print("  • Fixed 8-9 week intervals after loading")
    print("  • No interval adjustments allowed")
    print("  • Minimal monitoring (2 visits/year)")
    print("  • Can schedule all visits in advance")
    print("  • Potential for nurse-led injection visits")
    
    print("\n🔵 Treat-and-Extend 2mg:")
    print("Structure:")
    print("  • Intervals adjust based on disease activity")
    print("  • Range: 4-16 weeks")
    print("  • Full monitoring at each visit")
    print("  • Scheduling depends on treatment response")
    print("  • Requires clinical decision-making each visit")
    
    print("\n🔵 Treat-and-Extend 8mg:")
    print("Structure:")
    print("  • Extended intervals possible (up to 24 weeks)")
    print("  • Stricter criteria for interval changes (PULSAR protocol)")
    print("  • 77-79% maintain q12-16 weeks (PULSAR trial data)")
    print("  • Higher drug cost per injection")
    print("  • Real-world IOI rate: 3.7% vs 1% in trials")
    
    print("\n📊 Outcomes:")
    print("Clinical effectiveness will be determined by simulation.")
    print("No assumptions about relative effectiveness are made.")
    
    print("\n" + "="*80)
    print("Note: This comparison shows structural differences only.")
    print("Clinical outcomes require simulation with appropriate parameters.")
    print("="*80)

if __name__ == "__main__":
    create_comparison_table()