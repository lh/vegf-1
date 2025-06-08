"""
Enhanced DES engine with cost tracking support.

This extends the DES engine to include cost metadata enhancement
for economic analysis while maintaining all clinical features.
"""

import heapq
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import Protocol
from simulation_v2.engines.abs_engine import SimulationResults

from .des_engine import DESEngine, Event, EventType


class DESEngineWithCosts(DESEngine):
    """
    Enhanced DES engine with cost tracking integration.
    
    Extends DES engine to support cost metadata enhancement
    while maintaining all clinical features.
    """
    
    def __init__(
        self,
        disease_model: DiseaseModel,
        protocol: Protocol,
        n_patients: int,
        seed: Optional[int] = None,
        visit_metadata_enhancer: Optional[Callable] = None
    ):
        """
        Initialize DES engine with cost tracking support.
        
        Args:
            disease_model: Disease state transition model
            protocol: Treatment protocol
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
            visit_metadata_enhancer: Function to enhance visit metadata for costs
        """
        super().__init__(disease_model, protocol, n_patients, seed)
        
        # Store the metadata enhancer
        self.visit_metadata_enhancer = visit_metadata_enhancer
    
    def run(self, duration_years: float, start_date: Optional[datetime] = None) -> SimulationResults:
        """
        Run the simulation with cost tracking.
        
        Args:
            duration_years: Simulation duration in years
            start_date: Simulation start date (default: 2024-01-01)
            
        Returns:
            SimulationResults with aggregate statistics
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)
            
        end_date = start_date + timedelta(days=int(duration_years * 365.25))
        
        # Initialize patients and schedule enrollments
        for i in range(self.n_patients):
            patient_id = f"P{i:04d}"
            
            # Schedule enrollment (staggered over first month)
            enrollment_day = random.randint(0, 28)
            enrollment_date = start_date + timedelta(days=enrollment_day)
            
            heapq.heappush(self.event_queue, Event(
                time=enrollment_date,
                patient_id=patient_id,
                event_type=EventType.ENROLLMENT
            ))
            
        # Process events
        total_injections = 0
        
        while self.event_queue and self.event_queue[0].time <= end_date:
            event = heapq.heappop(self.event_queue)
            
            if event.event_type == EventType.ENROLLMENT:
                # Create patient
                baseline_vision = self._sample_baseline_vision()
                patient = Patient(event.patient_id, baseline_vision)
                
                # Add metadata enhancer to patient if available
                if self.visit_metadata_enhancer:
                    patient.visit_metadata_enhancer = self.visit_metadata_enhancer
                    
                self.patients[event.patient_id] = patient
                
                # Schedule first visit
                heapq.heappush(self.event_queue, Event(
                    time=event.time,
                    patient_id=event.patient_id,
                    event_type=EventType.VISIT
                ))
                
            elif event.event_type == EventType.VISIT:
                patient = self.patients[event.patient_id]
                
                if patient.is_discontinued:
                    continue
                    
                # Disease progression
                days_since = patient.days_since_last_injection_at(event.time)
                new_state = self.disease_model.progress(
                    patient.current_state,
                    days_since_injection=days_since
                )
                
                # Treatment decision
                should_treat = self.protocol.should_treat(patient, event.time)
                
                # Vision change
                vision_change = self._calculate_vision_change(
                    patient.current_state,
                    new_state,
                    should_treat
                )
                new_vision = max(0, min(100, patient.current_vision + vision_change))
                
                # Prepare visit data for enhancement
                visit_data = {
                    'date': event.time,
                    'disease_state': new_state,
                    'treatment_given': should_treat,
                    'vision': new_vision,
                    'visit_number': len(patient.visit_history) + 1,
                    'protocol_name': self.protocol.name if hasattr(self.protocol, 'name') else 'Unknown'
                }
                
                # Record visit with enhanced metadata
                self._record_enhanced_visit(
                    patient, visit_data, event.time, new_state, should_treat, new_vision
                )
                
                if should_treat:
                    total_injections += 1
                    
                # Check discontinuation
                if self._should_discontinue(patient, event.time):
                    patient.discontinue(event.time, "planned")
                else:
                    # Schedule next visit
                    next_visit_date = self.protocol.next_visit_date(
                        patient, event.time, should_treat
                    )
                    
                    if next_visit_date <= end_date:
                        heapq.heappush(self.event_queue, Event(
                            time=next_visit_date,
                            patient_id=event.patient_id,
                            event_type=EventType.VISIT
                        ))
                        
        # Calculate final statistics
        final_visions = [p.current_vision for p in self.patients.values()]
        discontinued = sum(1 for p in self.patients.values() if p.is_discontinued)
        
        return SimulationResults(
            total_injections=total_injections,
            patient_histories=self.patients,
            final_vision_mean=sum(final_visions) / len(final_visions) if final_visions else 0,
            final_vision_std=self._calculate_std(final_visions),
            discontinuation_rate=discontinued / len(self.patients) if self.patients else 0
        )
    
    def _record_enhanced_visit(
        self,
        patient: Patient,
        visit_data: Dict[str, Any],
        date: datetime,
        disease_state: 'DiseaseState',
        treatment_given: bool,
        vision: int
    ) -> None:
        """
        Record visit with metadata enhancement support.
        
        Args:
            patient: Patient object
            visit_data: Visit data for enhancement
            date: Visit date
            disease_state: Current disease state
            treatment_given: Whether treatment was given
            vision: Current vision
        """
        # Create base visit record
        visit_record = {
            'date': date,
            'disease_state': disease_state,
            'treatment_given': treatment_given,
            'vision': vision
        }
        
        # Apply metadata enhancement if available
        if self.visit_metadata_enhancer:
            # Create enhanced record
            enhanced_record = self.visit_metadata_enhancer(visit_record.copy(), visit_data, patient)
            
            # Update patient's visit history with enhanced record
            patient.visit_history.append(enhanced_record)
            
            # Update patient state
            patient.current_state = disease_state
            patient.current_vision = vision
            
            # Update first visit date if needed
            if patient.first_visit_date is None:
                patient.first_visit_date = date
            
            # Update injection tracking
            if treatment_given:
                patient.injection_count += 1
                patient._last_injection_date = date
        else:
            # Fall back to standard recording
            patient.record_visit(date, disease_state, treatment_given, vision)