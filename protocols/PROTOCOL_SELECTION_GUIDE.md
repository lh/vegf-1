# Aflibercept 2mg Protocol Selection Guide

## Available Protocols

### 1. Standard Protocol: `aflibercept_2mg_treat_and_extend.yaml`
- **Use for**: Modeling best practice scenarios, comparative effectiveness, health economics evaluations
- **Characteristics**:
  - Based on RCT evidence and real-world registries
  - Includes appropriate medical discontinuations only
  - Models external disruptions (e.g., pandemics) but NOT clinical errors
  - Gap prevalence: ~12% (external factors only)

### 2. SASH-Specific Protocol: `aflibercept_2mg_treat_and_extend_sash.yaml`
- **Use for**: Real-world modeling in settings with identified clinical education gaps
- **Characteristics**:
  - Includes all standard protocol features PLUS
  - Models inappropriate clinical discontinuations (1.3% rate)
  - Reflects local practice patterns including:
    - "Too good to stop" errors (0.4%)
    - "Course complete" misconceptions (0.2%)
    - "Good enough" early stops (0.24%)
    - "Plateau" misinterpretations (0.2%)
  - Total gap prevalence: ~13.5% (external + clinical errors)

## Key Differences

| Aspect | Standard Protocol | SASH Protocol |
|--------|------------------|---------------|
| Discontinuation types | Medical only | Medical + Clinical errors |
| Gap prevalence | 11.9% | 13.5% |
| Mean VA outcomes | Better | Worse (due to errors) |
| Use case | Ideal practice | Real-world with education gaps |

## Selection Criteria

**Choose Standard Protocol when:**
- Modeling optimal clinical practice
- Comparing drug effectiveness
- Submitting for regulatory/reimbursement decisions
- Assuming well-trained clinical teams

**Choose SASH Protocol when:**
- Modeling real-world outcomes in your specific setting
- Planning resource allocation with realistic assumptions
- Evaluating impact of clinical education programs
- Accounting for known practice variations

## Both Protocols Include:

1. **Evidence-based gap consequences**:
   - Short gaps (3-6 months): -5.9 letters net
   - Long gaps (6-12 months): -8.1 letters net
   - VA loss rate: 0.47-0.81 letters/month during gaps

2. **Core clinical parameters**:
   - Same disease transitions (ALTAIR-based)
   - Same vision outcomes (VIEW-based)
   - Same T&E extension rules

3. **Recovery modeling**:
   - 50-55% show partial recovery after gaps
   - Recovery is incomplete

## Implementation Note

The SASH protocol's clinical error rates (1.3%) represent a specific point in time and location. As clinical education improves, these rates should decrease. Consider:
- Periodic re-evaluation of error rates
- Gradual transition toward standard protocol as practice improves
- Using the gap between protocols to measure education program impact

## Summary

The dual-protocol approach allows for:
- **Benchmarking**: Compare actual (SASH) vs optimal (Standard) outcomes
- **Education impact**: Quantify the cost of clinical misunderstanding
- **Realistic planning**: Use SASH for budgeting, Standard for aspirational targets