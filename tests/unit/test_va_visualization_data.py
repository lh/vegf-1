"""
Test that VA visualization functions receive properly structured data.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from streamlit_app.simulation_runner import (
    generate_va_over_time_plot,
    generate_va_distribution_plot,
    generate_va_over_time_thumbnail,
    generate_va_distribution_thumbnail
)


class TestVAVisualizationData:
    """Test visual acuity visualization data requirements."""
    
    @pytest.fixture
    def minimal_valid_results(self):
        """Create minimal valid results structure."""
        return {
            'mean_va_data': [
                {
                    'time': 0,
                    'visual_acuity': 70.0,
                    'std_error': 1.0,
                    'sample_size': 100
                },
                {
                    'time': 1,
                    'visual_acuity': 69.5,
                    'std_error': 1.1,
                    'sample_size': 98
                },
                {
                    'time': 2,
                    'visual_acuity': 69.0,
                    'std_error': 1.2,
                    'sample_size': 95
                }
            ],
            'patient_data': {
                'patient_0': [
                    {'time': 0, 'vision': 72.0},
                    {'time': 1, 'vision': 71.5},
                    {'time': 2, 'vision': 71.0}
                ],
                'patient_1': [
                    {'time': 0, 'vision': 68.0},
                    {'time': 1, 'vision': 67.5},
                    {'time': 2, 'vision': 67.0}
                ]
            },
            'simulation_type': 'ABS',
            'population_size': 100,
            'duration_years': 5
        }
    
    def test_mean_plot_data_structure(self, minimal_valid_results):
        """Test that mean plot works with expected data structure."""
        fig = generate_va_over_time_plot(minimal_valid_results)
        assert fig is not None
        assert len(fig.get_axes()) > 0
    
    def test_distribution_plot_data_structure(self, minimal_valid_results):
        """Test that distribution plot works with expected data structure."""
        fig = generate_va_distribution_plot(minimal_valid_results)
        assert fig is not None
        assert len(fig.get_axes()) > 0
    
    def test_mean_thumbnail_data_structure(self, minimal_valid_results):
        """Test that mean thumbnail works with expected data structure."""
        fig = generate_va_over_time_thumbnail(minimal_valid_results)
        assert fig is not None
        assert len(fig.get_axes()) > 0
    
    def test_distribution_thumbnail_data_structure(self, minimal_valid_results):
        """Test that distribution thumbnail works with expected data structure."""
        fig = generate_va_distribution_thumbnail(minimal_valid_results)
        assert fig is not None
        assert len(fig.get_axes()) > 0
    
    def test_missing_mean_data_fails(self):
        """Test that missing mean_va_data fails appropriately."""
        results = {
            'patient_data': {'patient_0': [{'time': 0, 'vision': 70}]},
            'simulation_type': 'ABS',
            'population_size': 1,
            'duration_years': 1
        }
        
        with pytest.raises(KeyError):
            generate_va_over_time_plot(results)
    
    def test_missing_patient_data_fails(self):
        """Test that missing patient_data fails for distribution plot."""
        results = {
            'mean_va_data': [{'time': 0, 'visual_acuity': 70}],
            'simulation_type': 'ABS',
            'population_size': 1,
            'duration_years': 1
        }
        
        with pytest.raises(ValueError, match="Patient-level data is required"):
            generate_va_distribution_plot(results)
    
    def test_invalid_time_column_fails(self):
        """Test that data without time column fails appropriately."""
        results = {
            'mean_va_data': [
                {
                    'invalid_column': 0,
                    'visual_acuity': 70.0,
                    'std_error': 1.0
                }
            ],
            'simulation_type': 'ABS',
            'population_size': 100,
            'duration_years': 5
        }
        
        with pytest.raises(ValueError, match="No time column found"):
            generate_va_over_time_plot(results)
    
    def test_expected_column_names(self, minimal_valid_results):
        """Test that we use expected column names consistently."""
        # Check mean_va_data structure
        mean_data = minimal_valid_results['mean_va_data'][0]
        assert 'time' in mean_data or 'time_months' in mean_data
        assert 'visual_acuity' in mean_data
        assert 'std_error' in mean_data
        assert 'sample_size' in mean_data
        
        # Check patient_data structure
        patient_data = minimal_valid_results['patient_data']
        first_patient = list(patient_data.values())[0]
        first_visit = first_patient[0]
        assert 'time' in first_visit or 'time_months' in first_visit
        assert 'vision' in first_visit or 'visual_acuity' in first_visit
    
    @pytest.mark.parametrize("time_column", ["time", "time_months"])
    def test_different_time_columns(self, time_column):
        """Test that both time and time_months columns work."""
        results = {
            'mean_va_data': [
                {
                    time_column: 0,
                    'visual_acuity': 70.0,
                    'std_error': 1.0,
                    'sample_size': 100
                },
                {
                    time_column: 1,
                    'visual_acuity': 69.5,
                    'std_error': 1.1,
                    'sample_size': 98
                }
            ],
            'simulation_type': 'ABS',
            'population_size': 100,
            'duration_years': 5
        }
        
        # Should work with either column name
        fig = generate_va_over_time_plot(results)
        assert fig is not None
    
    def test_mean_plot_y_axis_consistency(self, minimal_valid_results):
        """Test that mean VA plot uses consistent 0-85 y-axis range."""
        # Modify data to have values in the 40-50 range
        for point in minimal_valid_results['mean_va_data']:
            point['visual_acuity'] = 45.0
        
        fig = generate_va_over_time_plot(minimal_valid_results)
        
        # The plot has dual axes, we want the second (right) axis for acuity
        axes = fig.get_axes()
        acuity_axis = axes[1] if len(axes) > 1 else axes[0]
        
        ylim = acuity_axis.get_ylim()
        assert ylim == (0, 85), f"Expected y-axis range (0, 85), got {ylim}"
    
    def test_distribution_plot_has_dual_axes(self):
        """Test that distribution plot has dual axes for consistency."""
        # Need at least 5 patients at a time point for percentile calculation
        results = {
            'patient_data': {
                f'patient_{i}': [
                    {'time': 0, 'vision': 70 + i},
                    {'time': 3, 'vision': 71 + i},
                    {'time': 6, 'vision': 69 + i}
                ] for i in range(10)  # 10 patients to ensure we have enough data
            },
            'simulation_type': 'ABS',
            'population_size': 10,
            'duration_years': 1
        }
        
        fig = generate_va_distribution_plot(results)
        
        axes = fig.get_axes()
        assert len(axes) == 2, f"Expected 2 axes (counts + acuity), got {len(axes)}"
    
    def test_distribution_plot_y_axis_consistency(self):
        """Test that distribution plot uses consistent 0-85 y-axis range."""
        # Need sufficient data for percentile calculation
        results = {
            'patient_data': {
                f'patient_{i}': [
                    {'time': 0, 'vision': 45 + i},  # Values in 45-55 range
                    {'time': 3, 'vision': 46 + i},
                    {'time': 6, 'vision': 44 + i}
                ] for i in range(10)
            },
            'simulation_type': 'ABS',
            'population_size': 10,
            'duration_years': 1
        }
        
        fig = generate_va_distribution_plot(results)
        
        # Get the acuity axis (should be the second axis)
        axes = fig.get_axes()
        acuity_axis = axes[1]
        
        ylim = acuity_axis.get_ylim()
        assert ylim == (0, 85), f"Expected y-axis range (0, 85), got {ylim}"
    
    def test_distribution_plot_has_sample_size_bars(self):
        """Test that distribution plot includes sample size bars."""
        results = {
            'patient_data': {
                f'patient_{i}': [
                    {'time': 0, 'vision': 70 + i},
                    {'time': 3, 'vision': 71 + i},
                    {'time': 6, 'vision': 69 + i}
                ] for i in range(10)
            },
            'simulation_type': 'ABS',
            'population_size': 10,
            'duration_years': 1
        }
        
        fig = generate_va_distribution_plot(results)
        
        # Get the counts axis (should be the first axis)
        axes = fig.get_axes()
        counts_axis = axes[0]
        
        # Check for bar patches
        bar_patches = counts_axis.patches
        assert len(bar_patches) > 0, "Expected sample size bars in distribution plot"
    
    def test_distribution_plot_legend_positioning(self):
        """Test that distribution plot legend is positioned at the top."""
        results = {
            'patient_data': {
                f'patient_{i}': [
                    {'time': 0, 'vision': 70 + i},
                    {'time': 3, 'vision': 71 + i}
                ] for i in range(10)
            },
            'simulation_type': 'ABS',
            'population_size': 10,
            'duration_years': 1
        }
        
        fig = generate_va_distribution_plot(results)
        
        # Get all axes
        axes = fig.get_axes()
        
        # Check that at least one axis has a legend
        has_legend = False
        for ax in axes:
            if ax.get_legend() is not None:
                has_legend = True
                legend = ax.get_legend()
                # Check legend is positioned at top (bbox anchor y > 1)
                if hasattr(legend, '_bbox_to_anchor'):
                    bbox = legend._bbox_to_anchor
                    if bbox is not None and hasattr(bbox, 'y1'):
                        assert bbox.y1 > 1, "Legend should be positioned above the plot"
                break
        
        assert has_legend, "Plot should have a legend"
    
    def test_distribution_plot_axis_styling(self):
        """Test that distribution plot has consistent axis styling with mean plot."""
        results = {
            'patient_data': {
                f'patient_{i}': [
                    {'time': 0, 'vision': 70 + i},
                    {'time': 3, 'vision': 71 + i}
                ] for i in range(10)
            },
            'simulation_type': 'ABS',
            'population_size': 10,
            'duration_years': 1
        }
        
        fig = generate_va_distribution_plot(results)
        axes = fig.get_axes()
        
        # Check that we have dual axes
        assert len(axes) == 2
        
        # Check spine configuration
        counts_ax = axes[0]
        acuity_ax = axes[1]
        
        # Verify spine visibility matches the first chart
        assert not counts_ax.spines['top'].get_visible()
        assert not acuity_ax.spines['top'].get_visible()
        assert counts_ax.spines['left'].get_visible()
        assert counts_ax.spines['bottom'].get_visible()
        assert not counts_ax.spines['right'].get_visible()
        assert acuity_ax.spines['right'].get_visible()
        assert not acuity_ax.spines['left'].get_visible()
        assert not acuity_ax.spines['bottom'].get_visible()
        
        # Check spine styling (light, thin lines)
        assert counts_ax.spines['left'].get_linewidth() == 0.5
        assert counts_ax.spines['bottom'].get_linewidth() == 0.5
        assert acuity_ax.spines['right'].get_linewidth() == 0.5
    
    def test_plot_figure_sizes_consistent(self):
        """Test that mean and distribution plots have the same figure size."""
        # Create test data with sufficient patients for percentile calculation
        results = {
            'mean_va_data': [
                {'time': 0, 'visual_acuity': 65, 'std_error': 2.0, 'sample_size': 100},
                {'time': 3, 'visual_acuity': 68, 'std_error': 1.8, 'sample_size': 95},
                {'time': 6, 'visual_acuity': 67, 'std_error': 2.1, 'sample_size': 90},
            ],
            'patient_data': {
                f'patient_{i}': [
                    {'time': 0, 'vision': 65 + i},
                    {'time': 3, 'vision': 68 + i},
                    {'time': 6, 'vision': 67 + i}
                ] for i in range(10)  # Need at least 5 for percentiles
            },
            'simulation_type': 'ABS',
            'population_size': 10,
            'duration_years': 1
        }
        
        # Generate both plots
        fig1 = generate_va_over_time_plot(results)
        fig2 = generate_va_distribution_plot(results)
        
        # Get figure sizes
        size1 = fig1.get_size_inches()
        size2 = fig2.get_size_inches()
        
        # Check that sizes are equal
        assert np.allclose(size1, size2), f"Figure sizes differ: {size1} vs {size2}"
        
        # Check that both are the expected size (10, 6)
        expected_size = np.array([10.0, 6.0])
        assert np.allclose(size1, expected_size), f"Mean plot size {size1} doesn't match expected {expected_size}"
        assert np.allclose(size2, expected_size), f"Distribution plot size {size2} doesn't match expected {expected_size}"
        
        # Also check subplot positions to ensure consistency
        axes1 = fig1.get_axes()
        axes2 = fig2.get_axes()
        
        # Get subplot positions
        pos1 = axes1[0].get_position()
        pos2 = axes2[0].get_position()
        
        # Check that the main axis positions are similar
        assert np.allclose(pos1.width, pos2.width, rtol=0.1), f"Axis widths differ: {pos1.width} vs {pos2.width}"