"""
Chunked Parquet writer with progress tracking.

Efficiently writes large simulation results to disk without loading
everything into memory at once.
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import Any, Iterator, Optional, Callable
import time


class ParquetWriter:
    """Write simulation data to Parquet files in chunks with progress tracking."""
    
    def __init__(self, output_dir: Path, chunk_size: int = 5000):
        """
        Initialize Parquet writer.
        
        Args:
            output_dir: Directory to write Parquet files
            chunk_size: Number of records to process at once
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        
    def write_simulation_results(
        self,
        raw_results: Any,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> None:
        """
        Write simulation results to Parquet files.
        
        Creates three files:
        - patients.parquet: Patient-level summary data
        - visits.parquet: All visit records
        - metadata.parquet: Simulation metadata
        
        Args:
            raw_results: Raw simulation results object
            progress_callback: Function to call with (progress_pct, message)
        """
        start_time = time.time()
        
        # Total steps for progress tracking
        total_patients = len(raw_results.patient_histories)
        
        # Find the earliest visit date to use as reference
        start_date = None
        for patient_id, patient in raw_results.patient_histories.items():
            visits = getattr(patient, 'visit_history', [])
            if visits and isinstance(visits[0], dict) and 'date' in visits[0]:
                visit_date = visits[0]['date']
                if start_date is None or visit_date < start_date:
                    start_date = visit_date
        
        # Step 1: Write patient summaries
        if progress_callback:
            progress_callback(0, "Preparing patient data...")
            
        patient_records = []
        patients_processed = 0
        
        for patient_id, patient in raw_results.patient_histories.items():
            # Extract patient summary with start date for time conversion
            record = self._extract_patient_summary(patient_id, patient, start_date)
            patient_records.append(record)
            patients_processed += 1
            
            # Write chunk if needed
            if len(patient_records) >= self.chunk_size:
                # Check if this is the final chunk
                is_final = patients_processed == total_patients
                self._write_patient_chunk(patient_records, is_final)
                
                if progress_callback:
                    progress = (patients_processed / total_patients) * 0.5  # First 50%
                    progress_callback(
                        progress * 100,
                        f"Processing patients: {patients_processed:,}/{total_patients:,}"
                    )
                    
                # Clear the records AFTER writing
                patient_records = []
        
        # Write remaining patients
        if patient_records:
            self._write_patient_chunk(patient_records, True)
            
        if progress_callback:
            progress_callback(50, "Writing visit data...")
            
        # Step 2: Write visit data in chunks
        self._write_visits_chunked(raw_results, progress_callback)
        
        # Step 3: Write metadata
        if progress_callback:
            progress_callback(95, "Finalizing metadata...")
            
        self._write_metadata(raw_results, time.time() - start_time)
        
        if progress_callback:
            progress_callback(100, "Complete!")
            
    def _extract_patient_summary(self, patient_id: str, patient: Any, start_date=None) -> dict:
        """Extract summary data for a patient."""
        # Get final vision (last visit)
        if hasattr(patient, 'visit_history') and patient.visit_history:
            # visit_history contains dicts, not objects
            last_visit = patient.visit_history[-1]
            if isinstance(last_visit, dict):
                final_vision = last_visit.get('vision', patient.current_vision)
            else:
                # Fallback for object-style visits
                final_vision = getattr(last_visit, 'visual_acuity', patient.current_vision)
            total_visits = len(patient.visit_history)
        else:
            # Fallback for different patient structures
            final_vision = getattr(patient, 'current_vision', getattr(patient, 'vision', 70))
            total_visits = len(getattr(patient, 'visits', []))
        
        # Convert discontinuation_date to days if we have a start date
        disc_date = getattr(patient, 'discontinuation_date', getattr(patient, 'discontinuation_time', None))
        disc_time_days = None
        if disc_date and start_date and hasattr(disc_date, 'timestamp'):
            time_delta = disc_date - start_date
            disc_time_days = int(time_delta.total_seconds() / (24 * 3600))
            
        return {
            'patient_id': patient_id,
            'baseline_vision': getattr(patient, 'baseline_vision', 70),
            'final_vision': final_vision,
            'final_disease_state': str(getattr(patient, 'current_state', getattr(patient, 'disease_state', 'unknown'))),
            'total_injections': getattr(patient, 'injection_count', 0),
            'total_visits': total_visits,
            'discontinued': getattr(patient, 'is_discontinued', getattr(patient, 'discontinued', False)),
            'discontinuation_time': disc_time_days,  # Now in days, not datetime
            'discontinuation_type': getattr(patient, 'discontinuation_type', None)
        }
        
    def _write_patient_chunk(self, records: list, is_final: bool) -> None:
        """Write a chunk of patient records."""
        df = pd.DataFrame(records)
        
        # Convert to table without index
        table = pa.Table.from_pandas(df, preserve_index=False)
        
        # Write or append
        file_path = self.output_dir / 'patients.parquet'
        if file_path.exists():
            # Always append if file exists
            existing = pq.read_table(file_path)
            combined = pa.concat_tables([existing, table])
            pq.write_table(combined, file_path)
        else:
            # First write
            pq.write_table(table, file_path)
            
    def _write_visits_chunked(
        self,
        raw_results: Any,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> None:
        """Write visit data in chunks."""
        visit_records = []
        total_patients = len(raw_results.patient_histories)
        patients_processed = 0
        
        for patient_id, patient in raw_results.patient_histories.items():
            # Extract visits
            visits = getattr(patient, 'visit_history', getattr(patient, 'visits', []))
            
            for i, visit in enumerate(visits):
                # Handle both dict and object formats
                if isinstance(visit, dict):
                    # Dict format from visit_history
                    visit_date = visit.get('date')
                    if visit_date and hasattr(visit_date, 'timestamp'):
                        # Calculate days from simulation start (first visit)
                        if i == 0:
                            start_date = visit_date
                        time_delta = visit_date - visits[0].get('date', visit_date)
                        time_days = int(time_delta.total_seconds() / (24 * 3600))
                    else:
                        time_days = i * 30  # Fallback: assume monthly visits
                        
                    record = {
                        'patient_id': patient_id,
                        'date': visit_date,  # Store original datetime
                        'time_days': time_days,  # Days from start
                        'vision': visit.get('vision', 70),
                        'injected': visit.get('treatment_given', False),
                        'next_interval_days': visit.get('next_interval_days', None),
                        'disease_state': str(visit.get('disease_state', ''))
                    }
                else:
                    # Object format (fallback)
                    record = {
                        'patient_id': patient_id,
                        'date': getattr(visit, 'date', None),
                        'time_days': getattr(visit, 'time_days', getattr(visit, 'time', i * 30)),
                        'vision': getattr(visit, 'visual_acuity', getattr(visit, 'vision', 70)),
                        'injected': getattr(visit, 'received_injection', getattr(visit, 'injected', False)),
                        'next_interval_days': getattr(visit, 'next_interval_days', None),
                        'disease_state': str(getattr(visit, 'disease_state', ''))
                    }
                visit_records.append(record)
                
                # Write chunk if needed
                if len(visit_records) >= self.chunk_size:
                    self._write_visit_chunk(visit_records, False)
                    visit_records = []
                    
            patients_processed += 1
            if progress_callback and patients_processed % 100 == 0:
                progress = 50 + (patients_processed / total_patients) * 45  # 50-95%
                progress_callback(
                    progress,
                    f"Processing visits: {patients_processed:,}/{total_patients:,} patients"
                )
                
        # Write remaining visits
        if visit_records:
            self._write_visit_chunk(visit_records, True)
            
    def _write_visit_chunk(self, records: list, is_final: bool) -> None:
        """Write a chunk of visit records."""
        df = pd.DataFrame(records)
        
        # Sort by patient and time for better query performance
        df = df.sort_values(['patient_id', 'time_days'])
        
        # Convert to table without index
        table = pa.Table.from_pandas(df, preserve_index=False)
        
        # Write or append
        file_path = self.output_dir / 'visits.parquet'
        if file_path.exists():
            # Always append if file exists
            existing = pq.read_table(file_path)
            combined = pa.concat_tables([existing, table])
            pq.write_table(combined, file_path)
        else:
            # First write
            pq.write_table(table, file_path)
            
    def _write_metadata(self, raw_results: Any, write_time_seconds: float) -> None:
        """Write simulation metadata."""
        metadata = {
            'total_patients': len(raw_results.patient_histories),
            'total_injections': raw_results.total_injections,
            'mean_final_vision': raw_results.final_vision_mean,
            'std_final_vision': raw_results.final_vision_std,
            'discontinuation_rate': raw_results.discontinuation_rate,
            'write_time_seconds': write_time_seconds,
            'chunk_size': self.chunk_size
        }
        
        df = pd.DataFrame([metadata])
        df.to_parquet(self.output_dir / 'metadata.parquet', index=False)