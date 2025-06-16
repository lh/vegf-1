"""
Agent-Based Simulation (ABS) engine for AMD simulation V2.

In ABS, each patient is an autonomous agent that:
- Maintains their own state
- Makes decisions based on protocol
- Progresses through disease states
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass

from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import Protocol
from simulation_v2.models.baseline_vision_distributions import DistributionFactory, BaselineVisionDistribution


@dataclass
class SimulationResults:
    """Results from a simulation run."""
    total_injections: int
    patient_histories: Dict[str, Patient]
    final_vision_mean: float
    final_vision_std: float
    discontinuation_rate: float
    
    # Aliases for test compatibility
    @property
    def mean_final_vision(self) -> float:
        """Alias for final_vision_mean."""
        return self.final_vision_mean
        
    @property
    def patient_count(self) -> int:
        """Number of patients in simulation."""
        return len(self.patient_histories)
    

class ABSEngine:
    """
    Agent-Based Simulation engine.
    
    Each patient is simulated as an independent agent with:
    - Individual disease progression
    - Protocol-based treatment decisions
    - Vision outcomes
    """
    
    def __init__(
        self,
        disease_model: DiseaseModel,
        protocol: Protocol,
        n_patients: int = None,
        patient_arrival_rate: Optional[float] = None,
        seed: Optional[int] = None,
        visit_metadata_enhancer: Optional[Callable] = None,
        baseline_vision_distribution: Optional[BaselineVisionDistribution] = None
    ):
        """
        Initialize ABS engine.
        
        Args:
            disease_model: Disease state transition model
            protocol: Treatment protocol
            n_patients: Total number of patients (for Fixed Total Mode)
            patient_arrival_rate: Patients per week (for Constant Rate Mode)
            seed: Random seed for reproducibility
            visit_metadata_enhancer: Optional function to enhance visit metadata
            baseline_vision_distribution: Optional distribution for baseline vision
            
        Note: Either n_patients or patient_arrival_rate must be specified, not both.
        """
        self.disease_model = disease_model
        self.protocol = protocol
        self.visit_metadata_enhancer = visit_metadata_enhancer
        
        # Set baseline vision distribution (default to normal if not specified)
        if baseline_vision_distribution is None:
            from simulation_v2.models.baseline_vision_distributions import NormalDistribution
            self.baseline_vision_distribution = NormalDistribution()
        else:
            self.baseline_vision_distribution = baseline_vision_distribution
        
        # Validate recruitment mode
        if (n_patients is None) == (patient_arrival_rate is None):
            raise ValueError("Must specify either n_patients (Fixed Total Mode) or patient_arrival_rate (Constant Rate Mode), not both")
            
        self.n_patients = n_patients
        self.patient_arrival_rate = patient_arrival_rate
        self.is_fixed_total_mode = n_patients is not None
        
        # Set random seeds
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        # Initialize empty patient dictionary - patients will be created on arrival
        self.patients: Dict[str, Patient] = {}
        self.patient_arrival_schedule: List[Tuple[datetime, str]] = []
        self.enrollment_dates: Dict[str, datetime] = {}
            
    def _sample_baseline_vision(self) -> int:
        """
        Sample baseline vision from the configured distribution.
        
        Returns vision in ETDRS letters (0-100).
        """
        return self.baseline_vision_distribution.sample()
        
    def _generate_arrival_schedule(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, str]]:
        """
        Generate patient arrival times using Poisson process.
        
        Args:
            start_date: Simulation start date
            end_date: Simulation end date
            
        Returns:
            List of (arrival_datetime, patient_id) tuples
        """
        duration_days = (end_date - start_date).days
        
        # Handle edge case of zero patients
        if self.is_fixed_total_mode and self.n_patients == 0:
            return []
            
        if self.is_fixed_total_mode:
            # Fixed Total Mode: distribute n_patients across duration
            # Calculate arrival rate to achieve target total
            arrival_rate_per_day = self.n_patients / duration_days
            # Generate extra to ensure we hit target (will stop at n_patients)
            expected_patients = int(self.n_patients * 1.3)  # 30% buffer
        else:
            # Constant Rate Mode: use specified weekly rate
            arrival_rate_per_day = self.patient_arrival_rate / 7.0
            expected_patients = int(arrival_rate_per_day * duration_days * 1.2)  # 20% buffer
            
        # Generate inter-arrival times using exponential distribution
        # This creates a Poisson process
        mean_interarrival_days = 1.0 / arrival_rate_per_day
        interarrival_times = np.random.exponential(mean_interarrival_days, size=expected_patients)
        
        # Convert to arrival times
        arrivals = []
        current_time = start_date
        patient_num = 0
        
        for interval in interarrival_times:
            current_time += timedelta(days=interval)
            if current_time >= end_date:
                break
                
            patient_id = f"P{patient_num:04d}"
            arrivals.append((current_time, patient_id))
            patient_num += 1
            
            # For Fixed Total Mode, stop when we reach target
            if self.is_fixed_total_mode and patient_num >= self.n_patients:
                break
                
        return arrivals
        
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
        
        # Generate patient arrival schedule
        self.patient_arrival_schedule = self._generate_arrival_schedule(start_date, end_date)
        
        # Schedule visits for existing and arriving patients
        visit_schedule: Dict[str, datetime] = {}
            
        # Run simulation
        current_date = start_date
        total_injections = 0
        arrival_index = 0  # Track position in arrival schedule
        
        while current_date <= end_date:
            # Process new patient arrivals for today
            while (arrival_index < len(self.patient_arrival_schedule) and 
                   self.patient_arrival_schedule[arrival_index][0].date() <= current_date.date()):
                arrival_date, patient_id = self.patient_arrival_schedule[arrival_index]
                
                # Create new patient
                baseline_vision = self._sample_baseline_vision()
                patient = Patient(
                    patient_id,
                    baseline_vision,
                    visit_metadata_enhancer=self.visit_metadata_enhancer,
                    enrollment_date=arrival_date
                )
                self.patients[patient_id] = patient
                self.enrollment_dates[patient_id] = arrival_date
                
                # Schedule initial visit for start of next day after enrollment
                # This ensures visit time is after enrollment time
                next_day = arrival_date.date() + timedelta(days=1)
                visit_schedule[patient_id] = datetime.combine(next_day, datetime.min.time())
                
                arrival_index += 1
            
            # Process patients scheduled for today
            patients_today = [
                pid for pid, visit_date in visit_schedule.items()
                if visit_date.date() == current_date.date()
            ]
            
            for patient_id in patients_today:
                patient = self.patients[patient_id]
                
                if patient.is_discontinued:
                    # Skip discontinued patients
                    continue
                    
                # Disease progression
                new_state = self.disease_model.progress(
                    patient.current_state,
                    days_since_injection=patient.days_since_last_injection_at(current_date)
                )
                
                # Treatment decision
                should_treat = self.protocol.should_treat(patient, current_date)
                
                # Vision change (simplified model)
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
                
                if should_treat:
                    total_injections += 1
                    
                # Schedule next visit
                next_visit = self.protocol.next_visit_date(patient, current_date, should_treat)
                visit_schedule[patient_id] = next_visit
                
                # Check for discontinuation (simplified)
                if self._should_discontinue(patient, current_date):
                    patient.discontinue(current_date, "planned")
                    
            # Advance time
            current_date += timedelta(days=1)
            
        # Calculate final statistics
        final_visions = [p.current_vision for p in self.patients.values()]
        discontinued = sum(1 for p in self.patients.values() if p.is_discontinued)
        actual_patient_count = len(self.patients)
        
        # Handle edge case of zero patients
        if actual_patient_count == 0:
            final_vision_mean = 0.0
            final_vision_std = 0.0
            discontinuation_rate = 0.0
        else:
            final_vision_mean = sum(final_visions) / len(final_visions)
            final_vision_std = self._calculate_std(final_visions)
            discontinuation_rate = discontinued / actual_patient_count
        
        return SimulationResults(
            total_injections=total_injections,
            patient_histories=self.patients,
            final_vision_mean=final_vision_mean,
            final_vision_std=final_vision_std,
            discontinuation_rate=discontinuation_rate
        )
        
    def _calculate_vision_change(
        self, 
        old_state: 'DiseaseState',
        new_state: 'DiseaseState',
        treated: bool
    ) -> int:
        """
        Simple vision change model.
        
        - Stable/treated: small improvement (0-2 letters)
        - Active/treated: maintain or small loss (-1 to 1 letters)
        - Active/untreated: moderate loss (-3 to -1 letters)
        - Highly active/untreated: severe loss (-5 to -2 letters)
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
        Simple discontinuation logic.
        
        - Poor vision (< 35 letters): higher chance
        - Many injections (> 20): moderate chance
        - Long treatment (> 3 years): small chance
        """
        if patient.current_vision < 35:
            return random.random() < 0.1  # 10% chance per visit
        elif patient.injection_count > 20:
            return random.random() < 0.02  # 2% chance per visit
        elif len(patient.visit_history) > 36:  # ~3 years monthly
            return random.random() < 0.01  # 1% chance per visit
        return False
        
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5