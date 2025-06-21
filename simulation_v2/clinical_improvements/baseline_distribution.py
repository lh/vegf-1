"""
Baseline Vision Distribution Implementation

Implements realistic baseline vision distribution based on clinical trial data
showing normal distribution around 55 letters.
"""

import random
from typing import Optional, Tuple


class BaselineVisionDistribution:
    """
    Manages baseline vision distribution for patients.
    
    Clinical trials show baseline vision follows approximately normal
    distribution with mean ~55 letters and SD ~15 letters.
    """
    
    def __init__(
        self,
        mean: float = 55.0,
        std: float = 15.0,
        min_vision: float = 25.0,
        max_vision: float = 85.0
    ):
        """
        Initialize baseline distribution parameters.
        
        Args:
            mean: Mean baseline vision (default: 55 letters)
            std: Standard deviation (default: 15 letters)
            min_vision: Minimum allowed vision (default: 25 letters)
            max_vision: Maximum allowed vision (default: 85 letters)
        """
        self.mean = mean
        self.std = std
        self.min_vision = min_vision
        self.max_vision = max_vision
    
    def sample_baseline(self) -> int:
        """
        Sample a baseline vision value from the distribution.
        
        Returns:
            Baseline vision in ETDRS letters (integer)
        """
        # Sample from normal distribution
        baseline = random.gauss(self.mean, self.std)
        
        # Clamp to valid range
        baseline = max(self.min_vision, min(self.max_vision, baseline))
        
        return int(baseline)
    
    def get_percentile(self, vision: float) -> float:
        """
        Get the percentile rank of a vision value.
        
        Args:
            vision: Vision value to check
            
        Returns:
            Percentile (0-100)
        """
        # Use normal CDF approximation
        z_score = (vision - self.mean) / self.std
        
        # Approximate normal CDF using error function approximation
        # This is a simplified approximation for demonstration
        if z_score < -3:
            return 0.1
        elif z_score > 3:
            return 99.9
        else:
            # Linear approximation between -3 and 3
            percentile = 50 + (z_score * 16.67)
            return max(0, min(100, percentile))
    
    def get_category(self, vision: float) -> str:
        """
        Categorize baseline vision.
        
        Args:
            vision: Baseline vision value
            
        Returns:
            Category description
        """
        percentile = self.get_percentile(vision)
        
        if percentile < 20:
            return "Poor baseline vision"
        elif percentile < 40:
            return "Below average baseline vision"
        elif percentile < 60:
            return "Average baseline vision"
        elif percentile < 80:
            return "Above average baseline vision"
        else:
            return "Excellent baseline vision"
    
    def get_distribution_stats(self) -> dict:
        """
        Get statistics about the distribution.
        
        Returns:
            Dictionary with distribution statistics
        """
        return {
            'mean': self.mean,
            'std': self.std,
            'min': self.min_vision,
            'max': self.max_vision,
            'quartiles': {
                'Q1': self.mean - 0.674 * self.std,  # ~25th percentile
                'Q2': self.mean,                      # 50th percentile
                'Q3': self.mean + 0.674 * self.std   # ~75th percentile
            }
        }