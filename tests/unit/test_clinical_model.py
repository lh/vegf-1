import pytest
import numpy as np
from datetime import datetime
from simulation.clinical_model import ClinicalModel, DiseaseState
from simulation.config import SimulationConfig
from protocol_models import TreatmentProtocol, LoadingPhase, PhaseType

@pytest.fixture
def config():
    # Create a minimal TreatmentProtocol mock
    # Create a minimal LoadingPhase for the protocol
    loading_phase = LoadingPhase(
        phase_type=PhaseType.LOADING,
        duration_weeks=12,
        visit_interval_weeks=4,
        required_treatments=3
    )
    
    protocol = TreatmentProtocol(
        agent="test_agent",
        protocol_name="test_protocol",
        version="1.0",
        description="Test protocol",
        phases={"loading": loading_phase},
        parameters={}
    )
    
    # Create configuration parameters
    parameters = {
        "clinical_model": {
            "disease_states": ["NAIVE", "STABLE", "ACTIVE", "HIGHLY_ACTIVE"],
            "transition_probabilities": {
                "NAIVE": {"STABLE": 0.3, "ACTIVE": 0.6, "HIGHLY_ACTIVE": 0.1},
                "STABLE": {"STABLE": 0.7, "ACTIVE": 0.3},
                "ACTIVE": {"STABLE": 0.4, "ACTIVE": 0.4, "HIGHLY_ACTIVE": 0.2},
                "HIGHLY_ACTIVE": {"STABLE": 0.2, "ACTIVE": 0.3, "HIGHLY_ACTIVE": 0.5}
            },
            "vision_change": {
                "base_change": {
                    "STABLE": {"injection": [5, 2], "no_injection": [0, 1]},
                    "ACTIVE": {"injection": [3, 2], "no_injection": [-2, 1]},
                    "HIGHLY_ACTIVE": {"injection": [1, 2], "no_injection": [-5, 1]}
                },
                "time_factor": {"max_weeks": 52},
                "ceiling_factor": {"max_vision": 100},
                "measurement_noise": [0, 0.5]
            }
        },
        "vision": {
            "baseline_mean": 70,
            "baseline_sd": 5,
            "measurement_noise_sd": 0.5,
            "max_letters": 100,
            "min_letters": 0,
            "headroom_factor": 0.8
        }
    }
    
    return SimulationConfig(
        parameters=parameters,
        protocol=protocol,
        simulation_type="test",
        num_patients=100,
        duration_days=365,
        random_seed=42,
        verbose=False,
        start_date=datetime.now(),
        resources=None
    )

def test_disease_state_transitions(config):
    """Test that disease state transitions are valid and respect probabilities"""
    model = ClinicalModel(config)
    
    # Test transition probability calculation
    probs = model.get_transition_probabilities(DiseaseState.STABLE)
    # Each probability should be between 0 and 1
    assert all(0 <= p <= 1 for p in probs.values())
    
    # Test state progression
    new_state = model.simulate_disease_progression(DiseaseState.STABLE)
    assert isinstance(new_state, DiseaseState)

def test_vision_change_with_disease_states(config):
    """Test vision changes incorporate disease state effects"""
    model = ClinicalModel(config)
    
    base_state = {
        "disease_state": DiseaseState.STABLE,
        "current_vision": 70,
        "injections": 5,
        "last_recorded_injection": 4,
        "weeks_since_last_injection": 4
    }
    
    # Test vision changes in different disease states
    np.random.seed(42)  # For reproducibility
    
    # Highly active state should show more decline
    highly_active_state = base_state.copy()
    highly_active_state["disease_state"] = DiseaseState.HIGHLY_ACTIVE
    highly_active_change, _ = model.simulate_vision_change(highly_active_state)
    
    # Stable state should show more improvement
    stable_state = base_state.copy()
    stable_state["disease_state"] = DiseaseState.STABLE
    stable_change, _ = model.simulate_vision_change(stable_state)
    
    # Natural progression should be worse for highly active state
    assert highly_active_change < stable_change
    
    # Test treatment effects in different states
    injection_state = base_state.copy()
    injection_state["injections"] = 6  # Trigger injection
    
    # Test multiple samples to account for randomness
    n_samples = 100
    highly_active_effects = []
    stable_effects = []
    
    for _ in range(n_samples):
        test_state = injection_state.copy()
        test_state["disease_state"] = DiseaseState.HIGHLY_ACTIVE
        change, _ = model.simulate_vision_change(test_state)
        highly_active_effects.append(change)
        
        test_state["disease_state"] = DiseaseState.STABLE
        change, _ = model.simulate_vision_change(test_state)
        stable_effects.append(change)
    
    # On average, stable state should show better treatment response
    assert np.mean(stable_effects) > np.mean(highly_active_effects)

def test_vision_change_with_injection(config):
    """Test vision changes incorporate injection effects"""
    model = ClinicalModel(config)
    
    base_state = {
        "disease_state": DiseaseState.STABLE,
        "current_vision": 70,
        "injections": 5,
        "last_recorded_injection": 4,
        "weeks_since_last_injection": 4
    }
    
    # Test injection vs non-injection
    np.random.seed(42)  # For reproducibility
    
    # Non-injection visit
    non_injection_state = base_state.copy()
    non_injection_change, _ = model.simulate_vision_change(non_injection_state)
    
    # Injection visit
    injection_state = base_state.copy()
    injection_state["injections"] = 6  # Trigger injection
    injection_change, _ = model.simulate_vision_change(injection_state)
    
    # Test multiple samples to account for randomness
    n_samples = 100
    injection_effects = []
    non_injection_effects = []
    
    for _ in range(n_samples):
        test_state = base_state.copy()
        change, _ = model.simulate_vision_change(test_state)
        non_injection_effects.append(change)
        
        test_state["injections"] = 6
        change, _ = model.simulate_vision_change(test_state)
        injection_effects.append(change)
    
    # Verify there's a statistically significant difference between injection and non-injection
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(injection_effects, non_injection_effects)
    assert p_value < 0.05  # Significant at 95% confidence level

def test_treatment_response_variation(config):
    """Test that treatment response varies appropriately with disease state"""
    model = ClinicalModel(config)
    
    base_state = {
        "current_vision": 70,
        "injections": 6,  # Trigger injection
        "last_recorded_injection": 5,
        "weeks_since_last_injection": 4
    }
    
    responses = {
        DiseaseState.STABLE: [],
        DiseaseState.ACTIVE: [], 
        DiseaseState.HIGHLY_ACTIVE: []
    }
    n_samples = 100
    
    for state in responses.keys():
        test_state = base_state.copy()
        test_state["disease_state"] = state
        
        for _ in range(n_samples):
            change, _ = model.simulate_vision_change(test_state)
            responses[state].append(change)
    
    # Calculate mean responses
    mean_responses = {state: np.mean(resp) for state, resp in responses.items()}
    
    # Verify response patterns - better states should have better responses
    assert mean_responses[DiseaseState.STABLE] > mean_responses[DiseaseState.ACTIVE]
    assert mean_responses[DiseaseState.ACTIVE] > mean_responses[DiseaseState.HIGHLY_ACTIVE]

def test_initial_vision(config):
    """Test that initial vision values are generated correctly"""
    model = ClinicalModel(config)
    vision_values = [model.get_initial_vision() for _ in range(1000)]
    
    # Should be normally distributed around baseline mean
    assert 65 <= np.mean(vision_values) <= 75  # Within 1 SD of baseline_mean=70
    assert min(vision_values) >= 0  # Vision can't be negative
    assert max(vision_values) <= 100  # Vision can't exceed max
