"""
Configuration management utilities for the APE Streamlit application.

This module provides functions for loading, validating, and managing
application configuration settings.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "app": {
        "name": "APE: AMD Protocol Explorer",
        "version": "1.0.0",
        "debug_mode": False,
        "log_level": "INFO",
        "cache_dir": "output/cache",
        "reports_dir": "output/reports",
        "visualizations_dir": "output/visualizations"
    },
    "simulation": {
        "use_fixed_implementation": True,
        "default_simulation_type": "ABS",
        "max_population_size": 10000,
        "default_duration_years": 5,
        "default_r_dpi": 120
    },
    "visualization": {
        "use_r_if_available": True,
        "matplotlib_dpi": 80,
        "r_dpi": 120,
        "cache_ttl_days": 7,
        "enable_progressive_enhancement": True
    },
    "features": {
        "enable_staggered_simulation": True,
        "enable_reports": True,
        "enable_patient_explorer": True,
        "enable_r_visualization": True
    }
}


class Config:
    """Configuration manager for the APE application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Parameters
        ----------
        config_path : str, optional
            Path to configuration file, by default None
        """
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self.loaded = False
        
        # Try to load configuration
        if config_path:
            self.load(config_path)
    
    def load(self, config_path: str) -> bool:
        """Load configuration from file.
        
        Parameters
        ----------
        config_path : str
            Path to configuration file
        
        Returns
        -------
        bool
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found: {config_path}")
            return False
        
        try:
            # Determine file type based on extension
            _, ext = os.path.splitext(config_path)
            
            if ext.lower() in ['.yaml', '.yml']:
                # Load YAML configuration
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
            elif ext.lower() == '.json':
                # Load JSON configuration
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
            else:
                logger.error(f"Unsupported configuration file format: {ext}")
                return False
            
            # Update configuration
            self._update_config(loaded_config)
            self.config_path = config_path
            self.loaded = True
            
            logger.info(f"Loaded configuration from {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def _update_config(self, loaded_config: Dict[str, Any]) -> None:
        """Update configuration with loaded values.
        
        Parameters
        ----------
        loaded_config : Dict[str, Any]
            Loaded configuration values
        """
        # Update each section individually to preserve defaults for missing values
        for section in DEFAULT_CONFIG:
            if section in loaded_config and isinstance(loaded_config[section], dict):
                if section not in self.config:
                    self.config[section] = {}
                
                for key, value in loaded_config[section].items():
                    self.config[section][key] = value
            elif section in loaded_config:
                self.config[section] = loaded_config[section]
    
    def save(self, config_path: Optional[str] = None) -> bool:
        """Save configuration to file.
        
        Parameters
        ----------
        config_path : str, optional
            Path to save configuration to, by default None (use loaded path)
        
        Returns
        -------
        bool
            True if saved successfully, False otherwise
        """
        # Use provided path or loaded path
        save_path = config_path or self.config_path
        
        if not save_path:
            logger.error("No configuration path specified")
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Determine file type based on extension
            _, ext = os.path.splitext(save_path)
            
            if ext.lower() in ['.yaml', '.yml']:
                # Save as YAML
                with open(save_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif ext.lower() == '.json':
                # Save as JSON
                with open(save_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                logger.error(f"Unsupported configuration file format: {ext}")
                return False
            
            logger.info(f"Saved configuration to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Parameters
        ----------
        section : str
            Configuration section
        key : str
            Configuration key
        default : Any, optional
            Default value if not found, by default None
        
        Returns
        -------
        Any
            Configuration value
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Parameters
        ----------
        section : str
            Configuration section
        key : str
            Configuration key
        value : Any
            Configuration value
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section.
        
        Parameters
        ----------
        section : str
            Configuration section
        
        Returns
        -------
        Dict[str, Any]
            Section configuration
        """
        return self.config.get(section, {})
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled.
        
        Parameters
        ----------
        feature : str
            Feature name
        
        Returns
        -------
        bool
            True if feature is enabled, False otherwise
        """
        return self.get("features", feature, False)
    
    def get_app_name(self) -> str:
        """Get the application name.
        
        Returns
        -------
        str
            Application name
        """
        return self.get("app", "name", DEFAULT_CONFIG["app"]["name"])
    
    def get_app_version(self) -> str:
        """Get the application version.
        
        Returns
        -------
        str
            Application version
        """
        return self.get("app", "version", DEFAULT_CONFIG["app"]["version"])
    
    def get_cache_dir(self) -> str:
        """Get the cache directory.
        
        Returns
        -------
        str
            Cache directory
        """
        cache_dir = self.get("app", "cache_dir", DEFAULT_CONFIG["app"]["cache_dir"])
        
        # Create directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        return cache_dir
    
    def get_reports_dir(self) -> str:
        """Get the reports directory.
        
        Returns
        -------
        str
            Reports directory
        """
        reports_dir = self.get("app", "reports_dir", DEFAULT_CONFIG["app"]["reports_dir"])
        
        # Create directory if it doesn't exist
        os.makedirs(reports_dir, exist_ok=True)
        
        return reports_dir
    
    def get_visualizations_dir(self) -> str:
        """Get the visualizations directory.
        
        Returns
        -------
        str
            Visualizations directory
        """
        viz_dir = self.get("app", "visualizations_dir", DEFAULT_CONFIG["app"]["visualizations_dir"])
        
        # Create directory if it doesn't exist
        os.makedirs(viz_dir, exist_ok=True)
        
        return viz_dir
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled.
        
        Returns
        -------
        bool
            True if debug mode is enabled, False otherwise
        """
        return self.get("app", "debug_mode", DEFAULT_CONFIG["app"]["debug_mode"])
    
    def use_fixed_implementation(self) -> bool:
        """Check if fixed implementation should be used.
        
        Returns
        -------
        bool
            True if fixed implementation should be used, False otherwise
        """
        return self.get("simulation", "use_fixed_implementation", DEFAULT_CONFIG["simulation"]["use_fixed_implementation"])
    
    def get_log_level(self) -> str:
        """Get the log level.
        
        Returns
        -------
        str
            Log level
        """
        return self.get("app", "log_level", DEFAULT_CONFIG["app"]["log_level"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns
        -------
        Dict[str, Any]
            Configuration dictionary
        """
        return self.config.copy()


# Global instance for easy access
_config_instance = None

def get_config(config_path: Optional[str] = None, reset: bool = False) -> Config:
    """Get the global configuration instance.
    
    Parameters
    ----------
    config_path : str, optional
        Path to configuration file, by default None
    reset : bool, optional
        Whether to reset the configuration, by default False
    
    Returns
    -------
    Config
        Global configuration instance
    """
    global _config_instance
    
    if _config_instance is None or reset:
        _config_instance = Config(config_path)
    elif config_path and config_path != _config_instance.config_path:
        _config_instance.load(config_path)
    
    return _config_instance


def find_config_file() -> Optional[str]:
    """Find configuration file in standard locations.
    
    Returns
    -------
    Optional[str]
        Path to configuration file if found, None otherwise
    """
    # List of standard locations to check
    standard_locations = [
        # Current directory
        "ape_config.yaml",
        "ape_config.yml",
        "ape_config.json",
        
        # Config directory
        "config/ape_config.yaml",
        "config/ape_config.yml",
        "config/ape_config.json",
        
        # User home directory
        os.path.expanduser("~/.ape/config.yaml"),
        os.path.expanduser("~/.ape/config.yml"),
        os.path.expanduser("~/.ape/config.json"),
        
        # Environment variable
        os.environ.get("APE_CONFIG_PATH", "")
    ]
    
    # Check each location
    for location in standard_locations:
        if location and os.path.exists(location):
            return location
    
    return None


def initialize_config() -> Config:
    """Initialize configuration from standard locations.
    
    Returns
    -------
    Config
        Initialized configuration
    """
    # Find configuration file
    config_path = find_config_file()
    
    # Initialize configuration
    config = get_config(config_path, reset=True)
    
    # Set log level
    log_level = config.get_log_level()
    logging.getLogger().setLevel(log_level)
    
    return config