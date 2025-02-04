from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class ConfigurationError:
    path: str
    message: str

class ConfigValidator:
    """Validates configuration files against schema"""
    
    def __init__(self):
        self.errors: List[ConfigurationError] = []
    
    def validate_base_parameters(self, params: Dict) -> bool:
        """Validate base parameters structure"""
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
        """Validate protocol definition structure"""
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
        """Validate visit type configuration"""
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
        """Validate parameter set structure"""
        if 'protocol_specific' not in params:
            self.errors.append(ConfigurationError(
                'parameter_set',
                'Missing protocol_specific section'
            ))
            return False
            
        return True
    
    def validate_simulation_config(self, config: Dict) -> bool:
        """Validate simulation configuration"""
        required_sections = {'name', 'protocol', 'simulation', 'output'}
        
        if not all(section in config for section in required_sections):
            self.errors.append(ConfigurationError(
                'simulation_config',
                f'Missing required sections: {required_sections - set(config.keys())}'
            ))
            return False
            
        return True
