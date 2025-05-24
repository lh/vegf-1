# Enhanced DES Discontinuation Model Integration with Streamlit

This guide explains how to use the Enhanced Discontinuation Manager with the Discrete Event Simulation (DES) and integrate it with the Streamlit dashboard.

## Overview

The Enhanced Discontinuation Manager extends the base discontinuation manager to provide a more comprehensive framework for managing treatment discontinuation in DES models. The DES to Streamlit adapter ensures that the enhanced DES output is compatible with the existing Streamlit visualization components.

## Key Features

1. **Enhanced Discontinuation Types**
   - Protocol-based discontinuation (stable_max_interval)
   - Administrative discontinuation (random_administrative)
   - Time-based discontinuation (treatment_duration)
   - Premature discontinuation

2. **Monitoring Schedules**
   - Type-specific monitoring schedules
   - Configurable follow-up intervals
   - Different monitoring strategies for different discontinuation types

3. **Recurrence and Retreatment**
   - Time-dependent recurrence probabilities
   - Risk modifiers for recurrence (e.g., presence of PED)
   - Clinician-influenced retreatment decisions

## Using the DES to Streamlit Adapter

The adapter transforms the enhanced DES output to match the format expected by the Streamlit dashboard. This ensures backward compatibility with existing visualization components.

### Basic Usage

```python
from treat_and_extend_des import run_treat_and_extend_des

# Run the simulation with Streamlit-compatible output
results = run_treat_and_extend_des(
    verbose=False,
    streamlit_compatible=True  # This enables the adapter
)

# The results are now in Streamlit-compatible format
print(results.keys())  # Should include "discontinuation_counts", "recurrences", etc.
```

### Advanced Usage with Custom Configuration

```python
from simulation.config import SimulationConfig
from treat_and_extend_des import run_treat_and_extend_des

# Create a custom configuration
config = SimulationConfig.from_yaml("my_custom_config.yaml")

# Run the simulation with the custom configuration
results = run_treat_and_extend_des(
    config=config,
    verbose=True,
    streamlit_compatible=True
)
```

### Direct Adapter Usage

If you need to adapt existing DES results:

```python
from simulation.des_streamlit_adapter import adapt_des_for_streamlit

# Adapt existing DES results
adapted_results = adapt_des_for_streamlit(des_results)

# Use the adapted results with Streamlit visualizations
from streamlit_app.streamgraph_actual_data import generate_actual_data_streamgraph
fig = generate_actual_data_streamgraph(adapted_results)
```

## Adapter Functions

The adapter module (`simulation/des_streamlit_adapter.py`) provides the following functions:

1. **adapt_des_for_streamlit(des_results)**
   - Main adapter function that transforms DES results
   - Returns a dictionary with Streamlit-compatible format

2. **enhance_patient_histories(patient_histories)**
   - Enhances patient histories with standardized fields
   - Adds discontinuation and retreatment flags

3. **format_discontinuation_counts(raw_discontinuation_stats)**
   - Formats discontinuation counts for the dashboard
   - Maps DES cessation types to Streamlit categories

## Example Script

See `examples/des_streamlit_integration.py` for a complete example of running a DES simulation and using the adapter to generate Streamlit visualizations.

## Testing

To run the adapter tests:

```bash
python -m unittest tests/unit/test_des_streamlit_adapter.py
```

## Troubleshooting

If you encounter visualization issues:

1. Check that the adapter is enabled (`streamlit_compatible=True`)
2. Verify that the required fields are present in the results:
   - `discontinuation_counts`
   - `recurrences`
   - `patient_histories`
3. Ensure patient histories have the correct flags:
   - `is_discontinuation_visit`
   - `is_retreatment`
   - `discontinuation_reason`