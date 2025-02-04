from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from protocol_parser import ProtocolParser
from protocol_models import TreatmentProtocol

@dataclass
class SimulationConfig:
    """Configuration for a simulation run with protocol objects"""
    parameters: Dict[str, Any]
    protocol: TreatmentProtocol
    simulation_type: str
    num_patients: int
    duration_days: int
    random_seed: int
    verbose: bool
    start_date: datetime
    
    def get_vision_params(self) -> Dict[str, Any]:
        """Get vision-related parameters"""
        vision_params = self.parameters.get("vision", {})
        if not vision_params:
            raise ValueError("Vision parameters not found")
        return vision_params
    
    def get_loading_phase_params(self) -> Dict[str, Any]:
        """Get loading phase parameters"""
        params = self.parameters.get("treatment_response", {}).get("loading_phase", {})
        if not params:
            raise ValueError("Loading phase parameters not found")
        return params
    
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
        """Create configuration from YAML with protocol objects"""
        parser = ProtocolParser()
        full_config = parser.get_full_configuration(config_name)
        
        # Parse start_date string to datetime
        start_date = datetime.strptime(
            full_config['config'].start_date,
            '%Y-%m-%d'
        )
        
        # Validate protocol is correct type
        if not isinstance(full_config['protocol'], TreatmentProtocol):
            raise ValueError("Protocol must be a TreatmentProtocol object")
            
        # Create config with validated protocol
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
