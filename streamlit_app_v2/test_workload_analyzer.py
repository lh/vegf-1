"""Quick test of the workload analyzer with sample data."""

import pandas as pd
import numpy as np
from components.treatment_patterns.workload_analyzer import calculate_clinical_workload_attribution, format_workload_insight

# Create sample visit data that demonstrates the workload pattern
sample_data = []

# Intensive patients (few patients, many visits)
for patient_id in range(1, 21):  # 20 patients
    base_date = 0
    for visit in range(8):  # 8 visits each = 160 total visits
        sample_data.append({
            'patient_id': patient_id,
            'interval_days': 28 + np.random.normal(0, 5) if visit > 0 else np.nan
        })
        base_date += 30

# Regular patients (more patients, moderate visits)  
for patient_id in range(21, 121):  # 100 patients
    base_date = 0
    for visit in range(4):  # 4 visits each = 400 total visits
        sample_data.append({
            'patient_id': patient_id,
            'interval_days': 56 + np.random.normal(0, 10) if visit > 0 else np.nan
        })
        base_date += 60

# Extended patients (many patients, few visits)
for patient_id in range(121, 321):  # 200 patients  
    base_date = 0
    for visit in range(2):  # 2 visits each = 400 total visits
        sample_data.append({
            'patient_id': patient_id,
            'interval_days': 98 + np.random.normal(0, 15) if visit > 0 else np.nan
        })
        base_date += 100

# Create DataFrame
visits_df = pd.DataFrame(sample_data)

# Test the analyzer
print("Testing Clinical Workload Analyzer...")
print("=" * 50)

results = calculate_clinical_workload_attribution(visits_df)

print(f"Total patients: {results['total_patients']}")
print(f"Total visits: {results['total_visits']}")
print()

print("Visit Contributions by Category:")
print(results['visit_contributions'])
print()

print("Summary Statistics:")
for category, stats in results['summary_stats'].items():
    print(f"\n{category}:")
    print(f"  Patients: {stats['patient_count']} ({stats['patient_percentage']:.1f}%)")
    print(f"  Visits: {stats['visit_count']} ({stats['visit_percentage']:.1f}%)")
    print(f"  Visits/Patient: {stats['visits_per_patient']:.1f}")
    print(f"  Workload Efficiency: {stats['workload_efficiency']:.1f}x")

print("\nKey Insight:")
print(format_workload_insight(results['summary_stats']))

print("\nExpected Pattern:")
print("- Intensive patients (6.25% of patients) should generate ~17% of visits")
print("- Regular patients (31.25% of patients) should generate ~42% of visits")  
print("- Extended patients (62.5% of patients) should generate ~42% of visits")
print("- This demonstrates how intensive patients create disproportionate workload!")