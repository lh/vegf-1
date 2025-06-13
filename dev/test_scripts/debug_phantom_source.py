#!/usr/bin/env python3
"""
Debug where the phantom data beyond month 60 is coming from.
"""
import json
import pandas as pd

# Load actual simulation results
with open('/Users/rose/Code/CC/output/simulation_results/ape_simulation_ABS_20250514_221752.json', 'r') as f:
    results = json.loads(f.read())

print("=== CHECKING RESULTS['MEAN_VA_DATA'] DIRECTLY ===")

# Check what's in the saved results
mean_va_data = results.get('mean_va_data', [])
print(f"Number of points in mean_va_data: {len(mean_va_data)}")

# Convert to DataFrame for analysis
df = pd.DataFrame(mean_va_data)
print(f"\nColumns in mean_va_data: {list(df.columns)}")

# Check time range
if 'time' in df.columns:
    print(f"\nTime range: {df['time'].min():.2f} to {df['time'].max():.2f}")
    phantom_data = df[df['time'] > 60]
    print(f"Points beyond month 60: {len(phantom_data)}")
    
    if len(phantom_data) > 0:
        print("\nSample of phantom data:")
        print(phantom_data[['time', 'visual_acuity', 'sample_size']].head(10))
        
        print("\nAll phantom time points:")
        print(sorted(phantom_data['time'].unique()))

# Check if there's smoothing data
if 'visual_acuity_smoothed' in df.columns:
    print("\nSmoothing data present!")
    smoothed_phantom = df[(df['time'] > 60) & (df['visual_acuity_smoothed'].notna())]
    print(f"Smoothed points beyond month 60: {len(smoothed_phantom)}")

# Check duration
duration_years = results.get('duration_years', 'unknown')
print(f"\nSimulation duration: {duration_years} years")
expected_max_months = duration_years * 12 if isinstance(duration_years, (int, float)) else 'unknown'
print(f"Expected max months: {expected_max_months}")

# Check if there's a different time field
for col in df.columns:
    if 'time' in col.lower():
        print(f"\nTime-related column '{col}':")
        print(f"  Range: {df[col].min():.2f} to {df[col].max():.2f}")
        
# Check patient_count vs sample_size
if 'patient_count' in results:
    print(f"\npatient_count in results: {results['patient_count']}")
    
# Look for clues about data generation
print("\n=== LOOKING FOR CLUES ===")
if 'is_sample' in results:
    print(f"is_sample: {results['is_sample']}")
    
if 'runtime_seconds' in results:
    print(f"runtime_seconds: {results['runtime_seconds']}")
    
if 'failed' in results:
    print(f"failed: {results['failed']}")
    
# Check if this might be sample/test data
if 'timestamp' in results:
    print(f"timestamp: {results['timestamp']}")
    
# Check the structure of the first few and last few points
print("\n=== FIRST AND LAST DATA POINTS ===")
if len(df) > 0:
    print("First 5 points:")
    print(df.head(5))
    print("\nLast 5 points:")
    print(df.tail(5))