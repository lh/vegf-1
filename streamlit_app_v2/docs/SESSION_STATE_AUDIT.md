# Session State Management Audit

## Overview

This document provides a comprehensive audit of session state management across the Streamlit APE V2 application, identifying inconsistencies and proposing refactoring strategies.

## Current Session State Keys and Usage

### 1. Core Simulation State

#### `simulation_results`
- **Type**: Dict or None
- **Structure**:
  ```python
  {
      'results': SimulationResults,  # The actual results object
      'protocol': {
          'name': str,
          'version': str,
          'path': str,
          'spec': ProtocolSpecification (optional)
      },
      'parameters': {
          'engine': str,
          'n_patients': int,
          'duration_years': float,
          'seed': int,
          'runtime': float (optional)
      },
      'audit_trail': list,
      'runtime': float (optional),
      'timestamp': str (optional),
      'storage_type': str (optional),
      'memory_usage_mb': float (optional)
  }
  ```
- **Set by**: 
  - `pages/2_Simulations.py` (after running simulation)
  - `utils/simulation_loader.py` (when loading from disk)
- **Read by**: 
  - `pages/3_Analysis_Overview.py`
  - `components/export.py`
  - `APE.py` (for status display)

#### `current_sim_id`
- **Type**: str or None
- **Purpose**: Tracks the currently selected simulation ID
- **Set by**:
  - `pages/2_Simulations.py` (when simulation is run or selected)
  - `utils/simulation_loader.py` (when loading)
  - `components/import_component.py` (after import)
- **Read by**:
  - `pages/2_Simulations.py` (to highlight selected)
  - `components/export.py` (to know what to export)
  - `utils/simulation_loader.py` (for auto-loading)

#### `current_protocol`
- **Type**: Dict or None
- **Structure**:
  ```python
  {
      'name': str,
      'version': str,
      'path': str,
      'spec': ProtocolSpecification
  }
  ```
- **Set by**: `pages/1_Protocol_Manager.py`
- **Read by**: 
  - `pages/2_Simulations.py` (to run simulations)
  - `APE.py` (for status display)

#### `audit_trail`
- **Type**: list or None
- **Purpose**: Stores simulation audit events
- **Set by**: `pages/2_Simulations.py`
- **Read by**: `pages/3_Analysis_Overview.py`
- **Note**: This is duplicated in `simulation_results['audit_trail']`

### 2. UI State

#### `show_manage`
- **Type**: bool
- **Purpose**: Toggle state for manage section in Simulations page
- **Set by**: `pages/2_Simulations.py`

#### `show_duplicate`, `show_delete`, `show_upload`
- **Type**: bool
- **Purpose**: Toggle states for various Protocol Manager actions
- **Set by**: `pages/1_Protocol_Manager.py`

#### `duplicate_success`, `creating_duplicate`
- **Type**: bool
- **Purpose**: Track duplicate protocol creation state
- **Set by**: `pages/1_Protocol_Manager.py`

### 3. Import/Export State

#### `imported_simulations`
- **Type**: set
- **Purpose**: Track which simulations were imported in this session
- **Set by**: `components/import_component.py`
- **Read by**: `pages/2_Simulations.py` (for visual indicator)

#### `imported_simulation`
- **Type**: bool
- **Purpose**: Flag that an import just happened
- **Set by**: `components/import_component.py`

### 4. Temporary State

#### `preset_patients`, `preset_duration`
- **Type**: int/float
- **Purpose**: Store values from preset buttons
- **Set by**: `pages/2_Simulations.py`
- **Read by**: Same page for input defaults

#### `selected_protocol_name`
- **Type**: str
- **Purpose**: Maintain protocol selection across reruns
- **Set by**: `pages/1_Protocol_Manager.py`

### 5. Visualization State

#### `visualization_mode`
- **Type**: str ('analysis' or 'presentation')
- **Purpose**: Control chart styling mode
- **Set by**: `utils/visualization_modes.py`

#### `export_config`
- **Type**: Dict
- **Purpose**: Store export settings for charts
- **Set by**: `utils/export_config.py`

## Major Issues Identified

### 1. Data Duplication
- `audit_trail` exists both as a top-level key and inside `simulation_results`
- Protocol information is stored in multiple places

### 2. Inconsistent Loading
- `simulation_results` might not be loaded even when `current_sim_id` exists
- The loader tries to fix this but it's a band-aid solution

### 3. Missing Data Contracts
- No clear schema for what data should be in each key
- Different components expect different structures

### 4. State Synchronization Issues
- When importing, multiple keys need to be set in correct order
- No atomic operations for related state changes

### 5. Protocol Spec Loading
- Protocol spec is loaded differently in different contexts
- Sometimes it's a full ProtocolSpecification object, sometimes just metadata

### 6. Memory Management
- Large simulation results stored entirely in session state
- No cleanup mechanism for old data

## Proposed Refactoring

### 1. Centralized State Manager

Create a single class to manage all simulation-related state:

```python
class SimulationStateManager:
    """Centralized manager for all simulation-related session state"""
    
    @staticmethod
    def set_current_simulation(sim_id: str, results: SimulationResults = None):
        """Set the current simulation with atomic updates"""
        if results is None:
            # Load from disk
            results = load_simulation_from_disk(sim_id)
        
        # Atomic update of all related state
        st.session_state.update({
            'current_sim_id': sim_id,
            'simulation_results': results,
            'last_updated': datetime.now()
        })
    
    @staticmethod
    def get_current_simulation() -> Optional[SimulationResults]:
        """Get current simulation, loading if necessary"""
        if 'simulation_results' in st.session_state:
            return st.session_state.simulation_results
        elif 'current_sim_id' in st.session_state:
            # Auto-load
            return load_simulation_from_disk(st.session_state.current_sim_id)
        return None
```

### 2. Unified Data Structure

Define clear schemas for session state data:

```python
@dataclass
class SessionSimulationData:
    """Complete simulation data stored in session state"""
    sim_id: str
    results: SimulationResults
    protocol: ProtocolInfo
    parameters: SimulationParameters
    metadata: SimulationMetadata
    
    def to_dict(self) -> dict:
        """Convert to dictionary for session state storage"""
        ...
```

### 3. State Lifecycle Management

Implement clear lifecycle methods:

```python
def initialize_session_state():
    """Initialize all session state keys with defaults"""
    defaults = {
        'current_simulation': None,
        'current_protocol': None,
        'ui_state': UIState(),
        'import_history': set()
    }
    
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def clear_simulation_state():
    """Clear all simulation-related state"""
    keys_to_clear = ['current_simulation', 'current_sim_id']
    for key in keys_to_clear:
        st.session_state.pop(key, None)
```

### 4. Migration Strategy

1. **Phase 1**: Create state manager alongside existing code
2. **Phase 2**: Gradually migrate pages to use state manager
3. **Phase 3**: Remove old state management code
4. **Phase 4**: Add state persistence/recovery features

### 5. Best Practices

1. **Single Source of Truth**: Each piece of data should have one canonical location
2. **Atomic Updates**: Related state should be updated together
3. **Lazy Loading**: Load heavy data only when needed
4. **Clear Contracts**: Document expected data structures
5. **Validation**: Validate state on read/write
6. **Cleanup**: Implement state cleanup for memory management

## Implementation Priority

1. **High Priority**:
   - Fix data duplication issues
   - Implement consistent loading strategy
   - Create unified simulation data structure

2. **Medium Priority**:
   - Implement state manager class
   - Add validation and contracts
   - Clean up UI state management

3. **Low Priority**:
   - Add persistence features
   - Implement state history/undo
   - Add memory optimization

## Conclusion

The current session state management is functional but fragmented. A centralized approach with clear data contracts and lifecycle management would significantly improve maintainability and reduce bugs related to state synchronization.