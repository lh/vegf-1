"""
Regression tests for economic tracking integration.

Ensures that adding economic tracking does NOT break existing simulation functionality.
"""

import pytest
import numpy as np
from pathlib import Path
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner


class TestSimulationRegression:
    """Ensure existing simulations work unchanged with economic tracking."""
    
    @pytest.fixture
    def tnt_protocol_path(self):
        """Path to T&T protocol."""
        return Path("protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml")
    
    @pytest.fixture
    def tae_protocol_path(self):
        """Path to T&E protocol."""
        return Path("protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml")
    
    def test_baseline_simulation_runs(self, tnt_protocol_path):
        """Test that baseline simulation still runs without errors."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        # Load protocol
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        
        # Create runner
        runner = TimeBasedSimulationRunner(spec)
        
        # Run simulation
        results = runner.run(
            engine_type='abs',
            n_patients=50,
            duration_years=2,
            seed=42
        )
        
        # Basic assertions
        assert results is not None
        assert results.patient_count == 50
        assert results.total_injections > 0
        assert results.final_vision_mean is not None
        assert hasattr(results, 'patient_histories')
        assert len(results.patient_histories) == 50
    
    def test_disease_progression_unchanged(self, tnt_protocol_path):
        """Test that disease progression still happens every 14 days."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        runner = TimeBasedSimulationRunner(spec)
        
        results = runner.run(
            engine_type='abs',
            n_patients=10,
            duration_years=1,
            seed=123
        )
        
        # Check a patient's disease progression
        patient = next(iter(results.patient_histories.values()))
        
        # Disease states should be recorded at regular intervals
        if 'disease_states' in patient:
            times = patient.get('times', [])
            state_change_times = []
            
            for i in range(1, len(patient['disease_states'])):
                if patient['disease_states'][i] != patient['disease_states'][i-1]:
                    state_change_times.append(times[i])
            
            # All state changes should align with 14-day intervals
            for time in state_change_times:
                assert time % 14 == 0, f"Disease state changed at non-14-day interval: {time}"
    
    def test_visit_schedule_unchanged(self, tnt_protocol_path):
        """Test that visit schedules remain correct."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        runner = TimeBasedSimulationRunner(spec)
        
        results = runner.run(
            engine_type='abs',
            n_patients=20,
            duration_years=1.5,
            seed=456
        )
        
        # Check visit schedules for several patients
        for patient_id, history in list(results.patient_histories.items())[:5]:
            visits = history.get('visits', [])
            
            if len(visits) >= 4:
                # Loading phase should be monthly (28 days)
                assert abs(visits[1]['time'] - visits[0]['time'] - 28) <= 7
                assert abs(visits[2]['time'] - visits[1]['time'] - 28) <= 7
                
                # Maintenance should be bimonthly (56 days) after visit 3
                if len(visits) >= 6:
                    for i in range(3, min(6, len(visits)-1)):
                        interval = visits[i+1]['time'] - visits[i]['time']
                        assert abs(interval - 56) <= 14, f"Unexpected interval: {interval}"
    
    def test_injection_counts_reasonable(self, tnt_protocol_path, tae_protocol_path):
        """Test that injection counts are in expected ranges."""
        for protocol_path in [tnt_protocol_path, tae_protocol_path]:
            if not protocol_path.exists():
                pytest.skip(f"Protocol file not found: {protocol_path}")
                
            spec = TimeBasedProtocolSpecification.from_yaml(str(protocol_path))
            runner = TimeBasedSimulationRunner(spec)
            
            results = runner.run(
                engine_type='abs',
                n_patients=100,
                duration_years=2,
                seed=789
            )
            
            # Expected injections per patient over 2 years:
            # Year 1: ~7 injections (3 loading + 4-5 maintenance)
            # Year 2: ~6 injections
            # Total: ~13 injections per patient
            
            avg_injections_per_patient = results.total_injections / results.patient_count
            
            # Should be between 10-16 injections per patient
            assert 10 <= avg_injections_per_patient <= 16, \
                f"Unexpected injection count: {avg_injections_per_patient}"
    
    def test_vision_outcomes_unchanged(self, tnt_protocol_path):
        """Test that vision outcomes remain in expected ranges."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        runner = TimeBasedSimulationRunner(spec)
        
        # Run with same seed multiple times
        vision_means = []
        for _ in range(3):
            results = runner.run(
                engine_type='abs',
                n_patients=200,
                duration_years=2,
                seed=999
            )
            vision_means.append(results.final_vision_mean)
        
        # All runs with same seed should produce identical results
        assert all(abs(vm - vision_means[0]) < 0.001 for vm in vision_means), \
            "Vision outcomes not deterministic with same seed"
        
        # Vision should be in reasonable range (25-85 ETDRS letters)
        assert 25 <= vision_means[0] <= 85
    
    def test_discontinuation_tracking(self, tnt_protocol_path):
        """Test that discontinuations are still tracked."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        runner = TimeBasedSimulationRunner(spec)
        
        results = runner.run(
            engine_type='abs',
            n_patients=500,
            duration_years=5,
            seed=111
        )
        
        # Over 5 years, should have some discontinuations
        assert results.discontinuation_rate > 0
        assert results.discontinuation_rate < 1  # Not everyone discontinues
        
        # Check patient histories for discontinuation markers
        discontinued_count = 0
        for history in results.patient_histories.values():
            if history.get('discontinued', False):
                discontinued_count += 1
        
        expected_discontinued = int(results.patient_count * results.discontinuation_rate)
        assert abs(discontinued_count - expected_discontinued) <= 5
    
    def test_tae_year_one_matches_tnt(self, tnt_protocol_path, tae_protocol_path):
        """Test that T&E Year 1 produces similar results to T&T."""
        for protocol_path in [tnt_protocol_path, tae_protocol_path]:
            if not protocol_path.exists():
                pytest.skip(f"Protocol file not found: {protocol_path}")
        
        # Run both protocols for 1 year
        tnt_spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        tae_spec = TimeBasedProtocolSpecification.from_yaml(str(tae_protocol_path))
        
        tnt_runner = TimeBasedSimulationRunner(tnt_spec)
        tae_runner = TimeBasedSimulationRunner(tae_spec)
        
        tnt_results = tnt_runner.run('abs', n_patients=200, duration_years=1, seed=222)
        tae_results = tae_runner.run('abs', n_patients=200, duration_years=1, seed=222)
        
        # Year 1 injection counts should be very similar
        tnt_avg = tnt_results.total_injections / tnt_results.patient_count
        tae_avg = tae_results.total_injections / tae_results.patient_count
        
        assert abs(tnt_avg - tae_avg) < 0.5, \
            f"T&T: {tnt_avg:.1f} vs T&E: {tae_avg:.1f} injections per patient"
    
    def test_memory_usage_reasonable(self, tnt_protocol_path):
        """Test that memory usage hasn't increased significantly."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run a moderate simulation
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        runner = TimeBasedSimulationRunner(spec)
        
        results = runner.run(
            engine_type='abs',
            n_patients=1000,
            duration_years=3,
            seed=333
        )
        
        # Check memory after simulation
        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_memory - baseline_memory
        
        # Memory increase should be reasonable (< 500MB for 1000 patients)
        assert memory_increase < 500, f"Memory increased by {memory_increase:.1f}MB"
        
        # Cleanup
        del results
        del runner
    
    def test_performance_acceptable(self, tnt_protocol_path):
        """Test that performance hasn't degraded significantly."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
            
        import time
        
        spec = TimeBasedProtocolSpecification.from_yaml(str(tnt_protocol_path))
        runner = TimeBasedSimulationRunner(spec)
        
        # Time a standard simulation
        start_time = time.time()
        
        results = runner.run(
            engine_type='abs',
            n_patients=500,
            duration_years=2,
            seed=444
        )
        
        elapsed_time = time.time() - start_time
        
        # Should complete within reasonable time (< 30 seconds for 500 patients)
        assert elapsed_time < 30, f"Simulation took {elapsed_time:.1f} seconds"
        
        # Calculate patients per second
        patients_per_second = 500 / elapsed_time
        assert patients_per_second > 10, f"Too slow: {patients_per_second:.1f} patients/second"