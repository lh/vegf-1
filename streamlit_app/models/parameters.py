"""
Parameter definitions and validation for the APE Streamlit application.

This module provides structured data classes for simulation parameters,
with type hints and validation to ensure consistency.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import datetime


@dataclass
class DiscontinuationParameters:
    """Parameters for treatment discontinuation modeling."""
    
    planned_discontinue_prob: float = 0.2
    admin_discontinue_prob: float = 0.05
    premature_discontinue_prob: float = 2.0
    consecutive_stable_visits: int = 3
    monitoring_schedule: List[int] = field(default_factory=lambda: [12, 24, 36])
    no_monitoring_for_admin: bool = True
    recurrence_risk_multiplier: float = 1.0
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        if not 0 <= self.planned_discontinue_prob <= 1:
            raise ValueError("planned_discontinue_prob must be between 0 and 1")
        
        if not 0 <= self.admin_discontinue_prob <= 1:
            raise ValueError("admin_discontinue_prob must be between 0 and 1")
        
        if self.premature_discontinue_prob < 0:
            raise ValueError("premature_discontinue_prob must be non-negative")
        
        if self.consecutive_stable_visits < 1:
            raise ValueError("consecutive_stable_visits must be at least 1")
        
        if not self.monitoring_schedule:
            self.monitoring_schedule = [12, 24, 36]
        
        if self.recurrence_risk_multiplier <= 0:
            raise ValueError("recurrence_risk_multiplier must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "planned_discontinue_prob": self.planned_discontinue_prob,
            "admin_discontinue_prob": self.admin_discontinue_prob,
            "premature_discontinue_prob": self.premature_discontinue_prob,
            "consecutive_stable_visits": self.consecutive_stable_visits,
            "monitoring_schedule": self.monitoring_schedule,
            "no_monitoring_for_admin": self.no_monitoring_for_admin,
            "recurrence_risk_multiplier": self.recurrence_risk_multiplier
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiscontinuationParameters':
        """Create DiscontinuationParameters from dictionary."""
        return cls(
            planned_discontinue_prob=data.get("planned_discontinue_prob", 0.2),
            admin_discontinue_prob=data.get("admin_discontinue_prob", 0.05),
            premature_discontinue_prob=data.get("premature_discontinue_prob", 2.0),
            consecutive_stable_visits=data.get("consecutive_stable_visits", 3),
            monitoring_schedule=data.get("monitoring_schedule", [12, 24, 36]),
            no_monitoring_for_admin=data.get("no_monitoring_for_admin", True),
            recurrence_risk_multiplier=data.get("recurrence_risk_multiplier", 1.0)
        )


@dataclass
class StaggeredEnrollmentParameters:
    """Parameters for staggered patient enrollment."""
    
    arrival_rate: float = 10.0
    enable_staggered_enrollment: bool = True
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.arrival_rate <= 0:
            raise ValueError("arrival_rate must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "arrival_rate": self.arrival_rate,
            "enable_staggered_enrollment": self.enable_staggered_enrollment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StaggeredEnrollmentParameters':
        """Create StaggeredEnrollmentParameters from dictionary."""
        return cls(
            arrival_rate=data.get("arrival_rate", 10.0),
            enable_staggered_enrollment=data.get("enable_staggered_enrollment", True)
        )


@dataclass
class SimulationParameters:
    """Parameters for a simulation run."""
    
    simulation_type: str = "ABS"
    duration_years: float = 5.0
    population_size: int = 1000
    enable_clinician_variation: bool = True
    discontinuation_params: DiscontinuationParameters = field(default_factory=DiscontinuationParameters)
    staggered_params: Optional[StaggeredEnrollmentParameters] = None
    advanced_params: Dict[str, Any] = field(default_factory=dict)
    random_seed: Optional[int] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.simulation_type not in ["ABS", "DES"]:
            raise ValueError("simulation_type must be either 'ABS' or 'DES'")
        
        if self.duration_years <= 0:
            raise ValueError("duration_years must be positive")
        
        if self.population_size <= 0:
            raise ValueError("population_size must be positive")
        
        # Create default discontinuation parameters if None
        if self.discontinuation_params is None:
            self.discontinuation_params = DiscontinuationParameters()
        
        # If staggered_params is provided, ensure simulation_type is ABS
        if self.staggered_params is not None and self.simulation_type != "ABS":
            raise ValueError("Staggered enrollment is only available for ABS simulations")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "simulation_type": self.simulation_type,
            "duration_years": self.duration_years,
            "population_size": self.population_size,
            "enable_clinician_variation": self.enable_clinician_variation,
            **self.discontinuation_params.to_dict(),
            "random_seed": self.random_seed,
            "created_at": self.created_at.isoformat(),
            **self.advanced_params
        }
        
        # Add staggered parameters if available
        if self.staggered_params is not None:
            result.update(self.staggered_params.to_dict())
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationParameters':
        """Create SimulationParameters from dictionary."""
        # Extract basic parameters
        simulation_type = data.get("simulation_type", "ABS")
        duration_years = data.get("duration_years", 5.0)
        population_size = data.get("population_size", 1000)
        enable_clinician_variation = data.get("enable_clinician_variation", True)
        random_seed = data.get("random_seed")
        
        # Extract discontinuation parameters
        discontinuation_params = DiscontinuationParameters(
            planned_discontinue_prob=data.get("planned_discontinue_prob", 0.2),
            admin_discontinue_prob=data.get("admin_discontinue_prob", 0.05),
            premature_discontinue_prob=data.get("premature_discontinue_prob", 2.0),
            consecutive_stable_visits=data.get("consecutive_stable_visits", 3),
            monitoring_schedule=data.get("monitoring_schedule", [12, 24, 36]),
            no_monitoring_for_admin=data.get("no_monitoring_for_admin", True),
            recurrence_risk_multiplier=data.get("recurrence_risk_multiplier", 1.0)
        )
        
        # Extract staggered parameters if available
        staggered_params = None
        if "arrival_rate" in data or "enable_staggered_enrollment" in data:
            staggered_params = StaggeredEnrollmentParameters(
                arrival_rate=data.get("arrival_rate", 10.0),
                enable_staggered_enrollment=data.get("enable_staggered_enrollment", True)
            )
        
        # Extract advanced parameters (any keys not explicitly handled)
        known_keys = {
            "simulation_type", "duration_years", "population_size", "enable_clinician_variation",
            "planned_discontinue_prob", "admin_discontinue_prob", "premature_discontinue_prob",
            "consecutive_stable_visits", "monitoring_schedule", "no_monitoring_for_admin",
            "recurrence_risk_multiplier", "random_seed", "created_at", "arrival_rate",
            "enable_staggered_enrollment"
        }
        advanced_params = {k: v for k, v in data.items() if k not in known_keys}
        
        # Parse created_at if available
        created_at = datetime.datetime.now()
        if "created_at" in data:
            try:
                created_at = datetime.datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            simulation_type=simulation_type,
            duration_years=duration_years,
            population_size=population_size,
            enable_clinician_variation=enable_clinician_variation,
            discontinuation_params=discontinuation_params,
            staggered_params=staggered_params,
            advanced_params=advanced_params,
            random_seed=random_seed,
            created_at=created_at
        )
    
    def create_staggered_params(self, arrival_rate: float) -> None:
        """Create staggered enrollment parameters."""
        if self.simulation_type != "ABS":
            raise ValueError("Staggered enrollment is only available for ABS simulations")
        
        self.staggered_params = StaggeredEnrollmentParameters(
            arrival_rate=arrival_rate,
            enable_staggered_enrollment=True
        )
    
    def disable_staggered_enrollment(self) -> None:
        """Disable staggered enrollment."""
        self.staggered_params = None
    
    @property
    def is_staggered(self) -> bool:
        """Check if staggered enrollment is enabled."""
        return self.staggered_params is not None and self.staggered_params.enable_staggered_enrollment


def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate simulation parameters.
    
    Parameters
    ----------
    params : Dict[str, Any]
        Parameters to validate
    
    Returns
    -------
    Dict[str, Any]
        Validated parameters
    
    Raises
    ------
    ValueError
        If parameters are invalid
    """
    try:
        # Convert to SimulationParameters object for validation
        sim_params = SimulationParameters.from_dict(params)
        
        # Convert back to dictionary
        return sim_params.to_dict()
    except ValueError as e:
        raise ValueError(f"Parameter validation failed: {str(e)}")


def get_default_parameters(simulation_type: str = "ABS") -> Dict[str, Any]:
    """Get default parameters for a simulation.
    
    Parameters
    ----------
    simulation_type : str, optional
        Simulation type, by default "ABS"
    
    Returns
    -------
    Dict[str, Any]
        Default parameters
    """
    params = SimulationParameters(simulation_type=simulation_type)
    return params.to_dict()