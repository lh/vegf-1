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

---

**Created**: 2025-06-15  
**Status**: To be addressed  
**Priority**: High - affects simulation validity