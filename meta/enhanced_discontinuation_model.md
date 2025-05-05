# Enhanced Discontinuation Model

## Overview

The enhanced discontinuation model extends the existing discontinuation framework to provide a more sophisticated and clinically realistic approach to treatment discontinuation and recurrence in AMD simulations. This model incorporates multiple discontinuation types, time-dependent recurrence probabilities based on clinical data, and clinician variation in protocol adherence.

## Key Features

1. **Multiple Discontinuation Types**
   - Protocol-based (stable at max interval)
   - Administrative (random events like insurance issues)
   - Time-based (after fixed treatment duration)
   - Premature (non-adherence to protocol)

2. **Time-dependent Recurrence**
   - Different recurrence rates based on discontinuation type
   - Time-dependent probability curves based on clinical data
   - Risk factor modifiers (e.g., presence of PED)

3. **Clinician Variation**
   - Different adherence rates to protocol
   - Varying risk tolerance affecting discontinuation decisions
   - Different approaches to retreatment decisions

## Implementation

The enhanced model is implemented through the following components:

1. **EnhancedDiscontinuationManager**: Extends the base DiscontinuationManager to handle multiple discontinuation types and time-dependent recurrence.

2. **Clinician**: Models individual clinician behavior with varying protocol adherence and decision-making characteristics.

3. **ClinicianManager**: Manages a pool of clinicians and handles patient assignment.

## Configuration

The enhanced discontinuation model is configured through a YAML configuration file. Here's an example configuration:

```yaml
# Enhanced discontinuation configuration
discontinuation:
  enabled: true
  
  # Criteria for discontinuation
  criteria:
    # Planned discontinuation (protocol-based)
    stable_max_interval:
      consecutive_visits: 3       # Number of consecutive stable visits required
      probability: 0.2            # Probability of discontinuation when criteria met
      interval_weeks: 16          # Required interval for planned discontinuation
    
    # Unplanned discontinuations - administrative
    random_administrative:
      annual_probability: 0.05    # Annual probability of random discontinuation
    
    # Unplanned discontinuations - time-based
    treatment_duration:
      threshold_weeks: 52         # Weeks of treatment before considering discontinuation
      probability: 0.1            # Probability of discontinuation after threshold
    
    # Premature discontinuation (non-adherence to protocol)
    premature:
      min_interval_weeks: 8       # Minimum interval where premature discontinuation might occur
      probability_factor: 2.0     # Multiplier for discontinuation probability (relative to planned)
  
  # Post-discontinuation monitoring schedules by cessation type
  monitoring:
    planned:
      follow_up_schedule: [12, 24, 36]  # Weeks after discontinuation for follow-up visits
    unplanned:
      follow_up_schedule: [8, 16, 24]   # More frequent monitoring for unplanned cessation
    recurrence_detection_probability: 0.87  # Probability of detecting recurrence if present
  
  # Disease recurrence models
  recurrence:
    # Planned discontinuation (stable at max interval)
    planned:
      base_annual_rate: 0.13      # Annual base recurrence rate (from Arendt)
      cumulative_rates:           # Cumulative rates over time
        year_1: 0.13              # 1-year cumulative rate
        year_3: 0.40              # 3-year cumulative rate
        year_5: 0.65              # 5-year cumulative rate
    
    # Premature discontinuation (before reaching stability at max interval)
    premature:
      base_annual_rate: 0.53      # Annual base recurrence rate (from Aslanis)
      cumulative_rates:
        year_1: 0.53              # 1-year cumulative rate
        year_3: 0.85              # 3-year cumulative rate (estimated)
        year_5: 0.95              # 5-year cumulative rate (estimated)
    
    # Administrative discontinuation
    administrative:
      base_annual_rate: 0.30      # Annual base recurrence rate (estimated)
      cumulative_rates:
        year_1: 0.30              # 1-year cumulative rate
        year_3: 0.70              # 3-year cumulative rate
        year_5: 0.85              # 5-year cumulative rate
    
    # Time-based discontinuation (after fixed duration)
    duration_based:
      base_annual_rate: 0.32      # Annual base recurrence rate (from Artiaga)
      cumulative_rates:
        year_1: 0.21              # 1-year cumulative rate (from Artiaga)
        year_3: 0.74              # 3-year cumulative rate (from Artiaga)
        year_5: 0.88              # 5-year cumulative rate (from Artiaga)
    
    # Risk factors that modify recurrence rates
    risk_modifiers:
      with_PED: 1.54              # Multiplier for recurrence rate if PED is present (74%/48% from Aslanis)
      without_PED: 1.0            # Reference rate
  
  # Treatment re-entry criteria
  retreatment:
    eligibility_criteria:
      detected_fluid: true        # Fluid must be detected
      vision_loss_letters: 5      # Minimum vision loss to trigger retreatment
    probability: 0.95             # Probability of retreatment when eligible

# Clinician configuration
clinicians:
  enabled: true
  
  # Clinician profiles with different adherence characteristics
  profiles:
    # Protocol-adherent "by the book" clinician
    adherent:
      protocol_adherence_rate: 0.95
      probability: 0.25  # 25% of clinicians follow this profile
      characteristics:
        risk_tolerance: "low"      # Affects discontinuation decisions
        conservative_retreatment: true  # More likely to restart treatment
    
    # Average clinician
    average:
      protocol_adherence_rate: 0.80
      probability: 0.50  # 50% of clinicians follow this profile
      characteristics:
        risk_tolerance: "medium"
        conservative_retreatment: false
    
    # Less adherent "freestyle" clinician
    non_adherent:
      protocol_adherence_rate: 0.50
      probability: 0.25  # 25% of clinicians follow this profile
      characteristics:
        risk_tolerance: "high"     # More willing to discontinue early
        conservative_retreatment: false
  
  # Clinician decision biases
  decision_biases:
    # Different thresholds for considering "stable" disease
    stability_thresholds:
      adherent: 3       # Requires 3 consecutive stable visits
      average: 2        # Requires 2 consecutive stable visits
      non_adherent: 1   # Only requires 1 stable visit
    
    # Different preferences for treatment intervals
    interval_preferences:
      adherent:
        min_interval: 8
        max_interval: 16
        extension_threshold: 2   # Letters of improvement needed to extend
      average:
        min_interval: 8
        max_interval: 12        # More conservative max interval
        extension_threshold: 1
      non_adherent:
        min_interval: 6         # May use shorter intervals
        max_interval: 16
        extension_threshold: 0   # Extends even with no improvement
  
  # Patient assignment model
  patient_assignment:
    mode: "fixed"  # Options: "fixed", "random_per_visit", "weighted"
    continuity_of_care: 0.9  # Probability of seeing the same clinician (if mode="weighted")
```

## Usage

### Running a Simulation with the Enhanced Model

To run a simulation with the enhanced discontinuation model:

1. Create a configuration file with the enhanced discontinuation parameters (see example above).
2. Load the configuration and run the simulation:

```python
from simulation.config import SimulationConfig
from treat_and_extend_abs import TreatAndExtendABS

# Load the configuration
config = SimulationConfig.from_yaml("protocols/simulation_configs/enhanced_discontinuation.yaml")

# Run the simulation
sim = TreatAndExtendABS(config)
patient_histories = sim.run()
```

### Debugging and Testing

A debug script is provided to test the enhanced discontinuation model:

```python
python debug_enhanced_discontinuation.py
```

This script runs a simulation with the enhanced model and provides detailed statistics and visualizations of discontinuation patterns.

## Clinical Data Sources

The enhanced discontinuation model is based on clinical data from several sources:

1. **Aslanis et al. (2021)**: Prospective study of treatment discontinuation after treat-and-extend, with 12-month follow-up. Provides data on recurrence rates with and without PED.

2. **Artiaga et al. (2023)**: Retrospective study of treatment discontinuation with long-term follow-up (5 years). Provides data on time-dependent recurrence rates.

3. **Arendt et al.**: Study of discontinuation after three 16-week intervals. Provides data on recurrence rates for protocol-based discontinuation.

4. **ALTAIR Study (2020)**: Japanese treat-and-extend study with 2-week vs. 4-week adjustments. Provides data on treatment patterns and outcomes.

For more detailed information on the clinical data used in the model, see the comprehensive AMD parameters document in `meta/comprehensive-amd-parameters.md`.

## Statistics and Reporting

The enhanced discontinuation model provides detailed statistics on discontinuation patterns and outcomes:

- Discontinuations by type (protocol-based, administrative, time-based, premature)
- Retreatment rates by discontinuation type
- Clinician performance metrics (protocol adherence, discontinuation rates, retreatment rates)

These statistics can be accessed through the `get_statistics()` method of the EnhancedDiscontinuationManager and the `get_performance_metrics()` method of the ClinicianManager.

## Future Extensions

Potential future extensions to the enhanced discontinuation model include:

1. More sophisticated clinician decision models
2. Additional patient risk factors
3. Machine learning-based prediction of recurrence risk
4. Economic modeling of different discontinuation strategies
5. Patient preference modeling for treatment decisions
