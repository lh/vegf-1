# Eylea Patient Mortality Analysis Summary

## Executive Summary

Analysis of real-world Eylea (aflibercept) patient data reveals important mortality patterns that should be incorporated into simulation models for accurate representation of patient outcomes.

## Dataset Overview

- **Total patients**: 1,775
- **Total records**: 23,962 injections
- **Study period**: November 2007 to February 2025 (17.2 years)
- **Average follow-up**: 2.4 years per patient

## Key Mortality Findings

### Overall Mortality Rates

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Cumulative mortality | 18.5% | 328 of 1,775 patients died during study |
| Annual mortality rate | 7.8 per 100 patient-years | Most accurate measure accounting for follow-up time |
| Average age at death | 89.5 years | Range: 70-106 years |

### Mortality by Treatment Pattern

Treatment continuity shows strong correlation with mortality risk:

| Treatment Pattern | Interval Between Injections | Mortality Rate | Relative Risk |
|-------------------|----------------------------|----------------|---------------|
| Regular treatment | <90 days | 20.7% | Baseline |
| Short gaps | 90-180 days | 25.3% | +22% |
| Long gaps | 180-365 days | 27.8% | +34% |
| Discontinued | >365 days | 28.4% | +37% |

### COVID-19 Period Analysis

**Important caveat**: Without actual death dates, we used last injection date as a proxy, which creates significant limitations.

| Period | Timeframe | Observed Mortality Rate | vs. Baseline |
|--------|-----------|------------------------|--------------|
| Pre-COVID baseline | Jan 2018 - Feb 2020 | 11.4% | - |
| Early COVID | Mar - Aug 2020 | 2.6% | -76.8% |
| Peak COVID | Sep 2020 - Feb 2021 | 5.2% | -54.5% |
| Late COVID | Mar - Dec 2021 | 6.9% | -39.5% |
| Post-COVID | Jan 2022 - Dec 2023 | 10.6% | -6.3% |

**Note**: The apparent reduction in mortality during COVID likely reflects survivorship bias - we only captured patients who continued treatment. Those who discontinued care (and potentially died) are not reflected in these period-specific rates.

## Implications for Simulation Models

### Recommended Parameters for Protocols

1. **Base mortality rate**: 7.8% per year (0.65% per month)
   
2. **Age-adjusted mortality**: Consider implementing age-based mortality given:
   - Average age at death: 89.5 years
   - Patient age range at death: 70-106 years

3. **Treatment-gap mortality multipliers**:
   - Regular treatment (<90 days): 1.0x
   - Short gaps (90-180 days): 1.22x
   - Long gaps (180-365 days): 1.34x
   - Discontinued (>365 days): 1.37x

### Protocol Implementation Example

```yaml
# Example addition to protocol YAML files
mortality:
  base_annual_rate: 0.078  # 7.8% per year
  age_adjustment:
    enabled: true
    reference_age: 89.5
    # Mortality doubles every X years from reference
    doubling_time: 8  
  treatment_gap_multipliers:
    regular: 1.0      # <90 days
    short_gap: 1.22   # 90-180 days
    long_gap: 1.34    # 180-365 days
    discontinued: 1.37 # >365 days
```

## Recommendations

1. **Update simulation models** to include mortality as a competing risk to vision loss
2. **Consider age-specific mortality** rates rather than a flat rate
3. **Model increased mortality risk** for patients with treatment interruptions
4. **Account for survivorship bias** when modeling long-term outcomes
5. **Validate against real-world data** by comparing simulated mortality to observed rates

## Data Limitations

- No actual date of death available (only binary deceased status)
- Mortality timing estimated from last injection date
- Potential underestimation of mortality for discontinued patients
- COVID period analysis should be interpreted with caution

## Next Steps

1. Incorporate mortality parameters into existing protocol specifications
2. Update simulation engines (ABS and DES) to handle mortality events
3. Validate mortality modeling against known population statistics
4. Consider sensitivity analyses around mortality assumptions