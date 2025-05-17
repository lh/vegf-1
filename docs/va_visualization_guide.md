# Visual Acuity Visualization Guide

## Overview

The Clinical Pathway Engine provides two complementary visualizations for visual acuity data, each serving a distinct purpose. Understanding the differences between these plots is crucial for proper interpretation of simulation results.

## Mean Plot with Confidence Intervals

### Purpose
Shows the population mean visual acuity over time with 95% confidence intervals indicating our statistical certainty about the mean value.

### What it shows
- **Mean line**: Average visual acuity across all patients at each time point
- **Shaded area**: 95% confidence interval for the mean
- **Sample size bars**: Number of patients contributing data at each time point

### What the 95% CI means
- **IS**: A measure of our confidence in the estimated mean value
- **IS NOT**: The range where 95% of patients fall

### When to use
- Comparing average treatment effects between protocols
- Assessing overall population trends
- Statistical hypothesis testing
- Reporting average outcomes

### Key insight
A narrow CI indicates high confidence in the mean estimate (usually due to large sample size), not a narrow range of patient values.

## Distribution Plot with Percentile Bands

### Purpose
Shows the actual distribution of patient visual acuity values over time using percentile bands.

### What it shows
- **Median line**: The 50th percentile (middle value)
- **Dark band**: 25th-75th percentile (interquartile range) - where 50% of patients fall
- **Medium band**: 10th-90th percentile - where 80% of patients fall  
- **Light band**: 5th-95th percentile - where 90% of patients fall
- **Sample size labels**: Number of patients at each time point

### What the bands mean
- **ARE**: The actual range of patient visual acuity values
- **ARE NOT**: Statistical confidence intervals

### When to use
- Understanding patient heterogeneity
- Identifying outliers or subpopulations
- Clinical decision making for individual patients
- Assessing treatment response variability

### Key insight
Wide bands indicate high variability among patients, even if the mean is precisely estimated.

## Side-by-Side Comparison

The two plots answer different questions:

| Mean Plot | Distribution Plot |
|-----------|------------------|
| How confident are we in the average? | What is the range of patient outcomes? |
| Statistical inference | Clinical variability |
| Population parameter estimation | Individual patient expectations |
| Hypothesis testing | Treatment planning |

## Example Interpretation

Consider a scenario at baseline (Month 0):
- **Mean plot**: Shows a narrow 95% CI (e.g., 72-74 letters)
- **Distribution plot**: Shows a wide range (e.g., 55-85 letters)

This tells us:
1. We're very confident the true population mean is around 73 letters
2. Individual patients vary widely, from 55 to 85 letters
3. The narrow CI is due to large sample size, not homogeneous patients

## Common Misinterpretations to Avoid

1. **Don't interpret the 95% CI as patient range**
   - Wrong: "95% of patients have VA between 72-74 letters"
   - Right: "We're 95% confident the true mean is between 72-74 letters"

2. **Don't assume narrow CI means uniform patients**
   - Wrong: "All patients have similar vision"
   - Right: "We have a precise estimate of the average"

3. **Don't use mean plot for individual predictions**
   - Wrong: "A new patient will likely have 73 letters"
   - Right: "The average patient has 73 letters, individuals vary widely"

## Best Practices

1. **Always show both plots when possible**
   - Provides complete picture of population behavior
   - Prevents misinterpretation

2. **Label clearly**
   - Use descriptive titles
   - Include explanatory notes
   - Show sample sizes

3. **Consider the audience**
   - Statisticians: May prefer mean + CI
   - Clinicians: May prefer distribution
   - Mixed: Show both with clear explanations

4. **Document assumptions**
   - Data collection methods
   - Missing data handling
   - Smoothing or aggregation applied

## Technical Notes

### Mean Plot Calculation
```
Standard Error = Standard Deviation / √(Sample Size)
95% CI = Mean ± 1.96 × Standard Error
```

### Distribution Plot Calculation
```
For each time point:
  - Sort all patient values
  - Find percentiles directly from sorted data
  - No statistical inference involved
```

### Sample Size Effects
- **Mean plot**: Larger n → narrower CI
- **Distribution plot**: Larger n → more stable percentiles

## Conclusion

Both visualizations are essential for complete understanding of visual acuity outcomes. The mean plot answers "what is the average effect?" while the distribution plot answers "what is the range of effects?" Using both together provides the most comprehensive view of treatment outcomes.