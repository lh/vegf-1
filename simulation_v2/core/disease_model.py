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
                 transition_probabilities: Dict[str, Dict[str, float]],
                 treatment_effect_multipliers: Optional[Dict[str, Dict[str, float]]] = None,
                 seed: Optional[int] = None):
        """
        Initialize disease model.
        
        NO DEFAULTS - all parameters must be provided.
        
        Parameters
        ----------
        transition_probabilities : dict
            Base transition probabilities for each state
            Must include all states and sum to 1.0
        treatment_effect_multipliers : dict, optional
            Multipliers for transition probabilities when treated
        seed : int, optional
            Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
            
        # Validate and store transition probabilities
        self._validate_transitions(transition_probabilities)
        
        # Convert string keys to DiseaseState enums
        self.transition_probabilities = {}
        for state_str, transitions in transition_probabilities.items():
            state = DiseaseState[state_str]
            self.transition_probabilities[state] = {}
            for target_str, prob in transitions.items():
                target = DiseaseState[target_str]
                self.transition_probabilities[state][target] = prob
                
        # Store treatment effect multipliers
        self.treatment_multipliers = treatment_effect_multipliers or {}
        
    def _validate_transitions(self, transitions: Dict[str, Dict[str, float]]) -> None:
        """Validate transition probabilities."""
        states = {'NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE'}
        
        # Check all states present
        if set(transitions.keys()) != states:
            raise ValueError(f"Must define transitions for all states: {states}")
            
        # Check probabilities sum to 1
        for state, probs in transitions.items():
            total = sum(probs.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f"State {state} probabilities sum to {total}, not 1.0")
        
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
        
        # Apply treatment effect multipliers if provided
        if treated and current_state.name in self.treatment_multipliers:
            multipliers = self.treatment_multipliers[current_state.name].get('multipliers', {})
            
            # Apply multipliers
            for target_str, multiplier in multipliers.items():
                if target_str in base_probs:
                    target = DiseaseState[target_str]
                    base_probs[target] *= multiplier
                    
            # Renormalize probabilities to sum to 1.0
            total = sum(base_probs.values())
            if total > 0:
                base_probs = {k: v/total for k, v in base_probs.items()}
                
        # Make random choice based on probabilities
        states = list(base_probs.keys())
        probabilities = list(base_probs.values())
        
        return random.choices(states, weights=probabilities)[0]
    
    def progress(self, 
                 current_state: DiseaseState,
                 days_since_injection: Optional[int] = None) -> DiseaseState:
        """
        Progress disease state based on time since last injection.
        
        This wraps the transition method for compatibility with engines.
        
        Parameters
        ----------
        current_state : DiseaseState
            Current disease state
        days_since_injection : int, optional
            Days since last injection (affects treatment status)
            
        Returns
        -------
        DiseaseState
            New disease state
        """
        # Simple logic: consider patient "treated" if injection was recent
        # This is a placeholder - real model would be more sophisticated
        treated = days_since_injection is not None and days_since_injection <= 84  # 12 weeks
        
        return self.transition(current_state, treated=treated)