"""
Visualize Visual Acuity Trajectories by PCA Cluster

This script creates visualizations of visual acuity trajectories over time
for patients in each of the 4 clusters identified by PCA analysis.
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

def visualize_va_trajectories_by_cluster(interval_data: pl.DataFrame, cluster_df: pl.DataFrame) -> None:
    """
    Visualize visual acuity trajectories by PCA cluster.
    
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
    
    # Add cluster information to interval_data
    clusters = []
    for row in interval_data.iter_rows(named=True):
        patient_eye_id = row["patient_eye_id"]
        clusters.append(patient_cluster_map.get(patient_eye_id, None))
    
    interval_data = interval_data.with_columns([
        pl.Series("cluster", clusters)
    ])
    
    # Filter to records with cluster assignments
    clustered_data = interval_data.filter(pl.col("cluster").is_not_null())
    
    # Convert cluster to integer
    clustered_data = clustered_data.with_columns([
        pl.col("cluster").cast(pl.Int64)
    ])
    
    # Plot VA trajectories by cluster
    plt.figure(figsize=(14, 10))
    
    # Define cluster names
    cluster_names = {
        0: "Cluster 1: Moderate VA, Moderate Interval",
        1: "Cluster 2: Low VA, Moderate Interval",
        2: "Cluster 3: High VA, Short Interval",
        3: "Cluster 4: Long Gap Patients"
    }
    
    # Sample patients from each cluster
    for cluster_id in range(4):
        # Get patients in this cluster
        cluster_patients = clustered_data.filter(pl.col("cluster") == cluster_id).select("uuid", "eye").unique()
        
        # Sample up to 10 patients from each cluster
        sample_size = min(10, len(cluster_patients))
        if sample_size > 0:
            # Convert to numpy array for sampling
            cluster_patients_array = cluster_patients.to_numpy()
            
            # Get random sample of patient_eye_ids
            sample_indices = np.random.choice(len(cluster_patients_array), size=sample_size, replace=False)
            sample_patients = [
                (cluster_patients_array[i][0], cluster_patients_array[i][1]) 
                for i in sample_indices
            ]
            
            for i, (uuid, eye) in enumerate(sample_patients):
                # Get data for this patient eye
                patient_data = clustered_data.filter(
                    (pl.col("uuid") == uuid) & (pl.col("eye") == eye)
                ).sort("previous_date")
                
                if len(patient_data) == 0:
                    continue
                
                # Calculate days from first injection
                first_date = patient_data.select("previous_date").min()[0, 0]
                
                # Create a time series of VA measurements
                days_from_first = [0]  # First injection at day 0
                va_values = [patient_data.select("prev_va").min()[0, 0]]  # First VA
                
                for row in patient_data.iter_rows(named=True):
                    days_from_first.append((row["current_date"] - first_date).days)
                    va_values.append(row["current_va"])
                
                # Plot VA trajectory with low alpha
                plt.plot(
                    days_from_first, 
                    va_values, 
                    "o-", 
                    alpha=0.3, 
                    color=f"C{cluster_id}"
                )
    
    # Add cluster averages
    for cluster_id in range(4):
        # Get data for this cluster
        cluster_data = clustered_data.filter(pl.col("cluster") == cluster_id)
        
        # Group by days from first injection (binned) and calculate average VA
        max_days = 1000  # Limit to first 1000 days for clarity
        bin_size = 60  # 60-day bins
        
        avg_va = []
        days_bins = []
        
        for bin_start in range(0, max_days, bin_size):
            bin_end = bin_start + bin_size
            
            # For each bin, we need to work with a fresh copy of the data
            bin_cluster_data = cluster_data.clone()
            
            # Get the first injection date for each patient
            first_dates = bin_cluster_data.group_by(["uuid", "eye"]).agg([
                pl.col("previous_date").min().alias("first_date")
            ])
            
            # Join with the cluster data
            bin_cluster_data_with_first = bin_cluster_data.join(
                first_dates,
                on=["uuid", "eye"],
                how="left"
            )
            
            # Calculate days from first injection
            bin_cluster_data_with_days = bin_cluster_data_with_first.with_columns([
                ((pl.col("current_date") - pl.col("first_date")).dt.total_days()).alias("days_from_first")
            ])
            
            bin_data = bin_cluster_data_with_days.filter(
                (pl.col("days_from_first") >= bin_start) & 
                (pl.col("days_from_first") < bin_end)
            )
            
            if len(bin_data) > 10:  # Only include if we have enough data points
                avg_va_value = bin_data.select("current_va").mean()[0, 0]
                avg_va.append(avg_va_value)
                days_bins.append(bin_start + bin_size/2)  # Use bin midpoint
        
        if len(days_bins) > 0:
            plt.plot(
                days_bins, 
                avg_va, 
                "o-", 
                linewidth=3, 
                color=f"C{cluster_id}", 
                label=cluster_names[cluster_id]
            )
    
    plt.title("Visual Acuity Trajectories by PCA Cluster")
    plt.xlabel("Days from First Injection")
    plt.ylabel("Visual Acuity (letters)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_trajectories_by_pca_cluster.png")
    plt.close()
    
    # Plot VA change from baseline by cluster
    plt.figure(figsize=(14, 10))
    
    for cluster_id in range(4):
        # Get data for this cluster
        cluster_data = clustered_data.filter(pl.col("cluster") == cluster_id)
        
        # Calculate baseline VA for each patient (first VA measurement)
        baseline_va = cluster_data.group_by(["uuid", "eye"]).agg([
            pl.col("prev_va").first().alias("baseline_va")
        ])
        
        # Join baseline VA with cluster data
        cluster_data_with_baseline = cluster_data.join(
            baseline_va,
            on=["uuid", "eye"],
            how="left"
        )
        
        # Calculate VA change from baseline
        cluster_data_with_baseline = cluster_data_with_baseline.with_columns([
            (pl.col("current_va") - pl.col("baseline_va")).alias("va_change")
        ])
        
        # Group by days from first injection (binned) and calculate average VA change
        max_days = 1000  # Limit to first 1000 days for clarity
        bin_size = 60  # 60-day bins
        
        avg_va_change = []
        std_va_change = []
        days_bins = []
        
        for bin_start in range(0, max_days, bin_size):
            bin_end = bin_start + bin_size
            
            # Calculate days from first injection for each patient
            # For each bin, we need to work with a fresh copy of the data
            bin_baseline_data = cluster_data_with_baseline.clone()
            
            # Get the first injection date for each patient
            baseline_first_dates = bin_baseline_data.group_by(["uuid", "eye"]).agg([
                pl.col("previous_date").min().alias("baseline_first_date")
            ])
            
            # Join with the cluster data
            bin_baseline_data_with_first = bin_baseline_data.join(
                baseline_first_dates,
                on=["uuid", "eye"],
                how="left"
            )
            
            # Calculate days from first injection
            bin_baseline_data_with_days = bin_baseline_data_with_first.with_columns([
                ((pl.col("current_date") - pl.col("baseline_first_date")).dt.total_days()).alias("days_from_first")
            ])
            
            # Use the new DataFrame for filtering
            bin_data = bin_baseline_data_with_days.filter(
                (pl.col("days_from_first") >= bin_start) & 
                (pl.col("days_from_first") < bin_end)
            )
            
            if len(bin_data) > 10:  # Only include if we have enough data points
                avg_change = bin_data.select("va_change").mean()[0, 0]
                std_change = bin_data.select("va_change").std()[0, 0]
                
                avg_va_change.append(avg_change)
                std_va_change.append(std_change)
                days_bins.append(bin_start + bin_size/2)  # Use bin midpoint
        
        if len(days_bins) > 0:
            plt.errorbar(
                days_bins, 
                avg_va_change, 
                yerr=std_va_change, 
                fmt="o-", 
                capsize=5, 
                color=f"C{cluster_id}",
                label=cluster_names[cluster_id]
            )
    
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    plt.title("Visual Acuity Change from Baseline by PCA Cluster")
    plt.xlabel("Days from First Injection")
    plt.ylabel("VA Change from Baseline (letters)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_change_by_pca_cluster.png")
    plt.close()

def main():
    """Main function."""
    print("Loading data...")
    interval_data = load_interval_data()
    cluster_df = load_cluster_assignments()
    
    print("Visualizing VA trajectories by PCA cluster...")
    visualize_va_trajectories_by_cluster(interval_data, cluster_df)
    
    print("Visualization complete.")

if __name__ == "__main__":
    main()
