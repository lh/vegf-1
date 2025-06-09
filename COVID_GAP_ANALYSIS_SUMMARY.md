# COVID-Era Treatment Gap Analysis Summary
## Real-World Evidence from Aflibercept 2mg Treatment Interruptions

### Executive Summary

Analysis of 21,727 injection intervals from a real-world aflibercept 2mg cohort during the COVID-19 pandemic reveals critical insights about unplanned treatment gaps and their consequences. This data provides evidence-based parameters for modeling treatment interruptions in our simulation framework.

### Key Findings

#### 1. Gap Prevalence and Distribution
- **86.5%** maintained regular treatment (<90 days between injections)
- **11.9%** experienced COVID-related gaps (90-365 days)
  - 9.4% short gaps (3-6 months)
  - 2.5% long gaps (6-12 months)
- **1.6%** effective discontinuations (>365 days)

#### 2. Visual Acuity Consequences by Gap Duration

| Gap Type | Duration | Mean VA Change | Monthly VA Loss | Recovery Rate | Net Impact |
|----------|----------|----------------|-----------------|---------------|------------|
| Regular | <90 days | +0.61 letters | N/A (gaining) | N/A | +4.0/year |
| Short Gap | 90-180 days | -1.78 letters | 0.47 letters/mo | 50.5% | -5.9 letters |
| Long Gap | 180-365 days | -6.83 letters | 0.81 letters/mo | 55.4% | -8.1 letters |
| Discontinuation | >365 days | -11.50 letters | 0.51 letters/mo | Limited data | -11.8 letters |

#### 3. Time-Dependent Risk Profile

The probability of significant vision loss increases with gap duration:

| Gap Duration | % Losing ≥5 letters | % Losing ≥10 letters | % Losing ≥15 letters |
|--------------|--------------------|--------------------|---------------------|
| 0-3 months | 18.8% | 6.3% | 2.5% |
| 3-6 months | 29.9% | 15.0% | 7.0% |
| 6-12 months | 51.8% | 33.5% | 22.0% |
| 1-2 years | 64.2% | 47.8% | 38.4% |
| 2+ years | 61.2% | 49.4% | 40.0% |

#### 4. Recovery Patterns

Post-gap recovery analysis reveals:
- **Short gaps (3-6 months)**: 50.5% show some recovery at next visit
  - Mean recovery: +1.0 letters
  - Net deficit remains: -5.9 letters
- **Long gaps (6-12 months)**: 55.4% show some recovery
  - Mean recovery: +2.0 letters
  - Net deficit remains: -8.1 letters

### Modeling Implications

#### 1. VA Loss During Treatment Gaps
```yaml
# Monthly VA loss rates by gap type
gap_va_loss_rates:
  short_gap_3_6_months:
    mean: -0.47  # letters/month
    std: 2.0
  long_gap_6_12_months:
    mean: -0.81  # letters/month
    std: 3.0
  discontinuation_12_plus_months:
    mean: -0.51  # letters/month (plateaus)
    std: 3.5
```

#### 2. Partial Recovery Model
```yaml
# Recovery potential after resuming treatment
post_gap_recovery:
  short_gap:
    probability_of_recovery: 0.505
    mean_recovery_if_occurs: 2.05  # letters
    time_to_recovery: 1  # visit
  long_gap:
    probability_of_recovery: 0.554
    mean_recovery_if_occurs: 3.68  # letters
    time_to_recovery: 1-2  # visits
```

#### 3. Risk Stratification
```yaml
# Cumulative risk of significant vision loss
gap_duration_risk:
  3_months:
    risk_5_letter_loss: 0.188
    risk_10_letter_loss: 0.063
  6_months:
    risk_5_letter_loss: 0.299
    risk_10_letter_loss: 0.150
  12_months:
    risk_5_letter_loss: 0.518
    risk_10_letter_loss: 0.335
```

### Comparison with Planned Discontinuation (Aslanis)

| Aspect | COVID Gaps (Unplanned) | Aslanis (Planned at 12 weeks) |
|--------|------------------------|-------------------------------|
| Context | Good VA, forced interruption | Stable disease, monitored |
| VA at gap start | 64.4 letters (mean) | Stable at discontinuation |
| VA loss pattern | Immediate, continuous | Peak at 4-6 months |
| Recovery | Partial (50-55%) | Full with prompt retreatment |
| Monitoring | None during gap | Every 2 months |

### Integration with Aflibercept 2mg Protocol

#### 1. Unplanned Discontinuation Categories
Unlike the planned discontinuation rules in our protocol, we should add:

```yaml
unplanned_discontinuation_scenarios:
  covid_like_short_gap:
    duration: 90-180 days
    prevalence: 0.094  # 9.4% in COVID era
    va_impact: -5.9 letters net
    recovery_potential: 0.505
    
  covid_like_long_gap:
    duration: 180-365 days
    prevalence: 0.025  # 2.5% in COVID era
    va_impact: -8.1 letters net
    recovery_potential: 0.554
```

#### 2. Modified Vision Change Model for Gaps

For gaps beyond normal treatment intervals:
```yaml
vision_change_gap_modifier:
  # Applied when interval exceeds max_interval_days
  gap_90_180_days:
    additional_loss: -1.78  # On top of untreated disease progression
    monthly_rate: -0.47
  gap_180_365_days:
    additional_loss: -6.83
    monthly_rate: -0.81
```

### Key Insights for Simulation

1. **Gap consequences are severe but not catastrophic**: Unlike complete vision loss scenarios, most patients retain functional vision even after long gaps.

2. **Recovery is partial**: About half of patients show some improvement when treatment resumes, but full recovery to pre-gap levels is rare.

3. **Time sensitivity**: The 3-6 month window is critical - risk of significant loss doubles between 3 and 6 months.

4. **Real-world resilience**: Even with 11.9% experiencing significant gaps, the overall cohort maintained reasonable outcomes, suggesting robustness of aflibercept treatment.

5. **Monitoring matters**: The worse outcomes compared to Aslanis likely reflect lack of monitoring during unplanned gaps vs. planned discontinuation with regular follow-up.

### Recommendations for Protocol Implementation

1. **Add unplanned gap scenarios** to complement planned discontinuation rules
2. **Use time-dependent VA loss rates** rather than fixed values
3. **Model partial recovery** when treatment resumes
4. **Consider gap duration** in retreatment response modeling
5. **Adjust expectations** for real-world vs. trial settings (COVID showed ~12% gap rate)

This analysis provides robust, real-world parameters for modeling the unfortunately common scenario of treatment interruption, complementing our existing evidence base from controlled trials.