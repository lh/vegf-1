"""
Visualize VA Change by Interval with PCA Cluster Information

This script creates an enhanced visualization of VA change by interval length,
using different marker shapes to indicate which PCA cluster each data point belongs to.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sqlite3
from matplotlib.lines import Line2D

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

def load_cluster_assignments() -> pl.DataFrame:
    """Load the cluster assignments from the PCA analysis."""
    # Load the 4-cluster assignments
    cluster_df = pl.read_csv(output_dir / "va_interval_clusters_4.csv")
    return cluster_df

def visualize_va_change_by_cluster(interval_data: pl.DataFrame, cluster_df: pl.DataFrame) -> None:
    """
    Create an enhanced visualization of VA change by interval with cluster information.
    
    Args:
        interval_data: Raw interval data
        cluster_df: DataFrame with cluster assignments
    """
    # Create a unique identifier for each patient-eye combination in both dataframes
    interval_data = interval_data.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    # Get unique patient-eye combinations from cluster_df
    cluster_df = cluster_df.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    # Create a mapping of patient_eye_id to cluster
    patient_cluster_map = {}
    for row in cluster_df.iter_rows(named=True):
        patient_cluster_map[row["patient_eye_id"]] = row["cluster"]
    
    # Find all intervals and their associated VA changes, along with cluster info
    all_intervals = []
    all_va_changes = []
    all_clusters = []
    
    # Process each patient-eye combination
    for patient_eye_id in interval_data.select("patient_eye_id").unique().to_series():
        # Get data for this patient eye
        patient_data = interval_data.filter(pl.col("patient_eye_id") == patient_eye_id).sort("previous_date")
        
        if len(patient_data) < 2:
            continue
        
        # Get cluster for this patient-eye
        cluster = patient_cluster_map.get(patient_eye_id)
        
        # Skip if no cluster assignment
        if cluster is None:
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
                all_clusters.append(cluster)
            except Exception:
                continue
    
    # Convert to numpy arrays
    all_intervals = np.array(all_intervals)
    all_va_changes = np.array(all_va_changes)
    all_clusters = np.array(all_clusters)
    
    # Create scatter plot with cluster information
    plt.figure(figsize=(14, 10))
    
    # Define marker shapes for each cluster
    markers = ['o', 's', '^', 'd']  # circle, square, triangle, diamond
    
    # Define cluster names
    cluster_names = {
        0: "Cluster 1: Moderate VA, Moderate Interval",
        1: "Cluster 2: Low VA, Moderate Interval",
        2: "Cluster 3: High VA, Short Interval",
        3: "Cluster 4: Long Gap Patients"
    }
    
    # Plot points for each cluster
    for cluster_id in range(4):
        mask = all_clusters == cluster_id
        if np.sum(mask) > 0:
            plt.scatter(
                all_intervals[mask], 
                all_va_changes[mask],
                marker=markers[cluster_id],
                alpha=0.7,
                s=50,
                label=cluster_names[cluster_id]
            )
    
    # Add a horizontal line at y=0
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    
    # Add vertical lines for thresholds
    plt.axvline(x=365, color='r', linestyle='--', label='1 Year (365 days)')
    plt.axvline(x=NATURAL_THRESHOLD, color='g', linestyle='--', label=f'PCA Threshold ({NATURAL_THRESHOLD} days)')
    
    # Calculate and add trend lines for each cluster
    for cluster_id in range(4):
        mask = all_clusters == cluster_id
        if np.sum(mask) > 2:
            z = np.polyfit(all_intervals[mask], all_va_changes[mask], 1)
            p = np.poly1d(z)
            plt.plot(
                sorted(all_intervals[mask]), 
                p(sorted(all_intervals[mask])), 
                linestyle='--', 
                alpha=0.7,
                label=f"Cluster {cluster_id+1} trend: y={z[0]:.4f}x{z[1]:+.1f}"
            )
    
    plt.title("Visual Acuity Change by Interval Length and PCA Cluster")
    plt.xlabel("Interval (days)")
    plt.ylabel("VA Change (letters)")
    plt.xscale('log')  # Use log scale for better visualization
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "va_change_by_interval_and_cluster.png", bbox_inches='tight')
    plt.close()
    
    # Create a version focusing on the long intervals
    plt.figure(figsize=(14, 10))
    
    # Filter to intervals > 180 days
    long_interval_mask = all_intervals > 180
    
    # Plot points for each cluster
    for cluster_id in range(4):
        mask = (all_clusters == cluster_id) & long_interval_mask
        if np.sum(mask) > 0:
            plt.scatter(
                all_intervals[mask], 
                all_va_changes[mask],
                marker=markers[cluster_id],
                alpha=0.7,
                s=70,
                label=cluster_names[cluster_id]
            )
    
    # Add a horizontal line at y=0
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    
    # Add vertical lines for thresholds
    plt.axvline(x=365, color='r', linestyle='--', label='1 Year (365 days)')
    plt.axvline(x=NATURAL_THRESHOLD, color='g', linestyle='--', label=f'PCA Threshold ({NATURAL_THRESHOLD} days)')
    
    # Calculate and add trend lines for each cluster (for long intervals only)
    for cluster_id in range(4):
        mask = (all_clusters == cluster_id) & long_interval_mask
        if np.sum(mask) > 2:
            z = np.polyfit(all_intervals[mask], all_va_changes[mask], 1)
            p = np.poly1d(z)
            plt.plot(
                sorted(all_intervals[mask]), 
                p(sorted(all_intervals[mask])), 
                linestyle='--', 
                alpha=0.7,
                label=f"Cluster {cluster_id+1} trend: y={z[0]:.4f}x{z[1]:+.1f}"
            )
    
    plt.title("Visual Acuity Change for Long Intervals (>180 days) by PCA Cluster")
    plt.xlabel("Interval (days)")
    plt.ylabel("VA Change (letters)")
    plt.xscale('log')  # Use log scale for better visualization
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "va_change_by_long_interval_and_cluster.png", bbox_inches='tight')
    plt.close()
    
    # Calculate statistics for each cluster
    stats = []
    for cluster_id in range(4):
        mask = all_clusters == cluster_id
        if np.sum(mask) > 0:
            # Convert numpy types to Python native types for JSON serialization
            cluster_stats = {
                "cluster_id": int(cluster_id + 1),
                "cluster_name": cluster_names[cluster_id],
                "count": int(np.sum(mask)),
                "avg_interval": float(np.mean(all_intervals[mask])),
                "avg_va_change": float(np.mean(all_va_changes[mask])),
                "std_va_change": float(np.std(all_va_changes[mask])),
                "median_va_change": float(np.median(all_va_changes[mask])),
                "intervals_over_365": int(np.sum(all_intervals[mask] > 365)),
                "intervals_over_natural": int(np.sum(all_intervals[mask] > NATURAL_THRESHOLD))
            }
            stats.append(cluster_stats)
    
    # Save statistics
    with open(output_dir / "va_change_by_cluster_stats.json", "w") as f:
        import json
        json.dump(stats, f, indent=2)
    
    # Print statistics
    for stat in stats:
        print(f"Cluster {stat['cluster_id']} ({stat['cluster_name']}):")
        print(f"  Count: {stat['count']}")
        print(f"  Average interval: {stat['avg_interval']:.1f} days")
        print(f"  Average VA change: {stat['avg_va_change']:.2f} letters")
        print(f"  Intervals > 365 days: {stat['intervals_over_365']} ({stat['intervals_over_365']/stat['count']*100:.1f}%)")
        print(f"  Intervals > {NATURAL_THRESHOLD} days: {stat['intervals_over_natural']} ({stat['intervals_over_natural']/stat['count']*100:.1f}%)")
        print()

def main():
    """Main function."""
    print("Loading data...")
    interval_data = load_interval_data()
    cluster_df = load_cluster_assignments()
    
    print("Creating enhanced visualization...")
    visualize_va_change_by_cluster(interval_data, cluster_df)
    
    print("Visualization complete.")

if __name__ == "__main__":
    main()
