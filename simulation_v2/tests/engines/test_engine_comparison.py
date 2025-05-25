"""
Test that ABS and DES engines produce statistically similar results.

This is where we explore how the two approaches might diverge.
"""

import pytest
import numpy as np
from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.engines.des_engine import DESEngine
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol


class TestEngineConsistency:
    """Test that both engines produce similar aggregate results."""
    
    def test_both_engines_runnable(self):
        """Both engines should implement the same interface."""
        disease_model = DiseaseModel()
        protocol = StandardProtocol()
        
        abs_engine = ABSEngine(disease_model, protocol, n_patients=10)
        des_engine = DESEngine(disease_model, protocol, n_patients=10)
        
        # Both should have run method
        assert hasattr(abs_engine, 'run')
        assert hasattr(des_engine, 'run')
        
    def test_similar_injection_counts(self):
        """Total injections should be statistically similar."""
        disease_model = DiseaseModel(seed=42)
        protocol = StandardProtocol()
        
        # Run both engines with same parameters
        abs_engine = ABSEngine(disease_model, protocol, n_patients=100, seed=42)
        abs_results = abs_engine.run(duration_years=2)
        
        des_engine = DESEngine(disease_model, protocol, n_patients=100, seed=42)
        des_results = des_engine.run(duration_years=2)
        
        # Compare total injections
        abs_injections = abs_results.total_injections
        des_injections = des_results.total_injections
        
        # Should be within 10% of each other
        ratio = abs_injections / des_injections
        assert 0.9 <= ratio <= 1.1, f"ABS: {abs_injections}, DES: {des_injections}"
        
    def test_similar_vision_outcomes(self):
        """Mean vision at end should be similar."""
        disease_model = DiseaseModel(seed=42)
        protocol = StandardProtocol()
        
        # Run simulations
        abs_engine = ABSEngine(disease_model, protocol, n_patients=100, seed=42)
        abs_results = abs_engine.run(duration_years=2)
        
        des_engine = DESEngine(disease_model, protocol, n_patients=100, seed=42)
        des_results = des_engine.run(duration_years=2)
        
        # Compare mean final vision
        abs_mean_vision = abs_results.mean_final_vision
        des_mean_vision = des_results.mean_final_vision
        
        # Should be within 2 ETDRS letters
        assert abs(abs_mean_vision - des_mean_vision) < 2.0
        
    def test_discontinuation_patterns(self):
        """Discontinuation rates should be similar."""
        disease_model = DiseaseModel(seed=42)
        protocol = StandardProtocol()
        
        abs_engine = ABSEngine(disease_model, protocol, n_patients=200, seed=42)
        abs_results = abs_engine.run(duration_years=3)
        
        des_engine = DESEngine(disease_model, protocol, n_patients=200, seed=42)
        des_results = des_engine.run(duration_years=3)
        
        # Compare discontinuation rates
        abs_disc_rate = abs_results.discontinuation_rate
        des_disc_rate = des_results.discontinuation_rate
        
        # Should be within 5 percentage points
        assert abs(abs_disc_rate - des_disc_rate) < 0.05
        

class TestEngineDifferences:
    """Test expected differences between engines."""
    
    def test_abs_has_clinician_variation(self):
        """ABS should model individual clinician behavior."""
        disease_model = DiseaseModel()
        protocol = StandardProtocol()
        
        abs_engine = ABSEngine(
            disease_model, 
            protocol, 
            n_patients=100,
            enable_clinician_variation=True
        )
        
        results = abs_engine.run(duration_years=2)
        
        # Should have clinician assignment data
        assert hasattr(results, 'clinician_assignments')
        assert len(results.clinician_assignments) > 0
        
        # Different clinicians should have different treatment patterns
        clinician_stats = results.clinician_treatment_stats
        injection_rates = [stats['injection_rate'] for stats in clinician_stats.values()]
        
        # There should be variation
        assert max(injection_rates) > min(injection_rates)
        
    def test_des_has_consistent_scheduling(self):
        """DES should have more consistent visit intervals."""
        disease_model = DiseaseModel()
        protocol = StandardProtocol()
        
        des_engine = DESEngine(disease_model, protocol, n_patients=50)
        results = des_engine.run(duration_years=1)
        
        # Analyze visit intervals
        for patient_visits in results.patient_histories.values():
            intervals = []
            for i in range(1, len(patient_visits)):
                days_between = (patient_visits[i]['date'] - patient_visits[i-1]['date']).days
                intervals.append(days_between)
                
            if intervals:
                # DES should have low variance in intervals
                interval_variance = np.var(intervals)
                assert interval_variance < 100  # Low variance expected
                

class TestEngineScalability:
    """Test how engines handle different scales."""
    
    @pytest.mark.parametrize("n_patients", [10, 100, 1000])
    def test_both_scale_linearly(self, n_patients):
        """Runtime should scale roughly linearly with patients."""
        disease_model = DiseaseModel()
        protocol = StandardProtocol()
        
        # We won't actually test runtime here, just that they complete
        abs_engine = ABSEngine(disease_model, protocol, n_patients=n_patients)
        abs_results = abs_engine.run(duration_years=1)
        assert abs_results.patient_count == n_patients
        
        des_engine = DESEngine(disease_model, protocol, n_patients=n_patients)
        des_results = des_engine.run(duration_years=1)
        assert des_results.patient_count == n_patients