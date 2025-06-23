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
from datetime import datetime

from .writer_types import PatientRecord, VisitRecord, ensure_datetime, ensure_int_days


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
        
        # Find the earliest enrollment date to use as simulation start reference
        start_date = None
        for patient_id, patient in raw_results.patient_histories.items():
            enrollment_date = getattr(patient, 'enrollment_date', None)
            if not enrollment_date:
                raise ValueError(
                    f"Patient {patient_id} missing enrollment_date. "
                    "All patients must have an enrollment date."
                )
            if start_date is None or enrollment_date < start_date:
                start_date = enrollment_date
        
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
            
    def _extract_patient_summary(self, patient_id: str, patient: Any, start_date: datetime) -> PatientRecord:
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
        
        # Get enrollment_date and ensure it's a datetime
        enrollment_date = getattr(patient, 'enrollment_date', None)
        if not enrollment_date:
            raise ValueError(f"Patient {patient_id} missing enrollment_date")
        
        # Ensure enrollment_date is a datetime object
        enrollment_date = ensure_datetime(enrollment_date, f"Patient {patient_id} enrollment_date")
        
        # Ensure start_date is provided and is a datetime
        if not start_date:
            raise ValueError("Start date not provided for time calculation")
        start_date = ensure_datetime(start_date, "Simulation start_date")
            
        # Calculate days from simulation start
        time_delta = enrollment_date - start_date
        enrollment_time_days = ensure_int_days(
            time_delta.total_seconds(), 
            f"Patient {patient_id} enrollment_time_days"
        )
        
        # Convert discontinuation_date to days if patient is discontinued
        disc_date = getattr(patient, 'discontinuation_date', getattr(patient, 'discontinuation_time', None))
        disc_time_days = None
        if disc_date:
            # Ensure it's a datetime object
            disc_date = ensure_datetime(disc_date, f"Patient {patient_id} discontinuation_date")
            time_delta = disc_date - start_date
            disc_time_days = ensure_int_days(
                time_delta.total_seconds(),
                f"Patient {patient_id} discontinuation_time_days"
            )
            
        # Build record with strict typing
        record: PatientRecord = {
            'patient_id': str(patient_id),
            'enrollment_date': enrollment_date,  # datetime object
            'enrollment_time_days': int(enrollment_time_days),  # int days
            'baseline_vision': int(getattr(patient, 'baseline_vision', 70)),
            'final_vision': int(final_vision),
            'final_disease_state': str(getattr(patient, 'current_state', getattr(patient, 'disease_state', 'unknown'))),
            'total_injections': int(getattr(patient, 'injection_count', 0)),
            'total_visits': int(total_visits),
            'discontinued': bool(getattr(patient, 'is_discontinued', getattr(patient, 'discontinued', False))),
            'discontinuation_time': disc_time_days,  # int days or None
            'discontinuation_type': getattr(patient, 'discontinuation_type', None),
            'discontinuation_reason': getattr(patient, 'discontinuation_reason', None),
            'pre_discontinuation_vision': getattr(patient, 'pre_discontinuation_vision', None),
            'retreatment_count': int(getattr(patient, 'retreatment_count', 0))
        }
        return record
        
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
            
            # Get patient's enrollment date - REQUIRED
            enrollment_date = getattr(patient, 'enrollment_date', None)
            if not enrollment_date:
                raise ValueError(
                    f"Patient {patient_id} missing enrollment_date. "
                    "All patients must have an enrollment date."
                )
            
            for i, visit in enumerate(visits):
                # Handle both dict and object formats
                if isinstance(visit, dict):
                    # Dict format from visit_history
                    visit_date = visit.get('date')
                    if not visit_date:
                        raise ValueError(
                            f"Visit {i} for patient {patient_id} missing date"
                        )
                    
                    # Ensure visit date is a datetime object
                    visit_date = ensure_datetime(visit_date, f"Patient {patient_id} visit {i} date")
                    
                    # Calculate days from patient enrollment
                    time_delta = visit_date - enrollment_date
                    time_days_from_enrollment = ensure_int_days(
                        time_delta.total_seconds(),
                        f"Patient {patient_id} visit {i} time_days"
                    )
                        
                    # Build record with strict typing
                    record: VisitRecord = {
                        'patient_id': str(patient_id),
                        'date': visit_date,  # datetime object
                        'time_days': int(time_days_from_enrollment),  # int days
                        'vision': int(visit.get('vision', 70)),
                        'injected': bool(visit.get('treatment_given', False)),
                        'next_interval_days': visit.get('next_interval_days', None) if visit.get('next_interval_days') is None else int(visit.get('next_interval_days')),
                        'disease_state': str(visit.get('disease_state', ''))
                    }
                else:
                    # Object format
                    visit_date = getattr(visit, 'date', None)
                    if not visit_date:
                        raise ValueError(
                            f"Visit {i} for patient {patient_id} missing date attribute"
                        )
                    
                    # Ensure visit date is a datetime object
                    visit_date = ensure_datetime(visit_date, f"Patient {patient_id} visit {i} date")
                    
                    # Calculate days from patient enrollment
                    time_delta = visit_date - enrollment_date
                    time_days_from_enrollment = ensure_int_days(
                        time_delta.total_seconds(),
                        f"Patient {patient_id} visit {i} time_days"
                    )
                    
                    # Build record with strict typing
                    next_interval = getattr(visit, 'next_interval_days', None)
                    record: VisitRecord = {
                        'patient_id': str(patient_id),
                        'date': visit_date,  # datetime object
                        'time_days': int(time_days_from_enrollment),  # int days
                        'vision': int(getattr(visit, 'visual_acuity', getattr(visit, 'vision', 70))),
                        'injected': bool(getattr(visit, 'received_injection', getattr(visit, 'injected', False))),
                        'next_interval_days': None if next_interval is None else int(next_interval),
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
        
        # Check if resource tracking data is available
        if hasattr(raw_results, 'resource_tracker'):
            # Save resource tracking data separately
            self._write_resource_tracking_data(raw_results.resource_tracker)
            metadata['has_resource_tracking'] = True
        else:
            metadata['has_resource_tracking'] = False
        
        df = pd.DataFrame([metadata])
        df.to_parquet(self.output_dir / 'metadata.parquet', index=False)
    
    def _write_resource_tracking_data(self, resource_tracker: Any) -> None:
        """Write resource tracking data to separate files."""
        import json
        
        # Save resource configuration (roles and capacities)
        resource_config = {
            'roles': resource_tracker.roles,
            'session_parameters': resource_tracker.session_parameters,
            'visit_requirements': resource_tracker.visit_requirements
        }
        with open(self.output_dir / 'resource_config.json', 'w') as f:
            json.dump(resource_config, f, indent=2)
        
        # Write workload summary
        workload_summary = resource_tracker.get_workload_summary()
        with open(self.output_dir / 'workload_summary.json', 'w') as f:
            json.dump(workload_summary, f, indent=2)
        
        # Write cost breakdown
        cost_breakdown = resource_tracker.get_total_costs()
        with open(self.output_dir / 'cost_breakdown.json', 'w') as f:
            json.dump(cost_breakdown, f, indent=2)
        
        # Write bottlenecks
        bottlenecks = resource_tracker.identify_bottlenecks()
        bottleneck_data = [
            {
                'date': b['date'].isoformat(),
                'role': b['role'],
                'sessions_needed': b['sessions_needed'],
                'sessions_available': b['sessions_available'],
                'overflow': b['overflow'],
                'procedures_affected': b['procedures_affected']
            }
            for b in bottlenecks
        ]
        with open(self.output_dir / 'bottlenecks.json', 'w') as f:
            json.dump(bottleneck_data, f, indent=2)
        
        # Write daily usage data
        daily_usage_data = []
        for date in resource_tracker.get_all_dates_with_visits():
            daily_usage_data.append({
                'date': date.isoformat(),
                'usage': dict(resource_tracker.daily_usage[date])
            })
        
        daily_usage_df = pd.DataFrame(daily_usage_data)
        if not daily_usage_df.empty:
            daily_usage_df.to_parquet(self.output_dir / 'daily_resource_usage.parquet', index=False)
        
        # Write visits with costs
        visit_records = []
        for visit in resource_tracker.visits:
            record = {
                'date': visit['date'].isoformat(),
                'patient_id': visit['patient_id'],
                'visit_type': visit['visit_type'],
                'injection_given': visit['injection_given'],
                'oct_performed': visit['oct_performed'],
                'total_cost': sum(visit['costs'].values()),
                **visit['costs']  # Include individual cost components
            }
            visit_records.append(record)
        
        if visit_records:
            visits_with_costs_df = pd.DataFrame(visit_records)
            visits_with_costs_df.to_parquet(self.output_dir / 'visits_with_costs.parquet', index=False)