"""Test that x-axis labels show 'Months' instead of 'Time'."""

import pandas as pd
import matplotlib.pyplot as plt
from streamlit_app.simulation_runner import generate_va_over_time_plot, generate_va_distribution_plot


def test_xlabel_months():
    """Test both charts have 'Months' as x-axis label."""
    # Create simple mock data
    mock_data = {
        "mean_va_data": [
            {"time_months": 0, "visual_acuity": 60, "sample_size": 100},
            {"time_months": 12, "visual_acuity": 62, "sample_size": 90},
            {"time_months": 24, "visual_acuity": 64, "sample_size": 80},
        ],
        "duration_years": 2,
        "failed": False,
        "patient_data": {
            f"patient_{i}": [
                {"date": pd.Timestamp("2023-01-01") + pd.DateOffset(months=m), 
                 "vision": 60 + i}
                for m in [0, 12, 24]
            ]
            for i in range(5)
        }
    }
    
    # Generate both plots
    fig1 = generate_va_over_time_plot(mock_data)
    fig2 = generate_va_distribution_plot(mock_data)
    
    # Check x-axis labels
    plots = [("Mean VA", fig1), ("Distribution", fig2)]
    
    for plot_name, fig in plots:
        ax = fig.get_axes()[0]  # Get primary axis
        xlabel = ax.get_xlabel()
        print(f"{plot_name} plot x-axis label: '{xlabel}'")
        assert xlabel == "Months", f"Expected 'Months' but got '{xlabel}'"
    
    print("\nBoth plots correctly use 'Months' as x-axis label.")
    
    plt.close(fig1)
    plt.close(fig2)


if __name__ == "__main__":
    test_xlabel_months()