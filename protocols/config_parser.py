"""Configuration management for ophthalmic treatment protocol simulations.

This module handles loading and merging configuration files for simulation runs,
including protocol definitions, parameter sets, and simulation settings.

Key Components
--------------
SimulationConfig : Dataclass for storing simulation configuration
ConfigurationManager : Main class for loading and merging configurations

Configuration Files
-------------------
- base_parameters.yaml : Common parameters for all protocols
- protocol_definitions/ : Protocol-specific definitions
- parameter_sets/ : Protocol-specific parameters
- simulation_configs/ : Complete simulation configurations

Examples
--------
>>> manager = ConfigurationManager()
>>> config = manager.load_simulation_config('test_simulation')
>>> full_config = manager.get_full_configuration('test_simulation')
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for a simulation run.
    
    Attributes
    ----------
    name : str
        Name of the simulation configuration
    protocol_agent : str
        Name of the treatment agent (e.g., 'Aflibercept')
    protocol_type : str
        Type of protocol (e.g., 'standard', 'intensive')
    parameter_set : str
        Name of parameter set to use
    simulation_type : str
        Type of simulation ('abs' or 'des')
    duration_days : int
        Duration of simulation in days
    num_patients : int
        Number of patients to simulate
    random_seed : int
        Random seed for reproducibility
    save_results : bool
        Whether to save results to database
    database : str
        Database path/name for results
    plots : bool
        Whether to generate plots
    verbose : bool
        Enable verbose output
    resources : Dict[str, Any], optional
        Additional resource definitions
    """
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
    resources: Dict[str, Any] = None

class ConfigurationManager:
    def __init__(self, base_path: str = "protocols"):
        self.base_path = Path(base_path)
        self.base_parameters = self._load_base_parameters()
        
    def _load_base_parameters(self) -> Dict:
        """Load the base parameters file from protocols/base_parameters.yaml.
        
        Returns
        -------
        Dict
            Dictionary containing base parameters for all protocols
            
        Raises
        ------
        FileNotFoundError
            If base_parameters.yaml cannot be found
        """
        with open(self.base_path / "base_parameters.yaml") as f:
            return yaml.safe_load(f)
            
    def _load_protocol_definition(self, agent: str, protocol_type: str) -> Dict:
        """Load a protocol definition YAML file.
        
        Parameters
        ----------
        agent : str
            Name of treatment agent (e.g., 'Aflibercept')
        protocol_type : str
            Type of protocol (e.g., 'standard')
            
        Returns
        -------
        Dict
            Dictionary containing protocol definition
            
        Raises
        ------
        FileNotFoundError
            If protocol definition file cannot be found
        """
        path = self.base_path / "protocol_definitions" / agent / f"{protocol_type}.yaml"
        with open(path) as f:
            return yaml.safe_load(f)
            
    def _load_parameter_set(self, agent: str, parameter_set: str) -> Dict:
        """Load a parameter set and merge with base parameters.
        
        Parameters
        ----------
        agent : str
            Name of treatment agent
        parameter_set : str
            Name of parameter set to load
            
        Returns
        -------
        Dict
            Merged dictionary of base and protocol-specific parameters
            
        Notes
        -----
        - Base parameters provide defaults
        - Protocol-specific parameters override base parameters
        - Parameters are stored under 'protocol_specific' key in YAML
        """
        path = self.base_path / "parameter_sets" / agent / f"{parameter_set}.yaml"
        with open(path) as f:
            params = yaml.safe_load(f)
            
        # Merge with base parameters
        merged = self.base_parameters.copy()
        merged.update(params.get("protocol_specific", {}))
        return merged
        
    def load_simulation_config(self, config_name: str) -> SimulationConfig:
        """Load a simulation configuration from YAML.
        
        Parameters
        ----------
        config_name : str
            Name of configuration file (without .yaml extension)
            
        Returns
        -------
        SimulationConfig
            Configuration dataclass instance
            
        Examples
        --------
        >>> manager = ConfigurationManager()
        >>> config = manager.load_simulation_config('test_simulation')
        >>> print(config.protocol_agent)
        'Aflibercept'
        """
        path = self.base_path / "simulation_configs" / f"{config_name}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
            
        # Extract resources if present
        resources = None
        if "resources" in config["simulation"]:
            resources = config["simulation"]["resources"]
            
        return SimulationConfig(
            name=config["name"],
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
            resources=resources
        )
        
    def get_full_configuration(self, config_name: str) -> Dict[str, Any]:
        """Get complete merged configuration for a simulation.
        
        Combines:
        - Simulation configuration
        - Protocol definition
        - Parameter sets
        - Clinical model parameters (if present)
        
        Parameters
        ----------
        config_name : str
            Name of configuration file (without .yaml extension)
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all configuration components with keys:
            - 'config': SimulationConfig
            - 'protocol': Protocol definition
            - 'parameters': Merged parameters
            
        Examples
        --------
        >>> manager = ConfigurationManager()
        >>> full_config = manager.get_full_configuration('test_simulation')
        >>> print(full_config['parameters']['injection_interval_weeks'])
        4
        """
        logger.debug(f"Loading full configuration for {config_name}")
        config_path = self.base_path / "simulation_configs" / f"{config_name}.yaml"
        logger.debug(f"Loading configuration from: {config_path}")
        logger.debug(f"Absolute path: {config_path.resolve()}")
        if config_path.exists():
            logger.debug(f"Config file exists at {config_path}")
            with open(config_path, 'r') as f:
                logger.debug(f"File contents: {f.read()}")
        else:
            logger.warning(f"Config file does not exist at {config_path}")
            logger.debug(f"Current working directory: {Path.cwd()}")
            logger.debug(f"Contents of {self.base_path / 'simulation_configs'}: {list((self.base_path / 'simulation_configs').glob('*'))}")
        
        config = self.load_simulation_config(config_name)
        logger.debug(f"Loaded simulation config: {config}")
        
        protocol_path = self.base_path / "protocol_definitions" / config.protocol_agent / f"{config.protocol_type}.yaml"
        logger.debug(f"Loading protocol definition from: {protocol_path}")
        protocol = self._load_protocol_definition(config.protocol_agent, config.protocol_type)
        logger.debug(f"Loaded protocol definition: {protocol}")
        
        parameter_set_path = self.base_path / "parameter_sets" / config.protocol_agent / f"{config.parameter_set}.yaml"
        logger.debug(f"Loading parameter set from: {parameter_set_path}")
        parameters = self._load_parameter_set(config.protocol_agent, config.parameter_set)
        logger.debug(f"Loaded parameter set: {parameters}")
        
        # Load the full simulation configuration to get clinical model parameters
        path = self.base_path / "simulation_configs" / f"{config_name}.yaml"
        with open(path) as f:
            full_config = yaml.safe_load(f)
        logger.debug(f"Loaded full simulation config: {full_config}")
        
        # Create final configuration with resources and clinical model
        final_config = {
            "config": config,
            "protocol": protocol,
            "parameters": parameters
        }
        
        # Add clinical model parameters if present
        logger.debug(f"Full config structure: {full_config.keys()}")
        logger.debug(f"Simulation section: {full_config.get('simulation', {})}")
        logger.debug(f"Clinical model content from YAML: {full_config.get('simulation', {}).get('clinical_model')}")
        if "simulation" in full_config and "clinical_model" in full_config["simulation"]:
            final_config["parameters"]["clinical_model"] = full_config["simulation"]["clinical_model"]
            logger.debug(f"Added clinical model parameters: {final_config['parameters']['clinical_model']}")
        else:
            logger.warning("Clinical model parameters not found in simulation configuration")
            logger.debug(f"Full simulation config structure: {full_config.keys()}")
            if "simulation" in full_config:
                logger.debug(f"Simulation section keys: {full_config['simulation'].keys()}")
        
        logger.debug(f"Final config structure: {final_config.keys()}")
        logger.debug(f"Final parameters structure: {final_config['parameters'].keys()}")
        logger.debug(f"Clinical model in final parameters: {final_config['parameters'].get('clinical_model')}")
        
        # Add resources to parameters if present
        if config.resources:
            if "resources" not in final_config["parameters"]:
                final_config["parameters"]["resources"] = {}
            final_config["parameters"]["resources"].update(config.resources)
            logger.debug(f"Added resources: {final_config['parameters']['resources']}")
        
        logger.debug(f"Final configuration parameters: {final_config['parameters'].keys()}")
        logger.debug(f"Full final configuration: {final_config}")
        return final_config
