# Eylea Parameter Calibration Tools

This directory contains tools for systematically calibrating Eylea treat-and-extend protocol parameters to match clinical trial outcomes (VIEW trials, 2-year data).

## Overview

The calibration framework helps find optimal parameter values by:
1. Running simulations with different parameter combinations
2. Comparing outcomes to known clinical trial targets
3. Scoring each combination based on how closely it matches targets
4. Identifying the best parameter sets

## Target Outcomes (VIEW Trials)

- **Vision Gain Year 1**: 8-10 letters (target: 9.0)
- **Vision Year 2**: Slight decline from peak (target: 8.0)
- **Injections Year 1**: 7-8 (target: 7.5)
- **Injections Year 2**: 5-6 (target: 5.5)
- **Discontinuation by Year 2**: 10-15% (target: 12.5%)

## Tools

### 1. eylea_calibration_framework.py

Core framework for testing parameter sets and scoring results.

```python
from eylea_calibration_framework import EyleaCalibrationFramework, ParameterSet

# Create framework
framework = EyleaCalibrationFramework()

# Define parameters to test
params = ParameterSet(
    name="test_params",
    description="Test parameter set",
    discontinuation_year1=0.05,
    discontinuation_year2=0.125,
    # ... other parameters
)

# Run test
result = framework.test_parameters(params, n_patients=200)
```

### 2. parameter_exploration.py

Systematic grid search through parameter combinations.

```python
from parameter_exploration import ParameterExplorer

# Create explorer
explorer = ParameterExplorer()

# Define parameter ranges
explorer.add_parameter_range(
    'discontinuation_year2',
    [0.10, 0.125, 0.15],
    'Year 2 discontinuation rate'
)

# Run exploration
explorer.explore(n_patients=150)
```

### 3. quick_test.py

Quick test script to verify everything is working.

```bash
python calibration/quick_test.py
```

## Usage

### Quick Test
```bash
# Run a quick test with one parameter set
python calibration/quick_test.py
```

### Focused Exploration
```bash
# Explore key parameters systematically
python calibration/parameter_exploration.py
```

### 2D Heatmap Exploration
```bash
# Create heatmaps for 2 parameters
python calibration/parameter_exploration.py 2d
```

### Custom Calibration
```python
# In Python script or notebook
from calibration.eylea_calibration_framework import *

framework = EyleaCalibrationFramework()

# Test multiple parameter sets
param_sets = [
    ParameterSet(name="low_disc", discontinuation_year2=0.10),
    ParameterSet(name="high_resp", good_responder_ratio=0.4),
    # ... more sets
]

for params in param_sets:
    framework.test_parameters(params)

# Save and visualize results
framework.save_results()
framework.plot_results()
```

## Key Parameters to Calibrate

1. **Discontinuation Rates**
   - `discontinuation_year1`: Annual rate in year 1
   - `discontinuation_year2`: Annual rate in year 2
   - etc.

2. **Response Heterogeneity**
   - `good_responder_ratio`: Proportion of good responders
   - `average_responder_ratio`: Proportion of average responders
   - `poor_responder_ratio`: Proportion of poor responders

3. **Vision Response Multipliers**
   - `good_responder_multiplier`: Vision gain multiplier for good responders
   - `average_responder_multiplier`: For average responders
   - `poor_responder_multiplier`: For poor responders

4. **Protocol Parameters**
   - `protocol_interval`: Days between visits after loading phase

## Output Files

- `calibration_results.json`: Detailed results from all tested parameter sets
- `exploration_results.json`: Results from parameter exploration
- `calibration_results.png`: Visualization of outcomes vs targets
- `parameter_impacts.png`: Impact of each parameter on outcomes
- `outcome_heatmap.png`: 2D heatmap of outcomes
- `test_protocols/`: Generated YAML protocol files

## Scoring System

Each parameter set is scored based on deviation from targets:
- **Vision Score**: Weighted deviation from vision targets
- **Injection Score**: Weighted deviation from injection targets
- **Discontinuation Score**: Weighted deviation from discontinuation targets
- **Total Score**: Weighted sum (lower is better)

## Tips for Calibration

1. Start with the quick test to ensure everything works
2. Use focused exploration to test specific parameter ranges
3. Look at both individual scores and total score
4. Verify that parameters are clinically plausible
5. Test best parameters with larger patient counts for confirmation

## Next Steps

After finding optimal parameters:
1. Update the Eylea protocol YAML files with calibrated values
2. Run full-scale simulations to verify outcomes
3. Document the calibration process and results
4. Consider sensitivity analysis around optimal values