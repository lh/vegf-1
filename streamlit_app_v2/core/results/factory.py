"""
Factory for creating appropriate SimulationResults based on size.

Automatically selects between in-memory and Parquet storage based on
simulation size and available memory.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict

from .base import SimulationResults, SimulationMetadata
from .memory import InMemoryResults
from .parquet import ParquetResults


class ResultsFactory:
    """Factory for creating SimulationResults instances."""
    
    # Thresholds for automatic tier selection
    MEMORY_THRESHOLD_PATIENT_YEARS = 10_000  # Switch to Parquet above this
    MEMORY_WARNING_PATIENT_YEARS = 5_000     # Warn about memory usage
    
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
        runtime_seconds: float,
        force_parquet: bool = False
    ) -> SimulationResults:
        """
        Create appropriate SimulationResults instance based on size.
        
        Args:
            raw_results: Raw results from simulation engine
            protocol_name: Name of the protocol used
            protocol_version: Version of the protocol
            engine_type: 'abs' or 'des'
            n_patients: Number of patients simulated
            duration_years: Duration of simulation in years
            seed: Random seed used
            runtime_seconds: Time taken to run simulation
            force_parquet: If True, always use Parquet storage
            
        Returns:
            SimulationResults instance (either InMemory or Parquet)
        """
        # Generate unique simulation ID
        sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Calculate simulation size
        patient_years = n_patients * duration_years
        
        # Determine storage type
        use_parquet = force_parquet or (patient_years > cls.MEMORY_THRESHOLD_PATIENT_YEARS)
        storage_type = 'parquet' if use_parquet else 'memory'
        
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
            storage_type=storage_type
        )
        
        # Print info about storage choice
        if use_parquet:
            print(f"📁 Using Parquet storage for {n_patients:,} patients × {duration_years} years")
            
            # Create Parquet results
            save_path = cls.DEFAULT_RESULTS_DIR / sim_id
            return ParquetResults.create_from_raw_results(
                raw_results,
                metadata,
                save_path
            )
        else:
            print(f"💾 Using in-memory storage for {n_patients:,} patients × {duration_years} years")
            
            # Warn if approaching threshold
            if patient_years > cls.MEMORY_WARNING_PATIENT_YEARS:
                print(f"⚠️  Warning: Simulation size ({patient_years:,} patient-years) "
                      f"approaching memory limit ({cls.MEMORY_THRESHOLD_PATIENT_YEARS:,})")
                
            return InMemoryResults(metadata, raw_results)
            
    @classmethod
    def load_results(cls, path: Path) -> SimulationResults:
        """
        Load results from disk.
        
        Automatically detects the storage type and loads appropriately.
        
        Args:
            path: Path to saved results directory
            
        Returns:
            SimulationResults instance
        """
        path = Path(path)
        
        # Check metadata to determine type
        metadata_path = path / 'metadata.json'
        if not metadata_path.exists():
            raise FileNotFoundError(f"No metadata found at {metadata_path}")
            
        import json
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        storage_type = metadata.get('storage_type', 'memory')
        
        if storage_type == 'parquet':
            return ParquetResults.load(path)
        else:
            return InMemoryResults.load(path)
            
    @classmethod
    def convert_to_parquet(
        cls,
        results: SimulationResults,
        output_path: Optional[Path] = None
    ) -> ParquetResults:
        """
        Convert any results to Parquet format.
        
        Args:
            results: Results to convert
            output_path: Where to save (defaults to sim_id directory)
            
        Returns:
            ParquetResults instance
        """
        if isinstance(results, ParquetResults):
            return results
            
        if output_path is None:
            output_path = cls.DEFAULT_RESULTS_DIR / results.metadata.sim_id
            
        # For InMemoryResults, we have direct access to raw results
        if isinstance(results, InMemoryResults):
            # Update metadata
            new_metadata = SimulationMetadata(
                sim_id=results.metadata.sim_id,
                protocol_name=results.metadata.protocol_name,
                protocol_version=results.metadata.protocol_version,
                engine_type=results.metadata.engine_type,
                n_patients=results.metadata.n_patients,
                duration_years=results.metadata.duration_years,
                seed=results.metadata.seed,
                timestamp=results.metadata.timestamp,
                runtime_seconds=results.metadata.runtime_seconds,
                storage_type='parquet'
            )
            
            return ParquetResults.create_from_raw_results(
                results.raw_results,
                new_metadata,
                output_path
            )
        else:
            raise ValueError(f"Cannot convert {type(results)} to Parquet")
            
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
            'recommended_storage': 'parquet' if patient_years > cls.MEMORY_THRESHOLD_PATIENT_YEARS else 'memory',
            'warning': total_mb > 300
        }