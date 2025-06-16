"""
Time-based Agent-Based Simulation (ABS) engine.

Key differences from standard ABS:
- Disease states update every 14 days for all patients
- Vision changes fortnightly based on disease state
- Visits only determine treatment, not progression
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.core.protocol import Protocol
from simulation_v2.engines.abs_engine import ABSEngine, SimulationResults


class ABSEngineTimeBased(ABSEngine):
    """
    Time-based ABS engine with fortnightly disease updates.
    
    Inherits patient management from base ABSEngine but overrides
    the simulation loop to include fortnightly state updates.
    """
    
    def __init__(
        self,
        disease_model: DiseaseModelTimeBased,
        protocol: Protocol,
        n_patients: int,
        seed: Optional[int] = None,
        baseline_vision_distribution: Optional[Any] = None
    ):
        """
        Initialize time-based ABS engine.
        
        Args:
            disease_model: Time-based disease model with fortnightly updates
            protocol: Treatment protocol
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
        """
        # Store time-based model before calling parent init
        self.time_based_model = disease_model
        
        # Call parent init (but we'll override the disease model behavior)
        super().__init__(
            disease_model=disease_model,  # Pass for compatibility
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            baseline_vision_distribution=baseline_vision_distribution
        )
        
        # Track actual vision values (not just measured)
        self.patient_actual_vision: Dict[str, float] = {}
        self.patient_vision_ceiling: Dict[str, int] = {}
        
        # Track fortnightly update state
        self.last_fortnightly_update: Optional[datetime] = None
        
        # Store visit metadata enhancer (if not already set by parent)
        if not hasattr(self, 'visit_metadata_enhancer'):
            self.visit_metadata_enhancer = None
        
    def run(self, duration_years: float, start_date: Optional[datetime] = None) -> SimulationResults:
        """
        Run time-based simulation with fortnightly updates.
        
        Args:
            duration_years: Simulation duration in years
            start_date: Simulation start date (default: 2024-01-01)
            
        Returns:
            SimulationResults with patient histories
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)
            
        end_date = start_date + timedelta(days=int(duration_years * 365.25))
        
        # Generate patient arrival schedule
        self.patient_arrival_schedule = self._generate_arrival_schedule(start_date, end_date)
        
        # Initialize fortnightly update tracking
        self.last_fortnightly_update = start_date
        
        # Schedule visits for patients
        visit_schedule: Dict[str, datetime] = {}
        
        # Run simulation day by day
        current_date = start_date
        total_injections = 0
        arrival_index = 0
        
        while current_date <= end_date:
            # Check if we need fortnightly updates
            days_since_start = (current_date - start_date).days
            if days_since_start > 0 and days_since_start % 14 == 0:
                self._perform_fortnightly_updates(current_date)
            
            # Process new patient arrivals
            while (arrival_index < len(self.patient_arrival_schedule) and 
                   self.patient_arrival_schedule[arrival_index][0].date() <= current_date.date()):
                arrival_date, patient_id = self.patient_arrival_schedule[arrival_index]
                
                # Create new patient
                # Normalize arrival date to midnight for consistency with visit scheduling
                normalized_arrival_date = arrival_date.replace(hour=0, minute=0, second=0, microsecond=0)
                patient = self._create_patient(patient_id, normalized_arrival_date)
                self.patients[patient_id] = patient
                self.enrollment_dates[patient_id] = normalized_arrival_date
                
                # Initialize actual vision tracking
                baseline_vision = patient.baseline_vision
                self.patient_actual_vision[patient_id] = float(baseline_vision)
                self.patient_vision_ceiling[patient_id] = min(85, int(baseline_vision * 1.1))
                
                # Schedule first visit at enrollment date (already normalized to midnight)
                visit_schedule[patient_id] = normalized_arrival_date
                
                arrival_index += 1
            
            # Process scheduled visits for today
            visits_today = [
                patient_id for patient_id, visit_date in visit_schedule.items()
                if visit_date.date() == current_date.date()
            ]
            
            for patient_id in visits_today:
                patient = self.patients[patient_id]
                
                if not patient.is_discontinued:
                    # Process visit (treatment decision only)
                    treated = self._process_visit(patient, current_date)
                    
                    if treated:
                        total_injections += 1
                    
                    # Schedule next visit
                    next_date = self.protocol.next_visit_date(patient, current_date, treated)
                    
                    # Ensure next visit is in the future and within simulation
                    if next_date > current_date and next_date <= end_date:
                        visit_schedule[patient_id] = next_date
                    else:
                        # Remove from schedule if beyond simulation
                        del visit_schedule[patient_id]
                else:
                    # Remove discontinued patients from schedule
                    if patient_id in visit_schedule:
                        del visit_schedule[patient_id]
            
            # Advance to next day
            current_date += timedelta(days=1)
        
        # Calculate final statistics
        final_visions = []
        discontinued_count = 0
        
        for patient in self.patients.values():
            if patient.is_discontinued:
                discontinued_count += 1
            
            # Use last measured vision
            if patient.visit_history:
                final_visions.append(patient.visit_history[-1]['vision'])
        
        # Calculate statistics
        final_vision_mean = np.mean(final_visions) if final_visions else 0
        final_vision_std = np.std(final_visions) if final_visions else 0
        discontinuation_rate = discontinued_count / len(self.patients) if self.patients else 0
        
        return SimulationResults(
            total_injections=total_injections,
            patient_histories=self.patients,
            final_vision_mean=final_vision_mean,
            final_vision_std=final_vision_std,
            discontinuation_rate=discontinuation_rate
        )
    
    def _perform_fortnightly_updates(self, current_date: datetime):
        """
        Perform fortnightly updates for all enrolled patients.
        
        Updates disease states and vision for all patients,
        regardless of visit schedule.
        """
        # Batch process all patients
        for patient_id, patient in self.patients.items():
            if patient.is_discontinued:
                continue
                
            # Skip if patient not yet enrolled
            if current_date < self.enrollment_dates[patient_id]:
                continue
            
            # Update disease state
            days_since_injection = patient.days_since_last_injection_at(current_date)
            new_state = self.time_based_model.update_state(
                patient_id=patient_id,
                current_state=patient.current_state,
                current_date=current_date,
                days_since_last_injection=days_since_injection
            )
            
            # Update patient state if changed
            if new_state != patient.current_state:
                patient.current_state = new_state
                # Note: We don't record this in visit history - it's internal
            
            # Update vision (this will be implemented with vision parameters)
            # For now, placeholder logic
            self._update_patient_vision(patient_id, patient, current_date)
    
    def _update_patient_vision(self, patient_id: str, patient: Patient, current_date: datetime):
        """
        Update patient's actual vision based on disease state and treatment.
        
        This is a placeholder - will be replaced with full vision model.
        """
        # Simple placeholder logic for now
        # TODO: Implement full vision model with parameters
        
        current_vision = self.patient_actual_vision[patient_id]
        vision_ceiling = self.patient_vision_ceiling[patient_id]
        
        # Basic vision change based on disease state
        if patient.current_state.name == 'STABLE':
            change = random.gauss(-0.1, 0.1)  # Minimal change
        elif patient.current_state.name == 'ACTIVE':
            change = random.gauss(-0.5, 0.3)  # Moderate decline
        elif patient.current_state.name == 'HIGHLY_ACTIVE':
            change = random.gauss(-1.0, 0.5)  # Significant decline
        else:  # NAIVE
            change = random.gauss(-0.3, 0.2)
        
        # Apply change with ceiling
        new_vision = current_vision + change
        new_vision = min(new_vision, vision_ceiling)
        new_vision = max(0, new_vision)
        
        self.patient_actual_vision[patient_id] = new_vision
    
    def _process_visit(self, patient: Patient, visit_date: datetime) -> bool:
        """
        Process a patient visit - treatment decision and measurement only.
        
        Disease progression happens separately in fortnightly updates.
        """
        # Determine treatment
        should_treat = self.protocol.should_treat(patient, visit_date)
        
        # Record measured vision (with noise)
        actual_vision = self.patient_actual_vision[patient.id]
        measurement_noise = random.gauss(0, 2.5)  # ±5 letter noise
        measured_vision = int(round(actual_vision + measurement_noise))
        measured_vision = max(0, min(100, measured_vision))
        
        # Check discontinuation (only at visits)
        should_discontinue = self._should_discontinue(patient, visit_date)
        
        if should_discontinue:
            patient.is_discontinued = True
            patient.discontinuation_date = visit_date
        
        # Record visit
        visit_record = {
            'date': visit_date,
            'disease_state': patient.current_state,
            'vision': measured_vision,
            'actual_vision': actual_vision,  # For analysis
            'treatment_given': should_treat and not should_discontinue,
            'days_since_last_injection': patient.days_since_last_injection_at(visit_date)
        }
        
        # Update patient state based on visit
        patient.visit_history.append(visit_record)
        
        if should_treat and not should_discontinue:
            patient.injection_count += 1
            patient._last_injection_date = visit_date
            return True
            
        return False
    
    def _create_patient(self, patient_id: str, enrollment_date: datetime) -> Patient:
        """
        Create a new patient for the simulation.
        
        Args:
            patient_id: Unique patient identifier
            enrollment_date: Date patient enters the simulation
            
        Returns:
            New Patient instance
        """
        baseline_vision = self._sample_baseline_vision()
        
        patient = Patient(
            patient_id=patient_id,
            baseline_vision=baseline_vision,
            visit_metadata_enhancer=self.visit_metadata_enhancer,
            enrollment_date=enrollment_date
        )
        
        return patient