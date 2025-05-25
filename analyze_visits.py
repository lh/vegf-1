"""
Analyzes the number of visits per year in our simulations.
"""

import sys
import math
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def analyze_visits_per_year(data_file):
    """
    Analyzes visits per year from the simulation results
    """
    # Read in the data
    df = pd.read_csv(data_file)
    
    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by patient_id and date
    df = df.sort_values(['patient_id', 'date'])
    
    # Group by patient_id
    patient_data = []
    for patient_id, patient_df in df.groupby('patient_id'):
        # Get the first and last date for this patient
        first_date = patient_df['date'].min()
        last_date = patient_df['date'].max()
        
        # Calculate the duration in years
        duration_days = (last_date - first_date).days
        duration_years = duration_days / 365.25  # Using average year length
        
        # Calculate visits per year
        total_visits = len(patient_df)
        visits_per_year = total_visits / max(duration_years, 0.1)  # Prevent division by zero
        
        patient_data.append({
            'patient_id': patient_id,
            'total_visits': total_visits,
            'duration_days': duration_days,
            'duration_years': duration_years,
            'visits_per_year': visits_per_year
        })
    
    # Convert to DataFrame
    result_df = pd.DataFrame(patient_data)
    
    # Calculate summary statistics
    mean_visits = result_df['visits_per_year'].mean()
    median_visits = result_df['visits_per_year'].median()
    min_visits = result_df['visits_per_year'].min()
    max_visits = result_df['visits_per_year'].max()
    std_visits = result_df['visits_per_year'].std()
    
    print(f"Analysis of '{data_file}':")
    print(f"Number of patients: {len(result_df)}")
    print(f"Average visits per year: {mean_visits:.2f}")
    print(f"Median visits per year: {median_visits:.2f}")
    print(f"Min visits per year: {min_visits:.2f}")
    print(f"Max visits per year: {max_visits:.2f}")
    print(f"Standard deviation: {std_visits:.2f}")
    
    # Calculate the distribution of visits per year
    bins = [0, 4, 8, 12, 16, 20, float('inf')]
    labels = ['0-4', '4-8', '8-12', '12-16', '16-20', '20+']
    result_df['visits_bin'] = pd.cut(result_df['visits_per_year'], bins=bins, labels=labels)
    
    # Print the distribution
    print("\nDistribution of visits per year:")
    for label, count in result_df['visits_bin'].value_counts().sort_index().items():
        percentage = 100 * count / len(result_df)
        print(f"{label} visits/year: {count} patients ({percentage:.1f}%)")
    
    return result_df

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = "treat_and_extend_abs_fixed_data.csv"
    
    if not data_file.endswith('.csv'):
        print(f"Error: Input file must be a CSV file. Got: {data_file}")
        sys.exit(1)
    
    try:
        result_df = analyze_visits_per_year(data_file)
        print("\nAnalysis complete.")
    except Exception as e:
        print(f"Error analyzing data: {e}")
        sys.exit(1)