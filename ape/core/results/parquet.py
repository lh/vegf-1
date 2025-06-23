"""
Parquet-based implementation of SimulationResults.

This implementation stores patient data on disk in Parquet format,
loading only what's needed into memory. Suitable for large simulations.
"""

import json
from typing import Dict, Any, Iterator, Optional, List, Tuple, Callable
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
from datetime import datetime

from .base import SimulationResults, SimulationMetadata
from ape.core.storage import ParquetWriter, ParquetReader


class ParquetResults(SimulationResults):
    """
    Parquet-based storage of simulation results.
    
    This implementation stores patient data in Parquet files on disk,
    providing memory-efficient access to large datasets.
    """
    
    def __init__(self, metadata: SimulationMetadata, data_path: Path):
        """
        Initialize with metadata and path to Parquet files.
        
        Args:
            metadata: Simulation metadata
            data_path: Path to directory containing Parquet files
        """
        super().__init__(metadata)
        self.data_path = Path(data_path)
        
        # Initialize reader
        self.reader = ParquetReader(data_path)
        
        # Load resource tracker if available
        self.resource_tracker = None
        self._load_resource_tracker()
        
        # Load summary statistics from metadata
        summary_path = self.data_path / 'summary_stats.json'
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                self._summary_stats = json.load(f)
        else:
            # Get from reader metadata
            self._summary_stats = self.reader.get_summary_statistics()
            # Add any missing fields
            if 'patient_count' not in self._summary_stats:
                self._summary_stats['patient_count'] = self.reader.patient_count
            # Save for next time
            with open(summary_path, 'w') as f:
                json.dump(self._summary_stats, f, indent=2)
    
    def _load_resource_tracker(self) -> None:
        """Load resource tracking data if available."""
        # Check if we have resource tracking data
        metadata_parquet = self.data_path / 'metadata.parquet'
        if metadata_parquet.exists():
            metadata_df = pd.read_parquet(metadata_parquet)
            if 'has_resource_tracking' in metadata_df.columns and metadata_df['has_resource_tracking'].iloc[0]:
                # Create a mock resource tracker with the saved data
                from types import SimpleNamespace
                
                tracker = SimpleNamespace()
                
                # Load workload summary
                workload_file = self.data_path / 'workload_summary.json'
                if workload_file.exists():
                    with open(workload_file, 'r') as f:
                        workload_summary = json.load(f)
                        tracker.get_workload_summary = lambda: workload_summary
                
                # Load cost breakdown
                cost_file = self.data_path / 'cost_breakdown.json'
                if cost_file.exists():
                    with open(cost_file, 'r') as f:
                        costs = json.load(f)
                        tracker.get_total_costs = lambda: costs
                
                # Load bottlenecks
                bottleneck_file = self.data_path / 'bottlenecks.json'
                if bottleneck_file.exists():
                    with open(bottleneck_file, 'r') as f:
                        bottlenecks = json.load(f)
                        # Convert date strings back to datetime objects
                        from datetime import datetime
                        for b in bottlenecks:
                            b['date'] = datetime.fromisoformat(b['date']).date()
                        tracker.identify_bottlenecks = lambda: bottlenecks
                
                # Load resource configuration
                resource_config_file = self.data_path / 'resource_config.json'
                if resource_config_file.exists():
                    with open(resource_config_file, 'r') as f:
                        resource_config = json.load(f)
                        tracker.roles = resource_config.get('roles', {})
                        tracker.session_parameters = resource_config.get('session_parameters', {})
                        tracker.visit_requirements = resource_config.get('visit_requirements', {})
                else:
                    # If config file doesn't exist, raise error instead of using defaults
                    raise FileNotFoundError(
                        f"Resource configuration file not found at {resource_config_file}. "
                        "This simulation's resource tracking data appears to be incomplete."
                    )
                
                # Load daily usage
                daily_usage_file = self.data_path / 'daily_resource_usage.parquet'
                if daily_usage_file.exists():
                    daily_df = pd.read_parquet(daily_usage_file)
                    from collections import defaultdict
                    from datetime import datetime
                    
                    daily_usage = defaultdict(lambda: defaultdict(int))
                    for _, row in daily_df.iterrows():
                        date = datetime.fromisoformat(row['date']).date()
                        for role, count in row['usage'].items():
                            daily_usage[date][role] = count
                    
                    tracker.daily_usage = dict(daily_usage)
                    tracker.get_all_dates_with_visits = lambda: sorted(daily_usage.keys())
                    
                    def calculate_sessions_needed(date, role):
                        if role not in tracker.roles:
                            raise ValueError(f"Unknown role: {role}. Available roles: {list(tracker.roles.keys())}")
                        if date not in daily_usage:
                            raise ValueError(f"No visit data available for {date}")
                        if role not in daily_usage[date]:
                            return 0.0
                        daily_count = daily_usage[date][role]
                        role_info = tracker.roles.get(role)
                        if not role_info:
                            raise ValueError(f"Role '{role}' not found in tracker.roles")
                        if 'capacity_per_session' not in role_info:
                            raise ValueError(f"Role '{role}' missing 'capacity_per_session' field")
                        capacity = role_info['capacity_per_session']
                        if capacity is None or capacity <= 0:
                            raise ValueError(f"Invalid capacity for role '{role}': {capacity}")
                        return daily_count / capacity
                    
                    tracker.calculate_sessions_needed = calculate_sessions_needed
                
                # Load visits with costs
                visits_file = self.data_path / 'visits_with_costs.parquet'
                if visits_file.exists():
                    visits_df = pd.read_parquet(visits_file)
                    visits = []
                    for _, row in visits_df.iterrows():
                        visit = {
                            'date': datetime.fromisoformat(row['date']).date(),
                            'patient_id': row['patient_id'],
                            'visit_type': row['visit_type'],
                            'injection_given': row['injection_given'],
                            'oct_performed': row['oct_performed'],
                            'costs': {}
                        }
                        # Extract cost components
                        for col in visits_df.columns:
                            if col not in ['date', 'patient_id', 'visit_type', 'injection_given', 
                                         'oct_performed', 'total_cost']:
                                if pd.notna(row[col]):
                                    visit['costs'][col] = row[col]
                        visits.append(visit)
                    
                    tracker.visits = visits
                
                self.resource_tracker = tracker
                
    def get_patient_count(self) -> int:
        """Get the total number of patients."""
        return self._summary_stats['patient_count']
        
    def get_total_injections(self) -> int:
        """Get the total number of injections."""
        return self._summary_stats['total_injections']
        
    def get_final_vision_stats(self) -> Tuple[float, float]:
        """Get final vision statistics."""
        return (
            self._summary_stats['mean_final_vision'],
            self._summary_stats['std_final_vision']
        )
        
    def get_discontinuation_rate(self) -> float:
        """Get discontinuation rate."""
        return self._summary_stats['discontinuation_rate']
        
    def iterate_patients(self, batch_size: int = 100) -> Iterator[List[Dict[str, Any]]]:
        """
        Iterate over patients in batches.
        
        Uses lazy reader to minimize memory usage.
        """
        # Iterate over patient batches
        for patient_batch_df in self.reader.iterate_patients(batch_size=batch_size):
            batch_data = []
            
            for _, patient_row in patient_batch_df.iterrows():
                patient_id = patient_row['patient_id']
                
                # Get visits for this patient
                visits_df = self.reader.get_patient_visits(patient_id)
                
                patient_dict = {
                    'patient_id': patient_id,
                    'disease_state': patient_row['final_disease_state'],
                    'vision': patient_row['final_vision'],
                    'visits': visits_df.to_dict('records'),
                    'total_injections': patient_row['total_injections'],
                    'discontinued': patient_row['discontinued'],
                    'discontinuation_time': patient_row.get('discontinuation_time')
                }
                batch_data.append(patient_dict)
                
            yield batch_data
            
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific patient."""
        # Get patient data
        patient_data = self.reader.get_patient_by_id(patient_id)
        if not patient_data:
            return None
            
        # Get visits
        visits_df = self.reader.get_patient_visits(patient_id)
        
        return {
            'patient_id': patient_id,
            'disease_state': patient_data['final_disease_state'],
            'vision': patient_data['final_vision'],
            'visits': visits_df.to_dict('records'),
            'total_injections': patient_data['total_injections'],
            'discontinued': patient_data['discontinued'],
            'discontinuation_time': patient_data.get('discontinuation_time')
        }
        
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            **self._summary_stats,
            'metadata': self.metadata.to_dict()
        }
        
    def get_vision_trajectory_df(self, sample_size: Optional[int] = None) -> pd.DataFrame:
        """Get vision trajectories as DataFrame."""
        visits_path = self.data_path / 'visits.parquet'
        
        if sample_size:
            # Sample patients
            patients_df = pd.read_parquet(self.data_path / 'patients.parquet')
            sample_ids = patients_df['patient_id'].sample(
                n=min(sample_size, len(patients_df)),
                random_state=42
            ).tolist()
            
            # Read visits for sampled patients
            filters = [('patient_id', 'in', sample_ids)]
            visits_df = pd.read_parquet(visits_path, filters=filters)
        else:
            # Read all visits
            visits_df = pd.read_parquet(visits_path)
            
        # Return with time_days (no conversion needed)
        result_df = visits_df[['patient_id', 'time_days', 'vision']].copy()
        
        return result_df
        
    def get_patients_df(self) -> pd.DataFrame:
        """Get patient summary data as DataFrame including enrollment info."""
        patients_path = self.data_path / 'patients.parquet'
        return pd.read_parquet(patients_path)
        
    def get_visits_df(self) -> pd.DataFrame:
        """Get all visits as DataFrame with discontinuation/retreatment info."""
        visits_path = self.data_path / 'visits.parquet'
        visits_df = pd.read_parquet(visits_path)
        
        # Add discontinuation and retreatment columns if not present
        if 'is_discontinuation_visit' not in visits_df.columns:
            visits_df['is_discontinuation_visit'] = False
        if 'discontinuation_reason' not in visits_df.columns:
            visits_df['discontinuation_reason'] = None
        if 'is_retreatment_visit' not in visits_df.columns:
            visits_df['is_retreatment_visit'] = False
            
        return visits_df
    
    def get_treatment_intervals_df(self) -> pd.DataFrame:
        """Get treatment intervals as DataFrame - VECTORIZED for speed."""
        visits_path = self.data_path / 'visits.parquet'
        visits_df = pd.read_parquet(visits_path)
        
        # Sort by patient and time once
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        
        # Calculate intervals using shift - fully vectorized!
        visits_df['prev_time'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time']
        
        # Convert to int only for non-null values
        mask = visits_df['interval_days'].notna()
        visits_df.loc[mask, 'interval_days'] = visits_df.loc[mask, 'interval_days'].astype(int)
        
        # Add visit number for each patient
        visits_df['visit_number'] = visits_df.groupby('patient_id').cumcount()
        
        # Filter out first visits (no previous interval) and return
        intervals_df = visits_df[visits_df['prev_time'].notna()].copy()
        
        # Return only needed columns
        return intervals_df[['patient_id', 'visit_number', 'interval_days']].reset_index(drop=True)
        
    def save(self, path: Path) -> None:
        """
        Save results to disk.
        
        Note: For ParquetResults, this is typically called during
        initial creation, not after loading.
        """
        # If already saved at this path, nothing to do
        if path == self.data_path:
            return
            
        # Otherwise, copy files to new location
        import shutil
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        for file in self.data_path.glob('*'):
            shutil.copy2(file, path / file.name)
            
        self.data_path = path
        
    @classmethod
    def load(cls, path: Path) -> 'ParquetResults':
        """Load results from disk."""
        path = Path(path)
        
        # Load metadata
        metadata_path = path / 'metadata.json'
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
            
        # Convert back to SimulationMetadata
        metadata = SimulationMetadata(
            sim_id=metadata_dict['sim_id'],
            protocol_name=metadata_dict['protocol_name'],
            protocol_version=metadata_dict['protocol_version'],
            engine_type=metadata_dict['engine_type'],
            n_patients=metadata_dict['n_patients'],
            duration_years=metadata_dict['duration_years'],
            seed=metadata_dict['seed'],
            timestamp=datetime.fromisoformat(metadata_dict['timestamp']),
            runtime_seconds=metadata_dict['runtime_seconds'],
            storage_type=metadata_dict['storage_type'],
            memorable_name=metadata_dict.get('memorable_name', '')  # Handle older simulations
        )
        
        return cls(metadata, path)
        
    def get_memory_usage_mb(self) -> float:
        """
        Estimate memory usage in MB.
        
        For Parquet results, this is minimal as data is on disk.
        """
        # Only metadata and cached summary stats in memory
        return 1.0  # Approximately 1MB for overhead
        
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """Calculate and return summary statistics."""
        patients_df = pd.read_parquet(self.data_path / 'patients.parquet')
        
        return {
            'patient_count': len(patients_df),
            'total_injections': int(patients_df['total_injections'].sum()),
            'mean_final_vision': float(patients_df['final_vision'].mean()),
            'std_final_vision': float(patients_df['final_vision'].std()),
            'discontinuation_rate': float(patients_df['discontinued'].mean()),
            'total_visits': int(patients_df['total_visits'].sum()),
            'mean_visits_per_patient': float(patients_df['total_visits'].mean())
        }
        
    @staticmethod
    def create_from_raw_results(
        raw_results: Any,
        metadata: SimulationMetadata,
        save_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> 'ParquetResults':
        """
        Create ParquetResults from raw simulation results.
        
        This is used to convert in-memory results to Parquet format.
        
        Args:
            raw_results: Raw simulation results
            metadata: Simulation metadata
            save_path: Directory to save results
            progress_callback: Optional progress callback
            
        Returns:
            ParquetResults instance
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata_path = save_path / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
            
        # Use ParquetWriter for efficient chunked writing
        writer = ParquetWriter(save_path)
        writer.write_simulation_results(raw_results, progress_callback)
        
        # Create index for fast lookup
        reader = ParquetReader(save_path)
        reader.create_patient_index()
        
        return ParquetResults(metadata, save_path)