# Fixed Q8W Aflibercept Outcomes: Beyond VIEW Trials

## Executive Summary

While the VIEW 1/2 trials established fixed q8w aflibercept as effective (+7.9 to +8.9 letters at Year 1), real-world studies and alternative protocols provide additional insights into fixed 8-week dosing outcomes.

## Key Studies with Fixed or Near-Fixed Q8W Components

### 1. ALTAIR Study (Japanese Population)
While primarily a T&E study, ALTAIR provides insights on q8w performance:
- **Minimum interval**: 8 weeks (no shorter intervals allowed)
- **Loading phase**: Same as VIEW (3 monthly doses)
- **Key finding**: 50.4-57.7% of patients could NOT extend beyond 8 weeks at Week 16
- **Implication**: ~50% of patients effectively receive fixed q8w dosing in T&E protocols

### 2. Real-World Evidence from FRB! Registry
- **Average maximum interval achieved**: ~70 days (10 weeks)
- **Many patients unable to extend beyond 8-9 weeks**
- **Real-world T&E outcomes**: +4.2 letters at 2 years
- **Comparison**: Lower than VIEW trials but includes all comers

### 3. Conservative T&E (Maruko Study)
- **Protocol**: Slower extensions (1-month increments)
- **Many patients maintained at 8-week intervals**
- **2-year outcome**: +6.5 letters
- **Closer to real-world practice patterns**

### 4. AMD Commissioning Guidance (2024) Insights
- **Real-world observation**: "Less costly but drying effect is not as effective as aflibercept"
- **Faricimab/Aflibercept 8mg**: ~70% achieve ≥12-week intervals
- **Implication**: ~30% remain on shorter intervals (likely 8 weeks)

## Comparison: Fixed Q8W vs Other Approaches

### Visual Outcomes Comparison

| Protocol | Study | Year 1 VA Gain | Year 2 VA Gain | Notes |
|----------|-------|----------------|----------------|-------|
| Fixed q8w | VIEW 1/2 | +7.9 to +8.9 | +6.3 | Gold standard |
| T&E (8-16w) | ALTAIR | +8.5 to +9.0 | +6.1 to +7.6 | Similar to fixed |
| Conservative T&E | Maruko | Not reported | +6.5 | Real-world like |
| Real-world T&E | FRB! | Not reported | +4.2 | All comers |

### Injection Frequency

| Protocol | Year 1 | Year 2 | Total 2 Years |
|----------|--------|--------|---------------|
| Fixed q8w | 7.5 | 6.5 | 14.0 |
| T&E (ALTAIR) | ~7 | ~3.4 | 10.4 |
| T&E (Maruko) | ~8 | ~5 | 13.0 |
| Real-world | ~8 | ~7 | 14.9 |

## Key Insights for Fixed Q8W Performance

### 1. Patient Selection Effects
- **Clinical trials**: Selected patients, high adherence
- **Real-world**: Mixed population, variable adherence
- **~50% "natural" q8w patients**: Cannot extend beyond 8 weeks even with T&E

### 2. Anatomic Stability
From VIEW trials:
- **CRT fluctuations**: 8-17 μm between injections
- **Clinically acceptable**: No impact on vision outcomes
- **Dry retina rates**: 63.4-71.9%

### 3. Long-Term Trajectory
From the aflibercept variations document:
```yaml
# Fixed q8w (VIEW-based)
vision_gain_year1: [8.4, 1.3]  # mean, SD
vision_gain_year2: [6.3, 1.5]
```

### 4. Cost Calculator Assumptions
From the wAMD cost calculator:
- **Year 1**: 6 injections (after loading)
- **Year 2**: 3 injections
- **Assumes 60% optimal responders** who can extend intervals
- **40% suboptimal**: Remain on fixed 8-week intervals

## Clinical Implications

### When Fixed Q8W May Be Preferred
1. **Resource constraints**: Predictable scheduling
2. **Patient factors**: Travel burden, compliance concerns
3. **Disease characteristics**: Moderately active, predictable
4. **System efficiency**: Lower monitoring burden

### Expected Outcomes with Fixed Q8W
Based on aggregated evidence:
- **Year 1**: +7-9 letters (with good adherence)
- **Year 2**: +5-7 letters
- **Long-term**: Gradual decline but better than natural history
- **Injection burden**: Predictable 6-7 per year after loading

### Comparison to Individualized Approaches
- **Vision outcomes**: Similar in first 2 years
- **Injection frequency**: Higher than optimized T&E
- **Monitoring burden**: Much lower (2-3 visits/year vs 8-12)
- **Cost-effectiveness**: Depends on drug cost vs monitoring cost

## Real-World Modifications

### "Treat-and-Treat" Approach
As noted in commissioning guidance:
- Fixed q8w extended indefinitely
- Minimal monitoring (2 visits/year)
- Expected ~85% effectiveness of full T&E
- Practical for resource-constrained settings

### NHS Constraints
- Many T&E protocols constrained to 8-week minimum
- Effectively creates "modified fixed" protocol for active patients
- May explain real-world underperformance vs trials

## Recommendations for Simulation

### Fixed Q8W Parameters
```yaml
protocol_type: fixed_interval
loading_doses: 3
loading_interval: 28  # days
maintenance_interval: 56  # days (8 weeks)

expected_outcomes:
  year1_vision_gain: 
    mean: 8.0
    sd: 1.5
    range: [7.0, 9.0]
  year2_vision_gain:
    mean: 6.0
    sd: 1.5
    range: [5.0, 7.0]
  
  injections_year1: 7.5  # 3 loading + 4.5 maintenance
  injections_year2: 6.5
  
  dry_retina_rate: 0.67  # 67% average
  acceptable_crt_fluctuation: 17  # μm
```

### Patient Stratification
- **Good candidates (60%)**: Achieve stable disease
- **Suboptimal (40%)**: Persistent activity but controlled
- **Poor candidates**: Would need q4-6w (exclude from fixed protocol)

## Conclusion

Fixed q8w aflibercept remains a viable option with:
- **Proven efficacy**: +7-9 letters Year 1 in trials
- **Real-world effectiveness**: +5-7 letters when adherent
- **Lower monitoring burden**: 2-3 visits vs 8-12 for T&E
- **Predictable outcomes**: Suitable for population health planning
- **Trade-off**: May overtreat some, undertreat others

The "treat-and-treat" approach (indefinite fixed q8w) represents a pragmatic balance between efficacy and resource utilization, particularly relevant for NHS settings with capacity constraints.