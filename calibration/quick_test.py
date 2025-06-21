#!/usr/bin/env python3
"""
Quick test of the calibration framework with a single parameter set.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eylea_calibration_framework import EyleaCalibrationFramework, ParameterSet


def main():
    """Run a quick test with one parameter set."""
    print("Running quick calibration test...")
    
    framework = EyleaCalibrationFramework()
    
    # Test with VIEW-aligned parameters
    test_params = ParameterSet(
        name="view_aligned",
        description="Parameters aligned with VIEW trial expectations",
        # Keep all improvements enabled
        use_loading_phase=True,
        use_time_based_discontinuation=True,
        use_response_based_vision=True,
        use_baseline_distribution=True,
        use_response_heterogeneity=True,
        # Adjust discontinuation to match VIEW
        discontinuation_year1=0.05,      # 5% by year 1
        discontinuation_year2=0.125,     # 12.5% by year 2  
        discontinuation_year3=0.10,      # Lower in later years
        discontinuation_year4=0.08,
        discontinuation_year5_plus=0.06,
        # Slightly more good responders
        good_responder_ratio=0.35,       # 35% good responders
        average_responder_ratio=0.50,    # 50% average
        poor_responder_ratio=0.15,       # 15% poor
        # Moderate response multipliers
        good_responder_multiplier=1.6,
        average_responder_multiplier=1.1,
        poor_responder_multiplier=0.6,
        # Standard TAE interval
        protocol_interval=56             # 8 weeks standard
    )
    
    # Run test with small patient count for speed
    result = framework.test_parameters(test_params, n_patients=50)
    
    print(f"\n{'='*60}")
    print("QUICK TEST COMPLETE")
    print(f"{'='*60}")
    print(f"Total Score: {result.total_score:.2f}")
    print("\nTarget vs Actual:")
    print(f"Vision Y1: {framework.targets.VISION_GAIN_YEAR1_MEAN:.1f} vs {result.vision_gain_year1:.1f}")
    print(f"Vision Y2: {framework.targets.VISION_YEAR2_MEAN:.1f} vs {result.vision_year2:.1f}")
    print(f"Injections Y1: {framework.targets.INJECTIONS_YEAR1_MEAN:.1f} vs {result.injections_year1:.1f}")
    print(f"Injections Y2: {framework.targets.INJECTIONS_YEAR2_MEAN:.1f} vs {result.injections_year2:.1f}")
    print(f"Discontinuation Y2: {framework.targets.DISCONTINUATION_YEAR2_MEAN:.1%} vs {result.discontinuation_year2:.1%}")
    
    # Save test protocol for inspection
    print(f"\nTest protocol saved to: calibration/test_protocols/{test_params.name}.yaml")


if __name__ == "__main__":
    main()