"""
Patient state model for archetype-based simulations.

This module defines the patient state representation used in archetype-driven simulations,
tracking behavior patterns and visual acuity trends specific to each patient archetype.
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional
from .patient_state import PatientState

class ArchetypeBehavior(Enum):
    """Behavior states for archetype patients.
    
    Attributes
    ----------
    COMPLIANT : str
        Patient follows treatment protocol consistently
    LAPSED : str 
        Patient has missed treatments beyond threshold
    REACTIVATED : str
        Previously lapsed patient returned to treatment
    DROPOUT : str
        Patient has stopped treatment permanently
    """
    COMPLIANT = "compliant"
    LAPSED = "lapsed"
    REACTIVATED = "reactivated"
    DROPOUT = "dropout"

class ArchetypePatientState(PatientState):
    """Patient state with archetype-specific behavior tracking.
    
    Extends the base PatientState with archetype-specific attributes and behavior
    modeling for treatment adherence patterns.

    Parameters
    ----------
    archetype_id : int
        ID of the archetype this patient belongs to
    behavior_state : ArchetypeBehavior, optional
        Current adherence behavior state (default: COMPLIANT)
    va_trend : Optional[float], optional
        Slope of visual acuity changes over time (default: None)
    interval_adjustment : float, optional
        Weeks adjustment from protocol interval (default: 0.0)

    Attributes
    ----------
    archetype_id : int
        Archetype identifier
    behavior_state : ArchetypeBehavior
        Current adherence state
    va_trend : Optional[float]
        Visual acuity trend slope
    interval_adjustment : float
        Protocol interval adjustment
    """
    archetype_id: int
    behavior_state: ArchetypeBehavior = ArchetypeBehavior.COMPLIANT
    va_trend: Optional[float] = None
    interval_adjustment: float = 0.0
    
    def update_behavior(self, va_change: float, interval: int):
        """Update patient behavior state based on treatment response.
        
        Parameters
        ----------
        va_change : float
            Change in visual acuity (ETDRS letters)
        interval : int
            Actual treatment interval in weeks

        Notes
        -----
        Behavior transitions:
        - Dropout if VA change > 15 letters
        - Lapsed if interval > 12 weeks
        - Reactivated if previously lapsed and interval <= 8 weeks
        """
        if abs(va_change) > 15:
            self.behavior_state = ArchetypeBehavior.DROPOUT
        elif interval > 12:  # Weeks
            self.behavior_state = ArchetypeBehavior.LAPSED
        elif self.behavior_state == ArchetypeBehavior.LAPSED and interval <= 8:
            self.behavior_state = ArchetypeBehavior.REACTIVATED
