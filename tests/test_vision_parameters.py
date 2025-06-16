#!/usr/bin/env python3
"""
Unit tests for vision parameter system.

Tests the parameter-driven vision model including:
- Treatment effect decay curves
- Vision ceiling calculations
- Hemorrhage risk modeling
- Improvement mechanics
"""

import pytest
import yaml
from pathlib import Path
import sys
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.engines.abs_engine_time_based_with_params import ABSEngineTimeBasedWithParams, PatientVisionState
from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseState


class TestVisionParameters:
    """Test vision parameter loading and usage."""
    
    @pytest.fixture
    def vision_params(self):
        """Load vision parameters."""
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "vision.yaml"
        with open(params_path) as f:
            return yaml.safe_load(f)
    
    def test_parameter_structure(self, vision_params):
        """Test that all required parameter sections exist."""
        required_sections = [
            'vision_measurement',
            'vision_ceilings', 
            'vision_decline_fortnightly',
            'hemorrhage_risk',
            'vision_improvement',
            'treatment_effect_decay',
            'vision_floor_discontinuation',
            'misc_parameters'
        ]
        
        for section in required_sections:
            assert section in vision_params, f"Missing section: {section}"
    
    def test_vision_measurement_params(self, vision_params):
        """Test vision measurement parameters."""
        measurement = vision_params['vision_measurement']
        
        assert measurement['min_measurable_vision'] == 0
        assert measurement['max_measurable_vision'] == 100
        assert 0 < measurement['measurement_noise_std'] < 5
    
    def test_treatment_effect_decay_params(self, vision_params):
        """Test treatment effect decay parameters."""
        decay = vision_params['treatment_effect_decay']
        
        # Check time points are in order
        assert decay['full_effect_duration_days'] < decay['gradual_decline_end_days']
        assert decay['gradual_decline_end_days'] < decay['faster_decline_end_days']
        
        # Check effect levels decrease
        assert decay['effect_at_gradual_start'] > decay['effect_at_faster_start']
        assert decay['effect_at_faster_start'] > decay['effect_at_minimal_start']
        
        # Check values are reasonable
        assert 0 <= decay['effect_at_minimal_start'] <= 1
        assert 0 <= decay['effect_at_gradual_start'] <= 1


class TestTreatmentEffectDecay:
    """Test treatment effect decay calculations."""
    
    @pytest.fixture
    def mock_engine(self):
        """Create a minimal engine for testing."""
        # Create mock engine with vision params
        engine = type('MockEngine', (), {})()
        
        # Load actual vision parameters
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "vision.yaml"
        with open(params_path) as f:
            engine.vision_params = yaml.safe_load(f)
        
        # Copy the method we want to test
        engine._calculate_treatment_effect = ABSEngineTimeBasedWithParams._calculate_treatment_effect.__get__(engine)
        
        return engine
    
    def test_full_effect_period(self, mock_engine):
        """Test treatment effect during full effect period."""
        # Days 0-28: Full effect
        for days in [0, 7, 14, 21, 28]:
            effect = mock_engine._calculate_treatment_effect(days)
            assert effect == pytest.approx(1.0, rel=0.01)
    
    def test_gradual_decline_period(self, mock_engine):
        """Test treatment effect during gradual decline."""
        # Days 28-56: Gradual decline from 1.0 to 0.6
        effect_30 = mock_engine._calculate_treatment_effect(30)
        effect_42 = mock_engine._calculate_treatment_effect(42)
        effect_56 = mock_engine._calculate_treatment_effect(56)
        
        assert 0.9 < effect_30 < 1.0
        assert 0.7 < effect_42 < 0.9
        assert effect_56 == pytest.approx(0.6, rel=0.01)
        
        # Should decrease monotonically
        assert effect_30 > effect_42 > effect_56
    
    def test_faster_decline_period(self, mock_engine):
        """Test treatment effect during faster decline."""
        # Days 56-84: Faster decline from 0.6 to 0.2
        effect_60 = mock_engine._calculate_treatment_effect(60)
        effect_70 = mock_engine._calculate_treatment_effect(70)
        effect_84 = mock_engine._calculate_treatment_effect(84)
        
        assert 0.5 < effect_60 < 0.6
        assert 0.3 < effect_70 < 0.5
        assert effect_84 == pytest.approx(0.2, rel=0.01)
        
        # Should decrease monotonically
        assert effect_60 > effect_70 > effect_84
    
    def test_minimal_effect_period(self, mock_engine):
        """Test treatment effect during minimal effect period."""
        # After day 84: Minimal but continuing decline
        effect_90 = mock_engine._calculate_treatment_effect(90)
        effect_120 = mock_engine._calculate_treatment_effect(120)
        effect_180 = mock_engine._calculate_treatment_effect(180)
        
        assert effect_90 < 0.2
        assert effect_120 < effect_90
        assert effect_180 < effect_120
        assert effect_180 >= 0  # Never negative
    
    def test_no_injection_case(self, mock_engine):
        """Test treatment effect when no injection given."""
        effect = mock_engine._calculate_treatment_effect(None)
        assert effect == 0.0


class TestVisionCeilings:
    """Test vision ceiling calculations."""
    
    @pytest.fixture
    def mock_engine_with_patients(self):
        """Create engine with patient tracking."""
        engine = type('MockEngine', (), {})()
        
        # Load vision parameters
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "vision.yaml"
        with open(params_path) as f:
            engine.vision_params = yaml.safe_load(f)
        
        # Initialize tracking dictionaries
        engine.patient_vision_states = {}
        engine.patient_actual_vision = {}
        engine.patient_vision_ceiling = {}
        
        # Copy the method we want to test
        engine._initialize_patient_vision = ABSEngineTimeBasedWithParams._initialize_patient_vision.__get__(engine)
        
        return engine
    
    def test_ceiling_above_baseline(self, mock_engine_with_patients):
        """Test that ceiling is always above baseline."""
        for baseline in [40, 50, 60, 70, 80]:
            patient = Patient(f"TEST{baseline}", baseline_vision=baseline)
            mock_engine_with_patients._initialize_patient_vision(
                f"TEST{baseline}", patient, datetime.now()
            )
            
            ceiling = mock_engine_with_patients.patient_vision_ceiling[f"TEST{baseline}"]
            assert ceiling >= baseline
    
    def test_ceiling_limits(self, mock_engine_with_patients):
        """Test ceiling limits for different baseline ranges."""
        # Low baseline patient
        low_patient = Patient("LOW", baseline_vision=45)
        mock_engine_with_patients._initialize_patient_vision("LOW", low_patient, datetime.now())
        low_ceiling = mock_engine_with_patients.patient_vision_ceiling["LOW"]
        assert low_ceiling <= 70  # Should hit low baseline ceiling
        
        # High baseline patient  
        high_patient = Patient("HIGH", baseline_vision=85)
        mock_engine_with_patients._initialize_patient_vision("HIGH", high_patient, datetime.now())
        high_ceiling = mock_engine_with_patients.patient_vision_ceiling["HIGH"]
        assert high_ceiling <= 85  # Should be limited
        
        # Medium baseline patient
        med_patient = Patient("MED", baseline_vision=65)
        mock_engine_with_patients._initialize_patient_vision("MED", med_patient, datetime.now())
        med_ceiling = mock_engine_with_patients.patient_vision_ceiling["MED"]
        assert 65 <= med_ceiling <= 80
    
    def test_ceiling_factor_application(self, mock_engine_with_patients):
        """Test that ceiling factor is applied correctly."""
        baseline = 60
        patient = Patient("TEST", baseline_vision=baseline)
        mock_engine_with_patients._initialize_patient_vision("TEST", patient, datetime.now())
        
        ceiling = mock_engine_with_patients.patient_vision_ceiling["TEST"]
        params = mock_engine_with_patients.vision_params['vision_ceilings']
        
        # Should be at least baseline * factor
        min_ceiling = baseline * params['baseline_ceiling_factor']
        assert ceiling >= min_ceiling
        
        # But not exceed absolute ceiling
        assert ceiling <= params['absolute_ceiling_default']


class TestHemorrhageRisk:
    """Test hemorrhage risk calculations."""
    
    @pytest.fixture
    def mock_engine_hemorrhage(self):
        """Create engine with hemorrhage checking."""
        engine = type('MockEngine', (), {})()
        
        # Load vision parameters
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "vision.yaml"
        with open(params_path) as f:
            engine.vision_params = yaml.safe_load(f)
        
        # Copy the method
        engine._check_hemorrhage = ABSEngineTimeBasedWithParams._check_hemorrhage.__get__(engine)
        
        return engine
    
    def test_no_hemorrhage_in_stable(self, mock_engine_hemorrhage):
        """Test that stable patients don't have hemorrhages."""
        patient = Patient("STABLE", baseline_vision=70)
        patient.current_state = DiseaseState.STABLE
        
        # Run many times - should never see hemorrhage
        for _ in range(1000):
            loss = mock_engine_hemorrhage._check_hemorrhage(patient, 30)
            assert loss == 0.0
    
    def test_hemorrhage_risk_increases_with_time(self, mock_engine_hemorrhage):
        """Test that hemorrhage risk increases with time since injection."""
        patient = Patient("ACTIVE", baseline_vision=70)
        patient.current_state = DiseaseState.ACTIVE
        
        # Test different time periods
        hemorrhages_recent = 0
        hemorrhages_medium = 0
        hemorrhages_long = 0
        
        for _ in range(10000):
            # Recently treated
            if mock_engine_hemorrhage._check_hemorrhage(patient, 20) > 0:
                hemorrhages_recent += 1
            
            # Medium gap
            if mock_engine_hemorrhage._check_hemorrhage(patient, 50) > 0:
                hemorrhages_medium += 1
            
            # Long gap
            if mock_engine_hemorrhage._check_hemorrhage(patient, 100) > 0:
                hemorrhages_long += 1
        
        # Risk should increase with time
        assert hemorrhages_recent < hemorrhages_medium < hemorrhages_long
    
    def test_hemorrhage_severity(self, mock_engine_hemorrhage):
        """Test that hemorrhages cause significant vision loss."""
        patient = Patient("HIGHLY_ACTIVE", baseline_vision=70)
        patient.current_state = DiseaseState.HIGHLY_ACTIVE
        
        # Collect hemorrhage magnitudes
        hemorrhage_losses = []
        for _ in range(10000):
            loss = mock_engine_hemorrhage._check_hemorrhage(patient, 60)
            if loss > 0:
                hemorrhage_losses.append(loss)
        
        # Should have some hemorrhages
        assert len(hemorrhage_losses) > 0
        
        # Check severity
        params = mock_engine_hemorrhage.vision_params['hemorrhage_risk']
        min_loss = params['hemorrhage_loss_min']
        max_loss = params['hemorrhage_loss_max']
        
        assert all(min_loss <= loss <= max_loss for loss in hemorrhage_losses)
        assert min(hemorrhage_losses) >= min_loss
        assert max(hemorrhage_losses) <= max_loss
    
    def test_highly_active_multiplier(self, mock_engine_hemorrhage):
        """Test that highly active disease has higher hemorrhage risk."""
        active_patient = Patient("ACTIVE", baseline_vision=70)
        active_patient.current_state = DiseaseState.ACTIVE
        
        highly_active_patient = Patient("HIGHLY_ACTIVE", baseline_vision=70)
        highly_active_patient.current_state = DiseaseState.HIGHLY_ACTIVE
        
        # Compare hemorrhage rates
        active_hemorrhages = 0
        highly_active_hemorrhages = 0
        
        for _ in range(10000):
            if mock_engine_hemorrhage._check_hemorrhage(active_patient, 60) > 0:
                active_hemorrhages += 1
            
            if mock_engine_hemorrhage._check_hemorrhage(highly_active_patient, 60) > 0:
                highly_active_hemorrhages += 1
        
        # Highly active should have more hemorrhages
        params = mock_engine_hemorrhage.vision_params['hemorrhage_risk']
        multiplier = params['highly_active_multiplier']
        
        expected_ratio = multiplier
        actual_ratio = highly_active_hemorrhages / (active_hemorrhages + 1)  # Avoid division by zero
        
        # Should be approximately the multiplier
        assert abs(actual_ratio - expected_ratio) < expected_ratio * 0.3


class TestImprovementMechanics:
    """Test vision improvement mechanics."""
    
    @pytest.fixture  
    def mock_engine_improvement(self):
        """Create engine with improvement mechanics."""
        engine = type('MockEngine', (), {})()
        
        # Load vision parameters
        params_path = Path(__file__).parent.parent / "protocols" / "v2_time_based" / "parameters" / "vision.yaml"
        with open(params_path) as f:
            engine.vision_params = yaml.safe_load(f)
        
        # Initialize tracking
        engine.patient_vision_states = {}
        
        # Copy methods
        engine._update_improvement_status = ABSEngineTimeBasedWithParams._update_improvement_status.__get__(engine)
        engine._calculate_improvement = ABSEngineTimeBasedWithParams._calculate_improvement.__get__(engine)
        
        return engine
    
    def test_improvement_eligibility(self, mock_engine_improvement):
        """Test improvement eligibility criteria."""
        patient = Patient("TEST", baseline_vision=60)
        patient.injection_count = 1  # First injection
        patient.current_state = DiseaseState.ACTIVE
        
        # Initialize vision state
        mock_engine_improvement.patient_vision_states["TEST"] = PatientVisionState(
            actual_vision=60,
            vision_ceiling=75,
            is_improving=False
        )
        
        # Should be eligible with first injection and good treatment effect
        mock_engine_improvement._update_improvement_status(
            "TEST", patient, datetime.now(), treatment_effect=0.8
        )
        
        # Check improvement started (probabilistic)
        improvements_started = 0
        for _ in range(100):
            mock_engine_improvement.patient_vision_states["TEST"].is_improving = False
            mock_engine_improvement._update_improvement_status(
                "TEST", patient, datetime.now(), treatment_effect=0.8
            )
            if mock_engine_improvement.patient_vision_states["TEST"].is_improving:
                improvements_started += 1
        
        # Should see some improvements start
        assert improvements_started > 0
    
    def test_improvement_duration_limit(self, mock_engine_improvement):
        """Test that improvement stops after max duration."""
        patient = Patient("TEST", baseline_vision=60)
        patient.current_state = DiseaseState.ACTIVE
        
        vision_state = PatientVisionState(
            actual_vision=65,
            vision_ceiling=75,
            is_improving=True,
            improvement_start_date=datetime.now() - timedelta(days=120)  # Long time ago
        )
        mock_engine_improvement.patient_vision_states["TEST"] = vision_state
        
        # Should stop improvement due to duration
        mock_engine_improvement._update_improvement_status(
            "TEST", patient, datetime.now(), treatment_effect=0.8
        )
        
        assert not vision_state.is_improving
    
    def test_improvement_magnitude(self, mock_engine_improvement):
        """Test improvement magnitude is reasonable."""
        patient = Patient("TEST", baseline_vision=60)
        
        # Test different disease states
        for state in [DiseaseState.STABLE, DiseaseState.ACTIVE]:
            patient.current_state = state
            vision_state = PatientVisionState(
                actual_vision=60,
                vision_ceiling=75,
                is_improving=True
            )
            
            improvements = []
            for _ in range(1000):
                improvement = mock_engine_improvement._calculate_improvement(patient, vision_state)
                improvements.append(improvement)
            
            # Should all be positive (during improvement phase)
            assert all(imp >= 0 for imp in improvements)
            
            # Should have reasonable magnitude
            assert max(improvements) < 10  # Not too large
            assert sum(imp > 0 for imp in improvements) > 500  # Most should be positive


if __name__ == "__main__":
    pytest.main([__file__, "-v"])