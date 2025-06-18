# ABS Heterogeneity: Final Consolidated Specification

Version: 1.0  
Date: 2025-01-18  
Status: Ready for Implementation

## Executive Summary

This specification defines a heterogeneous Agent-Based Simulation (ABS) engine that models patient variability in AMD treatment response based on real-world data from the Seven-UP study. The engine extends the existing ABS implementation with automatic selection based on configuration content.

## Background

The Seven-UP study revealed enormous variability in patient outcomes:
- Mean 7-year decline: -8.6 letters (SD: 30 letters)
- ~25% maintain >70 letters, ~35% decline to <35 letters
- Year 2 outcomes strongly predict Year 7 (r = 0.97)

Key insight: Heterogeneity is "baked in" from the start through patient-specific characteristics, not accumulated through random walks.

## System Architecture

### Class Hierarchy

```
BaseSimulation (existing)
    ├── AgentBasedSimulation (existing)
    └── HeterogeneousABS (new)
            ├── HeterogeneousPatient (new)
            └── HeterogeneityManager (new)

ABSFactory (new)
    └── create_simulation() - Automatic engine selection
```

### Automatic Engine Selection

```python
# Usage - configuration determines engine automatically
config = SimulationConfig.from_yaml('eylea_protocol.yaml')
sim = ABSFactory.create_simulation(config, start_date)
# Console: "✓ Heterogeneity configuration detected - using HeterogeneousABS engine"
# or: "→ Standard configuration - using AgentBasedSimulation engine"
```

## Configuration Design

### YAML Structure

Add `heterogeneity` section to existing protocol files:

```yaml
# Standard protocol parameters remain unchanged
name: Eylea Treat and Extend
version: '1.0'

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
  
  # Patient-specific parameters
  patient_parameters:
    resistance_rate:
      distribution: beta
      alpha: 2
      beta: 5
      comment: "Treatment resistance development"
    
    max_achievable_va_offset:
      distribution: normal
      mean: 10
      std: 15
      comment: "Added to baseline to determine ceiling"
  
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
      vision_impact:
        distribution: normal
        mean: -20
        std: 5
      permanent: true
      max_va_reduction: 20
  
  # Variance decomposition
  variance_components:
    between_patient: 0.65
    within_patient: 0.25
    measurement: 0.10
  
  # Validation targets
  validation:
    mean_change_7_years: -8.6
    std_7_years: 30
    year2_year7_correlation: 0.97
    proportion_above_70: 0.25
    proportion_below_35: 0.35
  
  # Optional debug settings
  debug: false
  debug_output:
    - patient_assignments
    - distribution_samples
    - validation_metrics
```

## Core Components

### 1. ABSFactory

```python
class ABSFactory:
    """Factory for automatic engine selection based on configuration."""
    
    @staticmethod
    def create_simulation(config: SimulationConfig, start_date: datetime) -> BaseSimulation:
        """Create appropriate simulation engine with console notification."""
        if ABSFactory._supports_heterogeneity(config):
            print("✓ Heterogeneity configuration detected - using HeterogeneousABS engine")
            return HeterogeneousABS(config, start_date)
        else:
            print("→ Standard configuration - using AgentBasedSimulation engine")
            return AgentBasedSimulation(config, start_date)
    
    @staticmethod
    def _supports_heterogeneity(config: SimulationConfig) -> bool:
        """Validate heterogeneity configuration."""
        # Check for section, enabled=true, required fields, valid proportions
```

### 2. HeterogeneousABS

```python
class HeterogeneousABS(AgentBasedSimulation):
    """ABS engine with patient heterogeneity."""
    
    def __init__(self, config, start_date: datetime):
        super().__init__(config, start_date)
        self.heterogeneity_manager = HeterogeneityManager(
            config.protocol.heterogeneity, 
            config.random_seed
        )
        
    def add_patient(self, patient_id: str, protocol_name: str):
        """Create heterogeneous patient with individual characteristics."""
        # Generate baseline VA
        baseline_va = self.clinical_model.get_initial_vision()
        
        # Create heterogeneous patient
        patient = self.heterogeneity_manager.create_patient(
            patient_id, baseline_va
        )
        
        self.agents[patient_id] = patient
```

### 3. HeterogeneityManager

```python
class HeterogeneityManager:
    """Manages heterogeneity parameters and patient creation."""
    
    def __init__(self, config: Dict, seed: int):
        self.config = config
        
        # Separate RNG streams for reproducibility
        self.trajectory_rng = np.random.RandomState(seed)
        self.parameter_rng = np.random.RandomState(seed + 1)
        self.event_rng = np.random.RandomState(seed + 2)
        
        # Pre-compute samples for performance
        self.sample_cache_size = 10000
        self._precompute_samples()
        
    def create_patient(self, patient_id: str, baseline_va: float) -> HeterogeneousPatient:
        """Create patient with heterogeneous characteristics."""
        # 1. Assign trajectory class
        trajectory_class = self._assign_trajectory_class()
        
        # 2. Generate class-specific parameters
        characteristics = self._generate_characteristics(
            trajectory_class, baseline_va
        )
        
        # 3. Apply baseline VA correlations
        if baseline_va > 70:
            characteristics['treatment_effect_multiplier'] *= 1.3
            characteristics['disease_progression_multiplier'] *= 0.7
        
        # 4. Calculate max achievable VA
        offset = self.parameter_rng.normal(10, 15)
        characteristics['max_achievable_va'] = min(85, baseline_va + offset)
        
        return HeterogeneousPatient(patient_id, baseline_va, characteristics)
```

### 4. HeterogeneousPatient

```python
class HeterogeneousPatient(Patient):
    """Patient with heterogeneous characteristics."""
    
    def __init__(self, patient_id: str, baseline_va: float, characteristics: Dict):
        # Standard initialization
        initial_state = PatientState(patient_id, "protocol", baseline_va, datetime.now())
        super().__init__(patient_id, initial_state)
        
        # Heterogeneous characteristics
        self.characteristics = characteristics
        self.treatments_received = 0
        self.catastrophic_event_history = []
        
    def update_vision(self, treatment_given: bool, weeks_elapsed: float) -> float:
        """Update vision with heterogeneous response."""
        current_va = self.state.vision
        
        # 1. Treatment effect with multiplier and resistance
        treatment_benefit = 0
        if treatment_given:
            base_effect = 5.0
            ceiling_factor = 1 - (current_va / self.characteristics['max_achievable_va'])
            treatment_benefit = (base_effect * 
                               self.characteristics['treatment_effect_multiplier'] * 
                               ceiling_factor)
            
            # Apply treatment resistance
            self.treatments_received += 1
            resistance_factor = np.exp(-self.characteristics['resistance_rate'] * 
                                     self.treatments_received)
            treatment_benefit *= resistance_factor
        
        # 2. Disease progression with multiplier
        base_progression = -0.5  # letters per week
        progression = (base_progression * 
                      self.characteristics['disease_progression_multiplier'] * 
                      weeks_elapsed)
        
        # 3. Measurement noise
        noise = np.random.normal(0, 2)
        
        # 4. Catastrophic events
        catastrophic_drop = self._check_catastrophic_events(weeks_elapsed)
        
        # 5. Apply changes and bounds
        new_va = current_va + treatment_benefit + progression + noise + catastrophic_drop
        self.state.vision = np.clip(new_va, 0, 85)
        
        return self.state.vision
```

## Data Persistence

### Visit Record Structure

```python
visit_record = {
    'date': datetime,
    'vision': float,
    # ... existing fields ...
    'patient_characteristics': {  # NEW
        'trajectory_class': str,
        'treatment_effect_multiplier': float,
        'disease_progression_multiplier': float,
        'max_achievable_va': float,
        'resistance_rate': float,
        'treatments_received': int
    }
}
```

This ensures characteristics are saved for analysis and resumption.

## Validation Framework

### Validation Targets

```yaml
# protocols/validation/seven_up_targets.yaml
validation_targets:
  seven_up:
    duration_years: 7
    population_size: 1000
    
    statistical_targets:
      mean_change:
        value: -8.6
        tolerance: 2.0
      standard_deviation:
        value: 30
        tolerance: 3.0
      correlations:
        year2_year7:
          value: 0.97
          tolerance: 0.02
      distributions:
        above_70_letters:
          value: 0.25
          tolerance: 0.05
```

### Validation Process

1. Run 1000+ patients for 7 years
2. Calculate metrics
3. Compare to targets with tolerances
4. Generate validation report

## Performance Optimizations

### 1. Distribution Pre-sampling

```python
def _precompute_samples(self):
    """Pre-generate samples for efficiency."""
    self.samples = {}
    for param, config in self.all_parameters.items():
        self.samples[param] = self._generate_samples(
            config, self.sample_cache_size
        )
```

### 2. Performance Requirements

- < 20% overhead vs homogeneous engine
- Support 10,000+ patient simulations
- Memory overhead < 100 bytes per patient

## Testing Strategy

### 1. Unit Tests
- Configuration parsing and validation
- Patient characteristic assignment
- Vision update calculations
- Engine selection logic

### 2. Integration Tests
- Full simulation runs
- Output format compatibility
- Performance benchmarking

### 3. Validation Tests
- Seven-UP statistical reproduction
- Sensitivity analysis
- Edge cases

### Test Execution

```bash
# All heterogeneity tests
pytest tests/unit/test_heterogeneous_abs.py -v

# Validation tests (slow)
pytest tests/validation/test_seven_up_validation.py -v

# With coverage
pytest --cov=simulation.heterogeneous_abs
```

## Implementation Plan

### Phase 1: Core Implementation
1. `simulation/abs_factory.py` - Engine selection
2. `simulation/heterogeneous_abs.py` - Main engine
3. `simulation/heterogeneity_manager.py` - Parameter management

### Phase 2: Testing & Validation
1. Unit test suite
2. Seven-UP validation
3. Performance benchmarking

### Phase 3: Integration
1. Update simulation runner
2. Add visualization support
3. Create example configurations

### Phase 4: Documentation
1. User guide
2. Parameter tuning guide
3. Migration guide

## Error Handling

- **Missing heterogeneity section**: Use standard engine
- **Invalid configuration**: Warn and fall back
- **Validation failure**: Clear error messages
- **Performance issues**: Profiling hooks

## Integration Notes

### Time Series Generator Interaction

**Note**: The `ape/components/treatment_patterns/time_series_generator.py` may be modified in another session. This file is used by the streamgraph visualization to process patient visit data.

**Data Flow**:
1. Heterogeneous ABS → Patient visit records (with characteristics)
2. Visit records → `extract_treatment_patterns_vectorized()` 
3. Pattern data → `time_series_generator.generate_patient_state_time_series()`
4. Time series → Streamgraph visualization

**Key Requirements**:
- Visit records must maintain standard structure:
  - `patient_id`, `time_days`, `treatment_state`
- Patient characteristics are stored separately in visit records
- Time series generator doesn't need modification for heterogeneity
- Changes to time series generator should preserve this interface

## Future Extensions

1. **Biomarker modeling**: Explicit OCT parameters
2. **Adaptive protocols**: Change protocol based on response
3. **Machine learning**: Learn parameters from real data
4. **Parallel processing**: Multi-core patient simulation

## Summary

This heterogeneous ABS engine provides:
- Automatic selection based on configuration
- Scientifically accurate patient variability
- Full backward compatibility
- Clear validation framework
- Performance optimization

The design balances scientific accuracy with practical implementation concerns, ensuring the tool can reproduce real-world heterogeneity while remaining maintainable and performant.