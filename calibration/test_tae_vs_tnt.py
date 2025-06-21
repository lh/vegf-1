#!/usr/bin/env python3
"""
Test T&E vs T&T protocols to ensure they work correctly and produce comparable results.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import yaml
from eylea_calibration_framework import EyleaCalibrationFramework, ParameterSet


def test_protocol_loading():
    """Test that both protocols load correctly."""
    print("Testing protocol loading...\n")
    
    # Test T&E protocol
    tae_path = Path("protocols/v2/aflibercept_tae_8week_min.yaml")
    try:
        with open(tae_path) as f:
            tae_data = yaml.safe_load(f)
        print(f"✓ T&E protocol loaded: {tae_data['name']}")
        print(f"  Protocol type: {tae_data['protocol_type']}")
        print(f"  Min interval: {tae_data['min_interval_days']} days")
        print(f"  Max interval: {tae_data['max_interval_days']} days")
    except Exception as e:
        print(f"✗ Failed to load T&E protocol: {e}")
        return False
    
    # Test T&T protocol
    tnt_path = Path("protocols/v2/aflibercept_treat_and_treat.yaml")
    try:
        with open(tnt_path) as f:
            tnt_data = yaml.safe_load(f)
        print(f"\n✓ T&T protocol loaded: {tnt_data['name']}")
        print(f"  Protocol type: {tnt_data['protocol_type']}")
        print(f"  Min interval: {tnt_data['min_interval_days']} days")
        print(f"  Max interval: {tnt_data['max_interval_days']} days")
    except Exception as e:
        print(f"✗ Failed to load T&T protocol: {e}")
        return False
    
    return True


def run_protocol_comparison():
    """Run both protocols and compare results."""
    print("\n" + "="*60)
    print("RUNNING PROTOCOL COMPARISON")
    print("="*60)
    
    # Initialize frameworks
    tae_framework = EyleaCalibrationFramework()
    tnt_framework = EyleaCalibrationFramework()
    
    # Test T&E protocol
    print("\n1. Testing T&E Protocol (8-week minimum)")
    print("-" * 40)
    
    tae_params = ParameterSet(
        name="tae_8week",
        description="T&E with 8-week minimum interval",
        use_loading_phase=True,
        use_time_based_discontinuation=True,
        use_response_based_vision=True,
        use_baseline_distribution=False,
        use_response_heterogeneity=True,
        good_responder_ratio=0.60,   # 60% optimal responders
        average_responder_ratio=0.30,
        poor_responder_ratio=0.10,
        good_responder_multiplier=1.8,
        average_responder_multiplier=1.0,
        poor_responder_multiplier=0.5,
        protocol_interval=56  # Starting interval
    )
    
    # Note: For now, we'll use the existing protocol loading mechanism
    # In production, we'd update to use EnhancedProtocolSpecification
    try:
        # Create a temporary protocol without base import for testing
        tae_protocol_path = Path("calibration/test_protocols/tae_test.yaml")
        tae_framework.create_test_protocol(tae_params, tae_protocol_path)
        
        # Run simulation
        tae_result = tae_framework.test_parameters(tae_params, n_patients=100)
        
    except Exception as e:
        print(f"Error running T&E protocol: {e}")
        return
    
    # Test T&T protocol  
    print("\n2. Testing T&T Protocol (Fixed q8w)")
    print("-" * 40)
    
    tnt_params = ParameterSet(
        name="tnt_fixed",
        description="Fixed q8w dosing (T&T)",
        use_loading_phase=True,
        use_time_based_discontinuation=True,
        use_response_based_vision=True,
        use_baseline_distribution=False,
        use_response_heterogeneity=True,
        good_responder_ratio=0.30,   # Standard VIEW-like distribution
        average_responder_ratio=0.50,
        poor_responder_ratio=0.20,
        good_responder_multiplier=1.8,
        average_responder_multiplier=1.0,
        poor_responder_multiplier=0.5,
        protocol_interval=56  # Fixed 8 weeks
    )
    
    try:
        # For T&T, we need to ensure it's recognized as fixed_interval
        # This would be handled by the enhanced spec in production
        tnt_result = tnt_framework.test_parameters(tnt_params, n_patients=100)
        
    except Exception as e:
        print(f"Error running T&T protocol: {e}")
        return
    
    # Compare results
    print("\n" + "="*60)
    print("PROTOCOL COMPARISON RESULTS")
    print("="*60)
    
    print("\nYear 1 Outcomes:")
    print(f"{'Metric':<30} {'T&E':>10} {'T&T':>10} {'Difference':>12}")
    print("-" * 64)
    
    vision_diff = tnt_result.vision_gain_year1 - tae_result.vision_gain_year1
    print(f"{'Mean BCVA change (letters)':<30} {tae_result.vision_gain_year1:>10.1f} {tnt_result.vision_gain_year1:>10.1f} {vision_diff:>+12.1f}")
    
    inj_diff = tnt_result.injections_year1 - tae_result.injections_year1
    print(f"{'Mean injections':<30} {tae_result.injections_year1:>10.1f} {tnt_result.injections_year1:>10.1f} {inj_diff:>+12.1f}")
    
    disc_diff = (tnt_result.discontinuation_year1 - tae_result.discontinuation_year1) * 100
    print(f"{'Discontinuation rate (%)':<30} {tae_result.discontinuation_year1*100:>10.1f} {tnt_result.discontinuation_year1*100:>10.1f} {disc_diff:>+12.1f}")
    
    print("\nYear 2 Cumulative Outcomes:")
    print(f"{'Metric':<30} {'T&E':>10} {'T&T':>10} {'Difference':>12}")
    print("-" * 64)
    
    vision2_diff = tnt_result.vision_year2 - tae_result.vision_year2
    print(f"{'Mean BCVA change (letters)':<30} {tae_result.vision_year2:>10.1f} {tnt_result.vision_year2:>10.1f} {vision2_diff:>+12.1f}")
    
    total_inj_tae = tae_result.injections_year1 + tae_result.injections_year2
    total_inj_tnt = tnt_result.injections_year1 + tnt_result.injections_year2
    total_inj_diff = total_inj_tnt - total_inj_tae
    print(f"{'Total injections':<30} {total_inj_tae:>10.1f} {total_inj_tnt:>10.1f} {total_inj_diff:>+12.1f}")
    
    disc2_diff = (tnt_result.discontinuation_year2 - tae_result.discontinuation_year2) * 100
    print(f"{'Discontinuation rate (%)':<30} {tae_result.discontinuation_year2*100:>10.1f} {tnt_result.discontinuation_year2*100:>10.1f} {disc2_diff:>+12.1f}")
    
    # Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    if vision_diff > 0:
        print(f"✓ T&T shows better vision outcomes (+{vision_diff:.1f} letters)")
    else:
        print(f"✓ T&E shows better vision outcomes (+{-vision_diff:.1f} letters)")
    
    if abs(inj_diff) < 0.5:
        print("✓ Similar injection burden in Year 1 (as expected with 8-week constraint)")
    else:
        print(f"✗ Unexpected injection difference: {inj_diff:+.1f}")
    
    print("\nNote: These results use temporary test protocols.")
    print("Full implementation would use the enhanced protocol spec with base config import.")


def main():
    """Run all tests."""
    print("T&E vs T&T Protocol Testing\n")
    
    # Test protocol loading
    if not test_protocol_loading():
        print("\nProtocol loading failed. Exiting.")
        return
    
    # Run comparison
    run_protocol_comparison()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Update simulation engine to use EnhancedProtocolSpecification")
    print("2. Test protocols in the Streamlit UI")
    print("3. Validate that q8w patients have identical outcomes")
    print("4. Fine-tune response distributions based on results")


if __name__ == "__main__":
    main()