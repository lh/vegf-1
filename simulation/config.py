from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime
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
    verbose: bool
    start_date: datetime
    
    def get_loading_phase_params(self) -> Dict[str, Any]:
        """Get loading phase parameters"""
        return self.parameters.get("treatment_response", {}).get("loading_phase", {})
    
    def get_maintenance_params(self) -> Dict[str, Any]:
        """Get maintenance phase parameters"""
        return self.parameters.get("treatment_response", {}).get("maintenance_phase", {})
    
    def get_vision_params(self) -> Dict[str, Any]:
        """Get vision-related parameters"""
        return self.parameters.get("vision", {})
    
    def get_resource_params(self) -> Dict[str, Any]:
        """Get resource-related parameters"""
        return self.parameters.get("resources", {})
    
    @classmethod
    def from_yaml(cls, config_name: str) -> 'SimulationConfig':
        parser = ProtocolParser()
        full_config = parser.get_full_configuration(config_name)
        
        # Parse start_date string to datetime
        start_date = datetime.strptime(
            full_config['config'].start_date,
            '%Y-%m-%d'
        )
        
        return cls(
            parameters=full_config['parameters'],
            protocol=full_config['protocol'],
            simulation_type=full_config['config'].simulation_type,
            num_patients=full_config['config'].num_patients,
            duration_days=full_config['config'].duration_days,
            random_seed=full_config['config'].random_seed,
            verbose=full_config['config'].verbose,
            start_date=start_date
        )
