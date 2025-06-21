#!/usr/bin/env python3
"""
Test the VIEW 2q8 protocol to see if it produces results closer to trial outcomes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from eylea_calibration_framework import EyleaCalibrationFramework, ParameterSet


def main():
    """Test VIEW 2q8 protocol."""
    print("Testing VIEW 2q8 Fixed Dosing Protocol\n")
    
    # Use the VIEW 2q8 protocol as base
    framework = EyleaCalibrationFramework(
        base_protocol_path="protocols/v2/view_2q8.yaml"
    )
    
    # Test with default parameters from the protocol
    test_params = ParameterSet(
        name="view_2q8_default",
        description="VIEW 2q8 protocol with default parameters",
        # All improvements enabled as specified in protocol
        use_loading_phase=True,
        use_time_based_discontinuation=False,
        use_response_based_vision=True,
        use_baseline_distribution=False,
        use_response_heterogeneity=True,
        # Use protocol-specified response types
        good_responder_ratio=0.31,
        average_responder_ratio=0.64,
        poor_responder_ratio=0.05,
        good_responder_multiplier=2.0,
        average_responder_multiplier=1.2,
        poor_responder_multiplier=0.3,
        # Fixed protocol doesn't use T&E intervals
        protocol_interval=56  # 8 weeks
    )
    
    # Run test with more patients for better statistics
    result = framework.test_parameters(test_params, n_patients=200)
    
    print(f"\n{'='*60}")
    print("VIEW 2q8 PROTOCOL TEST RESULTS")
    print(f"{'='*60}")
    
    # Compare to VIEW trial targets
    print("\nTarget vs Actual (Year 1):")
    print(f"  Mean BCVA change: 8.4 vs {result.vision_gain_year1:.1f} letters")
    print(f"  Injections: 7.5 vs {result.injections_year1:.1f}")
    
    print("\nTarget vs Actual (Year 2):")
    print(f"  Vision: ~8.0 vs {result.vision_year2:.1f} letters")
    print(f"  Total injections: 11.2 vs {result.injections_year1 + result.injections_year2:.1f}")
    print(f"  Discontinuation: ~10% vs {result.discontinuation_year2:.1%}")
    
    print(f"\nScores (lower is better):")
    print(f"  Vision score: {result.vision_score:.2f}")
    print(f"  Injection score: {result.injection_score:.2f}")
    print(f"  Discontinuation score: {result.discontinuation_score:.2f}")
    print(f"  Total score: {result.total_score:.2f}")
    
    # Check if this is better than the T&E results
    print(f"\n{'='*60}")
    print("COMPARISON TO TREAT-AND-EXTEND:")
    print(f"{'='*60}")
    print("T&E results: Vision -3.4 letters, 3.7 injections")
    print(f"2q8 results: Vision {result.vision_gain_year1:.1f} letters, {result.injections_year1:.1f} injections")
    
    if result.vision_gain_year1 > 0:
        print("\n✓ SUCCESS: Positive vision gains achieved!")
    else:
        print("\n✗ Still showing vision loss - further calibration needed")


if __name__ == "__main__":
    main()