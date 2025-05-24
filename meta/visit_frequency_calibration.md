# Visit Frequency Calibration for Discontinuation Probability

## Background

In our AMD treatment simulation, we need to convert annual discontinuation probabilities into per-visit probabilities. This conversion is crucial for accurate modeling of administrative discontinuations, which are assessed at each visit rather than on an annual basis.

The original implementation used an assumption of approximately 13 visits per year in the following formula:

```python
admin_visit_prob = 1 - ((1 - admin_annual_prob) ** (1/13))
```

This assumption was not based on actual simulation data and led to inaccuracies in the discontinuation rates.

## Data-Driven Calibration

We conducted an analysis of our simulation outputs to determine the actual visit frequency:

1. First, we created an analysis script (`analyze_visits.py`) to process simulation output data and calculate the average visits per year for each patient.

2. We ran this analysis on both the ABS and DES simulation results:

### Results from Agent-Based Simulation (ABS)
- Average visits per year: **6.54**
- Median visits per year: 6.52
- Range: 5.55 to 10.73 visits per year
- 98.7% of patients had between 4-8 visits per year
- 1.3% of patients had between 8-12 visits per year

### Results from Discrete Event Simulation (DES)
- Average visits per year: **6.99**
- Median visits per year: 7.00
- Range: 5.55 to 8.70 visits per year
- 89.4% of patients had between 4-8 visits per year
- 10.6% of patients had between 8-12 visits per year

## Implementation Change

Based on the analysis results, we updated the calculation in `enhanced_discontinuation_manager.py` to use a more accurate value of 7 visits per year:

```python
# Convert annual probability to per-visit probability (analysis shows ~7 visits/year on average)
admin_visit_prob = 1 - ((1 - admin_annual_prob) ** (1/7))
```

## Impact

This calibration has the following impacts:

1. **More accurate discontinuation rates**: The per-visit probability is now higher (approximately 1.75x the previous value for small annual probabilities), which means we'll achieve annual discontinuation rates closer to the target values.

2. **Example calculation**:
   - For 5% annual administrative discontinuation probability:
     - Previous calculation (13 visits): 1 - ((1 - 0.05) ** (1/13)) ≈ 0.004 per visit
     - Updated calculation (7 visits): 1 - ((1 - 0.05) ** (1/7)) ≈ 0.007 per visit

3. **Consistency with treatment protocols**: The 7 visits per year average better reflects real-world treat-and-extend protocols where most stable patients converge to 8-12 week intervals.

## Methodology

The calibration was performed by analyzing the actual simulation outputs:

1. We extracted the dates of all visits for each patient
2. We calculated the duration of each patient's treatment (from first to last visit)
3. We divided the total number of visits by the duration in years
4. We calculated summary statistics (mean, median, range, distribution)

The analysis script (`analyze_visits.py`) is available in the repository for future recalibration as treatment protocols evolve.

## Future Considerations

For even more precision, we may consider:

1. Differentiating visit frequency by treatment phase (loading vs. maintenance)
2. Adjusting visit frequency by clinician profile (adherent vs. non-adherent)
3. Recalibrating after significant protocol changes
4. Making the visit frequency a configurable parameter