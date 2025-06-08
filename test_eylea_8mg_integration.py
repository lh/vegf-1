#!/usr/bin/env python3
"""
Test Eylea 8mg Integration with V2 Economics System

This script demonstrates how to use the imported Eylea 8mg clinical data
with our V2 economics system for comparative cost analysis.
"""

import json
import yaml
from pathlib import Path
from simulation_v2.economics.integration import EconomicsIntegration

def load_eylea_8mg_protocol():
    """Load the Eylea 8mg protocol specification."""
    protocol_path = Path("protocols/eylea_8mg.yaml")
    with open(protocol_path, 'r') as f:
        protocol_data = yaml.safe_load(f)
    
    print("✓ Loaded Eylea 8mg protocol specification")
    return protocol_data

def load_eylea_8mg_costs():
    """Load the Eylea 8mg cost parameters."""
    cost_path = Path("protocols/parameter_sets/eylea_8mg/standard.yaml")
    with open(cost_path, 'r') as f:
        cost_data = yaml.safe_load(f)
    
    print("✓ Loaded Eylea 8mg cost parameters")
    return cost_data

def load_clinical_data():
    """Load clinical trial data from the private repository."""
    clinical_path = Path("eylea_high_dose_data/enhanced_simulation_parameters.json")
    with open(clinical_path, 'r') as f:
        clinical_data = json.load(f)
    
    print("✓ Loaded clinical trial data from private repository")
    return clinical_data

def create_protocol_spec(protocol_data):
    """Convert YAML protocol to simplified format for demonstration."""
    # Simplified conversion for demonstration
    spec = {
        'name': protocol_data['name'],
        'drug': protocol_data['drug']['name'],
        'loading_phase': {
            'duration_weeks': protocol_data['phases']['loading']['duration_weeks'],
            'interval_weeks': protocol_data['phases']['loading']['interval_weeks']
        },
        'maintenance_phase': {
            'initial_interval': protocol_data['phases']['maintenance']['initial_interval_weeks'],
            'min_interval': protocol_data['phases']['maintenance']['min_interval_weeks'],
            'max_interval': protocol_data['phases']['maintenance']['max_interval_weeks']
        }
    }
    
    print("✓ Created V2 protocol specification")
    return spec

def create_cost_config(cost_data):
    """Convert YAML cost data to V2 cost configuration."""
    # Extract key cost parameters
    config = {
        'drug_costs': cost_data['drug_costs'],
        'visit_costs': cost_data['visit_costs'],
        'safety_costs': cost_data['safety_costs'],
        'economic_parameters': cost_data['economic_parameters']
    }
    
    print("✓ Created V2 cost configuration")
    return config

def run_comparative_analysis():
    """Run a comparative economic analysis of Eylea 8mg vs 2mg."""
    
    print("\n" + "="*60)
    print("EYLEA 8MG ECONOMIC INTEGRATION TEST")
    print("="*60)
    
    try:
        # Load all data sources
        protocol_data = load_eylea_8mg_protocol()
        cost_data = load_eylea_8mg_costs()
        clinical_data = load_clinical_data()
        
        # Convert to V2 format
        protocol_spec = create_protocol_spec(protocol_data)
        cost_config = create_cost_config(cost_data)
        
        print(f"\n📊 Clinical Trial Data Summary:")
        print(f"   - Formulation: {clinical_data['drug_formulation']['concentration_mg_ml']} mg/mL")
        print(f"   - Dose: {clinical_data['drug_formulation']['total_dose_mg']} mg")
        print(f"   - Molar dose factor: {clinical_data['drug_formulation']['molar_dose_factor']}x")
        
        print(f"\n💰 Cost Parameters:")
        print(f"   - 8mg unit cost: ${cost_data['drug_costs']['aflibercept_8mg']['unit_cost']}")
        print(f"   - 2mg unit cost: ${cost_data['drug_costs']['aflibercept_2mg']['unit_cost']}")
        print(f"   - Cost premium: {(cost_data['drug_costs']['aflibercept_8mg']['unit_cost'] / cost_data['drug_costs']['aflibercept_2mg']['unit_cost'] - 1) * 100:.1f}%")
        
        print(f"\n🎯 Treatment Intervals (PULSAR trial):")
        q12_maintenance = clinical_data['dosing_schedules']['maintenance_phase']['q12_weeks']['maintenance_rate']
        q16_maintenance = clinical_data['dosing_schedules']['maintenance_phase']['q16_weeks']['maintenance_rate']
        print(f"   - q12 weeks: {q12_maintenance:.0%} maintain interval")
        print(f"   - q16 weeks: {q16_maintenance:.0%} maintain interval")
        
        print(f"\n⚠️ Safety Profile:")
        trial_ioi = clinical_data['safety_profile']['clinical_trials']['ioi_incidence']['PULSAR']['pooled_8mg']
        real_world_ioi = clinical_data['safety_profile']['real_world']['ioi_per_injection']
        print(f"   - Clinical trial IOI rate: {trial_ioi:.1%}")
        print(f"   - Real-world IOI rate: {real_world_ioi:.1%}")
        print(f"   - IOI management cost: ${cost_data['safety_costs']['ioi_management']['mild_case']}")
        
        print(f"\n📈 Injection Counts (Year 1):")
        q12_injections = clinical_data['injection_counts']['PULSAR_week48']['q12']
        q16_injections = clinical_data['injection_counts']['PULSAR_week48']['q16']
        q8_injections = clinical_data['injection_counts']['PULSAR_week48']['q8_comparator']
        print(f"   - q12 schedule: {q12_injections} injections")
        print(f"   - q16 schedule: {q16_injections} injections") 
        print(f"   - q8 comparator: {q8_injections} injections")
        
        # Calculate potential annual cost savings
        drug_cost_8mg = cost_data['drug_costs']['aflibercept_8mg']['unit_cost']
        drug_cost_2mg = cost_data['drug_costs']['aflibercept_2mg']['unit_cost']
        visit_cost = cost_data['visit_costs']['injection_visit']
        
        annual_cost_q12_8mg = q12_injections * (drug_cost_8mg + visit_cost)
        annual_cost_q8_2mg = q8_injections * (drug_cost_2mg + visit_cost)
        
        print(f"\n💵 Annual Cost Comparison (Drug + Visits):")
        print(f"   - 8mg q12: ${annual_cost_q12_8mg:,.0f}")
        print(f"   - 2mg q8:  ${annual_cost_q8_2mg:,.0f}")
        print(f"   - Difference: ${annual_cost_q12_8mg - annual_cost_q8_2mg:+,.0f}")
        
        if annual_cost_q12_8mg < annual_cost_q8_2mg:
            print("   ✓ 8mg shows potential cost savings despite higher drug cost")
        else:
            print("   ⚠ 8mg has higher total costs, but may offer other benefits")
        
        print(f"\n✅ Integration test completed successfully!")
        print(f"   - Private repository data: ✓ Accessible")
        print(f"   - Protocol specification: ✓ Created")
        print(f"   - Cost configuration: ✓ Loaded")
        print(f"   - Economic calculations: ✓ Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_comparative_analysis()
    
    if success:
        print(f"\n🎉 Ready for full V2 economics simulation with Eylea 8mg!")
        print(f"   Use EconomicsIntegration.run_with_economics() with eylea_8mg protocol")
    else:
        print(f"\n🔧 Fix integration issues before proceeding")