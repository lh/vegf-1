"""
Extract initial visual acuities from eylea_intervals.db and create simple histogram
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Connect to database
db_path = Path('output/eylea_intervals.db')
conn = sqlite3.connect(db_path)

# Get initial VA for each patient
query = """
SELECT uuid, eye, current_va, current_date 
FROM interval_va_data 
WHERE (uuid, eye, current_date) IN (
    SELECT uuid, eye, MIN(current_date) 
    FROM interval_va_data 
    GROUP BY uuid, eye
)
"""

# Load data
initial_va_df = pd.read_sql_query(query, conn)
conn.close()

# Print summary statistics
print(f"Total patients/eyes: {len(initial_va_df)}")
print(f"Mean initial VA: {initial_va_df['current_va'].mean():.2f} letters")
print(f"Median initial VA: {initial_va_df['current_va'].median():.2f} letters")
print(f"Standard deviation: {initial_va_df['current_va'].std():.2f} letters")
print(f"Min initial VA: {initial_va_df['current_va'].min():.2f} letters")
print(f"Max initial VA: {initial_va_df['current_va'].max():.2f} letters")

# Create histogram
plt.figure(figsize=(10, 6))
plt.hist(initial_va_df['current_va'], bins=20, alpha=0.7, color='steelblue', edgecolor='black')

# Add reference line at 70 letters
plt.axvline(x=70, color='red', linestyle='--', 
            label='Treatment eligibility cutoff (70 letters)')

# Styling
plt.title('Distribution of Initial Visual Acuity in AMD Patients')
plt.xlabel('Visual Acuity (ETDRS Letters)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(alpha=0.3)

# Save the figure
output_file = Path('output/initial_va_distribution.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved distribution plot to {output_file}")

# Save data to CSV for further analysis
initial_va_df.to_csv('output/initial_va_data.csv', index=False)
print(f"Saved raw data to output/initial_va_data.csv")