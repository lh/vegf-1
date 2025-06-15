# Disease Transition Model: Time-Based vs Visit-Based Probabilities

## The Current Issue

Our simulation currently applies disease state transition probabilities **per visit**, but this creates a fundamental modeling problem when visit intervals vary (as they do in treat-and-extend protocols).

### Example of the Problem

If we have a 10% probability of disease progression "per visit":

- **Patient A** (active disease, 4-week intervals):
  - 13 visits/year × 10% = 130% annual progression (impossible!)
  - Actual progression events: ~1.3/year

- **Patient B** (stable disease, 16-week intervals):
  - 3 visits/year × 10% = 30% annual progression
  - Actual progression events: ~0.3/year

This means Patient A appears to have 4x higher disease progression simply because they're seen more often - which is backwards! In reality, Patient A is seen more often BECAUSE their disease is active.

## Why This Matters

1. **Biological Reality**: Disease progression happens continuously, not just when we observe it
2. **Treatment Paradox**: More frequent visits (usually indicating worse disease) paradoxically lead to more transition opportunities
3. **Parameter Estimation**: Clinical data often reports monthly or annual rates, not per-visit rates
4. **Treat-and-Extend Impact**: The protocol's variable intervals (4-16 weeks) magnify this issue

## Proposed Solution: Time-Based Transitions

### Option 1: Continuous Monthly Updates
- Apply transitions every simulated month regardless of visits
- Visits only affect treatment decisions, not disease progression
- Most biologically accurate

### Option 2: Interval-Adjusted Probabilities
Calculate the cumulative probability over the actual interval:
```
P(transition over interval) = 1 - (1 - monthly_rate)^(interval_days/30)
```

Example:
- Monthly progression rate: 3%
- 4-week interval: 1 - (1 - 0.03)^(28/30) = 2.8%
- 16-week interval: 1 - (1 - 0.03)^(112/30) = 10.7%

### Option 3: Time-Scaled Lookup Tables
- Define transition probabilities for standard intervals (4, 6, 8, 12, 16 weeks)
- Interpolate for non-standard intervals
- Based on clinical data at those specific intervals

## Implementation Considerations

1. **Parameter Re-estimation**: Need to convert existing per-visit probabilities to monthly rates
2. **Clinical Validation**: Ensure the time-based model matches observed progression patterns
3. **Treatment Effects**: Should also be time-adjusted (drug efficacy wanes over time)
4. **Backward Compatibility**: May need migration path for existing protocols

## Impact on Current Protocols

All existing protocol files would need updating:
- Current: `disease_transitions` with per-visit probabilities
- New: `disease_transitions` with monthly probabilities + calculation method

## Next Steps

1. Review clinical literature for monthly/annual progression rates
2. Implement time-based transition calculations in disease model
3. Create migration tool for existing protocols
4. Validate against real-world outcomes

## Other Issues to Address

### Discontinuation Types
The protocol files define discontinuation types (planned, adverse, ineffective) but these are not currently used in the simulation logic:
- All discontinuations are marked as "planned" regardless of the actual reason
- The discontinuation_types field in protocols is not referenced by the simulation engine
- Consider implementing different behaviors for different discontinuation types:
  - Adverse events might prevent retreatment
  - Ineffective treatment might trigger protocol changes
  - Planned discontinuations might allow retreatment after a period

### Baseline Vision Distribution
Current protocols assume normal distribution for baseline vision, but UK data (2,029 patients) shows:
- **Actual mean**: 58.36 letters (not 70) at first treatment
- **Best fit**: Beta distribution (not normal) with threshold effect
- **Negative skew**: -0.72 due to NICE treatment threshold at 70 letters
- **51.6% of patients** present in the 51-70 letter range
- **20.4% measure >70** at first treatment despite all qualifying ≤70 at funding

Key insight: The baseline vision data is from **first treatment**, not funding decision:
- All patients qualified with ≤70 letters for funding
- Measurement variability (±5 letters) causes some to measure >70 at treatment
- Regression to mean effects
- Time delays between funding and treatment
- Possible measurement bias at funding assessment

Should update:
1. Protocol baseline vision parameters to reflect actual UK data
2. Implement Beta distribution with threshold effect:
   - Natural disease progression: Beta(α=3.5, β=2.0) on [5,98]
   - 60% reduction in density above 70 (funding filter effect)
   - Add measurement noise to model funding→treatment variability
3. Default mean from 70 to 58.36 letters
4. Consider modeling the funding decision → first treatment process explicitly

---

**Created**: 2025-06-15  
**Status**: To be addressed  
**Priority**: High - affects simulation validity