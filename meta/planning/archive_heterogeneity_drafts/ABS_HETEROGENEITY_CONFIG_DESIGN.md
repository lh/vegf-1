# ABS Heterogeneity Configuration Design

Date: 2025-01-18
Purpose: Design a configuration approach that supports patient heterogeneity while maintaining backward compatibility

## Current Configuration System

The existing system uses YAML files with the following hierarchy:
1. **base_parameters.yaml** - Common parameters for all protocols
2. **Protocol files** (e.g., eylea.yaml) - Protocol-specific definitions
3. **Distribution files** - Patient population distributions
4. **V2 protocol files** - Enhanced protocol definitions with more parameters

## Design Goals

1. **Backward Compatible**: Existing ABS engine should ignore new parameters
2. **Extensible**: Easy to add new heterogeneity dimensions
3. **Data-Driven**: All parameters configurable, not hard-coded
4. **Validation-Friendly**: Clear structure for parameter validation
5. **Auto-Selection**: Configuration content determines engine selection automatically

## Proposed Configuration Approach

### Option 1: New Section in Protocol YAML (Recommended)

Add a `heterogeneity` section to protocol YAML files that the current engine will ignore:

```yaml
# Existing sections remain unchanged
name: Eylea Treat and Extend
version: '1.0'
# ... existing parameters ...

# New section - ignored by current engine
heterogeneity:
  enabled: true
  version: '1.0'
  
  # Patient trajectory classes
  trajectory_classes:
    good_responders:
      proportion: 0.25
      description: "Maintain vision near baseline"
      parameters:
        treatment_effect_multiplier:
          distribution: lognormal
          mean: 1.3
          std: 0.2
        disease_progression_multiplier:
          distribution: lognormal
          mean: 0.7
          std: 0.15
        max_achievable_va_offset:
          distribution: normal
          mean: 10
          std: 5
    
    moderate_decliners:
      proportion: 0.40
      description: "Gradual decline over time"
      parameters:
        treatment_effect_multiplier:
          distribution: lognormal
          mean: 1.0
          std: 0.3
        disease_progression_multiplier:
          distribution: lognormal
          mean: 1.0
          std: 0.3
        max_achievable_va_offset:
          distribution: normal
          mean: 5
          std: 5
    
    poor_responders:
      proportion: 0.35
      description: "Rapid/severe decline"
      parameters:
        treatment_effect_multiplier:
          distribution: lognormal
          mean: 0.7
          std: 0.2
        disease_progression_multiplier:
          distribution: lognormal
          mean: 1.5
          std: 0.4
        max_achievable_va_offset:
          distribution: normal
          mean: 0
          std: 5
  
  # Correlated parameters
  patient_parameters:
    # Treatment response heterogeneity
    treatment_responder_type:
      distribution: lognormal
      mean: 1.0
      std: 0.4
      correlation_with_baseline_va: 0.3
    
    # Disease aggressiveness
    disease_aggressiveness:
      distribution: lognormal
      mean: 1.0
      std: 0.5
      correlation_with_baseline_va: -0.2
    
    # Treatment resistance development
    resistance_rate:
      distribution: beta
      alpha: 2
      beta: 5
      comment: "Most patients stay responsive, some develop resistance"
    
    # Maximum achievable vision (ceiling effect)
    max_achievable_va:
      calculation: "baseline_va + offset"
      offset_distribution: normal
      offset_mean: 10
      offset_std: 15
      ceiling: 85
  
  # Catastrophic events
  catastrophic_events:
    geographic_atrophy:
      probability_per_month: 0.001
      vision_impact:
        distribution: uniform
        min: -30
        max: -10
      permanent: true
    
    subretinal_fibrosis:
      probability_per_month: 0.0005
      max_va_reduction: 20
      permanent: true
  
  # Variance decomposition
  variance_components:
    between_patient: 0.65  # 65% of variance
    within_patient: 0.25   # 25% of variance
    measurement: 0.10      # 10% of variance
  
  # Validation targets (from Seven-UP study)
  validation:
    mean_change_7_years: -8.6
    std_7_years: 30
    year2_year7_correlation: 0.97
    proportion_above_70_letters: 0.25
    proportion_below_35_letters: 0.35
```

### Option 2: Separate Heterogeneity Configuration File

Create companion files like `eylea_heterogeneity.yaml`:

```yaml
# Reference to base protocol
base_protocol: eylea_treat_and_extend_v1.0
heterogeneity_version: '1.0'

# All heterogeneity parameters...
```

### Option 3: Enhanced Distribution Files

Extend the existing distribution system:

```yaml
# protocols/distributions/real_uk_population_heterogeneous.yaml
name: "Real UK Population with Heterogeneity"
base_distribution: "real_uk_population"

heterogeneity:
  patient_clusters:
    # Define clusters based on initial characteristics
    high_baseline_good_responders:
      selection_criteria:
        baseline_va: [70, 90]
      proportion: 0.15
      modifiers:
        treatment_response: 1.3
        progression_rate: 0.7
```

## Recommended Approach: Option 1

**Advantages:**
1. Single file contains all protocol information
2. Clear version control and association
3. Easy to enable/disable heterogeneity
4. Current engine naturally ignores unknown sections
5. Validation targets included with parameters

**Implementation Strategy:**
1. Current ABS engine continues to work unchanged
2. New heterogeneous ABS engine checks for `heterogeneity` section
3. Falls back to standard behavior if section missing
4. Can gradually migrate protocols to include heterogeneity

## Configuration Usage in Code

### Automatic Engine Selection

```python
# In simulation runner or main code
from simulation.abs_factory import ABSFactory

# Load configuration
config = SimulationConfig.from_yaml('eylea_treat_and_extend.yaml')

# Factory automatically selects appropriate engine
sim = ABSFactory.create_simulation(config, start_date)
# Console: "✓ Heterogeneity configuration detected - using HeterogeneousABS engine"
# or: "→ Standard configuration - using AgentBasedSimulation engine"
```

### Inside HeterogeneousABS

```python
class HeterogeneousABS(AgentBasedSimulation):
    def __init__(self, config, start_date):
        super().__init__(config, start_date)
        
        # Heterogeneity configuration already validated by factory
        protocol_config = config.protocol.to_dict()
        self.heterogeneity_config = protocol_config['heterogeneity']
        self.heterogeneity_enabled = True
        
        # Initialize heterogeneity components
        self._setup_heterogeneity()
    
    def _setup_heterogeneity(self):
        """Initialize heterogeneity parameters from configuration."""
        self.trajectory_classes = self._parse_trajectory_classes()
        self.patient_parameters = self._parse_patient_parameters()
        self.catastrophic_events = self._parse_catastrophic_events()
        # etc.
```

## Migration Path

1. **Phase 1**: Implement heterogeneity section parsing in new engine
2. **Phase 2**: Add heterogeneity sections to test protocols
3. **Phase 3**: Validate against Seven-UP data
4. **Phase 4**: Roll out to production protocols
5. **Phase 5**: Document best practices for parameter tuning

## Parameter Validation

The heterogeneity section should include:
- **Proportions** must sum to 1.0 for trajectory classes
- **Distributions** must have valid parameters
- **Correlations** must be between -1 and 1
- **Validation targets** for testing model accuracy

## Next Steps

1. Implement configuration parser for heterogeneity section
2. Design patient initialization using these parameters
3. Create validation framework against Seven-UP targets
4. Write comprehensive tests for configuration handling