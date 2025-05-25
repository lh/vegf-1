"""
Disease model implementation - FOV (Four Option Version).

This is a minimal implementation to demonstrate TDD approach.
We implement just enough to make the tests pass.
"""

from enum import Enum
import random
from typing import Dict, Optional


class DiseaseState(Enum):
    """Four disease states based on literature review."""
    NAIVE = 0
    STABLE = 1  
    ACTIVE = 2
    HIGHLY_ACTIVE = 3


class DiseaseModel:
    """
    Models disease state transitions.
    
    No fluid detection - uses probabilistic transitions based on:
    - Current state
    - Treatment status
    - Time factors (not implemented yet)
    """
    
    def __init__(self, 
                 transition_probabilities: Optional[Dict] = None,
                 seed: Optional[int] = None):
        """
        Initialize disease model.
        
        Parameters
        ----------
        transition_probabilities : dict, optional
            Custom transition probabilities
        seed : int, optional
            Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
            
        # Default transition probabilities from literature
        self.transition_probabilities = transition_probabilities or {
            DiseaseState.NAIVE: {
                DiseaseState.NAIVE: 0.0,  # Never stays naive
                DiseaseState.STABLE: 0.3,
                DiseaseState.ACTIVE: 0.6,
                DiseaseState.HIGHLY_ACTIVE: 0.1
            },
            DiseaseState.STABLE: {
                DiseaseState.STABLE: 0.85,  # Usually stays stable
                DiseaseState.ACTIVE: 0.15,  # Can deteriorate
                DiseaseState.HIGHLY_ACTIVE: 0.0
            },
            DiseaseState.ACTIVE: {
                DiseaseState.STABLE: 0.2,   # Can improve
                DiseaseState.ACTIVE: 0.7,   # Often stays active
                DiseaseState.HIGHLY_ACTIVE: 0.1  # Can worsen
            },
            DiseaseState.HIGHLY_ACTIVE: {
                DiseaseState.STABLE: 0.05,  # Rarely improves much
                DiseaseState.ACTIVE: 0.15,  # Some improvement
                DiseaseState.HIGHLY_ACTIVE: 0.8  # Usually stays severe
            }
        }
        
    def transition(self, 
                   current_state: DiseaseState,
                   treated: bool = False) -> DiseaseState:
        """
        Determine next disease state.
        
        Parameters
        ----------
        current_state : DiseaseState
            Current disease state
        treated : bool
            Whether patient received treatment
            
        Returns
        -------
        DiseaseState
            New disease state
        """
        # Get base probabilities
        base_probs = self.transition_probabilities[current_state].copy()
        
        # Adjust for treatment effect
        if treated and current_state != DiseaseState.NAIVE:
            # Treatment improves chances of stability
            # This is a simple model - could be more sophisticated
            if current_state == DiseaseState.ACTIVE:
                base_probs[DiseaseState.STABLE] = 0.4  # Better chance
                base_probs[DiseaseState.ACTIVE] = 0.55
                base_probs[DiseaseState.HIGHLY_ACTIVE] = 0.05
            elif current_state == DiseaseState.HIGHLY_ACTIVE:
                base_probs[DiseaseState.STABLE] = 0.1
                base_probs[DiseaseState.ACTIVE] = 0.3
                base_probs[DiseaseState.HIGHLY_ACTIVE] = 0.6
                
        # Make random choice based on probabilities
        states = list(base_probs.keys())
        probabilities = list(base_probs.values())
        
        return random.choices(states, weights=probabilities)[0]