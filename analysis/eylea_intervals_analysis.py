"""
Eylea Injection Intervals Analysis

This script analyzes the injection intervals data from the SQLite database
to identify patterns in treatment, specifically looking for two groups:
- Group LH: 7 injections in first year, then continuing with injections every ~2 months
- Group MR: 7 injections in first year, then a pause before resumption of treatment

The script also performs Principal Component Analysis (PCA) to identify patterns
in treatment intervals and visual acuity measures (previous VA, current VA, next VA).
"""

import polars as pl
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import ast  # For safely evaluating string representations of Python literals
from typing import List, Dict, Any, Optional, Tuple
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

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

def load_interval_summary() -> pl.DataFrame:
    """Load the interval_summary table into a Polars DataFrame."""
    conn = connect_to_db()
    
    # Read the raw data
    query = "SELECT * FROM interval_summary"
    df = pl.read_database(query=query, connection=conn)
    
    # Parse the intervals column from string to Python objects
    df = df.with_columns([
        pl.col("intervals").map_elements(lambda x: ast.literal_eval(x), return_dtype=pl.List(pl.Int64))
    ])
    
    # For va_data, we'll just convert it to a string representation for now
    # since we're not using it directly in the analysis
    df = df.with_columns([
        pl.col("va_data").cast(pl.Utf8)
    ])
    
    conn.close()
    return df

def analyze_first_year_injections(df: pl.DataFrame) -> pl.DataFrame:
    """
    Analyze the first year of injections for each patient.
    
    Args:
        df: DataFrame with interval_va_data
        
    Returns:
        DataFrame with first year injection analysis
    """
    # Group by uuid and calculate first year metrics
    result = []
    
    # Get unique patients
    patients = df.select("uuid").unique()
    
    for patient_row in patients.iter_rows():
        uuid = patient_row[0]
        
        # Get patient data sorted by date
        patient_data = df.filter(pl.col("uuid") == uuid).sort("previous_date")
        
        if len(patient_data) == 0:
            continue
            
        # Get first injection date
        first_date = patient_data.select("previous_date")[0, 0]
        
        # Calculate one year from first injection
        one_year_date = first_date + timedelta(days=365)
        
        # Filter to first year injections
        first_year_data = patient_data.filter(pl.col("previous_date") < one_year_date)
        
        # Count injections in first year (add 1 for the first injection)
        first_year_injections = len(first_year_data) + 1
        
        # Get last injection date in first year
        if len(first_year_data) > 0:
            last_first_year_date = first_year_data.select("current_date").max()[0, 0]
        else:
            last_first_year_date = first_date
            
        # Calculate first year duration in days
        first_year_duration = (last_first_year_date - first_date).days
        
        # Calculate average interval in first year
        if len(first_year_data) > 0:
            avg_interval = first_year_data.select("interval_days").mean()[0, 0]
        else:
            avg_interval = None
            
        # Get post-first-year data
        post_year_data = patient_data.filter(pl.col("previous_date") >= one_year_date)
        post_year_injections = len(post_year_data)
        
        # Calculate post-first-year metrics
        if post_year_injections > 0:
            # Check for pause after first year
            if len(first_year_data) > 0:
                # Get the last injection date in first year
                last_first_year_date = first_year_data.select("current_date").max()[0, 0]
                
                # Get the first injection date after first year
                first_post_year_date = post_year_data.select("previous_date").min()[0, 0]
                
                # Calculate pause duration
                pause_duration = (first_post_year_date - last_first_year_date).days
            else:
                pause_duration = None
                
            # Calculate average interval in post-first-year
            post_year_avg_interval = post_year_data.select("interval_days").mean()[0, 0]
            
            # Calculate standard deviation of intervals
            post_year_std_interval = post_year_data.select("interval_days").std()[0, 0]
            
            # Check for long gaps (>120 days) in post-first-year
            long_gaps = post_year_data.filter(pl.col("interval_days") > 120).height
        else:
            pause_duration = None
            post_year_avg_interval = None
            post_year_std_interval = None
            long_gaps = 0
            
        result.append({
            "uuid": uuid,
            "first_year_injections": first_year_injections,
            "first_year_duration": first_year_duration,
            "first_year_avg_interval": avg_interval,
            "post_year_injections": post_year_injections,
            "post_year_avg_interval": post_year_avg_interval,
            "post_year_std_interval": post_year_std_interval,
            "pause_duration": pause_duration,
            "long_gaps": long_gaps
        })
    
    return pl.DataFrame(result)

def identify_treatment_groups(df: pl.DataFrame) -> pl.DataFrame:
    """
    Identify the two treatment groups:
    - Group LH: 7 injections in first year, then continuing with injections every ~2 months
    - Group MR: 7 injections in first year, then a pause before resumption of treatment
    
    Args:
        df: DataFrame with first year injection analysis
        
    Returns:
        DataFrame with group assignments
    """
    # Filter to patients with 7 injections in first year
    seven_inj_patients = df.filter(pl.col("first_year_injections") == 7)
    
    # Filter to patients with post-first-year data
    with_post_year = seven_inj_patients.filter(pl.col("post_year_injections") > 0)
    
    # Define criteria for Group LH: 
    # - Consistent ~2 month intervals (40-80 days)
    # - No long pause after first year (<120 days)
    # - Low variability in intervals (std < 30)
    group_lh = with_post_year.filter(
        (pl.col("post_year_avg_interval").is_between(40, 80)) &
        (pl.col("pause_duration") < 120) &
        (pl.col("post_year_std_interval") < 30)
    )
    
    # Define criteria for Group MR:
    # - Pause after first year (>120 days)
    # - Resumed treatment after pause
    group_mr = with_post_year.filter(
        (pl.col("pause_duration") >= 120) &
        (pl.col("post_year_injections") > 1)
    )
    
    # Add group labels to the original dataframe
    df = df.with_columns([
        pl.lit(None).alias("treatment_group")
    ])
    
    # Update group labels
    df = df.with_columns([
        pl.when(pl.col("uuid").is_in(group_lh.select("uuid")))
        .then(pl.lit("LH"))
        .when(pl.col("uuid").is_in(group_mr.select("uuid")))
        .then(pl.lit("MR"))
        .otherwise(pl.col("treatment_group"))
        .alias("treatment_group")
    ])
    
    return df

def cluster_treatment_patterns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Use K-means clustering to identify treatment pattern groups.
    
    Args:
        df: DataFrame with first year injection analysis
        
    Returns:
        DataFrame with cluster assignments
    """
    # Filter to patients with 7 injections in first year and post-year data
    patients = df.filter(
        (pl.col("first_year_injections") == 7) &
        (pl.col("post_year_injections") > 0)
    )
    
    if len(patients) == 0:
        print("No patients with 7 injections in first year and post-year data")
        return df
    
    # Select features for clustering
    features = [
        "post_year_avg_interval",
        "pause_duration",
        "post_year_std_interval",
        "long_gaps"
    ]
    
    # Drop rows with missing values in features
    complete_data = patients.drop_nulls(features)
    
    if len(complete_data) < 10:
        print("Not enough complete data for clustering")
        return df
    
    # Extract feature matrix
    X = complete_data.select(features).to_numpy()
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply PCA for visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Apply K-means clustering with 2 clusters
    kmeans = KMeans(n_clusters=2, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Add cluster labels to the dataframe
    cluster_df = pl.DataFrame({
        "uuid": complete_data.select("uuid").to_series(),
        "cluster": clusters,
        "pca1": X_pca[:, 0],
        "pca2": X_pca[:, 1]
    })
    
    # Analyze cluster characteristics
    cluster_stats = []
    for cluster_id in range(2):
        cluster_data = complete_data.filter(
            pl.col("uuid").is_in(
                cluster_df.filter(pl.col("cluster") == cluster_id).select("uuid")
            )
        )
        
        stats = {
            "cluster_id": cluster_id,
            "count": len(cluster_data),
            "avg_pause": cluster_data.select("pause_duration").mean()[0, 0],
            "avg_interval": cluster_data.select("post_year_avg_interval").mean()[0, 0],
            "avg_std_interval": cluster_data.select("post_year_std_interval").mean()[0, 0],
            "avg_long_gaps": cluster_data.select("long_gaps").mean()[0, 0]
        }
        cluster_stats.append(stats)
    
    # Determine which cluster corresponds to which group
    cluster_stats_df = pl.DataFrame(cluster_stats)
    
    # Cluster with longer pause is MR, shorter pause is LH
    mr_cluster = cluster_stats_df.filter(pl.col("avg_pause") == cluster_stats_df.select("avg_pause").max()[0, 0]).select("cluster_id")[0, 0]
    lh_cluster = 1 - mr_cluster  # The other cluster
    
    # Map clusters to group names
    cluster_map = {
        lh_cluster: "LH (cluster)",
        mr_cluster: "MR (cluster)"
    }
    
    # Add cluster-based group to the dataframe
    df = df.join(
        cluster_df.select(["uuid", "cluster"]),
        on="uuid",
        how="left"
    )
    
    # Map cluster to group name - handle null values and type conversion
    # Create a new column with the cluster group mapping
    cluster_groups = []
    for row in df.iter_rows(named=True):
        if "cluster" not in row or row["cluster"] is None:
            cluster_groups.append(None)
        else:
            cluster_id = int(row["cluster"])
            cluster_groups.append(cluster_map.get(cluster_id, "Unknown"))
    
    # Add the cluster_group column
    df = df.with_columns([
        pl.Series("cluster_group", cluster_groups)
    ])
    
    # Save cluster visualization
    plt.figure(figsize=(10, 8))
    for cluster_id in range(2):
        mask = clusters == cluster_id
        plt.scatter(
            X_pca[mask, 0], 
            X_pca[mask, 1], 
            label=f"Cluster {cluster_map.get(cluster_id, 'Unknown')}", 
            alpha=0.7
        )
    
    plt.title("Treatment Pattern Clusters (PCA)")
    plt.xlabel("Principal Component 1")
    plt.ylabel("Principal Component 2")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "treatment_clusters_pca.png")
    plt.close()
    
    # Save cluster statistics
    with open(output_dir / "cluster_statistics.json", "w") as f:
        json.dump(cluster_stats, f, indent=2)
    
    return df

def analyze_intervals_by_group(df: pl.DataFrame, interval_data: pl.DataFrame) -> None:
    """
    Analyze and visualize injection intervals by treatment group.
    
    Args:
        df: DataFrame with group assignments
        interval_data: Raw interval data
    """
    # Join group information with interval data
    interval_with_group = interval_data.join(
        df.select(["uuid", "treatment_group", "cluster_group"]),
        on="uuid",
        how="left"
    )
    
    # Filter to patients with group assignments
    grouped_data = interval_with_group.filter(pl.col("treatment_group").is_not_null())
    
    # Plot interval distributions by group
    plt.figure(figsize=(12, 8))
    
    # Create a histogram for each group
    for group in ["LH", "MR"]:
        group_intervals = grouped_data.filter(pl.col("treatment_group") == group).select("interval_days").to_numpy().flatten()
        if len(group_intervals) > 0:
            sns.histplot(group_intervals, bins=30, alpha=0.5, label=f"Group {group}")
    
    plt.title("Distribution of Injection Intervals by Treatment Group")
    plt.xlabel("Interval (days)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "interval_distribution_by_group.png")
    plt.close()
    
    # Plot interval time series by group
    plt.figure(figsize=(14, 10))
    
    # Sample patients from each group
    for group in ["LH", "MR"]:
        group_patients = df.filter(pl.col("treatment_group") == group).select("uuid").to_series()
        
        # Sample up to 10 patients from each group
        sample_size = min(10, len(group_patients))
        if sample_size > 0:
            sample_patients = np.random.choice(group_patients, size=sample_size, replace=False)
            
            for i, patient_id in enumerate(sample_patients):
                patient_data = interval_data.filter(pl.col("uuid") == patient_id).sort("previous_date")
                
                # Calculate days from first injection
                first_date = patient_data.select("previous_date").min()[0, 0]
                
                # Create a time series of injection dates
                injection_dates = [0]  # First injection at day 0
                
                for row in patient_data.iter_rows(named=True):
                    days_from_first = (row["current_date"] - first_date).days
                    injection_dates.append(days_from_first)
                
                # Plot injection timeline
                plt.plot(
                    injection_dates, 
                    [i + (0.5 if group == "LH" else 0)] * len(injection_dates), 
                    "o-", 
                    alpha=0.7,
                    label=f"{group} Patient {i+1}" if i == 0 else ""
                )
    
    plt.title("Injection Timelines by Treatment Group")
    plt.xlabel("Days from First Injection")
    plt.yticks([])
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "injection_timelines_by_group.png")
    plt.close()
    
    # Calculate and plot average intervals by group
    plt.figure(figsize=(12, 8))
    
    for group in ["LH", "MR"]:
        group_data = grouped_data.filter(pl.col("treatment_group") == group)
        
        # Calculate overall average and std for each group
        avg_interval = group_data.select("interval_days").mean()[0, 0]
        std_interval = group_data.select("interval_days").std()[0, 0]
        
        # Create a bar chart
        plt.bar(
            group, 
            avg_interval, 
            yerr=std_interval, 
            capsize=5, 
            alpha=0.7,
            label=f"Group {group}"
        )
        
        # Add text label
        plt.text(
            0 if group == "LH" else 1, 
            avg_interval + std_interval + 5, 
            f"{avg_interval:.1f} ± {std_interval:.1f} days", 
            ha="center"
        )
    
    plt.title("Average Injection Intervals by Sequence and Group")
    plt.xlabel("Injection Number")
    plt.ylabel("Interval (days)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "avg_intervals_by_sequence_and_group.png")
    plt.close()

def prepare_va_interval_data_for_pca(interval_data: pl.DataFrame) -> pl.DataFrame:
    """
    Prepare data for PCA analysis by calculating next VA for each record.
    
    This function processes the interval data to create a dataset with:
    - treatment_interval (interval_days)
    - previous_va (prev_va)
    - current_va
    - next_va (calculated by joining with next record)
    
    Args:
        interval_data: Raw interval data from the database
        
    Returns:
        DataFrame with prepared features for PCA analysis
    """
    # Work with a copy of the data
    df = interval_data.clone()
    
    # Sort data by patient and date
    df = df.sort(["uuid", "eye", "previous_date"])
    
    # Create a unique identifier for each eye of each patient
    df = df.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    # For each patient_eye_id, we need to calculate the next VA
    # We'll do this by creating a shifted version of the dataframe
    
    # Group by patient_eye_id and create a window for shifting
    result_dfs = []
    
    for patient_eye_id in df.select("patient_eye_id").unique().to_series():
        # Get data for this patient eye
        patient_eye_data = df.filter(pl.col("patient_eye_id") == patient_eye_id)
        
        if len(patient_eye_data) <= 1:
            # Skip if there's only one record (can't calculate next VA)
            continue
            
        # Create next_va column by shifting current_va
        patient_eye_data = patient_eye_data.with_columns([
            pl.col("current_va").shift(-1).alias("next_va")
        ])
        
        # Drop the last row which will have null next_va
        patient_eye_data = patient_eye_data.filter(pl.col("next_va").is_not_null())
        
        result_dfs.append(patient_eye_data)
    
    if not result_dfs:
        print("No valid data for PCA analysis")
        return pl.DataFrame()
        
    # Combine all patient eye data
    result_df = pl.concat(result_dfs)
    
    # Select only the columns we need for PCA
    pca_data = result_df.select([
        "uuid", 
        "eye", 
        "interval_days", 
        "prev_va", 
        "current_va", 
        "next_va",
        "previous_date",
        "current_date"
    ])
    
    # Rename columns for clarity
    pca_data = pca_data.rename({
        "interval_days": "treatment_interval"
    })
    
    return pca_data

def perform_va_interval_pca(interval_data: pl.DataFrame) -> None:
    """
    Perform PCA analysis on treatment intervals and visual acuity measures.
    
    This function identifies patterns in:
    - Treatment interval
    - Previous VA
    - Current VA
    - Next VA
    
    Args:
        interval_data: Raw interval data from the database
    """
    print("Preparing data for PCA analysis...")
    pca_data = prepare_va_interval_data_for_pca(interval_data)
    
    if len(pca_data) == 0:
        print("No data available for PCA analysis")
        return
        
    print(f"Prepared {pca_data.height} records for PCA analysis")
    
    # Select features for PCA
    features = ["treatment_interval", "prev_va", "current_va", "next_va"]
    
    # Drop rows with missing values in features
    complete_data = pca_data.drop_nulls(features)
    
    if len(complete_data) < 10:
        print("Not enough complete data for PCA analysis")
        return
    
    print(f"Using {complete_data.height} complete records for PCA analysis")
    
    # Extract feature matrix
    X = complete_data.select(features).to_numpy()
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Create a DataFrame with PCA results
    pca_result = pl.DataFrame({
        "uuid": complete_data.select("uuid").to_series(),
        "eye": complete_data.select("eye").to_series(),
        "pca1": X_pca[:, 0],
        "pca2": X_pca[:, 1],
        "treatment_interval": complete_data.select("treatment_interval").to_series(),
        "prev_va": complete_data.select("prev_va").to_series(),
        "current_va": complete_data.select("current_va").to_series(),
        "next_va": complete_data.select("next_va").to_series()
    })
    
    # Save PCA results
    pca_result.write_csv(output_dir / "va_interval_pca_results.csv")
    
    # Visualize PCA results
    plt.figure(figsize=(12, 10))
    
    # Create a scatter plot of PCA results
    scatter = plt.scatter(
        X_pca[:, 0], 
        X_pca[:, 1], 
        c=complete_data.select("treatment_interval").to_numpy(), 
        cmap="viridis", 
        alpha=0.7,
        s=50
    )
    
    # Add a colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label("Treatment Interval (days)")
    
    # Add feature vectors
    feature_names = ["Treatment Interval", "Previous VA", "Current VA", "Next VA"]
    
    # Get the PCA components (loadings)
    components = pca.components_
    
    # Calculate scaling factor for arrows
    # This helps make the arrows visible on the plot
    scale_factor = 5
    
    # Plot feature vectors
    for i, (name, component) in enumerate(zip(feature_names, components.T)):
        plt.arrow(
            0, 0,  # Start at origin
            component[0] * scale_factor,  # Scale x component
            component[1] * scale_factor,  # Scale y component
            head_width=0.2,
            head_length=0.3,
            fc='red',
            ec='red'
        )
        
        # Add feature name label
        # Position the label slightly beyond the arrow
        label_scale = scale_factor * 1.1
        plt.text(
            component[0] * label_scale,
            component[1] * label_scale,
            name,
            color='red',
            ha='center',
            va='center'
        )
    
    plt.title("PCA of Treatment Intervals and Visual Acuity")
    plt.xlabel(f"Principal Component 1 ({pca.explained_variance_ratio_[0]:.2%} variance)")
    plt.ylabel(f"Principal Component 2 ({pca.explained_variance_ratio_[1]:.2%} variance)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_interval_pca.png")
    plt.close()
    
    # Create additional visualizations to explore patterns
    
    # 1. Scatter plot of treatment interval vs. VA change
    plt.figure(figsize=(12, 8))
    
    # Calculate VA change
    va_change = complete_data.select("next_va").to_numpy() - complete_data.select("current_va").to_numpy()
    
    # Create scatter plot
    scatter = plt.scatter(
        complete_data.select("treatment_interval").to_numpy(),
        va_change,
        c=complete_data.select("current_va").to_numpy(),
        cmap="coolwarm",
        alpha=0.7,
        s=50
    )
    
    # Add a colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label("Current VA (letters)")
    
    plt.title("Treatment Interval vs. VA Change")
    plt.xlabel("Treatment Interval (days)")
    plt.ylabel("VA Change (letters)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "interval_vs_va_change.png")
    plt.close()
    
    # 2. Cluster the PCA results using K-means
    # Try different numbers of clusters
    for n_clusters in [2, 3, 4]:
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_pca)
        
        # Add cluster labels to the dataframe
        cluster_df = pl.DataFrame({
            "uuid": complete_data.select("uuid").to_series(),
            "eye": complete_data.select("eye").to_series(),
            "cluster": clusters,
            "pca1": X_pca[:, 0],
            "pca2": X_pca[:, 1],
            "treatment_interval": complete_data.select("treatment_interval").to_series(),
            "prev_va": complete_data.select("prev_va").to_series(),
            "current_va": complete_data.select("current_va").to_series(),
            "next_va": complete_data.select("next_va").to_series()
        })
        
        # Save cluster results
        cluster_df.write_csv(output_dir / f"va_interval_clusters_{n_clusters}.csv")
        
        # Visualize clusters
        plt.figure(figsize=(12, 10))
        
        # Create a scatter plot of clusters
        for cluster_id in range(n_clusters):
            mask = clusters == cluster_id
            plt.scatter(
                X_pca[mask, 0], 
                X_pca[mask, 1], 
                label=f"Cluster {cluster_id+1}", 
                alpha=0.7,
                s=50
            )
        
        # Add cluster centroids
        plt.scatter(
            kmeans.cluster_centers_[:, 0],
            kmeans.cluster_centers_[:, 1],
            marker='X',
            s=200,
            c='black',
            label='Centroids'
        )
        
        plt.title(f"PCA with {n_clusters} Clusters")
        plt.xlabel(f"Principal Component 1 ({pca.explained_variance_ratio_[0]:.2%} variance)")
        plt.ylabel(f"Principal Component 2 ({pca.explained_variance_ratio_[1]:.2%} variance)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(output_dir / f"va_interval_clusters_{n_clusters}.png")
        plt.close()
        
        # Analyze cluster characteristics
        cluster_stats = []
        for cluster_id in range(n_clusters):
            cluster_data = complete_data.filter(
                pl.Series(clusters) == cluster_id
            )
            
            stats = {
                "cluster_id": cluster_id + 1,
                "count": len(cluster_data),
                "avg_interval": cluster_data.select("treatment_interval").mean()[0, 0],
                "avg_prev_va": cluster_data.select("prev_va").mean()[0, 0],
                "avg_current_va": cluster_data.select("current_va").mean()[0, 0],
                "avg_next_va": cluster_data.select("next_va").mean()[0, 0],
                "avg_va_change": (cluster_data.select("next_va").mean()[0, 0] - 
                                 cluster_data.select("current_va").mean()[0, 0])
            }
            cluster_stats.append(stats)
        
        # Save cluster statistics
        with open(output_dir / f"va_interval_cluster_stats_{n_clusters}.json", "w") as f:
            json.dump(cluster_stats, f, indent=2)
    
    print(f"PCA analysis complete. Results saved to {output_dir}")

def analyze_va_by_group(df: pl.DataFrame, interval_data: pl.DataFrame) -> None:
    """
    Analyze and visualize visual acuity by treatment group.
    
    Args:
        df: DataFrame with group assignments
        interval_data: Raw interval data
    """
    # Join group information with interval data
    va_with_group = interval_data.join(
        df.select(["uuid", "treatment_group"]),
        on="uuid",
        how="left"
    )
    
    # Filter to patients with group assignments
    grouped_data = va_with_group.filter(pl.col("treatment_group").is_not_null())
    
    # Plot VA trajectories by group
    plt.figure(figsize=(12, 8))
    
    # Sample patients from each group
    for group in ["LH", "MR"]:
        group_patients = df.filter(pl.col("treatment_group") == group).select("uuid").to_series()
        
        # Sample up to 10 patients from each group
        sample_size = min(10, len(group_patients))
        if sample_size > 0:
            sample_patients = np.random.choice(group_patients, size=sample_size, replace=False)
            
            for patient_id in sample_patients:
                patient_data = interval_data.filter(pl.col("uuid") == patient_id).sort("previous_date")
                
                # Calculate days from first injection
                first_date = patient_data.select("previous_date").min()[0, 0]
                
                # Create a time series of VA measurements
                days_from_first = [0]  # First injection at day 0
                va_values = [patient_data.select("prev_va").min()[0, 0]]  # First VA
                
                for row in patient_data.iter_rows(named=True):
                    days_from_first.append((row["current_date"] - first_date).days)
                    va_values.append(row["current_va"])
                
                # Plot VA trajectory
                plt.plot(days_from_first, va_values, "o-", alpha=0.3)
    
    # Add group averages
    for group in ["LH", "MR"]:
        group_data = grouped_data.filter(pl.col("treatment_group") == group)
        
        # Group by days from first injection (binned) and calculate average VA
        max_days = 1000  # Limit to first 1000 days for clarity
        bin_size = 60  # 60-day bins
        
        avg_va = []
        days_bins = []
        
        for bin_start in range(0, max_days, bin_size):
            bin_end = bin_start + bin_size
            
            # For each bin, we need to work with a fresh copy of the data
            bin_group_data = group_data.clone()
            
            # Get the first injection date for each patient
            first_dates = bin_group_data.group_by("uuid").agg([
                pl.col("previous_date").min().alias("first_date")
            ])
            
            # Join with the group data
            bin_group_data_with_first = bin_group_data.join(
                first_dates,
                on="uuid",
                how="left"
            )
            
            # Calculate days from first injection
            bin_group_data_with_days = bin_group_data_with_first.with_columns([
                ((pl.col("current_date") - pl.col("first_date")).dt.total_days()).alias("days_from_first")
            ])
            
            bin_data = bin_group_data_with_days.filter(
                (pl.col("days_from_first") >= bin_start) & 
                (pl.col("days_from_first") < bin_end)
            )
            
            if len(bin_data) > 10:  # Only include if we have enough data points
                avg_va_value = bin_data.select("current_va").mean()[0, 0]
                avg_va.append(avg_va_value)
                days_bins.append(bin_start + bin_size/2)  # Use bin midpoint
        
        if len(days_bins) > 0:
            plt.plot(days_bins, avg_va, "o-", linewidth=3, label=f"Group {group} Average")
    
    plt.title("Visual Acuity Trajectories by Treatment Group")
    plt.xlabel("Days from First Injection")
    plt.ylabel("Visual Acuity (letters)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_trajectories_by_group.png")
    plt.close()
    
    # Plot VA change from baseline by group
    plt.figure(figsize=(12, 8))
    
    for group in ["LH", "MR"]:
        group_data = grouped_data.filter(pl.col("treatment_group") == group)
        
        # Calculate baseline VA for each patient (first VA measurement)
        baseline_va = group_data.group_by("uuid").agg([
            pl.col("prev_va").first().alias("baseline_va")
        ])
        
        # Join baseline VA with group data
        group_data_with_baseline = group_data.join(
            baseline_va,
            on="uuid",
            how="left"
        )
        
        # Calculate VA change from baseline
        group_data_with_baseline = group_data_with_baseline.with_columns([
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
            bin_baseline_data = group_data_with_baseline.clone()
            
            # Get the first injection date for each patient
            baseline_first_dates = bin_baseline_data.group_by("uuid").agg([
                pl.col("previous_date").min().alias("baseline_first_date")
            ])
            
            # Join with the group data
            bin_baseline_data_with_first = bin_baseline_data.join(
                baseline_first_dates,
                on="uuid",
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
                label=f"Group {group}"
            )
    
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    plt.title("Visual Acuity Change from Baseline by Treatment Group")
    plt.xlabel("Days from First Injection")
    plt.ylabel("VA Change from Baseline (letters)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / "va_change_by_group.png")
    plt.close()

def main():
    """Main analysis function."""
    print("Loading data from SQLite database...")
    interval_data = load_interval_data()
    interval_summary = load_interval_summary()
    
    print(f"Loaded {interval_data.height} interval records for {interval_data.select('uuid').unique().height} patients")
    
    print("Analyzing first year injection patterns...")
    first_year_analysis = analyze_first_year_injections(interval_data)
    
    # Save first year analysis
    first_year_analysis.write_csv(output_dir / "first_year_analysis.csv")
    
    # Count patients with 7 injections in first year
    seven_inj_count = first_year_analysis.filter(pl.col("first_year_injections") == 7).height
    print(f"Found {seven_inj_count} patients with 7 injections in first year")
    
    print("Identifying treatment groups...")
    grouped_data = identify_treatment_groups(first_year_analysis)
    
    # Count patients in each group
    lh_count = grouped_data.filter(pl.col("treatment_group") == "LH").height
    mr_count = grouped_data.filter(pl.col("treatment_group") == "MR").height
    print(f"Group LH: {lh_count} patients")
    print(f"Group MR: {mr_count} patients")
    
    print("Clustering treatment patterns...")
    clustered_data = cluster_treatment_patterns(grouped_data)
    
    # Save grouped data
    clustered_data.write_csv(output_dir / "treatment_groups.csv")
    
    print("Analyzing intervals by group...")
    analyze_intervals_by_group(clustered_data, interval_data)
    
    print("Analyzing visual acuity by group...")
    analyze_va_by_group(clustered_data, interval_data)
    
    print("Performing PCA analysis on treatment intervals and visual acuity...")
    perform_va_interval_pca(interval_data)
    
    print(f"Analysis complete. Results saved to {output_dir}")
    
    # Generate summary report
    total_patients = interval_data.select("uuid").unique().height
    with_7_injections = seven_inj_count
    lh_patients = lh_count
    mr_patients = mr_count
    other_patients = total_patients - lh_patients - mr_patients
    
    summary = {
        "total_patients": total_patients,
        "patients_with_7_injections_first_year": with_7_injections,
        "group_lh_patients": lh_patients,
        "group_mr_patients": mr_patients,
        "other_patients": other_patients,
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(output_dir / "analysis_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Create a summary plot
    plt.figure(figsize=(10, 6))
    groups = ["Group LH", "Group MR", "Other"]
    counts = [lh_patients, mr_patients, other_patients]
    
    plt.bar(groups, counts)
    plt.title("Patient Distribution by Treatment Pattern")
    plt.ylabel("Number of Patients")
    plt.grid(True, alpha=0.3)
    
    # Add count labels on bars
    for i, count in enumerate(counts):
        plt.text(i, count + 5, str(count), ha="center")
    
    # Add percentage labels
    total = sum(counts)
    for i, count in enumerate(counts):
        percentage = (count / total) * 100
        plt.text(i, count / 2, f"{percentage:.1f}%", ha="center", color="white", fontweight="bold")
    
    plt.savefig(output_dir / "patient_distribution.png")
    plt.close()

if __name__ == "__main__":
    main()
