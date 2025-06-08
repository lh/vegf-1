"""
Discrete Event Simulation (DES) engine for AMD simulation V2.

In DES, the simulation advances by processing events in chronological order:
- Visit events
- State change events  
- Decision events
"""

import heapq
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import Protocol
from simulation_v2.engines.abs_engine import SimulationResults


class EventType(Enum):
    """Types of events in the simulation."""
    VISIT = "visit"
    ENROLLMENT = "enrollment"
    

@dataclass
class Event:
    """An event in the simulation."""
    time: datetime
    patient_id: str
    event_type: EventType
    
    def __lt__(self, other):
        """Events are ordered by time."""
        return self.time < other.time


class DESEngine:
    """
    Discrete Event Simulation engine.
    
    The simulation maintains an event queue and processes events
    in chronological order. This is more efficient for sparse events.
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
        Initialize DES engine.
        
        Args:
            disease_model: Disease state transition model
            protocol: Treatment protocol
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
            visit_metadata_enhancer: Optional function to enhance visit metadata
        """
        self.disease_model = disease_model
        self.protocol = protocol
        self.n_patients = n_patients
        self.visit_metadata_enhancer = visit_metadata_enhancer
        
        if seed is not None:
            random.seed(seed)
            
        # Initialize patients
        self.patients: Dict[str, Patient] = {}
        self.event_queue: List[Event] = []
        
    def _sample_baseline_vision(self) -> int:
        """
        Sample baseline vision from realistic distribution.
        
        Returns vision in ETDRS letters (0-100).
        """
        vision = int(random.gauss(70, 10))
        return max(20, min(90, vision))
        
    def run(self, duration_years: float, start_date: Optional[datetime] = None) -> SimulationResults:
        """
        Run the simulation.
        
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
                # Create patient with optional metadata enhancer
                baseline_vision = self._sample_baseline_vision()
                patient = Patient(
                    event.patient_id, 
                    baseline_vision,
                    visit_metadata_enhancer=self.visit_metadata_enhancer
                )
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
                
                # Record visit
                patient.record_visit(
                    date=event.time,
                    disease_state=new_state,
                    treatment_given=should_treat,
                    vision=new_vision
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
        
    def _calculate_vision_change(
        self, 
        old_state: 'DiseaseState',
        new_state: 'DiseaseState',
        treated: bool
    ) -> int:
        """
        Simple vision change model (same as ABS for consistency).
        """
        from simulation_v2.core.disease_model import DiseaseState
        
        if new_state == DiseaseState.STABLE:
            return random.randint(0, 2)
        elif new_state == DiseaseState.ACTIVE:
            if treated:
                return random.randint(-1, 1)
            else:
                return random.randint(-3, -1)
        elif new_state == DiseaseState.HIGHLY_ACTIVE:
            if treated:
                return random.randint(-2, 0)
            else:
                return random.randint(-5, -2)
        else:  # NAIVE
            return 0
            
    def _should_discontinue(self, patient: Patient, current_date: datetime) -> bool:
        """
        Simple discontinuation logic (same as ABS).
        """
        if patient.current_vision < 35:
            return random.random() < 0.1
        elif patient.injection_count > 20:
            return random.random() < 0.02
        elif len(patient.visit_history) > 36:
            return random.random() < 0.01
        return False
        
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5