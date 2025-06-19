# Aflibercept Long-Term Data Summary

## Key Finding: Limited Data Beyond 5 Years
Unlike ranibizumab (SEVEN-UP study provides 7-year data), aflibercept lacks comparable long-term follow-up studies.

## Available Long-Term Studies

### 1. Nishikawa 2019 (4-year, Japan)
- **Sample**: 98 patients, 73 completed (25% dropout)
- **Injections**: Year 1: 7.0±0.1, Years 2-4: 8.0±7.4 total (2.7/year)
- **VA**: Improved to 0.14 logMAR at year 1, stabilized at 0.22 by year 4
- **Key finding**: Bimodal distribution - some need minimal treatment, others continuous

### 2. Kim 2020 (5-year, Moorfields)
- **Sample**: 512 eyes, 66% completed
- **Injections**: Declining from 7.2 (Y1) to 3.8 (Y5), total 24.2±10.6
- **VA**: Final change -2.9±23.4 letters
- **Critical threshold**: ≥5 injections/year needed to maintain gains
- **Dose effect**: ≥20 total injections → 8 letters better VA (p=0.001)

### 3. Gillies 2019 (3-year, FRB Registry)
- **Direct comparison**: No significant difference vs ranibizumab
- **Injections**: ~18.6 over 3 years
- **Attrition**: 43% non-completion by 3 years

### 4. Spooner 2025 (Meta-analysis)
- **Trajectory**: +3.1 letters (Y1), -0.2 (Y3), -2.2 (Y5)
- **Macular atrophy**: 49% by year 10 (all anti-VEGF)
- **Pattern**: Progressive decline from year 2 onwards

## Simulation Parameters Extracted

### Injection Frequencies (Real-World)
| Year | Mean | Range |
|------|------|-------|
| 1 | 7.0 | 6.8-7.7 |
| 2 | 3.3 | 2.5-4.0 |
| 3-5 | 3.2 | 2.7-3.8 |

### Visual Acuity Trajectory
| Year | Mean Change (letters) |
|------|---------------------|
| 1 | +5.5 |
| 2 | +2.0 |
| 3 | +0.5 |
| 4 | -1.0 |
| 5 | -2.9 |

### Discontinuation Rates (Cumulative)
- Year 1: 10-15%
- Year 2: 25-30%
- Year 3: 35-43%
- Year 5: 45-50%

### Disease Progression
- Geographic atrophy: 20% by year 5
- Fibrosis: 15% by year 5
- Treatment resistance: 20-25%

## Critical Gaps for Simulation
1. **No data beyond 5 years** - must extrapolate from ranibizumab
2. **Limited geographic atrophy progression data** specific to aflibercept
3. **Biosimilar impact** unknown (too recent)
4. **Long-term safety profile** incomplete

## Recommendations for ABS Engine
1. Implement bimodal patient phenotypes (low vs high treatment need)
2. Model treatment intensity as primary outcome driver
3. Include time-dependent treatment effectiveness decline
4. Sensitivity analysis essential for years 6-10
5. Validate against: 7.0±0.7 injections Y1, +5.5±2.5 letters Y1, 50-60% retention at 5Y