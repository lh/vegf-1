"""
Extract patients with baseline VA > 70 letters and analyze their details
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# Connect to database
db_path = Path('output/eylea_intervals.db')
conn = sqlite3.connect(db_path)

# Query for the very first measurement for each patient/eye
query = """
WITH RankedMeasurements AS (
    SELECT 
        uuid, 
        eye,
        current_va,
        current_date,
        ROW_NUMBER() OVER (PARTITION BY uuid, eye ORDER BY current_date ASC) as row_num
    FROM interval_va_data 
    WHERE current_va > 70
    GROUP BY uuid, eye
)
SELECT 
    uuid, 
    eye, 
    current_va,
    current_date
FROM RankedMeasurements
WHERE row_num = 1
ORDER BY current_va DESC
"""

# Load data
above_threshold_df = pd.read_sql_query(query, conn)

# Get the next visit for these patients to see if VA changed
patient_list = []
for _, row in above_threshold_df.iterrows():
    # Get the second visit for this patient/eye
    follow_up_query = f"""
    SELECT 
        uuid, 
        eye, 
        current_va,
        current_date
    FROM interval_va_data
    WHERE uuid = '{row['uuid']}' AND eye = '{row['eye']}'
    ORDER BY current_date ASC
    LIMIT 1, 1
    """
    
    follow_up = pd.read_sql_query(follow_up_query, conn)
    
    if not follow_up.empty and pd.notnull(follow_up.iloc[0]['current_va']):
        patient_data = {
            'uuid': row['uuid'],
            'eye': row['eye'],
            'baseline_va': row['current_va'],
            'baseline_date': row['current_date'],
            'second_va': follow_up.iloc[0]['current_va'],
            'second_date': follow_up.iloc[0]['current_date'],
            'va_change': follow_up.iloc[0]['current_va'] - row['current_va']
        }
    else:
        patient_data = {
            'uuid': row['uuid'],
            'eye': row['eye'],
            'baseline_va': row['current_va'],
            'baseline_date': row['current_date'],
            'second_va': None,
            'second_date': None,
            'va_change': None
        }
    
    patient_list.append(patient_data)

# Create dataframe with patient data
detailed_df = pd.DataFrame(patient_list)

conn.close()

# Save to CSV
output_file = Path('output/patients_above_threshold.csv')
detailed_df.to_csv(output_file, index=False)

# Print summary statistics
print(f"Total patients with baseline VA > 70 letters: {len(detailed_df)}")
if len(detailed_df) > 0:
    print(f"VA range: {detailed_df['baseline_va'].min():.1f} to {detailed_df['baseline_va'].max():.1f} letters")

    # Analyze VA distribution in these patients
    va_ranges = [(70, 75), (76, 80), (81, 85), (86, 90), (91, 100)]
    print("\nDistribution of baseline VA in these patients:")
    for low, high in va_ranges:
        count = ((detailed_df['baseline_va'] >= low) & (detailed_df['baseline_va'] <= high)).sum()
        percent = (count / len(detailed_df)) * 100
        print(f"{low}-{high} letters: {count} patients ({percent:.1f}%)")

    # Analyze VA change in the second visit
    with_second_visit = detailed_df.dropna(subset=['second_va'])
    print(f"\nPatients with a recorded second visit: {len(with_second_visit)}")

    if len(with_second_visit) > 0:
        mean_change = with_second_visit['va_change'].mean()
        print(f"Mean VA change at second visit: {mean_change:.2f} letters")
        
        # Direction of change
        improved = (with_second_visit['va_change'] > 0).sum()
        stable = (with_second_visit['va_change'] == 0).sum()
        declined = (with_second_visit['va_change'] < 0).sum()
        
        print(f"VA improved: {improved} patients ({improved/len(with_second_visit)*100:.1f}%)")
        print(f"VA stable: {stable} patients ({stable/len(with_second_visit)*100:.1f}%)")
        print(f"VA declined: {declined} patients ({declined/len(with_second_visit)*100:.1f}%)")
        
        # Significant decline (which might explain treatment decision)
        significant_decline = (with_second_visit['va_change'] <= -5).sum()
        print(f"VA declined by 5+ letters: {significant_decline} patients ({significant_decline/len(with_second_visit)*100:.1f}%)")

print(f"\nData saved to {output_file}")