# PCA Analysis of Eylea Treatment Intervals and Visual Acuity

## Overview

This report presents the findings from Principal Component Analysis (PCA) performed on Eylea treatment data, focusing on the relationship between treatment intervals and visual acuity (VA) measures. The analysis aims to identify distinct patterns in treatment responses and outcomes.

## Methodology

The analysis focused on four key variables:
- **Treatment interval**: Days between injections
- **Previous VA**: Visual acuity at previous injection (letters)
- **Current VA**: Visual acuity at current injection (letters)
- **Next VA**: Visual acuity at next injection (letters)

Data preparation involved:
1. Calculating "next VA" for each record by linking sequential injections for each patient eye
2. Standardizing all variables to ensure equal weighting in the PCA
3. Applying PCA to reduce dimensionality and identify key patterns
4. Using K-means clustering (with k=2, 3, and 4) to identify distinct patient groups

## Results

The analysis was performed on 16,769 complete records from the Eylea injection database.

### Two-Cluster Analysis

The two-cluster analysis revealed two distinct treatment patterns:

1. **Cluster 1** (5,165 records, 30.8%):
   - Higher average interval: 83.6 days
   - Lower average VA: ~41-42 letters
   - Greater VA decline: -0.65 letters between injections

2. **Cluster 2** (11,604 records, 69.2%):
   - Lower average interval: 73.5 days
   - Higher average VA: ~68-69 letters
   - Less VA decline: -0.21 letters between injections

This suggests a relationship between treatment frequency, visual acuity, and outcomes. Patients with better vision tend to receive more frequent injections and experience less vision decline between treatments.

### Three-Cluster Analysis

The three-cluster analysis provided further granularity:

1. **Cluster 1** (5,331 records, 31.8%):
   - Moderate interval: 80.5 days
   - Moderate VA: ~56 letters
   - Moderate VA decline: -0.45 letters

2. **Cluster 2** (3,028 records, 18.1%):
   - Longer interval: 86.2 days
   - Low VA: ~35 letters
   - Greater VA decline: -0.61 letters

3. **Cluster 3** (8,410 records, 50.2%):
   - Shorter interval: 70.7 days
   - High VA: ~72 letters
   - Less VA decline: -0.19 letters

This analysis reveals a more nuanced relationship, with a middle group of patients who have moderate vision and experience moderate vision decline.

### Four-Cluster Analysis

The four-cluster analysis revealed a particularly interesting small group:

1. **Cluster 1** (5,236 records, 31.2%):
   - Moderate interval: 69.1 days
   - Moderate VA: ~56 letters
   - Moderate VA decline: -0.49 letters

2. **Cluster 2** (2,979 records, 17.8%):
   - Moderate interval: 69.7 days
   - Low VA: ~35 letters
   - Greater VA decline: -0.65 letters

3. **Cluster 3** (8,347 records, 49.8%):
   - Shorter interval: 66.0 days
   - High VA: ~72 letters
   - Less VA decline: -0.20 letters

4. **Cluster 4** (207 records, 1.2%):
   - Very long intervals: 793.7 days (>2 years)
   - Moderate starting VA: 64.4 letters
   - Significant VA drop at injection: 52.4 letters
   - VA improvement after injection: +1.59 letters

Cluster 4 represents a small but clinically significant group of patients who have very long gaps between treatments, experience significant vision loss during the gap, but show improvement after receiving an injection. This pattern may represent patients who discontinue regular treatment but return when vision deteriorates significantly.

## Clinical Implications

1. **Treatment Frequency and Outcomes**:
   - Patients with better vision (Cluster 3 in the 4-cluster analysis) tend to receive more frequent injections and maintain stable vision.
   - Patients with poorer vision (Cluster 2) may benefit from more frequent injections to prevent further decline.

2. **Long-Gap Patients**:
   - The identification of a small group with very long treatment gaps (Cluster 4) suggests a need for better follow-up strategies for patients who discontinue treatment.
   - The positive VA response after injection in this group indicates that treatment can still be beneficial even after long gaps.

3. **Personalized Treatment Approaches**:
   - The distinct clusters suggest that different treatment frequencies may be optimal for different patient groups.
   - Monitoring VA changes between injections could help optimize treatment intervals for individual patients.

## Conclusion

The PCA analysis has revealed distinct patterns in the relationship between treatment intervals and visual acuity outcomes in Eylea patients. These patterns suggest opportunities for more personalized treatment approaches based on patient characteristics and response patterns.

Further analysis could explore:
- Demographic and clinical factors associated with each cluster
- Long-term outcomes for patients in each cluster
- Optimal treatment intervals for different patient groups
- Strategies to improve outcomes for patients in the lower-performing clusters
