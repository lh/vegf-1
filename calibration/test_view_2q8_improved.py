#!/usr/bin/env python3
"""
Test the improved VIEW 2q8 protocol parameters to achieve closer trial alignment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from eylea_calibration_framework import EyleaCalibrationFramework, ParameterSet


def main():
    """Test improved VIEW 2q8 protocol parameters."""
    print("Testing Improved VIEW 2q8 Fixed Dosing Protocol\n")
    print("="*60)
    print("Target: 8.4 letters vision gain, 7.5 injections Year 1")
    print("Current: 4.7 letters vision gain, 6.7 injections Year 1")
    print("="*60)
    
    # Use the improved VIEW 2q8 protocol
    framework = EyleaCalibrationFramework(
        base_protocol_path="protocols/v2/view_2q8_improved.yaml"
    )
    
    # Test with parameters optimized for VIEW outcomes
    test_params = ParameterSet(
        name="view_2q8_improved",
        description="Improved VIEW 2q8 protocol with enhanced vision parameters",
        # All improvements enabled as specified in protocol
        use_loading_phase=True,
        use_time_based_discontinuation=False,
        use_response_based_vision=True,
        use_baseline_distribution=False,
        use_response_heterogeneity=True,
        # Enhanced response parameters
        good_responder_ratio=0.31,
        average_responder_ratio=0.64,
        poor_responder_ratio=0.05,
        good_responder_multiplier=2.5,  # Increased from 2.0
        average_responder_multiplier=1.5,  # Increased from 1.2
        poor_responder_multiplier=0.5,  # Increased from 0.3
        # Fixed protocol interval
        protocol_interval=56  # 8 weeks
    )
    
    # Run test with more patients for better statistics
    print("\nRunning simulation with 500 patients for better statistics...")
    result = framework.test_parameters(test_params, n_patients=500)
    
    print(f"\n{'='*60}")
    print("IMPROVED VIEW 2q8 PROTOCOL TEST RESULTS")
    print(f"{'='*60}")
    
    # Compare to VIEW trial targets
    print("\nYear 1 Results:")
    print(f"  Vision Gain:")
    print(f"    Target:   8.4 letters")
    print(f"    Previous: 4.7 letters")
    print(f"    Current:  {result.vision_gain_year1:.1f} letters")
    print(f"    Improvement: {result.vision_gain_year1 - 4.7:+.1f} letters")
    
    print(f"\n  Injections:")
    print(f"    Target:   7.5")
    print(f"    Previous: 6.7")
    print(f"    Current:  {result.injections_year1:.1f}")
    
    print("\nYear 2 Results:")
    print(f"  Vision:       {result.vision_year2:.1f} letters (target: ~8.0)")
    print(f"  Total injections: {result.injections_year1 + result.injections_year2:.1f} (target: 11.2)")
    print(f"  Discontinuation:  {result.discontinuation_year2:.1%} (target: ~10%)")
    
    # Detailed analysis
    print(f"\n{'='*60}")
    print("PERFORMANCE METRICS")
    print(f"{'='*60}")
    
    # Calculate percentage of target achieved
    vision_achievement = (result.vision_gain_year1 / 8.4) * 100
    injection_accuracy = (1 - abs(result.injections_year1 - 7.5) / 7.5) * 100
    
    print(f"\nTarget Achievement:")
    print(f"  Vision gain: {vision_achievement:.1f}% of target")
    print(f"  Injection accuracy: {injection_accuracy:.1f}%")
    
    print(f"\nCalibration Scores (lower is better):")
    print(f"  Vision score: {result.vision_score:.2f}")
    print(f"  Injection score: {result.injection_score:.2f}")
    print(f"  Discontinuation score: {result.discontinuation_score:.2f}")
    print(f"  Total score: {result.total_score:.2f}")
    
    # Success criteria
    print(f"\n{'='*60}")
    print("SUCCESS CRITERIA CHECK")
    print(f"{'='*60}")
    
    vision_success = 7.0 <= result.vision_gain_year1 <= 10.0
    injection_success = 7.0 <= result.injections_year1 <= 8.0
    
    if vision_success and injection_success:
        print("\n✓ SUCCESS: Protocol achieves VIEW trial outcomes!")
        print(f"  Vision gain: {result.vision_gain_year1:.1f} letters (within 7-10 range)")
        print(f"  Injections: {result.injections_year1:.1f} (within 7-8 range)")
    else:
        print("\n⚠ Further calibration needed:")
        if not vision_success:
            print(f"  Vision gain: {result.vision_gain_year1:.1f} letters (target: 7-10)")
        if not injection_success:
            print(f"  Injections: {result.injections_year1:.1f} (target: 7-8)")
    
    # Recommendations
    if result.vision_gain_year1 < 7.0:
        print("\nRecommendations:")
        print("- Further increase vision change parameters")
        print("- Increase response multipliers")
        print("- Make disease transitions more favorable")
    elif result.vision_gain_year1 > 10.0:
        print("\nRecommendations:")
        print("- Slightly reduce vision change parameters")
        print("- Add more variability to account for poor responders")


if __name__ == "__main__":
    main()