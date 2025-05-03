# Vision Models Module Documentation

## Overview

The `vision_models.py` module provides a centralized implementation of vision change models for AMD disease progression simulations. This module ensures consistent vision change calculations across different simulation types (ABS and DES).

## Motivation

Previously, the ABS and DES implementations had different approaches to calculating vision changes:

- The ABS implementation used the `clinical_model.simulate_vision_change` method, which is complex and based on disease states
- The DES implementation used a simplified normal distribution model

This inconsistency led to different vision outcomes between the two simulation types, making it difficult to compare results. The `vision_models.py` module addresses this issue by providing a common interface for vision change calculations.

## Module Structure

The module consists of:

1. **BaseVisionModel** - Abstract base class defining the interface for all vision models
2. **SimplifiedVisionModel** - Simple normally distributed vision change model
3. **LiteratureBasedVisionModel** - Vision change model based on literature data
4. **create_vision_model** - Factory function to create vision models

## Usage

### Basic Usage

```python
from simulation.vision_models import SimplifiedVisionModel

# Create a vision model
vision_model = SimplifiedVisionModel(config)

# Calculate vision change
state = {
    "fluid_detected": True,
    "treatments_in_phase": 1,
    "interval": 4,
    "current_vision": 65,
    "treatment_status": {"active": True}
}
actions = ["vision_test", "oct_scan", "injection"]
phase = "loading"

vision_change, fluid_detected = vision_model.calculate_vision_change(
    state=state,
    actions=actions,
    phase=phase
)
```

### Using the Factory Function

```python
from simulation.vision_models import create_vision_model

# Create a simplified vision model
vision_model = create_vision_model(
    model_type="simplified",
    config=config
)

# Create a literature-based vision model
vision_model = create_vision_model(
    model_type="literature_based",
    config=config,
    clinical_model=clinical_model
)
```

## Model Descriptions

### SimplifiedVisionModel

This model uses fixed normal distributions for vision change, with different parameters for loading and maintenance phases. It matches the model used in the original `treat_and_extend_des.py`.

**Default Parameters:**
- Loading phase: mean = 6.0, std = 1.5
- Maintenance phase: mean = 2.0, std = 1.0
- Fluid detection probability: 0.3 (30% chance)

These parameters can be overridden through configuration.

### LiteratureBasedVisionModel

This model uses the `clinical_model.simulate_vision_change` method, which implements a more complex vision change model based on literature data and disease states. It requires a `ClinicalModel` instance.

## Configuration

The vision models can be configured through the simulation configuration YAML files. For example:

```yaml
parameters:
  vision:
    vision_model:
      type: "simplified"  # Options: simplified, literature_based
      parameters:
        loading_phase:
          mean: 6.0
          std: 1.5
        maintenance_phase:
          mean: 2.0
          std: 1.0
        fluid_detection_probability: 0.3
```

## Implementation Details

### State Dictionary

The `calculate_vision_change` method expects a state dictionary with the following keys:

- `fluid_detected` - Whether fluid was detected at the last visit
- `treatments_in_phase` - Number of treatments in the current phase
- `interval` - Current treatment interval in weeks
- `current_vision` - Current visual acuity
- `treatment_status` - Dictionary with treatment status information

### Return Values

The `calculate_vision_change` method returns a tuple containing:

1. `vision_change` - Change in visual acuity (ETDRS letters)
2. `fluid_detected` - Whether fluid was detected at this visit

## Benefits of the Vision Models Module

1. **Consistency** - Both ABS and DES implementations use the same vision change logic
2. **Modularity** - Easy to implement and test different vision models
3. **Configurability** - Vision model parameters can be configured through YAML files
4. **Maintainability** - Single source of truth for vision change logic
5. **Extensibility** - Easy to add new vision models in the future

## Future Improvements

1. **Additional Models** - Implement more sophisticated vision change models based on clinical data
2. **Parameter Tuning** - Refine model parameters based on real-world data
3. **Validation** - Validate models against clinical trial data
4. **Visualization** - Add tools to visualize vision change distributions
