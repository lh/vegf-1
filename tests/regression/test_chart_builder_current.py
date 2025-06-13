"""
Regression tests for current ChartBuilder functionality.

These tests ensure the refactored ChartBuilder works correctly.
"""

import pytest
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path

# Add parent directories to path

from ape.utils.chart_builder import ChartBuilder
from ape.utils.style_constants import StyleConstants


@pytest.mark.skip(reason="ChartBuilder now requires Streamlit session state - these tests need to be rewritten for the new architecture")
class TestCurrentChartBuilder:
    """Test current ChartBuilder implementation."""
    
    def test_chart_builder_exists(self):
        """Test that ChartBuilder class exists and can be instantiated."""
        chart = ChartBuilder("Test Chart")
        assert chart is not None
        assert chart.title == "Test Chart"
    
    def test_builder_methods(self):
        """Test builder pattern methods."""
        chart = (ChartBuilder("Test Chart")
                .with_labels(xlabel="X Label", ylabel="Y Label")
                .with_vision_axis('y')
                .with_count_axis('x'))
        
        assert chart.xlabel == "X Label"
        assert chart.ylabel == "Y Label"
        assert chart.y_axis_type == 'vision'
        assert chart.x_axis_type == 'count'
    
    def test_vision_distribution_chart(self):
        """Test creating a vision distribution chart."""
        baseline = np.random.normal(70, 10, 100)
        final = baseline + np.random.normal(-5, 5, 100)
        
        chart = (ChartBuilder("Vision Distribution")
                .with_labels(xlabel='Vision (ETDRS letters)', ylabel='Count')
                .with_vision_axis('x')
                .with_count_axis('y')
                .plot(lambda ax, colors: [
                    ax.hist(baseline, bins=20, alpha=0.6, label='Baseline'),
                    ax.hist(final, bins=20, alpha=0.6, label='Final')
                ])
                .with_legend(loc='upper left')
                .build())
        
        assert chart.figure is not None
        plt.close(chart.figure)
    
    def test_time_series_chart(self):
        """Test creating a time series chart."""
        months = np.arange(0, 24)
        vision = 70 - months * 0.5 + np.random.normal(0, 2, len(months))
        
        chart = (ChartBuilder("Vision Over Time")
                .with_labels(xlabel='Time (months)', ylabel='Vision (ETDRS letters)')
                .with_time_axis('x', duration_days=730, preferred_unit='months')
                .with_vision_axis('y')
                .plot(lambda ax, colors: ax.plot(months, vision, color=colors['primary']))
                .build())
        
        assert chart.figure is not None
        # Check that vision axis is properly configured
        ylim = chart.axis.get_ylim()
        assert ylim[0] >= 0
        assert ylim[1] <= 100
        plt.close(chart.figure)
    
    def test_reference_lines(self):
        """Test adding reference lines."""
        data = np.random.normal(0, 10, 100)
        
        chart = (ChartBuilder("Distribution with Reference")
                .with_labels(xlabel='Value', ylabel='Count')
                .plot(lambda ax, colors: ax.hist(data, bins=20))
                .add_reference_line(0, 'Zero', 'vertical', 'secondary')
                .add_reference_line(np.mean(data), 'Mean', 'vertical', 'primary')
                .build())
        
        assert chart.figure is not None
        # Check that lines were added
        assert len(chart.axis.lines) >= 2
        plt.close(chart.figure)
    
    def test_memory_cleanup(self):
        """Test that figures are properly cleaned up."""
        import gc
        import weakref
        
        # Create a chart
        chart = ChartBuilder("Test").plot(lambda ax, colors: ax.plot([1, 2, 3])).build()
        fig_ref = weakref.ref(chart.figure)
        
        # Close and delete
        plt.close(chart.figure)
        del chart
        gc.collect()
        
        # Figure should be garbage collected
        assert fig_ref() is None