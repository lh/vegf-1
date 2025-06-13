"""
Integration test to verify the data format produced by simulations
matches what visualization functions expect.
"""

import pytest
from simulation.abs import AgentBasedSimulation
from simulation.config import SimulationConfig
from streamlit_app.simulation_runner import (
    generate_va_over_time_plot,
    generate_va_distribution_plot,
    generate_va_over_time_thumbnail,
    generate_va_distribution_thumbnail
)


class TestSimulationDataFormat:
    """Test that simulation produces correctly formatted data."""
    
    @pytest.fixture
    def minimal_config(self):
        """Create minimal simulation config."""
        # Use the test configuration
        config = SimulationConfig.from_yaml("test_simulation")
        config.num_patients = 10  # Small for quick test
        config.duration_days = 365  # 1 year
        return config
    
    def test_abs_produces_correct_data_format(self, minimal_config):
        """Test that ABS produces the expected data format."""
        from datetime import datetime
        
        # Run simulation
        sim = AgentBasedSimulation(minimal_config, start_date=datetime(2024, 1, 1))
        sim.run()
        
        # Get results
        results = sim.get_results()
        
        # Check required fields exist
        assert "mean_va_data" in results
        assert "patient_histories" in results or "patient_data" in results
        assert "simulation_type" in results
        assert "population_size" in results
        assert "duration_years" in results
        
        # Check mean_va_data structure
        mean_data = results["mean_va_data"]
        assert isinstance(mean_data, list)
        assert len(mean_data) > 0
        
        # Check first element has required fields
        first_point = mean_data[0]
        assert "time" in first_point or "time_months" in first_point
        assert "visual_acuity" in first_point
        assert "std_error" in first_point
        assert "sample_size" in first_point
        
        # Test that visualization functions work with this data
        fig1 = generate_va_over_time_plot(results)
        assert fig1 is not None
        
        fig2 = generate_va_distribution_plot(results)
        assert fig2 is not None
        
        fig3 = generate_va_over_time_thumbnail(results)
        assert fig3 is not None
        
        fig4 = generate_va_distribution_thumbnail(results)
        assert fig4 is not None
    
    def test_consistent_time_columns(self, minimal_config):
        """Test that time columns are consistent."""
        from datetime import datetime
        
        sim = AgentBasedSimulation(minimal_config, start_date=datetime(2024, 1, 1))
        sim.run()
        results = sim.get_results()
        
        # Check mean_va_data
        mean_data = results["mean_va_data"]
        time_columns = []
        for point in mean_data:
            if "time" in point:
                time_columns.append("time")
            if "time_months" in point:
                time_columns.append("time_months")
        
        # Should use consistent time column
        assert len(set(time_columns)) == 1, "Inconsistent time columns in mean_va_data"
        
        # Check patient data
        patient_data = results.get("patient_histories", results.get("patient_data", {}))
        if patient_data:
            patient_time_columns = []
            for patient_id, history in patient_data.items():
                if isinstance(history, list) and history:
                    visit = history[0]
                    if "time" in visit:
                        patient_time_columns.append("time")
                    if "time_months" in visit:
                        patient_time_columns.append("time_months")
            
            # Should use consistent time column
            assert len(set(patient_time_columns)) <= 1, "Inconsistent time columns in patient data"