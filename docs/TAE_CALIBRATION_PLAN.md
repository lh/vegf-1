# Treat-and-Extend Protocol Calibration Plan

## Current Status

### Problem
The current T&E protocol is severely underperforming:
- **Current**: -5.3 letters vision gain Year 1
- **Target**: +6-8 letters (based on real-world evidence)
- **Gap**: 11-13 letters

### Root Cause Analysis
1. **Disease transitions too pessimistic**: Too many patients remain in ACTIVE/HIGHLY_ACTIVE states
2. **Insufficient treatment effect**: Treatment not adequately improving disease states
3. **Vision parameters not aligned**: Vision changes don't reflect real-world T&E outcomes

## Calibration Targets

### Based on Literature Review

#### Primary Sources
1. **Spooner 2025 Meta-Analysis (10-year)**:
   - TAE outperforms PRN by +3.72 letters
   - Mean Year 1 gain: ~4.3 letters (all protocols)
   - TAE specifically: Better maintained over time

2. **ALTAIR Study (96 weeks)**:
   - Vision gain: +6.1 to +7.6 letters
   - Injections: 10.4 over 2 years (~7 Year 1)
   - 41.5-46.3% achieved 16-week intervals

3. **Real-World FRB Registry**:
   - TAE: +4.2 letters with 14.9 injections over 2 years
   - Shows TAE effectiveness in practice

### Year 1 Targets
- **Vision gain**: 6-7 letters
- **Injections**: 7-8 (after 3 loading doses)
- **Patients stable at 12w+**: 40-45%
- **Vision maintenance** (losing <15 letters): >90%

### Year 2 Targets
- **Vision**: 5-6 letters from baseline
- **Total injections**: 10-11 cumulative
- **Discontinuation**: <15%

## Calibration Strategy

### Phase 1: Adjust Disease Model for T&E

#### Current Issues
- 59% of patients in ACTIVE/HIGHLY_ACTIVE states
- Only achieving 3.7 injections Year 1 (too low)
- Vision declining instead of improving

#### Proposed Changes

1. **Disease State Transitions**
```yaml
disease_transitions:
  NAIVE:
    STABLE: 0.40 → 0.50      # More achieve stability with loading
    ACTIVE: 0.50 → 0.40      # Fewer remain active
    HIGHLY_ACTIVE: 0.10 → 0.10  # Unchanged
    
  STABLE:
    STABLE: 0.85 → 0.88      # Better maintenance on T&E
    ACTIVE: 0.15 → 0.12      # Lower recurrence
    
  ACTIVE:
    STABLE: 0.25 → 0.35      # Better response to treatment
    ACTIVE: 0.65 → 0.55      # More improve
    HIGHLY_ACTIVE: 0.10 → 0.10  # Unchanged
```

2. **Treatment Effect Multipliers**
```yaml
treatment_effect_on_transitions:
  STABLE:
    multipliers:
      STABLE: 1.1 → 1.3      # Stronger maintenance effect
      ACTIVE: 0.9 → 0.7      # Better prevention
      
  ACTIVE:
    multipliers:
      STABLE: 1.8 → 2.5      # Much better improvement
      ACTIVE: 0.9 → 0.7      # Less likely to stay active
      HIGHLY_ACTIVE: 0.8 → 0.5  # Prevent worsening
```

3. **Vision Change Parameters**
```yaml
vision_change_model:
  stable_treated:
    mean: 0.5 → 1.2         # Better maintenance
  active_treated:
    mean: -1.0 → 0.3        # Slight gain even when active
  highly_active_treated:
    mean: -2.0 → -0.5       # Less loss with treatment
```

### Phase 2: Protocol-Specific Adjustments

#### T&E Decision Logic
- Ensure proper extension/shortening based on disease state
- Verify interval adjustments are working correctly
- Check that stable patients reach 12-16 week intervals

#### Clinical Improvements Integration
- Enable response-based vision changes
- Use response heterogeneity (30% good, 50% average, 20% poor)
- Apply loading phase benefits

### Phase 3: Validation Against Multiple Endpoints

1. **Primary Validation**:
   - Year 1 vision: 6-7 letters ✓
   - Year 1 injections: 7-8 ✓
   - Proportion gaining ≥15 letters: ~25% ✓

2. **Secondary Validation**:
   - Better than PRN by 3-4 letters ✓
   - 40%+ reaching 12+ week intervals ✓
   - Realistic long-term trajectory ✓

3. **Cross-Protocol Validation**:
   - Fixed (VIEW): ~8 letters with 8 injections ✓
   - T&E: ~6 letters with 7-8 injections ✓
   - PRN: ~3 letters with 5-6 injections ✓

## Implementation Steps

### Step 1: Create T&E-Specific Protocol File
```bash
cp protocols/v2/eylea_treat_and_extend_v1.0.yaml \
   protocols/v2/eylea_treat_and_extend_calibrated.yaml
```

### Step 2: Apply Parameter Updates
- Update disease transitions
- Enhance treatment effects
- Adjust vision parameters
- Enable clinical improvements

### Step 3: Test with Patient-Time Analysis
```python
# Use the patient-time analysis framework
python calibration/analyze_patient_time_outcomes.py
```

### Step 4: Compare All Protocols
- Run VIEW 2q8 (fixed)
- Run calibrated T&E
- Run PRN (when implemented)
- Verify relative performance

### Step 5: Fine-Tune Based on Results
- If vision too high: Reduce vision parameters by 10-20%
- If injections too low: Check extension logic
- If too many unstable: Adjust disease transitions

## Success Criteria

### Must Have
- [ ] T&E achieves 6-7 letters Year 1
- [ ] T&E shows 7-8 injections Year 1
- [ ] T&E outperforms PRN by 3+ letters
- [ ] All protocols work with same disease model

### Should Have
- [ ] 40%+ patients reach 12-week intervals
- [ ] Year 2 outcomes align with literature
- [ ] Realistic discontinuation rates
- [ ] Appropriate response heterogeneity

### Nice to Have
- [ ] Long-term trajectory matches 10-year data
- [ ] Atrophy development modeled
- [ ] Protocol switching capability

## Next Actions

1. **Immediate**: Implement calibrated T&E protocol file
2. **Today**: Test with patient-time analysis
3. **This Week**: Achieve primary targets
4. **Next Week**: Validate across all protocols

---

*Note*: The key insight is that T&E requires a more optimistic disease model than our current implementation, reflecting the proactive nature of the protocol preventing disease progression rather than just reacting to it.