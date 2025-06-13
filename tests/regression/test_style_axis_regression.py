"""
Focused regression test for the style_axis parameter issue.

This test specifically ensures that the style_axis function
doesn't accept invalid parameters like spine_color.
"""

import pytest
import matplotlib.pyplot as plt
import inspect
import sys
from pathlib import Path

# Add parent directory to path


class TestStyleAxisRegression:
    """Test to prevent regression of the style_axis spine_color issue."""
    
    def test_style_axis_parameters(self):
        """Test that style_axis has the correct parameters."""
        from ape.utils.tufte_zoom_style import style_axis
        
        # Get function signature
        sig = inspect.signature(style_axis)
        params = list(sig.parameters.keys())
        
        # These should be the only parameters
        expected_params = {'ax', 'xlabel', 'ylabel', 'remove_top', 'remove_right'}
        actual_params = set(params)
        
        # Check exact match
        assert actual_params == expected_params, \
            f"style_axis parameters changed. Expected {expected_params}, got {actual_params}"
        
        # Specifically ensure spine_color is not present
        assert 'spine_color' not in params, \
            "spine_color parameter should not exist in style_axis"
    
    def test_style_axis_usage_patterns(self):
        """Test common usage patterns of style_axis."""
        from ape.utils.tufte_zoom_style import style_axis
        
        # Create test figure
        fig, ax = plt.subplots()
        
        # All these should work
        style_axis(ax)  # Minimal usage
        style_axis(ax, xlabel="Time")  # With xlabel
        style_axis(ax, ylabel="Value")  # With ylabel
        style_axis(ax, xlabel="X", ylabel="Y")  # Both labels
        style_axis(ax, remove_top=True)  # Spine control
        style_axis(ax, remove_right=False)  # Keep right spine
        style_axis(ax, xlabel="X", ylabel="Y", remove_top=True, remove_right=True)  # All params
        
        # Clean up
        plt.close(fig)
    
    def test_style_axis_invalid_parameters(self):
        """Test that invalid parameters raise appropriate errors."""
        from ape.utils.tufte_zoom_style import style_axis
        
        fig, ax = plt.subplots()
        
        # This should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            style_axis(ax, spine_color='black')
        
        # Check error message mentions the invalid parameter
        assert 'spine_color' in str(exc_info.value)
        assert 'unexpected keyword argument' in str(exc_info.value)
        
        # Other invalid parameters should also fail
        with pytest.raises(TypeError):
            style_axis(ax, unknown_param='value')
        
        with pytest.raises(TypeError):
            style_axis(ax, color='red')  # Not a valid parameter
        
        plt.close(fig)
    
    def test_analysis_overview_style_axis_calls(self):
        """Test that Analysis Overview page would use style_axis correctly."""
        from ape.utils.tufte_zoom_style import style_axis, create_figure
        
        # Simulate the code pattern from Analysis Overview
        fig, ax = create_figure("Patient Trajectories")
        
        # Add some dummy data
        months = list(range(0, 37, 6))
        values = [70, 68, 66, 65, 64, 63, 62]
        ax.plot(months, values)
        
        # This is the pattern used in Analysis Overview
        ax.set_xticks(months)
        ax.set_xlim(0, 36)
        
        # This was the failing line - should work now
        style_axis(ax)  # No spine_color parameter
        
        # Verify the axis was styled
        assert not ax.spines['top'].get_visible()
        assert not ax.spines['right'].get_visible()
        
        plt.close(fig)


class TestVisualizationIntegration:
    """Test integration between visualization components."""
    
    def test_tufte_style_imports(self):
        """Test that all tufte style functions can be imported."""
        # These should all import successfully
        from ape.utils.tufte_zoom_style import (
            style_axis,
            create_figure,
            add_reference_line,
            format_zoom_legend,
            add_zoom_annotation,
            setup_zoom_tufte_style
        )
        
        # Verify they're callable
        assert callable(style_axis)
        assert callable(create_figure)
        assert callable(add_reference_line)
        assert callable(format_zoom_legend)
    
    def test_visualization_modes_imports(self):
        """Test visualization mode imports."""
        from ape.utils.visualization_modes import (
            init_visualization_mode,
            mode_aware_figure,
            get_mode_colors,
            apply_visualization_mode
        )
        
        # Verify they're callable
        assert callable(init_visualization_mode)
        assert callable(mode_aware_figure)
        assert callable(get_mode_colors)
        assert callable(apply_visualization_mode)
    
    def test_complete_visualization_workflow(self):
        """Test a complete visualization workflow."""
        from ape.utils.tufte_zoom_style import create_figure, style_axis, add_reference_line
        
        # Create figure
        fig, ax = create_figure("Test Visualization", subtitle="Testing workflow")
        
        # Add data
        import numpy as np
        x = np.linspace(0, 36, 100)
        y = 70 - x * 0.5 + np.random.normal(0, 1, 100)
        ax.plot(x, y, label="Vision", linewidth=2)
        
        # Add reference line
        add_reference_line(ax, 70, "Baseline", orientation='horizontal')
        
        # Style the axis (no spine_color!)
        style_axis(ax, xlabel="Time (months)", ylabel="Vision (ETDRS)")
        
        # Set limits
        ax.set_xlim(0, 36)
        ax.set_ylim(40, 80)
        
        # Verify styling was applied
        assert ax.get_xlabel() == "Time (months)"
        assert ax.get_ylabel() == "Vision (ETDRS)"
        assert not ax.spines['top'].get_visible()
        assert not ax.spines['right'].get_visible()
        
        plt.close(fig)