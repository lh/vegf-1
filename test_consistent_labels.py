"""Test that both VA charts have consistent labels for the measurement counts."""

import pandas as pd
import matplotlib.pyplot as plt
from streamlit_app.simulation_runner import generate_va_over_time_plot, generate_va_distribution_plot


def test_consistent_labels():
    """Test both charts for consistent labeling."""
    # Create mock data with sample size variation
    mock_data = {
        "mean_va_data": [
            {"time_months": 0, "visual_acuity": 60, "sample_size": 100},
            {"time_months": 3, "visual_acuity": 62, "sample_size": 85},
            {"time_months": 6, "visual_acuity": 63, "sample_size": 70},
            {"time_months": 9, "visual_acuity": 64, "sample_size": 55},
            {"time_months": 12, "visual_acuity": 65, "sample_size": 40},
        ],
        "duration_years": 2,
        "failed": False,
        "patient_data": {
            "patient_0": [
                {"date": pd.Timestamp("2023-01-01"), "vision": 62},
                {"date": pd.Timestamp("2023-04-01"), "vision": 64},
                {"date": pd.Timestamp("2023-07-01"), "vision": 65},
                {"date": pd.Timestamp("2023-10-01"), "vision": 66},
                {"date": pd.Timestamp("2024-01-01"), "vision": 67}
            ],
            "patient_1": [
                {"date": pd.Timestamp("2023-01-01"), "vision": 58},
                {"date": pd.Timestamp("2023-04-01"), "vision": 60},
                {"date": pd.Timestamp("2023-07-01"), "vision": 61},
                {"date": pd.Timestamp("2023-10-01"), "vision": 62},
                {"date": pd.Timestamp("2024-01-01"), "vision": 63}
            ],
            "patient_2": [
                {"date": pd.Timestamp("2023-01-01"), "vision": 55},
                {"date": pd.Timestamp("2023-04-01"), "vision": 57},
                {"date": pd.Timestamp("2023-07-01"), "vision": 59},
                {"date": pd.Timestamp("2023-10-01"), "vision": 60},
                {"date": pd.Timestamp("2024-01-01"), "vision": 61}
            ],
            # Add more patients for better distribution
            "patient_3": [
                {"date": pd.Timestamp("2023-01-01"), "vision": 65},
                {"date": pd.Timestamp("2023-04-01"), "vision": 66},
                {"date": pd.Timestamp("2023-07-01"), "vision": 67},
                {"date": pd.Timestamp("2023-10-01"), "vision": 68},
                {"date": pd.Timestamp("2024-01-01"), "vision": 69}
            ],
            "patient_4": [
                {"date": pd.Timestamp("2023-01-01"), "vision": 52},
                {"date": pd.Timestamp("2023-04-01"), "vision": 54},
                {"date": pd.Timestamp("2023-07-01"), "vision": 56},
                {"date": pd.Timestamp("2023-10-01"), "vision": 58},
                {"date": pd.Timestamp("2024-01-01"), "vision": 60}
            ]
        }
    }
    
    # Generate both plots
    fig1 = generate_va_over_time_plot(mock_data)
    fig2 = generate_va_distribution_plot(mock_data)
    
    # Check mean VA plot
    print("=== Mean VA Plot ===")
    title1 = fig1._suptitle.get_text()
    print(f"Title: {title1}")
    
    axes1 = fig1.get_axes()
    for i, ax in enumerate(axes1):
        ylabel = ax.get_ylabel()
        if ylabel:
            print(f"Axis {i} y-label: '{ylabel}'")
    
    # Check distribution plot
    print("\n=== Distribution Plot ===")
    if hasattr(fig2, '_suptitle') and fig2._suptitle:
        title2 = fig2._suptitle.get_text()
        print(f"Title: {title2}")
    else:
        print("Title: (no suptitle found)")
    
    axes2 = fig2.get_axes()
    for i, ax in enumerate(axes2):
        ylabel = ax.get_ylabel()
        if ylabel:
            print(f"Axis {i} y-label: '{ylabel}'")
            
    # Check legends
    print("\n=== Legends ===")
    for ax in axes1:
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                label = text.get_text()
                print(f"Mean VA plot legend: '{label}'")
                    
    for ax in axes2:
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                label = text.get_text()
                print(f"Distribution plot legend: '{label}'")
    
    # Save the plots for visual inspection
    fig1.savefig('/Users/rose/Code/CC/test_mean_va_plot.png', dpi=150, bbox_inches='tight')
    fig2.savefig('/Users/rose/Code/CC/test_distribution_plot.png', dpi=150, bbox_inches='tight')
    
    plt.close(fig1)
    plt.close(fig2)
    
    print("\nPlots saved for inspection.")
    print("Both plots should have 'Number of Measurements' in y-axis labels and legends.")


if __name__ == "__main__":
    test_consistent_labels()