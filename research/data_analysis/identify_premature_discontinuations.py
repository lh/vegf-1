"""
Identify Premature Discontinuations

This script identifies patients who could be classified as having a premature discontinuation,
defined as:
1. Visual acuity better than 20 letters
2. Treatment interval increasing from ≤2 months (60 days) to ≥6 months (180 days)

These patients represent those who had good vision but moved from a regular treatment
schedule to a much longer interval or effective discontinuation.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sqlite3
import json

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

def identify_premature_discontinuations(interval_data: pl.DataFrame, exclude_one_year_gaps: bool = True) -> pl.DataFrame:
    """
    Identify patients meeting criteria for premature discontinuation:
    1. Visual acuity better than 20 letters
    2. Treatment interval increasing from ≤2 months (60 days) to ≥6 months (180 days)
    3. Optionally exclude gaps that occur around one year of treatment (these would be 
       classified as "course complete but not renewed" rather than true premature discontinuations)
    
    Args:
        interval_data: DataFrame with injection intervals and visual acuity
        exclude_one_year_gaps: If True, exclude gaps occurring at ~1 year (between 11-13 months)
        
    Returns:
        DataFrame with patients meeting the criteria and their data
    """
    # Create a unique identifier for each patient-eye combination
    interval_data = interval_data.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    # Get unique patient-eye combinations
    patient_eyes = interval_data.select("patient_eye_id").unique()
    
    # Track patients who meet the criteria
    premature_discontinuations = []
    
    # Iterate through each patient-eye combination
    for patient_eye_id in patient_eyes.to_series():
        # Get data for this patient eye sorted by date
        patient_data = interval_data.filter(
            pl.col("patient_eye_id") == patient_eye_id
        ).sort("previous_date")
        
        if len(patient_data) < 2:
            continue
        
        # Get first injection date for this patient to calculate days from start
        first_date = patient_data.select("previous_date").min()[0, 0]
        
        # Track whether this patient has a premature discontinuation
        has_premature_discontinuation = False
        
        # Examine every consecutive pair of injections
        for i in range(len(patient_data) - 1):
            # Get current row
            current_row = patient_data.row(i, named=True)
            next_row = patient_data.row(i + 1, named=True)
            
            # Get current VA and interval
            current_va = current_row.get("current_va")
            
            # Skip if VA is missing
            if current_va is None:
                continue
                
            # Check condition 1: VA better than 20 letters
            if current_va > 20:
                # Get current interval and next interval
                current_interval = current_row.get("interval_days")
                next_interval = next_row.get("interval_days")
                
                # Skip if intervals are missing
                if current_interval is None or next_interval is None:
                    continue
                
                # Calculate days from first injection to current point
                current_date = current_row.get("current_date")
                days_from_first = (current_date - first_date).days
                
                # If excluding one-year gaps, check if this gap occurs around 1 year
                if exclude_one_year_gaps:
                    one_year_lower = 330  # ~11 months
                    one_year_upper = 390  # ~13 months
                    
                    # Skip this gap if it occurs around 1 year from treatment start
                    if one_year_lower <= days_from_first <= one_year_upper:
                        continue
                
                # Check condition 2: Interval increases from ≤2 months to ≥6 months
                if current_interval <= 60 and next_interval >= 180:
                    # Get uuid and eye
                    uuid = current_row.get("uuid")
                    eye = current_row.get("eye")
                    
                    # Record the premature discontinuation
                    premature_discontinuations.append({
                        "uuid": uuid,
                        "eye": eye,
                        "patient_eye_id": patient_eye_id,
                        "previous_va": current_row.get("prev_va"),
                        "current_va": current_va,
                        "next_va": next_row.get("current_va"),
                        "previous_date": current_row.get("previous_date").strftime("%Y-%m-%d"),
                        "current_date": current_row.get("current_date").strftime("%Y-%m-%d"),
                        "next_date": next_row.get("current_date").strftime("%Y-%m-%d"),
                        "current_interval": current_interval,
                        "next_interval": next_interval,
                        "days_from_first_injection": days_from_first,
                        "va_change": next_row.get("current_va") - current_va if next_row.get("current_va") is not None else None
                    })
                    
                    has_premature_discontinuation = True
                    break  # Record only the first occurrence for each patient
        
    # Create DataFrame from the results
    result_df = pl.DataFrame(premature_discontinuations)
    
    return result_df

def analyze_premature_discontinuations(premature_df: pl.DataFrame, exclude_one_year: bool = True) -> None:
    """
    Analyze and visualize the identified premature discontinuations.
    
    Args:
        premature_df: DataFrame with premature discontinuation cases
        exclude_one_year: Whether one-year gaps were excluded in the data
    """
    # Set up output file prefix
    prefix = "premature_discontinuation" if exclude_one_year else "all_premature_discontinuation"
    # Count unique patients
    unique_patients = premature_df.select("uuid").n_unique()
    unique_patient_eyes = premature_df.select("patient_eye_id").n_unique()
    
    print(f"Found {len(premature_df)} premature discontinuations")
    print(f"Affecting {unique_patients} unique patients ({unique_patient_eyes} unique eyes)")
    
    # Create a summary statistics report
    summary = {
        "total_premature_discontinuations": len(premature_df),
        "unique_patients": unique_patients,
        "unique_patient_eyes": unique_patient_eyes,
        "mean_va_at_discontinuation": float(premature_df.select(pl.col("current_va").mean()).item()),
        "median_va_at_discontinuation": float(premature_df.select(pl.col("current_va").median()).item()),
        "mean_interval_before": float(premature_df.select(pl.col("current_interval").mean()).item()),
        "mean_interval_after": float(premature_df.select(pl.col("next_interval").mean()).item())
    }
    
    # Calculate mean VA change only for non-null values
    va_change_data = premature_df.filter(pl.col("va_change").is_not_null())
    if len(va_change_data) > 0:
        summary["mean_va_change"] = float(va_change_data.select(pl.col("va_change").mean()).item())
    else:
        summary["mean_va_change"] = None
    
    # Save summary to JSON
    with open(output_dir / f"{prefix}_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Create visualizations
    
    # 1. Histogram of VA at discontinuation
    plt.figure(figsize=(12, 8))
    plt.hist(premature_df.select("current_va").to_numpy(), bins=20, alpha=0.7)
    plt.axvline(x=summary["mean_va_at_discontinuation"], color='r', linestyle='--', 
                label=f'Mean VA: {summary["mean_va_at_discontinuation"]:.1f}')
    plt.axvline(x=summary["median_va_at_discontinuation"], color='g', linestyle='--', 
                label=f'Median VA: {summary["median_va_at_discontinuation"]:.1f}')
    plt.title("Visual Acuity at Premature Discontinuation")
    plt.xlabel("VA (letters)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / f"{prefix}_va_histogram.png")
    plt.close()
    
    # 2. Scatter plot of VA vs. next interval
    plt.figure(figsize=(12, 8))
    plt.scatter(
        premature_df.select("current_va").to_numpy(),
        premature_df.select("next_interval").to_numpy(),
        alpha=0.7
    )
    plt.title("VA vs. Next Interval for Premature Discontinuations")
    plt.xlabel("VA at Discontinuation (letters)")
    plt.ylabel("Next Interval (days)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / f"{prefix}_va_vs_interval.png")
    plt.close()
    
    # 3. VA Change Distribution
    va_change_data = premature_df.filter(pl.col("va_change").is_not_null())
    if len(va_change_data) > 0:
        plt.figure(figsize=(12, 8))
        plt.hist(va_change_data.select("va_change").to_numpy(), bins=20, alpha=0.7)
        plt.axvline(x=0, color='k', linestyle='--', label='No Change')
        
        if "mean_va_change" in summary and summary["mean_va_change"] is not None:
            plt.axvline(x=summary["mean_va_change"], color='r', linestyle='--', 
                      label=f'Mean Change: {summary["mean_va_change"]:.1f}')
                      
        plt.title("VA Change After Premature Discontinuation")
        plt.xlabel("VA Change (letters)")
        plt.ylabel("Frequency")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(output_dir / f"{prefix}_va_change.png")
        plt.close()
    
    # 4. Raw interval increase (scatter plot)
    plt.figure(figsize=(12, 8))
    plt.scatter(
        premature_df.select("current_interval").to_numpy(),
        premature_df.select("next_interval").to_numpy(),
        alpha=0.7
    )
    plt.title("Interval Change in Premature Discontinuations")
    plt.xlabel("Interval Before (days)")
    plt.ylabel("Interval After (days)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / f"{prefix}_interval_change.png")
    plt.close()
    
    # Return summary statistics (also print to console)
    print("\nSummary statistics:")
    for key, value in summary.items():
        print(f"{key}: {value}")

def main():
    """Main function to run analysis."""
    print("Loading interval data...")
    interval_data = load_interval_data()
    
    # First analyze all premature discontinuations
    print("\n===== ANALYSIS WITH ALL PREMATURE DISCONTINUATIONS =====")
    print("Identifying all premature discontinuations...")
    all_premature_df = identify_premature_discontinuations(interval_data, exclude_one_year_gaps=False)
    
    if len(all_premature_df) > 0:
        print("Analyzing all premature discontinuations...")
        all_premature_df.write_csv(output_dir / "all_premature_discontinuations.csv")
        analyze_premature_discontinuations(all_premature_df, exclude_one_year=False)
    else:
        print("No premature discontinuations found.")
    
    # Now analyze excluding one-year gaps
    print("\n===== ANALYSIS EXCLUDING ONE-YEAR DISCONTINUATIONS =====")
    print("Identifying premature discontinuations (excluding one-year gaps)...")
    premature_df = identify_premature_discontinuations(interval_data, exclude_one_year_gaps=True)
    
    if len(premature_df) > 0:
        print("Analyzing premature discontinuations (excluding one-year gaps)...")
        premature_df.write_csv(output_dir / "premature_discontinuations.csv")
        analyze_premature_discontinuations(premature_df, exclude_one_year=True)
    else:
        print("No premature discontinuations found after excluding one-year gaps.")
    
    print("\nAnalysis complete.")

if __name__ == "__main__":
    main()