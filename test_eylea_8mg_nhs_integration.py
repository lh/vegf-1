#!/usr/bin/env python3
"""
Test Eylea 8mg Integration with NHS Cost Data

This script demonstrates economic analysis using real UK NHS cost data
from the compass_artifact for Eylea 8mg vs 2mg comparison.
"""

import json
import yaml
from pathlib import Path

def load_nhs_costs():
    """Load NHS cost parameters from compass_artifact data."""
    cost_path = Path("protocols/parameter_sets/eylea_8mg/nhs_costs.yaml")
    with open(cost_path, 'r') as f:
        cost_data = yaml.safe_load(f)
    
    print("✓ Loaded NHS cost parameters from compass_artifact data")
    return cost_data

def load_clinical_data():
    """Load clinical trial data from the private repository."""
    clinical_path = Path("eylea_high_dose_data/enhanced_simulation_parameters.json")
    with open(clinical_path, 'r') as f:
        clinical_data = json.load(f)
    
    print("✓ Loaded clinical trial data (PULSAR/PHOTON)")
    return clinical_data

def run_nhs_economic_analysis():
    """Run comprehensive NHS economic analysis."""
    
    print("\n" + "="*60)
    print("EYLEA 8MG NHS ECONOMIC ANALYSIS")
    print("="*60)
    
    try:
        # Load data
        nhs_costs = load_nhs_costs()
        clinical_data = load_clinical_data()
        
        print(f"\n💷 NHS Drug Procurement Costs (after patient access schemes):")
        print(f"   - Eylea 8mg: £{nhs_costs['drug_costs']['aflibercept_8mg']['unit_cost']:,}")
        print(f"   - Eylea 2mg: £{nhs_costs['drug_costs']['aflibercept_2mg']['unit_cost']:,}")
        print(f"   - List prices: £{nhs_costs['drug_costs']['aflibercept_8mg']['list_price']:,} vs £{nhs_costs['drug_costs']['aflibercept_2mg']['list_price']:,}")
        print(f"   - NHS discounts: {nhs_costs['drug_costs']['aflibercept_8mg']['procurement_discount']:.0%} vs {nhs_costs['drug_costs']['aflibercept_2mg']['procurement_discount']:.0%}")
        
        print(f"\n🏥 NHS Visit Costs (per injection):")
        visit_cost = nhs_costs['visit_costs']['injection_visit']['total_excluding_drug']
        print(f"   - OCT monitoring: £{nhs_costs['visit_costs']['injection_visit']['oct_monitoring']}")
        print(f"   - Injection procedure: £{nhs_costs['visit_costs']['injection_visit']['injection_procedure']}")
        print(f"   - Consumables/setup: £{nhs_costs['visit_costs']['injection_visit']['consumables_setup']}")
        print(f"   - Total per visit (excl. drug): £{visit_cost}")
        
        print(f"\n👥 NHS Staff Costs (2024-2025 rates with 28-30% on-costs):")
        consultant_cost = nhs_costs['staff_costs']['consultant_ophthalmologist']['hourly_rate']
        nurse_cost = nhs_costs['staff_costs']['band_6_nurse']['hourly_rate']
        print(f"   - Consultant ophthalmologist: £{consultant_cost}/hour")
        print(f"   - Band 6 nurse: £{nurse_cost}/hour")
        print(f"   - Staff cost per injection: £{consultant_cost * 0.5 + nurse_cost * 1.0:.0f}")
        
        # Annual cost comparison using clinical trial data
        q12_injections = clinical_data['injection_counts']['PULSAR_week48']['q12']
        q8_injections = clinical_data['injection_counts']['PULSAR_week48']['q8_comparator']
        
        drug_cost_8mg = nhs_costs['drug_costs']['aflibercept_8mg']['unit_cost']
        drug_cost_2mg = nhs_costs['drug_costs']['aflibercept_2mg']['unit_cost']
        
        annual_cost_8mg = nhs_costs['annual_costs']['eylea_8mg_q12']['annual_total']
        annual_cost_2mg = nhs_costs['annual_costs']['eylea_2mg_q8']['annual_total']
        cost_difference = nhs_costs['annual_costs']['annual_difference']
        
        print(f"\n📊 Annual NHS Costs (Year 1):")
        print(f"   - Eylea 8mg q12: £{annual_cost_8mg:,} ({q12_injections} injections)")
        print(f"   - Eylea 2mg q8:  £{annual_cost_2mg:,} ({q8_injections} injections)")
        print(f"   - Difference: £{cost_difference:,} more for 8mg")
        print(f"   - Cost per injection saved: £{(q8_injections - q12_injections) * (drug_cost_2mg + visit_cost):,.0f}")
        
        # Extended interval benefits
        q16_savings = nhs_costs['interval_benefits']['reduced_visits_q16']['annual_savings']
        print(f"\n🎯 Extended Interval Benefits:")
        print(f"   - Potential q16 savings: £{q16_savings:,}/year")
        print(f"   - 77% maintain q16 intervals (PULSAR data)")
        print(f"   - Expected q16 savings: £{q16_savings * 0.77:,.0f}/year")
        
        # Safety costs
        ioi_cost_annual_8mg = nhs_costs['real_world_costs']['annual_ioi_cost_8mg']
        ioi_cost_annual_2mg = nhs_costs['real_world_costs']['annual_ioi_cost_2mg']
        print(f"\n⚠️ Real-world Safety Costs (3.7% IOI rate):")
        print(f"   - 8mg annual IOI cost: £{ioi_cost_annual_8mg}")
        print(f"   - 2mg annual IOI cost: £{ioi_cost_annual_2mg}")
        print(f"   - IOI management: £{nhs_costs['safety_costs']['ioi_management']['moderate_case']} per case")
        
        # Budget impact
        eligible_patients = nhs_costs['budget_impact']['eligible_patients_uk']
        potential_switchers = nhs_costs['budget_impact']['potential_8mg_switchers']
        
        # Handle both old field name (annual_budget_increase) and new (annual_budget_savings)
        if 'annual_budget_savings' in nhs_costs['budget_impact']:
            budget_impact = -nhs_costs['budget_impact']['annual_budget_savings']  # Negative because it's savings
            impact_text = "Annual budget SAVINGS"
        else:
            budget_impact = nhs_costs['budget_impact'].get('annual_budget_increase', 0)
            impact_text = "Annual budget increase"
        
        print(f"\n💰 NHS Budget Impact Analysis:")
        print(f"   - Eligible wet AMD patients (UK): {eligible_patients:,}")
        print(f"   - Potential 8mg switchers: {potential_switchers:,}")
        print(f"   - {impact_text}: £{abs(budget_impact):,}")
        
        if budget_impact > 0:
            print(f"   - Cost per QALY: £{budget_impact / (potential_switchers * 0.1):,.0f} (assuming 0.1 QALY gain)")
        else:
            print(f"   - 8mg SAVES money - no QALY justification needed!")
        
        # NICE threshold comparison
        nice_threshold = nhs_costs['economic_parameters']['willingness_to_pay_per_qaly']
        print(f"   - NICE threshold: £{nice_threshold:,}/QALY")
        
        # Value proposition analysis
        print(f"\n📈 Value Proposition:")
        print(f"   - Fewer injections: {q8_injections - q12_injections:.1f} fewer per year")
        print(f"   - Patient convenience: 77-79% maintain extended intervals")
        print(f"   - Superior anatomic outcomes: 63% vs 52% no fluid at week 16")
        print(f"   - NHS capacity: {(q8_injections - q12_injections) * potential_switchers:,.0f} fewer procedures/year")
        
        # Cost-effectiveness scenarios
        print(f"\n💡 Cost-Effectiveness Scenarios:")
        
        # Scenario 1: q16 intervals successful
        q16_success_cost = annual_cost_8mg - q16_savings * 0.77
        print(f"   1. 77% achieve q16 intervals: £{q16_success_cost:,.0f}/year")
        print(f"      vs 2mg q8: £{q16_success_cost - annual_cost_2mg:+,.0f}")
        
        # Scenario 2: Include patient time savings
        patient_time_savings = (q8_injections - q12_injections) * 4 * 25  # 4 hours @ £25/hour
        print(f"   2. Including patient time (£25/hour): £{patient_time_savings:.0f} savings/year")
        print(f"      Net NHS+patient cost: £{cost_difference - patient_time_savings:+,.0f}")
        
        # Scenario 3: NHS capacity value
        procedure_capacity_value = (q8_injections - q12_injections) * visit_cost * 0.5  # 50% capacity value
        print(f"   3. NHS capacity value (50%): £{procedure_capacity_value:.0f} savings/year")
        
        print(f"\n✅ NHS Economic Analysis Complete!")
        print(f"   - Based on real NHS costs from compass_artifact")
        print(f"   - Uses PULSAR/PHOTON clinical trial data")
        print(f"   - Includes real-world safety considerations")
        print(f"   - Ready for NICE technology appraisal format")
        
        return True
        
    except Exception as e:
        print(f"\n❌ NHS analysis failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_nhs_economic_analysis()
    
    if success:
        print(f"\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 Ready for NHS economic modeling with real cost data!")
        print(f"   Next: Create NICE technology appraisal economic model")
    else:
        print(f"\n🔧 Fix NHS cost integration issues")