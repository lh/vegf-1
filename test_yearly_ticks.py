"""Test yearly x-axis ticks implementation."""

import pandas as pd
import matplotlib.pyplot as plt
from streamlit_app.simulation_runner import generate_va_over_time_plot, generate_va_distribution_plot


def test_yearly_ticks():
    """Test the yearly ticks on both VA plots."""
    # Create mock data with 60 months (5 years) of data
    months = list(range(0, 61, 3))  # Every 3 months for 5 years
    
    mean_va_data = []
    for month in months:
        mean_va_data.append({
            "time_months": month,
            "visual_acuity": 60 + month * 0.2,  # Gradual improvement
            "sample_size": 100 - int(month * 0.5)  # Gradual dropout
        })
    
    mock_data = {
        "mean_va_data": mean_va_data,
        "duration_years": 5,
        "failed": False,
        "patient_data": {
            f"patient_{i}": [
                {"date": pd.Timestamp("2020-01-01") + pd.DateOffset(months=m), 
                 "vision": 58 + i + m * 0.2}
                for m in months
            ]
            for i in range(10)  # 10 patients
        }
    }
    
    # Generate both plots
    fig1 = generate_va_over_time_plot(mock_data)
    fig2 = generate_va_distribution_plot(mock_data)
    
    # Check the x-axis ticks
    for fig_num, fig in enumerate([fig1, fig2], 1):
        ax = fig.get_axes()[0]  # Get the primary axis
        x_ticks = ax.get_xticks()
        print(f"\nFigure {fig_num} x-ticks: {x_ticks}")
        
        # Verify they are at yearly intervals
        expected_ticks = list(range(0, 61, 12))  # 0, 12, 24, 36, 48, 60
        
        # Check if all expected ticks are present
        for tick in expected_ticks:
            if tick not in x_ticks:
                print(f"  Missing expected tick: {tick}")
        
        # Check tick labels
        x_labels = [label.get_text() for label in ax.get_xticklabels()]
        print(f"  X-tick labels: {x_labels}")
    
    # Save the plots
    fig1.savefig('/Users/rose/Code/CC/test_yearly_ticks_mean.png', dpi=150, bbox_inches='tight')
    fig2.savefig('/Users/rose/Code/CC/test_yearly_ticks_dist.png', dpi=150, bbox_inches='tight')
    
    plt.close(fig1)
    plt.close(fig2)
    
    print("\nPlots saved with yearly x-axis ticks.")


if __name__ == "__main__":
    test_yearly_ticks()