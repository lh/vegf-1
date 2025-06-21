# Long-Term Outcomes in nAMD Treatment: Literature Summary

## Overview

This document summarizes the available evidence on long-term outcomes (>2 years) for nAMD treatment across different protocols, based on clinical trials and real-world evidence.

## Key Long-Term Studies

### 1. Spooner et al. Meta-Analysis (10 years, 2023)
- **Scope**: 1,125 patients across multiple studies
- **Mean follow-up**: 98.4 months
- **Key findings**:
  - Mean vision change: -8.11 letters from baseline at 10 years
  - Total injections: 41.11 over 10 years
  - Attrition: 54-92% lost to follow-up
  - Macular atrophy: 49% of eyes

### 2. Chandra et al. UK Database Study (5 years)
- **Scope**: Real-world electronic medical records
- **Key findings**:
  - Year 1: +4.3-4.4 letters gain
  - Year 5: -2.9 letters from baseline
  - Progressive decline after initial gains

### 3. Fight Retinal Blindness Registry (3+ years)
- **Scope**: International real-world registry
- **Key findings**:
  - Similar outcomes for ranibizumab and aflibercept
  - Median 18 injections over 3 years
  - 43-51% eyes with active CNV at 3 years

## Vision Trajectory Over Time

### Typical Pattern
1. **Loading Phase (0-3 months)**: Rapid improvement
2. **Year 1**: Peak vision gains (6-10 letters)
3. **Years 2-3**: Plateau or slight decline
4. **Years 4-5**: Return to near baseline
5. **Years 6-10**: Progressive decline below baseline

### Protocol-Specific Trajectories

#### Fixed Interval (VIEW Extended)
- Year 1: +8.4 letters (trial data)
- Year 2: +7-8 letters (estimated)
- Year 5: +2-3 letters (projected)
- Year 10: -5 to -8 letters (projected)

#### Treat-and-Extend
- Year 1: +6-8 letters (real-world)
- Year 2: +5-6 letters
- Year 5: 0 to -2 letters
- Year 10: -6 to -10 letters

#### PRN (As-Needed)
- Year 1: +3-5 letters
- Year 2: +1-2 letters
- Year 5: -5 to -8 letters
- Year 10: -10 to -15 letters

## Injection Frequency Patterns

### Year-by-Year Breakdown
- **Year 1**: 6-8 injections (protocol-dependent)
- **Year 2**: 4-6 injections
- **Years 3-5**: 4-5 injections/year
- **Years 6-10**: 3-4 injections/year

### Cumulative Totals
- **2 years**: 10-14 injections
- **5 years**: 25-30 injections
- **10 years**: 40-45 injections (persistent patients)

## Discontinuation and Attrition

### Reasons for Discontinuation
1. **Death**: 14-52% (varies by study duration)
2. **Futility/Poor response**: 20%
3. **Patient decision**: 9%
4. **Transfer of care**: 30%
5. **Stable disease**: 5-10%

### Attrition Timeline
- **Year 1**: 10-15% discontinuation
- **Year 2**: 50% cumulative
- **Year 5**: 70-80% cumulative
- **Year 10**: 85-95% cumulative

## Anatomic Changes Over Time

### Central Macular Thickness
- Initial reduction: -100 to -150 μm
- Sustained through 10 years in treated eyes
- Mean at 10 years: -115.54 μm from baseline

### Macular Atrophy Development
- **Year 2**: 10-15% of eyes
- **Year 5**: 25-35% of eyes
- **Year 10**: 49% of eyes
- Associated with both disease and treatment

### Fibrosis and Scarring
- Develops in 30-50% of eyes by 10 years
- More common with higher disease activity
- Associated with worse visual outcomes

## Factors Affecting Long-Term Outcomes

### Positive Predictors
1. **Higher injection frequency**: +0.46 letters per injection over 10 years
2. **Continuous treatment**: No interruptions in first 2 years
3. **Good initial response**: Gaining ≥5 letters in first 3 months
4. **Lower baseline age**: Younger patients maintain gains longer
5. **T&E vs PRN**: +3.72 letters advantage for T&E

### Negative Predictors
1. **Treatment gaps**: Any gap >6 months
2. **Poor initial response**: <5 letter gain at 3 months
3. **Baseline factors**: Large lesion size, hemorrhage
4. **Development of atrophy**: Progressive vision loss
5. **Low injection frequency**: <4 per year after Year 1

## Implications for Simulation

### Key Parameters to Model
1. **Vision trajectory**: Non-linear decline after peak
2. **Injection frequency**: Gradual reduction over time
3. **Attrition rates**: Exponential increase
4. **Atrophy development**: Time-dependent probability
5. **Response heterogeneity**: Maintained throughout

### Protocol-Specific Considerations

#### Fixed/"Treat-and-Treat"
- Predictable injection schedule maintained
- Vision outcomes depend on matching disease activity
- Lower attrition due to predictability
- Risk of overtreatment in stable eyes

#### Treat-and-Extend
- Individualized intervals increase over time
- Better matching of treatment to disease
- Higher monitoring burden may increase attrition
- Optimal for maintaining long-term gains

#### PRN
- Lowest injection counts
- Consistently worse outcomes
- Highest risk of undertreatment
- Not recommended for long-term management

## Recommendations for Model Calibration

1. **Use stepped vision trajectory**: Different slopes for Years 1, 2-5, and 6-10
2. **Model atrophy as separate process**: Affects ~50% by 10 years
3. **Include realistic attrition**: 50% by 2 years, 90% by 10 years
4. **Adjust injection frequency**: Decline from Year 1 peak
5. **Account for survivor bias**: Persistent patients have better outcomes

---

*Sources*: Spooner et al. 2023, Chandra et al., Fight Retinal Blindness Registry, VIEW long-term extension studies