from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

class DiseaseState(Enum):
    """Disease states for AMD progression"""
    REMISSION = 0
    STABLE = 1
    ACTIVE = 2
    HIGHLY_ACTIVE = 3
    
    def __str__(self):
        return {
            DiseaseState.REMISSION: "remission",
            DiseaseState.STABLE: "stable",
            DiseaseState.ACTIVE: "active",
            DiseaseState.HIGHLY_ACTIVE: "highly_active"
        }[self]

class ClinicalModel:
    """Models clinical aspects like disease states, vision changes and OCT findings"""
    
    # Default transition probabilities (can be overridden by config)
    DEFAULT_TRANSITIONS = {
        DiseaseState.STABLE: {
            DiseaseState.ACTIVE: 0.15,  # Increased probability of worsening
            DiseaseState.HIGHLY_ACTIVE: 0.05,
            DiseaseState.REMISSION: 0.1
        },
        DiseaseState.ACTIVE: {
            DiseaseState.STABLE: 0.1,
            DiseaseState.HIGHLY_ACTIVE: 0.25,  # Higher chance of further progression
            DiseaseState.REMISSION: 0.05
        },
        DiseaseState.HIGHLY_ACTIVE: {
            DiseaseState.STABLE: 0.05,
            DiseaseState.ACTIVE: 0.2,
            DiseaseState.REMISSION: 0.02
        },
        DiseaseState.REMISSION: {
            DiseaseState.STABLE: 0.5,  # Higher chance of stability
            DiseaseState.ACTIVE: 0.08,
            DiseaseState.HIGHLY_ACTIVE: 0.02
        }
    }

    @staticmethod
    def get_transition_probabilities(current_state: DiseaseState, 
                                   state: Dict,
                                   raw_only: bool = False) -> Dict[DiseaseState, float]:
        """Get transition probabilities adjusted for patient factors
        
        Args:
            current_state: Current disease state
            state: Patient state dictionary containing risk factors and history
            raw_only: If True, return raw probabilities without normalization (deprecated)
            
        Returns:
            Dictionary mapping possible next states to their probabilities
        """
        # Start with base probabilities
        probs = ClinicalModel.DEFAULT_TRANSITIONS[current_state].copy()
        
        # Calculate individual risk components
        risk_factors = state.get("risk_factors", {})
        
        # Age effect: Stronger exponential increase in risk after age 65
        age_effect = np.exp(max(0, (risk_factors.get("age", 65) - 65) / 15)) - 1
        
        # Smoking effect: Stronger threshold effect
        smoking_value = risk_factors.get("smoking", 0)
        smoking_effect = 3.0 * smoking_value if smoking_value > 0.5 else 2.0 * smoking_value
        
        # Genetic risk: Steeper sigmoid for more pronounced genetic impact
        genetic_value = risk_factors.get("genetic_risk", 0)
        genetic_effect = 3.0 / (1 + np.exp(-6 * (genetic_value - 0.5)))
        
        # Time effect: Exponential increase in risk after 8 weeks
        weeks_since_injection = state.get("weeks_since_last_injection", 0)
        time_effect = np.exp(max(0, (weeks_since_injection - 8) / 8)) - 1
        
        # Apply effects based on transition type
        for next_state in probs:
            if next_state.value > current_state.value:  # Disease worsening
                # Each factor independently increases progression risk
                probs[next_state] *= (1 + age_effect)
                probs[next_state] *= (1 + smoking_effect)
                probs[next_state] *= (1 + genetic_effect)
                probs[next_state] *= (1 + time_effect)
                
                # Cap maximum progression probability
                probs[next_state] = min(0.8, probs[next_state])
                
            elif next_state.value < current_state.value:  # Disease improvement
                # Risk factors reduce improvement probability
                probs[next_state] /= (1 + age_effect)
                probs[next_state] /= (1 + smoking_effect)
                probs[next_state] /= (1 + genetic_effect)
                
                # Time without treatment reduces improvement probability
                probs[next_state] /= (1 + time_effect)
                
                # Ensure minimum improvement probability
                probs[next_state] = max(0.01, probs[next_state])
        
        return probs
    
    @staticmethod
    def simulate_disease_progression(state: Dict) -> Tuple[DiseaseState, float]:
        """Simulate disease state progression based on independent biological factors
        
        Args:
            state: Dictionary containing patient state
            
        Returns:
            Tuple of (new disease state, progression rate adjustment)
        """
        current_state = state.get("disease_state", DiseaseState.STABLE)
        transition_probs = ClinicalModel.get_transition_probabilities(current_state, state)
        
        # Evaluate each possible transition independently
        possible_transitions = []
        for next_state, prob in transition_probs.items():
            if np.random.random() < prob:
                possible_transitions.append(next_state)
        
        if not possible_transitions:
            return current_state, 1.0
            
        # If multiple transitions are possible, select based on severity and current state
        if len(possible_transitions) > 1:
            # Prioritize transitions based on biological rules
            if current_state == DiseaseState.HIGHLY_ACTIVE:
                # Highly active disease more likely to improve than worsen further
                better_states = [s for s in possible_transitions if s.value < current_state.value]
                if better_states:
                    new_state = min(better_states, key=lambda s: s.value)
                else:
                    new_state = min(possible_transitions, key=lambda s: s.value)
            
            elif current_state == DiseaseState.REMISSION:
                # Remission more likely to slightly worsen than jump to highly active
                worse_states = [s for s in possible_transitions if s.value > current_state.value]
                if worse_states:
                    new_state = min(worse_states, key=lambda s: s.value)
                else:
                    new_state = max(possible_transitions, key=lambda s: s.value)
            
            else:  # STABLE or ACTIVE
                # Prefer gradual changes over large jumps
                new_state = min(possible_transitions, 
                              key=lambda s: abs(s.value - current_state.value))
        else:
            new_state = possible_transitions[0]
        
        # Calculate biological impact using non-linear scaling
        severity_diff = abs(new_state.value - current_state.value)
        if new_state.value > current_state.value:  # Worsening
            # Exponential increase in impact with severity
            rate_adjustment = np.exp(severity_diff * 0.4)  # e.g., 1.49, 2.23, 3.32 for 1,2,3 steps
        elif new_state.value < current_state.value:  # Improving
            # Diminishing returns for improvement
            rate_adjustment = 1.0 / (1.0 + severity_diff * 0.3)  # e.g., 0.77, 0.63, 0.53 for 1,2,3 steps
        else:
            rate_adjustment = 1.0
            
        return new_state, rate_adjustment
    
    @staticmethod
    def simulate_vision_change(state: Dict) -> float:
        """Calculate vision change with memory and ceiling effects"""
        disease_state = state.get("disease_state", DiseaseState.STABLE)
        is_injection = state.get("injections", 0) > state.get("last_recorded_injection", -1)

        if disease_state == DiseaseState.REMISSION:
            return ClinicalModel._simulate_remission_change(is_injection)
        elif disease_state == DiseaseState.HIGHLY_ACTIVE:
            return ClinicalModel._simulate_highly_active_change(is_injection)
        elif disease_state == DiseaseState.ACTIVE:
            return ClinicalModel._simulate_active_change(state, is_injection)
        else:  # STABLE
            return ClinicalModel._simulate_stable_change(state, is_injection)

    @staticmethod
    def _simulate_remission_change(is_injection: bool) -> float:
        """Simulate vision change for remission state"""
        if is_injection:
            return 1.0  # Fixed moderate improvement
        else:
            return np.random.uniform(-0.1, 0.1)  # Very small random change

    @staticmethod
    def _simulate_highly_active_change(is_injection: bool) -> float:
        """Simulate vision change for highly active disease state"""
        if is_injection:
            # Use a normal distribution with much higher variability
            return np.clip(np.random.normal(-2.5, 2.5), -8.0, 0.0)
        else:
            # Use a normal distribution with even higher variability for non-injection visits
            return np.clip(np.random.normal(-4.0, 3.0), -10.0, -1.0)

    @staticmethod
    def _simulate_active_change(state: Dict, is_injection: bool) -> float:
        """Simulate vision change for active disease state"""
        base_effect = ClinicalModel._calculate_base_effect(state, is_injection)
        return base_effect * (0.4 if is_injection else -1.0)  # Poor response or moderate decline

    @staticmethod
    def _simulate_stable_change(state: Dict, is_injection: bool) -> float:
        """Simulate vision change for stable disease state"""
        base_effect = ClinicalModel._calculate_base_effect(state, is_injection)
        return base_effect * (1.2 if is_injection else -0.3)  # Normal response or mild decline

    @staticmethod
    def _calculate_base_effect(state: Dict, is_injection: bool) -> float:
        """Calculate base effect for vision change"""
        response_history = state.get("treatment_response_history", [])
        headroom_factor = ClinicalModel._calculate_headroom_factor(state)

        if is_injection:
            return ClinicalModel._calculate_treatment_effect(state, response_history, headroom_factor)
        else:
            base_effect = ClinicalModel._calculate_natural_progression(state, response_history)
            return base_effect * state.get("progression_rate_adjustment", 1.0)

    @staticmethod
    def _calculate_headroom_factor(state: Dict) -> float:
        """Calculate headroom factor for vision change"""
        current_vision = state["current_vision"]
        best_vision = state.get("best_vision_achieved", current_vision)
        absolute_max = 85  # ETDRS letter score maximum
        theoretical_max = min(absolute_max, best_vision + 5)
        headroom = max(0, theoretical_max - current_vision)
        return np.exp(-0.2 * headroom)
    
    @staticmethod
    def _calculate_treatment_effect(state: Dict, response_history: List[float], 
                                  headroom_factor: float) -> float:
        """Calculate vision improvement from treatment based on disease state"""
        disease_state = state.get("disease_state", DiseaseState.STABLE)
        
        # Adjust memory factor based on disease state
        if disease_state == DiseaseState.ACTIVE:
            memory_factor = 0.6  # Moderately reduced treatment memory
        elif disease_state == DiseaseState.STABLE:
            memory_factor = 0.7  # Normal treatment memory
        else:  # Remission
            memory_factor = 0.8  # Enhanced treatment memory
            
        # Calculate base effect from history
        base_effect = 0
        if response_history:
            base_effect = np.mean(response_history) * memory_factor
            if base_effect > 5:
                base_effect *= 0.8
        
        # Calculate treatment response with stronger biological constraints
        if state["current_step"] == "injection_phase" and state.get("injections", 0) < 3:
            # Loading phase
            if disease_state == DiseaseState.ACTIVE:
                mean, sigma = 1.0, 0.8  # Poor but positive response
            elif disease_state == DiseaseState.STABLE:
                mean, sigma = 3.0, 0.6  # Good response
            else:  # Remission
                mean, sigma = 1.2, 0.1  # Best response, extremely low variability
            random_effect = np.random.normal(mean, sigma)
        else:
            # Maintenance phase
            if disease_state == DiseaseState.ACTIVE:
                mean, sigma = -1.0, 0.8  # Moderate decline
                random_effect = min(0, np.random.normal(mean, sigma))  # Force negative
            elif disease_state == DiseaseState.STABLE:
                mean, sigma = 1.0, 0.6  # Mild improvement possible
                random_effect = np.random.normal(mean, sigma)
            else:  # Remission
                mean, sigma = 1.0, 0.05  # Consistent improvement, extremely low variability
                random_effect = np.clip(np.random.normal(mean, sigma), 0.8, 1.2)  # Very narrow range
        
        # Calculate final effect with headroom consideration
        return (base_effect + random_effect) * (1 - headroom_factor)
    
    @staticmethod
    def _calculate_natural_progression(state: Dict, response_history: List[float]) -> float:
        """Calculate natural vision changes between treatments based on disease state"""
        disease_state = state.get("disease_state", DiseaseState.STABLE)
        weeks_since_injection = state.get("weeks_since_last_injection", 0)
        current_vision = state["current_vision"]
        baseline_vision = state.get("baseline_vision", current_vision)
        
        # Adjust decline parameters based on disease state with tighter control in remission
        if disease_state == DiseaseState.HIGHLY_ACTIVE:
            mean, sigma = -1.5, 0.6  # Rapid decline, high variability
        elif disease_state == DiseaseState.ACTIVE:
            mean, sigma = -1.8, 0.5  # Moderate decline
        elif disease_state == DiseaseState.STABLE:
            mean, sigma = -2.0, 0.5  # Standard decline
        else:  # Remission
            mean, sigma = -1.0, 0.15  # Very slow decline, minimal variability
            
        base_decline = -np.random.lognormal(mean=mean, sigma=sigma)
        
        # Adjust time factor based on disease state
        if disease_state == DiseaseState.HIGHLY_ACTIVE:
            time_multiplier = 1.5  # Faster progression with time
        elif disease_state == DiseaseState.ACTIVE:
            time_multiplier = 1.2
        elif disease_state == DiseaseState.STABLE:
            time_multiplier = 1.0
        else:  # Remission
            time_multiplier = 0.8  # Slower progression with time
            
        time_factor = 1 + (weeks_since_injection/12) * time_multiplier
        
        # Vision factor reflects current disease control
        vision_factor = 1 + max(0, (current_vision - baseline_vision)/20)
        
        # Response factor reflects treatment history
        response_factor = 1.0
        if response_history:
            mean_response = np.mean(response_history)
            if disease_state == DiseaseState.HIGHLY_ACTIVE:
                response_weight = 0.05  # Minimal benefit from past responses
            elif disease_state == DiseaseState.ACTIVE:
                response_weight = 0.08
            elif disease_state == DiseaseState.STABLE:
                response_weight = 0.1
            else:  # Remission
                response_weight = 0.15  # Greater benefit from past responses
            response_factor = 1 + max(0, mean_response * response_weight)
            
        return base_decline * time_factor * vision_factor * response_factor
    
    @staticmethod
    def simulate_oct_findings(state: Dict) -> Dict:
        """Simulate OCT findings with realistic biological variation
        
        Args:
            state: Dictionary containing patient state including:
                - current_step: Current treatment phase
                - injections: Total injections received
                - next_visit_interval: Weeks until next visit
                - disease_state: Current DiseaseState (optional)
        
        Returns:
            Dict containing:
                - fluid_present: Boolean indicating fluid presence
                - fluid_type: Type of fluid present (IRF/SRF/None)
                - thickness_change: Change in retinal thickness
                - biomarkers: Dict of additional biomarkers
        """
        disease_state = state.get("disease_state", DiseaseState.STABLE)
        interval = state["next_visit_interval"]
        
        # Base risk adjusted by disease state - more extreme differences
        base_risk = 0.15 + (interval - 4) * 0.05
        if disease_state == DiseaseState.HIGHLY_ACTIVE:
            base_risk *= 2.5  # Much higher risk
        elif disease_state == DiseaseState.ACTIVE:
            base_risk *= 1.8  # Higher risk
        elif disease_state == DiseaseState.REMISSION:
            base_risk *= 0.25  # Much lower risk
            
        # Add random component from beta distribution
        risk_variation = np.random.beta(2, 5)
        fluid_risk = min(base_risk + risk_variation * 0.3, 1.0)
        
        # Determine fluid type based on disease state
        fluid_type = "none"
        if np.random.random() < fluid_risk:
            if disease_state == DiseaseState.HIGHLY_ACTIVE:
                fluid_type = "IRF+SRF" if np.random.random() < 0.6 else "IRF"
            elif disease_state == DiseaseState.ACTIVE:
                fluid_type = "SRF" if np.random.random() < 0.7 else "IRF"
            else:
                fluid_type = "SRF" if np.random.random() < 0.8 else "IRF"
        
        # Calculate thickness changes
        thickness_change = 0
        if state["current_step"] == "injection_phase":
            if state["injections"] < 3:
                # Strong improvement during loading
                thickness_change = -np.random.lognormal(mean=1.5, sigma=0.3)
            else:
                # Moderate improvement after loading
                thickness_change = -np.random.lognormal(mean=1.0, sigma=0.4)
        else:
            # Maintenance phase - changes depend on disease state
            if disease_state == DiseaseState.HIGHLY_ACTIVE:
                thickness_change = np.random.lognormal(mean=1.2, sigma=0.4)
            elif disease_state == DiseaseState.ACTIVE:
                thickness_change = np.random.lognormal(mean=0.8, sigma=0.5)
            elif disease_state == DiseaseState.STABLE:
                thickness_change = np.random.normal(0, 5)
            else:  # Remission
                thickness_change = -np.random.lognormal(mean=0.5, sigma=0.3)
        
        # Add biomarkers
        biomarkers = {
            "ped_present": np.random.random() < (0.3 if disease_state == DiseaseState.HIGHLY_ACTIVE else 0.1),
            "fibrosis_score": min(5, max(0, np.random.normal(
                2 if disease_state == DiseaseState.HIGHLY_ACTIVE else 1, 0.5))),
            "crt_baseline_ratio": np.random.normal(
                1.2 if disease_state in [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE] else 0.9, 0.1)
        }
        
        return {
            "fluid_present": fluid_type != "none",
            "fluid_type": fluid_type,
            "thickness_change": thickness_change,
            "biomarkers": biomarkers
        }
