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

try:
    import pendulum
    HAS_PENDULUM = True
except ImportError:
    HAS_PENDULUM = False


class ResultsFactory:
    """Factory for creating SimulationResults instances."""
    
    # Storage paths
    DEFAULT_RESULTS_DIR = Path("simulation_results")
    
    # Track used memorable names within session to ensure uniqueness
    _used_memorable_names = set()
    
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
        # Generate unique simulation ID with duration encoding
        # Use pendulum for timezone-aware timestamps
        if HAS_PENDULUM:
            now = pendulum.now()
            timestamp = now.strftime('%Y%m%d_%H%M%S')
        else:
            now = datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M%S')
        
        # Encode duration as YY-FF format
        years = int(duration_years)
        fraction = int((duration_years - years) * 100)
        duration_code = f"{years:02d}-{fraction:02d}"
        
        # Generate memorable name using haikunator with session uniqueness
        try:
            from haikunator import Haikunator
            haikunator = Haikunator()
            
            # Generate unique name within session
            max_attempts = 10
            for _ in range(max_attempts):
                memorable_name = haikunator.haikunate(token_length=0, delimiter='-')
                if memorable_name not in cls._used_memorable_names:
                    cls._used_memorable_names.add(memorable_name)
                    break
            else:
                # If we can't find unique name, add a token
                memorable_name = haikunator.haikunate(token_length=2, delimiter='-')
                cls._used_memorable_names.add(memorable_name)
                
        except ImportError:
            # Fallback to hex if haikunator not installed
            memorable_name = uuid.uuid4().hex[:8]
        
        # Combine elements: timestamp + duration + name
        sim_id = f"sim_{timestamp}_{duration_code}_{memorable_name}"
        
        # Create metadata
        metadata = SimulationMetadata(
            sim_id=sim_id,
            timestamp=now,
            protocol_name=protocol_name,
            protocol_version=protocol_version,
            engine_type=engine_type,
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed,
            runtime_seconds=runtime_seconds,
            storage_type="parquet",
            memorable_name=memorable_name
        )
        
        # Determine save path
        save_path = cls.DEFAULT_RESULTS_DIR / sim_id
        
        # Always create Parquet results
        results = ParquetResults.create_from_raw_results(
            raw_results=raw_results,
            metadata=metadata,
            save_path=save_path
        )
        
        return results
    
    @classmethod
    def load_results(cls, results_path: Path) -> SimulationResults:
        """
        Load existing results from disk.
        
        Args:
            results_path: Path to results directory
            
        Returns:
            SimulationResults instance
        """
        # Always load as Parquet
        return ParquetResults.load(results_path)
    
    @classmethod
    def estimate_memory_usage(
        cls,
        n_patients: int,
        duration_years: float
    ) -> Dict[str, Any]:
        """
        Estimate memory usage for a simulation.
        
        Args:
            n_patients: Number of patients
            duration_years: Duration in years
            
        Returns:
            Dictionary with memory estimates
        """
        # Estimate visits per patient (monthly visits)
        visits_per_patient = duration_years * 12
        total_visits = n_patients * visits_per_patient
        
        # Memory estimates (rough)
        bytes_per_patient = 1024  # 1KB per patient record
        bytes_per_visit = 256     # 256 bytes per visit
        
        estimated_memory_mb = (
            (n_patients * bytes_per_patient + 
             total_visits * bytes_per_visit) / (1024 * 1024)
        )
        
        # Disk estimates for Parquet (compressed)
        estimated_disk_mb = estimated_memory_mb * 0.2  # ~20% of memory size
        
        return {
            'patient_years': n_patients * duration_years,
            'estimated_memory_mb': round(estimated_memory_mb, 1),
            'estimated_disk_mb': round(estimated_disk_mb, 1),
            'storage_type': 'parquet'
        }