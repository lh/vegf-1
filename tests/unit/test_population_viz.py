import pytest
from datetime import datetime, timedelta
import numpy as np
from visualization.population_viz import PopulationVisualizer
from analysis.simulation_results import SimulationResults

@pytest.fixture
def sample_results():
    """Create sample simulation results for testing"""
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(weeks=52)
    
    # Create sample patient histories
    histories = {
        "P001": [
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
                "date": start_date + timedelta(weeks=52),
                "vision": 70,
                "actions": ["vision_test"]
            }
        ],
        "P002": [
            {
                "date": start_date,
                "vision": 50,
                "actions": ["vision_test"]
            },
            {
                "date": start_date + timedelta(weeks=4),
                "vision": 45,
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

class TestPopulationVisualizer:
    def test_vision_distribution(self, sample_results):
        """Test vision distribution plotting"""
        # Just verify it runs without error
        PopulationVisualizer.plot_vision_distribution(
            sample_results, 
            show=False
        )
    
    def test_treatment_patterns(self, sample_results):
        """Test treatment pattern plotting"""
        PopulationVisualizer.plot_treatment_patterns(
            sample_results,
            show=False
        )
    
    def test_response_categories(self, sample_results):
        """Test response category plotting"""
        PopulationVisualizer.plot_response_categories(
            sample_results,
            show=False
        )
    
    def test_population_summary(self, sample_results):
        """Test population summary statistics"""
        summary = PopulationVisualizer.create_population_summary(sample_results)
        
        assert summary['total_patients'] == 2
        assert summary['mean_treatments'] == 1.0  # Each patient had 1 injection
        assert summary['loading_phase_completion'] == 0  # No patients completed loading
        
        # One patient improved, one declined
        assert summary['vision_improved_percent'] == 50.0
        assert summary['vision_declined_percent'] == 50.0
        assert summary['vision_stable_percent'] == 0.0
