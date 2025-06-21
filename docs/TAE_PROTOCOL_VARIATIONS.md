# Treat-and-Extend Protocol Variations

## Overview

T&E protocols can vary significantly in their minimum interval constraints, which impacts patient outcomes. This document outlines the key variations and their clinical implications.

## Protocol Variations

### 1. Standard T&E (Literature/Label)
- **Minimum interval**: 4 weeks (28 days)
- **Maximum interval**: 16 weeks (112 days)
- **Extension/shortening**: 2-week increments
- **Patients needing <8 weeks**: ~23%
- **Expected outcomes**: 
  - Year 1: 6-8 letters gain
  - Can optimize treatment for all patient types

### 2. NHS T&E (Resource-Constrained)
- **Minimum interval**: 8 weeks (56 days) after loading
- **Maximum interval**: 16 weeks (112 days)
- **Extension/shortening**: 2-week increments
- **Impact**: May undertreat ~23% of patients
- **Expected outcomes**:
  - Year 1: 5-7 letters gain (slightly lower)
  - Better resource utilization

### 3. Fixed Interval/"Treat-and-Treat"
- **Fixed interval**: 8 weeks throughout
- **No adjustments**: Same schedule for all
- **Monitoring**: Only 2-3 visits/year
- **Expected outcomes**:
  - Year 1: 8-9 letters gain (if well-calibrated)
  - May overtreat stable patients
  - May undertreat active patients

## Clinical Impact of Interval Constraints

### Patients Requiring <8 Week Intervals

Based on ARIES post-hoc analysis:
- **23%** need at least one interval <8 weeks
- **5.7-7.7%** maintained at <8 weeks at Week 104
- **Distribution of intensive patients**:
  - 4-week intervals: 20.6%
  - 6-week intervals: 32.4%
  - 8-week intervals: 47%

### Outcomes by Minimum Interval

#### 4-Week Minimum (Full Flexibility)
- Allows optimization for highly active disease
- ~50% of resistant patients achieve fluid resolution when shortened to 4 weeks
- Best visual outcomes for the ~23% who need it

#### 8-Week Minimum (NHS Constraint)
- Adequate for ~77% of patients
- May result in persistent fluid for ~23%
- Potential vision loss of 1-2 letters vs optimal

## Modeling Implications

### For Calibration
1. **Standard T&E**: Model full range (4-16 weeks)
2. **NHS T&E**: Model with 8-week floor
3. **Compare outcomes**: Expect 0.5-1.5 letter difference

### Disease State Considerations
- Patients in HIGHLY_ACTIVE state may need 4-6 week intervals
- NHS protocol may keep more patients in ACTIVE state longer
- Consider separate calibration for each variant

### Real-World Factors
- Patient preference for less frequent visits
- Travel burden favoring longer intervals
- Resource constraints driving toward 8+ weeks
- Clinical need for flexibility in active disease

## Recommendations

### For Standard T&E Calibration
- Allow full 4-16 week range
- Model ~23% needing <8 weeks temporarily
- Target 6-7 letters Year 1 gain

### For NHS T&E Calibration
- Enforce 8-week minimum after loading
- Expect slightly worse outcomes for active patients
- Target 5-6 letters Year 1 gain

### For Fixed Interval Comparison
- Use as "simple but effective" benchmark
- Compare resource utilization
- Assess over/undertreatment rates

## Key Takeaway

The ability to use intervals shorter than 8 weeks is clinically important for approximately 1 in 4 patients. While NHS constraints of 8-week minimum intervals are practical from a resource perspective, they may result in suboptimal outcomes for patients with highly active disease. This trade-off should be explicitly modeled in our simulations.