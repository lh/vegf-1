from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ProtocolParameters:
    """Container for protocol parameters with validation"""
    
    # Vision parameters
    max_letters: int = 85
    min_letters: int = 0
    baseline_mean: float = 65.0
    baseline_sd: float = 5.0
    measurement_noise_sd: float = 2.0
    
    # Loading phase parameters
    loading_duration_weeks: int = 12
    loading_visits: int = 3
    loading_interval_weeks: int = 4
    loading_improvement_prob: float = 0.25
    loading_stable_prob: float = 0.70
    loading_decline_prob: float = 0.05
    
    # Treatment response parameters
    memory_factor: float = 0.7
    headroom_factor: float = 0.2
    regression_factor: float = 0.8
    
    # Disease progression parameters
    base_decline_mean: float = -2.0
    base_decline_sd: float = 0.5
    time_factor_weeks: int = 12
    vision_factor: int = 20
    
    # Resource parameters
    doctors: int = 2
    nurses: int = 4
    oct_machines: int = 2
    visit_duration_minutes: int = 30
    
    @classmethod
    def from_dict(cls, params: Dict[str, Any]) -> 'ProtocolParameters':
        """Create parameters from configuration dictionary"""
        vision_params = params.get('vision', {})
        treatment_params = params.get('treatment_response', {})
        disease_params = params.get('disease_progression', {})
        resource_params = params.get('resources', {})
        
        return cls(
            max_letters=vision_params.get('max_letters', cls.max_letters),
            min_letters=vision_params.get('min_letters', cls.min_letters),
            baseline_mean=vision_params.get('baseline_mean', cls.baseline_mean),
            baseline_sd=vision_params.get('baseline_sd', cls.baseline_sd),
            measurement_noise_sd=vision_params.get('measurement_noise_sd', cls.measurement_noise_sd),
            
            loading_duration_weeks=treatment_params.get('loading_phase', {}).get('duration_weeks', cls.loading_duration_weeks),
            loading_visits=treatment_params.get('loading_phase', {}).get('required_injections', cls.loading_visits),
            loading_interval_weeks=treatment_params.get('loading_phase', {}).get('visit_interval_weeks', cls.loading_interval_weeks),
            loading_improvement_prob=treatment_params.get('loading_phase', {}).get('improve_probability', cls.loading_improvement_prob),
            loading_stable_prob=treatment_params.get('loading_phase', {}).get('stable_probability', cls.loading_stable_prob),
            loading_decline_prob=treatment_params.get('loading_phase', {}).get('decline_probability', cls.loading_decline_prob),
            
            memory_factor=treatment_params.get('memory_factor', cls.memory_factor),
            headroom_factor=treatment_params.get('headroom_factor', cls.headroom_factor),
            regression_factor=treatment_params.get('regression_factor', cls.regression_factor),
            
            base_decline_mean=disease_params.get('base_decline_mean', cls.base_decline_mean),
            base_decline_sd=disease_params.get('base_decline_sd', cls.base_decline_sd),
            time_factor_weeks=disease_params.get('time_factor_weeks', cls.time_factor_weeks),
            vision_factor=disease_params.get('vision_factor_threshold', cls.vision_factor),
            
            doctors=resource_params.get('doctors', cls.doctors),
            nurses=resource_params.get('nurses', cls.nurses),
            oct_machines=resource_params.get('oct_machines', cls.oct_machines),
            visit_duration_minutes=resource_params.get('visit_duration_minutes', cls.visit_duration_minutes)
        )
