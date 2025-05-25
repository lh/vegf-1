"""
Test disease model with FOV (Four Option Version) states.

Testing strategy:
1. Disease states are enums
2. Transitions are probabilistic but testable with seeds
3. No fluid detection involved
"""

import pytest
from enum import Enum
from simulation_v2.core.disease_model import DiseaseState, DiseaseModel


class TestDiseaseState:
    """Test the disease state enum."""
    
    def test_disease_states_exist(self):
        """FOV model should have exactly 4 states."""
        assert DiseaseState.NAIVE.value == 0
        assert DiseaseState.STABLE.value == 1
        assert DiseaseState.ACTIVE.value == 2
        assert DiseaseState.HIGHLY_ACTIVE.value == 3
        
    def test_disease_state_names(self):
        """States should have correct names."""
        assert DiseaseState.NAIVE.name == "NAIVE"
        assert DiseaseState.STABLE.name == "STABLE"
        assert DiseaseState.ACTIVE.name == "ACTIVE"
        assert DiseaseState.HIGHLY_ACTIVE.name == "HIGHLY_ACTIVE"
        
    def test_no_fluid_detection_state(self):
        """Ensure we don't have any fluid-based states."""
        state_names = [s.name for s in DiseaseState]
        assert "FLUID_DETECTED" not in state_names
        assert "FLUID" not in " ".join(state_names)


class TestDiseaseModel:
    """Test disease state transitions and behavior."""
    
    def test_model_creation(self):
        """Should create model with transition probabilities."""
        model = DiseaseModel()
        assert model is not None
        assert hasattr(model, 'transition_probabilities')
        
    def test_naive_transitions(self):
        """NAIVE patients should transition to other states."""
        model = DiseaseModel(seed=42)
        
        # Run 100 transitions from NAIVE
        outcomes = []
        for i in range(100):
            model = DiseaseModel(seed=i)  # Different seeds
            new_state = model.transition(DiseaseState.NAIVE)
            outcomes.append(new_state)
            
        # Should never stay NAIVE
        assert DiseaseState.NAIVE not in outcomes
        
        # Should transition to all other states with expected proportions
        assert DiseaseState.STABLE in outcomes
        assert DiseaseState.ACTIVE in outcomes
        assert DiseaseState.HIGHLY_ACTIVE in outcomes
        
        # Rough proportion check (with 100 samples)
        stable_count = outcomes.count(DiseaseState.STABLE)
        active_count = outcomes.count(DiseaseState.ACTIVE)
        highly_active_count = outcomes.count(DiseaseState.HIGHLY_ACTIVE)
        
        # Literature suggests roughly 30% stable, 60% active, 10% highly active
        assert 20 <= stable_count <= 40  # 30% ± 10%
        assert 50 <= active_count <= 70   # 60% ± 10%
        assert 5 <= highly_active_count <= 15  # 10% ± 5%
        
    def test_stable_can_deteriorate(self):
        """STABLE patients can deteriorate to ACTIVE."""
        model = DiseaseModel()
        
        # With enough transitions, should see deterioration
        outcomes = []
        for i in range(100):
            model = DiseaseModel(seed=i)
            new_state = model.transition(DiseaseState.STABLE)
            outcomes.append(new_state)
            
        # Most stay stable, but some deteriorate
        assert DiseaseState.STABLE in outcomes
        assert DiseaseState.ACTIVE in outcomes
        
    def test_treatment_affects_transitions(self):
        """Treatment should improve transition probabilities."""
        model = DiseaseModel()
        
        # Without treatment
        no_treatment_outcomes = []
        for i in range(50):
            model = DiseaseModel(seed=i)
            new_state = model.transition(DiseaseState.ACTIVE, treated=False)
            no_treatment_outcomes.append(new_state)
            
        # With treatment  
        treatment_outcomes = []
        for i in range(50):
            model = DiseaseModel(seed=i)
            new_state = model.transition(DiseaseState.ACTIVE, treated=True)
            treatment_outcomes.append(new_state)
            
        # Treatment should lead to more stable outcomes
        stable_without = no_treatment_outcomes.count(DiseaseState.STABLE)
        stable_with = treatment_outcomes.count(DiseaseState.STABLE)
        assert stable_with > stable_without
        
    def test_no_fluid_detection_in_logic(self):
        """Ensure transitions don't depend on fluid detection."""
        model = DiseaseModel()
        
        # The transition method should not accept fluid_detected parameter
        with pytest.raises(TypeError):
            model.transition(DiseaseState.ACTIVE, fluid_detected=True)
            
    def test_configurable_probabilities(self):
        """Model should accept custom transition probabilities."""
        custom_probs = {
            DiseaseState.NAIVE: {
                DiseaseState.STABLE: 0.5,
                DiseaseState.ACTIVE: 0.4,
                DiseaseState.HIGHLY_ACTIVE: 0.1
            }
        }
        
        model = DiseaseModel(transition_probabilities=custom_probs)
        
        # Verify custom probabilities are used
        # (would need to test with many samples to verify statistically)