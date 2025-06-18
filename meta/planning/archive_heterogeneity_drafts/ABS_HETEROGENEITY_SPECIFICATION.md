# Heterogeneous ABS Engine Specification

Version: 1.0  
Date: 2025-01-18  
Status: Draft

## Executive Summary

This specification defines a new Agent-Based Simulation (ABS) engine variant that models patient heterogeneity in AMD treatment response. The engine extends the existing ABS implementation to capture the wide variability in patient outcomes observed in real-world studies, particularly the Seven-UP study.

## Requirements

### Functional Requirements

1. **FR1: Backward Compatibility**
   - The new engine must accept the same inputs as the existing ABS engine
   - Must produce outputs in the same format
   - Must be selectable via configuration

2. **FR2: Patient Heterogeneity Modeling**
   - Model patient-specific treatment response
   - Model patient-specific disease progression rates
   - Model patient-specific maximum achievable vision
   - Support trajectory classes (good/moderate/poor responders)

3. **FR3: Configuration-Driven**
   - All heterogeneity parameters must be configurable via YAML
   - No hard-coded patient characteristics
   - Support enabling/disabling heterogeneity

4. **FR4: Validation Support**
   - Must reproduce Seven-UP study outcomes
   - Support validation metrics extraction
   - Enable comparison with target distributions

### Non-Functional Requirements

1. **NFR1: Performance**
   - Performance degradation < 20% compared to homogeneous engine
   - Support 10,000+ patient simulations

2. **NFR2: Maintainability**
   - Clear separation from existing engine
   - Well-documented heterogeneity algorithms
   - Comprehensive unit tests

3. **NFR3: Scientific Accuracy**
   - Reproduce real-world outcome distributions
   - Maintain patient conservation principles
   - No synthetic data generation

## Design

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

### Core Components

#### 0. ABSFactory Class (New)

```python
class ABSFactory:
    """
    Factory for creating appropriate ABS engine based on configuration.
    
    Automatically selects between standard and heterogeneous engines
    based on configuration content.
    """
    
    @staticmethod
    def create_simulation(config: SimulationConfig, start_date: datetime) -> BaseSimulation:
        """
        Create appropriate simulation engine.
        
        Checks configuration for valid heterogeneity section and
        returns either AgentBasedSimulation or HeterogeneousABS.
        Prints console message indicating which engine was selected.
        """
    
    @staticmethod
    def _supports_heterogeneity(config: SimulationConfig) -> bool:
        """
        Validate heterogeneity configuration.
        
        Checks for:
        - Presence of heterogeneity section
        - enabled: true
        - Required fields (trajectory_classes, patient_parameters)
        - Valid trajectory proportions sum to 1.0
        """
```

#### 1. HeterogeneousABS Class

```python
class HeterogeneousABS(AgentBasedSimulation):
    """
    Agent-based simulation with patient heterogeneity.
    
    Extends the base ABS to model individual patient characteristics
    that affect treatment response and disease progression.
    """
    
    def __init__(self, config, start_date: datetime):
        """
        Initialize with standard config plus heterogeneity parameters.
        
        Parameters
        ----------
        config : SimulationConfig
            Standard configuration object
        start_date : datetime
            Simulation start date
        """
        
    def add_patient(self, patient_id: str, protocol_name: str):
        """
        Add a heterogeneous patient to the simulation.
        
        Overrides base method to create HeterogeneousPatient instances
        with individual characteristics.
        """
        
    def _assign_patient_characteristics(self, patient_id: str) -> Dict[str, Any]:
        """
        Assign heterogeneous characteristics to a patient.
        
        Returns
        -------
        Dict containing:
        - trajectory_class: str
        - treatment_responder_type: float
        - disease_aggressiveness: float
        - max_achievable_va: float
        - resistance_rate: float
        """
```

#### 2. HeterogeneousPatient Class

```python
class HeterogeneousPatient(Patient):
    """
    Patient with heterogeneous characteristics.
    
    Extends base Patient class with individual response parameters.
    """
    
    def __init__(self, patient_id: str, initial_state: PatientState, 
                 characteristics: Dict[str, Any]):
        """
        Initialize with standard state plus heterogeneous characteristics.
        
        Parameters
        ----------
        characteristics : Dict[str, Any]
            Individual patient characteristics including:
            - trajectory_class: Patient responder category
            - treatment_responder_type: Treatment effect multiplier
            - disease_aggressiveness: Progression rate multiplier
            - max_achievable_va: Vision ceiling
            - resistance_rate: Treatment resistance development
        """
        
    def update_vision(self, treatment_given: bool, weeks_elapsed: float) -> float:
        """
        Update vision with heterogeneous response.
        
        Implements the heterogeneous vision change model incorporating
        individual patient characteristics.
        """
```

#### 3. HeterogeneityManager Class

```python
class HeterogeneityManager:
    """
    Manages heterogeneity parameters and patient assignment.
    
    Responsible for parsing configuration, assigning patient
    characteristics, and tracking population statistics.
    """
    
    def __init__(self, heterogeneity_config: Dict[str, Any]):
        """Initialize from heterogeneity configuration section."""
        
    def assign_trajectory_class(self) -> str:
        """Randomly assign a patient to a trajectory class."""
        
    def generate_patient_characteristics(self, trajectory_class: str, 
                                       baseline_va: float) -> Dict[str, Any]:
        """Generate correlated patient characteristics."""
        
    def should_catastrophic_event_occur(self, event_type: str, 
                                       weeks_elapsed: float) -> bool:
        """Check if a catastrophic event should occur."""
```

### Data Flow

1. **Initialization Phase**:
   ```
   Config → HeterogeneousABS → HeterogeneityManager
                            ↓
                    Parse heterogeneity section
                            ↓
                    Validate parameters
   ```

2. **Patient Creation**:
   ```
   add_patient() → Assign trajectory class
                ↓
         Generate baseline VA
                ↓
         Generate correlated characteristics
                ↓
         Create HeterogeneousPatient
   ```

3. **Vision Update**:
   ```
   process_event() → Patient.update_vision()
                  ↓
           Calculate treatment benefit (with multiplier)
                  ↓
           Calculate disease progression (with multiplier)
                  ↓
           Apply ceiling effect
                  ↓
           Check catastrophic events
                  ↓
           Add measurement noise
   ```

### Configuration Schema

```yaml
heterogeneity:
  enabled: boolean
  version: string
  
  trajectory_classes:
    <class_name>:
      proportion: float (0-1)
      description: string
      parameters:
        <parameter_name>:
          distribution: string (normal|lognormal|beta|uniform)
          # distribution-specific parameters
  
  patient_parameters:
    <parameter_name>:
      distribution: string
      # distribution parameters
      correlation_with_baseline_va: float (-1 to 1)
  
  catastrophic_events:
    <event_name>:
      probability_per_month: float
      vision_impact:
        distribution: string
        # distribution parameters
      permanent: boolean
  
  variance_components:
    between_patient: float (0-1)
    within_patient: float (0-1)
    measurement: float (0-1)
  
  validation:
    # Target metrics for validation
```

### Algorithms

#### Patient Characteristic Assignment

```python
def assign_patient_characteristics(baseline_va: float) -> Dict:
    # 1. Assign trajectory class based on proportions
    trajectory_class = weighted_random_choice(trajectory_classes)
    
    # 2. Generate base characteristics from class parameters
    characteristics = generate_from_class(trajectory_class)
    
    # 3. Apply correlations with baseline VA
    if baseline_va > 70:
        characteristics['treatment_responder_type'] *= 1.3
        characteristics['disease_aggressiveness'] *= 0.7
    
    # 4. Calculate max achievable VA
    offset = sample_distribution(max_va_offset_params)
    characteristics['max_achievable_va'] = min(85, baseline_va + offset)
    
    return characteristics
```

#### Heterogeneous Vision Update

```python
def update_vision(current_va: float, treatment: bool, weeks: float) -> float:
    # 1. Treatment effect (heterogeneous)
    if treatment:
        base_effect = 5.0
        ceiling_factor = 1 - (current_va / max_achievable_va)
        treatment_benefit = base_effect * treatment_responder_type * ceiling_factor
    else:
        treatment_benefit = 0
    
    # 2. Disease progression (heterogeneous)
    base_progression = -0.5
    progression = base_progression * disease_aggressiveness * weeks
    
    # 3. Treatment resistance
    if treatment:
        treatments_received += 1
        resistance_factor = exp(-resistance_rate * treatments_received)
        treatment_benefit *= resistance_factor
    
    # 4. Random walk (small)
    noise = normal(0, 2)
    
    # 5. Catastrophic events (rare)
    catastrophic_drop = 0
    for event in catastrophic_events:
        if random() < event.probability * weeks:
            catastrophic_drop = sample_distribution(event.impact)
    
    # 6. Apply changes
    new_va = current_va + treatment_benefit + progression + noise + catastrophic_drop
    return clip(new_va, 0, 85)
```

## Validation

### Validation Metrics

The engine must track and report:

1. **Population Statistics**:
   - Mean vision change at 7 years
   - Standard deviation of vision change
   - Distribution percentiles (25th, 50th, 75th)

2. **Correlation Metrics**:
   - Year 2 vs Year 7 correlation
   - Age vs outcome correlation

3. **Outcome Proportions**:
   - % maintaining >70 letters
   - % declining to <35 letters
   - % with catastrophic events

### Validation Targets (from Seven-UP)

```python
VALIDATION_TARGETS = {
    'mean_change_7_years': -8.6,
    'std_7_years': 30,
    'year2_year7_correlation': 0.97,
    'proportion_above_70': 0.25,
    'proportion_below_35': 0.35,
    'iqr': 40  # Interquartile range
}
```

## Interface Specifications

### Input Interface

```python
# Configuration loading
config = SimulationConfig.from_yaml('protocol_with_heterogeneity.yaml')

# Automatic engine selection via factory
from simulation.abs_factory import ABSFactory
sim = ABSFactory.create_simulation(config, start_date)
# Console output: "✓ Heterogeneity configuration detected - using HeterogeneousABS engine"
# or: "→ Standard configuration - using AgentBasedSimulation engine"
```

### Engine Selection Logic

The `ABSFactory` automatically selects the appropriate engine based on configuration content:

1. **Checks for heterogeneity section** in the protocol configuration
2. **Validates heterogeneity is enabled** (`enabled: true`)
3. **Verifies required fields** are present
4. **Validates trajectory proportions** sum to 1.0
5. **Returns appropriate engine** with console notification

No manual engine selection is required - the configuration content drives the choice.

### Output Interface

The output format remains identical to the standard ABS:

```python
results = sim.get_results()
# Returns:
{
    'patients': Dict[str, Patient],  # Patient objects with histories
    'events': List[Event],           # Event log
    'validation_metrics': Dict       # (optional) If heterogeneity enabled
}
```

## Error Handling

1. **Missing Heterogeneity Section**: Falls back to homogeneous model
2. **Invalid Distribution Parameters**: Raises `ConfigurationError`
3. **Proportions Don't Sum to 1**: Raises `ValidationError`
4. **Correlation Out of Range**: Raises `ValidationError`

## Performance Considerations

1. **Memory**: Additional ~100 bytes per patient for characteristics
2. **Computation**: ~10% overhead for heterogeneous calculations
3. **Caching**: Pre-compute distribution samples where possible

## Testing Requirements

1. **Unit Tests**:
   - Configuration parsing
   - Patient characteristic assignment
   - Vision update calculations
   - Catastrophic event triggering

2. **Integration Tests**:
   - Full simulation runs
   - Validation metric calculation
   - Comparison with homogeneous engine

3. **Validation Tests**:
   - Seven-UP reproduction
   - Sensitivity analysis
   - Edge cases (all good/poor responders)

## Future Extensions

1. **Adaptive Heterogeneity**: Parameters that change over time
2. **Biomarker Modeling**: Explicit OCT/fluid modeling
3. **Personalized Protocols**: Protocol selection based on characteristics
4. **Machine Learning**: Learn parameters from real data

## Appendix: Distribution Sampling

### Supported Distributions

1. **Normal**: `normal(mean, std)`
2. **Lognormal**: `lognormal(mean, std)`
3. **Beta**: `beta(alpha, beta)`
4. **Uniform**: `uniform(min, max)`

### Correlation Implementation

For correlated parameters:
```python
# Generate base value
base_value = sample_distribution(param_config)

# Apply correlation with baseline VA
if correlation != 0:
    z_score = (baseline_va - population_mean_va) / population_std_va
    adjustment = correlation * z_score * param_std
    correlated_value = base_value + adjustment
```