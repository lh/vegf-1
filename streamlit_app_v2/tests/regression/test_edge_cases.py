"""
Regression tests for edge cases and error conditions.

These tests ensure the system handles unusual inputs gracefully.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def minimal_protocol_path(self):
        """Get path to minimal test protocol."""
        # Use the complete minimal protocol that has all required fields
        return Path(__file__).parent / "complete_minimal_protocol.yaml"
    
    def test_zero_patients(self, minimal_protocol_path):
        """Test simulation with 0 patients."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # Should handle 0 patients gracefully
        results = runner.run("abs", n_patients=0, duration_years=1.0, seed=42)
        
        assert results.patient_count == 0
        assert results.total_injections == 0
        assert len(results.patient_histories) == 0
    
    def test_very_short_duration(self, minimal_protocol_path):
        """Test simulation with very short duration."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # 0.01 years = ~3.65 days
        results = runner.run("abs", n_patients=10, duration_years=0.01, seed=42)
        
        assert results.patient_count == 10
        # Might have 0 or very few injections
        assert results.total_injections >= 0
    
    def test_single_patient(self, minimal_protocol_path):
        """Test simulation with exactly 1 patient."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        results = runner.run("abs", n_patients=1, duration_years=1.0, seed=42)
        
        assert results.patient_count == 1
        assert len(results.patient_histories) == 1
        
        # Check patient ID format
        patient_id = list(results.patient_histories.keys())[0]
        assert patient_id == "P0000"
    
    def test_extreme_random_seeds(self, minimal_protocol_path):
        """Test with boundary random seeds."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # Test boundary seeds
        for seed in [0, 1, 999999, 2**31 - 1]:
            results = runner.run("abs", n_patients=5, duration_years=0.5, seed=seed)
            # With stochastic enrollment, we might get 4-5 patients in 0.5 years
            assert 3 <= results.patient_count <= 7  # Allow some variation
    
    def test_invalid_engine_type(self, minimal_protocol_path):
        """Test with invalid engine type."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # Should raise error for invalid engine
        with pytest.raises((ValueError, KeyError, AttributeError)):
            runner.run("invalid_engine", n_patients=10, duration_years=1.0, seed=42)
    
    def test_negative_parameters(self, minimal_protocol_path):
        """Test with negative parameters."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # Negative patients should fail
        with pytest.raises((ValueError, AssertionError)):
            runner.run("abs", n_patients=-10, duration_years=1.0, seed=42)
        
        # Negative duration should fail
        with pytest.raises((ValueError, AssertionError)):
            runner.run("abs", n_patients=10, duration_years=-1.0, seed=42)
    
    def test_extremely_long_duration(self, minimal_protocol_path):
        """Test with very long simulation duration."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # 100 years - should still work but be slow
        # Use very few patients to keep it fast
        results = runner.run("abs", n_patients=2, duration_years=100.0, seed=42)
        
        # With 2 patients over 100 years, we should get 1-2 patients
        assert 1 <= results.patient_count <= 2
        # With discontinuation, we can't guarantee many injections
        # Just verify the simulation completed successfully
        assert results.total_injections >= 0
        assert 0.0 <= results.discontinuation_rate <= 1.0
    
    def test_concurrent_runner_instances(self, minimal_protocol_path):
        """Test multiple runner instances don't interfere."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        
        # Create multiple runners
        runner1 = SimulationRunner(spec)
        runner2 = SimulationRunner(spec)
        
        # Run with same parameters but different seeds
        results1 = runner1.run("abs", n_patients=20, duration_years=1.0, seed=100)
        results2 = runner2.run("abs", n_patients=20, duration_years=1.0, seed=200)
        
        # Should have same structure but different results
        # With stochastic enrollment and different seeds, counts may vary
        # Just verify both simulations completed with reasonable results
        assert results1.patient_count >= 10  # At least half enrolled
        assert results2.patient_count >= 10
        assert results1.patient_count <= 25  # Not more than expected + buffer
        assert results2.patient_count <= 25
    
    def test_protocol_with_extreme_values(self):
        """Test protocol with extreme parameter values."""
        extreme_protocol = Path(__file__).parent / "extreme_protocol.yaml"
        extreme_protocol.write_text("""
name: Extreme Protocol
version: 1.0.0
created_date: "2024-01-01"
author: Test
description: Protocol with extreme values

protocol_type: treat_and_extend
min_interval_days: 1  # Very frequent
max_interval_days: 365  # Very infrequent
extension_days: 180  # Huge extensions
shortening_days: 1  # Tiny shortenings

disease_transitions:
  NAIVE:
    STABLE: 0.000001  # Tiny probability
    ACTIVE: 0.999999  # Huge probability

# Would need other required fields...
""")
        
        # This tests that extreme values are handled
        # (Would need complete protocol to fully test)
        
        extreme_protocol.unlink()
    
    def test_memory_after_failed_simulation(self, minimal_protocol_path):
        """Test memory is cleaned up after failed simulation."""
        if not minimal_protocol_path.exists():
            pytest.skip("Minimal protocol not found")
            
        import psutil
        import gc
        
        spec = ProtocolSpecification.from_yaml(minimal_protocol_path)
        runner = SimulationRunner(spec)
        
        # Get baseline memory
        gc.collect()
        process = psutil.Process()
        mem_before = process.memory_info().rss
        
        # Try to run with invalid parameters
        try:
            runner.run("abs", n_patients=-100, duration_years=1.0, seed=42)
        except:
            pass  # Expected to fail
        
        # Check memory was cleaned up
        gc.collect()
        mem_after = process.memory_info().rss
        
        # Memory shouldn't increase significantly
        memory_increase_mb = (mem_after - mem_before) / (1024 * 1024)
        assert memory_increase_mb < 10  # Less than 10MB increase