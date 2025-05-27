"""
Lazy Parquet reader for efficient data access.

Provides memory-efficient access to large datasets by reading only
what's needed when it's needed.
"""

import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import Iterator, Optional, List, Dict, Any, Tuple
import numpy as np


class ParquetReader:
    """Read simulation data from Parquet files lazily."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize reader with data directory.
        
        Args:
            data_dir: Directory containing Parquet files
        """
        self.data_dir = Path(data_dir)
        self._validate_files()
        
        # Cache metadata
        self._metadata = None
        self._patient_count = None
        
    def _validate_files(self) -> None:
        """Validate required files exist."""
        required_files = ['patients.parquet', 'visits.parquet', 'metadata.parquet']
        for file in required_files:
            if not (self.data_dir / file).exists():
                raise FileNotFoundError(f"Required file {file} not found in {self.data_dir}")
                
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get cached metadata."""
        if self._metadata is None:
            df = pd.read_parquet(self.data_dir / 'metadata.parquet')
            self._metadata = df.iloc[0].to_dict()
        return self._metadata
        
    @property
    def patient_count(self) -> int:
        """Get total patient count."""
        if self._patient_count is None:
            # Use Parquet metadata for fast count
            pf = pq.ParquetFile(self.data_dir / 'patients.parquet')
            self._patient_count = pf.metadata.num_rows
        return self._patient_count
        
    def iterate_patients(
        self,
        batch_size: int = 100,
        columns: Optional[List[str]] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Iterate over patients in batches.
        
        Args:
            batch_size: Number of patients per batch
            columns: Specific columns to load (None for all)
            
        Yields:
            DataFrames with patient data
        """
        # Use Parquet's native batch reading
        parquet_file = pq.ParquetFile(self.data_dir / 'patients.parquet')
        
        for batch in parquet_file.iter_batches(batch_size=batch_size, columns=columns):
            yield batch.to_pandas()
            
    def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific patient's data.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Patient data as dictionary or None if not found
        """
        # Read only the needed patient using filters
        filters = [('patient_id', '==', patient_id)]
        
        try:
            df = pd.read_parquet(
                self.data_dir / 'patients.parquet',
                filters=filters
            )
            
            if df.empty:
                return None
                
            return df.iloc[0].to_dict()
            
        except Exception:
            return None
            
    def get_patient_visits(
        self,
        patient_id: str,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get all visits for a specific patient.
        
        Args:
            patient_id: Patient identifier
            columns: Specific columns to load
            
        Returns:
            DataFrame with visit data
        """
        filters = [('patient_id', '==', patient_id)]
        
        df = pd.read_parquet(
            self.data_dir / 'visits.parquet',
            filters=filters,
            columns=columns
        )
        
        return df.sort_values('time_years')
        
    def iterate_visits(
        self,
        batch_size: int = 5000,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Tuple]] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Iterate over visits in batches.
        
        Args:
            batch_size: Number of visits per batch
            columns: Specific columns to load
            filters: PyArrow filters to apply
            
        Yields:
            DataFrames with visit data
        """
        parquet_file = pq.ParquetFile(self.data_dir / 'visits.parquet')
        
        # If filters provided, we need to read differently
        if filters:
            # Read with filters (less efficient but necessary)
            df = pd.read_parquet(
                self.data_dir / 'visits.parquet',
                filters=filters,
                columns=columns
            )
            
            # Yield in batches
            for start_idx in range(0, len(df), batch_size):
                end_idx = min(start_idx + batch_size, len(df))
                yield df.iloc[start_idx:end_idx]
        else:
            # Use native batch reading
            for batch in parquet_file.iter_batches(batch_size=batch_size, columns=columns):
                yield batch.to_pandas()
                
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get pre-computed summary statistics.
        
        Returns:
            Dictionary with summary stats
        """
        # Start with metadata
        stats = self.metadata.copy()
        
        # Add patient-level summaries using Parquet metadata
        patients_file = pq.ParquetFile(self.data_dir / 'patients.parquet')
        visits_file = pq.ParquetFile(self.data_dir / 'visits.parquet')
        
        stats['total_patients'] = patients_file.metadata.num_rows
        stats['total_visits'] = visits_file.metadata.num_rows
        stats['mean_visits_per_patient'] = stats['total_visits'] / stats['total_patients']
        
        return stats
        
    def get_vision_trajectories_lazy(
        self,
        patient_ids: Optional[List[str]] = None,
        sample_size: Optional[int] = None,
        time_points: Optional[List[float]] = None
    ) -> Iterator[pd.DataFrame]:
        """
        Get vision trajectories lazily.
        
        Args:
            patient_ids: Specific patients to include
            sample_size: Random sample size (if no patient_ids)
            time_points: Specific time points to include
            
        Yields:
            DataFrames with vision trajectory data
        """
        # If sampling needed
        if sample_size and not patient_ids:
            # Get random sample of patient IDs
            all_patients = pd.read_parquet(
                self.data_dir / 'patients.parquet',
                columns=['patient_id']
            )
            patient_ids = all_patients.sample(n=min(sample_size, len(all_patients)))['patient_id'].tolist()
            
        # Set up filters
        filters = []
        if patient_ids:
            filters.append(('patient_id', 'in', patient_ids))
        if time_points:
            # This is less efficient but necessary for specific time filtering
            for tp in time_points:
                filters.append(('time_years', '>=', tp - 0.01))
                filters.append(('time_years', '<=', tp + 0.01))
                
        # Iterate over visits with filters
        columns = ['patient_id', 'time_years', 'vision']
        
        for batch in self.iterate_visits(
            batch_size=10000,
            columns=columns,
            filters=filters if filters else None
        ):
            yield batch
            
    def create_patient_index(self) -> None:
        """
        Create an index for fast patient lookup.
        
        This creates a small index file mapping patient IDs to row numbers
        for faster individual patient access.
        """
        # Read patient IDs and create index
        df = pd.read_parquet(
            self.data_dir / 'patients.parquet',
            columns=['patient_id']
        )
        
        # Create index mapping
        index_data = {
            'patient_id': df['patient_id'].tolist(),
            'row_number': list(range(len(df)))
        }
        
        # Save index
        index_df = pd.DataFrame(index_data)
        index_df.to_parquet(self.data_dir / 'patient_index.parquet', index=False)
        
    def get_patient_batch(self, patient_ids: List[str]) -> pd.DataFrame:
        """
        Get multiple patients efficiently.
        
        Args:
            patient_ids: List of patient IDs
            
        Returns:
            DataFrame with patient data
        """
        filters = [('patient_id', 'in', patient_ids)]
        
        return pd.read_parquet(
            self.data_dir / 'patients.parquet',
            filters=filters
        )