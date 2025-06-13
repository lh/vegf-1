"""
Fit statistical distributions to the initial visual acuity data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import seaborn as sns

# Load the data
data_path = Path('output/initial_va_data.csv')
df = pd.read_csv(data_path)

# Extract the visual acuity values and clean non-finite values
va_values = df['current_va'].dropna().values
print(f"Original data points: {len(df)}")
print(f"Valid data points after dropping NaN: {len(va_values)}")

# Additional check for infinite values
va_values = va_values[np.isfinite(va_values)]
print(f"Valid data points after dropping non-finite: {len(va_values)}")

# Create figure
plt.figure(figsize=(12, 8))

# Create histogram with kernel density estimate
sns.histplot(va_values, bins=30, kde=True, color='steelblue', 
             edgecolor='black', alpha=0.7, stat='density')

# List of distributions to try
distributions = [
    ('Normal', stats.norm),
    ('Skew Normal', stats.skewnorm),
    ('Beta', stats.beta),
    ('Gamma', stats.gamma),
    ('Truncated Normal', stats.truncnorm)
]

# Colors for plotting
colors = ['red', 'green', 'purple', 'orange', 'magenta']

# Prepare x values for plotting
x = np.linspace(0, 100, 1000)

# Fit each distribution and plot
best_fit = None
best_aic = np.inf
results = []

for (name, distribution), color in zip(distributions, colors):
    try:
        # Handle special cases
        if name == 'Beta':
            # Scale to [0, 1] for beta distribution
            scaled_data = va_values / 100
            params = distribution.fit(scaled_data)
            pdf = distribution.pdf(x/100, *params) / 100  # Scale back
            aic = -2 * np.sum(np.log(distribution.pdf(scaled_data, *params))) + 2 * len(params)
            
        elif name == 'Truncated Normal':
            # Truncated normal distribution (between 0 and 100)
            a, b = (0 - np.mean(va_values)) / np.std(va_values), (100 - np.mean(va_values)) / np.std(va_values)
            params = distribution.fit(va_values, a, b)
            pdf = distribution.pdf(x, *params)
            aic = -2 * np.sum(np.log(distribution.pdf(va_values, *params))) + 2 * len(params)
            
        else:
            # Standard fit for other distributions
            params = distribution.fit(va_values)
            pdf = distribution.pdf(x, *params)
            aic = -2 * np.sum(np.log(distribution.pdf(va_values, *params))) + 2 * len(params)
        
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
plt.title('Distribution of Initial Visual Acuity with Fitted Distributions', fontsize=16)
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
print("\nSummary Statistics:")
print(f"Count: {len(va_values)}")
print(f"Mean: {np.mean(va_values):.2f}")
print(f"Median: {np.median(va_values):.2f}")
print(f"Standard Deviation: {np.std(va_values):.2f}")
print(f"Min: {np.min(va_values):.2f}")
print(f"Max: {np.max(va_values):.2f}")
print(f"Skewness: {stats.skew(va_values):.2f}")
print(f"Kurtosis: {stats.kurtosis(va_values):.2f}")

# Show percentiles
percentiles = [5, 10, 25, 50, 75, 90, 95]
percentile_values = np.percentile(va_values, percentiles)
print("\nPercentiles:")
for p, v in zip(percentiles, percentile_values):
    print(f"{p}th: {v:.2f}")

# Save the figure
output_file = Path('output/va_distribution_fitted.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved distribution plot to {output_file}")

# Show the plot
plt.tight_layout()
plt.show()