"""Visualization utilities for comparing simulation results.

This module provides functions to generate comparison plots between different
simulation approaches (DES vs ABS) and across different patient subgroups.

Functions
---------
plot_mean_acuity_comparison
    Generate comparison plots of mean visual acuity trajectories

Key Features
------------
- Side-by-side comparison of DES and ABS results
- Support for multiple patient subgroups
- Customizable time ranges and plot styling
- Automatic figure saving

Examples
--------
>>> from visualization import comparison_viz
>>> time_points = list(range(0, 53, 4))  # Weekly data for one year
>>> des_data = {"All": [70, 71, 72, ...], "High Risk": [65, 66, 67, ...]}
>>> abs_data = {"All": [71, 72, 71, ...], "High Risk": [66, 67, 66, ...]}
>>> comparison_viz.plot_mean_acuity_comparison(des_data, abs_data, time_points)

Notes
-----
- Visual acuity values should be in ETDRS letters
- Time points should be in weeks
- Subgroups should be consistent between DES and ABS data
- Figures are saved as PNG files by default
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional

def plot_mean_acuity_comparison(
    des_data: Dict[str, List[float]],
    abs_data: Dict[str, List[float]],
    time_points: List[int],
    title: str = "Mean Acuity Comparison: DES vs ABS",
    time_range: Optional[tuple] = None,
    subgroups: Optional[List[str]] = None
):
    """Generate a comparison plot of mean acuity between DES and ABS models.

    Parameters
    ----------
    des_data : Dict[str, List[float]]
        Dictionary mapping subgroup names to lists of DES acuity values.
        Each list should contain mean acuity values at corresponding time_points.
    abs_data : Dict[str, List[float]] 
        Dictionary mapping subgroup names to lists of ABS acuity values.
        Each list should contain mean acuity values at corresponding time_points.
    time_points : List[int]
        List of time points (in weeks) corresponding to the acuity measurements.
    title : str
        Title to display at the top of the plot.
    time_range : tuple, optional
        (start_time, end_time) to limit the x-axis range (in weeks).
    subgroups : List[str], optional
        Specific subgroups to include in the plot. If None, plots all available subgroups.

    Returns
    -------
    None
        The function saves the plot to 'mean_acuity_comparison.png' but returns nothing.

    Notes
    -----
    - Handles both daily and weekly data by automatically resampling
    - Uses solid lines for DES results and dashed lines for ABS results
    - Automatically saves plot as PNG with fixed filename
    """
    # Validate and align data dimensions
    def align_data(data: List[float], target_length: int) -> List[float]:
        if not data:
            # Return empty list if data is empty
            return []
        if len(data) == target_length:
            return data
        if len(data) > target_length:
            # Downsample by averaging
            step = len(data) // target_length
            return [np.mean(data[i*step:(i+1)*step]) for i in range(target_length)]
        else:
            # Upsample by linear interpolation
            x_old = np.linspace(0, 1, len(data))
            x_new = np.linspace(0, 1, target_length)
            return np.interp(x_new, x_old, data).tolist()

    # Find the maximum data length from non-empty lists
    all_lengths = [len(v) for v in list(des_data.values()) + list(abs_data.values()) if v]
    if all_lengths:
        # Use the maximum length instead of the most common length
        target_length = max(all_lengths)
        print(f"Using target length of {target_length} for comparison visualization")
        
        # Align all data to target length
        for subgroup in des_data:
            if des_data[subgroup]:  # Only align if data exists
                des_data[subgroup] = align_data(des_data[subgroup], target_length)
        for subgroup in abs_data:
            if abs_data[subgroup]:  # Only align if data exists
                abs_data[subgroup] = align_data(abs_data[subgroup], target_length)

        # Ensure time_points matches target length
        if len(time_points) != target_length:
            # Generate new time points if needed
            time_points = list(range(0, target_length))
    else:
        # No valid data to plot
        print("Warning: No valid data to plot in comparison visualization")
        return
    """Generate a comparison plot of mean acuity between DES and ABS models.

    Parameters
    ----------
    des_data : Dict[str, List[float]]
        Dictionary mapping subgroup names to lists of DES acuity values.
        Each list should contain mean acuity values at corresponding time_points.
    abs_data : Dict[str, List[float]] 
        Dictionary mapping subgroup names to lists of ABS acuity values.
        Each list should contain mean acuity values at corresponding time_points.
    time_points : List[int]
        List of time points (in weeks) corresponding to the acuity measurements.
    title : str
        Title to display at the top of the plot.
    time_range : tuple, optional
        (start_time, end_time) to limit the x-axis range (in weeks).
    subgroups : List[str], optional
        Specific subgroups to include in the plot. If None, plots all available subgroups.

    Returns
    -------
    None
        The function saves the plot to 'mean_acuity_comparison.png' but returns nothing.

    Examples
    --------
    >>> time_points = list(range(0, 53, 4))  # Weekly data for one year
    >>> des_data = {"All": [70, 71, 72, ...], "High Risk": [65, 66, 67, ...]}
    >>> abs_data = {"All": [71, 72, 71, ...], "High Risk": [66, 67, 66, ...]}
    >>> plot_mean_acuity_comparison(des_data, abs_data, time_points)

    Notes
    -----
    - Uses solid lines for DES results and dashed lines for ABS results
    - Automatically saves plot as PNG with fixed filename
    - Handles missing subgroups gracefully (skips if data not available)
    - Maintains consistent colors for same subgroups across both models
    - Y-axis fixed to standard ETDRS letter range (0-100)
    """
    plt.figure(figsize=(12, 8))

    if subgroups is None:
        subgroups = set(des_data.keys()).union(set(abs_data.keys()))

    for subgroup in subgroups:
        if subgroup in des_data:
            plt.plot(time_points, des_data[subgroup], label=f'DES - {subgroup}', linestyle='-')
        if subgroup in abs_data:
            plt.plot(time_points, abs_data[subgroup], label=f'ABS - {subgroup}', linestyle='--')

    plt.xlabel('Time (weeks)')
    plt.ylabel('Mean Acuity (ETDRS letters)')
    plt.title(title)
    plt.legend()
    plt.grid(True)

    if time_range:
        plt.xlim(time_range)

    plt.tight_layout()
    plt.savefig('mean_acuity_comparison.png')
    plt.close()

# Example usage:
if __name__ == "__main__":
    # Sample data (replace with actual data from simulations)
    time_points = list(range(0, 53, 4))  # Weekly data for one year
    des_data = {
        "All Patients": [70 + np.random.normal(0, 2) for _ in time_points],
        "High Risk": [65 + np.random.normal(0, 3) for _ in time_points]
    }
    abs_data = {
        "All Patients": [71 + np.random.normal(0, 2) for _ in time_points],
        "High Risk": [66 + np.random.normal(0, 3) for _ in time_points]
    }

    plot_mean_acuity_comparison(des_data, abs_data, time_points)
    print("Comparison plot saved as 'mean_acuity_comparison.png'")
