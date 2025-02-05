import pytest
from datetime import datetime, timedelta
import numpy as np
from analysis.simulation_results import SimulationResults

@pytest.fixture
def sample_results():
    """Create sample simulation results for testing"""
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(weeks=52)
    
    # Create sample patient histories with known outcomes
    histories = {
        "P001": [  # Early responder
            {
                "date": start_date,
                "vision": 60,
                "actions": ["vision_test"]
            },
            {
                "date": start_date + timedelta(weeks=4),
                "vision": 65,
                "actions": ["vision_test", "injection"]
            },
            {
                "date": start_date + timedelta(weeks=8),
                "vision": 70,
                "actions": ["vision_test", "injection"]
            }
        ],
        "P002": [  # Late responder
            {
                "date": start_date,
                "vision": 50,
                "actions": ["vision_test"]
            },
            {
                "date": start_date + timedelta(weeks=16),
                "vision": 60,
                "actions": ["vision_test", "injection"]
            },
            {
                "date": start_date + timedelta(weeks=52),
                "vision": 65,
                "actions": ["vision_test"]
            }
        ],
        "P003": [  # Non-responder
            {
                "date": start_date,
                "vision": 45,
                "actions": ["vision_test"]
            },
            {
                "date": start_date + timedelta(weeks=4),
                "vision": 43,
                "actions": ["vision_test", "injection"]
            },
            {
                "date": start_date + timedelta(weeks=52),
                "vision": 40,
                "actions": ["vision_test"]
            }
        ]
    }
    
    return SimulationResults(start_date, end_date, histories)

class TestSimulationResults:
    def test_analyze_treatment_response(self, sample_results):
        """Test treatment response analysis"""
        response = sample_results.analyze_treatment_response()
        
        # Check response categorization
        assert response["early_responders"] == 1/3  # P001
        assert response["late_responders"] == 1/3   # P002
        assert response["non_responders"] == 1/3    # P003
        
        # Check response timing
        assert 0 < response["response_time_mean"] < 52  # Mean weeks to response
        assert 0 < response["response_time_median"] < 52  # Median weeks to response

    def test_time_to_event_analysis(self, sample_results):
        """Test time-to-event analysis"""
        results = sample_results.time_to_event_analysis('vision_improvement')
        
        assert results["median_time"] is not None
        assert 0 <= results["event_rate"] <= 1
        assert 0 <= results["censored_rate"] <= 1
        assert len(results["survival_times"]) == 3  # One per patient
        assert len(results["censored"]) == 3
        
        # Test vision loss analysis
        loss_results = sample_results.time_to_event_analysis('vision_loss')
        assert loss_results["median_time"] is not None
        assert len(loss_results["survival_times"]) == 3

    def test_compare_groups(self, sample_results):
        """Test group comparison analysis"""
        # Compare responders vs non-responders
        responders = ["P001", "P002"]
        non_responders = ["P003"]
        
        comparison = sample_results.compare_groups(responders, non_responders)
        
        assert comparison["mean_diff"] > 0  # Responders should show better outcomes
        assert comparison["p_value"] is not None
        assert len(comparison["confidence_interval"]) == 2
        assert comparison["effect_size"] != 0

    def test_regression_analysis(self, sample_results):
        """Test regression analysis"""
        results = sample_results.regression_analysis()
        
        assert 0 <= results["r_squared"] <= 1
        assert len(results["coefficients"]) == 3  # baseline_vision, num_injections, num_visits
        assert len(results["p_values"]) == 3
        assert len(results["confidence_intervals"]) == 3
        
        # Check coefficient names
        expected_predictors = {'baseline_vision', 'num_injections', 'num_visits'}
        assert set(results["coefficients"].keys()) == expected_predictors
