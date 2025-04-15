"""
Configuration model for archetype-based simulations.

This module defines the configuration structure for simulations that use patient archetypes.
The configuration includes archetype parameters, cluster mappings, and simulation settings.
"""

from pydantic import BaseModel
from typing import Dict, Any

class ArchetypeSimulationConfig(BaseModel):
    """Configuration for archetype-driven simulations.
    
    This configuration defines the parameters needed to run simulations using
    patient archetypes derived from cluster analysis of real-world data.

    Parameters
    ----------
    archetype_params : Dict[str, Any]
        Dictionary containing parameters for each archetype including:
        - baseline_va: Initial visual acuity (ETDRS letters)
        - baseline_interval: Typical treatment interval (days)
        - response_curve: Parameters for treatment response model
    cluster_mapping : Dict[int, str]
        Mapping of cluster IDs to descriptive archetype names
    max_sim_days : int, optional
        Maximum simulation duration in days (default: 1825 [5 years])
    validation_enabled : bool, optional
        Whether to enable parameter validation (default: True)

    Attributes
    ----------
    archetype_params : Dict[str, Any]
        Archetype-specific parameters
    cluster_mapping : Dict[int, str]
        Cluster ID to archetype name mapping
    max_sim_days : int
        Maximum simulation duration
    validation_enabled : bool
        Parameter validation flag

    Examples
    --------
    >>> config = ArchetypeSimulationConfig(
    ...     archetype_params={
    ...         "cluster_1": {"baseline_va": 65, "baseline_interval": 56},
    ...         "cluster_2": {"baseline_va": 55, "baseline_interval": 84}
    ...     },
    ...     cluster_mapping={0: "cluster_1", 1: "cluster_2"},
    ...     max_sim_days=365*3
    ... )
    """
    archetype_params: Dict[str, Any]
    cluster_mapping: Dict[int, str]
    max_sim_days: int = 365*5
    validation_enabled: bool = True
    
    class Config:
        """Pydantic model configuration.
        
        Attributes
        ----------
        arbitrary_types_allowed : bool
            Allow arbitrary types in model fields
        extra : str
            How to handle extra fields ('forbid' raises error)
        """
        arbitrary_types_allowed = True
        extra = "forbid"
