"""Clinical model for AMD disease progression and vision changes.

This module implements the clinical aspects of AMD progression, including disease states,
vision changes, and treatment effects. It uses a state-based model with probabilistic
transitions and configurable parameters for vision changes.

Notes
-----
Key Features:
- Four disease states (NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE)
- Configurable transition probabilities between states
- Vision change modeling with:
  - State-dependent base changes
  - Time since last injection factor
  - Vision ceiling effect
  - Measurement noise
- Injection vs non-injection visit differentiation
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

class DiseaseState(Enum):
    """Disease states for AMD progression.

    Enumeration of possible disease states in the AMD progression model:
    - NAIVE: Initial state for new patients
    - STABLE: Disease is under control
    - ACTIVE: Disease shows signs of activity
    - HIGHLY_ACTIVE: Disease shows high levels of activity
    """
    NAIVE = 0
    STABLE = 1
    ACTIVE = 2
    HIGHLY_ACTIVE = 3
    
    def __str__(self):
        return self.name.lower()

from simulation.config import SimulationConfig

class ClinicalModel:
    """Models clinical aspects of AMD progression, including disease states and vision changes.
    
    This model includes four disease states: NAIVE, STABLE, ACTIVE, and HIGHLY_ACTIVE.
    It simulates disease progression and vision changes based on the current state and treatment.
    
    The model uses configurable transition probabilities between states and simulates vision changes
    with normal distributions, differentiating between injection and non-injection visits.

    Parameters
    ----------
    config : SimulationConfig
        Configuration object containing:
        - clinical_model_params: Clinical model parameters
        - vision_params: Vision change parameters
        - transition_probabilities: State transition probabilities

    Attributes
    ----------
    config : SimulationConfig
        Configuration object containing model parameters
    transition_probabilities : Dict[DiseaseState, Dict[DiseaseState, float]]
        Probability matrix for transitions between disease states with structure:
        {
            DiseaseState.NAIVE: {DiseaseState.STABLE: 0.3, ...},
            DiseaseState.STABLE: {DiseaseState.STABLE: 0.7, ...},
            ...
        }
    vision_change_params : Dict
        Parameters controlling vision changes under different conditions including:
        - base_change: Mean/SD for each state and injection status
        - time_factor: Effect of time since last injection
        - ceiling_factor: Vision ceiling effect
        - measurement_noise: Random variability
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.transition_probabilities = self._parse_transition_probabilities()
        self.vision_change_params = self._parse_vision_change_params()

    def _parse_transition_probabilities(self) -> Dict[DiseaseState, Dict[DiseaseState, float]]:
        """Parse transition probabilities from configuration.

        Returns
        -------
        Dict[DiseaseState, Dict[DiseaseState, float]]
            Nested dictionary of transition probabilities between disease states

        Notes
        -----
        Ensures NAIVE state transitions are included with default probabilities if not specified
        in the configuration.
        """
        clinical_model_params = self.config.get_clinical_model_params()
        config_probs = clinical_model_params.get('transition_probabilities', {})
        
        # Ensure NAIVE state is included
        if 'NAIVE' not in config_probs:
            config_probs['NAIVE'] = {'NAIVE': 0.0, 'STABLE': 0.3, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.1}
        
        return {
            DiseaseState[state]: {
                DiseaseState[next_state]: prob
                for next_state, prob in probs.items()
            }
            for state, probs in config_probs.items()
        }

    def _parse_vision_change_params(self) -> Dict:
        """Parse vision change parameters from configuration.

        Returns
        -------
        Dict
            Dictionary containing vision change parameters for different states and conditions

        Raises
        ------
        ValueError
            If required vision change parameters are missing from configuration
        """
        clinical_model_params = self.config.get_clinical_model_params()
        vision_change = clinical_model_params.get('vision_change', {})
        if not vision_change:
            raise ValueError("Missing vision change parameters in configuration")
        return vision_change

    def get_transition_probabilities(self, current_state: DiseaseState) -> Dict[DiseaseState, float]:
        """Get transition probabilities for the current disease state.

        Parameters
        ----------
        current_state : DiseaseState
            Current disease state (NAIVE, STABLE, ACTIVE, or HIGHLY_ACTIVE)

        Returns
        -------
        Dict[DiseaseState, float]
            Dictionary mapping possible next states to their transition probabilities

        Raises
        ------
        ValueError
            If no transition probabilities are defined for the current state
        """
        if current_state not in self.transition_probabilities:
            raise ValueError(f"No transition probabilities defined for state: {current_state}")
        return self.transition_probabilities[current_state].copy()

    def simulate_disease_progression(self, current_state: DiseaseState) -> DiseaseState:
        """Simulate disease state progression.

        Parameters
        ----------
        current_state : DiseaseState
            Current disease state (NAIVE, STABLE, ACTIVE, or HIGHLY_ACTIVE)

        Returns
        -------
        DiseaseState
            New disease state after progression

        Notes
        -----
        Progression logic:
        1. NAIVE state has special transition probabilities to other states
        2. Other states use configured transition probabilities
        3. If no probabilities defined, remains in current state
        4. Probabilities are normalized to sum to 1
        """
        print(f"DEBUG: Simulating disease progression - Current state: {current_state}")
        
        if current_state == DiseaseState.NAIVE:
            # For NAIVE state, transition to other states based on predefined probabilities
            states = [DiseaseState.STABLE, DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE]
            probs = [0.3, 0.6, 0.1]  # These should match the probabilities defined earlier
        else:
            if current_state not in self.transition_probabilities:
                print(f"WARNING: No transition probabilities defined for state {current_state}")
                return current_state
            transition_probs = self.transition_probabilities[current_state]
            states = list(DiseaseState)
            probs = [transition_probs.get(s, 0) for s in states]
        
        # Normalize probabilities
        total_prob = sum(probs)
        if total_prob == 0:
            print(f"WARNING: All transition probabilities are zero for state {current_state}")
            return current_state
        normalized_probs = [p / total_prob for p in probs]
        
        new_state = np.random.choice(states, p=normalized_probs)
        print(f"DEBUG: Disease progression - From {current_state} to {new_state}")
        return new_state

    def get_initial_vision(self) -> int:
        """Get initial vision for a new patient.

        Returns
        -------
        int
            Initial vision score (ETDRS letters)

        Notes
        -----
        Uses normal distribution with configurable mean and standard deviation.
        Defaults to mean=70, sd=5 if not specified in configuration.
        """
        vision_params = self.config.get_vision_params()
        baseline_mean = vision_params.get('baseline_mean', 70)
        baseline_sd = vision_params.get('baseline_sd', 5)
        return int(np.random.normal(baseline_mean, baseline_sd))

    def simulate_vision_change(self, state: Dict) -> Tuple[float, DiseaseState]:
        """Calculate vision change and new disease state based on current state and treatment.

        Parameters
        ----------
        state : Dict
            Current patient state including:
            - disease_state: Current disease state (str or DiseaseState)
            - injections: Total number of injections (int)
            - last_recorded_injection: Number of last recorded injection (int)
            - weeks_since_last_injection: Weeks since last injection (int)
            - current_vision: Current vision score (ETDRS letters, int)

        Returns
        -------
        Tuple[float, DiseaseState]
            Tuple containing:
            - Vision change in ETDRS letters (positive = improvement)
            - New disease state

        Notes
        -----
        Vision change calculation formula:
        total_change = (base_change * time_factor * ceiling_factor) + measurement_noise

        Where:
        - base_change: State and injection-dependent mean change
        - time_factor: 1 + (weeks_since_injection / max_weeks)
        - ceiling_factor: 1 - (current_vision / max_vision)
        - measurement_noise: Random variability

        Raises
        ------
        ValueError
            If required vision change parameters are missing from configuration
        """
        current_disease_state = state.get("disease_state", DiseaseState.NAIVE)
        if isinstance(current_disease_state, str):
            current_disease_state = DiseaseState[current_disease_state]
        
        is_injection = state.get("injections", 0) > state.get("last_recorded_injection", -1)
        weeks_since_injection = state.get("weeks_since_last_injection", 0)
        current_vision = state.get("current_vision", 70)  # Assume 70 letters as default

        params = self.vision_change_params
        
        # Simulate disease state transition
        new_disease_state = self.simulate_disease_progression(current_disease_state)
        
        # Base change
        if 'base_change' not in params:
            raise ValueError("Missing 'base_change' in vision change parameters")
        
        base_params = params['base_change'].get(new_disease_state.name)
        if not base_params:
            raise ValueError(f"Missing base change parameters for disease state: {new_disease_state.name}")
        
        if is_injection:
            base_change = np.random.normal(*base_params['injection'])
        else:
            base_change = np.random.normal(*base_params['no_injection'])

        # Time factor
        max_weeks = params.get('time_factor', {}).get('max_weeks', 52)
        time_factor = 1 + (weeks_since_injection / max_weeks)
        
        # Ceiling effect
        max_vision = params.get('ceiling_factor', {}).get('max_vision', 100)
        ceiling_factor = 1 - (current_vision / max_vision)
        
        # Measurement variability
        measurement_noise = np.random.normal(*params.get('measurement_noise', [0, 0.5]))

        total_change = base_change * time_factor * ceiling_factor + measurement_noise
        
        return total_change, new_disease_state
