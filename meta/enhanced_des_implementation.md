# Enhanced DES Implementation Guide

This document details the implementation of the enhanced Discrete Event Simulation (DES) with configuration-driven protocol parameters.

## Overview

The EnhancedDES implementation provides a more flexible and extensible DES core with support for:

1. Configuration-driven protocol parameters
2. Event handler registration
3. Standardized event structure
4. Extension points for protocol-specific behavior

## Key Components

The implementation includes the following key components:

### EnhancedDES Class

Located in `/simulation/enhanced_des.py`, this class extends the original DiscreteEventSimulation with:

- Event handler registration system
- Configuration-driven protocol parameters
- Improved patient state tracking
- Standardized event processing

### Configuration Integration

Protocols are now configured through YAML files with parameters like:

```yaml
treatment_phases:
  initial_loading:
    rules:
      interval_weeks: 6
      injections_required: 4
  maintenance:
    rules:
      initial_interval_weeks: 10
      max_interval_weeks: 14
      extension_step: 4
      reduction_step: 6
```

### Parameter Handling

The implementation dynamically loads protocol parameters from the configuration:

1. `protocol_type` from config parameters determines which protocol to use
2. Loading phase parameters (interval, number of injections)
3. Maintenance phase parameters (initial interval, max interval, extension/reduction steps)
4. Fallback values ensure robustness when config parameters are missing

## Implementation Details

### Configuration Loading

Protocol parameters are loaded from the configuration hierarchy:

```python
protocol_name = patient.state.get("protocol", "treat_and_extend")
protocol_config = self.config.parameters.get("protocols", {}).get(protocol_name, {})
protocol_phases = protocol_config.get("treatment_phases", {})

# Get loading phase parameters
loading_phase = protocol_phases.get("initial_loading", {})
loading_rules = loading_phase.get("rules", {})
loading_interval_weeks = loading_rules.get("interval_weeks", 4)  # Use 4 weeks as fallback
injections_required = loading_rules.get("injections_required", 3)  # Use 3 as fallback
```

### Dynamic Protocol Behavior

The implementation uses these parameters to determine:

1. Loading phase injection intervals
2. Number of injections required to complete loading phase
3. Initial maintenance phase interval
4. Maximum extension interval
5. Interval adjustment steps (extension and reduction)

### Patient State Initialization

Patient state is initialized with protocol-specific parameters:

```python
patient.state.update({
    "current_phase": "loading",
    "treatments_in_phase": 0,
    "next_visit_interval": loading_interval_weeks,
    "disease_activity": {
        "fluid_detected": True,
        "consecutive_stable_visits": 0,
        "max_interval_reached": False,
        "current_interval": loading_interval_weeks
    }
})
```

### Protocol Updates

The `_handle_treat_and_extend_updates` method is the core method for protocol-specific logic:

```python
if phase == "loading":
    # Fixed intervals during loading, from configuration
    patient.state["next_visit_interval"] = loading_interval_weeks
    disease_activity["current_interval"] = loading_interval_weeks
    
    # Check for phase completion (default 3 loading injections or from config)
    if treatments_in_phase >= injections_required:
        # Will transition to maintenance in next visit
        patient.state["next_visit_interval"] = initial_interval_weeks
        disease_activity["current_interval"] = initial_interval_weeks

elif phase == "maintenance":
    current_interval = disease_activity.get("current_interval", initial_interval_weeks)
    
    if fluid_detected:
        # Decrease interval by reduction_step, but not below initial interval
        new_interval = max(initial_interval_weeks, current_interval - reduction_step)
        disease_activity["consecutive_stable_visits"] = 0
        disease_activity["max_interval_reached"] = False
    else:
        # Increase interval by extension_step, up to max interval
        new_interval = min(max_interval_weeks, current_interval + extension_step)
        disease_activity["consecutive_stable_visits"] += 1
```

## Configuration Structure

Protocol configurations should follow this structure in YAML files:

```yaml
protocols:
  treat_and_extend:
    treatment_phases:
      initial_loading:
        rules:
          interval_weeks: 4
          injections_required: 3
      maintenance:
        rules:
          initial_interval_weeks: 8
          max_interval_weeks: 16
          extension_step: 2
          reduction_step: 2
```

## Validation

A validation script (`validate_enhanced_des.py`) verifies that:

1. Protocol parameters are correctly loaded from config
2. Intervals between visits match the configured values
3. Phase transitions occur after the configured number of injections

## Next Steps

Further enhancements could include:

1. More comprehensive protocol modeling (beyond treat-and-extend)
2. Direct integration with protocol YAML files
3. Support for dynamic protocol switching
4. Advanced protocol validation 
5. More flexible event handler composition

## Usage Example

```python
from simulation.config import SimulationConfig
from simulation.enhanced_des import EnhancedDES

# Load configuration with protocol parameters
config = SimulationConfig.from_yaml("eylea_literature_based")

# Initialize simulation with config-driven parameters
sim = EnhancedDES(config)

# Run simulation
results = sim.run()

# Access patient histories for analysis
patient_histories = results["patient_histories"]
```

## Summary

The enhanced DES implementation provides a more flexible and maintainable approach to protocol modeling by:

1. Removing hard-coded protocol parameters
2. Supporting diverse protocol configurations
3. Providing default fallback values for robustness
4. Enhancing extensibility through event handler registration 

This enables the simulation of different protocols through configuration changes rather than code modifications, supporting the goal of comparing different protocols in future analyses.