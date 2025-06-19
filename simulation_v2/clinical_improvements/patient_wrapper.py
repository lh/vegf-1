"""
Patient Wrapper for Clinical Improvements

Wraps the existing Patient class to add clinical improvements without
modifying the original code.
"""

import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..core.patient import Patient
from ..core.disease_model import DiseaseState
from .config import ClinicalImprovements


class ImprovedPatientWrapper:
    """
    Wraps existing Patient with clinical improvements.
    
    This wrapper intercepts and modifies patient behavior based on
    enabled clinical improvements while maintaining compatibility.
    """
    
    def __init__(self, patient: Patient, improvements: ClinicalImprovements):
        """
        Initialize wrapper with patient and improvement configuration.
        
        Args:
            patient: The original patient instance
            improvements: Clinical improvements configuration
        """
        self.patient = patient
        self.config = improvements
        
        # Loading phase tracking
        self.loading_phase_injection_count = 0
        
        # Response type assignment
        self.response_type = self._assign_response_type()
        self.response_multiplier = self._get_response_multiplier()
        
        # Vision trajectory tracking
        self.months_since_start = 0
        self.true_vision = patient.current_vision  # Track true vision separately
        
        # Apply baseline distribution if enabled
        if self.config.use_baseline_distribution and hasattr(patient, 'baseline_vision'):
            self._apply_baseline_distribution()
    
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped patient"""
        return getattr(self.patient, name)
    
    def _assign_response_type(self) -> str:
        """Assign patient to a response category"""
        if not self.config.use_response_heterogeneity:
            return 'average'
        
        rand = random.random()
        cumulative = 0.0
        
        for resp_type, params in self.config.response_types.items():
            cumulative += params['probability']
            if rand < cumulative:
                return resp_type
        
        return 'average'  # Default fallback
    
    def _get_response_multiplier(self) -> float:
        """Get response multiplier based on response type"""
        if not self.config.use_response_heterogeneity:
            return 1.0
        
        return self.config.response_types[self.response_type]['multiplier']
    
    def _apply_baseline_distribution(self) -> None:
        """Apply normal distribution to baseline vision"""
        # Generate from normal distribution
        baseline = random.gauss(
            self.config.baseline_vision_mean,
            self.config.baseline_vision_std
        )
        
        # Clamp to valid range
        baseline = max(self.config.baseline_vision_min,
                      min(self.config.baseline_vision_max, baseline))
        
        # Update patient's baseline and current vision
        self.patient.baseline_vision = int(baseline)
        self.patient.current_vision = int(baseline)
        self.true_vision = baseline
    
    def get_next_injection_interval(self, current_date: Optional[datetime] = None) -> int:
        """
        Get the interval to next injection, applying loading phase if enabled.
        
        Returns:
            Days until next injection
        """
        # Check if we're in loading phase (use patient's injection count, not wrapper's)
        if (self.config.use_loading_phase and 
            self.patient.injection_count < self.config.loading_phase_injections):
            return self.config.loading_phase_interval_days
        
        # Otherwise use patient's current interval
        return self.patient.current_interval_days
    
    def check_time_based_discontinuation(self, current_date: datetime) -> bool:
        """
        Check if patient should discontinue based on time.
        
        Args:
            current_date: Current simulation date
            
        Returns:
            True if patient should discontinue
        """
        if not self.config.use_time_based_discontinuation:
            return False
        
        if self.patient.is_discontinued:
            return False
        
        # Calculate years since first visit
        if not self.patient.first_visit_date:
            return False
        
        years_elapsed = (current_date - self.patient.first_visit_date).days / 365.25
        current_year = int(years_elapsed) + 1
        
        # Initialize tracking if needed
        if not hasattr(self, '_last_discontinuation_check_year'):
            self._last_discontinuation_check_year = 0
        
        # Only check once per year
        if current_year <= self._last_discontinuation_check_year:
            return False
        
        # Update last check year
        self._last_discontinuation_check_year = current_year
        
        # Get discontinuation probability for current year
        prob = self.config.discontinuation_probabilities.get(
            min(current_year, 5),  # Cap at year 5 probability
            self.config.discontinuation_probabilities[5]
        )
        
        # Perform discontinuation check
        if random.random() < prob:
            # Apply discontinuation
            self.patient.is_discontinued = True
            self.patient.discontinuation_date = current_date
            self.patient.discontinuation_type = "time_based"
            self.patient.discontinuation_reason = f"Time-based discontinuation in year {current_year}"
            return True
        
        return False
    
    def calculate_vision_change(self, current_date: Optional[datetime] = None) -> float:
        """
        Calculate vision change based on response-based model.
        
        Args:
            current_date: Current simulation date
            
        Returns:
            Vision change in ETDRS letters
        """
        if not self.config.use_response_based_vision:
            # Use default vision model
            return 0.0
        
        # Update months since start
        if self.patient.first_visit_date and current_date:
            self.months_since_start = (current_date - self.patient.first_visit_date).days / 30.4
        
        # Determine phase and get parameters
        if self.months_since_start <= 3:
            # Loading phase
            params = self.config.vision_response_params['loading']
        elif self.months_since_start <= 12:
            # Rest of year 1
            params = self.config.vision_response_params['year1']
        elif self.months_since_start <= 24:
            # Year 2
            params = self.config.vision_response_params['year2']
        else:
            # Year 3+
            params = self.config.vision_response_params['year3plus']
        
        # Calculate base change
        base_change = random.gauss(params['mean'], params['std'])
        
        # Apply response multiplier
        vision_change = base_change * self.response_multiplier
        
        return vision_change
    
    def update_vision(self, vision_change: float) -> int:
        """
        Update patient vision with optional measurement noise.
        
        Args:
            vision_change: Change in vision (ETDRS letters)
            
        Returns:
            Measured vision (with noise if enabled)
        """
        # Update true vision
        self.true_vision += vision_change
        self.true_vision = max(0, min(100, self.true_vision))  # Clamp to valid range
        
        # Apply measurement noise if enabled
        if self.config.vision_measurement_std > 0:
            measured = self.true_vision + random.gauss(0, self.config.vision_measurement_std)
            measured = max(0, min(100, measured))  # Clamp to valid range
        else:
            measured = self.true_vision
        
        # Update patient's current vision
        self.patient.current_vision = int(measured)
        
        return int(measured)
    
    def record_injection(self, date: datetime) -> None:
        """
        Record an injection, updating loading phase counter.
        
        Args:
            date: Date of injection
        """
        # Update loading phase counter
        if self.config.use_loading_phase:
            self.loading_phase_injection_count += 1
        
        # Update patient injection count
        self.patient.injection_count += 1
        self.patient._last_injection_date = date
    
    def get_clinical_summary(self) -> Dict[str, Any]:
        """
        Get summary of clinical improvements applied to this patient.
        
        Returns:
            Dictionary with improvement details
        """
        return {
            'patient_id': self.patient.id,
            'response_type': self.response_type,
            'response_multiplier': self.response_multiplier,
            'loading_phase_injections': self.loading_phase_injection_count,
            'true_vision': self.true_vision,
            'measured_vision': self.patient.current_vision,
            'months_since_start': self.months_since_start,
            'improvements_active': {
                'loading_phase': self.config.use_loading_phase,
                'time_based_discontinuation': self.config.use_time_based_discontinuation,
                'response_based_vision': self.config.use_response_based_vision,
                'baseline_distribution': self.config.use_baseline_distribution,
                'response_heterogeneity': self.config.use_response_heterogeneity
            }
        }