"""
ABS engine with enhanced cost tracking integration.

This module extends the standard ABS engine to include:
- Visit type classification
- Workload tracking
- NHS HRG-aligned cost calculations
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..engines.abs_engine import ABSEngine, SimulationResults
from ..core.patient import Patient
from ..core.disease_model import DiseaseModel
from ..core.protocol import Protocol
from ..protocols.protocol_spec import ProtocolSpecification
from ..clinical_improvements import ClinicalImprovements
from ..economics.cost_config import CostConfig
from ..economics.enhanced_cost_tracker import EnhancedCostTracker, VisitType


class ABSEngineWithEnhancedCosts(ABSEngine):
    """ABS engine with integrated enhanced cost tracking."""
    
    def __init__(self, 
                 disease_model: DiseaseModel,
                 protocol: Protocol,
                 protocol_spec: ProtocolSpecification,
                 n_patients: int,
                 seed: Optional[int] = None,
                 clinical_improvements: Optional[ClinicalImprovements] = None,
                 cost_config: Optional[CostConfig] = None,
                 drug_type: str = "eylea_2mg_biosimilar"):
        """
        Initialize engine with cost tracking.
        
        Args:
            disease_model: Disease progression model
            protocol: Treatment protocol
            protocol_spec: Protocol specification
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
            clinical_improvements: Optional clinical improvements wrapper
            cost_config: Cost configuration (if None, no cost tracking)
            drug_type: Active drug for cost calculations
        """
        # Initialize parent ABS engine
        super().__init__(disease_model, protocol, n_patients, seed=seed)
        
        self.protocol_spec = protocol_spec
        self.clinical_improvements = clinical_improvements
        
        # Initialize cost tracking if config provided
        self.cost_tracker = None
        if cost_config:
            protocol_type = "fixed" if protocol_spec.protocol_type == "fixed" else "treat_and_extend"
            self.cost_tracker = EnhancedCostTracker(cost_config, protocol_type)
            self.cost_tracker.set_drug_type(drug_type)
        
        # Track annual assessments for T&T
        self.annual_assessment_months = [12, 24, 36, 48, 60]  # Annual assessments
    
    def _should_track_costs(self) -> bool:
        """Check if cost tracking is enabled."""
        return self.cost_tracker is not None
    
    def _determine_if_annual_assessment(self, patient: Patient, current_date: datetime) -> bool:
        """
        Determine if this visit should be an annual assessment (T&T only).
        
        Args:
            patient: Patient object
            current_date: Current simulation date
            
        Returns:
            True if this should be an annual assessment
        """
        if self.protocol_spec.protocol_type != "fixed":
            return False
        
        # Calculate months since enrollment
        months_since_start = (current_date - patient.enrollment_date).days / 30.44
        
        # Check if we're near an annual mark (within 2 weeks)
        for annual_month in self.annual_assessment_months:
            if abs(months_since_start - annual_month) < 0.5:
                return True
        
        return False
    
    def _record_visit_cost(self, patient: Patient, visit_date: datetime, 
                          treatment_given: bool, vision: float) -> None:
        """
        Record cost and workload for a visit.
        
        Args:
            patient: Patient object
            visit_date: Date of visit
            treatment_given: Whether injection was administered
            vision: Current visual acuity
        """
        if not self._should_track_costs():
            return
        
        # Determine visit type
        visit_number = len(patient.visit_history)
        is_annual = self._determine_if_annual_assessment(patient, visit_date)
        
        visit_type = self.cost_tracker.determine_visit_type(
            patient, visit_number, is_annual
        )
        
        # Record the visit
        self.cost_tracker.record_visit(
            patient_id=patient.id,
            visit_date=visit_date,
            visit_type=visit_type,
            injection_given=treatment_given,
            vision=vision
        )
    
    def run(self, duration_years: float, start_date: Optional[datetime] = None) -> SimulationResults:
        """
        Run simulation with cost tracking.
        
        This overrides the parent's run method to add cost tracking
        for each patient visit.
        
        Args:
            duration_years: Simulation duration in years
            start_date: Simulation start date (default: 2024-01-01)
            
        Returns:
            SimulationResults with cost tracking data
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
                next_day = arrival_date.date() + timedelta(days=1)
                visit_schedule[patient_id] = datetime.combine(next_day, datetime.min.time())
                
                arrival_index += 1
            
            # Process patients scheduled for today
            patients_today = [
                patient_id for patient_id, visit_date in visit_schedule.items()
                if visit_date.date() == current_date.date()
            ]
            
            for patient_id in patients_today:
                patient = self.patients[patient_id]
                
                # Skip if patient is discontinued
                if patient.is_discontinued:
                    continue
                    
                # Get current disease state
                old_state = patient.disease_state
                
                # Treatment decision
                should_treat = self.protocol.should_treat(patient, current_date)
                
                # Disease progression
                new_state = self.disease_model.get_next_state(old_state, treated=should_treat)
                
                # Vision change
                vision_change = self._calculate_vision_change(old_state, new_state, should_treat)
                
                # Apply clinical improvements if available
                if self.clinical_improvements:
                    vision_change = self.clinical_improvements.adjust_vision_change(
                        patient, vision_change, len(patient.visit_history)
                    )
                
                new_vision = patient.current_vision + vision_change
                new_vision = max(0, min(100, new_vision))  # Clamp to valid range
                
                # Add visit
                patient.add_visit(
                    date=current_date,
                    disease_state=new_state,
                    treatment_given=should_treat,
                    vision=new_vision
                )
                
                if should_treat:
                    total_injections += 1
                
                # Record cost if tracking enabled
                if self._should_track_costs():
                    self._record_visit_cost(
                        patient, 
                        current_date,
                        should_treat,
                        new_vision
                    )
                    
                # Schedule next visit
                next_visit = self.protocol.next_visit_date(patient, current_date, should_treat)
                visit_schedule[patient_id] = next_visit
                
                # Check for discontinuation
                if self.clinical_improvements:
                    if self.clinical_improvements.should_discontinue(
                        patient, len(patient.visit_history)
                    ):
                        reason = self.clinical_improvements.get_discontinuation_reason(patient)
                        patient.discontinue(current_date, reason)
                elif self._should_discontinue(patient, current_date):
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
        
        # Create base results
        base_results = SimulationResults(
            total_injections=total_injections,
            patient_histories=self.patients,
            final_vision_mean=final_vision_mean,
            final_vision_std=final_vision_std,
            discontinuation_rate=discontinuation_rate
        )
        
        # Add cost tracking data if enabled
        if self._should_track_costs():
            # Create enhanced results with cost data
            from ..models.results import SimulationResults as V2SimulationResults
            
            enhanced_results = V2SimulationResults(
                patient_histories=base_results.patient_histories,
                summary_stats={
                    'total_injections': base_results.total_injections,
                    'mean_final_vision': base_results.final_vision_mean,
                    'std_final_vision': base_results.final_vision_std,
                    'discontinuation_rate': base_results.discontinuation_rate,
                    'patient_count': len(base_results.patient_histories)
                },
                metadata={
                    'engine': 'ABS_with_enhanced_costs',
                    'n_patients': self.n_patients,
                    'duration_years': duration_years,
                    'protocol': self.protocol.__class__.__name__,
                    'disease_model': self.disease_model.__class__.__name__,
                    'has_cost_tracking': True,
                    'drug_type': self.cost_tracker.active_drug,
                    'storage_type': 'memory'
                }
            )
            
            # Add cost tracking objects
            enhanced_results.cost_tracker = self.cost_tracker
            enhanced_results.cost_effectiveness = self.cost_tracker.calculate_cost_effectiveness()
            enhanced_results.workload_summary = self.cost_tracker.get_workload_summary()
            
            return enhanced_results
            
        return base_results