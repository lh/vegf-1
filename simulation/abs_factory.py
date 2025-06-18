"""Factory for creating appropriate ABS engine based on configuration.

This module provides automatic engine selection between standard and heterogeneous
ABS implementations based on the presence and validity of heterogeneity configuration
in the protocol YAML.

The factory validates heterogeneity sections and provides clear console feedback
about which engine is being used.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

from .base import BaseSimulation
from .abs import AgentBasedSimulation
from .heterogeneous_abs import HeterogeneousABS
from .config import SimulationConfig

logger = logging.getLogger(__name__)


class ABSFactory:
    """Factory for creating appropriate ABS engine based on configuration."""
    
    @staticmethod
    def create_simulation(config: SimulationConfig, start_date: datetime) -> BaseSimulation:
        """
        Create appropriate simulation engine based on configuration content.
        
        Automatically selects between standard AgentBasedSimulation and
        HeterogeneousABS based on the presence and validity of heterogeneity
        configuration in the protocol.
        
        Parameters
        ----------
        config : SimulationConfig
            Simulation configuration containing protocol definitions
        start_date : datetime
            Start date for the simulation
            
        Returns
        -------
        BaseSimulation
            Either AgentBasedSimulation or HeterogeneousABS instance
            
        Notes
        -----
        Prints console message indicating which engine was selected:
        - "✓ Heterogeneity configuration detected - using HeterogeneousABS engine"
        - "→ Standard configuration - using AgentBasedSimulation engine"
        """
        # Check if configuration supports heterogeneity
        if ABSFactory._supports_heterogeneity(config):
            # Import here to avoid circular imports
            from .heterogeneous_abs import HeterogeneousABS
            
            print("✓ Heterogeneity configuration detected - using HeterogeneousABS engine")
            logger.info("Creating HeterogeneousABS instance with heterogeneity enabled")
            return HeterogeneousABS(config, start_date)
        else:
            print("→ Standard configuration - using AgentBasedSimulation engine")
            logger.info("Creating standard AgentBasedSimulation instance")
            return AgentBasedSimulation(config, start_date)
    
    @staticmethod
    def _supports_heterogeneity(config: SimulationConfig) -> bool:
        """
        Check if configuration has valid heterogeneity section.
        
        Validates:
        1. Presence of heterogeneity section in protocol
        2. heterogeneity.enabled = true
        3. Required fields are present
        4. Trajectory class proportions sum to 1.0
        
        Parameters
        ----------
        config : SimulationConfig
            Configuration to validate
            
        Returns
        -------
        bool
            True if configuration supports heterogeneity, False otherwise
        """
        try:
            # Get protocol configuration
            protocol_dict = ABSFactory._get_protocol_dict(config)
            if not protocol_dict:
                return False
            
            # Check for heterogeneity section
            if 'heterogeneity' not in protocol_dict:
                logger.debug("No heterogeneity section found in protocol")
                return False
            
            heterogeneity = protocol_dict['heterogeneity']
            
            # Check if enabled
            if not heterogeneity.get('enabled', False):
                logger.debug("Heterogeneity section present but not enabled")
                return False
            
            # Validate required fields
            required_fields = ['version', 'trajectory_classes']
            for field in required_fields:
                if field not in heterogeneity:
                    print(f"⚠️  Heterogeneity section missing required field: {field}")
                    logger.warning(f"Heterogeneity validation failed: missing {field}")
                    return False
            
            # Validate trajectory classes
            trajectory_classes = heterogeneity.get('trajectory_classes', {})
            if not trajectory_classes:
                print("⚠️  No trajectory classes defined in heterogeneity section")
                return False
            
            # Check trajectory class proportions sum to 1.0
            total_proportion = sum(
                tc.get('proportion', 0) 
                for tc in trajectory_classes.values()
            )
            if abs(total_proportion - 1.0) > 0.001:
                print(f"⚠️  Trajectory class proportions sum to {total_proportion:.3f}, not 1.0")
                logger.warning(f"Invalid trajectory proportions: {total_proportion}")
                return False
            
            # Validate each trajectory class has required fields
            for class_name, class_config in trajectory_classes.items():
                if 'proportion' not in class_config:
                    print(f"⚠️  Trajectory class '{class_name}' missing proportion")
                    return False
                if 'parameters' not in class_config:
                    print(f"⚠️  Trajectory class '{class_name}' missing parameters")
                    return False
            
            logger.info("Heterogeneity configuration validated successfully")
            return True
            
        except Exception as e:
            print(f"⚠️  Error checking heterogeneity configuration: {e}")
            logger.error(f"Error validating heterogeneity: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _get_protocol_dict(config: SimulationConfig) -> Optional[Dict[str, Any]]:
        """
        Extract protocol dictionary from configuration.
        
        Handles different ways protocols might be stored in the config.
        
        Parameters
        ----------
        config : SimulationConfig
            Configuration object
            
        Returns
        -------
        Optional[Dict[str, Any]]
            Protocol dictionary or None if not found
        """
        # Try different ways to get protocol dict
        if hasattr(config, 'protocol'):
            protocol = config.protocol
            
            # If protocol has to_dict method
            if hasattr(protocol, 'to_dict'):
                return protocol.to_dict()
            
            # If protocol has __dict__
            if hasattr(protocol, '__dict__'):
                return protocol.__dict__
            
            # If protocol is already a dict
            if isinstance(protocol, dict):
                return protocol
        
        # Try parameters directly
        if hasattr(config, 'parameters'):
            params = config.parameters
            if isinstance(params, dict) and 'protocol' in params:
                return params['protocol']
        
        logger.warning("Could not extract protocol dictionary from configuration")
        return None