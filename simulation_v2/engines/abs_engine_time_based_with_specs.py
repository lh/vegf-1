"""
Time-based ABS engine with protocol specification support.

This wrapper adds parameter reading from protocol specifications,
matching the pattern used by ABSEngineWithSpecs.
"""

import random
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.engines.abs_engine_time_based import ABSEngineTimeBased
from simulation_v2.clinical_improvements import ClinicalImprovements


class ABSEngineTimeBasedWithSpecs(ABSEngineTimeBased):
    """
    Time-based ABS engine that reads parameters from protocol specifications.
    
    This matches the interface of ABSEngineWithSpecs but uses time-based
    disease progression and vision models.
    """
    
    def __init__(
        self,
        disease_model: DiseaseModelTimeBased,
        protocol: StandardProtocol,
        protocol_spec: TimeBasedProtocolSpecification,
        n_patients: int,
        seed: Optional[int] = None,
        baseline_vision_distribution: Optional[Any] = None,
        clinical_improvements: Optional[ClinicalImprovements] = None
    ):
        """
        Initialize with protocol specification.
        
        Args:
            disease_model: Time-based disease model
            protocol: Treatment protocol
            protocol_spec: Full protocol specification with parameters
            n_patients: Number of patients to simulate
            seed: Random seed
            baseline_vision_distribution: Optional baseline vision distribution
            clinical_improvements: Optional clinical improvements configuration
        """
        self.protocol_spec = protocol_spec
        self.clinical_improvements = clinical_improvements
        
        # Load vision parameters if available
        self._load_vision_parameters()
        
        # Load discontinuation parameters if available
        self._load_discontinuation_parameters()
        
        # Load demographics parameters if available
        self._load_demographics_parameters()
        
        # Call parent init
        super().__init__(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            baseline_vision_distribution=baseline_vision_distribution
        )
    
    def _load_vision_parameters(self):
        """Load vision parameters from protocol spec or parameter files."""
        # Check if protocol spec has time-based vision parameters
        if hasattr(self.protocol_spec, 'vision_parameters_file') and self.protocol_spec.vision_parameters_file:
            # Load from external file
            params_path = Path(self.protocol_spec.source_file).parent / self.protocol_spec.vision_parameters_file
            if params_path.exists():
                with open(params_path) as f:
                    self.vision_params = yaml.safe_load(f)
            else:
                # Fallback to default location
                default_path = Path(__file__).parent.parent.parent / 'protocols' / 'v2_time_based' / 'parameters' / 'vision.yaml'
                if default_path.exists():
                    with open(default_path) as f:
                        self.vision_params = yaml.safe_load(f)
                else:
                    # Use default parameters
                    self.vision_params = self._get_default_vision_params()
        else:
            # Use default parameters for now
            self.vision_params = self._get_default_vision_params()
    
    def _load_discontinuation_parameters(self):
        """Load discontinuation parameters from protocol spec or parameter files."""
        if hasattr(self.protocol_spec, 'discontinuation_parameters_file'):
            # Load from external file
            params_path = Path(self.protocol_spec.source_file).parent / self.protocol_spec.discontinuation_parameters_file
            with open(params_path) as f:
                self.discontinuation_params = yaml.safe_load(f)
        else:
            # Use default parameters
            self.discontinuation_params = self._get_default_discontinuation_params()
    
    def _load_demographics_parameters(self):
        """Load demographics parameters from protocol spec or parameter files."""
        if hasattr(self.protocol_spec, 'demographics_parameters_file') and self.protocol_spec.demographics_parameters_file:
            # Load from external file
            params_path = Path(self.protocol_spec.source_file).parent / self.protocol_spec.demographics_parameters_file
            if params_path.exists():
                with open(params_path) as f:
                    self.demographics_params = yaml.safe_load(f)
            else:
                self.demographics_params = None
        else:
            # No demographics parameters
            self.demographics_params = None
    
    def _sample_baseline_vision(self) -> int:
        """Sample baseline vision from protocol specification."""
        vision = int(random.gauss(
            self.protocol_spec.baseline_vision_mean,
            self.protocol_spec.baseline_vision_std
        ))
        return max(
            self.protocol_spec.baseline_vision_min,
            min(self.protocol_spec.baseline_vision_max, vision)
        )
    
    def _update_patient_vision(self, patient_id: str, patient: Any, current_date: Any):
        """
        Update patient vision using loaded parameters.
        
        This implements the full vision model from TIME_BASED_VISION_MODEL.md
        """
        # Get current values
        current_vision = self.patient_actual_vision[patient_id]
        vision_ceiling = self.patient_vision_ceiling[patient_id]
        
        # Calculate treatment effect
        days_since_injection = patient.days_since_last_injection_at(current_date)
        treatment_effect = self._calculate_treatment_effect(days_since_injection)
        
        # Get vision change parameters based on state and treatment
        state_name = patient.current_state.name
        
        if self.vision_params:
            # Use loaded parameters
            decline_params = self.vision_params['vision_decline_fortnightly'][state_name]
            
            # Interpolate between treated and untreated based on effect
            untreated_params = decline_params['untreated']
            treated_params = decline_params['treated']
            
            mean_change = (
                untreated_params['mean'] * (1 - treatment_effect) +
                treated_params['mean'] * treatment_effect
            )
            std_change = (
                untreated_params['std'] * (1 - treatment_effect) +
                treated_params['std'] * treatment_effect
            )
            
            # Apply stochastic change
            change = random.gauss(mean_change, std_change)
        else:
            # Fallback to simple model
            change = self._simple_vision_change(state_name, treatment_effect)
        
        # Apply change with bounds
        new_vision = current_vision + change
        new_vision = min(new_vision, vision_ceiling)
        new_vision = max(0, new_vision)
        
        self.patient_actual_vision[patient_id] = new_vision
    
    def _calculate_treatment_effect(self, days_since_injection: Optional[int]) -> float:
        """Calculate treatment efficacy with decay."""
        if days_since_injection is None:
            return 0.0
        
        if self.vision_params and 'treatment_effect_decay' in self.vision_params:
            params = self.vision_params['treatment_effect_decay']
            full_duration = params['full_effect_duration_days']
            
            if days_since_injection <= full_duration:
                return 1.0
            else:
                # Use disease model's decay calculation
                return self.time_based_model.get_treatment_efficacy(days_since_injection)
        else:
            # Use disease model's default
            return self.time_based_model.get_treatment_efficacy(days_since_injection)
    
    def _simple_vision_change(self, state_name: str, treatment_effect: float) -> float:
        """Simple vision change model as fallback."""
        base_changes = {
            'NAIVE': -0.3,
            'STABLE': -0.1,
            'ACTIVE': -0.5,
            'HIGHLY_ACTIVE': -1.0
        }
        
        base = base_changes.get(state_name, -0.3)
        # Treatment reduces decline
        adjusted = base * (1 - treatment_effect * 0.7)
        
        return random.gauss(adjusted, abs(adjusted) * 0.3)
    
    def _should_discontinue(self, patient: Any, current_date: Any) -> bool:
        """
        Check discontinuation using loaded parameters.
        
        Implements the discontinuation model from TIME_BASED_DISCONTINUATION_MODEL.md
        """
        # Get measured vision from last visit
        if patient.visit_history:
            measured_vision = patient.visit_history[-1]['vision']
        else:
            measured_vision = patient.baseline_vision
        
        # Check poor vision discontinuation
        if self.discontinuation_params:
            poor_vision_params = self.discontinuation_params.get(
                'discontinuation_parameters', {}
            ).get('poor_vision', {})
            
            threshold = poor_vision_params.get('vision_threshold', 20)
            probability = poor_vision_params.get('discontinuation_probability', 0.8)
            
            if measured_vision < threshold:
                if random.random() < probability:
                    return True
        
        # Add other discontinuation reasons here (death, attrition, etc.)
        # For now, just use base class logic as well
        return super()._should_discontinue(patient, current_date)
    
    def _get_default_vision_params(self) -> Dict[str, Any]:
        """Get default vision parameters."""
        return {
            'vision_decline_fortnightly': {
                'NAIVE': {
                    'untreated': {'mean': -1.2, 'std': 0.5},
                    'treated': {'mean': -0.8, 'std': 0.4}
                },
                'STABLE': {
                    'untreated': {'mean': -0.3, 'std': 0.2},
                    'treated': {'mean': -0.1, 'std': 0.1}
                },
                'ACTIVE': {
                    'untreated': {'mean': -1.5, 'std': 0.6},
                    'treated': {'mean': -0.4, 'std': 0.3}
                },
                'HIGHLY_ACTIVE': {
                    'untreated': {'mean': -2.0, 'std': 0.8},
                    'treated': {'mean': -0.6, 'std': 0.4}
                }
            }
        }
    
    def _get_default_discontinuation_params(self) -> Dict[str, Any]:
        """Get default discontinuation parameters."""
        return {
            'discontinuation_parameters': {
                'poor_vision': {
                    'vision_threshold': 20,
                    'discontinuation_probability': 0.8,
                    'grace_period_visits': 2
                }
            }
        }