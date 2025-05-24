"""
Simulation results data model for the APE Streamlit application.

This module provides structured data classes for simulation results,
ensuring consistent access patterns throughout the application.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
import datetime


@dataclass
class DiscontinuationCounts:
    """Counts of discontinuations by type."""
    
    planned: int = 0
    administrative: int = 0
    premature: int = 0
    time_based: int = 0
    
    @property
    def total(self) -> int:
        """Get total count of discontinuations."""
        return self.planned + self.administrative + self.premature + self.time_based
    
    def as_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {
            "Planned": self.planned,
            "Administrative": self.administrative,
            "Premature": self.premature,
            "Time-based": self.time_based
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'DiscontinuationCounts':
        """Create DiscontinuationCounts from dictionary."""
        return cls(
            planned=data.get("Planned", 0),
            administrative=data.get("Administrative", 0),
            premature=data.get("Premature", 0),
            time_based=data.get("Time-based", 0)
        )


@dataclass
class RecurrenceData:
    """Data about disease recurrences."""
    
    total: int = 0
    unique_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    
    @property
    def recurrence_rate(self) -> float:
        """Calculate recurrence rate (if total_discontinuations is provided)."""
        if hasattr(self, "_total_discontinuations") and self._total_discontinuations > 0:
            return self.unique_count / self._total_discontinuations * 100
        return 0.0
    
    def set_total_discontinuations(self, total: int) -> None:
        """Set total discontinuations for rate calculation."""
        self._total_discontinuations = total


@dataclass
class VisualAcuityDatapoint:
    """Single datapoint of visual acuity data."""
    
    time: Union[int, float]  # Time in weeks or other unit
    visual_acuity: float
    sample_size: Optional[int] = None


@dataclass
class SimulationResults:
    """Structured container for simulation results."""
    
    simulation_type: str
    population_size: int
    duration_years: float
    
    # Core metrics
    total_injections: int = 0
    mean_injections: float = 0.0
    total_discontinuations: int = 0
    
    # Detailed data
    discontinuation_counts: Optional[DiscontinuationCounts] = None
    recurrences: Optional[RecurrenceData] = None
    mean_va_data: List[VisualAcuityDatapoint] = field(default_factory=list)
    
    # Parameters used
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Raw data and statistics
    raw_discontinuation_stats: Dict[str, Any] = field(default_factory=dict)
    patient_histories: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    runtime_seconds: Optional[float] = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    is_sample: bool = False
    failed: bool = False
    error: Optional[str] = None
    
    @property
    def discontinuation_rate(self) -> float:
        """Calculate discontinuation rate as percentage."""
        if self.population_size > 0:
            return self.total_discontinuations / self.population_size * 100
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        result = {
            "simulation_type": self.simulation_type,
            "population_size": self.population_size,
            "duration_years": self.duration_years,
            "total_injections": self.total_injections,
            "mean_injections": self.mean_injections,
            "total_discontinuations": self.total_discontinuations,
            "parameters": self.parameters,
            "runtime_seconds": self.runtime_seconds,
            "timestamp": self.timestamp.isoformat(),
            "is_sample": self.is_sample,
            "failed": self.failed
        }
        
        if self.discontinuation_counts:
            result["discontinuation_counts"] = self.discontinuation_counts.as_dict()
        
        if self.recurrences:
            result["recurrences"] = {
                "total": self.recurrences.total,
                "unique_count": self.recurrences.unique_count,
                "by_type": self.recurrences.by_type
            }
        
        if self.mean_va_data:
            result["mean_va_data"] = [
                {"time": point.time, "visual_acuity": point.visual_acuity}
                for point in self.mean_va_data
            ]
        
        if self.raw_discontinuation_stats:
            result["raw_discontinuation_stats"] = self.raw_discontinuation_stats
        
        if self.error:
            result["error"] = self.error
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationResults':
        """Create SimulationResults from dictionary."""
        # Extract the required fields
        simulation_type = data.get("simulation_type", "Unknown")
        population_size = data.get("population_size", 0)
        duration_years = data.get("duration_years", 0)
        
        # Create the instance
        result = cls(
            simulation_type=simulation_type,
            population_size=population_size,
            duration_years=duration_years,
            total_injections=data.get("total_injections", 0),
            mean_injections=data.get("mean_injections", 0.0),
            total_discontinuations=data.get("total_discontinuations", 0),
            parameters=data.get("parameters", {}),
            runtime_seconds=data.get("runtime_seconds"),
            is_sample=data.get("is_sample", False),
            failed=data.get("failed", False),
            error=data.get("error")
        )
        
        # Parse timestamp if available
        if "timestamp" in data:
            try:
                result.timestamp = datetime.datetime.fromisoformat(data["timestamp"])
            except ValueError:
                # If parsing fails, keep the default (now)
                pass
        
        # Parse discontinuation counts if available
        if "discontinuation_counts" in data:
            result.discontinuation_counts = DiscontinuationCounts.from_dict(data["discontinuation_counts"])
        
        # Parse recurrences if available
        if "recurrences" in data:
            recurrences_data = data["recurrences"]
            result.recurrences = RecurrenceData(
                total=recurrences_data.get("total", 0),
                unique_count=recurrences_data.get("unique_count", 0),
                by_type=recurrences_data.get("by_type", {})
            )
            # Set total discontinuations for rate calculation
            result.recurrences.set_total_discontinuations(result.total_discontinuations)
        
        # Parse mean VA data if available
        if "mean_va_data" in data:
            result.mean_va_data = [
                VisualAcuityDatapoint(
                    time=point.get("time", 0),
                    visual_acuity=point.get("visual_acuity", 0),
                    sample_size=point.get("sample_size")
                )
                for point in data["mean_va_data"]
            ]
        
        # Add raw discontinuation stats if available
        if "raw_discontinuation_stats" in data:
            result.raw_discontinuation_stats = data["raw_discontinuation_stats"]
        
        return result