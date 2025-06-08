"""
Cost configuration module for V2 economic analysis.

This module handles loading and managing cost configurations from YAML files.
"""

from typing import Dict, Any, Optional, Union
import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CostConfig:
    """Holds cost configuration data for economic analysis."""
    
    metadata: Dict[str, Any]
    drug_costs: Dict[str, float]
    visit_components: Dict[str, float]
    visit_types: Dict[str, Dict[str, Any]]
    special_events: Dict[str, float]
    
    @classmethod
    def from_yaml(cls, filepath: Union[str, Path]) -> 'CostConfig':
        """
        Load cost configuration from YAML file.
        
        Args:
            filepath: Path to the YAML configuration file
            
        Returns:
            CostConfig instance with loaded data
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Cost configuration file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            
        return cls(
            metadata=data.get('metadata', {}),
            drug_costs=data.get('drug_costs', {}),
            visit_components=data.get('visit_components', {}),
            visit_types=data.get('visit_types', {}),
            special_events=data.get('special_events', {})
        )
    
    def get_drug_cost(self, drug_name: str) -> float:
        """
        Get cost for a specific drug.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            Cost of the drug, or 0.0 if not found
        """
        return self.drug_costs.get(drug_name, 0.0)
    
    def get_visit_cost(self, visit_type: str) -> float:
        """
        Calculate total cost for a visit type.
        
        This method handles both component-based costs and explicit overrides.
        
        Args:
            visit_type: Type of visit
            
        Returns:
            Total cost of the visit, or 0.0 if visit type not found
        """
        if visit_type not in self.visit_types:
            return 0.0
            
        visit_def = self.visit_types[visit_type]
        
        # Check for explicit cost override
        if visit_def.get('total_override') is not None:
            return visit_def['total_override']
            
        # Calculate sum of component costs
        total = 0.0
        for component in visit_def.get('components', []):
            total += self.visit_components.get(component, 0.0)
            
        return total
    
    def get_component_cost(self, component: str) -> float:
        """
        Get cost for a specific visit component.
        
        Args:
            component: Name of the component
            
        Returns:
            Cost of the component, or 0.0 if not found
        """
        return self.visit_components.get(component, 0.0)
    
    def get_special_event_cost(self, event_type: str) -> float:
        """
        Get cost for a special event.
        
        Args:
            event_type: Type of special event
            
        Returns:
            Cost of the event, or 0.0 if not found
        """
        return self.special_events.get(event_type, 0.0)