"""
Configuration for Clinical Improvements

Feature flags to enable/disable individual improvements without
modifying existing simulation code.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ClinicalImprovements:
    """Feature flags and parameters for clinical improvements"""
    
    # Feature flags
    use_loading_phase: bool = False
    use_time_based_discontinuation: bool = False
    use_response_based_vision: bool = False
    use_baseline_distribution: bool = False
    use_response_heterogeneity: bool = False
    
    # Loading phase parameters
    loading_phase_injections: int = 3
    loading_phase_interval_days: int = 28
    
    # Discontinuation parameters (annual probabilities, not cumulative)
    discontinuation_probabilities: Dict[int, float] = field(default_factory=lambda: {
        1: 0.125,   # 12.5% in Year 1
        2: 0.15,    # Additional 15% in Year 2
        3: 0.12,    # Additional 12% in Year 3
        4: 0.08,    # Additional 8% in Year 4
        5: 0.075    # Additional 7.5% in Year 5+
    })
    
    # Vision response parameters
    vision_response_params: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'loading': {'mean': 3.0, 'std': 1.0},      # +3 letters/month during loading
        'year1': {'mean': 0.5, 'std': 0.5},        # +0.5 letters/month rest of year 1
        'year2': {'mean': 0.0, 'std': 0.5},        # Stable in year 2
        'year3plus': {'mean': -0.2, 'std': 0.3}    # -0.2 letters/month year 3+
    })
    
    # Baseline vision distribution parameters
    baseline_vision_mean: float = 55.0
    baseline_vision_std: float = 15.0
    baseline_vision_min: float = 25.0
    baseline_vision_max: float = 85.0
    
    # Response heterogeneity parameters
    response_types: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'good': {'probability': 0.3, 'multiplier': 1.2},      # 30% of patients, 120% response
        'average': {'probability': 0.5, 'multiplier': 1.0},   # 50% of patients, 100% response
        'poor': {'probability': 0.2, 'multiplier': 0.6}       # 20% of patients, 60% response
    })
    
    # Measurement noise
    vision_measurement_std: float = 3.0  # ±3 letter measurement variability
    
    def enable_all(self) -> None:
        """Enable all clinical improvements"""
        self.use_loading_phase = True
        self.use_time_based_discontinuation = True
        self.use_response_based_vision = True
        self.use_baseline_distribution = True
        self.use_response_heterogeneity = True
    
    def disable_all(self) -> None:
        """Disable all clinical improvements"""
        self.use_loading_phase = False
        self.use_time_based_discontinuation = False
        self.use_response_based_vision = False
        self.use_baseline_distribution = False
        self.use_response_heterogeneity = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            'use_loading_phase': self.use_loading_phase,
            'use_time_based_discontinuation': self.use_time_based_discontinuation,
            'use_response_based_vision': self.use_response_based_vision,
            'use_baseline_distribution': self.use_baseline_distribution,
            'use_response_heterogeneity': self.use_response_heterogeneity,
            'loading_phase_injections': self.loading_phase_injections,
            'loading_phase_interval_days': self.loading_phase_interval_days,
            'discontinuation_probabilities': self.discontinuation_probabilities,
            'vision_response_params': self.vision_response_params,
            'baseline_vision_mean': self.baseline_vision_mean,
            'baseline_vision_std': self.baseline_vision_std,
            'response_types': self.response_types
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClinicalImprovements':
        """Create configuration from dictionary"""
        return cls(**data)