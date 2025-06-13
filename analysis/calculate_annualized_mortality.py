"""
Calculate annualized mortality rate from Eylea patient data
"""

import pandas as pd
from datetime import datetime

# Load the data
data_path = '/Users/rose/Code/aided/input_data/output_file.csv'
print(f"Loading data from {data_path}...")

# Read the CSV
df = pd.read_csv(data_path, low_memory=False, parse_dates=['Injection Date', 'Date of 1st Injection'])

# Get study period
study_start = df['Date of 1st Injection'].min()
study_end = df['Injection Date'].max()
study_duration_years = (study_end - study_start).days / 365.25

print(f"\nStudy period: {study_start.strftime('%Y-%m-%d')} to {study_end.strftime('%Y-%m-%d')}")
print(f"Study duration: {study_duration_years:.1f} years")

# Get patient counts
total_patients = df['UUID'].nunique()
deceased_by_patient = df.groupby('UUID')['Deceased'].max()
total_deceased = deceased_by_patient.sum()

# Calculate rates
cumulative_mortality_rate = (total_deceased / total_patients) * 100
annualized_mortality_rate = cumulative_mortality_rate / study_duration_years

print(f"\nMortality Statistics:")
print(f"Total patients: {total_patients}")
print(f"Deceased patients: {int(total_deceased)}")
print(f"Cumulative mortality rate: {cumulative_mortality_rate:.1f}%")
print(f"Annualized mortality rate: {annualized_mortality_rate:.2f}% per year")

# Also calculate patient-years of follow-up for more accurate rate
print(f"\nNote: This is a crude annualized rate.")
print(f"A more accurate calculation would require individual patient follow-up times.")

# Let's also see first/last injection dates per patient to get a sense of follow-up
patient_followup = df.groupby('UUID').agg({
    'Date of 1st Injection': 'first',
    'Injection Date': 'max',
    'Deceased': 'max'
})

# Calculate average follow-up time
patient_followup['followup_years'] = (
    patient_followup['Injection Date'] - patient_followup['Date of 1st Injection']
).dt.days / 365.25

avg_followup = patient_followup['followup_years'].mean()
total_patient_years = patient_followup['followup_years'].sum()

# More accurate mortality rate per patient-year
deaths_per_patient_year = total_deceased / total_patient_years
deaths_per_100_patient_years = deaths_per_patient_year * 100

print(f"\nFollow-up Analysis:")
print(f"Average follow-up per patient: {avg_followup:.1f} years")
print(f"Total patient-years of follow-up: {total_patient_years:.0f}")
print(f"Mortality rate: {deaths_per_100_patient_years:.1f} deaths per 100 patient-years")