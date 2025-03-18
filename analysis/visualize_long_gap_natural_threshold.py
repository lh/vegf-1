"""
Visualize Long Gap Patients with Natural Threshold

This script creates visualizations for long-gap patients using the natural threshold
derived from the PCA clustering results (approximately 794 days) rather than
the arbitrary 365-day threshold used previously.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sqlite3
from datetime import timedelta

# Set up output directory
output_dir = Path("output/analysis_results")
output_dir.mkdir(exist_ok=True, parents=True)

# Database path
DB_PATH = "output/eylea_intervals.db"

# Natural threshold from PCA clustering (rounded to nearest 50)
NATURAL_THRESHOLD = 800  # ~794 days from PCA

def connect_to_db() -> sqlite3.Connection:
    """Connect to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def load_interval_data() -> pl.DataFrame:
    """Load the interval_va_data table into a Polars DataFrame."""
    conn = connect_to_db()
    
    # Use Polars to read from SQLite
    query = "SELECT * FROM interval_va_data"
    df = pl.read_database(query=query, connection=conn)
    
    # Convert date strings to datetime objects
    df = df.with_columns([
        pl.col("previous_date").str.to_datetime("%Y-%m-%d"),
        pl.col("current_date").str.to_datetime("%Y-%m-%d")
    ])
    
    conn.close()
    return df

def analyze_interval_distribution(interval_data: pl.DataFrame) -> None:
    """
    Analyze the distribution of intervals to identify natural breaks.
    
    Args:
        interval_data: Raw interval data
    """
    # Get all intervals
    intervals = interval_data.select("interval_days").to_numpy().flatten()
    
    # Create a histogram of intervals
    plt.figure(figsize=(12, 8))
    
    # Use log scale for x-axis to better visualize the distribution
    plt.hist(intervals, bins=100, alpha=0.7)
    plt.xscale('log')
    
    # Add vertical lines for different thresholds
    plt.axvline(x=365, color='r', linestyle='--', label='1 Year (365 days)')
    plt.axvline(x=NATURAL_THRESHOLD, color='g', linestyle='--', label=f'PCA Threshold ({NATURAL_THRESHOLD} days)')
    
    plt.title("Distribution of Injection Intervals")
    plt.xlabel("Interval (days, log scale)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "interval_distribution_with_thresholds.png")
    plt.close()
    
    # Calculate statistics for different thresholds
    intervals_365_plus = intervals[intervals > 365]
    intervals_natural_plus = intervals[intervals > NATURAL_THRESHOLD]
    
    stats = {
        "total_intervals": len(intervals),
        "intervals_over_365": len(intervals_365_plus),
        "intervals_over_natural": len(intervals_natural_plus),
        "percent_over_365": (len(intervals_365_plus) / len(intervals)) * 100,
        "percent_over_natural": (len(intervals_natural_plus) / len(intervals)) * 100,
        "natural_threshold": NATURAL_THRESHOLD
    }
    
    # Save statistics
    with open(output_dir / "interval_threshold_stats.json", "w") as f:
        import json
        json.dump(stats, f, indent=2)
    
    print(f"Total intervals: {len(intervals)}")
    print(f"Intervals > 365 days: {len(intervals_365_plus)} ({stats['percent_over_365']:.2f}%)")
    print(f"Intervals > {NATURAL_THRESHOLD} days: {len(intervals_natural_plus)} ({stats['percent_over_natural']:.2f}%)")

def visualize_va_change_by_threshold(interval_data: pl.DataFrame) -> None:
    """
    Visualize VA change for different interval thresholds.
    
    Args:
        interval_data: Raw interval data
    """
    # Find all gaps and their associated VA changes
    all_intervals = []
    all_va_changes = []
    
    # Process each patient-eye combination
    for patient_eye_id in interval_data.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ]).select("patient_eye_id").unique().to_series():
        # Get data for this patient eye
        patient_data = interval_data.with_columns([
            (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
        ]).filter(pl.col("patient_eye_id") == patient_eye_id).sort("previous_date")
        
        if len(patient_data) < 2:
            continue
        
        # Get intervals and VA changes
        for i in range(len(patient_data)):
            try:
                interval = patient_data.select("interval_days")[i, 0]
                va_before = patient_data.select("prev_va")[i, 0]
                va_after = patient_data.select("current_va")[i, 0]
                
                # Skip if any value is None
                if interval is None or va_before is None or va_after is None:
                    continue
                    
                va_change = va_after - va_before
                
                all_intervals.append(interval)
                all_va_changes.append(va_change)
            except Exception:
                continue
    
    # Convert to numpy arrays
    all_intervals = np.array(all_intervals)
    all_va_changes = np.array(all_va_changes)
    
    # Create scatter plot with both thresholds highlighted
    plt.figure(figsize=(12, 8))
    
    # Plot all points with alpha based on density
    plt.scatter(all_intervals, all_va_changes, alpha=0.1, s=10, color='blue')
    
    # Highlight points above 365 days
    mask_365 = all_intervals > 365
    plt.scatter(all_intervals[mask_365], all_va_changes[mask_365], 
                alpha=0.5, s=30, color='red', label='>365 days')
    
    # Highlight points above natural threshold
    mask_natural = all_intervals > NATURAL_THRESHOLD
    plt.scatter(all_intervals[mask_natural], all_va_changes[mask_natural], 
                alpha=0.7, s=50, color='green', label=f'>{NATURAL_THRESHOLD} days')
    
    # Add a horizontal line at y=0
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    
    # Add vertical lines for thresholds
    plt.axvline(x=365, color='r', linestyle='--')
    plt.axvline(x=NATURAL_THRESHOLD, color='g', linestyle='--')
    
    # Calculate and add trend lines
    if np.sum(mask_365) > 2:
        z_365 = np.polyfit(all_intervals[mask_365], all_va_changes[mask_365], 1)
        p_365 = np.poly1d(z_365)
        plt.plot(
            sorted(all_intervals[mask_365]), 
            p_365(sorted(all_intervals[mask_365])), 
            "r--", 
            alpha=0.7,
            label=f">365 days trend: y={z_365[0]:.4f}x{z_365[1]:+.1f}"
        )
    
    if np.sum(mask_natural) > 2:
        z_natural = np.polyfit(all_intervals[mask_natural], all_va_changes[mask_natural], 1)
        p_natural = np.poly1d(z_natural)
        plt.plot(
            sorted(all_intervals[mask_natural]), 
            p_natural(sorted(all_intervals[mask_natural])), 
            "g--", 
            alpha=0.7,
            label=f">{NATURAL_THRESHOLD} days trend: y={z_natural[0]:.4f}x{z_natural[1]:+.1f}"
        )
    
    plt.title("Visual Acuity Change by Interval Length with Different Thresholds")
    plt.xlabel("Interval (days)")
    plt.ylabel("VA Change (letters)")
    plt.xscale('log')  # Use log scale for better visualization
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_change_by_interval_thresholds.png")
    plt.close()
    
    # Calculate statistics for different thresholds
    if np.sum(mask_365) > 0:
        mean_change_365 = np.mean(all_va_changes[mask_365])
        std_change_365 = np.std(all_va_changes[mask_365])
        median_change_365 = np.median(all_va_changes[mask_365])
    else:
        mean_change_365 = std_change_365 = median_change_365 = None
        
    if np.sum(mask_natural) > 0:
        mean_change_natural = np.mean(all_va_changes[mask_natural])
        std_change_natural = np.std(all_va_changes[mask_natural])
        median_change_natural = np.median(all_va_changes[mask_natural])
    else:
        mean_change_natural = std_change_natural = median_change_natural = None
    
    # Create a bar chart comparing VA change statistics
    plt.figure(figsize=(10, 8))
    
    # Create bar chart if we have data for both thresholds
    if mean_change_365 is not None and mean_change_natural is not None:
        labels = ['>365 days', f'>{NATURAL_THRESHOLD} days']
        means = [mean_change_365, mean_change_natural]
        stds = [std_change_365, std_change_natural]
        
        plt.bar(labels, means, yerr=stds, capsize=10, alpha=0.7)
        
        # Add text labels
        for i, (mean, std) in enumerate(zip(means, stds)):
            plt.text(i, mean + (0.1 if mean >= 0 else -0.1), 
                    f"Mean: {mean:.2f}\nStd: {std:.2f}\nMedian: {median_change_365 if i == 0 else median_change_natural:.2f}", 
                    ha='center', va='center' if mean >= 0 else 'top',
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))
    
        plt.title("VA Change Statistics by Threshold")
        plt.ylabel("VA Change (letters)")
        plt.grid(True, alpha=0.3)
        plt.savefig(output_dir / "va_change_stats_by_threshold.png")
        plt.close()

def main():
    """Main function."""
    print("Loading data...")
    interval_data = load_interval_data()
    
    print("Analyzing interval distribution...")
    analyze_interval_distribution(interval_data)
    
    print("Visualizing VA change by threshold...")
    visualize_va_change_by_threshold(interval_data)
    
    print("Visualization complete.")

if __name__ == "__main__":
    main()
