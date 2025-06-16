#!/usr/bin/env python3
"""
Test integration of beta distribution with simulation engines.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.models.baseline_vision_distributions import (
    BetaWithThresholdDistribution, NormalDistribution
)


def test_protocol_with_beta_distribution():
    """Test that the new protocol with beta distribution works correctly."""
    # Load the UK real-world protocol
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea_treat_and_extend_uk_real_world_v1.1.yaml"
    
    # Load specification
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Initialize runner
    runner = SimulationRunner(spec)
    
    # Run a small simulation
    results = runner.run(
        engine_type='abs',
        n_patients=100,
        duration_years=1.0,
        seed=42
    )
    
    # Check that results are produced
    assert results is not None
    assert len(results.patient_histories) > 0
    
    # Extract baseline visions
    baseline_visions = [p.baseline_vision for p in results.patient_histories.values()]
    
    # Check statistics match beta distribution expectations
    mean_vision = np.mean(baseline_visions)
    assert 55 <= mean_vision <= 62  # Expected around 58.36
    
    # Check that we see the full range
    assert min(baseline_visions) < 30  # Should see some low values
    assert max(baseline_visions) > 70  # Should see some high values
    
    # Check proportion above 70
    above_70 = sum(v > 70 for v in baseline_visions)
    pct_above_70 = above_70 / len(baseline_visions) * 100
    assert 10 <= pct_above_70 <= 30  # Expected around 20.4%


def test_compare_distributions():
    """Compare results between normal and beta distributions."""
    # Run with standard protocol (normal distribution)
    standard_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea_treat_and_extend_v1.0.yaml"
    standard_spec = ProtocolSpecification.from_yaml(standard_path)
    standard_runner = SimulationRunner(standard_spec)
    standard_results = standard_runner.run(
        engine_type='abs',
        n_patients=200,
        duration_years=1.0,
        seed=12345
    )
    
    # Run with UK real-world protocol (beta distribution)
    uk_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea_treat_and_extend_uk_real_world_v1.1.yaml"
    uk_spec = ProtocolSpecification.from_yaml(uk_path)
    uk_runner = SimulationRunner(uk_spec)
    uk_results = uk_runner.run(
        engine_type='abs',
        n_patients=200,
        duration_years=1.0,
        seed=12345
    )
    
    # Extract baseline visions
    standard_visions = [p.baseline_vision for p in standard_results.patient_histories.values()]
    uk_visions = [p.baseline_vision for p in uk_results.patient_histories.values()]
    
    # Compare statistics
    print("\nDistribution Comparison:")
    print(f"Standard Protocol (Normal):")
    print(f"  Mean: {np.mean(standard_visions):.1f}")
    print(f"  Std: {np.std(standard_visions):.1f}")
    print(f"  Min: {min(standard_visions)}")
    print(f"  Max: {max(standard_visions)}")
    print(f"  % > 70: {sum(v > 70 for v in standard_visions) / len(standard_visions) * 100:.1f}%")
    
    print(f"\nUK Real-World Protocol (Beta with threshold):")
    print(f"  Mean: {np.mean(uk_visions):.1f}")
    print(f"  Std: {np.std(uk_visions):.1f}")
    print(f"  Min: {min(uk_visions)}")
    print(f"  Max: {max(uk_visions)}")
    print(f"  % > 70: {sum(v > 70 for v in uk_visions) / len(uk_visions) * 100:.1f}%")
    
    # Check differences
    assert np.mean(standard_visions) > np.mean(uk_visions)  # Standard should have higher mean
    assert np.std(uk_visions) > np.std(standard_visions)  # UK should have higher variance


def test_des_engine_with_beta():
    """Test that DES engine also works with beta distribution."""
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea_treat_and_extend_uk_real_world_v1.1.yaml"
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    runner = SimulationRunner(spec)
    
    # Run with DES engine
    results = runner.run(
        engine_type='des',
        n_patients=50,
        duration_years=0.5,
        seed=99
    )
    
    # Check results
    assert results is not None
    assert len(results.patient_histories) > 0
    
    # Check baseline visions
    baseline_visions = [p.baseline_vision for p in results.patient_histories.values()]
    mean_vision = np.mean(baseline_visions)
    assert 50 <= mean_vision <= 65  # Should be lower than normal distribution


if __name__ == "__main__":
    # Run comparison test
    test_compare_distributions()
    
    # Run pytest
    pytest.main([__file__, "-v"])