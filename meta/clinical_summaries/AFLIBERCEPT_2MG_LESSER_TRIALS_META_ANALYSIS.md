# Aflibercept 2mg Lesser Trials Meta-Analysis
## Synthesis of Real-World and Smaller RCT Evidence

### Executive Summary

This meta-analysis synthesizes data from three "lesser" trials alongside pivotal studies to refine aflibercept 2mg T&E parameters:

1. **FRB! Registry (2024)**: Real-world international data (n=3,313) showing lower gains but higher treatment burden
2. **Maruko et al. (2020)**: Japanese 2-year prospective study (n=97) with conservative 12-week maximum
3. **HAGA et al. (2018)**: Small Japanese RCT (n=41) comparing TAE vs fixed dosing

### Key Findings Across Studies

| Study | Design | Sample | Max Interval | VA Gain | Injections/2yr | Key Insight |
|-------|--------|--------|--------------|---------|----------------|-------------|
| ALTAIR | RCT | 247 | 16 weeks | +6.1-7.6 | 10.4 | Gold standard T&E |
| FRB! | Real-world | 3,313 | ~10 weeks | +4.2 | 14.9 | Real-world gap |
| Maruko | Prospective | 97 | 12 weeks | +6.5 | 13.0 | Conservative success |
| HAGA | RCT | 41 | 12 weeks | +13-16 | ~15 | High PCV response |

### Real-World vs RCT Performance Gap

**Visual Acuity**:
- RCTs: +6-8 letters (typical range)
- Real-world: +4.2 letters (FRB! registry)
- Exception: +13-16 letters (HAGA - likely PCV effect)

**Treatment Burden**:
- RCTs: 10.4 injections/2 years (ALTAIR)
- Real-world: 14.9 injections/2 years (FRB!)
- Conservative protocols: 13.0 injections/2 years (Maruko)

**Extension Achievement**:
- ALTAIR: 41-46% reach 16-week intervals
- FRB!: Maximum ~10 weeks in practice
- Maruko: 60.8% at 12-week intervals
- HAGA: 76% achieve optimal 7 injections/year

### Disease State Transition Insights

**Extension Success Patterns**:
1. **Early Extenders**: 50-60% achieve extension after loading
2. **Stability Maintenance**: 
   - 51% maintain if extended early (Maruko)
   - 80-85% per interval in ALTAIR
3. **Late Achievers**: Additional 10-15% extend in year 2

**Real-World Discontinuation**:
- 28-33% discontinue by 2 years (FRB!)
- Higher than RCT completion rates

### Protocol Variation Effects

**Maximum Interval Impact**:
- 16 weeks (ALTAIR): 41-46% achieve, 10.4 total injections
- 12 weeks (Maruko/HAGA): 60-76% achieve, 13-15 injections
- ~10 weeks (FRB! real-world): Reflects practical limitations

**Adjustment Increments**:
- 2-4 weeks (ALTAIR): Standard approach
- 1 month (Maruko): More conservative, similar outcomes
- Both achieve comparable visual gains

### Population-Specific Considerations

**Japanese Studies (High PCV)**:
- PCV prevalence: 36-76% vs ~10% Western
- Higher visual gains in some studies
- More predictable response patterns
- Consider separate parameters for Asian populations

**International Real-World**:
- Mixed pathology types
- Greater variability in outcomes
- Higher loss to follow-up
- More conservative extension patterns

### Simulation Parameter Recommendations

**For Base Case (Mixed Population)**:
```yaml
# Visual outcomes (2-year horizon)
vision_gain_rct: 6-8 letters
vision_gain_real_world: 4-5 letters
adjustment_factor: 0.6-0.7  # Real-world/RCT ratio

# Treatment patterns
initial_extension_rate: 55-60%  # After loading
max_interval_achievement: 
  rct_protocol: 40-45%  # 16 weeks
  conservative: 60-65%  # 12 weeks
  real_world: 25-30%   # 10+ weeks

# Injection burden (2 years)
injections_optimal: 10-11
injections_typical: 13-15
injections_intensive: 16-18
```

**For Sensitivity Analysis**:
1. **Optimistic**: Use ALTAIR parameters (16-week max, 10.4 injections)
2. **Base Case**: Blend ALTAIR transitions with FRB! outcomes
3. **Conservative**: Use Maruko protocol (12-week max, 13 injections)
4. **Real-World**: Apply FRB! registry patterns

### Key Modeling Insights

1. **Protocol Flexibility**: Similar visual outcomes achievable with 12-week or 16-week maximum intervals
2. **Real-World Adjustment**: Expect 30-40% reduction in visual gains and 40-50% increase in injection frequency
3. **Early Response Predicts Success**: 50%+ who extend early maintain extension
4. **Discontinuation Planning**: Budget for 30% discontinuation by 2 years in real-world settings

### Data Quality and Confidence

| Parameter | Confidence | Rationale |
|-----------|------------|-----------|
| RCT outcomes | High | Multiple studies, consistent findings |
| Real-world gap | High | Large FRB! registry validates |
| Extension patterns | Medium-High | Varies by protocol and population |
| Population differences | Medium | Limited Western vs Asian comparisons |
| Long-term sustainability | Medium | Most data ≤2 years |

### Recommendations for Protocol Implementation

1. **Use ALTAIR transitions** as base (most robust data)
2. **Apply real-world adjustment factors** from FRB! for resource planning
3. **Consider protocol variations** for sensitivity analysis
4. **Model population-specific parameters** if high PCV prevalence
5. **Include 28-33% discontinuation** for realistic 2-year projections
6. **Document assumptions** about maximum interval achievability

This meta-analysis demonstrates that while RCT protocols show what's possible, real-world evidence reveals what's practical. The synthesis supports our current parameter choices while highlighting areas for sensitivity testing.