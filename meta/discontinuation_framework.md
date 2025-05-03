# Treatment Discontinuation Framework

## Overview

The Treatment Discontinuation Framework provides a configurable mechanism for managing treatment discontinuation in both Agent-Based Simulation (ABS) and Discrete Event Simulation (DES) models. This framework addresses the need for more realistic modeling of treatment discontinuation patterns in AMD simulations.

## Key Features

- **Configuration-driven**: All discontinuation parameters are configurable through YAML files
- **Multiple discontinuation criteria**: Supports various discontinuation scenarios:
  - Protocol-based (stable at maximum interval)
  - Administrative/random (e.g., insurance issues, patient choice)
  - Time-based (e.g., after a certain treatment duration)
- **Post-discontinuation monitoring**: Configurable follow-up schedule
- **Treatment re-entry**: Patients can re-enter treatment if disease recurs
- **Consistent implementation**: Same logic used in both ABS and DES models
- **Selective enabling**: Each criterion can be individually enabled/disabled via probability settings

## Configuration

Discontinuation parameters are defined in a YAML file. Here's an example configuration:

```yaml
discontinuation:
  enabled: true
  
  # Criteria for discontinuation
  criteria:
    # Discontinuation after stable visits at maximum interval
    stable_max_interval:
      consecutive_visits: 3  # Number of consecutive stable visits required
      probability: 0.2       # Probability of discontinuation when criteria met
    
    # Random administrative discontinuations (e.g., insurance issues, patient choice)
    random_administrative:
      annual_probability: 0.05  # Annual probability of random discontinuation
    
    # Time-based discontinuation (e.g., after 1 year of treatment)
    treatment_duration:
      threshold_weeks: 52    # Weeks of treatment before considering discontinuation
      probability: 0.1       # Probability of discontinuation after threshold
  
  # Post-discontinuation monitoring
  monitoring:
    follow_up_schedule: [12, 24, 36]  # Weeks after discontinuation for follow-up visits
    recurrence_detection_probability: 0.87  # Probability of detecting recurrence if present
  
  # Treatment re-entry criteria
  retreatment:
    eligibility_criteria:
      detected_fluid: true           # Fluid must be detected
      vision_loss_letters: 5         # Minimum vision loss to trigger retreatment
    probability: 0.95                # Probability of retreatment when eligible
```

## Implementation

The framework is implemented through the `DiscontinuationManager` class, which provides methods for:

1. Evaluating discontinuation criteria
2. Scheduling post-discontinuation monitoring visits
3. Processing monitoring visits
4. Evaluating retreatment eligibility

### DiscontinuationManager Class

The `DiscontinuationManager` class is the core of the framework. It provides the following methods:

- `evaluate_discontinuation()`: Evaluates whether a patient should discontinue treatment
- `schedule_monitoring()`: Schedules post-discontinuation monitoring visits
- `process_monitoring_visit()`: Processes a monitoring visit for a discontinued patient
- `evaluate_retreatment()`: Evaluates whether a discontinued patient should re-enter treatment

### Integration with Simulation Models

The framework is integrated into both the ABS and DES models:

#### DES Implementation

In the DES model, the `DiscontinuationManager` is used in the `_process_visit` method to evaluate discontinuation criteria and schedule monitoring visits.

#### ABS Implementation

In the ABS model, the `DiscontinuationManager` is used in the `process_event` method to evaluate discontinuation criteria and schedule monitoring visits.

## Statistics

The framework tracks various statistics related to discontinuation:

- `stable_max_interval_discontinuations`: Number of discontinuations due to stable visits at maximum interval
- `random_administrative_discontinuations`: Number of discontinuations due to administrative reasons
- `treatment_duration_discontinuations`: Number of discontinuations due to treatment duration
- `total_discontinuations`: Total number of discontinuations
- `retreatments`: Number of patients who re-entered treatment after discontinuation

## Usage

To use the discontinuation framework:

1. Create a discontinuation parameters YAML file
2. Reference the file in your simulation configuration:

```yaml
discontinuation:
  enabled: true
  parameter_file: "protocols/parameter_sets/eylea/discontinuation_parameters.yaml"
```

3. Run your simulation as usual

### Selectively Enabling Criteria

Each discontinuation criterion can be individually enabled or disabled by setting its probability:

- **Setting probability to 0**: Disables the criterion completely
- **Setting probability between 0 and 1**: Enables the criterion with the specified probability
- **Setting probability to 1**: Always applies the criterion when conditions are met

For example, to enable only the stable_max_interval criterion:

```yaml
discontinuation:
  enabled: true
  criteria:
    stable_max_interval:
      consecutive_visits: 3
      probability: 0.2  # Enabled with 20% probability
    random_administrative:
      annual_probability: 0.0  # Disabled (0% probability)
    treatment_duration:
      threshold_weeks: 52
      probability: 0.0  # Disabled (0% probability)
```

## Benefits

- **More realistic modeling**: Better reflects real-world treatment patterns
- **Configurable parameters**: Easy to adjust discontinuation criteria for different scenarios
- **Consistent implementation**: Same logic used in both simulation types
- **Detailed statistics**: Track discontinuation patterns and retreatment rates
