from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

class DiseaseState(Enum):
    """Disease states for AMD progression"""
    NAIVE = 0
    STABLE = 1
    ACTIVE = 2
    HIGHLY_ACTIVE = 3
    
    def __str__(self):
        return self.name.lower()

from simulation.config import SimulationConfig

class ClinicalModel:
    """
    Models clinical aspects of AMD progression, including disease states and vision changes.
    
    This model includes three disease states: STABLE, ACTIVE, and HIGHLY_ACTIVE.
    It simulates disease progression and vision changes based on the current state and treatment.
    
    The model uses configurable transition probabilities between states and simulates vision changes
    with normal distributions, differentiating between injection and non-injection visits.
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.transition_probabilities = self._parse_transition_probabilities()
        self.vision_change_params = self._parse_vision_change_params()

    def _parse_transition_probabilities(self) -> Dict[DiseaseState, Dict[DiseaseState, float]]:
        """Parse transition probabilities from config"""
        config_probs = self.config.parameters.get('clinical_model', {}).get('transition_probabilities', {})
        return {
            DiseaseState[state]: {
                DiseaseState[next_state]: prob
                for next_state, prob in probs.items()
            }
            for state, probs in config_probs.items()
        }

    def _parse_vision_change_params(self) -> Dict:
        """Parse vision change parameters from config"""
        return self.config.parameters.get('clinical_model', {}).get('vision_change', {})

    def get_transition_probabilities(self, current_state: DiseaseState) -> Dict[DiseaseState, float]:
        """Get transition probabilities for the current disease state"""
        return self.transition_probabilities[current_state].copy()
    
    def simulate_disease_progression(self, state: Dict) -> DiseaseState:
        """Simulate disease state progression"""
        current_state = state.get("disease_state", DiseaseState.NAIVE)
        
        print(f"DEBUG: Simulating disease progression - Current state: {current_state}")
        
        transition_probs = self.get_transition_probabilities(current_state)
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

    def get_transition_probabilities(self, current_state: DiseaseState) -> Dict[DiseaseState, float]:
        """Get transition probabilities for the current disease state"""
        if current_state not in self.transition_probabilities:
            raise ValueError(f"No transition probabilities defined for state: {current_state}")
        return self.transition_probabilities[current_state].copy()

    def _parse_transition_probabilities(self) -> Dict[DiseaseState, Dict[DiseaseState, float]]:
        """Parse transition probabilities from config"""
        clinical_model_params = self.config.get_clinical_model_params()
        config_probs = clinical_model_params.get('transition_probabilities', {})
        
        # Add transition probabilities for NAIVE state
        config_probs['NAIVE'] = {'NAIVE': 0.0, 'STABLE': 0.3, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.1}
        
        return {
            DiseaseState[state]: {
                DiseaseState[next_state]: prob
                for next_state, prob in probs.items()
            }
            for state, probs in config_probs.items()
        }
    
    def get_initial_vision(self) -> int:
        """Get initial vision for a new patient"""
        vision_params = self.config.get_vision_params()
        return int(np.random.normal(vision_params['baseline_mean'], vision_params['baseline_sd']))

    def simulate_vision_change(self, state: Dict) -> Tuple[float, DiseaseState]:
        """Calculate vision change and new disease state based on current state and treatment"""
        current_disease_state = state.get("disease_state", DiseaseState.NAIVE)
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

    def simulate_disease_progression(self, current_state: DiseaseState) -> DiseaseState:
        """Simulate disease state progression"""
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

    def simulate_vision_change(self, state: Dict) -> Tuple[float, DiseaseState]:
        """Calculate vision change and new disease state based on current state and treatment"""
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

    def _parse_vision_change_params(self) -> Dict:
        """Parse vision change parameters from config"""
        clinical_model_params = self.config.get_clinical_model_params()
        vision_change = clinical_model_params.get('vision_change', {})
        if not vision_change:
            raise ValueError("Missing vision change parameters in configuration")
        return vision_change

    def get_initial_vision(self) -> int:
        """Get initial vision for a new patient"""
        vision_params = self.config.get_vision_params()
        baseline_mean = vision_params.get('baseline_mean', 70)
        baseline_sd = vision_params.get('baseline_sd', 5)
        return int(np.random.normal(baseline_mean, baseline_sd))

    def _parse_transition_probabilities(self) -> Dict[DiseaseState, Dict[DiseaseState, float]]:
        """Parse transition probabilities from config"""
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
