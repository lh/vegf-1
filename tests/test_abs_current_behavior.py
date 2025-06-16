"""
Test suite to capture current ABS engine behavior.

This establishes a baseline for the time-based implementation.
We test the current per-visit transition model to understand
its behavior before implementing fortnightly updates.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.core.disease_model import DiseaseModel, DiseaseState
from simulation_v2.core.protocol import Protocol
from simulation_v2.protocols.protocol_spec import ProtocolSpecification


class TestABSCurrentBehavior:
    """Capture current ABS engine behavior for comparison."""
    
    @pytest.fixture
    def simple_protocol_spec(self):
        """Create a simple protocol for testing."""
        spec = {
            'name': 'test_protocol',
            'version': '1.0',
            'protocol_type': 'treat_and_extend',
            'min_interval_days': 28,
            'max_interval_days': 112,
            'extension_days': 14,
            'shortening_days': 14,
            'disease_transitions': {
                'NAIVE': {'NAIVE': 0.0, 'STABLE': 0.3, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.1},
                'STABLE': {'NAIVE': 0.0, 'STABLE': 0.85, 'ACTIVE': 0.15, 'HIGHLY_ACTIVE': 0.0},
                'ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.2, 'ACTIVE': 0.7, 'HIGHLY_ACTIVE': 0.1},
                'HIGHLY_ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.05, 'ACTIVE': 0.15, 'HIGHLY_ACTIVE': 0.8}
            },
            'treatment_effect_on_transitions': {
                'STABLE': {'multipliers': {'STABLE': 1.1, 'ACTIVE': 0.9}},
                'ACTIVE': {'multipliers': {'STABLE': 2.0, 'ACTIVE': 0.8, 'HIGHLY_ACTIVE': 0.5}},
                'HIGHLY_ACTIVE': {'multipliers': {'STABLE': 2.0, 'ACTIVE': 1.5, 'HIGHLY_ACTIVE': 0.75}}
            },
            'baseline_vision': {'mean': 70, 'std': 10, 'min': 20, 'max': 90},
            'vision_change_model': {
                'naive_treated': {'mean': 0.0, 'std': 1.0},
                'stable_treated': {'mean': 1.0, 'std': 1.0},
                'active_treated': {'mean': -1.0, 'std': 2.0},
                'highly_active_treated': {'mean': -2.0, 'std': 2.0}
            },
            'discontinuation_rules': {
                'poor_vision_threshold': 35,
                'poor_vision_probability': 0.1,
                'high_injection_count': 20,
                'high_injection_probability': 0.02
            }
        }
        return ProtocolSpecification(**spec)
    
    def test_patient_initialization(self, simple_protocol_spec):
        """Test that patients are initialized correctly."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=10,
            seed=42
        )
        
        # Run short simulation
        results = engine.run(duration_years=0.1)
        
        # Check all patients were created
        assert len(results.patient_histories) == 10
        
        # Check baseline vision distribution
        baseline_visions = []
        for patient in results.patient_histories.values():
            if patient.visit_history:
                baseline_visions.append(patient.visit_history[0]['vision'])
        
        # Should be roughly normal with mean ~70
        assert 50 <= np.mean(baseline_visions) <= 90
        assert 5 <= np.std(baseline_visions) <= 20
    
    def test_per_visit_transitions(self, simple_protocol_spec):
        """Test that disease transitions happen PER VISIT, not over time."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        # Run two simulations with same patients but different visit frequencies
        # Simulation 1: Force frequent visits (monthly)
        engine1 = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=100,
            seed=42
        )
        
        # Simulation 2: Force infrequent visits (quarterly)
        # We'll need to modify the protocol to achieve this
        spec2 = simple_protocol_spec
        spec2.min_interval_days = 84  # Force longer intervals
        protocol2 = Protocol(spec2)
        
        engine2 = ABSEngine(
            disease_model=disease_model,
            protocol=protocol2,
            n_patients=100,
            seed=42  # Same seed for same initial patients
        )
        
        results1 = engine1.run(duration_years=2)
        results2 = engine2.run(duration_years=2)
        
        # Count state transitions for each
        transitions1 = self._count_transitions(results1)
        transitions2 = self._count_transitions(results2)
        
        # With current per-visit model, more visits = more transitions
        # This is the bug we're fixing!
        assert transitions1 > transitions2 * 1.5, \
            f"Expected more transitions with frequent visits: {transitions1} vs {transitions2}"
    
    def test_treatment_effect_on_transitions(self, simple_protocol_spec):
        """Test that treatment affects transition probabilities."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=200,
            seed=42
        )
        
        results = engine.run(duration_years=3)
        
        # Analyze transitions from ACTIVE state
        active_transitions_treated = []
        active_transitions_untreated = []
        
        for patient in results.patient_histories.values():
            visits = patient.visit_history
            for i in range(1, len(visits)):
                prev_visit = visits[i-1]
                curr_visit = visits[i]
                
                if prev_visit['disease_state'] == DiseaseState.ACTIVE:
                    if prev_visit.get('treatment_given', False):
                        active_transitions_treated.append(curr_visit['disease_state'])
                    else:
                        active_transitions_untreated.append(curr_visit['disease_state'])
        
        # Calculate transition rates to STABLE
        if active_transitions_treated:
            treated_to_stable = sum(1 for s in active_transitions_treated 
                                  if s == DiseaseState.STABLE) / len(active_transitions_treated)
        else:
            treated_to_stable = 0
            
        if active_transitions_untreated:
            untreated_to_stable = sum(1 for s in active_transitions_untreated 
                                    if s == DiseaseState.STABLE) / len(active_transitions_untreated)
        else:
            untreated_to_stable = 0
        
        # Treatment should increase transitions to STABLE (multiplier = 2.0)
        assert treated_to_stable > untreated_to_stable, \
            f"Treatment should improve stability: {treated_to_stable:.2f} vs {untreated_to_stable:.2f}"
    
    def test_vision_changes_per_visit(self, simple_protocol_spec):
        """Test that vision changes are applied per visit."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=50,
            seed=42
        )
        
        results = engine.run(duration_years=2)
        
        # Calculate vision changes between visits
        vision_changes = []
        for patient in results.patient_histories.values():
            visits = patient.visit_history
            for i in range(1, len(visits)):
                change = visits[i]['vision'] - visits[i-1]['vision']
                vision_changes.append(change)
        
        # Vision changes should be discrete per visit
        # In current model: STABLE gains 0-2, ACTIVE loses -1 to 1 or -3 to -1
        assert len(vision_changes) > 0
        assert all(isinstance(change, (int, float)) for change in vision_changes)
        
        # Most changes should be small integers
        change_counts = {}
        for change in vision_changes:
            rounded = round(change)
            change_counts[rounded] = change_counts.get(rounded, 0) + 1
        
        # Verify changes cluster around expected values
        common_changes = sorted(change_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        common_values = [change for change, count in common_changes]
        
        # Should see mostly -3 to +2 range
        assert any(-3 <= v <= 2 for v in common_values)
    
    def test_discontinuation_per_visit(self, simple_protocol_spec):
        """Test that discontinuation checks happen per visit."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        # Run with many patients to get discontinuation statistics
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=500,
            seed=42
        )
        
        results = engine.run(duration_years=3)
        
        # Track discontinuations by visit count
        discontinuations_by_visit_count = {}
        
        for patient in results.patient_histories.values():
            if patient.is_discontinued:
                visit_count = len(patient.visit_history)
                discontinuations_by_visit_count[visit_count] = \
                    discontinuations_by_visit_count.get(visit_count, 0) + 1
        
        # With per-visit discontinuation, patients with more visits
        # have more chances to discontinue
        assert len(discontinuations_by_visit_count) > 0
        
        # Calculate discontinuation rate
        total_discontinued = sum(1 for p in results.patient_histories.values() 
                               if p.is_discontinued)
        disc_rate = total_discontinued / len(results.patient_histories)
        
        assert 0 < disc_rate < 1, f"Discontinuation rate should be reasonable: {disc_rate}"
    
    def test_treatment_decision_at_visits(self, simple_protocol_spec):
        """Test that treatment decisions are made at each visit."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=20,
            seed=42
        )
        
        results = engine.run(duration_years=1)
        
        # Check that treatment decisions align with disease states
        for patient in results.patient_histories.values():
            for visit in patient.visit_history:
                # In T&E protocol, treatment is based on disease activity
                if 'treatment_given' in visit:
                    state = visit['disease_state']
                    treated = visit['treatment_given']
                    
                    # Active/Highly active should usually get treatment
                    if state in [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE]:
                        assert treated in [True, False]  # Protocol decides
    
    def test_visit_intervals(self, simple_protocol_spec):
        """Test that visit intervals follow protocol rules."""
        disease_model = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=42
        )
        protocol = Protocol(simple_protocol_spec)
        
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=20,
            seed=42
        )
        
        results = engine.run(duration_years=2)
        
        # Check visit intervals
        all_intervals = []
        for patient in results.patient_histories.values():
            visits = patient.visit_history
            for i in range(1, len(visits)):
                interval = (visits[i]['date'] - visits[i-1]['date']).days
                all_intervals.append(interval)
        
        # All intervals should be within protocol bounds
        assert all(28 <= interval <= 112 for interval in all_intervals), \
            f"Some intervals outside bounds: {[i for i in all_intervals if not (28 <= i <= 112)]}"
        
        # Should see variety of intervals based on disease state
        unique_intervals = set(all_intervals)
        assert len(unique_intervals) > 1, "Should see varied intervals"
    
    def test_deterministic_with_seed(self, simple_protocol_spec):
        """Test that simulations are deterministic with same seed."""
        disease_model1 = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=12345
        )
        protocol1 = Protocol(simple_protocol_spec)
        
        disease_model2 = DiseaseModel(
            simple_protocol_spec.disease_transitions,
            simple_protocol_spec.treatment_effect_on_transitions,
            seed=12345
        )
        protocol2 = Protocol(simple_protocol_spec)
        
        engine1 = ABSEngine(
            disease_model=disease_model1,
            protocol=protocol1,
            n_patients=50,
            seed=12345
        )
        
        engine2 = ABSEngine(
            disease_model=disease_model2,
            protocol=protocol2,
            n_patients=50,
            seed=12345
        )
        
        results1 = engine1.run(duration_years=1)
        results2 = engine2.run(duration_years=1)
        
        # Same seed should give identical results
        assert results1.total_injections == results2.total_injections
        assert abs(results1.final_vision_mean - results2.final_vision_mean) < 0.01
        assert results1.discontinuation_rate == results2.discontinuation_rate
    
    def _count_transitions(self, results):
        """Count total disease state transitions."""
        transitions = 0
        for patient in results.patient_histories.values():
            visits = patient.visit_history
            for i in range(1, len(visits)):
                if visits[i]['disease_state'] != visits[i-1]['disease_state']:
                    transitions += 1
        return transitions


class TestVisitFrequencyBug:
    """Specific tests to demonstrate the visit-frequency bug."""
    
    def test_progression_depends_on_visit_frequency(self):
        """Demonstrate that disease progression incorrectly depends on visit frequency."""
        # Create identical protocols except for visit intervals
        base_transitions = {
            'NAIVE': {'NAIVE': 0.0, 'STABLE': 0.3, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.1},
            'STABLE': {'NAIVE': 0.0, 'STABLE': 0.7, 'ACTIVE': 0.3, 'HIGHLY_ACTIVE': 0.0},
            'ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.1, 'ACTIVE': 0.7, 'HIGHLY_ACTIVE': 0.2},
            'HIGHLY_ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.0, 'ACTIVE': 0.1, 'HIGHLY_ACTIVE': 0.9}
        }
        
        # Protocol 1: Frequent visits (4-week intervals)
        spec1 = {
            'name': 'frequent_visits',
            'version': '1.0',
            'protocol_type': 'fixed',  # Use fixed intervals for clearer demonstration
            'fixed_interval_days': 28,
            'disease_transitions': base_transitions,
            'baseline_vision': {'mean': 70, 'std': 10, 'min': 20, 'max': 90},
            'vision_change_model': {},
            'discontinuation_rules': {'poor_vision_threshold': 0, 'poor_vision_probability': 0}
        }
        
        # Protocol 2: Infrequent visits (12-week intervals)
        spec2 = spec1.copy()
        spec2['name'] = 'infrequent_visits'
        spec2['fixed_interval_days'] = 84  # 12 weeks
        
        # Run simulations
        disease_model1 = DiseaseModel(base_transitions, seed=999)
        disease_model2 = DiseaseModel(base_transitions, seed=999)
        
        protocol1 = Protocol(ProtocolSpecification(**spec1))
        protocol2 = Protocol(ProtocolSpecification(**spec2))
        
        engine1 = ABSEngine(disease_model1, protocol1, n_patients=200, seed=999)
        engine2 = ABSEngine(disease_model2, protocol2, n_patients=200, seed=999)
        
        results1 = engine1.run(duration_years=3)
        results2 = engine2.run(duration_years=3)
        
        # Count how many patients progressed to HIGHLY_ACTIVE
        highly_active_count1 = sum(1 for p in results1.patient_histories.values()
                                  if p.current_state == DiseaseState.HIGHLY_ACTIVE)
        highly_active_count2 = sum(1 for p in results2.patient_histories.values()
                                  if p.current_state == DiseaseState.HIGHLY_ACTIVE)
        
        # BUG: More frequent visits lead to more progression!
        assert highly_active_count1 > highly_active_count2 * 1.5, \
            f"Frequent visits: {highly_active_count1}, Infrequent: {highly_active_count2}"
        
        print(f"\nDemonstrated bug: ")
        print(f"4-week visits: {highly_active_count1}/{len(results1.patient_histories)} highly active")
        print(f"12-week visits: {highly_active_count2}/{len(results2.patient_histories)} highly active")
        print(f"Ratio: {highly_active_count1/max(1, highly_active_count2):.2f}x more with frequent visits!")


if __name__ == "__main__":
    # Run specific test to show the bug
    test = TestVisitFrequencyBug()
    test.test_progression_depends_on_visit_frequency()