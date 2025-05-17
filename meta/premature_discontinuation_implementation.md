# Premature Discontinuation Implementation

## Overview

This document describes the implementation of clinician-dependent premature discontinuations in the simulation model. The implementation is based on real-world data analysis that found approximately 14.5% of patients experience premature discontinuations, resulting in an average vision loss of 9.4 letters.

## Implementation Features

1. **Clinician Dependency**: Premature discontinuations are primarily driven by clinician profiles:
   - Adherent clinicians (0.2x multiplier): Rarely trigger premature discontinuations
   - Average clinicians (1.0x multiplier): Occasionally trigger premature discontinuations
   - Non-adherent clinicians (3.0x multiplier): Frequently trigger premature discontinuations

2. **Target Rate Calibration**: The implementation is calibrated to match the observed 14.5% rate from real-world data.

3. **Time-Dependent Factors**: Premature discontinuation probability varies based on treatment duration:
   - Higher in early treatment (first 6 months)
   - Lower after extended treatment (>1 year)

4. **Interval-Dependent Factors**: Probability increases with longer treatment intervals, reflecting the tendency to discontinue patients who appear stable.

5. **Visual Acuity Impact**: The implementation models the observed 9.4 letter average vision loss, with individual variation.

## Configuration Parameters

The enhanced configuration includes the following parameters in the `premature` section:

```yaml
premature:
  min_interval_weeks: 8       # Minimum interval where premature discontinuation might occur
  probability_factor: 1.0     # Base multiplier for discontinuation probability
  target_rate: 0.145          # Target overall premature discontinuation rate (14.5%)
  profile_multipliers:        # Profile-specific multipliers (relative to base rate)
    adherent: 0.2             # Adherent clinicians rarely trigger premature discontinuations
    average: 1.0              # Average clinicians use the base rate
    non_adherent: 3.0         # Non-adherent clinicians are 3x more likely to discontinue prematurely
  mean_va_loss: -9.4          # Mean VA loss in letters (negative value = loss)
  va_loss_std: 5.0            # Standard deviation of VA loss
```

## Implementation Details

### 1. Probability Calculation

The probability of premature discontinuation is calculated using multiple factors:

```
premature_probability = base_probability * prob_factor * profile_multiplier * time_factor * interval_factor
```

Where:
- `base_probability`: Stable max interval probability (e.g., 0.2)
- `prob_factor`: Base multiplier for premature discontinuations (e.g., 1.0)
- `profile_multiplier`: Clinician-specific multiplier (0.2 for adherent, 1.0 for average, 3.0 for non-adherent)
- `time_factor`: 1.5 for first 6 months, 0.7 after 1 year, 1.0 otherwise
- `interval_factor`: Increases with longer intervals, capped at 2.0

### 2. Vision Impact

When a premature discontinuation occurs, the patient's vision is affected:

1. A vision change is drawn from a normal distribution with mean -9.4 letters and standard deviation 5.0 letters
2. The change is applied to the patient's current vision, ensuring it doesn't go below 0
3. The change is tracked in statistics to validate the implementation

### 3. Statistics Tracking

The implementation includes comprehensive tracking:

1. **Overall Premature Rate**: Premature discontinuations as percentage of all discontinuations
2. **Profile-Specific Rates**: Breakdown of premature discontinuations by clinician profile
3. **Vision Impact**: Mean, min, and max vision changes caused by premature discontinuations
4. **Target Rate Validation**: Comparison of actual rate to target rate (14.5%)

## Usage Notes

When using this implementation:

1. The clinician profiles should be configured with appropriate probabilities to achieve the desired distribution in the simulation.

2. To validate the implementation, run a large-scale simulation (1000+ patients) and check the statistics to ensure:
   - Overall premature discontinuation rate is approximately 14.5%
   - Vision impact is approximately -9.4 letters on average
   - Adherent clinicians have substantially fewer premature discontinuations than non-adherent clinicians

3. For maximum realism, use the clinician assignment modes that reflect real-world practice:
   - "fixed" mode: Each patient sees the same clinician throughout treatment
   - "weighted" mode with continuity_of_care: Patients usually see the same clinician with occasional switches

## References

1. The real-world analysis of premature discontinuations is documented in `/meta/premature_discontinuation_analysis.md`.
2. Implementation code is primarily in `enhanced_discontinuation_manager.py`.
3. Configuration file is `/protocols/simulation_configs/enhanced_discontinuation.yaml`.