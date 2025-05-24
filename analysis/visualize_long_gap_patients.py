"""
Visualize Long Gap Patients (Cluster 4)

This script creates visualizations specifically focused on the long-gap patients
(Cluster 4) identified in the PCA analysis, to better illustrate what happens
to visual acuity before, during, and after the long treatment gaps.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sqlite3
from datetime import timedelta

# Import the central color system
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback if the central color system is not available
    COLORS = {
        'primary': '#4682B4',    # Steel Blue - for visual acuity data
        'secondary': '#B22222',  # Firebrick - for critical information
        'patient_counts': '#8FAD91',  # Muted Sage Green - for patient counts
    }
    ALPHAS = {
        'high': 0.8,        # High opacity for primary elements
        'medium': 0.5,      # Medium opacity for standard elements
        'low': 0.2,         # Low opacity for background elements
        'very_low': 0.1,    # Very low opacity for subtle elements
        'patient_counts': 0.5  # Consistent opacity for all patient/sample count visualizations
    }
    SEMANTIC_COLORS = {
        'acuity_data': COLORS['primary'],
        'patient_counts': COLORS['patient_counts'],
        'critical_info': COLORS['secondary'],
    }

# Set up output directory
output_dir = Path("output/analysis_results")
output_dir.mkdir(exist_ok=True, parents=True)

# Database path
DB_PATH = "output/eylea_intervals.db"

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

def load_cluster_assignments() -> pl.DataFrame:
    """Load the cluster assignments from the PCA analysis."""
    # Load the 4-cluster assignments
    cluster_df = pl.read_csv(output_dir / "va_interval_clusters_4.csv")
    return cluster_df

def get_long_gap_patients(interval_data: pl.DataFrame, cluster_df: pl.DataFrame) -> pl.DataFrame:
    """
    Identify and prepare data for long-gap patients (Cluster 4).
    
    Args:
        interval_data: Raw interval data
        cluster_df: DataFrame with cluster assignments
        
    Returns:
        DataFrame with long-gap patient data
    """
    # Create a unique identifier for each patient-eye combination in both dataframes
    interval_data = interval_data.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    # Get unique patient-eye combinations from cluster_df
    cluster_df = cluster_df.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    # Filter to Cluster 4 (long-gap patients)
    long_gap_cluster_df = cluster_df.filter(pl.col("cluster") == 3)
    
    # Get the list of patient_eye_ids in Cluster 4
    long_gap_patient_ids = long_gap_cluster_df.select("patient_eye_id").to_series().to_list()
    
    # Filter interval_data to only include long-gap patients
    long_gap_data = interval_data.filter(pl.col("patient_eye_id").is_in(long_gap_patient_ids))
    
    return long_gap_data

def visualize_long_gap_patients(long_gap_data: pl.DataFrame) -> None:
    """
    Create visualizations focused on long-gap patients.
    
    Args:
        long_gap_data: DataFrame with long-gap patient data
    """
    # Get unique patient-eye combinations
    patient_eyes = long_gap_data.select("patient_eye_id").unique()
    
    # Count the number of unique patients
    num_patients = len(patient_eyes)
    print(f"Number of unique long-gap patients: {num_patients}")
    
    # 1. Visualize individual patient trajectories
    plt.figure(figsize=(14, 10))
    
    # Sample up to 20 patients to visualize
    sample_size = min(20, num_patients)
    if sample_size > 0:
        # Convert to numpy array for sampling
        patient_eyes_array = patient_eyes.to_numpy()
        
        # Get random sample of patient_eye_ids
        sample_indices = np.random.choice(len(patient_eyes_array), size=sample_size, replace=False)
        sample_patients = [patient_eyes_array[i][0] for i in sample_indices]
        
        for i, patient_eye_id in enumerate(sample_patients):
            # Get data for this patient eye
            patient_data = long_gap_data.filter(pl.col("patient_eye_id") == patient_eye_id).sort("previous_date")
            
            if len(patient_data) == 0:
                continue
            
            # Calculate days from first injection
            first_date = patient_data.select("previous_date").min()[0, 0]
            
            # Create a time series of VA measurements and intervals
            days_from_first = [0]  # First injection at day 0
            va_values = [patient_data.select("prev_va").min()[0, 0]]  # First VA
            intervals = []
            
            for row in patient_data.iter_rows(named=True):
                days_from_first.append((row["current_date"] - first_date).days)
                va_values.append(row["current_va"])
                intervals.append(row["interval_days"])
            
            # Find the longest interval (gap)
            if intervals:
                max_interval_idx = np.argmax(intervals)
                max_interval = intervals[max_interval_idx]
                
                # Get VA before and after the gap
                va_before_gap = va_values[max_interval_idx]
                va_after_gap = va_values[max_interval_idx + 1]
                va_change = va_after_gap - va_before_gap
                
                # Plot VA trajectory
                plt.plot(days_from_first, va_values, "o-", alpha=0.7, label=f"Patient {i+1}" if i == 0 else "")
                
                # Highlight the gap
                gap_start_day = days_from_first[max_interval_idx]
                gap_end_day = days_from_first[max_interval_idx + 1]
                
                # Add annotation for the gap
                plt.annotate(
                    f"{max_interval} days\nVA change: {va_change:.1f}",
                    xy=((gap_start_day + gap_end_day) / 2, (va_before_gap + va_after_gap) / 2),
                    xytext=(0, 30),
                    textcoords="offset points",
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"),
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3),
                    ha="center"
                )
    
    plt.title("Visual Acuity Trajectories for Long-Gap Patients (Cluster 4)")
    plt.xlabel("Days from First Injection")
    plt.ylabel("Visual Acuity (letters)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "long_gap_patient_trajectories.png")
    plt.close()
    
    # 2. Analyze and visualize VA change during long gaps
    plt.figure(figsize=(10, 8))
    
    # Find all gaps > 365 days
    long_gaps = []
    va_before_gaps = []
    va_after_gaps = []
    va_changes = []
    
    for patient_eye_id in long_gap_data.select("patient_eye_id").unique().to_series():
        # Get data for this patient eye
        patient_data = long_gap_data.filter(pl.col("patient_eye_id") == patient_eye_id).sort("previous_date")
        
        if len(patient_data) < 2:
            continue
        
        # Get intervals and find long gaps
        intervals = patient_data.select("interval_days").to_numpy().flatten()
        
        for i, interval in enumerate(intervals):
            if interval > 365:  # More than 1 year
                # Get VA before and after the gap
                try:
                    va_before = patient_data.select("prev_va")[i, 0]
                    va_after = patient_data.select("current_va")[i, 0]
                    
                    # Skip if either value is None
                    if va_before is None or va_after is None:
                        continue
                        
                    va_change = va_after - va_before
                    
                    long_gaps.append(interval)
                    va_before_gaps.append(va_before)
                    va_after_gaps.append(va_after)
                    va_changes.append(va_change)
                except Exception as e:
                    print(f"Error processing interval {i}: {e}")
                    continue
    
    # Create a scatter plot of gap duration vs. VA change
    plt.scatter(long_gaps, va_changes, alpha=0.7, s=50)
    
    # Add a horizontal line at y=0
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    
    # Add a trend line
    if long_gaps:
        z = np.polyfit(long_gaps, va_changes, 1)
        p = np.poly1d(z)
        plt.plot(
            sorted(long_gaps), 
            p(sorted(long_gaps)), 
            "r--", 
            alpha=0.7,
            label=f"Trend: y={z[0]:.4f}x{z[1]:+.1f}"
        )
    
    plt.title("Visual Acuity Change During Long Gaps (>365 days)")
    plt.xlabel("Gap Duration (days)")
    plt.ylabel("VA Change (letters)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_change_during_long_gaps.png")
    plt.close()
    
    # 3. Create a before/after comparison for long gaps
    plt.figure(figsize=(10, 8))
    
    # Create paired data for before/after comparison
    if va_before_gaps and va_after_gaps:
        # Calculate statistics
        mean_before = np.mean(va_before_gaps)
        mean_after = np.mean(va_after_gaps)
        std_before = np.std(va_before_gaps)
        std_after = np.std(va_after_gaps)
        mean_change = np.mean(va_changes)
        
        # Create bar chart with sage green to match our semantic color system
        plt.bar(
            ["Before Gap", "After Gap"],
            [mean_before, mean_after],
            yerr=[std_before, std_after],
            capsize=10,
            width=0.5,
            color=SEMANTIC_COLORS['patient_counts'],  # Use central color definition
            alpha=ALPHAS['patient_counts']  # Use standardized alpha specifically for patient counts
        )
        
        # Add text labels
        plt.text(0, mean_before + 2, f"{mean_before:.1f} ± {std_before:.1f}", ha="center")
        plt.text(1, mean_after + 2, f"{mean_after:.1f} ± {std_after:.1f}", ha="center")
        
        # Add arrow showing change
        plt.annotate(
            f"Change: {mean_change:+.1f}",
            xy=(1, mean_after),
            xytext=(0, mean_before),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"),
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3),
            ha="center",
            va="center"
        )
    
    plt.title("Visual Acuity Before and After Long Gaps (>365 days)")
    plt.ylabel("Visual Acuity (letters)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_before_after_long_gaps.png")
    plt.close()

def main():
    """Main function."""
    print("Loading data...")
    interval_data = load_interval_data()
    cluster_df = load_cluster_assignments()
    
    print("Identifying long-gap patients (Cluster 4)...")
    long_gap_data = get_long_gap_patients(interval_data, cluster_df)
    
    print("Creating visualizations for long-gap patients...")
    visualize_long_gap_patients(long_gap_data)
    
    print("Visualization complete.")

if __name__ == "__main__":
    main()
