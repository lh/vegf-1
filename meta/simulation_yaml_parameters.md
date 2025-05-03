# Simulation YAML Parameters

This document provides a concise overview of the key YAML parameters needed for configuring AMD treatment simulations, with brief descriptions of each parameter.

## Core Simulation Parameters

```yaml
name: "Simulation Name"  # Descriptive name for the simulation
description: "Brief description"  # Purpose and scope of the simulation

protocol:
  agent: "eylea"  # Anti-VEGF agent (eylea, eylea_hd, vabysmo)
  type: "treat_and_extend"  # Protocol type (fixed, treat_and_extend, prn)
  parameter_set: "standard"  # Parameter set to use

simulation:
  type: "agent_based"  # Simulation type (agent_based, discrete_event)
  duration_days: 365  # Duration of simulation in days
  num_patients: 100  # Number of patients to simulate
  random_seed: 42  # Seed for reproducibility
  start_date: "2023-01-01"  # Start date for simulation
```

## Clinical Model Parameters

```yaml
clinical_model:
  # Disease states in the model
  disease_states:
    - NAIVE
    - STABLE
    - ACTIVE
    - HIGHLY_ACTIVE
  
  # Initial phase transitions (from NAIVE state)
  initial_phase_transitions:
    HIGHLY_ACTIVE: 0.01  # 1% chance per decision
  
  # State transition probabilities
  transition_probabilities:
    NAIVE:  # From NAIVE state
      STABLE: 0.35
      ACTIVE: 0.60
      HIGHLY_ACTIVE: 0.05
    STABLE:  # From STABLE state
      STABLE: 0.88
      ACTIVE: 0.12
      HIGHLY_ACTIVE: 0.0
    ACTIVE:  # From ACTIVE state
      STABLE: 0.20
      ACTIVE: 0.75
      HIGHLY_ACTIVE: 0.05
    HIGHLY_ACTIVE:  # From HIGHLY_ACTIVE state
      STABLE: 0.10
      ACTIVE: 0.30
      HIGHLY_ACTIVE: 0.60
  
  # Vision change parameters
  vision_change:
    # Base change in vision by disease state and treatment
    base_change:
      NAIVE:
        injection: [5, 1]  # mean, std dev for letter change with injection
        no_injection: [0, 0.5]  # mean, std dev for letter change without injection
      STABLE:
        injection: [1, 0.5]
        no_injection: [-0.5, 0.5]
      ACTIVE:
        injection: [3, 1]
        no_injection: [-2, 1]
      HIGHLY_ACTIVE:
        injection: [2, 1]
        no_injection: [-3, 1]
    
    # Time factor for waning treatment effect
    time_factor:
      max_weeks: 52  # Time period over which effect wanes
    
    # Ceiling factor for diminishing returns
    ceiling_factor:
      max_vision: 100  # Maximum vision score
    
    # Measurement noise
    measurement_noise: [0, 0.5]  # mean, std dev of measurement variability
```

## Scheduling Parameters

```yaml
scheduling:
  daily_capacity: 20  # Patients that can be seen per day
  days_per_week: 5  # Clinic days per week (e.g., Monday-Friday)

patient_generation:
  rate_per_week: 1  # New patients per week
  random_seed: 42  # Seed for patient generation
```

## Treatment Protocol Parameters

```yaml
protocol:
  # Loading phase parameters
  loading_phase:
    num_injections: 3  # Number of loading injections
    interval_weeks: 4  # Interval between loading injections
  
  # Maintenance phase parameters
  maintenance_phase:
    initial_interval_weeks: 8  # Starting interval after loading
    min_interval_weeks: 4  # Minimum interval allowed
    max_interval_weeks: 16  # Maximum interval allowed
    extension_increment_weeks: 2  # Weeks to add when extending
    reduction_increment_weeks: 2  # Weeks to subtract when reducing
```

## Output Parameters

```yaml
output:
  save_results: true  # Whether to save results
  database: "simulations.db"  # Database to save results
  plots: true  # Generate plots
  verbose: false  # Detailed output
```

## Drug-Specific Parameter Sets

### Aflibercept 2mg (Eylea)

```yaml
vision_change:
  base_change:
    NAIVE:
      injection: [8.4, 1.2]
    ACTIVE:
      injection: [6.9, 1.5]
    HIGHLY_ACTIVE:
      injection: [4.2, 2.0]
  time_factor:
    max_weeks: 12
```

### Aflibercept 8mg (Eylea HD)

```yaml
vision_change:
  base_change:
    NAIVE:
      injection: [8.7, 1.3]
    ACTIVE:
      injection: [7.1, 1.6]
    HIGHLY_ACTIVE:
      injection: [4.5, 2.1]
  time_factor:
    max_weeks: 16
```

### Faricimab (Vabysmo)

```yaml
vision_change:
  base_change:
    NAIVE:
      injection: [8.3, 1.4]
    ACTIVE:
      injection: [7.0, 1.5]
    HIGHLY_ACTIVE:
      injection: [4.3, 2.0]
  time_factor:
    max_weeks: 16
```
