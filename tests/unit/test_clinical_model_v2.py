import pytest
import numpy as np
from simulation.clinical_model import ClinicalModel, DiseaseState

def test_transition_probabilities():
    """Test that disease state transitions are biologically plausible"""
    for state in DiseaseState:
        probs = ClinicalModel.get_transition_probabilities(state)
        
        # Each transition should have a valid probability
        for next_state, prob in probs.items():
            assert 0 <= prob <= 1, f"Probability for {state} to {next_state} should be between 0 and 1"
        
        # Verify biological relationships
        if state == DiseaseState.STABLE:
            assert probs[DiseaseState.ACTIVE] > probs[DiseaseState.HIGHLY_ACTIVE], \
                "From STABLE state, progression to ACTIVE should be more likely than to HIGHLY_ACTIVE"
        elif state == DiseaseState.ACTIVE:
            assert probs[DiseaseState.HIGHLY_ACTIVE] > probs[DiseaseState.STABLE], \
                "From ACTIVE state, progression should be more likely than improvement"

def test_disease_progression():
    """Test that disease progression follows expected patterns"""
    initial_state = {
        "disease_state": DiseaseState.STABLE,
        "weeks_since_last_injection": 4
    }
    
    # Simulate progression over multiple time points
    n_trajectories = 1000
    n_steps = 12  # Simulate 12 time points
    
    trajectories = []
    for _ in range(n_trajectories):
        state = initial_state.copy()
        trajectory = []
        
        for _ in range(n_steps):
            new_state = ClinicalModel.simulate_disease_progression(state)
            trajectory.append(new_state)
            state["disease_state"] = new_state
            
        trajectories.append(trajectory)
    
    # Analyze progression patterns
    for step in range(n_steps):
        states_at_step = [t[step] for t in trajectories]
        
        # Calculate proportions
        active_rate = sum(1 for s in states_at_step if s in 
                         [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE]) / n_trajectories
        
        # Test time-dependent progression
        if step > 8:  # After significant time
            assert active_rate > 0.3, \
                f"Disease activity should increase over time, got {active_rate:.2f} at step {step}"

def test_vision_change():
    """Test that vision changes are biologically plausible"""
    base_state = {
        "disease_state": DiseaseState.STABLE,
        "injections": 3,
        "last_recorded_injection": 2
    }
    
    n_samples = 1000
    
    for state in DiseaseState:
        test_state = base_state.copy()
        test_state["disease_state"] = state
        
        injection_changes = []
        non_injection_changes = []
        
        for _ in range(n_samples):
            # Test injection visit
            test_state["injections"] = test_state["last_recorded_injection"] + 1
            injection_changes.append(ClinicalModel.simulate_vision_change(test_state))
            
            # Test non-injection visit
            test_state["injections"] = test_state["last_recorded_injection"]
            non_injection_changes.append(ClinicalModel.simulate_vision_change(test_state))
        
        # Verify biological constraints
        assert np.mean(injection_changes) > 0, f"{state}: Injection visits should show mean vision improvement"
        assert np.mean(non_injection_changes) < 0, f"{state}: Non-injection visits should show mean vision decline"
        
        if state == DiseaseState.HIGHLY_ACTIVE:
            assert np.mean(non_injection_changes) < np.mean(injection_changes), \
                f"{state}: Vision decline without treatment should be more severe than with treatment"
