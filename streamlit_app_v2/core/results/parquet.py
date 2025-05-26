"""
Parquet-based implementation of SimulationResults.

This implementation stores patient data on disk in Parquet format,
loading only what's needed into memory. Suitable for large simulations.
"""

import json
from typing import Dict, Any, Iterator, Optional, List, Tuple
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
from datetime import datetime

from .base import SimulationResults, SimulationMetadata


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
        
        # Load summary statistics from metadata
        summary_path = self.data_path / 'summary_stats.json'
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                self._summary_stats = json.load(f)
        else:
            # Calculate and cache summary statistics
            self._summary_stats = self._calculate_summary_stats()
            with open(summary_path, 'w') as f:
                json.dump(self._summary_stats, f, indent=2)
                
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
        
        Reads data from Parquet files in chunks to minimize memory usage.
        """
        visits_path = self.data_path / 'visits.parquet'
        patients_path = self.data_path / 'patients.parquet'
        
        # Read patient metadata
        patients_df = pd.read_parquet(patients_path)
        
        # Process in batches
        for start_idx in range(0, len(patients_df), batch_size):
            end_idx = min(start_idx + batch_size, len(patients_df))
            batch_patients = patients_df.iloc[start_idx:end_idx]
            
            batch_data = []
            for _, patient_row in batch_patients.iterrows():
                patient_id = patient_row['patient_id']
                
                # Read visits for this patient
                visits_df = pd.read_parquet(
                    visits_path,
                    filters=[('patient_id', '=', patient_id)]
                )
                
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
        patients_path = self.data_path / 'patients.parquet'
        visits_path = self.data_path / 'visits.parquet'
        
        # Read patient metadata
        patients_df = pd.read_parquet(
            patients_path,
            filters=[('patient_id', '=', patient_id)]
        )
        
        if patients_df.empty:
            return None
            
        patient_row = patients_df.iloc[0]
        
        # Read visits
        visits_df = pd.read_parquet(
            visits_path,
            filters=[('patient_id', '=', patient_id)]
        )
        
        return {
            'patient_id': patient_id,
            'disease_state': patient_row['final_disease_state'],
            'vision': patient_row['final_vision'],
            'visits': visits_df.to_dict('records'),
            'total_injections': patient_row['total_injections'],
            'discontinued': patient_row['discontinued'],
            'discontinuation_time': patient_row.get('discontinuation_time')
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
            
        # Transform to expected format
        result_df = visits_df[['patient_id', 'time_years', 'vision']].copy()
        result_df['time_months'] = result_df['time_years'] * 12
        result_df = result_df[['patient_id', 'time_months', 'vision']]
        
        return result_df
        
    def get_treatment_intervals_df(self) -> pd.DataFrame:
        """Get treatment intervals as DataFrame."""
        visits_path = self.data_path / 'visits.parquet'
        visits_df = pd.read_parquet(visits_path)
        
        # Calculate intervals
        intervals = []
        for patient_id in visits_df['patient_id'].unique():
            patient_visits = visits_df[visits_df['patient_id'] == patient_id].sort_values('time_years')
            
            if len(patient_visits) > 1:
                times = patient_visits['time_years'].values * 365
                for i in range(1, len(times)):
                    intervals.append({
                        'patient_id': patient_id,
                        'visit_number': i,
                        'interval_days': times[i] - times[i-1]
                    })
                    
        return pd.DataFrame(intervals)
        
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
            storage_type=metadata_dict['storage_type']
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
        save_path: Path
    ) -> 'ParquetResults':
        """
        Create ParquetResults from raw simulation results.
        
        This is used to convert in-memory results to Parquet format.
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata_path = save_path / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
            
        # Convert patients to DataFrame
        patient_records = []
        visit_records = []
        
        for patient_id, patient in raw_results.patient_histories.items():
            # Patient summary
            patient_records.append({
                'patient_id': patient_id,
                'final_disease_state': patient.disease_state.value,
                'final_vision': patient.vision,
                'total_injections': patient.injection_count,
                'total_visits': len(patient.visits),
                'discontinued': patient.discontinued,
                'discontinuation_time': getattr(patient, 'discontinuation_time', None)
            })
            
            # Visit details
            for visit in patient.visits:
                visit_records.append({
                    'patient_id': patient_id,
                    'time_years': visit.time_years,
                    'vision': visit.vision,
                    'injected': visit.injected,
                    'next_interval_days': visit.next_interval_days
                })
                
        # Save as Parquet
        patients_df = pd.DataFrame(patient_records)
        patients_df.to_parquet(save_path / 'patients.parquet', index=False)
        
        visits_df = pd.DataFrame(visit_records)
        visits_df.to_parquet(save_path / 'visits.parquet', index=False)
        
        return ParquetResults(metadata, save_path)