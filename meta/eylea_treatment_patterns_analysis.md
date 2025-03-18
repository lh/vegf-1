# Eylea Treatment Patterns Analysis

## Overview

This analysis examines the treatment patterns of patients receiving Eylea injections, with a focus on identifying two hypothesized groups:

1. **Group LH**: Patients who receive 7 injections in the first year and then continue with injections approximately every two months.
2. **Group MR**: Patients who receive 7 injections in the first year, then have a pause before resuming treatment.

## Data Summary

- Total patients analyzed: 1,723
- Patients with exactly 7 injections in first year: 382 (22.2% of total)
- Patients identified in Group LH: 36 (2.1% of total)
- Patients identified in Group MR: 33 (1.9% of total)
- Other patients: 1,654 (96.0% of total)

## Group Characteristics

### Manual Classification

We defined the following criteria for each group:

**Group LH**:
- Consistent ~2 month intervals (40-80 days)
- No long pause after first year (<120 days)
- Low variability in intervals (std < 30)

**Group MR**:
- Pause after first year (>120 days)
- Resumed treatment after pause

### Clustering Analysis

We also performed K-means clustering on patients with 7 injections in the first year and post-year data, using the following features:
- Post-year average interval
- Pause duration after first year
- Post-year standard deviation of intervals
- Number of long gaps (>120 days) in post-year

The clustering identified two distinct groups with the following characteristics:

**Cluster 0 (MR-like)**:
- Count: 91 patients
- Average pause: 223.9 days
- Average interval: 67.4 days
- Standard deviation of intervals: 26.4 days
- Average number of long gaps: 0.36

**Cluster 1 (LH-like)**:
- Count: 31 patients
- Average pause: 15.7 days
- Average interval: 130.1 days
- Standard deviation of intervals: 150.5 days
- Average number of long gaps: 2.65

## Key Findings

1. The clustering analysis identified more patients in each group than our manual classification, suggesting that our manual criteria may be too strict.

2. The MR-like cluster (Cluster 0) shows a clear pattern of a long pause (average 224 days) after the first year, followed by relatively consistent intervals (std dev 26.4 days).

3. The LH-like cluster (Cluster 1) shows minimal pause after the first year (average 15.7 days) but has more variable intervals (std dev 150.5 days) and more long gaps during treatment.

4. The proportion of patients following either pattern is relatively small compared to the total population, suggesting that most patients follow different treatment patterns.

## Visualizations

The analysis generated several visualizations to help understand the treatment patterns:

1. **Treatment Pattern Clusters (PCA)**: Shows the clustering of patients based on their treatment patterns.
2. **Injection Timelines by Group**: Shows the timing of injections for sample patients from each group.
3. **Distribution of Injection Intervals by Group**: Shows the distribution of intervals between injections for each group.
4. **Average Injection Intervals by Group**: Shows the average interval between injections for each group.
5. **Visual Acuity Trajectories by Group**: Shows the visual acuity over time for each group.
6. **Visual Acuity Change from Baseline by Group**: Shows the change in visual acuity from baseline for each group.

## Conclusion

The analysis confirms the existence of two distinct treatment patterns among patients receiving Eylea injections. Group LH patients continue treatment with minimal interruption after the first year, while Group MR patients have a significant pause before resuming treatment. However, these patterns represent a small proportion of the total patient population, suggesting that most patients follow different treatment trajectories.

Further analysis could explore:
1. The outcomes (visual acuity) associated with each treatment pattern
2. The reasons for the pause in treatment for Group MR patients
3. The identification of additional treatment patterns in the larger patient population
