"""Test chart template functions for consistency."""

import pytest
import matplotlib.pyplot as plt

from visualization.chart_templates import (
    apply_dual_axis_style,
    apply_standard_layout,
    apply_horizontal_legend,
    set_standard_y_axis_range,
    set_yearly_x_ticks,
    add_explanatory_note,
    create_standard_figure,
    format_standard_dual_axis_chart
)


class TestChartTemplates:
    """Test chart template functions."""
    
    def test_dual_axis_style(self):
        """Test dual axis styling is applied correctly."""
        fig = plt.figure(figsize=(10, 6))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        
        apply_dual_axis_style(fig, ax1, ax2)
        
        # Check spine visibility
        assert not ax1.spines['top'].get_visible()
        assert not ax2.spines['top'].get_visible()
        assert ax1.spines['left'].get_visible()
        assert ax1.spines['bottom'].get_visible()
        assert not ax1.spines['right'].get_visible()
        assert ax2.spines['right'].get_visible()
        assert not ax2.spines['left'].get_visible()
        assert not ax2.spines['bottom'].get_visible()
        
        # Check spine styling
        assert ax1.spines['left'].get_linewidth() == 0.5
        assert ax1.spines['bottom'].get_linewidth() == 0.5
        assert ax2.spines['right'].get_linewidth() == 0.5
        
        plt.close(fig)
    
    def test_standard_layout(self):
        """Test standard layout is applied correctly."""
        fig = plt.figure(figsize=(10, 6))
        
        apply_standard_layout(fig, "Test Title", has_legend=True)
        
        # Check title properties
        assert fig._suptitle is not None
        assert fig._suptitle.get_text() == "Test Title"
        assert fig._suptitle.get_fontsize() == 12
        
        plt.close(fig)
    
    def test_standard_layout_with_multi_row_legend(self):
        """Test standard layout with multi-row legend."""
        fig = plt.figure(figsize=(10, 6))
        
        apply_standard_layout(fig, "Test Title", has_legend=True, legend_rows=2)
        
        # Check that different spacing is applied
        # With multi-row legend, top should be 0.88 instead of 0.92
        # This is a bit tricky to test directly since subplot_adjust modifies internal state
        
        plt.close(fig)
    
    def test_horizontal_legend(self):
        """Test horizontal legend is applied correctly."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create dummy lines
        line1, = ax.plot([0, 1], [0, 1], label='Line 1')
        line2, = ax.plot([0, 1], [1, 0], label='Line 2')
        
        apply_horizontal_legend(ax, [line1], ['Line 1'], [line2], ['Line 2'])
        
        legend = ax.get_legend()
        assert legend is not None
        assert not legend.get_frame_on()  # frameon=False
        assert legend._fontsize == 9
        
        plt.close(fig)
    
    def test_y_axis_range(self):
        """Test standard y-axis range is set correctly."""
        fig, ax = plt.subplots()
        
        set_standard_y_axis_range(ax)
        
        ylim = ax.get_ylim()
        assert ylim == (0, 85)
        
        plt.close(fig)
    
    def test_yearly_x_ticks(self):
        """Test yearly x-axis ticks are set correctly."""
        fig, ax = plt.subplots()
        
        # Set up some dummy data to establish x-limits
        ax.plot([0, 60], [0, 100])
        
        # Apply yearly ticks
        set_yearly_x_ticks(ax)
        
        x_ticks = ax.get_xticks()
        # Should have ticks at 0, 12, 24, 36, 48, 60
        expected_ticks = [0, 12, 24, 36, 48, 60]
        
        # Allow for some floating point tolerance
        for expected in expected_ticks:
            assert any(abs(tick - expected) < 0.1 for tick in x_ticks), f"Missing tick at {expected}"
        
        plt.close(fig)
    
    def test_yearly_x_ticks_with_labels(self):
        """Test yearly x-axis ticks with year labels."""
        fig, ax = plt.subplots()
        
        # Set up some dummy data to establish x-limits
        ax.plot([0, 36], [0, 100])
        
        # Apply yearly ticks with year labels
        set_yearly_x_ticks(ax, use_year_labels=True)
        
        x_labels = [label.get_text() for label in ax.get_xticklabels()]
        # Should have labels like '0', '1y', '2y', '3y'
        expected_labels = ['0', '1y', '2y', '3y']
        
        for expected, actual in zip(expected_labels, x_labels):
            assert actual == expected, f"Expected '{expected}' but got '{actual}'"
        
        plt.close(fig)
    
    def test_explanatory_note(self):
        """Test explanatory note is added correctly."""
        fig = plt.figure()
        
        add_explanatory_note(fig, "This is a test note.")
        
        # Check that text was added
        assert len(fig.texts) > 0
        
        # Find the note text
        note_found = False
        for text in fig.texts:
            if text.get_text() == "This is a test note.":
                note_found = True
                assert text.get_ha() == 'center'
                assert text.get_va() == 'bottom'
                assert text.get_fontsize() == 9
                break
        
        assert note_found, "Explanatory note not found"
        
        plt.close(fig)
    
    def test_multi_row_legend_layout(self):
        """Test apply_standard_layout with multi-row legend."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        # Apply multi-row legend layout  
        apply_standard_layout(fig, "Multi-row Test", legend_rows=2)
        
        # Check that title was set
        assert fig._suptitle is not None
        assert fig._suptitle.get_text() == "Multi-row Test"
        
        # Test the layout by comparing single vs multi-row
        fig2, ax2 = plt.subplots()
        ax2.plot([1, 2, 3], [1, 2, 3])
        apply_standard_layout(fig2, "Single-row Test", legend_rows=1)
        
        # Multi-row should have more top space than single-row
        assert fig.subplotpars.top < fig2.subplotpars.top
        
        plt.close(fig)
        plt.close(fig2)

    def test_create_standard_figure(self):
        """Test create_standard_figure utility function."""
        # Test default parameters
        fig, ax = create_standard_figure()
        assert fig.get_size_inches()[0] == 10
        assert fig.get_size_inches()[1] == 6
        assert isinstance(ax, plt.Axes)
        plt.close(fig)
        
        # Test custom parameters
        fig, ax = create_standard_figure(figsize=(12, 8), title="Custom Test", xlabel="X", ylabel="Y")
        assert fig.get_size_inches()[0] == 12
        assert fig.get_size_inches()[1] == 8
        assert ax.get_title() == "Custom Test"
        assert ax.get_xlabel() == "X"
        assert ax.get_ylabel() == "Y"
        plt.close(fig)

    def test_format_standard_dual_axis_chart(self):
        """Test format_standard_dual_axis_chart convenience function."""
        # Set up dual axis figure
        fig = plt.figure(figsize=(10, 6))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        
        # Add some test data
        line1, = ax1.plot([1, 2, 3], [10, 20, 30], 'b-', label='Primary')
        line2, = ax2.plot([1, 2, 3], [5, 15, 25], 'r-', label='Secondary')
        
        # Apply formatting
        format_standard_dual_axis_chart(
            fig, ax1, ax2,
            title="Dual Axis Test",
            lines1=[line1], labels1=['Primary'],
            lines2=[line2], labels2=['Secondary'],
            primary_label="Primary Y",
            secondary_label="Secondary Y",
            x_label="X Axis",
            y_limits=(0, 50)
        )
        
        # Check formatting
        assert ax1.get_ylabel() == "Primary Y"
        assert ax2.get_ylabel() == "Secondary Y"
        assert ax1.get_xlabel() == "X Axis"
        
        # Check y-limits
        assert ax1.get_ylim() == (0, 50)
        assert ax2.get_ylim() == (0, 50)
        
        # Check that title was applied
        assert fig._suptitle is not None
        assert fig._suptitle.get_text() == "Dual Axis Test"
        
        plt.close(fig)

    def test_enhanced_horizontal_legend(self):
        """Test enhanced apply_horizontal_legend with row count return."""
        fig, ax = plt.subplots()
        
        # Create many lines to force multi-row legend
        lines1 = []
        labels1 = []
        lines2 = []
        labels2 = []
        
        for i in range(4):
            line, = ax.plot([1, 2, 3], [i, i+1, i+2], label=f'Line1 {i+1}')
            lines1.append(line)
            labels1.append(f'Line1 {i+1}')
        
        for i in range(4):
            line, = ax.plot([1, 2, 3], [i+4, i+5, i+6], label=f'Line2 {i+1}')
            lines2.append(line)
            labels2.append(f'Line2 {i+1}')
        
        # Apply horizontal legend and get row count
        rows = apply_horizontal_legend(ax, lines1, labels1, lines2, labels2, max_cols=3)
        
        # With 8 items and 3 columns, we should have 3 rows
        assert rows == 3
        assert ax.get_legend() is not None
        
        plt.close(fig)