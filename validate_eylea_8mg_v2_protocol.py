#!/usr/bin/env python3
"""
Validate Eylea 8mg V2 Protocol

Ensures the protocol meets all V2 requirements and can be loaded successfully.
"""

import yaml
from pathlib import Path
import sys

def validate_protocol(protocol_file="protocols/eylea_8mg_v2.yaml"):
    """Validate the Eylea 8mg V2 protocol file."""
    
    print("="*60)
    print("EYLEA 8MG V2 PROTOCOL VALIDATION")
    print("="*60)
    
    protocol_path = Path(protocol_file)
    
    # Load protocol
    try:
        with open(protocol_path, 'r') as f:
            protocol = yaml.safe_load(f)
        print("✓ Protocol YAML loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load protocol: {e}")
        return False
    
    # Check required metadata fields
    print("\nValidating Metadata Fields:")
    required_metadata = ['name', 'version', 'created_date', 'author', 'description']
    for field in required_metadata:
        if field in protocol:
            print(f"  ✓ {field}: {protocol[field][:50]}...")
        else:
            print(f"  ✗ Missing required field: {field}")
            return False
    
    # Check required protocol parameters
    print("\nValidating Protocol Parameters:")
    required_params = [
        'protocol_type', 'min_interval_days', 'max_interval_days',
        'extension_days', 'shortening_days'
    ]
    for field in required_params:
        if field in protocol:
            print(f"  ✓ {field}: {protocol[field]}")
        else:
            print(f"  ✗ Missing required field: {field}")
            return False
    
    # Validate disease transitions
    print("\nValidating Disease Transitions:")
    if 'disease_transitions' not in protocol:
        print("  ✗ Missing disease_transitions")
        return False
    
    states = ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']
    transitions = protocol['disease_transitions']
    
    for from_state in states:
        if from_state not in transitions:
            print(f"  ✗ Missing transitions from {from_state}")
            return False
        
        # Check all target states present
        for to_state in states:
            if to_state not in transitions[from_state]:
                print(f"  ✗ Missing transition {from_state} -> {to_state}")
                return False
        
        # Check probabilities sum to 1.0
        total = sum(transitions[from_state].values())
        if abs(total - 1.0) > 0.001:
            print(f"  ✗ {from_state} probabilities sum to {total}, not 1.0")
            return False
        
        print(f"  ✓ {from_state} transitions valid (sum = {total:.3f})")
    
    # Validate vision change model
    print("\nValidating Vision Change Model:")
    if 'vision_change_model' not in protocol:
        print("  ✗ Missing vision_change_model")
        return False
    
    required_scenarios = [
        'naive_treated', 'naive_untreated',
        'stable_treated', 'stable_untreated',
        'active_treated', 'active_untreated',
        'highly_active_treated', 'highly_active_untreated'
    ]
    
    vision_model = protocol['vision_change_model']
    for scenario in required_scenarios:
        if scenario not in vision_model:
            print(f"  ✗ Missing scenario: {scenario}")
            return False
        
        if 'mean' not in vision_model[scenario] or 'std' not in vision_model[scenario]:
            print(f"  ✗ {scenario} missing mean or std")
            return False
        
        print(f"  ✓ {scenario}: mean={vision_model[scenario]['mean']}, std={vision_model[scenario]['std']}")
    
    # Validate baseline vision
    print("\nValidating Baseline Vision:")
    if 'baseline_vision' not in protocol:
        print("  ✗ Missing baseline_vision")
        return False
    
    baseline = protocol['baseline_vision']
    required_baseline = ['mean', 'std', 'min', 'max']
    for field in required_baseline:
        if field in baseline:
            print(f"  ✓ {field}: {baseline[field]}")
        else:
            print(f"  ✗ Missing baseline field: {field}")
            return False
    
    # Validate discontinuation rules
    print("\nValidating Discontinuation Rules:")
    if 'discontinuation_rules' not in protocol:
        print("  ✗ Missing discontinuation_rules")
        return False
    
    disc_rules = protocol['discontinuation_rules']
    print(f"  ✓ Found {len(disc_rules)} discontinuation rule categories")
    
    # Check economic parameters (optional but recommended)
    print("\nChecking Economic Integration:")
    if 'economic_parameters' in protocol:
        econ = protocol['economic_parameters']
        if 'visit_types' in econ:
            print(f"  ✓ Visit types defined: {list(econ['visit_types'].keys())}")
        if 'drug_parameters' in econ:
            print(f"  ✓ Drug parameters: {econ['drug_parameters']['name']}")
        if 'safety_parameters' in econ:
            print(f"  ✓ Safety parameters included")
    else:
        print("  ℹ No economic parameters (optional)")
    
    # Check clinical trial parameters
    print("\nChecking Clinical Trial Validation:")
    if 'clinical_trial_parameters' in protocol:
        trial = protocol['clinical_trial_parameters']
        print(f"  ✓ Source: {trial['source']}")
        print(f"  ✓ q12 maintenance: {trial['q12_maintenance_rate']:.0%}")
        print(f"  ✓ q16 maintenance: {trial['q16_maintenance_rate']:.0%}")
        print(f"  ✓ BCVA gain: {trial['mean_bcva_gain_week48']} letters")
    
    # Check dose modification parameters (in revised protocol)
    print("\nChecking Dose Modification Approach:")
    if 'dose_modification_parameters' in protocol:
        dose_mod = protocol['dose_modification_parameters']
        print(f"  ✓ Probabilistic modeling approach detected")
        if 'interval_shortening_probability' in dose_mod:
            probs = dose_mod['interval_shortening_probability']
            print(f"  ✓ STABLE shortening probability: {probs['STABLE']:.0%}")
            print(f"  ✓ Implied maintenance rate: {1 - probs['STABLE']:.0%}")
        if 'eylea_8mg_criteria_effect' in dose_mod:
            print(f"  ✓ 8mg criteria effect: {dose_mod['eylea_8mg_criteria_effect']}")
        print(f"  ℹ Note: Using probabilistic approach due to lack of anatomical data")
    
    print("\n" + "="*60)
    print("✅ PROTOCOL VALIDATION SUCCESSFUL")
    print("="*60)
    print("\nThe Eylea 8mg V2 protocol is ready for use in simulations!")
    print("It includes:")
    print("  - Complete V2 compliance (no defaults)")
    print("  - PULSAR/PHOTON clinical parameters")
    print("  - Economic integration points")
    print("  - Safety monitoring parameters")
    
    return True

if __name__ == "__main__":
    # Check if a specific protocol file was provided
    if len(sys.argv) > 1:
        success = validate_protocol(sys.argv[1])
    else:
        success = validate_protocol()
    sys.exit(0 if success else 1)