# Analysis of Patients with High Baseline Visual Acuity (≥75 letters)

## Overview
This document summarizes the findings from our analysis of patients with high baseline visual acuity (≥75 letters) to investigate potential data recording errors or outliers.

## Methods
We analyzed visual acuity trajectories for all patients with baseline VA ≥ 75 letters across their first 4 visits. The analysis included:
1. Individual patient trajectory plots
2. Aggregate trajectories by VA range groups
3. Statistical analysis of VA changes between visits 1 and 2
4. Correlation between initial VA and subsequent vision changes

## Key Findings

### Patient Population
- **Total patients with baseline VA ≥ 75 letters**: 224 patients
- **Distribution by letter range**:
  - 75-80 letters: ~72% 
  - 81-85 letters: ~23%
  - 86-90 letters: < 5%
  - 91-100 letters: < 1%

### Visual Acuity Trajectories
- Most patients maintained relatively stable VA over subsequent visits
- The average VA remained above 70 letters (treatment threshold) for most patients
- Patients with the highest initial VA (91-100 letters) showed substantial vision drops by visit 2
- Patients in the 86-90 range showed the most dramatic decline pattern over multiple visits

### Vision Changes Between Visits 1 and 2
- **Mean vision drop**: 2.49 letters
- **Median vision drop**: 2.00 letters
- **Standard deviation**: 6.17 letters
- **Proportion with significant decline (≥5 letters)**: 27.9% (61 patients)
- **Distribution pattern**: Right-skewed with more patients showing vision loss than vision gain

### Relationship Between Initial VA and Vision Drop
- Patients with the highest initial VA (>90 letters) tended to show larger vision drops
- No clear linear relationship across the entire range
- Vision drop variance increases at the extremes of the baseline VA range

## Conclusions

1. **Not Measurement Errors**: The patterns observed suggest these high VA measurements are not likely to be simple recording errors:
   - Gradual rather than sudden changes in most cases
   - Consistent patterns by initial VA group
   - High proportion of patients (27.9%) showing significant vision deterioration at second visit

2. **Possible Explanations**:
   - True disease progression: Patients were likely measured correctly, but their disease was actively progressing
   - Treatment timing: Baseline measurements may have been taken before the impact of disease was fully evident
   - Patient selection: Patients may have been selected for treatment based on OCT findings rather than vision loss

3. **Clinical Implications**:
   - Higher baseline VA is associated with greater risk of substantial vision loss in early visits
   - Patients with very high VA (>85 letters) at baseline warrant close monitoring
   - VA changes should be interpreted in context of OCT findings rather than in isolation

## Recommendations for Vision Model
- Initial VA distribution in the model should include patients with high baseline VA (>70 letters)
- Incorporate differential VA change patterns based on baseline VA
- Model should account for regression to the mean effect in patients with very high baseline VA
- Include realistic VA fluctuations, especially in higher VA ranges