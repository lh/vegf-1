#!/usr/bin/env python3
"""
Test baseline vision distribution implementations.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.models.baseline_vision_distributions import (
    NormalDistribution, BetaWithThresholdDistribution, 
    UniformDistribution, DistributionFactory
)


class TestNormalDistribution:
    """Test the normal distribution implementation."""
    
    def test_basic_sampling(self):
        """Test that sampling works and produces values in expected range."""
        dist = NormalDistribution(mean=70, std=10, min_value=20, max_value=90)
        
        samples = [dist.sample() for _ in range(1000)]
        
        # All samples should be integers in valid range
        assert all(isinstance(s, int) for s in samples)
        assert all(20 <= s <= 90 for s in samples)
        
        # Mean should be close to 70
        assert 68 <= np.mean(samples) <= 72
        
        # Std should be somewhat close to 10 (truncation affects it)
        assert 8 <= np.std(samples) <= 12
    
    def test_parameters(self):
        """Test parameter retrieval."""
        dist = NormalDistribution(mean=65, std=12)
        params = dist.get_parameters()
        
        assert params['type'] == 'normal'
        assert params['mean'] == 65
        assert params['std'] == 12
        assert params['min'] == 20
        assert params['max'] == 90


class TestBetaWithThresholdDistribution:
    """Test the beta distribution with threshold effect."""
    
    def test_basic_sampling(self):
        """Test that sampling works and produces values in expected range."""
        dist = BetaWithThresholdDistribution()
        
        samples = [dist.sample() for _ in range(1000)]
        
        # All samples should be integers in valid range
        assert all(isinstance(s, int) for s in samples)
        assert all(5 <= s <= 98 for s in samples)
    
    def test_threshold_effect(self):
        """Test that threshold effect reduces density above 70."""
        dist = BetaWithThresholdDistribution(
            alpha=3.5, beta=2.0,
            threshold=70, threshold_reduction=0.6
        )
        
        # Sample many values
        samples = [dist.sample() for _ in range(10000)]
        
        # Count values above threshold
        above_70 = sum(s > 70 for s in samples)
        pct_above_70 = above_70 / len(samples) * 100
        
        # Should be significantly less than without threshold
        # UK data shows ~20.4% above 70
        assert 15 <= pct_above_70 <= 25
        
        # Most values should be below 70
        assert sum(s <= 70 for s in samples) > sum(s > 70 for s in samples) * 2
    
    def test_statistics_match_uk_data(self):
        """Test that distribution statistics match UK real-world data."""
        dist = BetaWithThresholdDistribution()
        stats = dist.get_statistics()
        
        # UK data: mean=58.36, median=62
        assert 56 <= stats['mean'] <= 60
        assert 60 <= stats['median'] <= 64
        
        # About 20.4% above 70 in UK data
        assert 15 <= stats['pct_above_70'] <= 25
    
    def test_parameters(self):
        """Test parameter retrieval."""
        dist = BetaWithThresholdDistribution(alpha=4.0, beta=2.5)
        params = dist.get_parameters()
        
        assert params['type'] == 'beta_with_threshold'
        assert params['alpha'] == 4.0
        assert params['beta'] == 2.5
        assert params['threshold'] == 70
        assert params['threshold_reduction'] == 0.6


class TestUniformDistribution:
    """Test the uniform distribution implementation."""
    
    def test_basic_sampling(self):
        """Test uniform sampling."""
        dist = UniformDistribution(min_value=30, max_value=80)
        
        samples = [dist.sample() for _ in range(1000)]
        
        # All values in range
        assert all(30 <= s <= 80 for s in samples)
        
        # Should cover most of the range
        assert min(samples) <= 35
        assert max(samples) >= 75
        
        # Mean should be close to midpoint
        assert 53 <= np.mean(samples) <= 57


class TestDistributionFactory:
    """Test the distribution factory."""
    
    def test_create_normal(self):
        """Test creating normal distribution."""
        config = {'type': 'normal', 'mean': 75, 'std': 8}
        dist = DistributionFactory.create_distribution(config)
        
        assert isinstance(dist, NormalDistribution)
        assert dist.mean == 75
        assert dist.std == 8
    
    def test_create_beta_with_threshold(self):
        """Test creating beta distribution."""
        config = {
            'type': 'beta_with_threshold',
            'alpha': 4.0,
            'beta': 2.0,
            'threshold': 70
        }
        dist = DistributionFactory.create_distribution(config)
        
        assert isinstance(dist, BetaWithThresholdDistribution)
        assert dist.alpha == 4.0
        assert dist.beta == 2.0
        assert dist.threshold == 70
    
    def test_create_uniform(self):
        """Test creating uniform distribution."""
        config = {'type': 'uniform', 'min': 40, 'max': 85}
        dist = DistributionFactory.create_distribution(config)
        
        assert isinstance(dist, UniformDistribution)
        assert dist.min_value == 40
        assert dist.max_value == 85
    
    def test_unknown_type(self):
        """Test that unknown type raises error."""
        config = {'type': 'unknown_distribution'}
        
        with pytest.raises(ValueError, match="Unknown distribution type"):
            DistributionFactory.create_distribution(config)
    
    def test_create_from_protocol_spec(self):
        """Test creating from protocol specification."""
        # Mock protocol spec with new distribution format
        class MockSpec:
            baseline_vision_distribution = {
                'type': 'beta_with_threshold',
                'alpha': 3.5,
                'beta': 2.0
            }
        
        dist = DistributionFactory.create_from_protocol_spec(MockSpec())
        assert isinstance(dist, BetaWithThresholdDistribution)
        
        # Mock protocol spec with legacy format
        class LegacySpec:
            baseline_vision = {
                'mean': 68,
                'std': 11,
                'min': 25,
                'max': 85
            }
        
        dist = DistributionFactory.create_from_protocol_spec(LegacySpec())
        assert isinstance(dist, NormalDistribution)
        assert dist.mean == 68
        assert dist.max_value == 85


def test_visual_comparison():
    """Generate visual comparison of distributions (for manual inspection)."""
    import matplotlib.pyplot as plt
    
    # Create distributions
    normal = NormalDistribution(mean=70, std=10)
    beta = BetaWithThresholdDistribution(alpha=3.5, beta=2.0)
    
    # Sample from each
    n_samples = 10000
    normal_samples = [normal.sample() for _ in range(n_samples)]
    beta_samples = [beta.sample() for _ in range(n_samples)]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot normal distribution
    ax1.hist(normal_samples, bins=50, density=True, alpha=0.7, color='blue')
    ax1.axvline(70, color='red', linestyle='--', label='Protocol mean')
    ax1.set_title('Normal Distribution (Current)')
    ax1.set_xlabel('Vision (ETDRS letters)')
    ax1.set_ylabel('Density')
    ax1.legend()
    
    # Plot beta with threshold
    ax2.hist(beta_samples, bins=50, density=True, alpha=0.7, color='orange')
    ax2.axvline(70, color='red', linestyle='--', label='NICE threshold')
    ax2.axvline(np.mean(beta_samples), color='green', linestyle='--', 
                label=f'Mean: {np.mean(beta_samples):.1f}')
    ax2.set_title('Beta with Threshold Effect (UK Data)')
    ax2.set_xlabel('Vision (ETDRS letters)')
    ax2.set_ylabel('Density')
    ax2.legend()
    
    plt.tight_layout()
    
    # Save to file
    output_dir = Path(__file__).parent.parent / 'output' / 'debug'
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / 'baseline_vision_distributions.png', dpi=150)
    plt.close()
    
    # Print statistics
    print("\nDistribution Statistics:")
    print("\nNormal Distribution:")
    print(f"  Mean: {np.mean(normal_samples):.1f}")
    print(f"  Std: {np.std(normal_samples):.1f}")
    print(f"  % > 70: {sum(s > 70 for s in normal_samples) / len(normal_samples) * 100:.1f}%")
    
    print("\nBeta with Threshold:")
    beta_stats = beta.get_statistics()
    for key, value in beta_stats.items():
        print(f"  {key}: {value:.1f}")


if __name__ == "__main__":
    # Run visual comparison
    test_visual_comparison()
    
    # Run tests
    pytest.main([__file__, "-v"])