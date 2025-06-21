"""
Enhanced protocol specification with base configuration import support.

Extends the original ProtocolSpecification to support importing shared
base configurations from Python modules.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import importlib
import copy
from simulation_v2.protocols.protocol_spec import ProtocolSpecification, _validate_disease_transitions, _validate_vision_change_model


class EnhancedProtocolSpecification(ProtocolSpecification):
    """
    Enhanced protocol specification that supports importing base configurations.
    
    Maintains all the strict validation of the base class while adding
    the ability to import and merge configurations from Python modules.
    """
    
    @classmethod
    def from_yaml(cls, filepath: Path) -> 'ProtocolSpecification':
        """
        Load from YAML with support for base configuration imports.
        
        If the YAML contains import_base_config: true, it will:
        1. Import the specified Python module
        2. Load the base configuration
        3. Merge with protocol-specific overrides
        4. Validate the complete configuration
        
        Args:
            filepath: Path to YAML protocol file
            
        Returns:
            ProtocolSpecification instance
            
        Raises:
            FileNotFoundError: If protocol file doesn't exist
            ValueError: If required fields are missing
            ImportError: If base config module cannot be imported
            yaml.YAMLError: If YAML is malformed
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Protocol file not found: {filepath}")
            
        # Load YAML
        with open(filepath) as f:
            data = yaml.safe_load(f)
            
        # Check if we need to import base configuration
        if data.get('import_base_config', False):
            # Import base configuration from Python module
            base_module_name = data.get('base_config_module', 'simulation_v2.protocols.base_configs')
            base_config_name = data.get('base_config_name', 'aflibercept')
            
            try:
                # Import the module
                base_module = importlib.import_module(base_module_name)
                
                # Get the base configuration
                if hasattr(base_module, 'get_base_config'):
                    base_config = base_module.get_base_config(base_config_name)
                else:
                    # Direct attribute access
                    config_attr = f"{base_config_name.upper()}_BASE_CONFIG"
                    if hasattr(base_module, config_attr):
                        base_config = getattr(base_module, config_attr)
                    else:
                        raise ValueError(f"No base configuration found for {base_config_name}")
                
                # Deep copy to avoid modifying the original
                base_config = copy.deepcopy(base_config)
                
                # Merge base config with protocol-specific data
                data = merge_protocol_configs(base_config, data)
                
            except ImportError as e:
                raise ImportError(f"Failed to import base config module {base_module_name}: {e}")
            except Exception as e:
                raise ValueError(f"Failed to load base configuration: {e}")
        
        # Ensure all required fields are present after merge
        _ensure_required_fields(data)
        
        # Continue with standard loading process
        return super().from_yaml_with_data(filepath, data)
    
    @classmethod
    def from_yaml_with_data(cls, filepath: Path, data: Dict[str, Any]) -> 'ProtocolSpecification':
        """
        Create specification from pre-loaded data.
        
        This is a helper method to avoid duplicating the validation logic.
        """
        # Use the parent class's from_yaml but with our pre-processed data
        # We need to temporarily save the data to use the parent's method
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(data, f)
            temp_path = f.name
        
        try:
            # Load using parent class
            result = ProtocolSpecification.from_yaml(Path(temp_path))
            # Update source file to point to original
            result = cls(
                **{k: v if k != 'source_file' else str(filepath.absolute()) 
                   for k, v in result.__dict__.items()}
            )
            return result
        finally:
            os.unlink(temp_path)


def merge_protocol_configs(base_config: Dict[str, Any], protocol_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge base configuration with protocol-specific overrides.
    
    Args:
        base_config: Base configuration from Python module
        protocol_data: Protocol-specific data from YAML
        
    Returns:
        Merged configuration dictionary
    """
    # Start with a copy of the base config
    merged = copy.deepcopy(base_config)
    
    # Copy metadata fields directly from protocol data
    metadata_fields = ['name', 'version', 'created_date', 'author', 'description',
                      'protocol_type', 'min_interval_days', 'max_interval_days',
                      'extension_days', 'shortening_days']
    
    for field in metadata_fields:
        if field in protocol_data:
            merged[field] = protocol_data[field]
    
    # Handle loading phase if present
    if 'loading_phase' in protocol_data:
        merged['loading_phase'] = protocol_data['loading_phase']
    
    # Handle clinical improvements with deep merge
    if 'clinical_improvements' in protocol_data:
        if 'clinical_improvements' not in merged:
            merged['clinical_improvements'] = {}
        
        # Deep merge clinical improvements
        for key, value in protocol_data['clinical_improvements'].items():
            if isinstance(value, dict) and key in merged['clinical_improvements']:
                # Merge nested dictionaries
                merged['clinical_improvements'][key].update(value)
            else:
                # Replace value
                merged['clinical_improvements'][key] = value
    
    # Copy any other protocol-specific fields
    for key, value in protocol_data.items():
        if key not in merged and key not in ['import_base_config', 'base_config_module', 'base_config_name']:
            merged[key] = value
    
    return merged


def _ensure_required_fields(data: Dict[str, Any]) -> None:
    """
    Ensure all required fields are present in the merged configuration.
    
    Args:
        data: Configuration dictionary to validate
        
    Raises:
        ValueError: If required fields are missing
    """
    # Required top-level fields
    required_fields = [
        'name', 'version', 'author', 'description',
        'protocol_type', 'min_interval_days', 'max_interval_days',
        'extension_days', 'shortening_days', 'disease_transitions',
        'vision_change_model', 'treatment_effect_on_transitions',
        'baseline_vision_distribution', 'discontinuation_rules'
    ]
    
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Missing required fields after merge: {missing}")