# ABS Heterogeneity Implementation Summary

Date: 2025-01-18  
Status: Planning Complete, Ready for Implementation

## Overview

This document summarizes the planning phase for implementing patient heterogeneity in the ABS (Agent-Based Simulation) engine. The goal is to model the wide variability in patient outcomes observed in real-world studies, particularly the Seven-UP study.

## Key Design Decisions

### 1. Configuration-Driven Heterogeneity
- Add `heterogeneity` section to existing protocol YAML files
- Current ABS engine ignores unknown sections (backward compatible)
- All parameters configurable, no hard-coding

### 2. Automatic Engine Selection
- `ABSFactory` class automatically selects appropriate engine
- Checks configuration content, not user preference
- Clear console feedback about which engine is being used
- Falls back to standard engine if configuration is invalid

### 3. Implementation Approach
- New `HeterogeneousABS` class extends `AgentBasedSimulation`
- Individual patient characteristics assigned at initialization
- Heterogeneity "baked in" from start, not accumulated over time

## Technical Architecture

```
ABSFactory.create_simulation(config, start_date)
    ↓
Checks for valid heterogeneity section
    ↓
If present and valid → HeterogeneousABS
If missing or invalid → AgentBasedSimulation
    ↓
Console notification of engine selection
```

## Key Components

1. **ABSFactory**: Automatic engine selection
2. **HeterogeneousABS**: Extended simulation engine
3. **HeterogeneousPatient**: Patient with individual characteristics
4. **HeterogeneityManager**: Configuration parsing and validation

## Heterogeneity Dimensions

1. **Trajectory Classes** (25% good, 40% moderate, 35% poor responders)
2. **Patient Parameters**:
   - Treatment response multiplier
   - Disease progression rate
   - Maximum achievable vision
   - Treatment resistance development
3. **Catastrophic Events** (geographic atrophy, fibrosis)
4. **Variance Components** (65% between-patient, 25% within-patient, 10% measurement)

## Validation Targets (Seven-UP Study)

- Mean 7-year change: -8.6 letters
- Standard deviation: 30 letters
- Year 2-7 correlation: 0.97
- 25% maintain >70 letters
- 35% decline to <35 letters

## Configuration Example

```yaml
heterogeneity:
  enabled: true
  version: '1.0'
  
  trajectory_classes:
    good_responders:
      proportion: 0.25
      parameters:
        treatment_effect_multiplier:
          distribution: lognormal
          mean: 1.3
          std: 0.2
    # ... other classes ...
  
  patient_parameters:
    treatment_responder_type:
      distribution: lognormal
      mean: 1.0
      std: 0.4
    # ... other parameters ...
  
  validation:
    mean_change_7_years: -8.6
    std_7_years: 30
```

## Usage

```python
# User perspective - no change needed!
config = SimulationConfig.from_yaml('eylea_protocol.yaml')
sim = ABSFactory.create_simulation(config, start_date)
# Automatically uses appropriate engine

sim.add_patient("pat001", "eylea")
sim.run(end_date)
results = sim.get_results()
```

## Testing Strategy

1. **Unit Tests**: Configuration parsing, patient assignment, vision updates
2. **Integration Tests**: Full simulations, backward compatibility
3. **Validation Tests**: Seven-UP reproduction, statistical targets
4. **Factory Tests**: Automatic engine selection logic

## Implementation Plan

1. **Phase 1**: Core Implementation
   - ABSFactory class
   - HeterogeneousABS engine
   - Configuration parsing

2. **Phase 2**: Testing
   - Unit test suite
   - Seven-UP validation

3. **Phase 3**: Integration
   - Update simulation runner
   - Add example configurations

4. **Phase 4**: Documentation
   - User guide
   - Migration guide

## Benefits

1. **Scientific Accuracy**: Reproduces real-world outcome variability
2. **Ease of Use**: Automatic engine selection
3. **Backward Compatible**: Existing protocols continue to work
4. **Extensible**: Easy to add new heterogeneity dimensions
5. **Transparent**: Clear feedback about engine selection

## Next Steps

With planning complete, we're ready to begin implementation starting with:
1. Create `simulation/abs_factory.py`
2. Create `simulation/heterogeneous_abs.py`
3. Write unit tests in `tests/unit/test_heterogeneous_abs.py`
4. Create example heterogeneous protocol configuration