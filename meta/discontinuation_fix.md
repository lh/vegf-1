# Discontinuation Manager Fix

## Issue Description

The discontinuation feature in both the Agent-Based Simulation (ABS) and Discrete Event Simulation (DES) implementations was not working correctly. Despite having `discontinuation: enabled: true` in the configuration file, the discontinuation manager was being initialized with `enabled=False`, resulting in no patients discontinuing treatment.

The issue was identified in the debug output:
```
INFO:simulation.discontinuation_manager:Initialized DiscontinuationManager with enabled=False
```

## Root Cause Analysis

The problem was found in both `treat_and_extend_abs.py` and `treat_and_extend_des.py` files. The discontinuation manager was being initialized with the entire configuration parameters instead of the specific discontinuation parameters:

```python
# Initialize discontinuation manager
discontinuation_params = self.config.get_treatment_discontinuation_params()
self.discontinuation_manager = DiscontinuationManager(self.config.parameters)
```

Additionally, there was a mismatch between the expected structure of the parameters in the `DiscontinuationManager` class and what was being returned by the `get_treatment_discontinuation_params()` method. The manager expected a dictionary with a top-level "discontinuation" key, but the method was returning a different structure.

Further investigation revealed that the `evaluate_discontinuation` and `process_monitoring_visit` methods in the `DiscontinuationManager` class expected dictionary-like objects with a `get` method, but we were passing `Patient` objects or patient dictionaries directly.

## Solution

The solution involved three key changes:

1. **Direct Parameter Loading**: Modified both ABS and DES implementations to directly load the discontinuation parameters from the file specified in the configuration, bypassing the problematic `get_treatment_discontinuation_params()` method:

```python
# Get the parameter file path from the config
discontinuation_config = self.config.parameters.get("discontinuation", {})
parameter_file = discontinuation_config.get("parameter_file", "")

if parameter_file:
    try:
        # Directly load the discontinuation parameters from the file
        with open(parameter_file, 'r') as f:
            import yaml
            discontinuation_params = yaml.safe_load(f)
            self.discontinuation_manager = DiscontinuationManager(discontinuation_params)
    except Exception as e:
        print(f"Error loading discontinuation parameters: {str(e)}")
        # Fall back to empty dict with enabled=True
        self.discontinuation_manager = DiscontinuationManager({"discontinuation": {"enabled": True}})
else:
    # If no parameter file specified, use the discontinuation config from the parameters
    self.discontinuation_manager = DiscontinuationManager({"discontinuation": {"enabled": True}})
```

2. **Patient State Conversion for Discontinuation Evaluation**: Modified the code to convert Patient objects to dictionaries with the expected structure before passing them to the discontinuation manager:

```python
# Convert Patient object to dictionary for discontinuation manager
patient_state = {
    "disease_activity": patient.disease_activity,
    "treatment_status": patient.treatment_status
}
should_discontinue, reason, probability = self.discontinuation_manager.evaluate_discontinuation(
    patient_state=patient_state,
    current_time=event.time,
    treatment_start_time=patient.treatment_start
)
```

3. **Patient State Conversion for Monitoring Visits**: Applied the same conversion for monitoring visit processing:

```python
# Convert Patient object to dictionary for discontinuation manager
patient_state = {
    "disease_activity": patient.disease_activity,
    "treatment_status": patient.treatment_status
}
retreatment, updated_patient = self.discontinuation_manager.process_monitoring_visit(
    patient_state=patient_state,
    actions=event.data["actions"]
)
```

## Results

After implementing these changes, the discontinuation feature now works correctly in both ABS and DES simulations:

### ABS Results
```
Discontinuation Statistics:
--------------------
stable_max_interval_discontinuations: 163
random_administrative_discontinuations: 0
treatment_duration_discontinuations: 0
total_discontinuations: 163
retreatments: 0
```

### DES Results
```
Discontinuation Statistics:
--------------------
stable_max_interval_discontinuations: 93
random_administrative_discontinuations: 0
treatment_duration_discontinuations: 0
total_discontinuations: 93
retreatments: 0
```

The simulation now correctly implements the discontinuation feature, with patients discontinuing treatment after reaching stable vision at the maximum interval.

## Future Considerations

1. The `get_treatment_discontinuation_params()` method in the `SimulationConfig` class should be reviewed and potentially fixed to return the correct structure expected by the `DiscontinuationManager` class.

2. The `DiscontinuationManager` class could be updated to handle different input types more gracefully, such as accepting both dictionary-like objects and Patient objects.

3. Unit tests should be added to verify that the discontinuation feature works correctly in both ABS and DES simulations.
