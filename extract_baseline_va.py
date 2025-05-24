"""
Extract truly baseline (treatment-naïve) visual acuities and analyze distribution
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import seaborn as sns

# Connect to database
db_path = Path('output/eylea_intervals.db')
conn = sqlite3.connect(db_path)

# Query for the very first measurement for each patient/eye
# This ensures we're getting only treatment-naïve baseline measurements
query = """
WITH RankedMeasurements AS (
    SELECT 
        uuid, 
        eye,
        current_va,
        current_date,
        ROW_NUMBER() OVER (PARTITION BY uuid, eye ORDER BY current_date ASC) as row_num
    FROM interval_va_data
)
SELECT 
    uuid, 
    eye, 
    current_va,
    current_date
FROM RankedMeasurements
WHERE row_num = 1
"""

# Load data
baseline_va_df = pd.read_sql_query(query, conn)
conn.close()

# Clean data - remove any non-finite values
baseline_va_df = baseline_va_df.dropna(subset=['current_va'])
baseline_va = baseline_va_df['current_va'].values
baseline_va = baseline_va[np.isfinite(baseline_va)]

print(f"Number of unique patients/eyes with baseline VA: {len(baseline_va)}")

# Create figure
plt.figure(figsize=(12, 8))

# Create histogram with KDE
sns.histplot(baseline_va, bins=30, kde=True, color='steelblue', 
             edgecolor='black', alpha=0.7, stat='density')

# List of distributions to try
distributions = [
    ('Normal', stats.norm),
    ('Skew Normal', stats.skewnorm),
    ('Beta', stats.beta),
    ('Gamma', stats.gamma)
]

# Colors for plotting
colors = ['red', 'green', 'purple', 'orange']

# Prepare x values for plotting
x = np.linspace(0, 100, 1000)

# Fit each distribution and plot
best_fit = None
best_aic = np.inf
results = []

for (name, distribution), color in zip(distributions, colors):
    try:
        # Handle special case for Beta
        if name == 'Beta':
            # Scale to [0, 1] for beta distribution
            scaled_data = baseline_va / 100
            params = distribution.fit(scaled_data)
            pdf = distribution.pdf(x/100, *params) / 100  # Scale back
            aic = -2 * np.sum(np.log(distribution.pdf(scaled_data, *params) + 1e-10)) + 2 * len(params)
        else:
            # Standard fit for other distributions
            params = distribution.fit(baseline_va)
            pdf = distribution.pdf(x, *params)
            aic = -2 * np.sum(np.log(distribution.pdf(baseline_va, *params) + 1e-10)) + 2 * len(params)
        
        # Plot the PDF
        plt.plot(x, pdf, color=color, linewidth=2, 
                label=f'{name} Distribution')
        
        # Store result
        results.append({
            'Distribution': name,
            'Parameters': params,
            'AIC': aic
        })
        
        # Update best fit
        if aic < best_aic:
            best_fit = name
            best_aic = aic
            
    except Exception as e:
        print(f"Could not fit {name} distribution: {e}")

# Add reference line at 70 letters
plt.axvline(x=70, color='black', linestyle='--', alpha=0.7, 
            label='Treatment eligibility cutoff (70 letters)')

# Styling
plt.title('Distribution of Baseline (Treatment-Naïve) Visual Acuity', fontsize=16)
plt.xlabel('Visual Acuity (ETDRS Letters)', fontsize=14)
plt.ylabel('Density', fontsize=14)
plt.legend()
plt.grid(alpha=0.3)

# Print results
print("\nDistribution Fitting Results:")
print("-" * 30)
for result in sorted(results, key=lambda x: x['AIC']):
    print(f"Distribution: {result['Distribution']}")
    print(f"AIC: {result['AIC']:.2f}")
    print(f"Parameters: {result['Parameters']}")
    print("-" * 30)

print(f"\nBest fitting distribution: {best_fit} (AIC: {best_aic:.2f})")

# Save statistics
print("\nBaseline VA Summary Statistics:")
print(f"Count: {len(baseline_va)}")
print(f"Mean: {np.mean(baseline_va):.2f}")
print(f"Median: {np.median(baseline_va):.2f}")
print(f"Standard Deviation: {np.std(baseline_va):.2f}")
print(f"Min: {np.min(baseline_va):.2f}")
print(f"Max: {np.max(baseline_va):.2f}")
print(f"Skewness: {stats.skew(baseline_va):.2f}")
print(f"Kurtosis: {stats.kurtosis(baseline_va):.2f}")

# Show percentiles
percentiles = [5, 10, 25, 50, 75, 90, 95]
percentile_values = np.percentile(baseline_va, percentiles)
print("\nPercentiles:")
for p, v in zip(percentiles, percentile_values):
    print(f"{p}th: {v:.2f}")

# Count patients above treatment threshold
above_threshold = np.sum(baseline_va > 70)
percent_above = (above_threshold / len(baseline_va)) * 100
print(f"\nPatients with baseline VA > 70 letters: {above_threshold} ({percent_above:.1f}%)")

# Additional analysis: frequency table by VA ranges
ranges = [(0, 30), (31, 50), (51, 70), (71, 85), (86, 100)]
range_counts = {}

for r_min, r_max in ranges:
    count = np.sum((baseline_va >= r_min) & (baseline_va <= r_max))
    percent = (count / len(baseline_va)) * 100
    range_counts[f"{r_min}-{r_max}"] = (count, percent)

print("\nFrequency by VA range:")
for range_name, (count, percent) in range_counts.items():
    print(f"{range_name} letters: {count} patients ({percent:.1f}%)")

# Save the figure
output_file = Path('output/baseline_va_distribution.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved distribution plot to {output_file}")

# Show the plot
plt.tight_layout()
plt.show()