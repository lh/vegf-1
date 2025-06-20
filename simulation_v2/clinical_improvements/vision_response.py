"""
Response-Based Vision Change Implementation

Implements realistic vision trajectories with initial gain, maintenance,
and gradual decline based on clinical data.
"""

import random
from datetime import datetime
from typing import Dict, Optional, Tuple


class ResponseBasedVisionModel:
    """
    Models vision changes based on treatment phase.
    
    Clinical patterns show:
    - Loading phase (0-3 months): Rapid improvement
    - Year 1 (3-12 months): Continued improvement
    - Year 2: Maintenance/stability
    - Year 3+: Gradual decline
    """
    
    def __init__(self, vision_params: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize vision response model.
        
        Args:
            vision_params: Parameters for each phase (mean, std)
        """
        self.vision_params = vision_params or {
            'loading': {'mean': 3.0, 'std': 1.0},      # +3 letters/month during loading
            'year1': {'mean': 0.5, 'std': 0.5},        # +0.5 letters/month rest of year 1
            'year2': {'mean': 0.0, 'std': 0.5},        # Stable in year 2
            'year3plus': {'mean': -0.2, 'std': 0.3}    # -0.2 letters/month year 3+
        }
    
    def calculate_vision_change(
        self,
        months_since_start: float,
        response_multiplier: float = 1.0,
        treatment_given: bool = True
    ) -> float:
        """
        Calculate vision change based on time since treatment start.
        
        Args:
            months_since_start: Months elapsed since first treatment
            response_multiplier: Patient-specific response multiplier
            treatment_given: Whether treatment was given (affects change)
            
        Returns:
            Vision change in ETDRS letters
        """
        # Determine phase
        if months_since_start <= 3:
            phase = 'loading'
        elif months_since_start <= 12:
            phase = 'year1'
        elif months_since_start <= 24:
            phase = 'year2'
        else:
            phase = 'year3plus'
        
        # Get parameters for phase
        params = self.vision_params[phase]
        
        # Calculate base change
        base_change = random.gauss(params['mean'], params['std'])
        
        # Apply response multiplier
        vision_change = base_change * response_multiplier
        
        # Reduce improvement if no treatment given
        if not treatment_given and vision_change > 0:
            vision_change *= 0.3  # Only 30% of improvement without treatment
        
        return vision_change
    
    def get_expected_trajectory(self, months: int = 60) -> Dict[int, float]:
        """
        Get expected vision trajectory over time.
        
        Args:
            months: Number of months to project
            
        Returns:
            Dictionary of month: cumulative_vision_change
        """
        cumulative = 0.0
        trajectory = {0: 0.0}
        
        for month in range(1, months + 1):
            # Determine phase
            if month <= 3:
                mean_change = self.vision_params['loading']['mean']
            elif month <= 12:
                mean_change = self.vision_params['year1']['mean']
            elif month <= 24:
                mean_change = self.vision_params['year2']['mean']
            else:
                mean_change = self.vision_params['year3plus']['mean']
            
            cumulative += mean_change
            trajectory[month] = cumulative
        
        return trajectory
    
    def get_phase_description(self, months_since_start: float) -> str:
        """
        Get description of current vision response phase.
        
        Args:
            months_since_start: Months elapsed since first treatment
            
        Returns:
            Description of current phase
        """
        if months_since_start <= 3:
            return "Loading phase (rapid improvement)"
        elif months_since_start <= 12:
            return "Year 1 (continued improvement)"
        elif months_since_start <= 24:
            return "Year 2 (maintenance)"
        else:
            return "Year 3+ (gradual decline)"
    
    def apply_measurement_noise(
        self,
        true_vision: float,
        measurement_std: float = 3.0
    ) -> float:
        """
        Apply measurement noise to vision value.
        
        Args:
            true_vision: True vision value
            measurement_std: Standard deviation of measurement noise
            
        Returns:
            Measured vision with noise applied
        """
        measured = true_vision + random.gauss(0, measurement_std)
        # Clamp to valid range
        return max(0, min(100, measured))