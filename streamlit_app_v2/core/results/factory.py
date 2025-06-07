"""
Factory for creating SimulationResults instances.

All simulations are stored in Parquet format for consistency,
reliability, and simplicity.
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
        runtime_seconds: float,
        force_parquet: bool = False  # DEPRECATED - kept for backward compatibility
    ) -> SimulationResults:
        """
        Create SimulationResults instance using Parquet storage.
        
        Note: As of the Parquet-only refactor, all simulations are stored
        in Parquet format regardless of size for consistency and simplicity.
        
        Args:
            raw_results: Raw results from simulation engine
            protocol_name: Name of the protocol used
            protocol_version: Version of the protocol
            engine_type: 'abs' or 'des'
            n_patients: Number of patients simulated
            duration_years: Duration of simulation in years
            seed: Random seed used
            runtime_seconds: Time taken to run simulation
            force_parquet: DEPRECATED - all simulations now use Parquet
            
        Returns:
            ParquetResults instance
        """
        # Generate unique simulation ID
        sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Always use Parquet storage for consistency
        storage_type = 'parquet'
        
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
        
        # Always create Parquet results
        print(f"📁 Saving simulation ({n_patients:,} patients × {duration_years} years) to disk...")
        
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
        
        All results are expected to be in Parquet format.
        
        Args:
            path: Path to saved results directory
            
        Returns:
            ParquetResults instance
        """
        path = Path(path)
        
        # Check metadata exists
        metadata_path = path / 'metadata.json'
        if not metadata_path.exists():
            raise FileNotFoundError(f"No metadata found at {metadata_path}")
            
        # Load as ParquetResults
        return ParquetResults.load(path)
            
    @classmethod
    def convert_to_parquet(
        cls,
        results: SimulationResults,
        output_path: Optional[Path] = None
    ) -> ParquetResults:
        """
        Convert any results to Parquet format.
        
        Note: As of the Parquet-only refactor, all results should already
        be in Parquet format. This method is kept for compatibility.
        
        Args:
            results: Results to convert
            output_path: Where to save (defaults to sim_id directory)
            
        Returns:
            ParquetResults instance
        """
        if isinstance(results, ParquetResults):
            return results
        else:
            raise ValueError(f"Cannot convert {type(results)} to Parquet - all results should already be ParquetResults")
            
    @classmethod
    def save_imported_results(cls, results: SimulationResults) -> str:
        """
        Save imported simulation results.
        
        Note: As of the Parquet-only refactor, all results should already
        be ParquetResults which are auto-saved during creation.
        
        Args:
            results: Imported SimulationResults instance
            
        Returns:
            New simulation ID
        """
        # The imported results should already have a new sim_id
        sim_id = results.metadata.sim_id
        
        if isinstance(results, ParquetResults):
            # ParquetResults are already saved during creation
            return sim_id
        else:
            # All results should be ParquetResults now
            raise ValueError(f"Expected ParquetResults, got {type(results)}")
    
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
        
        # Estimate Parquet disk usage (compressed)
        disk_mb = total_mb / 7  # Typical Parquet compression ratio
        
        return {
            'estimated_memory_mb': total_mb,
            'estimated_disk_mb': disk_mb,
            'patient_years': patient_years,
            'storage_type': 'parquet',  # Always Parquet now
            'warning': total_mb > 300
        }