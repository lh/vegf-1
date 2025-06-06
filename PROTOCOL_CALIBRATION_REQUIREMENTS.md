# Protocol Calibration Requirements

## Overview

The protocols created define the STRUCTURE of different treatment approaches but require calibration of clinical parameters to match known trial data before simulation.

## Parameters Requiring Calibration

### 1. Disease Transition Probabilities
Each protocol needs state transition matrices calibrated to reproduce:
- Disease activity patterns observed in trials
- Response rates to treatment
- Progression/improvement rates

**Required data sources:**
- Clinical trial publications with state transition data
- Natural history studies for untreated transitions
- Real-world evidence for treated populations

### 2. Vision Change Parameters
Mean and standard deviation of vision changes for each state/treatment combination:
- Loading phase vision gains
- Maintenance phase stability
- Vision loss rates when undertreated
- Natural history decline rates

**Required data sources:**
- BCVA outcomes from relevant trials
- Stratified by disease activity if available
- Time-course data for calibration

### 3. Treatment Effect Multipliers
How treatment modifies natural disease transitions:
- Effect of regular vs irregular dosing
- Impact of extended vs shortened intervals
- Differences between 2mg and 8mg formulations

**Required data sources:**
- Comparative effectiveness trials
- Dose-response studies
- Protocol-specific outcome data

## Specific Calibration Needs by Protocol

### Eylea 8mg Treat-and-Extend
**Have:** PULSAR/PHOTON trial data
- 77-79% maintain extended intervals
- Mean BCVA gain: 6.7 letters at 48 weeks
- Injection counts: 6.1 (q12) and 5.2 (q16) in year 1

**Need:** Parameters that reproduce these outcomes

### Eylea 2mg Treat-and-Extend  
**Need:** AFLIBERCEPT-SPECIFIC trial data
- ALTAIR trial (aflibercept T&E in Japanese patients)
- ARIES study (aflibercept T&E)
- Real-world aflibercept T&E effectiveness data
- NOT ranibizumab or bevacizumab trials

### Eylea 2mg Treat-and-Treat (Fixed)
**Need:** AFLIBERCEPT fixed dosing trial data
- VIEW 1 and VIEW 2 fixed dosing arms (2q4 and 2q8)
- Real-world aflibercept fixed interval outcomes
- NOT CATT (wrong drugs: bevacizumab/ranibizumab)
- NOT IVAN (wrong drugs: bevacizumab/ranibizumab)

## Calibration Process

1. **Identify reference trials** with relevant dosing schedules
2. **Extract key outcomes**:
   - Vision gains/losses over time
   - Proportion maintaining vision
   - Disease activity measures if available
   - Discontinuation rates

3. **Iterative calibration**:
   - Start with reasonable parameter estimates
   - Run simulations
   - Compare outputs to trial results
   - Adjust parameters
   - Repeat until match achieved

4. **Validation**:
   - Test calibrated parameters against different trial
   - Ensure reasonable behavior across scenarios
   - Document parameter sources and rationale

## Documentation Requirements

Each calibrated protocol should include:
```yaml
# Clinical evidence basis
clinical_evidence:
  primary_source: "TRIAL_NAME (Author et al., Year)"
  trial_design: "Description of protocol used"
  key_outcomes:
    bcva_gain_48wk: X.X  # letters
    bcva_sd: X.X
    injections_year1: X.X
    proportion_stable: 0.XX
  
  calibration_targets:
    - "Match mean BCVA gain within 0.5 letters"
    - "Match injection frequency within 0.2 injections"
    - "Reproduce proportion with extended intervals"
```

## Priority Order

1. **Eylea 8mg**: Have good trial data, calibrate first
2. **Eylea 2mg T&E**: Standard of care, multiple data sources
3. **Eylea 2mg Fixed**: Need to identify best reference trials

## Next Steps

1. Literature review for each protocol type
2. Extract calibration targets from trials
3. Implement calibration scripts
4. Document evidence sources in YAML files
5. Validate against independent data