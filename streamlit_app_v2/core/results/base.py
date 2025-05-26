"""
Abstract base class for simulation results.

This class defines the interface that all results implementations must follow,
whether they store data in memory or on disk.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, Optional, List, Tuple
from dataclasses import dataclass
import pandas as pd
from datetime import datetime
from pathlib import Path


@dataclass
class SimulationMetadata:
    """Metadata about a simulation run."""
    sim_id: str
    protocol_name: str
    protocol_version: str
    engine_type: str
    n_patients: int
    duration_years: float
    seed: int
    timestamp: datetime
    runtime_seconds: float
    storage_type: str  # 'memory' or 'parquet'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'sim_id': self.sim_id,
            'protocol_name': self.protocol_name,
            'protocol_version': self.protocol_version,
            'engine_type': self.engine_type,
            'n_patients': self.n_patients,
            'duration_years': self.duration_years,
            'seed': self.seed,
            'timestamp': self.timestamp.isoformat(),
            'runtime_seconds': self.runtime_seconds,
            'storage_type': self.storage_type
        }


class SimulationResults(ABC):
    """
    Abstract base class for simulation results.
    
    This class provides a uniform interface for accessing simulation data,
    regardless of whether it's stored in memory or on disk.
    """
    
    def __init__(self, metadata: SimulationMetadata):
        """
        Initialize with simulation metadata.
        
        Args:
            metadata: Information about the simulation run
        """
        self.metadata = metadata
        
    @abstractmethod
    def get_patient_count(self) -> int:
        """Get the total number of patients in the simulation."""
        pass
        
    @abstractmethod
    def get_total_injections(self) -> int:
        """Get the total number of injections across all patients."""
        pass
        
    @abstractmethod
    def get_final_vision_stats(self) -> Tuple[float, float]:
        """
        Get final vision statistics.
        
        Returns:
            Tuple of (mean, std) for final vision across all patients
        """
        pass
        
    @abstractmethod
    def get_discontinuation_rate(self) -> float:
        """Get the proportion of patients who discontinued treatment."""
        pass
        
    @abstractmethod
    def iterate_patients(self, batch_size: int = 100) -> Iterator[List[Dict[str, Any]]]:
        """
        Iterate over patients in batches.
        
        Args:
            batch_size: Number of patients per batch
            
        Yields:
            Lists of patient data dictionaries
        """
        pass
        
    @abstractmethod
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific patient.
        
        Args:
            patient_id: The patient identifier
            
        Returns:
            Patient data dictionary or None if not found
        """
        pass
        
    @abstractmethod
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics without loading all data.
        
        Returns:
            Dictionary containing:
            - patient_count
            - total_injections
            - mean_final_vision
            - std_final_vision
            - discontinuation_rate
            - mean_visits_per_patient
            - etc.
        """
        pass
        
    @abstractmethod
    def get_vision_trajectory_df(self, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Get vision trajectories as a DataFrame.
        
        Args:
            sample_size: If specified, randomly sample this many patients
            
        Returns:
            DataFrame with columns: patient_id, time_months, vision
        """
        pass
        
    @abstractmethod
    def get_treatment_intervals_df(self) -> pd.DataFrame:
        """
        Get treatment intervals as a DataFrame.
        
        Returns:
            DataFrame with columns: patient_id, visit_number, interval_days
        """
        pass
        
    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Save results to disk.
        
        Args:
            path: Directory to save results
        """
        pass
        
    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> 'SimulationResults':
        """
        Load results from disk.
        
        Args:
            path: Directory containing saved results
            
        Returns:
            SimulationResults instance
        """
        pass
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        
    def cleanup(self):
        """
        Cleanup resources (override in subclasses if needed).
        
        This is called automatically when using context managers,
        or can be called manually.
        """
        pass
        
    def get_memory_usage_mb(self) -> float:
        """
        Get estimated memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        # Default implementation - override in subclasses
        return 0.0
        
    @property
    def is_large_scale(self) -> bool:
        """Check if this is a large-scale simulation requiring special handling."""
        return self.metadata.n_patients * self.metadata.duration_years > 10_000