# Premature Discontinuation Analysis

## Overview

This document summarizes the analysis of premature discontinuations in the Eylea real-world dataset. Premature discontinuations are defined as cases where patients with good visual acuity (>20 letters) transition abruptly from regular treatment intervals (≤2 months) to extended intervals (≥6 months), suggesting a potential non-optimal treatment cessation.

## Methodology

The analysis identified premature discontinuations using the following criteria:
1. Visual acuity better than 20 letters at the time of the treatment pattern change
2. Treatment interval increasing from ≤60 days (regular treatment) to ≥180 days (extended interval/effective discontinuation)
3. Two analyses were performed:
   - All premature discontinuations
   - Excluding discontinuations occurring around the one-year mark (330-390 days from treatment start), as these would be classified as "course complete but not renewed" rather than true premature discontinuations

The analysis script is located at `/analysis/identify_premature_discontinuations.py` and output visualizations are in `/output/analysis_results/`.

## Key Findings

### All Premature Discontinuations

- **Total Count**: 282 premature discontinuations identified
- **Unique Patients**: 264 patients affected (282 unique eyes)
- **Visual Acuity at Discontinuation**:
  - Mean: 62.3 letters
  - Median: 65.0 letters
- **Treatment Intervals**:
  - Mean interval before discontinuation: 52.5 days (~7.5 weeks)
  - Mean interval after discontinuation: 418.9 days (~60 weeks/14 months)
- **Visual Acuity Change**:
  - Mean change: -9.8 letters (significant vision loss)

### True Premature Discontinuations (Excluding One-Year Gaps)

- **Total Count**: 266 premature discontinuations identified
- **Unique Patients**: 249 patients affected (266 unique eyes)
- **Visual Acuity at Discontinuation**:
  - Mean: 61.7 letters
  - Median: 65.0 letters
- **Treatment Intervals**:
  - Mean interval before discontinuation: 52.1 days (~7.5 weeks)
  - Mean interval after discontinuation: 411.5 days (~59 weeks/13.7 months)
- **Visual Acuity Change**:
  - Mean change: -9.4 letters (significant vision loss)

## Implications for Simulation

These findings have important implications for our simulation model:

1. **Prevalence**: Premature discontinuations affect approximately 10-15% of patients in real-world data, making this an important pattern to model.

2. **Visual Acuity Impact**: The substantial vision loss associated with premature discontinuations (-9.4 letters on average) highlights the clinical significance of this pattern.

3. **Distinct from Planned Discontinuations**: With only 16 cases (282 - 266) occurring at the one-year mark, true premature discontinuations appear to be distinct from "course complete but not renewed" discontinuations and should be modeled separately.

4. **Treatment Interval Change**: The 8x increase in treatment interval (from ~7.5 weeks to ~60 weeks) represents a dramatic change in treatment pattern that our simulation should capture.

## Implementation Recommendations

Based on this analysis, the simulation should include a specific "premature" discontinuation type with the following parameters:

1. **Eligibility**: Patients with VA > 20 letters who are on regular treatment intervals (≤60 days)

2. **Probability**: Apply a probability of approximately 10-15% per year, calibrated to match the observed real-world frequency

3. **Timing**: Can occur at any point in treatment, not specifically concentrated around the one-year mark

4. **Outcome Modeling**: Should include a model for vision changes after premature discontinuation, with an average decline of approximately 9-10 letters

5. **Monitoring**: Should include appropriate monitoring schedules following premature discontinuation, with recurrence detection as implemented in the enhanced discontinuation model

## Visualizations

Several visualizations were created to analyze the premature discontinuation data:

1. **VA Distribution at Discontinuation**: Histogram showing the distribution of visual acuity at the time of premature discontinuation
2. **VA vs Interval**: Scatter plot showing the relationship between visual acuity and subsequent interval length
3. **VA Change Distribution**: Histogram showing the distribution of vision changes after premature discontinuation
4. **Interval Change**: Scatter plot showing the change from short to long intervals

These visualizations are available in the `/output/analysis_results/` directory.

## Conclusion

Premature discontinuations represent a significant pattern in real-world AMD treatment data, characterized by abrupt transitions from regular treatment to extended intervals despite good visual acuity, resulting in substantial vision loss. Including this pattern in our simulation model will enhance its realism and clinical relevance.