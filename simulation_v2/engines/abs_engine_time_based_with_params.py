"""
Time-based ABS engine with full parameter-driven vision model.

This replaces all hardcoded values with parameters from configuration files.
Implements the complete vision model including:
- Bimodal vision loss (gradual + hemorrhage)
- Vision improvement mechanics
- Individual vision ceilings
- Treatment effect decay
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass

import yaml
from pathlib import Path
from simulation_v2.engines.abs_engine_time_based_with_specs import ABSEngineTimeBasedWithSpecs
from simulation_v2.core.patient import Patient
from simulation_v2.core.discontinuation_checker import DiscontinuationChecker
from simulation_v2.core.disease_model import DiseaseState


@dataclass
class PatientVisionState:
    """Track vision-related state for each patient."""
    actual_vision: float
    vision_ceiling: int
    is_improving: bool = False
    improvement_start_date: Optional[datetime] = None
    visits_below_threshold: int = 0


class ABSEngineTimeBasedWithParams(ABSEngineTimeBasedWithSpecs):
    """
    Time-based ABS engine with complete parameter-driven implementation.
    
    All values come from parameter files - no hardcoded constants.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with vision state tracking."""
        super().__init__(*args, **kwargs)
        self.patient_vision_states: Dict[str, PatientVisionState] = {}
        
        # Initialize discontinuation checker if we have the parameters
        self.discontinuation_checker = None
        if hasattr(self, 'discontinuation_params') and self.discontinuation_params:
            self.discontinuation_checker = DiscontinuationChecker(self.discontinuation_params)
        
        # Load demographics parameters
        self._load_demographics_parameters()
    
    def _load_demographics_parameters(self):
        """Load demographics parameters from parameter files."""
        # Try protocol-specific path first
        if hasattr(self, 'protocol_spec') and hasattr(self.protocol_spec, 'demographics_parameters_file'):
            params_path = Path(self.protocol_spec.source_file).parent / self.protocol_spec.demographics_parameters_file
            if params_path.exists():
                with open(params_path) as f:
                    self.demographics_params = yaml.safe_load(f)
                return
        
        # Fallback to default location
        default_path = Path(__file__).parent.parent.parent / 'protocols' / 'v2_time_based' / 'parameters' / 'demographics.yaml'
        if default_path.exists():
            with open(default_path) as f:
                self.demographics_params = yaml.safe_load(f)
        else:
            # No demographics parameters available
            self.demographics_params = None
    
    def _initialize_patient_vision(self, patient_id: str, patient: Patient, enrollment_date: datetime):
        """
        Initialize vision tracking for a new patient.
        
        Uses parameters from vision.yaml for all calculations.
        """
        baseline = float(patient.baseline_vision)
        
        # Calculate vision ceiling from parameters
        ceiling_params = self.vision_params['vision_ceilings']
        
        # Individual ceiling based on baseline
        individual_ceiling = baseline * ceiling_params['baseline_ceiling_factor']
        
        # Apply absolute ceiling based on baseline range
        if baseline > ceiling_params['high_baseline_threshold']:
            absolute_ceiling = ceiling_params['absolute_ceiling_high_baseline']
        elif baseline < ceiling_params['low_baseline_threshold']:
            absolute_ceiling = ceiling_params['absolute_ceiling_low_baseline']
        else:
            absolute_ceiling = ceiling_params['absolute_ceiling_default']
        
        # Take minimum of individual and absolute ceiling
        vision_ceiling = int(min(individual_ceiling, absolute_ceiling))
        
        # Create vision state
        self.patient_vision_states[patient_id] = PatientVisionState(
            actual_vision=baseline,
            vision_ceiling=vision_ceiling
        )
        
        # Also update the legacy tracking for compatibility
        self.patient_actual_vision[patient_id] = baseline
        self.patient_vision_ceiling[patient_id] = vision_ceiling
    
    def _update_patient_vision(self, patient_id: str, patient: Patient, current_date: datetime):
        """
        Complete vision update implementation using all parameters.
        
        Implements:
        - Bimodal vision loss (gradual + hemorrhage)
        - Vision improvement mechanics
        - Treatment effect decay
        - Individual ceilings
        """
        vision_state = self.patient_vision_states[patient_id]
        
        # Calculate treatment effect
        days_since_injection = patient.days_since_last_injection_at(current_date)
        treatment_effect = self._calculate_treatment_effect(days_since_injection)
        
        # Check improvement eligibility and status
        self._update_improvement_status(patient_id, patient, current_date, treatment_effect)
        
        # Calculate vision change
        if vision_state.is_improving:
            vision_change = self._calculate_improvement(patient, vision_state)
        else:
            # Bimodal loss: gradual decline + hemorrhage risk
            gradual_change = self._calculate_gradual_decline(patient, treatment_effect)
            hemorrhage_loss = self._check_hemorrhage(patient, days_since_injection)
            vision_change = gradual_change - hemorrhage_loss
        
        # Apply change with bounds
        new_vision = vision_state.actual_vision + vision_change
        new_vision = min(new_vision, vision_state.vision_ceiling)
        
        # Get minimum vision from parameters (should be 0, but parameterized)
        min_vision = self.vision_params['vision_measurement']['min_measurable_vision']
        new_vision = max(min_vision, new_vision)
        
        # Update state
        vision_state.actual_vision = new_vision
        self.patient_actual_vision[patient_id] = new_vision
    
    def _calculate_treatment_effect(self, days_since_injection: Optional[int]) -> float:
        """Calculate treatment efficacy with decay using parameters."""
        if days_since_injection is None:
            return 0.0
        
        decay_params = self.vision_params['treatment_effect_decay']
        
        if days_since_injection <= decay_params['full_effect_duration_days']:
            # Full effect period
            return decay_params['effect_at_gradual_start']
        
        elif days_since_injection <= decay_params['gradual_decline_end_days']:
            # Gradual decline phase
            progress = (days_since_injection - decay_params['full_effect_duration_days']) / (
                decay_params['gradual_decline_end_days'] - decay_params['full_effect_duration_days']
            )
            return decay_params['effect_at_gradual_start'] - (
                progress * (decay_params['effect_at_gradual_start'] - decay_params['effect_at_faster_start'])
            )
        
        elif days_since_injection <= decay_params['faster_decline_end_days']:
            # Faster decline phase
            progress = (days_since_injection - decay_params['gradual_decline_end_days']) / (
                decay_params['faster_decline_end_days'] - decay_params['gradual_decline_end_days']
            )
            return decay_params['effect_at_faster_start'] - (
                progress * (decay_params['effect_at_faster_start'] - decay_params['effect_at_minimal_start'])
            )
        
        else:
            # Minimal effect
            additional_days = days_since_injection - decay_params['faster_decline_end_days']
            misc_params = self.vision_params.get('misc_parameters', {})
            decay_rate = misc_params.get('minimal_effect_decay_rate', 0.25)
            remaining_effect = decay_params['effect_at_minimal_start'] - (additional_days / decay_params['faster_decline_end_days']) * decay_rate
            return max(0.0, remaining_effect)
    
    def _update_improvement_status(self, patient_id: str, patient: Patient, current_date: datetime, treatment_effect: float):
        """Update whether patient is in improvement phase."""
        vision_state = self.patient_vision_states[patient_id]
        improvement_params = self.vision_params['vision_improvement']
        
        # Check improvement eligibility
        can_improve = (
            patient.injection_count <= improvement_params['max_treatments_for_improvement'] and
            (patient.injection_count == 1 or  # First treatment
             (patient.days_since_last_injection_at(current_date) or 0) > improvement_params['treatment_gap_for_improvement_days'])
        )
        
        # Start improvement if eligible
        misc_params = self.vision_params.get('misc_parameters', {})
        effect_threshold = misc_params.get('treatment_effect_threshold', 0.5)
        if not vision_state.is_improving and can_improve and treatment_effect > effect_threshold:
            state_name = patient.current_state.name
            if state_name in improvement_params['improvement_probability']:
                if random.random() < improvement_params['improvement_probability'][state_name]:
                    vision_state.is_improving = True
                    vision_state.improvement_start_date = current_date
        
        # Check if improvement window expired
        if vision_state.is_improving and vision_state.improvement_start_date:
            days_improving = (current_date - vision_state.improvement_start_date).days
            misc_params = self.vision_params.get('misc_parameters', {})
            fortnights_per_day = misc_params.get('fortnights_per_day', 0.0714285714)
            fortnights_improving = days_improving * fortnights_per_day
            if fortnights_improving > improvement_params['max_improvement_duration_fortnights']:
                vision_state.is_improving = False
                vision_state.improvement_start_date = None
    
    def _calculate_improvement(self, patient: Patient, vision_state: PatientVisionState) -> float:
        """Calculate vision improvement when in improvement phase."""
        improvement_params = self.vision_params['vision_improvement']['improvement_rate']
        state_name = patient.current_state.name
        
        if state_name in improvement_params:
            params = improvement_params[state_name]
            improvement = random.gauss(params['mean'], params['std'])
            return max(0, improvement)  # Only positive changes during improvement
        
        return 0.0
    
    def _calculate_gradual_decline(self, patient: Patient, treatment_effect: float) -> float:
        """Calculate gradual vision decline with treatment effect."""
        decline_params = self.vision_params['vision_decline_fortnightly']
        state_name = patient.current_state.name
        
        if state_name not in decline_params:
            # Shouldn't happen, but safe fallback
            return 0.0
        
        state_params = decline_params[state_name]
        untreated = state_params['untreated']
        treated = state_params['treated']
        
        # Interpolate based on treatment effect
        mean = untreated['mean'] * (1 - treatment_effect) + treated['mean'] * treatment_effect
        std = untreated['std'] * (1 - treatment_effect) + treated['std'] * treatment_effect
        
        return random.gauss(mean, std)
    
    def _check_hemorrhage(self, patient: Patient, days_since_injection: Optional[int]) -> float:
        """Check for catastrophic hemorrhage event."""
        # Only risk in active disease states
        if patient.current_state.name not in ['ACTIVE', 'HIGHLY_ACTIVE']:
            return 0.0
        
        hemorrhage_params = self.vision_params['hemorrhage_risk']
        misc_params = self.vision_params.get('misc_parameters', {})
        default_days = misc_params.get('no_injection_default_days', 999)
        days_untreated = days_since_injection if days_since_injection is not None else default_days
        
        # Determine risk level based on time since treatment
        if days_untreated <= hemorrhage_params['treated_threshold_days']:
            base_risk = hemorrhage_params['risk_treated_fortnightly']
        elif days_untreated <= hemorrhage_params['medium_gap_threshold_days']:
            base_risk = hemorrhage_params['risk_medium_gap_fortnightly']
        else:
            base_risk = hemorrhage_params['risk_long_gap_fortnightly']
        
        # Apply multiplier for highly active disease
        if patient.current_state.name == 'HIGHLY_ACTIVE':
            base_risk *= hemorrhage_params['highly_active_multiplier']
        
        # Check if hemorrhage occurs
        if random.random() < base_risk:
            # Catastrophic vision loss
            loss = random.uniform(
                hemorrhage_params['hemorrhage_loss_min'],
                hemorrhage_params['hemorrhage_loss_max']
            )
            return loss
        
        return 0.0
    
    def _process_visit(self, patient: Patient, visit_date: datetime) -> bool:
        """
        Process visit with parameterized vision measurement.
        
        Override to use vision parameters for measurement noise.
        """
        # Determine treatment
        should_treat = self.protocol.should_treat(patient, visit_date)
        
        # Record measured vision with parameterized noise
        actual_vision = self.patient_actual_vision[patient.id]
        
        # Get measurement parameters
        measurement_params = self.vision_params['vision_measurement']
        measurement_noise = random.gauss(0, measurement_params['measurement_noise_std'])
        
        measured_vision = int(round(actual_vision + measurement_noise))
        measured_vision = max(
            measurement_params['min_measurable_vision'],
            min(measurement_params['max_measurable_vision'], measured_vision)
        )
        
        # Check discontinuation using comprehensive checker
        if self.discontinuation_checker:
            # Calculate patient age if birth date is available
            patient_age = None
            if patient.birth_date:
                patient_age = (visit_date - patient.birth_date).days // 365
            elif patient.age_years is not None:
                # Age at enrollment + time in study
                years_in_study = (visit_date - patient.enrollment_date).days / 365.25
                patient_age = int(patient.age_years + years_in_study)
            
            # Check all discontinuation reasons
            disc_result = self.discontinuation_checker.check_discontinuation(
                patient=patient,
                current_date=visit_date,
                measured_vision=measured_vision,
                patient_age=patient_age
            )
            
            if disc_result.should_discontinue:
                patient.is_discontinued = True
                patient.discontinuation_date = visit_date
                patient.discontinuation_reason = disc_result.reason
                return False  # Don't treat if discontinuing
        else:
            # Fallback to simple vision check
            should_discontinue = self._check_vision_discontinuation(patient.id, measured_vision)
            
            if should_discontinue:
                patient.is_discontinued = True
                patient.discontinuation_date = visit_date
                patient.discontinuation_reason = 'poor_vision'
                return False  # Don't treat if discontinuing
        
        # Record visit
        visit_record = {
            'date': visit_date,
            'disease_state': patient.current_state,
            'vision': measured_vision,
            'actual_vision': actual_vision,
            'treatment_given': should_treat and not patient.is_discontinued,
            'days_since_last_injection': patient.days_since_last_injection_at(visit_date),
            'is_improving': self.patient_vision_states[patient.id].is_improving,
            'is_discontinuation_visit': patient.is_discontinued and patient.discontinuation_date == visit_date
        }
        
        # Update patient state
        patient.visit_history.append(visit_record)
        patient.current_vision = measured_vision
        
        # Update tracking counters after recording visit
        self._update_patient_tracking(patient, patient.current_state, measured_vision)
        
        if should_treat and not patient.is_discontinued:
            patient.injection_count += 1
            patient._last_injection_date = visit_date
            return True
        
        return False
    
    def _check_vision_discontinuation(self, patient_id: str, measured_vision: int) -> bool:
        """Check if patient should discontinue due to poor vision."""
        vision_state = self.patient_vision_states[patient_id]
        disc_params = self.vision_params['vision_floor_discontinuation']
        
        if measured_vision >= disc_params['vision_threshold']:
            # Reset counter if above threshold
            vision_state.visits_below_threshold = 0
            return False
        
        # Below threshold
        vision_state.visits_below_threshold += 1
        
        # Check if grace period exceeded
        if vision_state.visits_below_threshold >= disc_params['grace_period_visits']:
            # Probabilistic discontinuation
            if random.random() < disc_params['discontinuation_probability']:
                return True
        
        return False
    
    def _create_patient(self, patient_id: str, enrollment_date: datetime) -> Patient:
        """
        Create patient with age initialization and vision tracking.
        
        Override to add age sampling and vision state initialization.
        """
        # Create base patient
        patient = super()._create_patient(patient_id, enrollment_date)
        
        # Sample and set patient age from demographics
        if self.demographics_params:
            age_dist = self.demographics_params.get('demographics_parameters', {}).get('age_distribution', {})
            mean_age = age_dist.get('mean', 77.5)
            std_age = age_dist.get('std', 8.2)
            min_age = age_dist.get('min', 50)
            max_age = age_dist.get('max', 95)
            
            # Sample age from normal distribution, bounded
            age = random.gauss(mean_age, std_age)
            age = max(min_age, min(max_age, age))
            patient.age_years = int(age)
            
            # Calculate birth date from age at enrollment
            patient.birth_date = enrollment_date - timedelta(days=int(age * 365.25))
        
        # Initialize vision tracking
        self._initialize_patient_vision(patient_id, patient, enrollment_date)
        
        return patient
    
    def _update_patient_tracking(self, patient: Patient, current_state: DiseaseState, measured_vision: int):
        """
        Update patient tracking counters for discontinuation logic.
        
        Args:
            patient: Patient to update
            current_state: Current disease state
            measured_vision: Current measured vision
        """
        # Track consecutive stable visits
        if current_state == DiseaseState.STABLE:
            patient.consecutive_stable_visits = getattr(patient, 'consecutive_stable_visits', 0) + 1
        else:
            patient.consecutive_stable_visits = 0
        
        # Track visits without improvement
        if len(patient.visit_history) > 1:
            previous_vision = patient.visit_history[-2]['vision']
            if measured_vision <= previous_vision:
                patient.visits_without_improvement = getattr(patient, 'visits_without_improvement', 0) + 1
            else:
                patient.visits_without_improvement = 0
        
        # Track visits with significant loss (handled in discontinuation checker)
        # Initialize if not present
        if not hasattr(patient, 'visits_with_significant_loss'):
            patient.visits_with_significant_loss = 0
        if not hasattr(patient, 'consecutive_poor_vision_visits'):
            patient.consecutive_poor_vision_visits = 0