"""
Test staggered enrollment implementation with proper statistical validation.

These tests use larger patient counts and longer durations to properly
validate the Poisson arrival process.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from scipy import stats
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner


class TestStaggeredEnrollment:
    """Test suite for staggered patient enrollment."""
    
    @pytest.fixture
    def protocol_path(self):
        """Get path to test protocol."""
        protocol_path = Path(__file__).parent.parent.parent / "protocols" / "eylea.yaml"
        if not protocol_path.exists():
            pytest.skip(f"Protocol not found at {protocol_path}")
        return protocol_path
    
    def test_fixed_total_mode_convergence(self, protocol_path):
        """Test that Fixed Total Mode converges to expected patient count."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        # Use larger numbers for reliable statistics
        target_patients = 500
        duration_years = 2.0
        
        results = runner.run("abs", n_patients=target_patients, 
                           duration_years=duration_years, seed=12345)
        
        # With Poisson process and buffer, we should get close to target
        actual_count = results.patient_count
        
        # Allow 5% deviation for stochastic variation
        assert abs(actual_count - target_patients) <= target_patients * 0.05, \
            f"Expected ~{target_patients} patients, got {actual_count}"
        
        # Verify patients are spread across the duration
        enrollment_dates = []
        for patient in results.patient_histories.values():
            if hasattr(patient, 'enrollment_date') and patient.enrollment_date:
                enrollment_dates.append(patient.enrollment_date)
        
        if enrollment_dates:
            enrollment_spread = (max(enrollment_dates) - min(enrollment_dates)).days
            expected_spread = duration_years * 365.25 * 0.9  # Expect at least 90% spread
            
            assert enrollment_spread >= expected_spread, \
                f"Enrollment spread {enrollment_spread} days < expected {expected_spread} days"
    
    def test_multiple_fixed_total_runs(self, protocol_path):
        """Test that Fixed Total Mode is consistent across runs."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        # Run multiple simulations to test consistency
        n_patients = 500
        duration_years = 1.0
        n_simulations = 5
        patient_counts = []
        
        for seed in range(n_simulations):
            runner = SimulationRunner(spec)
            results = runner.run("abs", n_patients=n_patients,
                               duration_years=duration_years, seed=seed)
            patient_counts.append(results.patient_count)
        
        # All runs should achieve close to the target count
        # With stochastic process, allow 5% deviation
        for count in patient_counts:
            assert abs(count - n_patients) <= n_patients * 0.05, \
                f"Run achieved {count} patients, expected {n_patients}"
    
    def test_poisson_inter_arrival_times(self, protocol_path):
        """Test that inter-arrival times follow exponential distribution."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        # Need many patients for good statistics
        results = runner.run("abs", n_patients=1000, 
                           duration_years=2.0, seed=42)
        
        # Extract enrollment dates
        enrollment_dates = []
        for patient in results.patient_histories.values():
            if hasattr(patient, 'enrollment_date') and patient.enrollment_date:
                enrollment_dates.append(patient.enrollment_date)
        
        # Sort and calculate inter-arrival times
        enrollment_dates.sort()
        inter_arrivals = []
        for i in range(1, len(enrollment_dates)):
            delta = (enrollment_dates[i] - enrollment_dates[i-1]).total_seconds() / 86400  # days
            inter_arrivals.append(delta)
        
        # Perform Kolmogorov-Smirnov test for exponential distribution
        # Expected rate: 1000 patients / (2 years * 365.25 days)
        expected_rate = 1000 / (2 * 365.25)
        expected_mean = 1 / expected_rate
        
        # K-S test comparing to exponential distribution
        ks_statistic, p_value = stats.kstest(inter_arrivals, 
                                            'expon', 
                                            args=(0, expected_mean))
        
        # p-value > 0.05 suggests data follows exponential distribution
        assert p_value > 0.05, \
            f"Inter-arrival times don't follow exponential distribution (p={p_value:.3f})"
    
    def test_enrollment_uniformity_across_time(self, protocol_path):
        """Test that enrollments are uniform across the simulation period."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        results = runner.run("abs", n_patients=600, 
                           duration_years=1.0, seed=54321)
        
        # Divide year into months and count enrollments
        start_date = datetime(2024, 1, 1)
        monthly_counts = [0] * 12
        
        for patient in results.patient_histories.values():
            if hasattr(patient, 'enrollment_date') and patient.enrollment_date:
                month = patient.enrollment_date.month - 1
                monthly_counts[month] += 1
        
        # Chi-square test for uniformity
        expected_per_month = 600 / 12  # 50 per month
        chi2, p_value = stats.chisquare(monthly_counts)
        
        # p-value > 0.05 suggests uniform distribution
        assert p_value > 0.05, \
            f"Enrollment not uniform across months (p={p_value:.3f})"
        
        # Also check no month is too extreme
        min_count = min(monthly_counts)
        max_count = max(monthly_counts)
        assert min_count >= expected_per_month * 0.5, \
            f"Month with too few patients: {min_count}"
        assert max_count <= expected_per_month * 1.5, \
            f"Month with too many patients: {max_count}"
    
    def test_des_abs_consistency(self, protocol_path):
        """Test that DES and ABS engines produce similar distributions."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        # Run both engines with same parameters
        n_patients = 400
        duration = 1.5
        seed = 99999
        
        runner_abs = SimulationRunner(spec)
        results_abs = runner_abs.run("abs", n_patients=n_patients,
                                   duration_years=duration, seed=seed)
        
        runner_des = SimulationRunner(spec)
        results_des = runner_des.run("des", n_patients=n_patients,
                                   duration_years=duration, seed=seed)
        
        # Both should produce similar patient counts
        assert abs(results_abs.patient_count - results_des.patient_count) <= 20, \
            f"ABS ({results_abs.patient_count}) and DES ({results_des.patient_count}) " \
            f"counts differ too much"
        
        # Both should have similar injection patterns
        injection_diff = abs(results_abs.total_injections - results_des.total_injections)
        assert injection_diff <= max(results_abs.total_injections, 
                                   results_des.total_injections) * 0.15, \
            f"Injection counts differ too much: ABS={results_abs.total_injections}, " \
            f"DES={results_des.total_injections}"
    
    def test_large_scale_enrollment(self, protocol_path):
        """Test system handles large numbers of patients correctly."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        # Large scale test
        n_patients = 2000
        duration = 2.0
        
        results = runner.run("abs", n_patients=n_patients,
                           duration_years=duration, seed=11111)
        
        # Should achieve very close to target with large numbers
        actual = results.patient_count
        relative_error = abs(actual - n_patients) / n_patients
        
        assert relative_error < 0.02, \
            f"Large scale: expected {n_patients}, got {actual} (error: {relative_error:.1%})"
    
    def test_seed_reproducibility_with_staggered(self, protocol_path):
        """Test that same seed produces identical enrollment patterns."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        # Run twice with same seed
        seed = 67890
        
        runner1 = SimulationRunner(spec)
        results1 = runner1.run("abs", n_patients=200, 
                             duration_years=1.0, seed=seed)
        
        runner2 = SimulationRunner(spec)
        results2 = runner2.run("abs", n_patients=200,
                             duration_years=1.0, seed=seed)
        
        # Should get exactly the same results
        assert results1.patient_count == results2.patient_count
        assert results1.total_injections == results2.total_injections
        
        # Extract and compare enrollment dates
        dates1 = sorted([p.enrollment_date for p in results1.patient_histories.values() 
                        if hasattr(p, 'enrollment_date')])
        dates2 = sorted([p.enrollment_date for p in results2.patient_histories.values()
                        if hasattr(p, 'enrollment_date')])
        
        assert len(dates1) == len(dates2), "Different number of enrollment dates"
        
        # All dates should match exactly
        for d1, d2 in zip(dates1, dates2):
            assert d1 == d2, f"Enrollment dates don't match: {d1} vs {d2}"