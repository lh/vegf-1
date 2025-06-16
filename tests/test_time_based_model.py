#!/usr/bin/env python3
"""
Comprehensive test suite for time-based disease model.

Tests cover:
1. Disease state transitions (fortnightly updates)
2. Vision mechanics (bimodal loss, improvement, ceilings)
3. Discontinuation system (all 6 reasons)
4. Mortality model integration
5. Demographics and gender distribution
6. Treatment effects and decay
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.engines.abs_engine_time_based_with_params import ABSEngineTimeBasedWithParams
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseState
from simulation_v2.core.discontinuation_checker import DiscontinuationChecker
from simulation_v2.models.mortality import MortalityModel, PopulationMortalityModel


class TestDiseaseModelTimeBased:
    """Test the time-based disease model."""
    
    @pytest.fixture
    def disease_model(self):
        """Create a disease model for testing."""
        params_dir = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters"
        return DiseaseModelTimeBased.from_parameter_files(params_dir, seed=42)
    
    def test_fortnightly_updates(self, disease_model):
        """Test that disease states update every 14 days."""
        # Test update interval
        assert disease_model.UPDATE_INTERVAL_DAYS == 14
        
        # Test state transitions
        current_state = DiseaseState.ACTIVE
        days_since_injection = 30
        current_date = datetime.now()
        
        # Run multiple updates and check for state changes
        states_seen = set()
        for _ in range(100):
            new_state = disease_model.update_state("TEST_PATIENT", current_state, current_date, days_since_injection)
            states_seen.add(new_state)
            current_state = new_state
        
        # Should see multiple states due to transitions
        assert len(states_seen) > 1
    
    def test_treatment_effect_on_transitions(self, disease_model):
        """Test that treatment affects state transitions."""
        # Compare transitions with and without recent treatment
        treated_transitions = []
        untreated_transitions = []
        current_date = datetime.now()
        
        for i in range(1000):
            # Recently treated (10 days since injection)
            treated_state = disease_model.update_state(f"PATIENT_{i}", DiseaseState.ACTIVE, current_date, 10)
            treated_transitions.append(treated_state == DiseaseState.STABLE)
            
            # Not recently treated (90 days since injection)
            untreated_state = disease_model.update_state(f"PATIENT_{i}_B", DiseaseState.ACTIVE, current_date, 90)
            untreated_transitions.append(untreated_state == DiseaseState.STABLE)
        
        # Treated patients should transition to STABLE more often
        treated_stable_rate = sum(treated_transitions) / len(treated_transitions)
        untreated_stable_rate = sum(untreated_transitions) / len(untreated_transitions)
        
        assert treated_stable_rate > untreated_stable_rate


class TestVisionMechanics:
    """Test vision loss, improvement, and ceiling mechanics."""
    
    @pytest.fixture
    def engine(self):
        """Create an engine with vision mechanics."""
        params_dir = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters"
        disease_model = DiseaseModelTimeBased.from_parameter_files(params_dir, seed=42)
        
        protocol_spec = TimeBasedProtocolSpecification.from_yaml(
            Path(__file__).parent.parent / "protocols" / "v2_time_based" / "eylea_time_based.yaml"
        )
        
        protocol = StandardProtocol(
            min_interval_days=protocol_spec.min_interval_days,
            max_interval_days=protocol_spec.max_interval_days,
            extension_days=protocol_spec.extension_days,
            shortening_days=protocol_spec.shortening_days
        )
        
        return ABSEngineTimeBasedWithParams(
            disease_model=disease_model,
            protocol=protocol,
            protocol_spec=protocol_spec,
            n_patients=10,
            seed=42
        )
    
    def test_vision_ceiling_calculation(self, engine):
        """Test that vision ceilings are calculated correctly."""
        patient = Patient("TEST001", baseline_vision=70)
        patient.age_years = 75
        patient.sex = 'female'
        
        engine._initialize_patient_vision("TEST001", patient, datetime.now())
        
        # Check ceiling exists and is reasonable
        ceiling = engine.patient_vision_ceiling["TEST001"]
        assert ceiling > patient.baseline_vision  # Should be above baseline
        assert ceiling <= 85  # Shouldn't exceed max ceiling
        
        # Test different baseline visions
        for baseline in [50, 60, 70, 80]:
            patient2 = Patient(f"TEST{baseline}", baseline_vision=baseline)
            patient2.age_years = 75
            patient2.sex = 'female'
            engine._initialize_patient_vision(f"TEST{baseline}", patient2, datetime.now())
            
            ceiling = engine.patient_vision_ceiling[f"TEST{baseline}"]
            # Higher baseline should generally have higher ceiling
            assert ceiling >= baseline
    
    def test_bimodal_vision_loss(self, engine):
        """Test gradual decline and catastrophic hemorrhage."""
        patient = Patient("TEST002", baseline_vision=70)
        patient.age_years = 75
        patient.sex = 'male'
        patient.current_state = DiseaseState.HIGHLY_ACTIVE
        
        engine._initialize_patient_vision("TEST002", patient, datetime.now())
        
        # Track vision changes over many updates
        vision_changes = []
        catastrophic_losses = 0
        
        for _ in range(1000):
            initial_vision = engine.patient_actual_vision["TEST002"]
            engine._update_patient_vision("TEST002", patient, datetime.now())
            final_vision = engine.patient_actual_vision["TEST002"]
            
            change = final_vision - initial_vision
            vision_changes.append(change)
            
            # Check for catastrophic loss (> 15 letters)
            if change < -15:
                catastrophic_losses += 1
        
        # Should see mostly gradual changes
        gradual_changes = [c for c in vision_changes if -5 < c < 5]
        assert len(gradual_changes) > len(vision_changes) * 0.8
        
        # But should see some hemorrhages in HIGHLY_ACTIVE state
        assert catastrophic_losses > 0
        assert catastrophic_losses < len(vision_changes) * 0.1  # Rare but possible
    
    def test_vision_improvement_mechanics(self, engine):
        """Test that vision can improve after treatment."""
        patient = Patient("TEST003", baseline_vision=60)
        patient.age_years = 70
        patient.sex = 'female'
        patient.current_state = DiseaseState.ACTIVE
        patient.injection_count = 1  # First injection
        patient._last_injection_date = datetime.now() - timedelta(days=7)
        
        engine._initialize_patient_vision("TEST003", patient, datetime.now())
        
        # Force improvement eligibility check
        improvements = 0
        for _ in range(100):
            initial_vision = engine.patient_actual_vision["TEST003"]
            engine._update_patient_vision("TEST003", patient, datetime.now())
            final_vision = engine.patient_actual_vision["TEST003"]
            
            if final_vision > initial_vision:
                improvements += 1
        
        # Should see some improvements
        assert improvements > 0
        
        # Test that improvement stops after max duration
        vision_state = engine.patient_vision_states["TEST003"]
        vision_state.is_improving = True
        vision_state.improvement_start_date = datetime.now() - timedelta(days=200)
        
        # Update should stop improvement
        engine._update_improvement_status("TEST003", patient, datetime.now(), 0.8)
        assert not vision_state.is_improving


class TestDiscontinuationSystem:
    """Test all 6 discontinuation reasons."""
    
    @pytest.fixture
    def discontinuation_checker(self):
        """Create a discontinuation checker."""
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "discontinuation.yaml"
        with open(params_path) as f:
            import yaml
            params = yaml.safe_load(f)
        return DiscontinuationChecker(params)
    
    def test_death_discontinuation(self, discontinuation_checker):
        """Test mortality-based discontinuation."""
        # Create elderly patient
        patient = Patient("TEST004", baseline_vision=65)
        patient.age_years = 90
        patient.sex = 'male'
        patient.current_state = DiseaseState.HIGHLY_ACTIVE
        patient.enrollment_date = datetime.now() - timedelta(days=365)
        patient.visit_history = [
            {
                'date': datetime.now() - timedelta(days=365-30*i),
                'treatment_given': True
            } 
            for i in range(12)
        ]
        
        # Check death probability over many trials
        deaths = 0
        for _ in range(10000):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 65, 90
            )
            if result.should_discontinue and result.reason == 'death':
                deaths += 1
        
        # 90-year-old male should have high mortality
        death_rate = deaths / 10000
        assert 0.01 < death_rate < 0.05  # Per-visit probability
    
    def test_poor_vision_discontinuation(self, discontinuation_checker):
        """Test vision floor discontinuation."""
        patient = Patient("TEST005", baseline_vision=25)
        patient.consecutive_poor_vision_visits = 0
        
        # First visit below threshold
        result = discontinuation_checker.check_discontinuation(
            patient, datetime.now(), 15, 75
        )
        assert not result.should_discontinue
        assert patient.consecutive_poor_vision_visits == 1
        
        # Second visit below threshold
        result = discontinuation_checker.check_discontinuation(
            patient, datetime.now(), 15, 75
        )
        # Might discontinue (probabilistic)
        
        # After grace period
        patient.consecutive_poor_vision_visits = 3
        discontinuations = 0
        for _ in range(100):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 15, 75
            )
            if result.should_discontinue:
                discontinuations += 1
                patient.consecutive_poor_vision_visits = 3  # Reset for next trial
        
        # Should see ~80% discontinuation rate
        assert 60 < discontinuations < 100
    
    def test_deterioration_discontinuation(self, discontinuation_checker):
        """Test continued deterioration discontinuation."""
        patient = Patient("TEST006", baseline_vision=70)
        patient.visits_with_significant_loss = 0
        
        # Not enough loss
        result = discontinuation_checker.check_discontinuation(
            patient, datetime.now(), 65, 75
        )
        assert not result.should_discontinue
        assert patient.visits_with_significant_loss == 0
        
        # Significant loss
        result = discontinuation_checker.check_discontinuation(
            patient, datetime.now(), 55, 75  # Lost 15 letters
        )
        assert patient.visits_with_significant_loss == 1
        
        # After threshold visits
        patient.visits_with_significant_loss = 3
        discontinuations = 0
        for _ in range(100):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 55, 75
            )
            if result.should_discontinue:
                discontinuations += 1
                patient.visits_with_significant_loss = 3  # Reset
        
        # Should see ~70% discontinuation rate
        assert 50 < discontinuations < 90
    
    def test_treatment_decision_discontinuation(self, discontinuation_checker):
        """Test clinical treatment decisions."""
        # Test stable disease
        patient = Patient("TEST007", baseline_vision=70)
        patient.injection_count = 5
        patient.consecutive_stable_visits = 6
        patient.visits_without_improvement = 2
        
        discontinuations = 0
        for _ in range(100):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 70, 75
            )
            if result.should_discontinue and 'stable' in result.reason:
                discontinuations += 1
        
        # Should see ~20% discontinuation rate
        assert 10 < discontinuations < 30
        
        # Test no improvement
        patient2 = Patient("TEST008", baseline_vision=70)
        patient2.injection_count = 5
        patient2.consecutive_stable_visits = 2
        patient2.visits_without_improvement = 4
        
        no_improvement_disc = 0
        for _ in range(100):
            result = discontinuation_checker.check_discontinuation(
                patient2, datetime.now(), 68, 75
            )
            if result.should_discontinue and 'no_improvement' in result.reason:
                no_improvement_disc += 1
        
        # Should see ~15% discontinuation rate
        assert 5 < no_improvement_disc < 25
    
    def test_attrition_discontinuation(self, discontinuation_checker):
        """Test loss to follow-up."""
        patient = Patient("TEST009", baseline_vision=70)
        patient.enrollment_date = datetime.now() - timedelta(days=900)  # 2.5 years
        patient.injection_count = 20
        patient._last_injection_date = datetime.now() - timedelta(days=30)
        
        # Create visit history for injection rate calculation
        patient.visit_history = []
        for i in range(20):
            visit_date = patient.enrollment_date + timedelta(days=45*i)
            patient.visit_history.append({
                'date': visit_date,
                'treatment_given': True
            })
        
        # High burden patient (many injections) after 2+ years
        attritions = 0
        for _ in range(1000):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 70, 75
            )
            if result.should_discontinue and result.reason == 'attrition':
                attritions += 1
        
        # Should see increased attrition rate
        assert attritions > 10  # At least 1%
    
    def test_administrative_discontinuation(self, discontinuation_checker):
        """Test NHS administrative errors."""
        patient = Patient("TEST010", baseline_vision=70)
        
        # Administrative errors are constant probability
        admin_errors = 0
        for _ in range(10000):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 70, 75
            )
            if result.should_discontinue and result.reason == 'administrative':
                admin_errors += 1
        
        # Should see ~0.5% rate
        error_rate = admin_errors / 10000
        assert 0.003 < error_rate < 0.007
    
    def test_discontinuation_priority(self, discontinuation_checker):
        """Test that discontinuation reasons follow priority order."""
        # Patient eligible for multiple discontinuation reasons
        patient = Patient("TEST011", baseline_vision=70)
        patient.age_years = 95
        patient.sex = 'female'
        patient.consecutive_poor_vision_visits = 3
        patient.visits_with_significant_loss = 3
        patient.consecutive_stable_visits = 6
        patient.injection_count = 5
        patient.enrollment_date = datetime.now() - timedelta(days=365)
        
        # Death should take priority
        reasons_seen = set()
        for _ in range(1000):
            result = discontinuation_checker.check_discontinuation(
                patient, datetime.now(), 15, 95  # Poor vision + old age
            )
            if result.should_discontinue:
                reasons_seen.add(result.reason)
        
        # Death should be most common due to priority
        assert 'death' in reasons_seen


class TestMortalityModel:
    """Test the mortality model integration."""
    
    @pytest.fixture
    def mortality_model(self):
        return MortalityModel()
    
    @pytest.fixture
    def population_model(self):
        return PopulationMortalityModel()
    
    def test_mortality_by_age_and_sex(self, mortality_model):
        """Test that mortality increases with age and differs by sex."""
        # Test age progression
        male_70 = mortality_model.get_annual_mortality_probability(70, 'male', True)
        male_80 = mortality_model.get_annual_mortality_probability(80, 'male', True)
        male_90 = mortality_model.get_annual_mortality_probability(90, 'male', True)
        
        assert male_70 < male_80 < male_90
        
        # Test sex differences
        male_75 = mortality_model.get_annual_mortality_probability(75, 'male', True)
        female_75 = mortality_model.get_annual_mortality_probability(75, 'female', True)
        
        # Males typically have higher mortality
        assert male_75 > female_75
    
    def test_wet_amd_hazard_ratio(self, mortality_model):
        """Test that wet AMD increases mortality risk."""
        # Compare with and without wet AMD
        no_amd = mortality_model.get_annual_mortality_probability(75, 'male', False)
        with_amd = mortality_model.get_annual_mortality_probability(75, 'male', True)
        
        # Should apply hazard ratio
        expected_ratio = 1.36  # Primary HR
        actual_ratio = with_amd / no_amd
        
        assert abs(actual_ratio - expected_ratio) < 0.01
    
    def test_population_gender_distribution(self, population_model):
        """Test age-dependent gender distribution."""
        # Young AMD patients - approximately 50% female
        prop_50 = population_model.get_female_proportion(50)
        assert 0.48 < prop_50 < 0.52  # ~0.50 expected from sigmoid function
        
        # Middle age - moderate female predominance
        prop_70 = population_model.get_female_proportion(70)
        assert 0.55 < prop_70 < 0.62  # ~0.58 expected
        
        # Elderly - more females
        prop_90 = population_model.get_female_proportion(90)
        assert prop_90 > 0.7
        
        # Monotonic increase
        ages = list(range(50, 95, 5))
        proportions = [population_model.get_female_proportion(age) for age in ages]
        
        # Check that it generally increases
        for i in range(1, len(proportions)):
            assert proportions[i] >= proportions[i-1]


class TestEngineIntegration:
    """Test the full engine integration."""
    
    @pytest.fixture
    def create_engine(self):
        """Factory for creating engines."""
        def _create_engine(n_patients=100, seed=42):
            params_dir = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters"
            disease_model = DiseaseModelTimeBased.from_parameter_files(params_dir, seed=seed)
            
            protocol_spec = TimeBasedProtocolSpecification.from_yaml(
                Path(__file__).parent.parent / "protocols" / "v2_time_based" / "eylea_time_based.yaml"
            )
            
            protocol = StandardProtocol(
                min_interval_days=protocol_spec.min_interval_days,
                max_interval_days=protocol_spec.max_interval_days,
                extension_days=protocol_spec.extension_days,
                shortening_days=protocol_spec.shortening_days
            )
            
            return ABSEngineTimeBasedWithParams(
                disease_model=disease_model,
                protocol=protocol,
                protocol_spec=protocol_spec,
                n_patients=n_patients,
                seed=seed
            )
        return _create_engine
    
    def test_patient_creation_with_demographics(self, create_engine):
        """Test that patients are created with appropriate demographics."""
        engine = create_engine(n_patients=1000)
        
        # Create patients
        patients = []
        for i in range(1000):
            patient = engine._create_patient(f"P{i:04d}", datetime.now())
            patients.append(patient)
        
        # Check age distribution
        ages = [p.age_years for p in patients]
        assert 50 <= min(ages) <= 60
        assert 85 <= max(ages) <= 95
        assert 70 <= np.mean(ages) <= 80
        
        # Check gender distribution varies with age
        young_females = sum(1 for p in patients if p.age_years < 65 and p.sex == 'female')
        young_total = sum(1 for p in patients if p.age_years < 65)
        
        old_females = sum(1 for p in patients if p.age_years > 80 and p.sex == 'female')
        old_total = sum(1 for p in patients if p.age_years > 80)
        
        if young_total > 10 and old_total > 10:
            young_female_prop = young_females / young_total
            old_female_prop = old_females / old_total
            
            # Older patients should have higher female proportion
            assert old_female_prop > young_female_prop
    
    def test_full_simulation_run(self, create_engine):
        """Test a complete simulation run."""
        engine = create_engine(n_patients=50, seed=12345)
        
        # Run for 2 years
        results = engine.run(duration_years=2.0)
        
        # Basic checks
        # Some patients will have died during the 2-year simulation
        assert 30 <= len(results.patient_histories) <= 50  # Allow for realistic mortality
        assert results.total_injections > 0
        assert 0 < results.final_vision_mean < 100
        assert results.final_vision_std > 0
        
        # Check discontinuations occurred
        # Note: Dead patients may not be in patient_histories anymore
        total_patients = 50
        remaining_patients = len(results.patient_histories)
        deaths = total_patients - remaining_patients
        
        discontinued_alive = sum(1 for p in results.patient_histories.values() 
                                if p.is_discontinued)
        total_discontinued = discontinued_alive + deaths
        assert total_discontinued > 0
        
        # Check various discontinuation reasons
        reasons = [p.discontinuation_reason for p in results.patient_histories.values() 
                  if p.is_discontinued]
        unique_reasons = set(reasons)
        assert len(unique_reasons) > 1  # Should see multiple reasons
    
    def test_vision_conservation(self, create_engine):
        """Test that vision values remain within valid bounds."""
        engine = create_engine(n_patients=100, seed=99999)
        results = engine.run(duration_years=3.0)
        
        # Check all vision measurements
        for patient in results.patient_histories.values():
            # Baseline should be in valid range
            assert 20 <= patient.baseline_vision <= 90
            
            # All measurements should be valid
            for visit in patient.visit_history:
                assert 0 <= visit['vision'] <= 100
                
                # Actual vision tracking if available
                if 'actual_vision' in visit:
                    assert 0 <= visit['actual_vision'] <= 100
            
            # Final vision should be valid
            assert 0 <= patient.current_vision <= 100


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])