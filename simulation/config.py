from dataclasses import dataclass
from typing import Dict, Any
from protocol_parser import ProtocolParser

@dataclass
class SimulationConfig:
    """Configuration for a simulation run"""
    parameters: Dict[str, Any]
    protocol: Dict[str, Any]
    simulation_type: str
    num_patients: int
    duration_days: int
    random_seed: int
    
    @classmethod
    def from_yaml(cls, config_name: str) -> 'SimulationConfig':
        parser = ProtocolParser()
        full_config = parser.get_full_configuration(config_name)
        
        return cls(
            parameters=full_config['parameters'],
            protocol=full_config['protocol'],
            simulation_type=full_config['config'].simulation_type,
            num_patients=full_config['config'].num_patients,
            duration_days=full_config['config'].duration_days,
            random_seed=full_config['config'].random_seed
        )
