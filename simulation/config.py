"""Simulation configuration management.

This module handles the configuration of simulation runs, including parameter validation,
protocol integration, and resource management. It ensures all simulation parameters
are properly validated before being used in a simulation run.

Classes
-------
SimulationConfig
    Main configuration class that encapsulates all simulation parameters

Key Features
------------
- Parameter validation for all configuration sections
- Protocol integration with validation
- Resource management
- Default value handling
- Type checking and range validation

Configuration Structure
----------------------- 
Example YAML configuration structure:
```yaml
simulation:
  type: "des"
  num_patients: 1000
  duration_days: 365
  random_seed: 42
  verbose: true
  start_date: "2023-01-01"
  resources:
    capacity:
      doctors: 5
      nurses: 10
      oct_machines: 3

clinical_model:
  disease_states: ["NAIVE", "STABLE", "ACTIVE", "HIGHLY_ACTIVE"]
  transition_probabilities:
    NAIVE:
      STABLE: 0.3
      ACTIVE: 0.6
      HIGHLY_ACTIVE: 0.1
    STABLE:
      STABLE: 0.7
      ACTIVE: 0.3
  vision_change:
    base_change:
      NAIVE:
        injection: [5, 2]
        no_injection: [0, 1]
      STABLE:
        injection: [2, 1]
        no_injection: [-1, 0.5]
    time_factor:
      max_weeks: 52
    ceiling_factor:
      max_vision: 100
    measurement_noise: [0, 0.5]
```

Notes
-----
- All numeric parameters are validated against expected ranges
- Probability parameters must sum to 1 where applicable
- Dates must be in YYYY-MM-DD format
- Missing parameters will use sensible defaults where possible
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from protocols.protocol_parser import ProtocolParser
from protocol_models import TreatmentProtocol
import logging

logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """
    Configuration for a simulation run with protocol objects.

    This class encapsulates all configuration parameters needed to run a simulation,
    including treatment protocols, patient parameters, and resource constraints.
    Provides validation methods for all configuration sections.

    Parameters
    ----------
    parameters : Dict[str, Any]
        Dictionary of simulation parameters
    protocol : TreatmentProtocol
        Treatment protocol to use in simulation
    simulation_type : str
        Type of simulation ('abs' or 'des')
    num_patients : int
        Number of patients to simulate
    duration_days : int
        Duration of simulation in days
    random_seed : int
        Random seed for reproducibility
    verbose : bool
        Whether to enable verbose logging
    start_date : datetime
        Simulation start date
    resources : Optional[Dict[str, Any]], optional
        Resource configuration dictionary

    Attributes
    ----------
    parameters : Dict[str, Any]
        Raw simulation parameters
    protocol : TreatmentProtocol
        Treatment protocol instance
    simulation_type : str
        Simulation type identifier
    num_patients : int
        Number of simulated patients
    duration_days : int
        Simulation duration
    random_seed : int
        Random seed value
    verbose : bool
        Verbosity flag
    start_date : datetime
        Simulation start date
    resources : Optional[Dict[str, Any]]
        Resource configuration
    """
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
        """
        Get validated vision-related parameters.

        Returns
        -------
        Dict[str, Any]
            Validated vision parameters

        Raises
        ------
        ValueError
            If required parameters are missing or invalid

        Notes
        -----
        Validates the following parameters:
        - baseline_mean: Valid ETDRS letter range (30-85)
        - measurement_noise_sd: Reasonable measurement noise (0-5)
        - max_letters: ETDRS maximum (0-100)
        - min_letters: ETDRS minimum (0-30)
        - headroom_factor: Must be between 0 and 1
        """
        vision_params = self.parameters.get("vision", {})
        if not vision_params:
            raise ValueError("Vision parameters not found")
            
        required_params = {
            "baseline_mean": (30, 85),
            "measurement_noise_sd": (0, 5),
            "max_letters": (0, 100),
            "min_letters": (0, 30),
            "headroom_factor": (0, 1)
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
        """
        Get validated maintenance phase parameters.

        Returns
        -------
        Dict[str, Any]
            Validated maintenance phase parameters

        Raises
        ------
        ValueError
            If required parameters are missing or invalid

        Notes
        -----
        Validates the following parameters:
        - memory_factor: Must be between 0 and 1
        - base_effect_ceiling: Maximum reasonable improvement (0-15)
        - regression_factor: Must be between 0 and 1
        - random_effect_mean: Reasonable range for log-normal mean (-2 to 2)
        - random_effect_sd: Reasonable range for log-normal SD (0 to 1)
        - decline_probability: Must be probability (0 to 1)
        - decline_effect_mean: Reasonable vision loss range (-5 to 0)
        - decline_effect_sd: Reasonable variation in loss (0 to 2)
        """
        params = self.parameters.get("treatment_response", {}).get("maintenance_phase", {})
        if not params:
            raise ValueError("Maintenance phase parameters not found")
            
        required_params = {
            "memory_factor": (0, 1),
            "base_effect_ceiling": (0, 15),
            "regression_factor": (0, 1),
            "random_effect_mean": (-2, 2),
            "random_effect_sd": (0, 1),
            "decline_probability": (0, 1),
            "decline_effect_mean": (-5, 0),
            "decline_effect_sd": (0, 2)
        }
        
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
        """
        Get validated loading phase parameters.

        Returns
        -------
        Dict[str, Any]
            Validated loading phase parameters

        Raises
        ------
        ValueError
            If required parameters are missing, invalid, or probabilities don't sum to 1

        Notes
        -----
        Validates the following parameters:
        - vision_improvement_mean: Reasonable letter improvement (0-15)
        - vision_improvement_sd: Reasonable variation (0-5)
        - improve_probability: Must be probability (0-1)
        - stable_probability: Must be probability (0-1)
        - decline_probability: Must be probability (0-1)
        """
        params = self.parameters.get("treatment_response", {}).get("loading_phase", {})
        if not params:
            raise ValueError("Loading phase parameters not found")
            
        required_params = {
            "vision_improvement_mean": (0, 15),
            "vision_improvement_sd": (0, 5),
            "improve_probability": (0, 1),
            "stable_probability": (0, 1),
            "decline_probability": (0, 1)
        }
        
        for param, (min_val, max_val) in required_params.items():
            if param not in params:
                raise ValueError(f"Missing required loading phase parameter: {param}")
            value = params[param]
            if not isinstance(value, (int, float)):
                raise ValueError(f"Loading phase parameter {param} must be numeric")
            if not min_val <= value <= max_val:
                raise ValueError(f"Loading phase parameter {param} must be between {min_val} and {max_val}")
                
        prob_sum = (params["improve_probability"] + 
                   params["stable_probability"] + 
                   params["decline_probability"])
        if not 0.99 <= prob_sum <= 1.01:
            raise ValueError("Loading phase probabilities must sum to 1.0")
                
        return params
    
    def get_resource_params(self) -> Dict[str, Any]:
        """
        Get resource configuration parameters.

        Returns
        -------
        Dict[str, Any]
            Resource parameters with defaults:
            - doctors: 5
            - nurses: 5
            - oct_machines: 5

        Notes
        -----
        First checks simulation.resources.capacity if it exists,
        otherwise falls back to default values.
        """
        sim_resources = getattr(self, 'resources', {})
        if sim_resources and isinstance(sim_resources, dict):
            capacity = sim_resources.get("capacity", {})
            if capacity:
                return {
                    "doctors": capacity.get("doctors", 5),
                    "nurses": capacity.get("nurses", 5),
                    "oct_machines": capacity.get("oct_machines", 5)
                }
        return {
            "doctors": 5,
            "nurses": 5,
            "oct_machines": 5
        }
    
    def get_des_params(self) -> Dict[str, Any]:
        """Get DES-specific parameters.

        Returns
        -------
        Dict[str, Any]
            DES parameters with defaults:
            - daily_capacity: 20 patients
            - days_per_week: 5 days
            - patient_generation:
                - rate_per_week: 3 patients
                - random_seed: None (use simulation seed)
        """
        simulation = self.parameters.get("simulation", {})
        scheduling = simulation.get("scheduling", {})
        patient_gen = simulation.get("patient_generation", {})
        
        return {
            "daily_capacity": scheduling.get("daily_capacity", 20),
            "days_per_week": scheduling.get("days_per_week", 5),
            "patient_generation": {
                "rate_per_week": patient_gen.get("rate_per_week", 3),
                "random_seed": patient_gen.get("random_seed", None)
            }
        }
        
    def get_output_params(self) -> Dict[str, Any]:
        """
        Get output configuration parameters.

        Returns
        -------
        Dict[str, Any]
            Output parameters with defaults:
            - save_results: True
            - database: 'simulations.db'
            - plots: True
            - verbose: False
        """
        output_params = self.parameters.get("output", {})
        if not output_params:
            return {
                "save_results": True,
                "database": "simulations.db",
                "plots": True,
                "verbose": False
            }
        return output_params

    def get_clinical_model_params(self) -> Dict[str, Any]:
        """
        Get validated clinical model parameters.

        Returns
        -------
        Dict[str, Any]
            Validated clinical model parameters

        Raises
        ------
        ValueError
            If required sections or parameters are missing

        Notes
        -----
        Validates the following required sections:
        - disease_states
        - transition_probabilities
        - vision_change

        For vision_change, validates:
        - base_change
        - time_factor
        - ceiling_factor
        - measurement_noise
        """
        logger.debug(f"Getting clinical model parameters. Full parameters: {self.parameters}")
        clinical_model_params = self.parameters.get("clinical_model", {})
        if not clinical_model_params:
            logger.error("Clinical model parameters not found in configuration")
            raise ValueError("Clinical model parameters not found in configuration")
        
        required_sections = ["disease_states", "transition_probabilities", "vision_change"]
        for section in required_sections:
            if section not in clinical_model_params:
                logger.error(f"Missing required clinical model section: {section}")
                raise ValueError(f"Missing required clinical model section: {section}")
        
        vision_change = clinical_model_params["vision_change"]
        required_vision_change_params = ["base_change", "time_factor", "ceiling_factor", "measurement_noise"]
        for param in required_vision_change_params:
            if param not in vision_change:
                logger.error(f"Missing required vision change parameter: {param}")
                raise ValueError(f"Missing required vision change parameter: {param}")
        
        return clinical_model_params
    
    @classmethod
    def from_yaml(cls, config_name: str) -> 'SimulationConfig':
        """
        Create configuration from YAML with protocol objects.

        Parameters
        ----------
        config_name : str
            Name of the configuration to load

        Returns
        -------
        SimulationConfig
            New SimulationConfig instance

        Raises
        ------
        ValueError
            If protocol is invalid or required parameters are missing

        Notes
        -----
        Uses ProtocolParser to load and validate the full configuration,
        including protocol definitions and parameter validation.
        """
        parser = ProtocolParser()
        full_config = parser.get_full_configuration(config_name)
        
        start_date = datetime.strptime(
            full_config['config'].start_date,
            '%Y-%m-%d'
        )
        
        if not isinstance(full_config['protocol'], TreatmentProtocol):
            raise ValueError("Protocol must be a TreatmentProtocol object")
            
        resources = None
        if hasattr(full_config['config'], 'simulation'):
            sim_config = full_config['config'].simulation
            if hasattr(sim_config, 'resources'):
                resources = sim_config.resources
        
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
