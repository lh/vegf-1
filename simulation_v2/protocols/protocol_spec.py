"""
Protocol specification with complete parameter tracking.

No defaults, no fallbacks - everything must be explicitly defined.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import json
from datetime import datetime
import hashlib


@dataclass(frozen=True)
class ProtocolSpecification:
    """
    Immutable protocol specification with full audit trail.
    
    Every parameter must be explicitly defined - no defaults.
    """
    # Metadata
    name: str
    version: str
    created_date: str
    author: str
    description: str
    
    # Protocol parameters (no defaults allowed)
    protocol_type: str  # "standard", "intensive", etc.
    min_interval_days: int
    max_interval_days: int
    extension_days: int
    shortening_days: int
    
    # Disease model parameters (no defaults allowed)
    disease_transitions: Dict[str, Dict[str, float]]
    vision_change_model: Dict[str, Any]
    treatment_effect_on_transitions: Dict[str, Any]
    
    # Patient population parameters
    baseline_vision_mean: int
    baseline_vision_std: int
    baseline_vision_min: int
    baseline_vision_max: int
    
    # Discontinuation parameters
    discontinuation_rules: Dict[str, Any]
    
    # Source tracking
    source_file: str
    load_timestamp: str
    checksum: str  # For verification
    
    # Optional: Advanced baseline vision distribution
    baseline_vision_distribution: Optional[Dict[str, Any]] = None
    
    # Optional: Clinical improvements for enhanced realism
    clinical_improvements: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, filepath: Path) -> 'ProtocolSpecification':
        """
        Load from YAML with strict validation.
        
        Args:
            filepath: Path to YAML protocol file
            
        Returns:
            ProtocolSpecification instance
            
        Raises:
            FileNotFoundError: If protocol file doesn't exist
            ValueError: If required fields are missing
            yaml.YAMLError: If YAML is malformed
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Protocol file not found: {filepath}")
            
        # Load YAML
        with open(filepath) as f:
            data = yaml.safe_load(f)
            
        # Calculate checksum for audit trail
        with open(filepath, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
            
        # Validate all required top-level fields exist - NO DEFAULTS
        required_fields = [
            'name', 'version', 'author', 'description',
            'protocol_type', 'min_interval_days', 'max_interval_days',
            'extension_days', 'shortening_days', 'disease_transitions',
            'vision_change_model', 'treatment_effect_on_transitions',
            'baseline_vision_distribution', 'discontinuation_rules'
        ]
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
            
        # Validate disease transitions
        _validate_disease_transitions(data['disease_transitions'])
        
        # Validate vision change model
        _validate_vision_change_model(data['vision_change_model'])
        
        # Validate baseline vision distribution
        baseline_dist = data['baseline_vision_distribution']
        if not isinstance(baseline_dist, dict):
            raise ValueError("baseline_vision_distribution must be a dictionary")
        if 'type' not in baseline_dist:
            raise ValueError("baseline_vision_distribution must have a 'type' field")
        
        # Extract parameters based on distribution type
        dist_type = baseline_dist['type']
        if dist_type == 'normal':
            required_fields = ['mean', 'std', 'min', 'max']
            missing = [f for f in required_fields if f not in baseline_dist]
            if missing:
                raise ValueError(f"Normal distribution missing fields: {missing}")
            baseline_mean = baseline_dist['mean']
            baseline_std = baseline_dist['std']
            baseline_min = baseline_dist['min']
            baseline_max = baseline_dist['max']
        elif dist_type == 'beta_with_threshold':
            # Beta distribution must specify all required parameters
            required_fields = ['alpha', 'beta', 'min', 'max', 'threshold', 'threshold_reduction']
            missing = [f for f in required_fields if f not in baseline_dist]
            if missing:
                raise ValueError(f"Beta with threshold distribution missing fields: {missing}")
            # For compatibility with legacy fields, calculate approximate values
            # These are only used for the legacy baseline_vision_* fields
            baseline_min = baseline_dist['min']
            baseline_max = baseline_dist['max']
            # Approximate mean and std from beta parameters
            alpha = baseline_dist['alpha']
            beta = baseline_dist['beta']
            # Mean of beta distribution scaled to range
            baseline_mean = baseline_min + (alpha / (alpha + beta)) * (baseline_max - baseline_min)
            # Approximate std (this is rough but sufficient for legacy compatibility)
            variance = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))
            baseline_std = ((baseline_max - baseline_min) * variance**0.5)
        elif dist_type == 'uniform':
            if 'min' not in baseline_dist or 'max' not in baseline_dist:
                raise ValueError("Uniform distribution requires 'min' and 'max' fields")
            baseline_min = baseline_dist['min']
            baseline_max = baseline_dist['max']
            baseline_mean = (baseline_min + baseline_max) / 2
            baseline_std = (baseline_max - baseline_min) / (2 * 1.732)  # std for uniform dist
        else:
            raise ValueError(f"Unknown baseline vision distribution type: {dist_type}")
            
        return cls(
            name=data['name'],
            version=data['version'],
            created_date=data.get('created_date', 'unknown'),
            author=data['author'],
            description=data['description'],
            protocol_type=data['protocol_type'],
            min_interval_days=data['min_interval_days'],
            max_interval_days=data['max_interval_days'],
            extension_days=data['extension_days'],
            shortening_days=data['shortening_days'],
            disease_transitions=data['disease_transitions'],
            vision_change_model=data['vision_change_model'],
            treatment_effect_on_transitions=data['treatment_effect_on_transitions'],
            baseline_vision_mean=baseline_mean,
            baseline_vision_std=baseline_std,
            baseline_vision_min=baseline_min,
            baseline_vision_max=baseline_max,
            baseline_vision_distribution=data['baseline_vision_distribution'],
            discontinuation_rules=data['discontinuation_rules'],
            clinical_improvements=data.get('clinical_improvements'),
            source_file=str(filepath.absolute()),
            load_timestamp=datetime.now().isoformat(),
            checksum=checksum
        )
    
    def to_audit_log(self) -> Dict[str, Any]:
        """Generate complete audit log entry."""
        return {
            'protocol_name': self.name,
            'protocol_version': self.version,
            'source_file': self.source_file,
            'checksum': self.checksum,
            'load_timestamp': self.load_timestamp,
            'all_parameters': {
                k: v for k, v in self.__dict__.items()
            }
        }
        
    def to_yaml_dict(self) -> Dict[str, Any]:
        """
        Convert specification to YAML-compatible dictionary.
        
        Returns:
            Dictionary ready for YAML serialization
        """
        data = {
            'name': self.name,
            'version': self.version,
            'created_date': self.created_date,
            'author': self.author,
            'description': self.description,
            'protocol_type': self.protocol_type,
            'min_interval_days': self.min_interval_days,
            'max_interval_days': self.max_interval_days,
            'extension_days': self.extension_days,
            'shortening_days': self.shortening_days,
            'disease_transitions': self.disease_transitions,
            'vision_change_model': self.vision_change_model,
            'treatment_effect_on_transitions': self.treatment_effect_on_transitions,
            'baseline_vision': {
                'mean': self.baseline_vision_mean,
                'std': self.baseline_vision_std,
                'min': self.baseline_vision_min,
                'max': self.baseline_vision_max
            },
            'baseline_vision_distribution': self.baseline_vision_distribution,
            'discontinuation_rules': self.discontinuation_rules
        }
        
        # Include clinical improvements if present
        if self.clinical_improvements is not None:
            data['clinical_improvements'] = self.clinical_improvements
        
        return data
    
    def save_as_yaml(self, filepath: Path) -> None:
        """
        Save protocol specification back to YAML.
        
        Useful for creating modified versions.
        """
        data = self.to_yaml_dict()
        # Update created_date when saving
        data['created_date'] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)


def _validate_disease_transitions(transitions: Dict[str, Dict[str, float]]) -> None:
    """
    Validate disease transition probabilities.
    
    - All states must be defined
    - Probabilities must sum to 1.0
    - No negative probabilities
    """
    required_states = {'NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE'}
    
    # Check all states present
    if set(transitions.keys()) != required_states:
        raise ValueError(f"Disease transitions must include all states: {required_states}")
        
    # Validate each state's transitions
    for state, probs in transitions.items():
        # Check all target states present
        if set(probs.keys()) != required_states:
            raise ValueError(f"State {state} must define transitions to all states")
            
        # Check probabilities sum to 1.0
        total = sum(probs.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"State {state} probabilities sum to {total}, not 1.0")
            
        # Check no negative probabilities
        for target, prob in probs.items():
            if prob < 0:
                raise ValueError(f"Negative probability {prob} for {state}->{target}")


def _validate_vision_change_model(model: Dict[str, Any]) -> None:
    """
    Validate vision change model parameters.
    
    All state/treatment combinations must be defined.
    """
    required_scenarios = [
        'naive_treated', 'naive_untreated',
        'stable_treated', 'stable_untreated',
        'active_treated', 'active_untreated',
        'highly_active_treated', 'highly_active_untreated'
    ]
    
    missing = [s for s in required_scenarios if s not in model]
    if missing:
        raise ValueError(f"Vision change model missing scenarios: {missing}")
        
    # Each scenario must have mean and std
    for scenario, params in model.items():
        if 'mean' not in params or 'std' not in params:
            raise ValueError(f"Scenario {scenario} must have 'mean' and 'std'")
        if params['std'] < 0:
            raise ValueError(f"Scenario {scenario} has negative std: {params['std']}")