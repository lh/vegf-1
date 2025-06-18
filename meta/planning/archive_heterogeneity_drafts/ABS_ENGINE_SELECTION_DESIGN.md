# ABS Engine Selection Design

Date: 2025-01-18  
Purpose: Design automatic engine selection based on configuration content

## Overview

Instead of requiring explicit engine selection, the system should automatically choose the appropriate ABS engine based on the presence and content of the heterogeneity configuration section.

## Current Approach (Manual Selection)

```python
# Current approach requires explicit selection
engine_type = 'abs'  # or 'heterogeneous_abs'
if engine_type == 'heterogeneous_abs':
    sim = HeterogeneousABS(config, start_date)
else:
    sim = AgentBasedSimulation(config, start_date)
```

## Proposed Approach (Automatic Selection)

### Option 1: Factory Pattern with Auto-Detection (Recommended)

```python
class ABSFactory:
    """Factory for creating appropriate ABS engine based on configuration."""
    
    @staticmethod
    def create_simulation(config: SimulationConfig, start_date: datetime) -> BaseSimulation:
        """
        Create appropriate simulation engine based on configuration.
        
        Returns
        -------
        BaseSimulation
            Either AgentBasedSimulation or HeterogeneousABS
        """
        # Check if configuration supports heterogeneity
        if ABSFactory._supports_heterogeneity(config):
            print("✓ Heterogeneity configuration detected - using HeterogeneousABS engine")
            return HeterogeneousABS(config, start_date)
        else:
            print("→ Standard configuration - using AgentBasedSimulation engine")
            return AgentBasedSimulation(config, start_date)
    
    @staticmethod
    def _supports_heterogeneity(config: SimulationConfig) -> bool:
        """Check if configuration has valid heterogeneity section."""
        try:
            # Get protocol configuration
            protocol_dict = config.protocol.to_dict() if hasattr(config.protocol, 'to_dict') else {}
            
            # Check for heterogeneity section
            if 'heterogeneity' not in protocol_dict:
                return False
            
            heterogeneity = protocol_dict['heterogeneity']
            
            # Check if enabled
            if not heterogeneity.get('enabled', False):
                return False
            
            # Validate minimum required fields
            required_fields = ['trajectory_classes', 'patient_parameters']
            for field in required_fields:
                if field not in heterogeneity:
                    print(f"⚠️  Heterogeneity section missing required field: {field}")
                    return False
            
            # Check trajectory classes sum to 1.0
            total_proportion = sum(
                tc.get('proportion', 0) 
                for tc in heterogeneity['trajectory_classes'].values()
            )
            if abs(total_proportion - 1.0) > 0.001:
                print(f"⚠️  Trajectory class proportions sum to {total_proportion}, not 1.0")
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error checking heterogeneity configuration: {e}")
            return False
```

### Option 2: Enhanced Configuration Loading

Modify the configuration loading to include engine selection:

```python
@dataclass
class SimulationConfig:
    # ... existing fields ...
    
    @property
    def recommended_engine(self) -> str:
        """Recommend engine based on configuration content."""
        if self._supports_heterogeneity():
            return 'heterogeneous_abs'
        return 'abs'
    
    def create_simulation(self, start_date: datetime) -> BaseSimulation:
        """Create appropriate simulation instance."""
        if self.recommended_engine == 'heterogeneous_abs':
            return HeterogeneousABS(self, start_date)
        return AgentBasedSimulation(self, start_date)
```

### Option 3: Override in Base Class

Make the base `AgentBasedSimulation` check and delegate:

```python
class AgentBasedSimulation(BaseSimulation):
    def __new__(cls, config, start_date):
        """Override object creation to return appropriate subclass."""
        if cls == AgentBasedSimulation and cls._should_use_heterogeneous(config):
            # Avoid circular import
            from .heterogeneous_abs import HeterogeneousABS
            return HeterogeneousABS(config, start_date)
        return super().__new__(cls)
```

## Recommended Implementation: Factory Pattern

### Usage in Code

```python
# In simulation runner or UI code
from simulation.abs_factory import ABSFactory

# Automatic engine selection
sim = ABSFactory.create_simulation(config, start_date)
# Console output: "✓ Heterogeneity configuration detected - using HeterogeneousABS engine"

# The simulation behaves identically regardless of engine
sim.add_patient("pat001", "eylea_treat_and_extend")
sim.run(end_date)
results = sim.get_results()
```

### Benefits

1. **Transparent**: Users don't need to know about engine variants
2. **Backward Compatible**: Existing code continues to work
3. **Fail-Safe**: Falls back to standard engine if configuration invalid
4. **Informative**: Tells user which engine is being used
5. **Extensible**: Easy to add more engine variants in future

### Configuration Examples

#### Configuration that triggers HeterogeneousABS:
```yaml
name: Eylea Treat and Extend
version: '1.0'
# ... standard parameters ...

heterogeneity:
  enabled: true
  version: '1.0'
  trajectory_classes:
    good_responders:
      proportion: 0.25
      # ... parameters ...
    moderate_decliners:
      proportion: 0.40
      # ... parameters ...
    poor_responders:
      proportion: 0.35
      # ... parameters ...
  patient_parameters:
    # ... parameters ...
```

#### Configuration that uses standard ABS:
```yaml
name: Eylea Treat and Extend
version: '1.0'
# ... standard parameters ...
# No heterogeneity section, or enabled: false
```

### Error Handling

The factory should handle various error cases gracefully:

1. **Missing heterogeneity section** → Use standard engine
2. **enabled: false** → Use standard engine
3. **Invalid proportions** → Warn and use standard engine
4. **Missing required fields** → Warn and use standard engine
5. **Malformed YAML** → Raise configuration error

### Integration Points

1. **Simulation Runner** (`ape/core/simulation_runner.py`):
```python
# Replace direct instantiation
# sim = AgentBasedSimulation(config, start_date)

# With factory
sim = ABSFactory.create_simulation(config, start_date)
```

2. **Testing**:
```python
def test_engine_selection():
    """Test automatic engine selection."""
    # Standard config
    config1 = load_config('standard.yaml')
    sim1 = ABSFactory.create_simulation(config1, datetime.now())
    assert isinstance(sim1, AgentBasedSimulation)
    assert not isinstance(sim1, HeterogeneousABS)
    
    # Heterogeneous config
    config2 = load_config('heterogeneous.yaml')
    sim2 = ABSFactory.create_simulation(config2, datetime.now())
    assert isinstance(sim2, HeterogeneousABS)
```

3. **UI Feedback**:
The factory's console output can be captured and displayed in Streamlit:
```python
# In Streamlit UI
with st.spinner("Initializing simulation engine..."):
    sim = ABSFactory.create_simulation(config, start_date)
    st.success(f"Using {sim.__class__.__name__} engine")
```

## Migration Path

1. **Phase 1**: Implement factory alongside existing code
2. **Phase 2**: Update simulation runner to use factory
3. **Phase 3**: Deprecate manual engine selection
4. **Phase 4**: Remove old instantiation code

## Documentation Updates

The user documentation would change from:

> "Select the appropriate engine type based on your needs"

To:

> "The simulation automatically selects the appropriate engine based on your protocol configuration. If your protocol includes a valid heterogeneity section, the advanced heterogeneous engine will be used automatically."

This approach makes heterogeneity a feature of the protocol, not a simulation setting, which is more intuitive and maintainable.