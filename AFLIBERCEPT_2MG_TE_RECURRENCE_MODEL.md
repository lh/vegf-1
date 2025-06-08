# Aflibercept 2mg Treat-and-Extend and Recurrence Model
## Meta-analysis of ALTAIR and Aslanis Data

### Overview
This model combines:
1. **ALTAIR**: T&E transitions up to 16-week intervals (96 weeks)
2. **Aslanis**: Recurrence after discontinuation at stable 12-week intervals (52 weeks)

### Disease Activity Continuum

| Interval | Disease State | Activity Level | Data Source |
|----------|--------------|----------------|-------------|
| <8 weeks | HIGHLY_ACTIVE | High recurrence | Clinical judgment |
| 8 weeks | ACTIVE | Moderate activity | ALTAIR baseline |
| 10-14 weeks | ACTIVE→STABLE | Improving | ALTAIR transitions |
| 16 weeks | STABLE | Minimal activity | ALTAIR (41-46% achieve) |
| Discontinued | STABLE_OFF | No treatment | Aslanis (52.9% recur at 12 months) |

### Unified Transition Probabilities

#### 1. On-Treatment Transitions (ALTAIR-based)

**From STABLE (≥12 week intervals):**
- Remain STABLE: 80-85% per interval
- Drop to ACTIVE (<12 weeks): 10-15% per interval
- Drop to HIGHLY_ACTIVE (<8 weeks): 5-10% per interval

**Key insight**: 15-20% lose extended interval status per decision point

#### 2. Extension Success Rates (ALTAIR)

| Time Point | Achieving ≥12 weeks | Achieving 16 weeks |
|------------|--------------------|--------------------|
| Week 16 | ~25% | 0% |
| Week 52 | 42-50% | 0-41% |
| Week 96 | 57-60% | 41-46% |

#### 3. Recurrence Model (Bridging 16-52 weeks)

**Assumptions**:
- ALTAIR shows 41-46% maintain 16-week intervals through 96 weeks
- Aslanis shows 52.9% recurrence at 12 months after discontinuation from 12-week intervals
- The difference suggests higher recurrence risk after complete discontinuation

**Proposed Annual Recurrence Rates**:

| Scenario | Annual Recurrence Rate | Source/Rationale |
|----------|------------------------|------------------|
| On T&E at 16 weeks | 15-20% | ALTAIR implicit rate |
| Discontinued from 12 weeks | 52.9% | Aslanis direct observation |
| Discontinued from 16 weeks | ~45% | Interpolated (more stable than 12-week) |

### Time-Dependent Recurrence Curve (Aslanis)

| Months Post-Discontinuation | Cumulative Recurrence | Monthly Rate |
|----------------------------|----------------------|--------------|
| 0-4 months | 13% | 3.25%/month |
| 4-6 months | 33% | 10%/month |
| 6-8 months | 46% | 6.5%/month |
| 8-10 months | 51% | 2.5%/month |
| 10-12 months | 54% | 1.5%/month |

**Key pattern**: Peak recurrence at 4-6 months, then declining rate

### Integrated Model for Simulation

#### For Active Treatment (T&E):
```
If interval ≥ 16 weeks:
  - 80% remain stable per interval
  - 15% drop to 10-14 weeks
  - 5% drop to <10 weeks

If interval 12-14 weeks:
  - 35% extend further
  - 55% maintain
  - 10% shorten
```

#### For Treatment Discontinuation:
```
If discontinuing from stable disease (≥12 weeks for 3+ visits):
  - Use Aslanis time-dependent curve
  - 54% cumulative recurrence at 12 months
  - Peak risk at 4-6 months
```

### Vision Outcomes

| Scenario | Vision Change | Source |
|----------|--------------|---------|
| Maintained at 16 weeks | +0.5 to +1.0 letters/year | ALTAIR year 2 |
| Recurrence on T&E | -0.5 to -1.0 letters | ALTAIR reduction data |
| Recurrence after discontinuation | -3.6 letters | Aslanis |
| After retreatment | Return to baseline | Aslanis |

### Implementation Notes

1. **Decision intervals**: Every 8-16 weeks based on current interval
2. **Extension criteria**: No fluid on OCT + stable/improved VA
3. **Reduction triggers**: New/increased fluid or VA loss
4. **Discontinuation criteria**: Stable at ≥12 weeks for 3 consecutive visits
5. **Monitoring after discontinuation**: Every 2 months for first year

### Data Quality Assessment

| Parameter | Confidence | Source |
|-----------|------------|---------|
| T&E transitions | High | ALTAIR RCT data |
| 16-week maintenance | High | 41-46% in ALTAIR |
| Discontinuation recurrence | High | Aslanis prospective |
| Bridging assumptions | Medium | Interpolated |
| Vision recovery | Medium | Limited sample size |

### Key Insights for Modeling

1. **Disease activity is continuous**: From highly active (<8 weeks) to stable off treatment
2. **Recurrence risk varies by context**: 15-20% on T&E vs 53% after discontinuation
3. **Time-dependent risk**: Peak recurrence at 4-6 months post-discontinuation
4. **Most recurrences are manageable**: Vision returns to baseline with retreatment