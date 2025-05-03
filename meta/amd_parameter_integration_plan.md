# AMD Parameter Integration Plan

## Overview

This document outlines the plan for integrating the comprehensive AMD parameters from literature into the simulation model. The parameters are derived from multiple studies including ALTAIR, VIEW 1/2, Mylight, and others, providing evidence-based values for disease progression, vision changes, and treatment protocols.

## 1. Parameter Structure and Organization

We will create three key parameter files:

1. **`eylea_base_parameters.yaml`** - The neutral, literature-based parameter set
2. **`eylea_sensitivity_parameters.yaml`** - Parameter variations for sensitivity analysis
3. **`cost_parameters.yaml`** - Cost-related parameters with placeholders

### Switchable Parameter System

To enable switching between different parameter configurations:

```yaml
# Example structure in simulation config
parameters:
  base_parameter_set: "protocols/parameter_sets/eylea/eylea_base_parameters.yaml"
  sensitivity_analysis:
    enabled: true
    parameter_file: "protocols/parameter_sets/eylea/eylea_sensitivity_parameters.yaml"
    selected_variation: "high_response"  # Options defined in the sensitivity file
```

This allows selecting predefined parameter variations during development while setting the groundwork for the future interactive application.

## 2. Treatment Discontinuation Approach

Treatment discontinuation will be modeled as a **process rather than a disease state** for these reasons:

1. **Conceptual clarity**: Treatment discontinuation is an event/decision rather than a biological state
2. **Flexibility**: A patient can be in any disease state (STABLE, ACTIVE, etc.) when treatment is discontinued
3. **Real-world alignment**: Treatment can be resumed based on monitoring, regardless of the underlying disease state

Implementation approach:
```yaml
# Add to patient state
treatment_status:
  active: true/false
  weeks_since_discontinuation: 0
  monitoring_schedule: 12  # weeks between monitoring visits
  recurrence_detected: false

# Add to clinical model parameters
treatment_discontinuation:
  recurrence_probabilities:
    base_risk_per_year: 0.207  # 1-year recurrence rate
    cumulative_3_year: 0.739
    cumulative_5_year: 0.880
  recurrence_impact:
    vision_loss_letters: 3.6
    vision_recovery_factor: 0.95  # Proportion of vision recovered after retreatment
  symptom_detection:
    probability: 0.609  # Probability recurrence causes symptoms
    detection_sensitivity: 1.0  # Probability symptoms lead to detection
```

## 3. Implementation Roadmap

### Phase 1: Base Parameter Integration
1. Create `eylea_base_parameters.yaml` with literature values
2. Update the `SimulationConfig` class to parse the new parameter structure
3. Modify the clinical model to use these parameters
4. Create a test simulation config that references the new parameters

### Phase 2: Treatment Discontinuation Logic
1. Extend the patient state to track treatment status
2. Add logic to handle recurrence probabilities after discontinuation
3. Implement monitoring visits with configurable schedules
4. Model vision changes during recurrence and after retreatment

### Phase 3: Sensitivity Analysis Framework
1. Create `eylea_sensitivity_parameters.yaml` with parameter variations
2. Add logic to switch between parameter sets
3. Implement basic comparison visualization for sensitivity analysis
4. Add the cost parameter structure as placeholders

### Phase 4: Documentation and Validation
1. Document the parameter sources and confidence levels
2. Compare simulation results against literature data
3. Create validation tests for the new parameters
4. Update existing documentation with the new parameter structure

## 4. Detailed Parameter Integration Examples

Here's how key literature parameters would map to the model:

### Visual Acuity Parameters
```yaml
vision_change:
  base_change:
    NAIVE:
      injection: [8.4, 1.3]  # Mean letter change, SD from ALTAIR/VIEW studies
      no_injection: [-2.5, 1.0]  # Estimated from literature
    STABLE:
      injection: [1.5, 0.7]  # From ALTAIR
      no_injection: [-0.75, 0.5]  # From ALTAIR
    ACTIVE:
      injection: [0.8, 0.7]
      no_injection: [-1.5, 1.0]
    HIGHLY_ACTIVE:
      injection: [0.3, 1.2]
      no_injection: [-4.0, 1.5]
```

### Transition Probabilities
```yaml
transition_probabilities:
  NAIVE:
    NAIVE: 0.0
    STABLE: 0.58  # From ALTAIR
    ACTIVE: 0.32  # From ALTAIR
    HIGHLY_ACTIVE: 0.10  # From ALTAIR
  STABLE:
    STABLE: 0.83  # From ALTAIR
    ACTIVE: 0.12  # From ALTAIR
    HIGHLY_ACTIVE: 0.05  # From ALTAIR
```

## 5. Cost Parameter Structure

```yaml
cost_parameters:
  visit_costs:
    standard_visit: 0
    injection_visit: 0
    imaging_visit: 0
    virtual_review: 0
  drug_costs:
    aflibercept_2mg: 0
  resource_utilization:
    time_per_standard_visit: 15  # minutes
    time_per_injection: 10  # additional minutes
    time_per_imaging: 15  # minutes
    time_per_virtual_review: 5  # minutes
```

## 6. References

The parameter values are derived from these key studies:

1. **ALTAIR Study** (2020): Japanese treat-and-extend study with 2-week vs. 4-week adjustments, 96-week data
2. **VIEW 1/2 Studies** (2012): Pivotal Phase 3 fixed dosing studies comparing aflibercept regimens to ranibizumab, 52-week data with 96-week extension
3. **Mylight Study** (2024): Fixed dosing study comparing biosimilar to reference aflibercept, 52-week data
4. **Maruko et al. Study** (2020): Prospective study of treat-and-extend aflibercept with 1-month adjustments, 2-year data
5. **Aslanis et al. Study** (2021): Prospective study of treatment discontinuation after treat-and-extend, 12-month follow-up
6. **Artiaga et al. Study** (2023): Retrospective study of treatment discontinuation with long-term follow-up (5 years)

The comprehensive parameter values are documented in `meta/comprehensive-amd-parameters.md`.
