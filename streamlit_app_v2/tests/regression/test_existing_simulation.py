"""
Regression tests for existing simulation functionality.

These tests establish a baseline to ensure our memory architecture
changes don't break current functionality.
"""

import pytest
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification


class TestExistingSimulation:
    """Baseline tests for current simulation functionality."""
    
    @pytest.fixture
    def default_protocol_path(self):
        """Get path to default protocol file."""
        # Try multiple possible locations, checking v2 directory first
        possible_paths = [
            Path(__file__).parent.parent.parent / "protocols" / "v2" / "eylea.yaml",
            Path(__file__).parent.parent.parent / "protocols" / "eylea.yaml",
            Path(__file__).parent.parent.parent.parent / "protocols" / "v2" / "eylea.yaml",
            Path(__file__).parent.parent.parent.parent / "protocols" / "eylea.yaml",
            Path(__file__).parent.parent.parent.parent / "simulation_v2" / "protocols" / "default.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        # If no default found, create a minimal one for testing
        test_protocol_path = Path(__file__).parent / "test_protocol.yaml"
        if not test_protocol_path.exists():
            test_protocol_path.write_text("""
name: Test Protocol
version: 1.0.0
description: Minimal protocol for regression testing

# Disease model parameters
disease_states:
  - name: naive
    description: Treatment naive
  - name: active
    description: Active disease
  - name: inactive
    description: Inactive disease
  - name: reactivated
    description: Reactivated disease

disease_transitions:
  naive:
    active: 0.8
    inactive: 0.2
  active:
    active: 0.7
    inactive: 0.3
  inactive:
    inactive: 0.8
    reactivated: 0.2
  reactivated:
    active: 0.6
    inactive: 0.4

# Treatment effect on transitions
treatment_effect_on_transitions:
  naive:
    active: 0.3
    inactive: 0.7
  active:
    active: 0.4
    inactive: 0.6
  inactive:
    inactive: 0.9
    reactivated: 0.1
  reactivated:
    active: 0.3
    inactive: 0.7

# Protocol parameters
min_interval_days: 28
max_interval_days: 112
extension_days: 14
shortening_days: 14

# Vision model parameters
baseline_vision_mean: 70
baseline_vision_std: 10
baseline_vision_min: 20
baseline_vision_max: 90

# Injection limits
max_injections_per_year: 13
loading_doses: 3

# Discontinuation parameters
discontinuation_vision_threshold: 20
discontinuation_low_vision_prob: 0.5
discontinuation_rate_per_month: 0.02
""")
        return test_protocol_path
    
    def test_simulation_loads_and_runs(self, default_protocol_path):
        """Verify basic simulation can load and run."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        runner = SimulationRunner(spec)
        
        # Small simulation should complete without error
        results = runner.run(
            engine_type="abs",
            n_patients=10,
            duration_years=0.5,
            seed=42
        )
        
        assert results is not None
        assert hasattr(results, 'patient_histories')
        assert hasattr(results, 'total_injections')
        
    def test_small_simulation_results(self, default_protocol_path):
        """Verify 100 patient simulation produces expected results."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        runner = SimulationRunner(spec)
        
        results = runner.run("abs", 100, 2.0, 42)
        
        # Basic sanity checks
        assert results.patient_count == 100
        assert results.total_injections > 0
        assert 0 <= results.discontinuation_rate <= 1
        
        # Vision should be in reasonable range
        assert 0 <= results.final_vision_mean <= 100
        assert results.final_vision_std >= 0
        
        # Should have some patient histories
        assert len(results.patient_histories) == 100
        
    def test_simulation_reproducible(self, default_protocol_path):
        """Verify same seed produces same results."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        
        # Run twice with same seed
        runner1 = SimulationRunner(spec)
        results1 = runner1.run("abs", 50, 1.0, 12345)
        
        runner2 = SimulationRunner(spec)
        results2 = runner2.run("abs", 50, 1.0, 12345)
        
        # Results should be identical
        assert results1.total_injections == results2.total_injections
        assert results1.final_vision_mean == results2.final_vision_mean
        assert results1.discontinuation_rate == results2.discontinuation_rate
        
    def test_both_engines_work(self, default_protocol_path):
        """Verify ABS and DES engines both function."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        runner = SimulationRunner(spec)
        
        # Both engines should work
        abs_results = runner.run("abs", 50, 1.0, 42)
        des_results = runner.run("des", 50, 1.0, 42)
        
        # With stochastic enrollment over 1 year, expect close to target
        assert 47 <= abs_results.patient_count <= 53, \
            f"ABS: Expected ~50 patients, got {abs_results.patient_count}"
        assert 47 <= des_results.patient_count <= 53, \
            f"DES: Expected ~50 patients, got {des_results.patient_count}"
        
        # Both should produce reasonable results
        assert abs_results.total_injections > 0
        assert des_results.total_injections > 0
        
    @pytest.mark.parametrize("n_patients,duration", [
        (10, 0.5),
        (50, 1.0),
        (100, 1.0),
        (100, 2.0),
    ])
    def test_various_sizes(self, default_protocol_path, n_patients, duration):
        """Test different simulation sizes work."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        runner = SimulationRunner(spec)
        
        results = runner.run("abs", n_patients, duration, 42)
        
        # With stochastic enrollment, allow reasonable variation
        # For short simulations (0.5 years), expect at least 80% of patients
        # For longer simulations (1-2 years), expect closer to target
        if duration <= 0.5:
            min_expected = int(n_patients * 0.8)
        else:
            min_expected = int(n_patients * 0.95)
            
        assert results.patient_count >= min_expected, \
            f"Expected at least {min_expected} patients, got {results.patient_count}"
        assert results.patient_count <= n_patients + 5, \
            f"Expected at most {n_patients + 5} patients, got {results.patient_count}"
        assert results.total_injections > 0
        
    def test_audit_trail_exists(self, default_protocol_path):
        """Verify audit trail is created."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        runner = SimulationRunner(spec)
        
        results = runner.run("abs", 20, 0.5, 42)
        
        # Should have audit log
        assert hasattr(runner, 'audit_log')
        assert len(runner.audit_log) > 0
        
        # Should have key events
        event_types = [entry['event'] for entry in runner.audit_log]
        assert 'protocol_loaded' in event_types
        assert 'simulation_start' in event_types
        
    def test_patient_structure(self, default_protocol_path):
        """Verify patient data structure is as expected."""
        spec = ProtocolSpecification.from_yaml(default_protocol_path)
        runner = SimulationRunner(spec)
        
        results = runner.run("abs", 5, 0.5, 42)
        
        # Check patient structure
        for patient_id, patient in results.patient_histories.items():
            assert hasattr(patient, 'id')
            assert hasattr(patient, 'baseline_vision')
            assert hasattr(patient, 'current_vision')
            assert hasattr(patient, 'visit_history')
            assert hasattr(patient, 'injection_count')
            
            # Vision in valid range
            assert 0 <= patient.baseline_vision <= 100
            assert 0 <= patient.current_vision <= 100
            
            # Should have visits
            assert isinstance(patient.visit_history, list)
            if len(patient.visit_history) > 0:
                visit = patient.visit_history[0]
                assert 'date' in visit
                assert 'treatment_given' in visit
                assert 'vision' in visit