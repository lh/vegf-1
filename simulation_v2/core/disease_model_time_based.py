"""
Time-based disease model with fortnightly updates.

This model separates disease progression from visit frequency by updating
patient states every 14 days regardless of when visits occur.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum

from .disease_model import DiseaseState


class DiseaseModelTimeBased:
    """
    Disease model with time-based transitions.
    
    Key differences from per-visit model:
    - Disease states update every 14 days (fortnightly)
    - Treatment effects decay continuously over time
    - Transitions are independent of visit frequency
    """
    
    UPDATE_INTERVAL_DAYS = 14  # Fortnightly updates
    
    def __init__(
        self,
        fortnightly_transitions: Dict[str, Dict[str, float]],
        treatment_effect_multipliers: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None,
        treatment_half_life_days: int = 56,  # 8 weeks default
        seed: Optional[int] = None
    ):
        """
        Initialize time-based disease model.
        
        Args:
            fortnightly_transitions: Transition probabilities per 14-day period
            treatment_effect_multipliers: How treatment modifies transitions
            treatment_half_life_days: Half-life of treatment effect (default 56 days)
            seed: Random seed for reproducibility
        """
        self.fortnightly_transitions = self._validate_transitions(fortnightly_transitions)
        self.treatment_multipliers = treatment_effect_multipliers or {}
        self.treatment_half_life_days = treatment_half_life_days
        
        if seed is not None:
            random.seed(seed)
            
        # Track state update history for each patient
        self.last_update_dates: Dict[str, datetime] = {}
        
    def _validate_transitions(self, transitions: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Validate that transition probabilities sum to 1.0."""
        validated = {}
        
        for from_state, to_states in transitions.items():
            total = sum(to_states.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f"Transitions from {from_state} sum to {total}, not 1.0")
                
            # Ensure all states are represented
            for state in DiseaseState:
                if state.name not in to_states:
                    raise ValueError(f"Missing transition from {from_state} to {state.name}")
                    
            validated[from_state] = to_states.copy()
            
        return validated
    
    def should_update(self, patient_id: str, current_date: datetime) -> bool:
        """
        Check if patient's disease state should be updated.
        
        Returns True if 14 days have passed since last update.
        """
        if patient_id not in self.last_update_dates:
            # First update
            return True
            
        days_since_update = (current_date - self.last_update_dates[patient_id]).days
        return days_since_update >= self.UPDATE_INTERVAL_DAYS
    
    def update_state(
        self,
        patient_id: str,
        current_state: DiseaseState,
        current_date: datetime,
        days_since_last_injection: Optional[int] = None
    ) -> DiseaseState:
        """
        Update patient's disease state based on fortnightly transitions.
        
        Args:
            patient_id: Unique patient identifier
            current_state: Current disease state
            current_date: Current simulation date
            days_since_last_injection: Days since last treatment (None if never treated)
            
        Returns:
            New disease state after transition
        """
        # Record update time
        self.last_update_dates[patient_id] = current_date
        
        # Get base transition probabilities
        state_name = current_state.name
        base_probs = self.fortnightly_transitions[state_name].copy()
        
        # Apply treatment effect if applicable
        if days_since_last_injection is not None:
            treatment_efficacy = self.get_treatment_efficacy(days_since_last_injection)
            
            if treatment_efficacy > 0 and state_name in self.treatment_multipliers:
                # Apply treatment multipliers weighted by efficacy
                multipliers = self.treatment_multipliers[state_name].get('multipliers', {})
                
                for to_state, multiplier in multipliers.items():
                    if to_state in base_probs:
                        # Interpolate between base probability and modified probability
                        base_prob = base_probs[to_state]
                        modified_prob = base_prob * multiplier
                        base_probs[to_state] = (
                            base_prob * (1 - treatment_efficacy) + 
                            modified_prob * treatment_efficacy
                        )
                
                # Renormalize to ensure sum = 1.0
                total = sum(base_probs.values())
                if total > 0:
                    base_probs = {k: v/total for k, v in base_probs.items()}
        
        # Apply transition
        rand = random.random()
        cumulative = 0.0
        
        for to_state_name, prob in base_probs.items():
            cumulative += prob
            if rand < cumulative:
                return DiseaseState[to_state_name]
                
        # Fallback (should not reach here if probabilities sum to 1)
        return current_state
    
    def get_treatment_efficacy(self, days_since_injection: int) -> float:
        """
        Calculate treatment efficacy based on time since injection.
        
        Uses exponential decay model with configurable half-life.
        
        Args:
            days_since_injection: Days since last treatment
            
        Returns:
            Efficacy between 0 and 1
        """
        if days_since_injection < 0:
            return 0.0
            
        # Exponential decay: efficacy = 0.5^(days/half_life)
        return 0.5 ** (days_since_injection / self.treatment_half_life_days)
    
    def get_fortnights_since_update(self, patient_id: str, current_date: datetime) -> int:
        """
        Get number of complete fortnights since last update.
        
        Useful for catching up if updates were missed.
        """
        if patient_id not in self.last_update_dates:
            return 0
            
        days_since = (current_date - self.last_update_dates[patient_id]).days
        return days_since // self.UPDATE_INTERVAL_DAYS
    
    def reset_patient(self, patient_id: str):
        """Reset tracking for a patient (e.g., after discontinuation)."""
        if patient_id in self.last_update_dates:
            del self.last_update_dates[patient_id]


def convert_per_visit_to_fortnightly(
    per_visit_prob: float,
    typical_interval_days: int
) -> float:
    """
    Convert per-visit probability to fortnightly rate.
    
    Args:
        per_visit_prob: Probability per visit (0-1)
        typical_interval_days: Typical days between visits for this state
        
    Returns:
        Equivalent fortnightly (14-day) probability
        
    Example:
        STABLE patients seen every 84 days (12 weeks)
        - 1 visit per 6 fortnights = 0.167 visits/fortnight
        - 15% per visit → 2.5% per fortnight
    """
    if per_visit_prob <= 0:
        return 0.0
    if per_visit_prob >= 1:
        return 1.0
        
    # Calculate visits per fortnight
    visits_per_fortnight = 14.0 / typical_interval_days
    
    # Convert probability
    # per_visit = 1 - (1 - fortnightly)^(1/visits_per_fortnight)
    # Solving for fortnightly:
    fortnightly_prob = 1 - (1 - per_visit_prob) ** visits_per_fortnight
    
    return fortnightly_prob


def get_typical_interval_days(disease_state: DiseaseState) -> int:
    """
    Get typical visit interval for each disease state.
    
    Based on clinical practice patterns.
    """
    intervals = {
        DiseaseState.NAIVE: 28,         # Initial monthly visits
        DiseaseState.STABLE: 84,        # Extended to 12 weeks
        DiseaseState.ACTIVE: 42,        # 6-week intervals
        DiseaseState.HIGHLY_ACTIVE: 28  # Monthly monitoring
    }
    return intervals.get(disease_state, 56)  # Default 8 weeks