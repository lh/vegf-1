"""
In-memory implementation of SimulationResults.

This is the traditional approach - all data is kept in memory.
Suitable for small to medium simulations.
"""

import sys
import pickle
import json
from typing import Dict, Any, Iterator, Optional, List, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

from .base import SimulationResults, SimulationMetadata


class InMemoryResults(SimulationResults):
    """
    In-memory storage of simulation results.
    
    This implementation keeps all patient data in memory, providing
    fast access but limited by available RAM.
    """
    
    def __init__(self, metadata: SimulationMetadata, raw_results: Any):
        """
        Initialize with simulation data.
        
        Args:
            metadata: Simulation metadata
            raw_results: The raw results object from simulation engine
        """
        super().__init__(metadata)
        self.raw_results = raw_results
        
        # Cache commonly accessed values
        self._patient_count = len(raw_results.patient_histories)
        self._total_injections = raw_results.total_injections
        self._final_vision_mean = raw_results.final_vision_mean
        self._final_vision_std = raw_results.final_vision_std
        self._discontinuation_rate = raw_results.discontinuation_rate
        
    def get_patient_count(self) -> int:
        """Get the total number of patients."""
        return self._patient_count
        
    def get_total_injections(self) -> int:
        """Get the total number of injections."""
        return self._total_injections
        
    def get_final_vision_stats(self) -> Tuple[float, float]:
        """Get final vision statistics."""
        return (self._final_vision_mean, self._final_vision_std)
        
    def get_discontinuation_rate(self) -> float:
        """Get discontinuation rate."""
        return self._discontinuation_rate
        
    def iterate_patients(self, batch_size: int = 100) -> Iterator[List[Dict[str, Any]]]:
        """
        Iterate over patients in batches.
        
        Note: For in-memory results, we could return all at once,
        but we maintain the batch interface for consistency.
        """
        patient_ids = list(self.raw_results.patient_histories.keys())
        
        for i in range(0, len(patient_ids), batch_size):
            batch_ids = patient_ids[i:i + batch_size]
            batch_patients = []
            
            for pid in batch_ids:
                patient = self.raw_results.patient_histories[pid]
                # Convert patient object to dictionary
                patient_dict = self._patient_to_dict(patient)
                batch_patients.append(patient_dict)
                
            yield batch_patients
            
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific patient."""
        if patient_id in self.raw_results.patient_histories:
            patient = self.raw_results.patient_histories[patient_id]
            return self._patient_to_dict(patient)
        return None
        
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics."""
        # Calculate additional statistics
        total_visits = sum(
            len(patient.visits) 
            for patient in self.raw_results.patient_histories.values()
        )
        mean_visits = total_visits / self._patient_count if self._patient_count > 0 else 0
        
        return {
            'patient_count': self._patient_count,
            'total_injections': self._total_injections,
            'mean_final_vision': self._final_vision_mean,
            'std_final_vision': self._final_vision_std,
            'discontinuation_rate': self._discontinuation_rate,
            'total_visits': total_visits,
            'mean_visits_per_patient': mean_visits,
            'metadata': self.metadata.to_dict()
        }
        
    def get_vision_trajectory_df(self, sample_size: Optional[int] = None) -> pd.DataFrame:
        """Get vision trajectories as DataFrame."""
        records = []
        patient_ids = list(self.raw_results.patient_histories.keys())
        
        # Sample if requested
        if sample_size and sample_size < len(patient_ids):
            import random
            random.seed(42)  # For reproducibility
            patient_ids = random.sample(patient_ids, sample_size)
            
        for patient_id in patient_ids:
            patient = self.raw_results.patient_histories[patient_id]
            for visit in patient.visits:
                records.append({
                    'patient_id': patient_id,
                    'time_months': visit.time_years * 12,
                    'vision': visit.vision
                })
                
        return pd.DataFrame(records)
        
    def get_treatment_intervals_df(self) -> pd.DataFrame:
        """Get treatment intervals as DataFrame."""
        records = []
        
        for patient_id, patient in self.raw_results.patient_histories.items():
            if len(patient.visits) > 1:
                for i in range(1, len(patient.visits)):
                    prev_time = patient.visits[i-1].time_years * 365
                    curr_time = patient.visits[i].time_years * 365
                    interval = curr_time - prev_time
                    
                    records.append({
                        'patient_id': patient_id,
                        'visit_number': i,
                        'interval_days': interval
                    })
                    
        return pd.DataFrame(records)
        
    def save(self, path: Path) -> None:
        """Save results to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata_path = path / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata.to_dict(), f, indent=2)
            
        # Save raw results using pickle
        results_path = path / 'results.pkl'
        with open(results_path, 'wb') as f:
            pickle.dump(self.raw_results, f)
            
    @classmethod
    def load(cls, path: Path) -> 'InMemoryResults':
        """Load results from disk."""
        path = Path(path)
        
        # Load metadata
        metadata_path = path / 'metadata.json'
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
            
        # Convert back to SimulationMetadata
        from datetime import datetime
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
        
        # Load raw results
        results_path = path / 'results.pkl'
        with open(results_path, 'rb') as f:
            raw_results = pickle.load(f)
            
        return cls(metadata, raw_results)
        
    def get_memory_usage_mb(self) -> float:
        """Estimate memory usage in MB."""
        # Rough estimate based on object size
        size_bytes = sys.getsizeof(self.raw_results)
        
        # Add size of patient histories
        for patient in self.raw_results.patient_histories.values():
            size_bytes += sys.getsizeof(patient)
            # Add visits if they exist (handle different patient structures)
            if hasattr(patient, 'visits'):
                for visit in patient.visits:
                    size_bytes += sys.getsizeof(visit)
            elif hasattr(patient, 'visit_history'):
                for visit in patient.visit_history:
                    size_bytes += sys.getsizeof(visit)
                    
        return size_bytes / (1024 * 1024)
        
    def _patient_to_dict(self, patient: Any) -> Dict[str, Any]:
        """Convert patient object to dictionary."""
        # Extract relevant fields from patient object
        # Handle different patient structures
        visits = []
        if hasattr(patient, 'visits'):
            visits = patient.visits
        elif hasattr(patient, 'visit_history'):
            visits = patient.visit_history
            
        visit_dicts = []
        for visit in visits:
            visit_dict = {
                'time_years': getattr(visit, 'time_years', getattr(visit, 'time', 0)),
                'vision': getattr(visit, 'vision', getattr(visit, 'visual_acuity', 0)),
                'injected': getattr(visit, 'injected', getattr(visit, 'received_injection', False)),
                'next_interval_days': getattr(visit, 'next_interval_days', None)
            }
            visit_dicts.append(visit_dict)
            
        return {
            'patient_id': getattr(patient, 'patient_id', str(id(patient))),
            'disease_state': getattr(patient.disease_state, 'value', str(patient.disease_state)) if hasattr(patient, 'disease_state') else 'unknown',
            'vision': getattr(patient, 'vision', getattr(patient, 'visual_acuity', 0)),
            'visits': visit_dicts,
            'total_injections': getattr(patient, 'injection_count', getattr(patient, 'total_injections', len([v for v in visits if getattr(v, 'injected', False)]))),
            'discontinued': getattr(patient, 'discontinued', False),
            'discontinuation_time': getattr(patient, 'discontinuation_time', None)
        }