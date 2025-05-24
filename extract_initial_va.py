"""
Extract initial visual acuities from eylea_intervals.db and create histogram
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

# Set plot style
plt.style.use('fivethirtyeight')
sns.set_context("talk")

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

# Create figure
plt.figure(figsize=(12, 8))

# Create histogram
sns.histplot(initial_va_df['current_va'], bins=20, kde=True, color='steelblue')

# Test different distributions
x = np.linspace(0, 85, 1000)
best_distribution = None
best_params = None
best_sse = np.inf

# List of distributions to test
distributions = [
    stats.norm,
    stats.truncnorm,
    stats.beta,
    stats.gamma,
    stats.lognorm
]

# Fit each distribution and find the best one
for distribution in distributions:
    try:
        # Fit distribution to data
        if distribution == stats.truncnorm:
            # Special case for truncated normal (between 0 and 85)
            params = distribution.fit(initial_va_df['current_va'], floc=0, fscale=85)
        elif distribution == stats.beta:
            # Beta needs to be scaled between 0 and 1
            scaled_data = initial_va_df['current_va'] / 85
            params = distribution.fit(scaled_data, floc=0, fscale=1)
        else:
            params = distribution.fit(initial_va_df['current_va'])
        
        # Get PDF values
        if distribution == stats.beta:
            pdf = distribution.pdf(x/85, *params) / 85  # Scale back
        else:
            pdf = distribution.pdf(x, *params)
        
        # Calculate SSE (sum of squared errors)
        hist, bin_edges = np.histogram(initial_va_df['current_va'], bins=20, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Interpolate PDF at bin centers
        if distribution == stats.beta:
            pdf_at_centers = distribution.pdf(bin_centers/85, *params) / 85
        else:
            pdf_at_centers = distribution.pdf(bin_centers, *params)
        
        sse = np.sum((hist - pdf_at_centers)**2)
        
        if sse < best_sse:
            best_distribution = distribution
            best_params = params
            best_sse = sse
            
    except Exception as e:
        print(f"Error fitting {distribution.name}: {e}")
        continue

# Plot the best fitting distribution
if best_distribution:
    if best_distribution == stats.beta:
        # Scale x values for beta distribution
        best_fit_line = best_distribution.pdf(x/85, *best_params) / 85
    else:
        best_fit_line = best_distribution.pdf(x, *best_params)
    
    plt.plot(x, best_fit_line, 'r-', linewidth=2, 
             label=f'Best fit: {best_distribution.name}')
    
    # Print distribution parameters
    param_names = ['a', 'b', 'loc', 'scale'] if best_distribution == stats.beta else ['loc', 'scale']
    param_values = best_params
    param_str = ', '.join([f'{name}={val:.3f}' for name, val in zip(param_names, param_values)])
    print(f"\nBest fitting distribution: {best_distribution.name}")
    print(f"Parameters: {param_str}")

# Add reference line at 70 letters
plt.axvline(x=70, color='red', linestyle='--', alpha=0.7, 
            label='Treatment eligibility cutoff (70 letters)')

# Styling
plt.title('Distribution of Initial Visual Acuity in AMD Patients', fontsize=16)
plt.xlabel('Visual Acuity (ETDRS Letters)', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.legend()
plt.grid(alpha=0.3)

# Save the figure
output_file = Path('output/initial_va_distribution.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved distribution plot to {output_file}")

# Show the plot
plt.tight_layout()
plt.show()