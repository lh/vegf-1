from pathlib import Path
from typing import Dict, Any, List
import yaml
from dataclasses import dataclass
from validation.config_validator import ConfigValidator, ConfigurationError

@dataclass
class SimulationConfig:
    name: str
    protocol_agent: str
    protocol_type: str
    parameter_set: str
    simulation_type: str
    duration_days: int
    num_patients: int
    random_seed: int
    save_results: bool
    database: str
    plots: bool
    verbose: bool
    start_date: str
    description: str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ProtocolParser:
    def __init__(self, base_path: str = "protocols"):
        self.base_path = Path(base_path)
        self.validator = ConfigValidator()
        self.base_parameters = self._load_base_parameters()
    
    def _load_base_parameters(self) -> Dict:
        """Load and validate base parameters file"""
        with open(self.base_path / "base_parameters.yaml") as f:
            params = yaml.safe_load(f)
            
        if not self.validator.validate_base_parameters(params):
            raise ValueError(f"Invalid base parameters: {self.validator.errors}")
            
        return params
    
    def _load_protocol_definition(self, agent: str, protocol_type: str) -> Dict:
        """Load and validate protocol definition"""
        path = self.base_path / "protocol_definitions" / agent / f"{protocol_type}.yaml"
        with open(path) as f:
            protocol = yaml.safe_load(f)
            
        if not self.validator.validate_protocol_definition(protocol):
            raise ValueError(f"Invalid protocol definition: {self.validator.errors}")
            
        return protocol
    
    def _load_parameter_set(self, agent: str, parameter_set: str) -> Dict:
        """Load and validate parameter set and merge with base parameters"""
        path = self.base_path / "parameter_sets" / agent / f"{parameter_set}.yaml"
        with open(path) as f:
            params = yaml.safe_load(f)
            
        if not self.validator.validate_parameter_set(params):
            raise ValueError(f"Invalid parameter set: {self.validator.errors}")
        
        # Deep copy base parameters to avoid modifying original
        merged = self.base_parameters.copy()
        
        # Merge protocol specific parameters
        protocol_params = params.get("protocol_specific", {})
        for category, values in protocol_params.items():
            if category in merged:
                merged[category].update(values)
            else:
                merged[category] = values
                
        return merged
    
    def load_simulation_config(self, config_name: str) -> SimulationConfig:
        """Load simulation configuration"""
        path = self.base_path / "simulation_configs" / f"{config_name}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
        
        return SimulationConfig(
            name=config["name"],
            description=config["description"],
            protocol_agent=config["protocol"]["agent"],
            protocol_type=config["protocol"]["type"],
            parameter_set=config["protocol"]["parameter_set"],
            simulation_type=config["simulation"]["type"],
            duration_days=config["simulation"]["duration_days"],
            num_patients=config["simulation"]["num_patients"],
            random_seed=config["simulation"]["random_seed"],
            save_results=config["output"]["save_results"],
            database=config["output"]["database"],
            plots=config["output"]["plots"],
            verbose=config["output"]["verbose"],
            start_date=config["simulation"]["start_date"]
        )
    
    def get_full_configuration(self, config_name: str) -> Dict[str, Any]:
        """Get complete configuration including protocol and parameters"""
        config = self.load_simulation_config(config_name)
        protocol = self._load_protocol_definition(config.protocol_agent, config.protocol_type)
        parameters = self._load_parameter_set(config.protocol_agent, config.parameter_set)
        
        return {
            "config": config,
            "protocol": protocol,
            "parameters": parameters
        }

def load_protocol(config_name: str) -> Dict[str, Any]:
    """Legacy support function"""
    parser = ProtocolParser()
    return parser.get_full_configuration(config_name)
