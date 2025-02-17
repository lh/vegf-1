from typing import Dict
import numpy as np

class ClinicalModel:
    """Models clinical aspects like vision changes and OCT findings"""
    
    @staticmethod
    def simulate_vision_change(state: Dict) -> float:
        """Calculate vision change with memory and ceiling effects
        
        Args:
            state: Dictionary containing patient state including:
                - current_vision: Current ETDRS letter score
                - best_vision_achieved: Best vision achieved so far
                - baseline_vision: Initial vision at treatment start
                - last_treatment_response: Previous treatment effect
                - treatment_response_history: List of previous responses
                - current_step: Current treatment phase
                - injections: Total injections received
                - weeks_since_last_injection: Time since last injection
        
        Returns:
            float: Change in vision (can be positive or negative)
        """
        # Get reference points
        current_vision = state["current_vision"]
        best_vision = state.get("best_vision_achieved", current_vision)
        baseline_vision = state.get("baseline_vision", current_vision)
        response_history = state.get("treatment_response_history", [])
        
        # Calculate headroom (ceiling effect)
        absolute_max = 85  # ETDRS letter score maximum
        theoretical_max = min(absolute_max, best_vision + 5)
        headroom = max(0, theoretical_max - current_vision)
        headroom_factor = np.exp(-0.2 * headroom)
        
        # Check if this is an injection visit
        is_injection = state.get("injections", 0) > state.get("last_recorded_injection", -1)
        
        if is_injection:
            return ClinicalModel._calculate_treatment_effect(
                state, response_history, headroom_factor)
        else:
            return ClinicalModel._calculate_natural_progression(
                state, response_history)
    
    @staticmethod
    def _calculate_treatment_effect(state: Dict, response_history: List[float], 
                                  headroom_factor: float) -> float:
        """Calculate vision improvement from treatment"""
        # Treatment effect parameters
        memory_factor = 0.7
        base_effect = 0
        
        if response_history:
            base_effect = np.mean(response_history) * memory_factor
            if base_effect > 5:
                base_effect *= 0.8
        
        # Different behavior for loading phase vs maintenance
        if state["current_step"] == "injection_phase" and state.get("injections", 0) < 3:
            random_effect = np.random.lognormal(mean=1.2, sigma=0.3)
        else:
            random_effect = np.random.lognormal(mean=0.5, sigma=0.4)
        
        return (base_effect + random_effect) * (1 - headroom_factor)
    
    @staticmethod
    def _calculate_natural_progression(state: Dict, response_history: List[float]) -> float:
        """Calculate natural vision changes between treatments"""
        weeks_since_injection = state.get("weeks_since_last_injection", 0)
        current_vision = state["current_vision"]
        baseline_vision = state.get("baseline_vision", current_vision)
        
        base_decline = -np.random.lognormal(mean=-2.0, sigma=0.5)
        
        time_factor = 1 + (weeks_since_injection/12)
        vision_factor = 1 + max(0, (current_vision - baseline_vision)/20)
        response_factor = 1.0
        
        if response_history:
            mean_response = np.mean(response_history)
            response_factor = 1 + max(0, mean_response/10)
            
        return base_decline * time_factor * vision_factor * response_factor
    
    @staticmethod
    def simulate_oct_findings(state: Dict) -> Dict:
        """Simulate OCT findings with realistic biological variation
        
        Args:
            state: Dictionary containing patient state including:
                - current_step: Current treatment phase
                - injections: Total injections received
                - next_visit_interval: Weeks until next visit
        
        Returns:
            Dict containing:
                - fluid_present: Boolean indicating fluid presence
                - thickness_change: Change in retinal thickness
        """
        # Base risk increases with interval length
        interval = state["next_visit_interval"]
        base_risk = 0.2 + (interval - 4) * 0.05
        
        # Add random component from beta distribution
        risk_variation = np.random.beta(2, 5)
        fluid_risk = min(base_risk + risk_variation * 0.3, 1.0)
        
        # Thickness changes based on treatment phase
        if state["current_step"] == "injection_phase":
            if state["injections"] < 3:
                # Strong improvement during loading
                thickness_change = -np.random.lognormal(mean=1.5, sigma=0.3)
            else:
                # Moderate improvement after loading
                thickness_change = -np.random.lognormal(mean=1.0, sigma=0.4)
        else:
            # Maintenance phase - changes depend on interval
            if fluid_risk > 0.5:
                # Disease activity - thickness increases
                thickness_change = np.random.lognormal(mean=1.0, sigma=0.5)
            else:
                # Stable - small variations
                thickness_change = np.random.normal(0, 5)
        
        return {
            "fluid_present": np.random.random() < fluid_risk,
            "thickness_change": thickness_change
        }
