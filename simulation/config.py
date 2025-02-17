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
    resources: Optional[Dict[str, Any]] = None
    
    def get_vision_params(self) -> Dict[str, Any]:
        """Get vision-related parameters with validation"""
        vision_params = self.parameters.get("vision", {})
        if not vision_params:
            raise ValueError("Vision parameters not found")
            
        required_params = {
            "baseline_mean": (30, 85),  # Valid ETDRS letter range
            "measurement_noise_sd": (0, 5),  # Reasonable measurement noise
            "max_letters": (0, 100),  # ETDRS maximum
            "min_letters": (0, 30),  # ETDRS minimum
            "headroom_factor": (0, 1)  # Must be between 0 and 1
        }
        
        for param, (min_val, max_val) in required_params.items():
            if param not in vision_params:
                raise ValueError(f"Missing required vision parameter: {param}")
            value = vision_params[param]
            if not isinstance(value, (int, float)):
                raise ValueError(f"Vision parameter {param} must be numeric")
            if not min_val <= value <= max_val:
                raise ValueError(f"Vision parameter {param} must be between {min_val} and {max_val}")
                
        return vision_params
    
    def get_maintenance_params(self) -> Dict[str, Any]:
        """Get maintenance phase parameters with validation"""
        params = self.parameters.get("treatment_response", {}).get("maintenance_phase", {})
        if not params:
            raise ValueError("Maintenance phase parameters not found")
            
        required_params = {
            "memory_factor": (0, 1),  # Must be between 0 and 1
            "base_effect_ceiling": (0, 15),  # Maximum reasonable improvement
            "regression_factor": (0, 1),  # Must be between 0 and 1
            "random_effect_mean": (-2, 2),  # Reasonable range for log-normal mean
            "random_effect_sd": (0, 1),  # Reasonable range for log-normal SD
            "decline_probability": (0, 1),  # Must be probability
            "decline_effect_mean": (-5, 0),  # Reasonable vision loss range
            "decline_effect_sd": (0, 2)  # Reasonable variation in loss
        }
        
        # Validate required parameters
        for param, (min_val, max_val) in required_params.items():
            if param not in params:
                raise ValueError(f"Missing required maintenance phase parameter: {param}")
            value = params[param]
            if not isinstance(value, (int, float)):
                raise ValueError(f"Maintenance phase parameter {param} must be numeric")
            if not min_val <= value <= max_val:
                raise ValueError(f"Maintenance phase parameter {param} must be between {min_val} and {max_val}")
                
        return params

    def get_loading_phase_params(self) -> Dict[str, Any]:
        """Get loading phase parameters with validation"""
        params = self.parameters.get("treatment_response", {}).get("loading_phase", {})
        if not params:
            raise ValueError("Loading phase parameters not found")
            
        required_params = {
            "vision_improvement_mean": (0, 15),  # Reasonable letter improvement
            "vision_improvement_sd": (0, 5),  # Reasonable variation
            "improve_probability": (0, 1),  # Must be probability
            "stable_probability": (0, 1),
            "decline_probability": (0, 1)
        }
        
        # Validate required parameters
        for param, (min_val, max_val) in required_params.items():
            if param not in params:
                raise ValueError(f"Missing required loading phase parameter: {param}")
            value = params[param]
            if not isinstance(value, (int, float)):
                raise ValueError(f"Loading phase parameter {param} must be numeric")
            if not min_val <= value <= max_val:
                raise ValueError(f"Loading phase parameter {param} must be between {min_val} and {max_val}")
                
        # Validate probabilities sum to 1
        prob_sum = (params["improve_probability"] + 
                   params["stable_probability"] + 
                   params["decline_probability"])
        if not 0.99 <= prob_sum <= 1.01:  # Allow for small floating point errors
            raise ValueError("Loading phase probabilities must sum to 1.0")
                
        return params
    
    def get_vision_params(self) -> Dict[str, Any]:
        """Get vision-related parameters"""
        vision_params = self.parameters.get("vision", {})
        if not vision_params:
            raise ValueError("Vision parameters not found")
        return vision_params

    def get_resource_params(self) -> Dict[str, Any]:
        """Get resource-related parameters"""
        # Get from simulation.resources.capacity if it exists
        sim_resources = getattr(self, 'resources', {})
        if sim_resources and isinstance(sim_resources, dict):
            capacity = sim_resources.get("capacity", {})
            if capacity:
                return {
                    "doctors": capacity.get("doctors", 5),
                    "nurses": capacity.get("nurses", 5),
                    "oct_machines": capacity.get("oct_machines", 5)
                }
        # Fallback to default values
        return {
            "doctors": 5,
            "nurses": 5,
            "oct_machines": 5
        }
    
    def get_des_params(self) -> Dict[str, Any]:
        """Get DES-specific parameters"""
        scheduling = self.parameters.get("simulation", {}).get("scheduling", {})
        return {
            "daily_capacity": scheduling.get("daily_capacity", 20),  # Default to 20 patients per day
            "days_per_week": scheduling.get("days_per_week", 5)     # Default to 5 days per week
        }
    
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
            
        # Extract resources configuration if present
        resources = None
        if hasattr(full_config['config'], 'simulation'):
            sim_config = full_config['config'].simulation
            if hasattr(sim_config, 'resources'):
                resources = sim_config.resources
        
        # Create config with validated protocol
        return cls(
            parameters=full_config['parameters'],
            protocol=full_config['protocol'],
            simulation_type=full_config['config'].simulation_type,
            num_patients=full_config['config'].num_patients,
            duration_days=full_config['config'].duration_days,
            random_seed=full_config['config'].random_seed,
            verbose=full_config['config'].verbose,
            start_date=start_date,
            resources=resources
        )
