"""
Time-based protocol specification.

Completely separate from standard ProtocolSpecification as the models
are fundamentally different in their parameters and behavior.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import hashlib
from datetime import datetime


@dataclass(frozen=True)
class TimeBasedProtocolSpecification:
    """
    Protocol specification for time-based disease progression model.
    
    Key differences from standard protocols:
    - Disease updates happen fortnightly, not per-visit
    - Vision evolves continuously between visits
    - Complex discontinuation model with multiple reasons
    - Treatment effects decay over time
    """
    
    # Metadata
    name: str
    version: str
    created_date: str
    author: str
    description: str
    
    # Treatment protocol parameters
    protocol_type: str  # "treat_and_extend", etc.
    
    # Treat-and-extend parameters
    min_interval_days: int
    max_interval_days: int
    extension_days: int
    shortening_days: int
    
    # Baseline parameters
    baseline_vision_mean: int
    baseline_vision_std: int
    baseline_vision_min: int
    baseline_vision_max: int
    
    # Parameter file references (relative to protocol file)
    disease_transitions_file: str
    treatment_effect_file: str
    vision_parameters_file: str
    discontinuation_parameters_file: str
    
    # File tracking
    source_file: str
    load_timestamp: str
    
    # Optional parameter files
    demographics_parameters_file: Optional[str] = None
    
    # Model configuration (with defaults)
    model_type: str = "time_based"
    transition_model: str = "fortnightly"  # How disease states transition
    update_interval_days: int = 14  # Fortnightly
    
    # Loading dose parameters (optional)
    loading_dose_injections: Optional[int] = None
    loading_dose_interval_days: Optional[int] = None
    
    # Protocol checksum for verification
    checksum: str = ""
    
    # Optional: Advanced baseline vision distribution
    baseline_vision_distribution: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, filepath: Path) -> 'TimeBasedProtocolSpecification':
        """
        Load time-based protocol from YAML file.
        
        Args:
            filepath: Path to YAML protocol file
            
        Returns:
            TimeBasedProtocolSpecification instance
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Protocol file not found: {filepath}")
        
        # Load YAML
        with open(filepath) as f:
            data = yaml.safe_load(f)
        
        # Calculate checksum for audit trail
        with open(filepath, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        # Validate model type
        model_type = data.get('model_type', '')
        if model_type != 'time_based':
            raise ValueError(f"Expected time_based model, got: {model_type}")
        
        # Validate required fields
        required_fields = [
            'name', 'version', 'author', 'description',
            'protocol_type', 'min_interval_days', 'max_interval_days',
            'extension_days', 'shortening_days',
            'disease_transitions_file', 'treatment_effect_file',
            'vision_parameters_file', 'discontinuation_parameters_file',
            'baseline_vision_distribution'
        ]
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
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
            model_type=data.get('model_type', 'time_based'),
            transition_model=data.get('transition_model', 'fortnightly'),
            update_interval_days=data.get('update_interval_days', 14),
            protocol_type=data['protocol_type'],
            loading_dose_injections=data.get('loading_dose_injections'),
            loading_dose_interval_days=data.get('loading_dose_interval_days'),
            min_interval_days=data['min_interval_days'],
            max_interval_days=data['max_interval_days'],
            extension_days=data['extension_days'],
            shortening_days=data['shortening_days'],
            baseline_vision_mean=baseline_mean,
            baseline_vision_std=baseline_std,
            baseline_vision_min=baseline_min,
            baseline_vision_max=baseline_max,
            baseline_vision_distribution=data['baseline_vision_distribution'],
            disease_transitions_file=data['disease_transitions_file'],
            treatment_effect_file=data['treatment_effect_file'],
            vision_parameters_file=data['vision_parameters_file'],
            discontinuation_parameters_file=data['discontinuation_parameters_file'],
            demographics_parameters_file=data.get('demographics_parameters_file'),
            source_file=str(filepath.absolute()),
            load_timestamp=datetime.now().isoformat(),
            checksum=checksum
        )
    
    def load_disease_transitions(self) -> Dict[str, Any]:
        """Load disease transition parameters from file."""
        param_path = Path(self.source_file).parent / self.disease_transitions_file
        with open(param_path) as f:
            return yaml.safe_load(f)
    
    def load_treatment_effects(self) -> Dict[str, Any]:
        """Load treatment effect parameters from file."""
        param_path = Path(self.source_file).parent / self.treatment_effect_file
        with open(param_path) as f:
            return yaml.safe_load(f)
    
    def load_vision_parameters(self) -> Dict[str, Any]:
        """Load vision model parameters from file."""
        param_path = Path(self.source_file).parent / self.vision_parameters_file
        with open(param_path) as f:
            return yaml.safe_load(f)
    
    def load_discontinuation_parameters(self) -> Dict[str, Any]:
        """Load discontinuation model parameters from file."""
        param_path = Path(self.source_file).parent / self.discontinuation_parameters_file
        with open(param_path) as f:
            return yaml.safe_load(f)
    
    def load_demographics_parameters(self) -> Optional[Dict[str, Any]]:
        """Load demographics parameters from file if available."""
        if not self.demographics_parameters_file:
            return None
        param_path = Path(self.source_file).parent / self.demographics_parameters_file
        if param_path.exists():
            with open(param_path) as f:
                return yaml.safe_load(f)
        return None
    
    def to_audit_log(self) -> Dict[str, Any]:
        """Generate audit log entry."""
        return {
            'protocol_name': self.name,
            'protocol_version': self.version,
            'model_type': self.model_type,
            'source_file': self.source_file,
            'checksum': self.checksum,
            'load_timestamp': self.load_timestamp,
            'parameter_files': {
                'disease_transitions': self.disease_transitions_file,
                'treatment_effects': self.treatment_effect_file,
                'vision': self.vision_parameters_file,
                'discontinuation': self.discontinuation_parameters_file,
                'demographics': self.demographics_parameters_file
            }
        }
    
    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert specification to YAML-serializable dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'created_date': self.created_date,
            'author': self.author,
            'description': self.description,
            'model_type': self.model_type,
            'transition_model': self.transition_model,
            'update_interval_days': self.update_interval_days,
            'protocol_type': self.protocol_type,
            'min_interval_days': self.min_interval_days,
            'max_interval_days': self.max_interval_days,
            'extension_days': self.extension_days,
            'shortening_days': self.shortening_days,
            'loading_dose_injections': self.loading_dose_injections,
            'loading_dose_interval_days': self.loading_dose_interval_days,
            'baseline_vision': {
                'mean': self.baseline_vision_mean,
                'std': self.baseline_vision_std,
                'min': self.baseline_vision_min,
                'max': self.baseline_vision_max
            },
            'baseline_vision_distribution': self.baseline_vision_distribution,
            'disease_transitions_file': self.disease_transitions_file,
            'treatment_effect_file': self.treatment_effect_file,
            'vision_parameters_file': self.vision_parameters_file,
            'discontinuation_parameters_file': self.discontinuation_parameters_file,
            'demographics_parameters_file': self.demographics_parameters_file
        }