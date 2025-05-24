"""
Analyze patients with high baseline VA (≥75 letters) to check for potential data recording errors.
Tracks vision changes over first 4 visits to identify potential outliers.
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns

# Set plot style
plt.style.use('ggplot')
sns.set_context("talk")

# Connect to database
db_path = Path('output/eylea_intervals.db')
conn = sqlite3.connect(db_path)

# First, identify patients with high initial VA (≥75 letters)
query_high_va = """
WITH RankedMeasurements AS (
    SELECT 
        uuid, 
        eye,
        current_va,
        current_date,
        ROW_NUMBER() OVER (PARTITION BY uuid, eye ORDER BY current_date ASC) as row_num
    FROM interval_va_data 
    GROUP BY uuid, eye
)
SELECT 
    uuid, 
    eye, 
    current_va as initial_va,
    current_date as initial_date
FROM RankedMeasurements
WHERE row_num = 1 AND current_va >= 75
ORDER BY current_va DESC
"""

# Load high VA patients
high_va_patients = pd.read_sql_query(query_high_va, conn)
print(f"Found {len(high_va_patients)} patients with initial VA ≥ 75 letters")

# Extract their first 4 visits
patient_trajectories = []

for _, patient in high_va_patients.iterrows():
    patient_query = f"""
    SELECT 
        uuid, 
        eye, 
        current_va,
        current_date,
        ROW_NUMBER() OVER (PARTITION BY uuid, eye ORDER BY current_date ASC) as visit_num
    FROM interval_va_data
    WHERE uuid = '{patient['uuid']}' AND eye = '{patient['eye']}'
    ORDER BY current_date ASC
    LIMIT 4
    """
    
    visits = pd.read_sql_query(patient_query, conn)
    
    if len(visits) > 0:
        patient_trajectory = {
            'uuid': patient['uuid'],
            'eye': patient['eye'],
            'initial_va': patient['initial_va'],
            'visits': []
        }
        
        for _, visit in visits.iterrows():
            patient_trajectory['visits'].append({
                'visit_num': visit['visit_num'],
                'date': visit['current_date'],
                'va': visit['current_va']
            })
        
        patient_trajectories.append(patient_trajectory)

conn.close()

# Prepare data for plotting
plot_data = []
for patient in patient_trajectories:
    for visit in patient['visits']:
        plot_data.append({
            'patient_id': f"{patient['uuid']}_{patient['eye']}",
            'initial_va': patient['initial_va'],
            'visit_num': visit['visit_num'],
            'va': visit['va'],
            'va_change': visit['va'] - patient['initial_va']
        })

plot_df = pd.DataFrame(plot_data)

# Create figure for all trajectories
plt.figure(figsize=(14, 8))
# Group by initial VA to color patients differently
initial_va_groups = pd.cut(plot_df['initial_va'], bins=[74, 80, 85, 90, 100], 
                        labels=['75-80', '81-85', '86-90', '91-100'])
plot_df['va_group'] = initial_va_groups

# Plot individual patient trajectories
for patient_id, patient_data in plot_df.groupby('patient_id'):
    if len(patient_data) >= 2:  # Only plot if we have at least 2 visits
        plt.plot(patient_data['visit_num'], patient_data['va'], 
                marker='o', alpha=0.5, 
                label=f"Initial VA: {patient_data['initial_va'].iloc[0]}")

# Formatting
plt.title('Visual Acuity Trajectories for Patients with High Baseline VA (≥75 letters)', fontsize=14)
plt.xlabel('Visit Number', fontsize=12)
plt.ylabel('Visual Acuity (ETDRS Letters)', fontsize=12)
plt.xticks([1, 2, 3, 4])
plt.ylim(0, 100)
plt.grid(True, alpha=0.3)

# Highlight the 70-letter threshold
plt.axhline(y=70, color='red', linestyle='--', alpha=0.7, 
            label='Treatment eligibility cutoff (70 letters)')

# Save the figure
output_fig1 = Path('output/high_va_trajectories.png')
plt.tight_layout()
plt.savefig(output_fig1, dpi=300)
print(f"Saved all trajectories to {output_fig1}")
plt.close()

# Calculate average trajectories by initial VA group for a cleaner view
plt.figure(figsize=(10, 6))

# Calculate mean VA and standard error for each group and visit
group_stats = plot_df.groupby(['va_group', 'visit_num']).agg(
    mean_va=('va', 'mean'),
    std_va=('va', 'std'),
    count=('va', 'count')
).reset_index()

group_stats['se_va'] = group_stats['std_va'] / np.sqrt(group_stats['count'])

# Plot mean trajectories with error bands
for group, data in group_stats.groupby('va_group'):
    if not pd.isna(group):  # Skip NaN groups
        plt.plot(data['visit_num'], data['mean_va'], 'o-', label=f'Initial VA: {group}')
        plt.fill_between(data['visit_num'], 
                        data['mean_va'] - data['se_va'], 
                        data['mean_va'] + data['se_va'], 
                        alpha=0.2)

# Add titles and labels
plt.title('Average VA Trajectories by Initial VA Group', fontsize=14)
plt.xlabel('Visit Number', fontsize=12)
plt.ylabel('Mean Visual Acuity (ETDRS Letters)', fontsize=12)
plt.xticks([1, 2, 3, 4])
plt.ylim(40, 100)
plt.legend(title='Initial VA Group')
plt.grid(True, alpha=0.3)

# Highlight the 70-letter threshold
plt.axhline(y=70, color='red', linestyle='--', alpha=0.7, 
            label='Treatment eligibility cutoff')

# Save the figure
output_fig2 = Path('output/high_va_mean_trajectories.png')
plt.tight_layout()
plt.savefig(output_fig2, dpi=300)
print(f"Saved mean trajectories to {output_fig2}")
plt.close()

# Calculate drop size from visit 1 to visit 2
if len(plot_df) > 0:
    visit1 = plot_df[plot_df['visit_num'] == 1].set_index('patient_id')
    visit2 = plot_df[plot_df['visit_num'] == 2].set_index('patient_id')
    
    # Keep only patients with both visits
    common_patients = list(set(visit1.index) & set(visit2.index))
    
    if common_patients:
        visit1 = visit1.loc[common_patients]
        visit2 = visit2.loc[common_patients]
        
        # Calculate VA drops
        va_drops = []
        for patient_id in common_patients:
            va_drop = {
                'patient_id': patient_id,
                'initial_va': visit1.loc[patient_id, 'initial_va'],
                'visit1_va': visit1.loc[patient_id, 'va'],
                'visit2_va': visit2.loc[patient_id, 'va'],
                'va_drop': visit1.loc[patient_id, 'va'] - visit2.loc[patient_id, 'va']
            }
            va_drops.append(va_drop)
        
        va_drop_df = pd.DataFrame(va_drops)
        
        # Calculate statistics
        drop_mean = va_drop_df['va_drop'].mean()
        drop_median = va_drop_df['va_drop'].median()
        drop_std = va_drop_df['va_drop'].std()
        significant_drops = (va_drop_df['va_drop'] >= 5).sum()
        
        print("\nVisual Acuity Change from Visit 1 to Visit 2:")
        print(f"Mean drop: {drop_mean:.2f} letters")
        print(f"Median drop: {drop_median:.2f} letters")
        print(f"Standard deviation: {drop_std:.2f} letters")
        print(f"Patients with ≥5 letter drop: {significant_drops} ({significant_drops/len(va_drop_df)*100:.1f}%)")
        
        # Plot the distribution of VA drops
        plt.figure(figsize=(10, 6))
        plt.hist(va_drop_df['va_drop'], bins=15, alpha=0.7, color='steelblue', edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='No change')
        plt.axvline(x=drop_mean, color='green', linestyle='-', alpha=0.7, 
                  label=f'Mean drop: {drop_mean:.2f} letters')
        
        # Add titles and labels
        plt.title('Distribution of VA Changes from Visit 1 to Visit 2\nfor Patients with High Baseline VA (≥75 letters)', 
                fontsize=14)
        plt.xlabel('VA Change in Letters (Positive = Vision Loss)', fontsize=12)
        plt.ylabel('Number of Patients', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save the figure
        output_fig3 = Path('output/high_va_drops.png')
        plt.tight_layout()
        plt.savefig(output_fig3, dpi=300)
        print(f"Saved VA drop distribution to {output_fig3}")
        plt.close()
        
        # Also create a scatterplot of initial VA vs drop size
        plt.figure(figsize=(10, 6))
        plt.scatter(va_drop_df['initial_va'], va_drop_df['va_drop'], 
                  alpha=0.7, color='steelblue', edgecolor='black')
        
        # Add regression line
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            va_drop_df['initial_va'], va_drop_df['va_drop'])
        
        x = np.array([min(va_drop_df['initial_va']), max(va_drop_df['initial_va'])])
        plt.plot(x, intercept + slope * x, 'r-', 
                label=f'Regression line (r={r_value:.2f}, p={p_value:.3f})')
        
        # Add titles and labels
        plt.title('Relationship Between Initial VA and Vision Drop\nat Second Visit', 
                fontsize=14)
        plt.xlabel('Initial Visual Acuity (ETDRS Letters)', fontsize=12)
        plt.ylabel('VA Change in Letters (Positive = Vision Loss)', fontsize=12)
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save the figure
        output_fig4 = Path('output/high_va_correlation.png')
        plt.tight_layout()
        plt.savefig(output_fig4, dpi=300)
        print(f"Saved VA correlation plot to {output_fig4}")