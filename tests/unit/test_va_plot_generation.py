"""
Unit tests for visual acuity plot generation in simulation_runner.

Tests the generate_va_over_time_plot function to ensure:
1. It handles valid data correctly
2. It handles missing/empty data gracefully
3. Plot elements are created as expected
4. Baseline reference line is properly rendered
5. Legend only contains expected items
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Import the function to test
from streamlit_app.simulation_runner import generate_va_over_time_plot


class TestVAPlotGeneration:
    """Test suite for visual acuity plot generation."""
    
    @pytest.fixture
    def sample_results_with_data(self):
        """Create sample simulation results with visual acuity data."""
        # Create sample data for 12 months
        months = list(range(13))
        mean_va = [66.0, 67.5, 68.0, 68.5, 68.8, 69.0, 69.2, 69.0, 68.8, 68.5, 68.3, 68.0, 69.0]
        std_error = [0.5] * 13
        sample_size = [100, 98, 95, 92, 90, 88, 85, 80, 75, 70, 65, 60, 55]
        
        mean_va_data = []
        for i in range(13):
            mean_va_data.append({
                "time": months[i],
                "time_months": months[i],
                "visual_acuity": mean_va[i],
                "std_error": std_error[i],
                "sample_size": sample_size[i],
                "visual_acuity_raw": mean_va[i] - 0.2  # Simulate raw vs smoothed
            })
        
        results = {
            "mean_va_data": mean_va_data,
            "duration_years": 5,
            "simulation_type": "ABS",
            "population_size": 100,
            "failed": False
        }
        
        return results
    
    @pytest.fixture
    def minimal_results(self):
        """Create minimal valid results."""
        mean_va_data = [
            {"time": 0, "visual_acuity": 66.0},
            {"time": 1, "visual_acuity": 67.0},
            {"time": 2, "visual_acuity": 68.0}
        ]
        
        return {
            "mean_va_data": mean_va_data,
            "duration_years": 1,
            "simulation_type": "ABS",
            "population_size": 100
        }
    
    @pytest.fixture
    def empty_results(self):
        """Create results with no visual acuity data."""
        return {
            "mean_va_data": [],
            "duration_years": 5,
            "simulation_type": "ABS",
            "population_size": 100,
            "failed": False
        }
    
    @pytest.fixture
    def failed_results(self):
        """Create results for a failed simulation."""
        return {
            "failed": True,
            "error": "Test error message",
            "simulation_type": "ABS",
            "population_size": 100,
            "duration_years": 5
        }
    
    def test_plot_with_valid_data(self, sample_results_with_data):
        """Test plot generation with valid comprehensive data."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        # Check figure is created
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Get axes
        axes = fig.get_axes()
        assert len(axes) >= 2  # Should have at least 2 axes (counts and acuity)
        
        # Check there's data plotted
        ax_acuity = axes[-1]  # Last axis should be acuity
        lines = ax_acuity.get_lines()
        assert len(lines) > 0  # Should have at least one line
        
        # Check baseline line exists
        # The baseline should be a horizontal line
        baseline_lines = [line for line in lines if line.get_linestyle() == '--']
        assert len(baseline_lines) >= 1  # Should have at least one dashed line
        
        # Check legend entries
        legend = ax_acuity.get_legend()
        if legend:
            labels = [text.get_text() for text in legend.get_texts()]
            # Should NOT have "Individual Patients"
            assert "Individual Patients" not in labels
            # Should have expected entries
            assert any("Mean VA" in label for label in labels)
        
        plt.close(fig)
    
    def test_plot_with_minimal_data(self, minimal_results):
        """Test plot generation with minimal data."""
        fig = generate_va_over_time_plot(minimal_results)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Should still create a valid plot
        axes = fig.get_axes()
        assert len(axes) >= 1
        
        plt.close(fig)
    
    def test_plot_with_empty_data(self, empty_results):
        """Test plot generation with empty visual acuity data."""
        fig = generate_va_over_time_plot(empty_results)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Should show an error message
        axes = fig.get_axes()
        assert len(axes) >= 1
        
        # Check for text indicating no data
        ax = axes[0]
        texts = ax.texts
        assert len(texts) > 0
        assert any("No visual acuity data" in text.get_text() for text in texts)
        
        plt.close(fig)
    
    def test_plot_with_failed_simulation(self, failed_results):
        """Test plot generation with failed simulation results."""
        fig = generate_va_over_time_plot(failed_results)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Should show error message
        axes = fig.get_axes()
        assert len(axes) >= 1
        
        ax = axes[0]
        texts = ax.texts
        assert len(texts) > 0
        assert any("failed" in text.get_text().lower() for text in texts)
        
        plt.close(fig)
    
    def test_baseline_line_properties(self, sample_results_with_data):
        """Test that baseline line has correct properties."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        axes = fig.get_axes()
        ax_acuity = axes[-1]  # Last axis should be acuity
        
        # Find the baseline line (dashed horizontal line with 2 points)
        lines = ax_acuity.get_lines()
        baseline_line = None
        
        for line in lines:
            if line.get_linestyle() == '--':
                ydata = line.get_ydata()
                # Baseline should have exactly 2 points and be horizontal
                if len(ydata) == 2 and all(y == ydata[0] for y in ydata):
                    baseline_line = line
                    break
        
        assert baseline_line is not None  # Should find the baseline line
        
        # Check properties
        assert baseline_line.get_alpha() < 0.5  # Should be subtle
        assert baseline_line.get_linewidth() <= 1.0  # Should be thin (0.75)
        
        plt.close(fig)
    
    def test_confidence_intervals(self, sample_results_with_data):
        """Test that confidence intervals are plotted when std_error is available."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        axes = fig.get_axes()
        ax_acuity = axes[-1]
        
        # Check for filled areas (confidence intervals)
        collections = ax_acuity.collections
        assert len(collections) > 0  # Should have at least one filled area
        
        # Check the alpha for CI and other collections
        ci_found = False
        for collection in collections:
            alpha = collection.get_alpha()
            if alpha is not None and alpha < 0.2:
                ci_found = True  # Found the CI with very low alpha
        
        assert ci_found  # Should have at least one collection with very low alpha (CI)
        
        plt.close(fig)
    
    def test_no_individual_points(self, sample_results_with_data):
        """Test that no individual patient points are plotted."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        axes = fig.get_axes()
        ax_acuity = axes[-1]
        
        # Check scatter plots (would be individual points)
        # Should only have markers on the mean line, not individual scattered points
        collections = ax_acuity.collections
        
        # Count scatter collections
        scatter_count = 0
        for collection in collections:
            if hasattr(collection, 'get_offsets'):
                offsets = collection.get_offsets()
                if len(offsets) > 0:
                    scatter_count += 1
        
        # Check that we don't have excessive scatter collections
        # May have markers for mean line, but should be minimal
        assert scatter_count <= 2  # Allow for mean line markers and potential sample size variations
        
        plt.close(fig)
    
    def test_sample_size_bars(self, sample_results_with_data):
        """Test that sample size bars are displayed when available."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        axes = fig.get_axes()
        
        # First axis should be for sample size bars
        ax_counts = axes[0]
        
        # Check for bar patches
        patches = ax_counts.patches
        assert len(patches) > 0  # Should have sample size bars
        
        # Check bar properties
        for patch in patches:
            # Bars should use the patient counts color and alpha
            alpha = patch.get_alpha()
            assert alpha > 0  # Should be visible but not too prominent
        
        plt.close(fig)
    
    def test_axes_labels(self, sample_results_with_data):
        """Test that axes have proper labels."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        axes = fig.get_axes()
        
        # Check x-axis label
        ax_counts = axes[0]
        xlabel = ax_counts.get_xlabel()
        assert "Months" in xlabel
        
        # Check y-axis labels
        ax_acuity = axes[-1]
        ylabel = ax_acuity.get_ylabel()
        assert "Visual Acuity" in ylabel
        assert "letters" in ylabel
        
        plt.close(fig)
    
    def test_plot_title(self, sample_results_with_data):
        """Test that plot has appropriate title."""
        fig = generate_va_over_time_plot(sample_results_with_data)
        
        # Get the suptitle
        suptitle = fig._suptitle
        if suptitle:
            assert "Visual Acuity" in suptitle.get_text()
        
        plt.close(fig)