"""
Calculate overall mortality rate from Eylea patient data
"""

import pandas as pd
import sys

# Load the data
data_path = '/Users/rose/Code/aided/input_data/output_file.csv'
print(f"Loading data from {data_path}...")

# Read the CSV with low_memory=False to avoid dtype warnings
df = pd.read_csv(data_path, low_memory=False)

# Get unique patients
total_patients = df['UUID'].nunique()
print(f"Total unique patients: {total_patients}")

# Count deceased patients (max per patient since it's repeated across rows)
deceased_by_patient = df.groupby('UUID')['Deceased'].max()
total_deceased = deceased_by_patient.sum()

# Calculate overall mortality rate
mortality_rate = (total_deceased / total_patients) * 100

print(f"\nOverall Mortality Statistics:")
print(f"Total patients: {total_patients}")
print(f"Deceased patients: {int(total_deceased)}")
print(f"Overall mortality rate: {mortality_rate:.1f}%")

# Also show average age at death if available
if 'Age at Death' in df.columns:
    deceased_data = df[df['Deceased'] == 1]
    if not deceased_data.empty:
        # Get unique age at death per patient (in case of multiple records)
        age_at_death_by_patient = deceased_data.groupby('UUID')['Age at Death'].first()
        avg_age_at_death = age_at_death_by_patient.mean()
        print(f"Average age at death: {avg_age_at_death:.1f} years")
        
        # Also show age distribution
        print(f"Age at death range: {age_at_death_by_patient.min():.0f} - {age_at_death_by_patient.max():.0f} years")