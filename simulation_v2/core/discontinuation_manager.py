"""
Discontinuation manager for V2 simulation.

Handles evaluation of discontinuation criteria, monitoring schedules,
and retreatment decisions based on configurable profiles.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

from .patient import Patient
from .disease_model import DiseaseState
from .discontinuation_profile import DiscontinuationProfile, get_default_profiles

logger = logging.getLogger(__name__)


class V2DiscontinuationManager:
    """
    Manages treatment discontinuation decisions for V2 simulation.
    
    Evaluates multiple discontinuation criteria based on a configurable
    profile, handles monitoring schedules, and manages retreatment decisions.
    """
    
    def __init__(self, profile: Optional[DiscontinuationProfile] = None):
        """
        Initialize discontinuation manager.
        
        Args:
            profile: Discontinuation profile to use. If None, uses default NHS_1 profile.
        """
        if profile is None:
            profile = get_default_profiles()['nhs_1']
        
        self.profile = profile
        
        # Validate profile
        errors = self.profile.validate()
        if errors:
            raise ValueError(f"Invalid discontinuation profile: {'; '.join(errors)}")
        
        # Track statistics
        self.stats = {
            'stable_max_interval': 0,
            'poor_response': 0,
            'premature': 0,
            'system_discontinuation': 0,
            'reauthorization_failure': 0,
            'mortality': 0,
            'total': 0,
            'retreatments': 0
        }
        
        # Track unique patients to avoid double counting
        self.discontinued_patients = set()
        
        logger.info(f"Initialized V2DiscontinuationManager with profile: {profile.name}")
    
    def evaluate_discontinuation(
        self, 
        patient: Patient, 
        current_date: datetime,
        current_interval_weeks: int,
        is_stable: bool
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Evaluate whether a patient should discontinue treatment.
        
        Evaluates in priority order:
        1. Mortality (ends everything)
        2. Poor response (clinical failure)
        3. System discontinuation (random admin)
        4. Reauthorization failure (time-based)
        5. Premature (patient choice)
        6. Stable protocol (best case)
        
        Args:
            patient: Patient to evaluate
            current_date: Current simulation date
            current_interval_weeks: Current treatment interval in weeks
            is_stable: Whether disease is currently stable
            
        Returns:
            Tuple of (should_discontinue, discontinuation_type, reason)
        """
        # Skip if already discontinued
        if patient.is_discontinued or patient.id in self.discontinued_patients:
            return False, "", None
        
        # Update interval tracking
        patient.current_interval_days = current_interval_weeks * 7
        
        # 1. Check mortality
        if self._check_mortality(patient, current_date):
            return True, "mortality", "Patient death"
        
        # 2. Check poor response
        poor_response, reason = self._check_poor_response(patient)
        if poor_response:
            return True, "poor_response", reason
        
        # 3. Check system discontinuation
        if self._check_system_discontinuation():
            return True, "system_discontinuation", "Administrative loss to follow-up"
        
        # 4. Check reauthorization failure
        if self._check_reauthorization_failure(patient, current_date):
            return True, "reauthorization_failure", "Treatment funding not renewed"
        
        # 5. Check premature
        if self._check_premature(patient, current_interval_weeks):
            return True, "premature", "Patient-initiated discontinuation"
        
        # 6. Check stable max interval
        if self._check_stable_max_interval(patient, current_interval_weeks, is_stable):
            return True, "stable_max_interval", "Protocol-based discontinuation"
        
        return False, "", None
    
    def _check_mortality(self, patient: Patient, current_date: datetime) -> bool:
        """Check mortality based on annual rate."""
        config = self.profile.categories.get('mortality')
        if not config or not config.enabled:
            return False
        
        if patient.first_visit_date is None:
            return False
        
        annual_rate = config.annual_rate
        
        # Calculate per-visit probability based on current interval
        # Default to 28 days if not set
        interval_days = patient.current_interval_days if patient.current_interval_days > 0 else 28
        visits_per_year = 365.0 / interval_days
        per_visit_probability = 1 - (1 - annual_rate) ** (1 / visits_per_year)
        
        return random.random() < per_visit_probability
    
    def _check_poor_response(self, patient: Patient) -> Tuple[bool, Optional[str]]:
        """Check if patient has poor response to treatment."""
        config = self.profile.categories.get('poor_response')
        if not config or not config.enabled:
            return False, None
        
        threshold = config.vision_threshold_letters
        required_visits = config.consecutive_visits
        
        # Check current vision
        if patient.current_vision < threshold:
            patient.consecutive_poor_vision_visits += 1
        else:
            patient.consecutive_poor_vision_visits = 0
            return False, None
        
        # Check if we've met the consecutive visit requirement
        if patient.consecutive_poor_vision_visits >= required_visits:
            return True, f"Vision below {threshold} letters for {required_visits} consecutive visits"
        
        return False, None
    
    def _check_system_discontinuation(self) -> bool:
        """Check random administrative discontinuation."""
        config = self.profile.categories.get('system_discontinuation')
        if not config or not config.enabled:
            return False
        
        # Convert annual probability to per-visit
        # Assuming average 8-week intervals = 6.5 visits per year
        annual_prob = config.annual_probability
        per_visit_prob = 1 - (1 - annual_prob) ** (1 / 6.5)
        
        return random.random() < per_visit_prob
    
    def _check_reauthorization_failure(self, patient: Patient, current_date: datetime) -> bool:
        """Check if treatment duration exceeds reauthorization threshold."""
        config = self.profile.categories.get('reauthorization_failure')
        if not config or not config.enabled:
            return False
        
        if patient.first_visit_date is None:
            return False
        
        threshold_weeks = config.threshold_weeks
        probability = config.probability
        
        # Calculate treatment duration
        treatment_duration = current_date - patient.first_visit_date
        treatment_weeks = treatment_duration.days / 7.0
        
        # Only check after threshold
        if treatment_weeks > threshold_weeks:
            return random.random() < probability
        
        return False
    
    def _check_premature(self, patient: Patient, current_interval_weeks: int) -> bool:
        """Check premature discontinuation."""
        config = self.profile.categories.get('premature')
        if not config or not config.enabled:
            return False
        
        # Check minimum criteria
        min_interval = config.min_interval_weeks
        min_vision = config.min_vision_letters
        
        if current_interval_weeks < min_interval:
            return False
        
        if patient.current_vision < min_vision:
            return False
        
        # Calculate probability to achieve target rate
        # This is simplified - in reality would need more sophisticated calibration
        target_rate = config.target_rate
        
        # Estimate annual probability needed
        # Assuming ~12 visits per year for eligible patients
        annual_visits = 52 / current_interval_weeks
        per_visit_prob = 1 - (1 - target_rate) ** (1 / annual_visits)
        
        return random.random() < per_visit_prob
    
    def _check_stable_max_interval(
        self, 
        patient: Patient, 
        current_interval_weeks: int, 
        is_stable: bool
    ) -> bool:
        """Check stable discontinuation at maximum interval."""
        config = self.profile.categories.get('stable_max_interval')
        if not config or not config.enabled:
            return False
        
        required_interval = config.required_interval_weeks
        required_visits = config.consecutive_visits
        probability = config.probability
        
        # Check if at required interval
        if current_interval_weeks < required_interval:
            patient.consecutive_stable_visits = 0
            return False
        
        # Update stable visit counter
        if is_stable:
            patient.consecutive_stable_visits += 1
        else:
            patient.consecutive_stable_visits = 0
            return False
        
        # Check if criteria met
        if patient.consecutive_stable_visits >= required_visits:
            return random.random() < probability
        
        return False
    
    def process_discontinuation(
        self,
        patient: Patient,
        discontinuation_date: datetime,
        discontinuation_type: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Process a discontinuation event.
        
        Args:
            patient: Patient being discontinued
            discontinuation_date: Date of discontinuation
            discontinuation_type: Type of discontinuation
            reason: Optional detailed reason
        """
        # Mark patient as discontinued
        patient.discontinue(discontinuation_date, discontinuation_type, reason)
        
        # Track in stats
        self.stats[discontinuation_type] += 1
        self.stats['total'] += 1
        self.discontinued_patients.add(patient.id)
        
        # Apply vision impact for premature discontinuation
        if discontinuation_type == 'premature':
            config = self.profile.categories.get('premature')
            if config and config.va_impact:
                mean_loss = config.va_impact['mean']
                std_loss = config.va_impact['std']
                vision_loss = random.gauss(mean_loss, std_loss)
                patient.current_vision = max(0, patient.current_vision + vision_loss)
        
        # Schedule monitoring visits (except for mortality and poor response)
        if discontinuation_type not in ['mortality', 'poor_response']:
            patient.monitoring_schedule = self.get_monitoring_schedule(
                discontinuation_date, 
                discontinuation_type
            )
        
        logger.info(
            f"Patient {patient.id} discontinued: {discontinuation_type} "
            f"(vision: {patient.current_vision}, reason: {reason})"
        )
    
    def get_monitoring_schedule(
        self, 
        discontinuation_date: datetime, 
        discontinuation_type: str
    ) -> List[datetime]:
        """
        Get monitoring visit schedule based on discontinuation type.
        
        Args:
            discontinuation_date: Date of discontinuation
            discontinuation_type: Type of discontinuation
            
        Returns:
            List of monitoring visit dates
        """
        # Map discontinuation type to schedule type
        schedule_map = {
            'stable_max_interval': 'planned',
            'premature': 'unplanned',
            'reauthorization_failure': 'unplanned',
            'system_discontinuation': 'system',
            'poor_response': 'poor_response',
            'mortality': 'mortality'
        }
        
        schedule_type = schedule_map.get(discontinuation_type, 'unplanned')
        weeks = self.profile.monitoring_schedules.get(schedule_type, [])
        
        # Convert weeks to dates
        monitoring_dates = []
        for week in weeks:
            monitoring_date = discontinuation_date + timedelta(weeks=week)
            monitoring_dates.append(monitoring_date)
        
        return monitoring_dates
    
    def evaluate_retreatment(
        self,
        patient: Patient,
        has_fluid: bool,
        current_date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate whether a discontinued patient should restart treatment.
        
        Args:
            patient: Patient to evaluate
            has_fluid: Whether fluid is detected on OCT
            current_date: Current simulation date
            
        Returns:
            Tuple of (should_retreat, reason)
        """
        if not patient.is_discontinued:
            return False, None
        
        # No retreatment for mortality or poor response
        if patient.discontinuation_type in ['mortality', 'poor_response']:
            return False, None
        
        retreatment_config = self.profile.retreatment
        
        # Check fluid requirement
        if retreatment_config['fluid_detection_required'] and not has_fluid:
            return False, None
        
        # Check vision loss requirement
        min_loss = retreatment_config['min_vision_loss_letters']
        if patient.pre_discontinuation_vision is not None:
            vision_loss = patient.pre_discontinuation_vision - patient.current_vision
            if vision_loss < min_loss:
                return False, None
        
        # Check detection probability
        detection_prob = retreatment_config.get('detection_probability', 1.0)
        if random.random() > detection_prob:
            return False, None
        
        # Check retreatment probability
        retreat_prob = retreatment_config['probability']
        if random.random() < retreat_prob:
            self.stats['retreatments'] += 1
            return True, f"Fluid detected with {vision_loss:.0f} letter vision loss"
        
        return False, None
    
    def get_recurrence_probability(
        self,
        discontinuation_type: str,
        years_since_discontinuation: float
    ) -> float:
        """
        Get probability of disease recurrence based on time since discontinuation.
        
        Uses linear interpolation between known time points.
        
        Args:
            discontinuation_type: Type of discontinuation
            years_since_discontinuation: Time since discontinuation in years
            
        Returns:
            Probability of recurrence (0-1)
        """
        rates = self.profile.recurrence_rates.get(discontinuation_type, {})
        
        if not rates:
            return 0.0
        
        # Linear interpolation between known points
        if years_since_discontinuation <= 1:
            return rates.get('year_1', 0.0) * years_since_discontinuation
        elif years_since_discontinuation <= 3:
            y1 = rates.get('year_1', 0.0)
            y3 = rates.get('year_3', 0.0)
            # Linear interpolation
            t = (years_since_discontinuation - 1) / 2
            return y1 + t * (y3 - y1)
        elif years_since_discontinuation <= 5:
            y3 = rates.get('year_3', 0.0)
            y5 = rates.get('year_5', 0.0)
            # Linear interpolation
            t = (years_since_discontinuation - 3) / 2
            return y3 + t * (y5 - y3)
        else:
            # Beyond 5 years, use 5-year rate
            return rates.get('year_5', 0.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discontinuation statistics."""
        total = self.stats['total']
        if total == 0:
            return self.stats
        
        # Calculate percentages
        stats_with_percentages = self.stats.copy()
        for key in self.stats:
            if key != 'total' and key != 'retreatments':
                percentage = (self.stats[key] / total) * 100 if total > 0 else 0
                stats_with_percentages[f'{key}_percent'] = round(percentage, 1)
        
        return stats_with_percentages
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        for key in self.stats:
            self.stats[key] = 0
        self.discontinued_patients.clear()