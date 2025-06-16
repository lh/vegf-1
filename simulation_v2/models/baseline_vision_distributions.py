"""
Baseline vision distribution models for patient initialization.

This module provides different statistical distributions for sampling
initial patient vision values, including:
- Normal (Gaussian) distribution - the current default
- Beta distribution with threshold effect - based on UK real-world data
- Uniform distribution - for testing
"""

import random
import numpy as np
from typing import Dict, Any, Protocol, Tuple
from abc import ABC, abstractmethod
from scipy import stats


class BaselineVisionDistribution(ABC):
    """Abstract base class for baseline vision distributions."""
    
    @abstractmethod
    def sample(self) -> int:
        """Sample a baseline vision value in ETDRS letters (0-100)."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return the parameters of this distribution."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of this distribution."""
        pass


class NormalDistribution(BaselineVisionDistribution):
    """
    Normal (Gaussian) distribution for baseline vision.
    
    This is the current default used in simulations.
    """
    
    def __init__(self, mean: float = 70, std: float = 10, 
                 min_value: int = 20, max_value: int = 90):
        """
        Initialize normal distribution.
        
        Args:
            mean: Mean vision in ETDRS letters
            std: Standard deviation
            min_value: Minimum allowed vision
            max_value: Maximum allowed vision
        """
        self.mean = mean
        self.std = std
        self.min_value = min_value
        self.max_value = max_value
    
    def sample(self) -> int:
        """Sample from truncated normal distribution."""
        vision = int(random.gauss(self.mean, self.std))
        return max(self.min_value, min(self.max_value, vision))
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return distribution parameters."""
        return {
            'type': 'normal',
            'mean': self.mean,
            'std': self.std,
            'min': self.min_value,
            'max': self.max_value
        }
    
    def get_description(self) -> str:
        """Return description."""
        return f"Normal(μ={self.mean}, σ={self.std}) truncated to [{self.min_value}, {self.max_value}]"


class BetaWithThresholdDistribution(BaselineVisionDistribution):
    """
    Beta distribution with threshold effect for baseline vision.
    
    Based on UK real-world data analysis showing:
    - Beta distribution fits the natural disease distribution
    - Threshold effect at 70 letters due to NICE funding criteria
    - 60% reduction in density above 70 letters
    
    This captures both the biological disease process and the 
    healthcare system's eligibility constraints.
    """
    
    def __init__(self, alpha: float = 3.5, beta: float = 2.0,
                 min_value: int = 5, max_value: int = 98,
                 threshold: int = 70, threshold_reduction: float = 0.6):
        """
        Initialize beta distribution with threshold effect.
        
        Args:
            alpha: Beta distribution alpha parameter
            beta: Beta distribution beta parameter  
            min_value: Minimum vision value (location parameter)
            max_value: Maximum vision value
            threshold: Vision threshold for funding eligibility
            threshold_reduction: Reduction factor above threshold (0.6 = 60% reduction)
        """
        self.alpha = alpha
        self.beta = beta
        self.min_value = min_value
        self.max_value = max_value
        self.scale = max_value - min_value
        self.threshold = threshold
        self.threshold_reduction = threshold_reduction
        
        # Pre-calculate the threshold effect probabilities
        self._setup_distribution()
    
    def _setup_distribution(self):
        """Pre-calculate the cumulative distribution with threshold effect."""
        # Create fine-grained x values
        self.x_values = np.linspace(self.min_value, self.max_value, 1000)
        
        # Calculate raw beta PDF
        x_normalized = (self.x_values - self.min_value) / self.scale
        pdf_raw = stats.beta.pdf(x_normalized, self.alpha, self.beta)
        
        # Apply threshold effect
        threshold_mask = self.x_values > self.threshold
        pdf_adjusted = pdf_raw.copy()
        pdf_adjusted[threshold_mask] *= (1 - self.threshold_reduction)
        
        # Normalize to ensure valid probability distribution
        self.pdf = pdf_adjusted / np.trapezoid(pdf_adjusted, self.x_values)
        
        # Calculate CDF for inverse transform sampling
        self.cdf = np.zeros_like(self.pdf)
        for i in range(1, len(self.pdf)):
            self.cdf[i] = self.cdf[i-1] + np.trapezoid(self.pdf[i-1:i+1], self.x_values[i-1:i+1])
        self.cdf = self.cdf / self.cdf[-1]  # Ensure it ends at 1.0
    
    def sample(self) -> int:
        """Sample using inverse transform method."""
        u = random.random()
        # Find where u falls in the CDF
        idx = np.searchsorted(self.cdf, u)
        if idx >= len(self.x_values):
            idx = len(self.x_values) - 1
        return int(round(self.x_values[idx]))
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return distribution parameters."""
        return {
            'type': 'beta_with_threshold',
            'alpha': self.alpha,
            'beta': self.beta,
            'min': self.min_value,
            'max': self.max_value,
            'threshold': self.threshold,
            'threshold_reduction': self.threshold_reduction
        }
    
    def get_description(self) -> str:
        """Return description."""
        return (f"Beta(α={self.alpha}, β={self.beta}) on [{self.min_value}, {self.max_value}] "
                f"with {self.threshold_reduction*100:.0f}% reduction above {self.threshold}")
    
    def get_statistics(self) -> Dict[str, float]:
        """Calculate and return distribution statistics."""
        # Sample many values to estimate statistics
        samples = [self.sample() for _ in range(10000)]
        
        return {
            'mean': np.mean(samples),
            'median': np.median(samples),
            'std': np.std(samples),
            'pct_above_70': sum(s > 70 for s in samples) / len(samples) * 100,
            'q25': np.percentile(samples, 25),
            'q75': np.percentile(samples, 75)
        }


class UniformDistribution(BaselineVisionDistribution):
    """Uniform distribution for testing purposes."""
    
    def __init__(self, min_value: int = 20, max_value: int = 90):
        """Initialize uniform distribution."""
        self.min_value = min_value
        self.max_value = max_value
    
    def sample(self) -> int:
        """Sample uniformly between min and max."""
        return random.randint(self.min_value, self.max_value)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return distribution parameters."""
        return {
            'type': 'uniform',
            'min': self.min_value,
            'max': self.max_value
        }
    
    def get_description(self) -> str:
        """Return description."""
        return f"Uniform[{self.min_value}, {self.max_value}]"


class DistributionFactory:
    """Factory for creating baseline vision distributions."""
    
    @staticmethod
    def create_distribution(config: Dict[str, Any]) -> BaselineVisionDistribution:
        """
        Create a distribution from configuration.
        
        Args:
            config: Distribution configuration with 'type' and parameters
            
        Returns:
            BaselineVisionDistribution instance
            
        Example configs:
            {'type': 'normal', 'mean': 70, 'std': 10}
            {'type': 'beta_with_threshold', 'alpha': 3.5, 'beta': 2.0}
            {'type': 'uniform', 'min': 20, 'max': 90}
        """
        dist_type = config.get('type', 'normal')
        
        if dist_type == 'normal':
            return NormalDistribution(
                mean=config.get('mean', 70),
                std=config.get('std', 10),
                min_value=config.get('min', 20),
                max_value=config.get('max', 90)
            )
        
        elif dist_type == 'beta_with_threshold':
            return BetaWithThresholdDistribution(
                alpha=config.get('alpha', 3.5),
                beta=config.get('beta', 2.0),
                min_value=config.get('min', 5),
                max_value=config.get('max', 98),
                threshold=config.get('threshold', 70),
                threshold_reduction=config.get('threshold_reduction', 0.6)
            )
        
        elif dist_type == 'uniform':
            return UniformDistribution(
                min_value=config.get('min', 20),
                max_value=config.get('max', 90)
            )
        
        else:
            raise ValueError(f"Unknown distribution type: {dist_type}")
    
    @staticmethod
    def create_from_protocol_spec(spec: Any) -> BaselineVisionDistribution:
        """
        Create a distribution from a protocol specification.
        
        Falls back to normal distribution if no distribution specified.
        """
        # Check if protocol has baseline_vision_distribution
        if hasattr(spec, 'baseline_vision_distribution') and spec.baseline_vision_distribution is not None:
            return DistributionFactory.create_distribution(spec.baseline_vision_distribution)
        
        # Fall back to legacy baseline_vision parameters
        if hasattr(spec, 'baseline_vision'):
            baseline = spec.baseline_vision
            if isinstance(baseline, dict):
                return NormalDistribution(
                    mean=baseline.get('mean', 70),
                    std=baseline.get('std', 10),
                    min_value=baseline.get('min', 20),
                    max_value=baseline.get('max', 90)
                )
        
        # Fall back to individual attributes (legacy support)
        return NormalDistribution(
            mean=getattr(spec, 'baseline_vision_mean', 70),
            std=getattr(spec, 'baseline_vision_std', 10),
            min_value=getattr(spec, 'baseline_vision_min', 20),
            max_value=getattr(spec, 'baseline_vision_max', 90)
        )