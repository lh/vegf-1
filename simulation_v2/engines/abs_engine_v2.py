"""
Enhanced ABS engine with V2 discontinuation support.

This extends the base ABS engine to include the full discontinuation
profile system with 6 categories and monitoring/retreatment logic.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseModel, DiseaseState
from simulation_v2.core.protocol import Protocol
from simulation_v2.core.discontinuation_manager import V2DiscontinuationManager
from simulation_v2.core.discontinuation_profile import DiscontinuationProfile

from .abs_engine import ABSEngine, SimulationResults


class ABSEngineV2(ABSEngine):
    """
    Enhanced ABS engine with V2 discontinuation support.
    
    Extends the basic ABS engine to include:
    - 6 discontinuation categories
    - Monitoring schedules
    - Retreatment logic
    - Configurable discontinuation profiles
    """
    
    def __init__(
        self,
        disease_model: DiseaseModel,
        protocol: Protocol,
        n_patients: int,
        seed: Optional[int] = None,
        discontinuation_profile: Optional[DiscontinuationProfile] = None
    ):
        """
        Initialize enhanced ABS engine.
        
        Args:
            disease_model: Disease state transition model
            protocol: Treatment protocol
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
            discontinuation_profile: Profile for discontinuation behavior
        """
        super().__init__(disease_model, protocol, n_patients, seed)
        
        # Initialize discontinuation manager
        self.discontinuation_manager = V2DiscontinuationManager(discontinuation_profile)
        
        # Track monitoring visits
        self.monitoring_schedule: Dict[str, List[datetime]] = {}
        
    def run(self, duration_years: float, start_date: Optional[datetime] = None) -> SimulationResults:
        """
        Run the simulation with enhanced discontinuation.
        
        Args:
            duration_years: Simulation duration in years
            start_date: Simulation start date (default: 2024-01-01)
            
        Returns:
            SimulationResults with aggregate statistics
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)
            
        end_date = start_date + timedelta(days=int(duration_years * 365.25))
        
        # Schedule initial visits for all patients
        visit_schedule: Dict[str, datetime] = {}
        monitoring_schedule: Dict[str, List[datetime]] = {}
        
        for patient_id in self.patients:
            # Stagger initial visits across first month
            days_offset = random.randint(0, 28)
            visit_schedule[patient_id] = start_date + timedelta(days=days_offset)
            monitoring_schedule[patient_id] = []
            
        # Run simulation
        current_date = start_date
        total_injections = 0
        
        while current_date <= end_date:
            # Process treatment visits scheduled for today
            patients_today = [
                pid for pid, visit_date in visit_schedule.items()
                if visit_date.date() == current_date.date()
            ]
            
            for patient_id in patients_today:
                patient = self.patients[patient_id]
                
                if patient.is_discontinued:
                    # Skip regular visits for discontinued patients
                    continue
                    
                # Process treatment visit
                injected = self._process_treatment_visit(
                    patient, current_date
                )
                
                if injected:
                    total_injections += 1
                    
                # Schedule next visit
                next_visit = self.protocol.next_visit_date(patient, current_date, injected)
                visit_schedule[patient_id] = next_visit
                
                # Get current interval in weeks
                if patient.days_since_last_injection_at(current_date) is not None:
                    current_interval_weeks = patient.days_since_last_injection_at(current_date) // 7
                else:
                    current_interval_weeks = 4  # Default loading phase
                
                # Check for discontinuation using V2 manager
                is_stable = (patient.current_state == DiseaseState.STABLE)
                should_discontinue, disc_type, reason = self.discontinuation_manager.evaluate_discontinuation(
                    patient, current_date, current_interval_weeks, is_stable
                )
                
                if should_discontinue:
                    self.discontinuation_manager.process_discontinuation(
                        patient, current_date, disc_type, reason
                    )
                    # Add monitoring visits to schedule
                    monitoring_schedule[patient_id] = patient.monitoring_schedule
                    
            # Process monitoring visits scheduled for today
            monitoring_today = []
            for patient_id, monitoring_dates in monitoring_schedule.items():
                if any(date.date() == current_date.date() for date in monitoring_dates):
                    monitoring_today.append(patient_id)
                    # Remove the processed date
                    monitoring_schedule[patient_id] = [
                        d for d in monitoring_dates if d.date() != current_date.date()
                    ]
            
            for patient_id in monitoring_today:
                patient = self.patients[patient_id]
                self._process_monitoring_visit(patient, current_date)
                
            # Advance time
            current_date += timedelta(days=1)
            
        # Calculate final statistics including discontinuation breakdown
        final_visions = [p.current_vision for p in self.patients.values()]
        discontinued = sum(1 for p in self.patients.values() if p.is_discontinued)
        
        # Handle edge case of zero patients
        if self.n_patients == 0:
            final_vision_mean = 0.0
            final_vision_std = 0.0
            discontinuation_rate = 0.0
        else:
            final_vision_mean = sum(final_visions) / len(final_visions)
            final_vision_std = self._calculate_std(final_visions)
            discontinuation_rate = discontinued / self.n_patients
        
        # Create results with discontinuation statistics
        results = SimulationResults(
            total_injections=total_injections,
            patient_histories=self.patients,
            final_vision_mean=final_vision_mean,
            final_vision_std=final_vision_std,
            discontinuation_rate=discontinuation_rate
        )
        
        # Add discontinuation statistics as additional attribute
        results.discontinuation_stats = self.discontinuation_manager.get_statistics()
        
        return results
    
    def _process_treatment_visit(
        self, 
        patient: Patient, 
        current_date: datetime
    ) -> bool:
        """
        Process a regular treatment visit.
        
        Args:
            patient: Patient to process
            current_date: Current simulation date
            
        Returns:
            Whether injection was given
        """
        # Disease progression
        new_state = self.disease_model.progress(
            patient.current_state,
            days_since_injection=patient.days_since_last_injection_at(current_date)
        )
        
        # Treatment decision
        should_treat = self.protocol.should_treat(patient, current_date)
        
        # Vision change
        vision_change = self._calculate_vision_change(
            patient.current_state,
            new_state,
            should_treat
        )
        new_vision = max(0, min(100, patient.current_vision + vision_change))
        
        # Record visit
        patient.record_visit(
            date=current_date,
            disease_state=new_state,
            treatment_given=should_treat,
            vision=new_vision
        )
        
        return should_treat
    
    def _process_monitoring_visit(
        self,
        patient: Patient,
        current_date: datetime
    ) -> None:
        """
        Process a monitoring visit for discontinued patient.
        
        Args:
            patient: Patient to monitor
            current_date: Current simulation date
        """
        # Disease can still progress
        new_state = self.disease_model.progress(
            patient.current_state,
            days_since_injection=patient.days_since_last_injection_at(current_date)
        )
        
        # Vision typically declines without treatment
        vision_change = self._calculate_vision_change(
            patient.current_state,
            new_state,
            treated=False
        )
        new_vision = max(0, min(100, patient.current_vision + vision_change))
        
        # Record monitoring visit
        patient.record_visit(
            date=current_date,
            disease_state=new_state,
            treatment_given=False,
            vision=new_vision
        )
        
        # Check for retreatment
        has_fluid = (new_state in [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE])
        should_retreat, retreat_reason = self.discontinuation_manager.evaluate_retreatment(
            patient, has_fluid, current_date
        )
        
        if should_retreat:
            patient.restart_treatment(current_date)
            # Schedule next treatment visit
            # This would need to be passed back to the main loop
            # For now, we'll handle this in the next iteration
    
    def _should_discontinue(self, patient: Patient, current_date: datetime) -> bool:
        """
        Override parent method - discontinuation is handled by V2 manager.
        
        This method is not used in V2 engine.
        """
        return False