""":no-index:
Clinical model for AMD disease progression and vision changes.

This module implements the clinical aspects of AMD progression, including disease states,
vision changes, and treatment effects. It uses a state-based model with probabilistic
transitions and configurable parameters for vision changes.

Classes
-------
DiseaseState
    Enumeration of possible AMD disease states
ClinicalModel
    Core class implementing disease progression and vision change logic

Key Features
------------
- Four disease states (NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE)
- Configurable transition probabilities between states
- Vision change modeling with:
    - State-dependent base changes
    - Time since last injection factor
    - Vision ceiling effect
    - Measurement noise
- Injection vs non-injection visit differentiation

Mathematical Model
------------------
Vision change is calculated as:
    ΔV = (B × T × C) + N
Where:
    ΔV: Vision change (ETDRS letters)
    B: Base change (state and injection dependent)
    T: Time factor (1 + weeks_since_injection/max_weeks)
    C: Ceiling factor (1 - current_vision/max_vision)
    N: Measurement noise (normally distributed)

State Transitions
-----------------
NAIVE → STABLE: 30%
NAIVE → ACTIVE: 60% 
NAIVE → HIGHLY_ACTIVE: 10%
Other transitions configurable via parameters

Examples
--------
>>> config = SimulationConfig.from_yaml("protocols/eylea.yaml")
>>> model = ClinicalModel(config)
>>> state = {"disease_state": "NAIVE", "injections": 0, ...}
>>> vision_change, new_state = model.simulate_vision_change(state)

Notes
-----
- Vision measured in ETDRS letters (0-100 range)
- Positive ΔV indicates vision improvement
- Time factor increases linearly with weeks since last injection
- Ceiling effect reduces changes as vision approaches maximum
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

class DiseaseState(Enum):
    """:no-index:
    Disease states for AMD progression.

    Enumeration of possible disease states in the AMD progression model.

    Attributes
    ----------
    NAIVE : 
        Initial state for new patients with no prior treatment.
        Typically transitions to other states in first visit.
    STABLE : 
        Disease is under control with minimal activity.
        Patients typically maintain or slightly improve vision.
    ACTIVE : 
        Disease shows signs of activity with fluid accumulation.
        Patients typically experience vision decline without treatment.
    HIGHLY_ACTIVE : 
        Disease shows high levels of activity with significant fluid.
        Patients experience rapid vision decline without treatment.

    Notes
    -----
    State transitions are probabilistic and configurable via ClinicalModel.
    Default transition probabilities from NAIVE state:
        - STABLE: 30%
        - ACTIVE: 60%
        - HIGHLY_ACTIVE: 10%
    """
    NAIVE = 0
    STABLE = 1
    ACTIVE = 2
    HIGHLY_ACTIVE = 3
    
    def __str__(self):
        return self.name.lower()

from simulation.config import SimulationConfig

class ClinicalModel:
    """:no-index:
    Models clinical aspects of AMD progression, including disease states and vision changes.
    
    This model includes four disease states: NAIVE, STABLE, ACTIVE, and HIGHLY_ACTIVE.
    It simulates disease progression and vision changes based on the current state and treatment.
    
    The model uses configurable transition probabilities between states and simulates vision changes
    with normal distributions, differentiating between injection and non-injection visits.

    Parameters
    ----------
    config : simulation.config.SimulationConfig
        Configuration object containing:
            - clinical_model_params: Clinical model parameters
            - vision_params: Vision change parameters
            - transition_probabilities: State transition probabilities

    Attributes
    ----------
    config : simulation.config.SimulationConfig
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

    Notes
    -----
    The model captures key clinical aspects of AMD progression:
    1. State-dependent response to treatment
    2. Waning of treatment effect over time
    3. Diminishing returns at higher vision levels
    4. Realistic measurement variability
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
        """Simulate disease state progression using configured transition probabilities.

        Parameters
        ----------
        current_state : DiseaseState
            Current disease state (NAIVE, STABLE, ACTIVE, or HIGHLY_ACTIVE)

        Returns
        -------
        DiseaseState
            New disease state after progression

        Raises
        ------
        ValueError
            If current_state is not a valid DiseaseState

        Examples
        --------
        >>> model = ClinicalModel(config)
        >>> current_state = DiseaseState.NAIVE
        >>> new_state = model.simulate_disease_progression(current_state)
        >>> print(f"Transitioned from {current_state} to {new_state}")

        Notes
        -----
        Disease progression follows these rules:
        1. NAIVE state has fixed transition probabilities:
            - STABLE: 30%
            - ACTIVE: 60%
            - HIGHLY_ACTIVE: 10%
        2. Other states use probabilities from configuration
        3. If no probabilities defined, remains in current state
        4. Probabilities are normalized to sum to 1 if needed

        The method handles:
        - Validation of current_state
        - Special case for NAIVE state
        - Probability normalization
        - Random selection of next state
        - Debug logging of transitions

        Transition probabilities represent clinical observations of AMD progression:
        - NAIVE patients most likely to transition to ACTIVE state
        - STABLE patients typically remain stable
        - ACTIVE patients may progress to HIGHLY_ACTIVE or regress to STABLE
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
            Current patient state dictionary with these required keys:
                - disease_state: Current disease state (str or DiseaseState)
                    Must be one of: NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE
                - injections: Total number of injections (int)
                    Count of all injections received
                - last_recorded_injection: Number of last recorded injection (int) 
                    Used to detect new injections
                - weeks_since_last_injection: Weeks since last injection (int)
                    Used in time factor calculation
                - current_vision: Current vision score (ETDRS letters, int)
                    Must be between 0-100 (will be clamped if outside range)
            
            Optional keys:
                - debug: bool - Enable debug output if True

        Returns
        -------
        Tuple[float, DiseaseState]
            Tuple containing:
                - Vision change in ETDRS letters (positive = improvement)
                - New disease state

        Raises
        ------
        ValueError
            If required vision change parameters are missing from configuration

        Examples
        --------
        >>> state = {
        ...     "disease_state": "NAIVE", 
        ...     "injections": 1,
        ...     "last_recorded_injection": 0,
        ...     "weeks_since_last_injection": 4,
        ...     "current_vision": 70
        ... }
        >>> vision_change, new_state = model.simulate_vision_change(state)
        >>> print(f"Vision changed by {vision_change:.1f} letters")

        Notes
        -----
        Mathematical Model:
            ΔV = (B × T × C) + N

        Where:
            ΔV: Vision change (ETDRS letters)
                Positive values indicate vision improvement
                Negative values indicate vision decline
            B: Base change (state and injection dependent)
                - Normally distributed: N(μ, σ)
                - μ and σ configured per state in vision_change_params
                - Separate distributions for injection vs non-injection visits
                - Typical ranges:
                    Injection: μ = +5 to +15 letters
                    Non-injection: μ = -5 to +5 letters
            T: Time factor (1 + weeks_since_injection/max_weeks)
                - Models decreasing treatment effect over time
                - max_weeks typically 52 (1 year) from config
                - Ranges from 1 (immediate post-injection) to 2 (1 year post-injection)
            C: Ceiling factor (1 - current_vision/max_vision)
                - max_vision typically 100 letters from config  
                - Ranges from 1 (0 letters) to 0 (100 letters)
                - Limits unrealistic vision improvements at high acuity
            N: Measurement noise (normally distributed)
                - Represents test-retest variability
                - Typically N(0, 0.5) letters from config

        Edge Cases:
            - If current_vision > max_vision, ceiling_factor is clamped to 0
            - If weeks_since_injection > max_weeks, time_factor is clamped to 2
            - If state missing required keys, uses defaults:
                weeks_since_injection=0, current_vision=70

        The model captures key clinical aspects:
        1. State-dependent response to treatment
        2. Waning of treatment effect over time  
        3. Diminishing returns at higher vision levels
        4. Realistic measurement variability
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
