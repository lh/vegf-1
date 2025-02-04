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
        for phase_name, phase in phases.items():
            if 'duration_weeks' not in phase and 'visit_interval_weeks' not in phase:
                self.errors.append(ConfigurationError(
                    'protocol_definition',
                    f'Phase {phase_name} missing required timing parameters'
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
