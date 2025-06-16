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
    
    # Loading dose parameters (optional)
    loading_dose_injections: Optional[int] = None
    loading_dose_interval_days: Optional[int] = None
    
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
    
    # Model configuration (with defaults)
    model_type: str = "time_based"
    update_interval_days: int = 14  # Fortnightly
    
    # Protocol checksum for verification
    checksum: str = ""
    
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
            'baseline_vision'
        ]
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Extract baseline vision
        baseline = data['baseline_vision']
        if not all(k in baseline for k in ['mean', 'std', 'min', 'max']):
            raise ValueError("baseline_vision must have mean, std, min, max")
        
        return cls(
            name=data['name'],
            version=data['version'],
            created_date=data.get('created_date', 'unknown'),
            author=data['author'],
            description=data['description'],
            model_type=data.get('model_type', 'time_based'),
            update_interval_days=data.get('update_interval_days', 14),
            protocol_type=data['protocol_type'],
            loading_dose_injections=data.get('loading_dose_injections'),
            loading_dose_interval_days=data.get('loading_dose_interval_days'),
            min_interval_days=data['min_interval_days'],
            max_interval_days=data['max_interval_days'],
            extension_days=data['extension_days'],
            shortening_days=data['shortening_days'],
            baseline_vision_mean=baseline['mean'],
            baseline_vision_std=baseline['std'],
            baseline_vision_min=baseline['min'],
            baseline_vision_max=baseline['max'],
            disease_transitions_file=data['disease_transitions_file'],
            treatment_effect_file=data['treatment_effect_file'],
            vision_parameters_file=data['vision_parameters_file'],
            discontinuation_parameters_file=data['discontinuation_parameters_file'],
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
                'discontinuation': self.discontinuation_parameters_file
            }
        }