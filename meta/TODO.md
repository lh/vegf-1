# Technical Debt and Future Improvements

## Overview
This document summarizes key technical debt items and modeling improvements identified during development. For detailed analysis and context, see the referenced documentation files.

## High Priority - Core Modeling Issues

### 1. Time-Based vs Visit-Based Transition Probabilities
**Issue**: Disease state transitions currently occur per-visit, creating unrealistic results when visit intervals vary.

**Impact**: Patients with frequent visits (4-week intervals) appear to have 4x higher disease progression than those with 16-week intervals.

**Details**: See `DISEASE_TRANSITION_MODEL_ISSUE.md` - Section "The Current Issue"

**Required Changes**:
- Convert all transition probabilities from per-visit to monthly rates
- Update disease model to use time-based calculations
- Migrate existing protocol files
- Validate against clinical data

### 2. Baseline Vision Distribution
**Issue**: Protocols assume normal distribution with mean=70, but UK data shows Beta distribution with mean=58.36.

**Impact**: Unrealistic patient populations that don't match UK treatment patterns.

**Details**: See `DISEASE_TRANSITION_MODEL_ISSUE.md` - Section "Baseline Vision Distribution"

**Required Changes**:
- Implement Beta(α=3.5, β=2.0) distribution on [5,98] range
- Add 60% threshold effect above 70 letters (NICE funding filter)
- Model measurement variability between funding decision and first treatment
- Update default protocol parameters

### 3. Discontinuation Types Implementation
**Issue**: Protocol files define discontinuation types (planned, adverse, ineffective) but simulation always uses "planned".

**Impact**: Cannot model different retreatment scenarios or adverse event tracking.

**Details**: See `DISEASE_TRANSITION_MODEL_ISSUE.md` - Section "Discontinuation Types"

**Required Changes**:
- Implement discontinuation type selection logic in simulation engines
- Add different behaviors for each type (e.g., adverse events prevent retreatment)
- Update patient tracking to use appropriate discontinuation types

## Medium Priority - Data Accuracy

### 4. Vision Model Parameters
**Issue**: Vision change parameters should be monthly rates, not per-visit changes.

**Impact**: Same as transition probabilities - visit frequency affects vision outcomes unrealistically.

**Details**: See protocols and `DISEASE_TRANSITION_MODEL_ISSUE.md`

**Required Changes**:
- Convert vision change model to monthly rates
- Update protocols with appropriate values
- Ensure consistent time-based modeling throughout

## Medium Priority - Analysis Features

### 5. Cost Analysis Implementation
**Issue**: No cost tracking or economic analysis in simulations.

**Impact**: Cannot evaluate cost-effectiveness or budget impact.

**Required Changes**:
- Add cost parameters to protocols (injection costs, visit costs, monitoring costs)
- Track cumulative costs per patient
- Implement cost analysis visualizations
- Add cost-effectiveness metrics (cost per QALY, etc.)

### 6. Weekly Clinic Load Analysis
**Issue**: Current analysis shows patient states over time but not weekly clinic workload.

**Impact**: Cannot plan clinic capacity or staffing requirements.

**Required Changes**:
- Calculate visits per week from patient histories
- Create weekly workload visualization
- Show peak/average clinic loads
- Break down by visit types (injection, monitoring, etc.)

### 7. Simulation Comparison Features
**Issue**: Cannot compare results between different simulation runs.

**Impact**: Difficult to evaluate protocol changes or parameter sensitivity.

**Required Changes**:
- Add simulation selection for comparison
- Create side-by-side visualizations
- Implement difference calculations
- Add statistical comparisons between runs

## Low Priority - UI/UX Improvements

### 8. Protocol Manager Tab Persistence
**Issue**: Edit/Save operations reset view to first tab.

**Impact**: Minor user annoyance when editing protocols.

**Details**: See `DISEASE_TRANSITION_MODEL_ISSUE.md` - Section "UI/UX Improvements"

**Potential Solutions**:
- URL query parameters
- Custom JavaScript components
- Wait for Streamlit native support

## Implementation Order

1. **Phase 1**: Time-based transitions (highest impact on validity)
2. **Phase 2**: Baseline vision distribution (affects all simulations)
3. **Phase 3**: Discontinuation types (enables new analyses)
4. **Phase 4**: Cost analysis (economic evaluation)
5. **Phase 5**: Weekly clinic load (operational planning)
6. **Phase 6**: Simulation comparisons (analysis enhancement)
7. **Phase 7**: UI improvements (quality of life)

## Key Files to Review

- `/Users/rose/Code/CC/DISEASE_TRANSITION_MODEL_ISSUE.md` - Detailed technical analysis
- `/Users/rose/Code/CC/protocols/v2/*.yaml` - Current protocol definitions
- `/Users/rose/Code/CC/simulation_v2/core/disease_model.py` - Disease transition implementation
- `/Users/rose/Code/CC/simulation_v2/engines/` - Simulation engines (ABS and DES)
- `/Users/rose/Code/CC/docs/literature/baseline-acuity-analysis.tex` - UK baseline vision data

## Testing Considerations

When implementing these changes:
1. Maintain backward compatibility or provide migration tools
2. Validate against the 2,029 patient UK dataset
3. Ensure ABS and DES engines remain synchronized
4. Document the scientific rationale for all changes

---
**Last Updated**: 2025-06-16
**Next Review**: When starting Phase 1 implementation