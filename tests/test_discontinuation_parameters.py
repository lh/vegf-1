#!/usr/bin/env python3
"""
Unit tests for discontinuation parameter system.

Tests each of the 6 discontinuation reasons with their specific parameters:
1. Death (mortality)
2. Poor vision (vision floor)
3. Deterioration (continued vision loss)
4. Treatment decision (stable/no improvement)
5. Attrition (loss to follow-up)
6. Administrative (NHS errors)
"""

import pytest
import yaml
from pathlib import Path
import sys
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.core.discontinuation_checker import DiscontinuationChecker, DiscontinuationResult
from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseState


class TestDiscontinuationParameters:
    """Test discontinuation parameter structure and values."""
    
    @pytest.fixture
    def disc_params(self):
        """Load discontinuation parameters."""
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "discontinuation.yaml"
        with open(params_path) as f:
            return yaml.safe_load(f)
    
    def test_parameter_structure(self, disc_params):
        """Test that all required sections exist."""
        # Check main sections
        assert 'discontinuation_parameters' in disc_params
        assert 'discontinuation_priority' in disc_params
        
        # Check all 6 reasons have parameters
        params = disc_params['discontinuation_parameters']
        required_reasons = ['death', 'poor_vision', 'deterioration', 
                          'treatment_decision', 'attrition', 'administrative']
        
        for reason in required_reasons:
            assert reason in params, f"Missing parameters for: {reason}"
    
    def test_priority_order(self, disc_params):
        """Test discontinuation priority is correctly defined."""
        priority = disc_params['discontinuation_priority']
        
        # Should have 6 priorities
        assert len(priority) == 6
        
        # Check order matches specification
        assert priority[1] == 'death'
        assert priority[2] == 'poor_vision'
        assert priority[3] == 'deterioration'
        assert priority[4] == 'treatment_decision'
        assert priority[5] == 'attrition'
        assert priority[6] == 'administrative'
    
    def test_death_parameters(self, disc_params):
        """Test death/mortality parameters."""
        death_params = disc_params['discontinuation_parameters']['death']
        
        assert 'base_annual_mortality' in death_params
        assert 0 < death_params['base_annual_mortality'] < 0.1
        
        assert 'age_adjustment_per_decade' in death_params
        assert death_params['age_adjustment_per_decade'] > 1.0
        
        assert 'disease_mortality_multiplier' in death_params
        multipliers = death_params['disease_mortality_multiplier']
        assert multipliers['STABLE'] <= multipliers['ACTIVE'] <= multipliers['HIGHLY_ACTIVE']
    
    def test_attrition_parameters(self, disc_params):
        """Test attrition parameters."""
        attrition_params = disc_params['discontinuation_parameters']['attrition']
        
        # Base probability
        assert 0 < attrition_params['base_probability_per_visit'] < 0.05
        
        # Time adjustments should increase
        time_adj = attrition_params['time_adjustment']
        assert time_adj['months_0_12'] < time_adj['months_12_24'] < time_adj['months_24_plus']
        
        # Burden adjustments should increase
        burden_adj = attrition_params['injection_burden_adjustment']
        assert burden_adj['injections_per_year_0_6'] < burden_adj['injections_per_year_6_12']
        assert burden_adj['injections_per_year_6_12'] < burden_adj['injections_per_year_12_plus']


class TestPrioritySystem:
    """Test that discontinuation priority system works correctly."""
    
    @pytest.fixture
    def checker(self):
        """Create discontinuation checker."""
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "discontinuation.yaml"
        with open(params_path) as f:
            params = yaml.safe_load(f)
        return DiscontinuationChecker(params)
    
    def test_death_takes_priority(self, checker):
        """Test that death overrides other reasons."""
        # Create patient eligible for multiple discontinuations
        patient = Patient("PRIORITY_TEST", baseline_vision=25)
        patient.age_years = 95
        patient.sex = 'male'
        patient.current_state = DiseaseState.HIGHLY_ACTIVE
        patient.consecutive_poor_vision_visits = 5  # Eligible for poor vision
        patient.visits_with_significant_loss = 5   # Eligible for deterioration
        patient.enrollment_date = datetime.now() - timedelta(days=365)
        patient.visit_history = [{'date': datetime.now() - timedelta(days=30)}]
        
        # Run many times to see distribution
        reasons = []
        for _ in range(1000):
            result = checker.check_discontinuation(patient, datetime.now(), 15, 95)
            if result.should_discontinue:
                reasons.append(result.reason)
        
        # Death should be most common due to priority
        death_count = reasons.count('death')
        other_count = len(reasons) - death_count
        
        # Given 95-year-old male, death should dominate
        assert death_count > other_count
    
    def test_no_double_checking(self, checker):
        """Test that once a reason triggers, no others are checked."""
        # Mock the individual check methods to track calls
        call_counts = {
            'death': 0,
            'poor_vision': 0,
            'deterioration': 0,
            'treatment_decision': 0,
            'attrition': 0,
            'administrative': 0
        }
        
        original_checks = {
            'death': checker._check_death,
            'poor_vision': checker._check_poor_vision,
            'deterioration': checker._check_deterioration,
            'treatment_decision': checker._check_treatment_decision,
            'attrition': checker._check_attrition,
            'administrative': checker._check_administrative
        }
        
        def make_counting_wrapper(reason, original_func):
            def wrapper(*args, **kwargs):
                call_counts[reason] += 1
                return original_func(*args, **kwargs)
            return wrapper
        
        # Wrap all check methods
        checker._check_death = make_counting_wrapper('death', original_checks['death'])
        checker._check_poor_vision = make_counting_wrapper('poor_vision', original_checks['poor_vision'])
        checker._check_deterioration = make_counting_wrapper('deterioration', original_checks['deterioration'])
        checker._check_treatment_decision = make_counting_wrapper('treatment_decision', original_checks['treatment_decision'])
        checker._check_attrition = make_counting_wrapper('attrition', original_checks['attrition'])
        checker._check_administrative = make_counting_wrapper('administrative', original_checks['administrative'])
        
        # Create patient likely to trigger early reason
        patient = Patient("TEST", baseline_vision=15)
        patient.age_years = 75
        patient.sex = 'male'
        patient.consecutive_poor_vision_visits = 5
        patient.enrollment_date = datetime.now()
        
        # Force administrative to trigger
        checker._check_administrative = lambda: DiscontinuationResult(True, 'administrative', 1.0)
        
        result = checker.check_discontinuation(patient, datetime.now(), 15, 75)
        
        # Should have checked in priority order until administrative
        assert call_counts['death'] == 1
        assert call_counts['poor_vision'] == 1
        assert call_counts['deterioration'] == 1
        assert call_counts['treatment_decision'] == 1
        assert call_counts['attrition'] == 1
        assert call_counts['administrative'] == 1
        
        # Result should be administrative (last in priority)
        assert result.reason == 'administrative'


class TestSpecificDiscontinuationLogic:
    """Test specific logic for each discontinuation reason."""
    
    @pytest.fixture
    def checker(self):
        """Create discontinuation checker."""
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "discontinuation.yaml"
        with open(params_path) as f:
            params = yaml.safe_load(f)
        return DiscontinuationChecker(params)
    
    def test_poor_vision_grace_period(self, checker):
        """Test that poor vision respects grace period."""
        patient = Patient("VISION_TEST", baseline_vision=25)
        
        # First visit below threshold
        result = checker._check_poor_vision(patient, 15)
        assert not result.should_discontinue
        assert patient.consecutive_poor_vision_visits == 1
        
        # Second visit - still in grace period
        result = checker._check_poor_vision(patient, 18)
        assert patient.consecutive_poor_vision_visits == 2
        
        # Above threshold resets counter
        result = checker._check_poor_vision(patient, 25)
        assert not result.should_discontinue
        assert patient.consecutive_poor_vision_visits == 0
    
    def test_deterioration_threshold(self, checker):
        """Test deterioration vision loss threshold."""
        patient = Patient("DETERIORATION_TEST", baseline_vision=70)
        patient.visits_with_significant_loss = 0
        
        # Small loss - not significant
        result = checker._check_deterioration(patient, 65)  # Lost 5 letters
        assert not result.should_discontinue
        assert patient.visits_with_significant_loss == 0
        
        # Significant loss
        result = checker._check_deterioration(patient, 55)  # Lost 15 letters
        assert patient.visits_with_significant_loss == 1
        
        # Recovery resets counter
        result = checker._check_deterioration(patient, 65)  # Back up
        assert patient.visits_with_significant_loss == 0
    
    def test_treatment_decision_minimum_treatments(self, checker):
        """Test that treatment decisions require minimum treatments."""
        patient = Patient("TREATMENT_TEST", baseline_vision=70)
        patient.injection_count = 2  # Below minimum
        patient.consecutive_stable_visits = 10
        patient.visits_without_improvement = 10
        
        result = checker._check_treatment_decision(patient, datetime.now())
        assert not result.should_discontinue  # Too few treatments
        
        # With enough treatments
        patient.injection_count = 5
        
        # Now it can trigger (probabilistically)
        triggered = False
        for _ in range(100):
            result = checker._check_treatment_decision(patient, datetime.now())
            if result.should_discontinue:
                triggered = True
                break
        
        assert triggered
    
    def test_attrition_time_factor(self, checker):
        """Test that attrition increases over time."""
        # Early patient
        early_patient = Patient("EARLY", baseline_vision=70)
        early_patient.enrollment_date = datetime.now() - timedelta(days=180)  # 6 months
        early_patient.visit_history = [{'date': datetime.now(), 'treatment_given': True}]
        
        # Late patient  
        late_patient = Patient("LATE", baseline_vision=70)
        late_patient.enrollment_date = datetime.now() - timedelta(days=900)  # 2.5 years
        late_patient.visit_history = [{'date': datetime.now(), 'treatment_given': True}]
        
        # Run many times and count attritions
        early_attritions = 0
        late_attritions = 0
        
        for _ in range(10000):
            if checker._check_attrition(early_patient, datetime.now()).should_discontinue:
                early_attritions += 1
            
            if checker._check_attrition(late_patient, datetime.now()).should_discontinue:
                late_attritions += 1
        
        # Late patient should have higher attrition
        assert late_attritions > early_attritions * 1.3
    
    def test_attrition_burden_factor(self, checker):
        """Test that treatment burden affects attrition."""
        # Low burden patient
        low_burden = Patient("LOW_BURDEN", baseline_vision=70)
        low_burden.enrollment_date = datetime.now() - timedelta(days=365)
        low_burden.visit_history = []
        
        # Create sparse visit history (4 per year)
        for i in range(4):
            visit_date = low_burden.enrollment_date + timedelta(days=90*i)
            low_burden.visit_history.append({
                'date': visit_date,
                'treatment_given': True
            })
        
        # High burden patient
        high_burden = Patient("HIGH_BURDEN", baseline_vision=70)
        high_burden.enrollment_date = datetime.now() - timedelta(days=365)
        high_burden.visit_history = []
        
        # Create frequent visit history (15 per year)
        for i in range(15):
            visit_date = high_burden.enrollment_date + timedelta(days=24*i)
            high_burden.visit_history.append({
                'date': visit_date,
                'treatment_given': True
            })
        
        # Compare attrition rates
        low_burden_attritions = 0
        high_burden_attritions = 0
        
        for _ in range(10000):
            if checker._check_attrition(low_burden, datetime.now()).should_discontinue:
                low_burden_attritions += 1
            
            if checker._check_attrition(high_burden, datetime.now()).should_discontinue:
                high_burden_attritions += 1
        
        # High burden should have higher attrition
        assert high_burden_attritions > low_burden_attritions
    
    def test_administrative_constant_rate(self, checker):
        """Test that administrative errors are constant."""
        patient1 = Patient("ADMIN1", baseline_vision=70)
        patient2 = Patient("ADMIN2", baseline_vision=30)
        patient2.age_years = 90
        patient2.injection_count = 20
        
        # Run many times
        admin_errors1 = 0
        admin_errors2 = 0
        
        for _ in range(10000):
            if checker._check_administrative().should_discontinue:
                admin_errors1 += 1
            
            if checker._check_administrative().should_discontinue:
                admin_errors2 += 1
        
        # Rates should be similar (within statistical noise)
        rate1 = admin_errors1 / 10000
        rate2 = admin_errors2 / 10000
        
        assert abs(rate1 - rate2) < 0.002  # Within 0.2%
        assert 0.003 < rate1 < 0.007  # Around 0.5%


class TestPatientTrackingIntegration:
    """Test that patient tracking attributes work with discontinuation."""
    
    @pytest.fixture
    def checker(self):
        """Create discontinuation checker."""
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "discontinuation.yaml"
        with open(params_path) as f:
            params = yaml.safe_load(f)
        return DiscontinuationChecker(params)
    
    def test_patient_tracking_attributes(self):
        """Test that Patient class has all required tracking attributes."""
        patient = Patient("TRACKING_TEST", baseline_vision=70)
        
        # Check all required attributes exist
        required_attrs = [
            'age_years',
            'birth_date',
            'sex',
            'consecutive_stable_visits',
            'consecutive_poor_vision_visits',
            'visits_without_improvement',
            'visits_with_significant_loss'
        ]
        
        for attr in required_attrs:
            assert hasattr(patient, attr), f"Missing attribute: {attr}"
    
    def test_visit_history_for_injection_rate(self):
        """Test that injection rate calculation works."""
        patient = Patient("RATE_TEST", baseline_vision=70)
        patient.enrollment_date = datetime.now() - timedelta(days=365)
        
        # Add visit history
        for i in range(10):
            visit_date = patient.enrollment_date + timedelta(days=35*i)
            patient.visit_history.append({
                'date': visit_date,
                'treatment_given': True
            })
            
        # Calculate rate
        rate = patient.calculate_recent_injection_rate(datetime.now())
        
        # Should be approximately 10 injections per year
        assert rate is not None
        assert 8 < rate < 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])