"""Configuration validation for ophthalmic treatment protocol simulations.

This module provides validation of configuration files to ensure they meet the
required schema and contain all necessary parameters for simulation runs.

Key Components
-------------
ConfigurationError : Dataclass for storing validation errors
ConfigValidator : Main validation class with validation methods

Validation Types
---------------
- Base parameters validation
- Protocol definition validation
- Parameter set validation
- Simulation configuration validation

Examples
--------
>>> validator = ConfigValidator()
>>> is_valid = validator.validate_base_parameters(params)
>>> errors = validator.errors
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class ConfigurationError:
    """Dataclass for storing configuration validation errors.
    
    Attributes
    ----------
    path : str
        Path to the configuration element that failed validation
        Example: "protocol_definition.phases.loading"
    message : str
        Description of the validation error
        Example: "Missing required parameter: duration_weeks"
    """
    path: str
    message: str

class ConfigValidator:
    """Validates configuration files against required schemas.
    
    Provides validation for:
    - Base parameters
    - Protocol definitions  
    - Parameter sets
    - Simulation configurations
    
    Attributes
    ----------
    errors : List[ConfigurationError]
        List of validation errors encountered during validation
    """
    
    def __init__(self):
        self.errors: List[ConfigurationError] = []
    
    def validate_base_parameters(self, params: Dict) -> bool:
        """Validate base parameters structure.
        
        Parameters
        ----------
        params : Dict
            Dictionary containing base parameters configuration
            Must include sections: vision, treatment_response, disease_progression, resources
            
        Returns
        -------
        bool
            True if validation passes, False otherwise
            
        Examples
        --------
        >>> validator = ConfigValidator()
        >>> params = {
        ...     "vision": {...},
        ...     "treatment_response": {...},
        ...     "disease_progression": {...},
        ...     "resources": {...}
        ... }
        >>> is_valid = validator.validate_base_parameters(params)
        """
        required_sections = {
            'vision', 'treatment_response', 'disease_progression', 'resources'
        }
        
        if not all(section in params for section in required_sections):
            self.errors.append(ConfigurationError(
                'base_parameters.yaml',
                f'Missing required sections: {required_sections - set(params.keys())}'
            ))
            return False
            
        # Validate vision parameters
        vision_params = params.get('vision', {})
        required_vision_params = {
            'max_letters', 'min_letters', 'baseline_mean', 'baseline_sd',
            'measurement_noise_sd'
        }
        
        if not all(param in vision_params for param in required_vision_params):
            self.errors.append(ConfigurationError(
                'base_parameters.yaml',
                f'Missing required vision parameters: {required_vision_params - set(vision_params.keys())}'
            ))
            return False
            
        return True
    
    def validate_protocol_definition(self, protocol: Dict) -> bool:
        """Validate protocol definition structure.
        
        Parameters
        ----------
        protocol : Dict
            Dictionary containing protocol definition
            Must include fields: name, description, version, phases
            
        Returns
        -------
        bool
            True if validation passes, False otherwise
            
        Notes
        -----
        Validates:
        - Required fields are present
        - Required phases (loading, maintenance) exist
        - Phase parameters meet requirements
        - Visit types (if specified) are valid
        """
        required_fields = {'name', 'description', 'version', 'phases'}
        
        if not all(field in protocol for field in required_fields):
            self.errors.append(ConfigurationError(
                'protocol_definition',
                f'Missing required fields: {required_fields - set(protocol.keys())}'
            ))
            return False
            
        # Validate phases
        phases = protocol.get('phases', {})
        required_phases = {'loading', 'maintenance'}
        if not all(phase in phases for phase in required_phases):
            self.errors.append(ConfigurationError(
                'protocol_definition',
                f'Missing required phases: {required_phases - set(phases.keys())}'
            ))
            return False
            
        # Validate each phase
        phase_requirements = {
            'loading': {'duration_weeks', 'visit_interval_weeks', 'required_treatments'},
            'maintenance': {'visit_interval_weeks', 'min_interval_weeks', 'max_interval_weeks', 'interval_adjustment_weeks'}
        }
        
        for phase_name, phase in phases.items():
            if phase_name in phase_requirements:
                required = phase_requirements[phase_name]
                if not all(param in phase for param in required):
                    self.errors.append(ConfigurationError(
                        'protocol_definition',
                        f'Phase {phase_name} missing required parameters: {required - set(phase.keys())}'
                    ))
                    return False
                    
            # Validate visit types if present
            if 'visit_type' in phase:
                if not self._validate_visit_type(phase['visit_type']):
                    return False
                    
        return True
        
    def _validate_visit_type(self, visit_type: Dict) -> bool:
        """Validate visit type configuration.
        
        Parameters
        ----------
        visit_type : Dict
            Dictionary containing visit type configuration
            Must include fields: name, required_actions
            
        Returns
        -------
        bool
            True if validation passes, False otherwise
            
        Notes
        -----
        Validates:
        - Required fields are present
        - Action types are valid (vision_test, oct_scan, injection, consultation)
        """
        required_fields = {'name', 'required_actions'}
        if not all(field in visit_type for field in required_fields):
            self.errors.append(ConfigurationError(
                'visit_type',
                f'Missing required fields: {required_fields - set(visit_type.keys())}'
            ))
            return False
            
        # Validate action types
        valid_actions = {'vision_test', 'oct_scan', 'injection', 'consultation'}
        for action in visit_type.get('required_actions', []):
            if action not in valid_actions:
                self.errors.append(ConfigurationError(
                    'visit_type',
                    f'Invalid action type: {action}'
                ))
                return False
                
        return True
    
    def validate_parameter_set(self, params: Dict) -> bool:
        """Validate parameter set structure.
        
        Parameters
        ----------
        params : Dict
            Dictionary containing parameter set configuration
            Must include section: protocol_specific
            
        Returns
        -------
        bool
            True if validation passes, False otherwise
        """
        if 'protocol_specific' not in params:
            self.errors.append(ConfigurationError(
                'parameter_set',
                'Missing protocol_specific section'
            ))
            return False
            
        return True
    
    def validate_simulation_config(self, config: Dict) -> bool:
        """Validate simulation configuration.
        
        Parameters
        ----------
        config : Dict
            Dictionary containing simulation configuration
            Must include sections: name, protocol, simulation, output
            
        Returns
        -------
        bool
            True if validation passes, False otherwise
            
        Examples
        --------
        >>> validator = ConfigValidator()
        >>> config = {
        ...     "name": "test_simulation",
        ...     "protocol": "treat_and_extend",
        ...     "simulation": {...},
        ...     "output": {...}
        ... }
        >>> is_valid = validator.validate_simulation_config(config)
        """
        required_sections = {'name', 'protocol', 'simulation', 'output'}
        
        if not all(section in config for section in required_sections):
            self.errors.append(ConfigurationError(
                'simulation_config',
                f'Missing required sections: {required_sections - set(config.keys())}'
            ))
            return False
            
        return True
