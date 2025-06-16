"""
Comprehensive discontinuation checker for time-based model.

Implements all 6 discontinuation reasons with priority ordering.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from simulation_v2.core.patient import Patient


@dataclass
class DiscontinuationResult:
    """Result of discontinuation check."""
    should_discontinue: bool
    reason: Optional[str] = None
    probability_used: Optional[float] = None
    

class DiscontinuationChecker:
    """
    Checks all discontinuation reasons in priority order.
    
    Priority order (first matching reason wins):
    1. Death
    2. Poor vision 
    3. Deterioration
    4. Treatment decision
    5. Attrition
    6. Administrative
    """
    
    def __init__(self, discontinuation_params: Dict[str, Any]):
        """
        Initialize with discontinuation parameters.
        
        Args:
            discontinuation_params: Parameters from discontinuation.yaml
        """
        self.params = discontinuation_params.get('discontinuation_parameters', {})
        self.priority = discontinuation_params.get('discontinuation_priority', {
            1: 'death',
            2: 'poor_vision',
            3: 'deterioration',
            4: 'treatment_decision',
            5: 'attrition',
            6: 'administrative'
        })
    
    def check_discontinuation(
        self, 
        patient: Patient, 
        current_date: datetime,
        measured_vision: int,
        patient_age: Optional[int] = None
    ) -> DiscontinuationResult:
        """
        Check all discontinuation reasons in priority order.
        
        Args:
            patient: Patient to check
            current_date: Current simulation date
            measured_vision: Most recent measured vision
            patient_age: Patient age in years (if None, death check skipped)
            
        Returns:
            DiscontinuationResult with reason if discontinuing
        """
        # Check each reason in priority order
        for priority in sorted(self.priority.keys()):
            reason = self.priority[priority]
            
            if reason == 'death':
                result = self._check_death(patient, patient_age)
            elif reason == 'poor_vision':
                result = self._check_poor_vision(patient, measured_vision)
            elif reason == 'deterioration':
                result = self._check_deterioration(patient, measured_vision)
            elif reason == 'treatment_decision':
                result = self._check_treatment_decision(patient, current_date)
            elif reason == 'attrition':
                result = self._check_attrition(patient, current_date)
            elif reason == 'administrative':
                result = self._check_administrative()
            else:
                continue
                
            if result.should_discontinue:
                return result
        
        # No discontinuation
        return DiscontinuationResult(should_discontinue=False)
    
    def _check_death(self, patient: Patient, patient_age: Optional[int]) -> DiscontinuationResult:
        """Check natural mortality."""
        if patient_age is None:
            return DiscontinuationResult(should_discontinue=False)
            
        death_params = self.params.get('death', {})
        
        # Base annual mortality
        base_annual = death_params.get('base_annual_mortality', 0.02)
        
        # Age adjustment (per decade over 70)
        age_adjustment = 1.0
        if patient_age > 70:
            decades_over_70 = (patient_age - 70) / 10
            age_factor = death_params.get('age_adjustment_per_decade', 1.5)
            age_adjustment = age_factor ** decades_over_70
        
        # Disease state adjustment
        state_multipliers = death_params.get('disease_mortality_multiplier', {})
        state_multiplier = state_multipliers.get(patient.current_state.name, 1.0)
        
        # Convert annual to per-visit probability
        # Assuming average 8 visits per year
        visits_per_year = 8
        annual_prob = base_annual * age_adjustment * state_multiplier
        per_visit_prob = 1 - (1 - annual_prob) ** (1 / visits_per_year)
        
        if random.random() < per_visit_prob:
            return DiscontinuationResult(
                should_discontinue=True, 
                reason='death',
                probability_used=per_visit_prob
            )
        
        return DiscontinuationResult(should_discontinue=False)
    
    def _check_poor_vision(self, patient: Patient, measured_vision: int) -> DiscontinuationResult:
        """Check vision floor discontinuation."""
        pv_params = self.params.get('poor_vision', {})
        
        threshold = pv_params.get('vision_threshold', 20)
        if measured_vision >= threshold:
            # Reset counter if above threshold
            patient.consecutive_poor_vision_visits = 0
            return DiscontinuationResult(should_discontinue=False)
        
        # Below threshold
        patient.consecutive_poor_vision_visits += 1
        
        # Check grace period
        grace_period = pv_params.get('grace_period_visits', 2)
        if patient.consecutive_poor_vision_visits >= grace_period:
            prob = pv_params.get('discontinuation_probability', 0.8)
            if random.random() < prob:
                return DiscontinuationResult(
                    should_discontinue=True,
                    reason='poor_vision',
                    probability_used=prob
                )
        
        return DiscontinuationResult(should_discontinue=False)
    
    def _check_deterioration(self, patient: Patient, measured_vision: int) -> DiscontinuationResult:
        """Check continued deterioration despite treatment."""
        det_params = self.params.get('deterioration', {})
        
        # Calculate vision loss from baseline
        vision_loss = measured_vision - patient.baseline_vision
        loss_threshold = det_params.get('vision_loss_threshold', -10)
        
        if vision_loss > loss_threshold:
            # Not enough loss, reset counter
            patient.visits_with_significant_loss = 0
            return DiscontinuationResult(should_discontinue=False)
        
        # Significant loss detected
        patient.visits_with_significant_loss += 1
        
        visits_threshold = det_params.get('visits_with_loss_threshold', 3)
        if patient.visits_with_significant_loss >= visits_threshold:
            prob = det_params.get('discontinuation_probability', 0.7)
            if random.random() < prob:
                return DiscontinuationResult(
                    should_discontinue=True,
                    reason='deterioration',
                    probability_used=prob
                )
        
        return DiscontinuationResult(should_discontinue=False)
    
    def _check_treatment_decision(self, patient: Patient, current_date: datetime) -> DiscontinuationResult:
        """Check clinical treatment decisions."""
        td_params = self.params.get('treatment_decision', {})
        
        # Must have minimum treatments first
        min_treatments = td_params.get('min_treatments_before_decision', 3)
        if patient.injection_count < min_treatments:
            return DiscontinuationResult(should_discontinue=False)
        
        # Check stable disease
        if hasattr(patient, 'consecutive_stable_visits'):
            stable_threshold = td_params.get('stable_disease_visits_threshold', 6)
            if patient.consecutive_stable_visits >= stable_threshold:
                prob = td_params.get('stable_discontinuation_probability', 0.2)
                if random.random() < prob:
                    return DiscontinuationResult(
                        should_discontinue=True,
                        reason='treatment_decision_stable',
                        probability_used=prob
                    )
        
        # Check no improvement
        if hasattr(patient, 'visits_without_improvement'):
            no_improve_threshold = td_params.get('no_improvement_visits_threshold', 4)
            if patient.visits_without_improvement >= no_improve_threshold:
                prob = td_params.get('no_improvement_probability', 0.15)
                if random.random() < prob:
                    return DiscontinuationResult(
                        should_discontinue=True,
                        reason='treatment_decision_no_improvement',
                        probability_used=prob
                    )
        
        return DiscontinuationResult(should_discontinue=False)
    
    def _check_attrition(self, patient: Patient, current_date: datetime) -> DiscontinuationResult:
        """Check loss to follow-up."""
        att_params = self.params.get('attrition', {})
        
        # Base probability
        base_prob = att_params.get('base_probability_per_visit', 0.01)
        
        # Time adjustment
        time_adj = 1.0
        if patient.enrollment_date:
            months_in_treatment = (current_date - patient.enrollment_date).days / 30.44
            time_adjustments = att_params.get('time_adjustment', {})
            
            if months_in_treatment < 12:
                time_adj = time_adjustments.get('months_0_12', 1.0)
            elif months_in_treatment < 24:
                time_adj = time_adjustments.get('months_12_24', 1.2)
            else:
                time_adj = time_adjustments.get('months_24_plus', 1.5)
        
        # Treatment burden adjustment
        burden_adj = 1.0
        injections_per_year = patient.calculate_recent_injection_rate(current_date)
        if injections_per_year is not None:
            burden_adjustments = att_params.get('injection_burden_adjustment', {})
            
            if injections_per_year < 6:
                burden_adj = burden_adjustments.get('injections_per_year_0_6', 1.0)
            elif injections_per_year < 12:
                burden_adj = burden_adjustments.get('injections_per_year_6_12', 1.2)
            else:
                burden_adj = burden_adjustments.get('injections_per_year_12_plus', 1.5)
        
        # Final probability
        final_prob = base_prob * time_adj * burden_adj
        
        if random.random() < final_prob:
            return DiscontinuationResult(
                should_discontinue=True,
                reason='attrition',
                probability_used=final_prob
            )
        
        return DiscontinuationResult(should_discontinue=False)
    
    def _check_administrative(self) -> DiscontinuationResult:
        """
        Check NHS administrative errors.
        
        Examples:
        - Lost appointment letters
        - Hospital transport failures
        - Clinic cancellations not communicated
        - Booking system errors
        - Patient records mix-ups
        """
        admin_params = self.params.get('administrative', {})
        prob = admin_params.get('probability_per_visit', 0.005)
        
        if random.random() < prob:
            return DiscontinuationResult(
                should_discontinue=True,
                reason='administrative',
                probability_used=prob
            )
        
        return DiscontinuationResult(should_discontinue=False)