"""
Factory for creating SimulationResults instances.

All simulations are stored in Parquet format for efficient disk-based storage
and easy persistence.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict

from .base import SimulationResults, SimulationMetadata
from .parquet import ParquetResults


class ResultsFactory:
    """Factory for creating SimulationResults instances."""
    
    # Storage paths
    DEFAULT_RESULTS_DIR = Path("simulation_results")
    
    @classmethod
    def create_results(
        cls,
        raw_results: Any,
        protocol_name: str,
        protocol_version: str,
        engine_type: str,
        n_patients: int,
        duration_years: float,
        seed: int,
        runtime_seconds: float
    ) -> SimulationResults:
        """
        Create SimulationResults instance with Parquet storage.
        
        Args:
            raw_results: Raw results from simulation engine
            protocol_name: Name of the protocol used
            protocol_version: Version of the protocol
            engine_type: 'abs' or 'des'
            n_patients: Number of patients simulated
            duration_years: Duration of simulation in years
            seed: Random seed used
            runtime_seconds: Time taken to run simulation
            
        Returns:
            ParquetResults instance
        """
        # Generate unique simulation ID
        sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create metadata
        metadata = SimulationMetadata(
            sim_id=sim_id,
            protocol_name=protocol_name,
            protocol_version=protocol_version,
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            timestamp=datetime.now(),
            runtime_seconds=runtime_seconds,
            storage_type='parquet'  # Always Parquet
        )
        
        print(f"📁 Saving simulation to Parquet: {n_patients:,} patients × {duration_years} years")
        
        # Create Parquet results with progress
        save_path = cls.DEFAULT_RESULTS_DIR / sim_id
        
        def progress_callback(pct: float, msg: str):
            print(f"  [{pct:3.0f}%] {msg}")
            
        return ParquetResults.create_from_raw_results(
            raw_results,
            metadata,
            save_path,
            progress_callback
        )
            
    @classmethod
    def load_results(cls, path: Path) -> SimulationResults:
        """
        Load results from disk.
        
        Args:
            path: Path to saved results directory
            
        Returns:
            ParquetResults instance
        """
        path = Path(path)
        return ParquetResults.load(path)
            
            
    @classmethod
    def estimate_memory_usage(cls, n_patients: int, duration_years: float) -> Dict[str, float]:
        """
        Estimate memory usage for a simulation.
        
        Args:
            n_patients: Number of patients
            duration_years: Duration in years
            
        Returns:
            Dictionary with memory estimates in MB
        """
        # Assumptions:
        # - ~8-10 visits per patient per year
        # - ~200 bytes per visit
        # - ~1KB overhead per patient
        
        visits_per_patient = duration_years * 9  # Average
        bytes_per_patient = 1024 + (visits_per_patient * 200)
        total_bytes = n_patients * bytes_per_patient
        
        # Add overhead for data structures
        overhead_factor = 1.5
        total_mb = (total_bytes * overhead_factor) / (1024 * 1024)
        
        patient_years = n_patients * duration_years
        return {
            'estimated_mb': total_mb,
            'patient_years': patient_years,
            'recommended_storage': 'parquet',  # Always recommend Parquet
            'warning': total_mb > 300
        }