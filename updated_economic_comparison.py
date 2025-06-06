#!/usr/bin/env python3
"""
Updated Economic Comparison with Correct Pricing
Shows how 8mg is now CHEAPER than 2mg due to strategic pricing
"""

def show_updated_economics():
    """Display the dramatic change in economics with correct pricing."""
    
    print("\n" + "="*80)
    print("AFLIBERCEPT PRICING UPDATE - ECONOMIC IMPACT")
    print("="*80)
    
    # Pricing comparison
    print("\n💊 DRUG PRICING (per injection)")
    print("-" * 60)
    print(f"{'Product':<25} {'List Price':<15} {'NHS Price':<15} {'Discount':<15}")
    print(f"{'Aflibercept 2mg':<25} {'£816':<15} {'£457':<15} {'44% off':<15}")
    print(f"{'Aflibercept 8mg':<25} {'£998':<15} {'£339':<15} {'66% off':<15}")
    print(f"{'Biosimilar (est)':<25} {'£400':<15} {'£229':<15} {'43% off':<15}")
    print(f"\n{'KEY FINDING:':<25} {'8mg is £118 CHEAPER per injection than 2mg!'}")
    
    # Annual cost comparison
    print("\n📊 ANNUAL COST COMPARISON (Drug + Procedure costs)")
    print("-" * 80)
    print(f"{'Protocol':<30} {'Injections/yr':<15} {'Drug Cost':<15} {'Total Cost':<15} {'vs 2mg T&E':<15}")
    print(f"{'Treat & Extend 2mg':<30} {'6.9':<15} {'£3,153':<15} {'£6,582':<15} {'--':<15}")
    print(f"{'Treat & Extend 8mg':<30} {'6.1':<15} {'£2,068':<15} {'£5,100':<15} {'SAVES £1,482':<15}")
    print(f"{'Treat & Treat 2mg':<30} {'6.5':<15} {'£2,971':<15} {'£6,084':<15} {'SAVES £498':<15}")
    print(f"{'Biosimilar T&E':<30} {'6.9':<15} {'£1,580':<15} {'£5,009':<15} {'SAVES £1,573':<15}")
    
    # Strategic implications
    print("\n🎯 STRATEGIC IMPLICATIONS")
    print("-" * 60)
    print("1. Eylea 8mg is now the CHEAPEST branded option")
    print("2. Only biosimilars will be cheaper (by just £91/year)")
    print("3. Complete reversal of previous economic analysis")
    print("4. No QALY justification needed - 8mg SAVES money")
    
    # Budget impact
    print("\n💰 NHS BUDGET IMPACT")
    print("-" * 60)
    print("If 28,000 patients switch from 2mg to 8mg:")
    print(f"  • Annual savings: £41.5 million")
    print(f"  • Per CCG (assuming 200 CCGs): £207,500 saved")
    print(f"  • Plus capacity savings from fewer visits")
    
    # Decision matrix
    print("\n📋 UPDATED DECISION MATRIX")
    print("-" * 60)
    print("Clinical Need                    Recommended Option           Rationale")
    print("-" * 80)
    print("New to treatment                 Eylea 8mg                   Lowest cost + best intervals")
    print("Stable on 2mg                    Switch to 8mg               Save money + reduce visits")
    print("Cost minimization only           Biosimilar when available   Cheapest option")
    print("Extended intervals crucial       Eylea 8mg                   Best interval maintenance")
    
    # Timeline considerations
    print("\n⏰ TIMING CONSIDERATIONS")
    print("-" * 60)
    print("• Current window: 8mg priced to gain market share")
    print("• Biosimilar entry: Will disrupt 2mg market")
    print("• Strategic opportunity: Lock in 8mg before biosimilar launch")
    print("• Price risk: 8mg discount may reduce post-biosimilar")
    
    print("\n" + "="*80)
    print("CONCLUSION: Eylea 8mg has transformed from premium product to cost-saving option")
    print("="*80)

if __name__ == "__main__":
    show_updated_economics()