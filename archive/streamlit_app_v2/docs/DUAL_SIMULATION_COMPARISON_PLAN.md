# Dual Simulation Comparison Feature Plan

## Overview
This document outlines the architecture changes needed to support comparing two simulations side by side in the Analysis Overview.

## Current State Architecture

### Session State Keys (Single Simulation)
- `active_simulation_id`: Currently selected simulation ID
- `current_sim_id`: Redundant key for backward compatibility
- `simulation_results`: Loaded simulation data
- `simulation_registry`: Registry of available simulations
- `audit_trail`: Audit trail for current simulation

### Problems with Current Approach
1. **Single simulation assumption**: All state keys assume only one simulation is active
2. **Redundant keys**: `active_simulation_id` and `current_sim_id` serve the same purpose
3. **Tight coupling**: Visualization components directly access global simulation state

## Proposed Architecture for Dual Comparison

### Option 1: Indexed Simulation Slots
```python
# Session state structure
st.session_state.comparison_mode = False  # Toggle for comparison mode
st.session_state.selected_simulations = {
    'primary': {
        'sim_id': 'sim_20250608_123456_02-00_blue-mountain',
        'results': SimulationResults object,
        'audit_trail': [...]
    },
    'secondary': {
        'sim_id': 'sim_20250608_654321_02-00_red-valley',
        'results': SimulationResults object,
        'audit_trail': [...]
    }
}
```

### Option 2: Array-Based Selection
```python
# Session state structure
st.session_state.comparison_mode = False
st.session_state.selected_simulations = [
    {'sim_id': '...', 'results': ..., 'position': 'left'},
    {'sim_id': '...', 'results': ..., 'position': 'right'}
]
```

### Recommended Approach: Option 1 with Named Slots

Benefits:
- Clear semantic meaning (primary vs secondary)
- Easy to extend (could add 'tertiary' for 3-way comparison)
- Backward compatible (primary can map to current active_simulation_id)

## Implementation Steps

### Phase 1: Refactor Current State Management
1. Create wrapper functions that abstract simulation access:
   ```python
   def get_primary_simulation():
       """Get primary simulation (backward compatible with single mode)"""
       if st.session_state.get('comparison_mode'):
           return st.session_state.selected_simulations.get('primary')
       else:
           return get_active_simulation()  # Current function
   
   def get_secondary_simulation():
       """Get secondary simulation for comparison"""
       if st.session_state.get('comparison_mode'):
           return st.session_state.selected_simulations.get('secondary')
       return None
   ```

2. Update all direct session state access to use these functions

### Phase 2: Update UI Components
1. **Simulation Selection UI**:
   - Add "Compare" toggle button
   - When enabled, show two selection columns
   - Each column allows independent simulation selection

2. **Analysis Overview Modifications**:
   - Split visualizations into two columns when in comparison mode
   - Add difference/delta visualizations
   - Synchronize axes for fair comparison

### Phase 3: Visualization Updates
1. **Chart Builder Updates**:
   - Accept optional `comparison_data` parameter
   - Support overlay mode (both datasets on same chart)
   - Support side-by-side mode (two charts)

2. **New Comparison-Specific Visualizations**:
   - Delta charts (difference between simulations)
   - Statistical comparison tables
   - Highlighted differences in parameters

## Migration Strategy

### Backward Compatibility
During transition, maintain both APIs:
```python
# Old API (single simulation)
results = get_active_simulation()

# New API (supports both modes)
primary = get_primary_simulation()
secondary = get_secondary_simulation()  # Returns None in single mode
```

### Gradual Rollout
1. **Phase 1**: Implement new state structure, keep UI unchanged
2. **Phase 2**: Add comparison toggle to Simulations page
3. **Phase 3**: Update Analysis Overview to support dual mode
4. **Phase 4**: Deprecate old session state keys

## UI/UX Considerations

### Selection Interface
```
[Toggle: Single | Compare]

When Compare is selected:
┌─────────────────┬─────────────────┐
│ Primary Sim     │ Secondary Sim   │
├─────────────────┼─────────────────┤
│ ○ blue-mountain │ ○ red-valley    │
│ ● green-forest  │ ○ yellow-sun    │
│ ○ purple-rain   │ ● orange-sunset │
└─────────────────┴─────────────────┘
```

### Visualization Layout
- **Single Mode**: Full-width visualizations (current behavior)
- **Compare Mode**: Split-screen with synchronized controls
- **Difference Mode**: Full-width showing deltas/comparisons

## Technical Considerations

### Performance
- Lazy loading: Only load secondary simulation when compare mode is activated
- Memory management: Clear secondary simulation when switching back to single mode
- Caching: Reuse loaded simulations from registry

### State Management
```python
def switch_to_comparison_mode():
    """Enable comparison mode, preserving current selection"""
    current = get_active_simulation()
    st.session_state.comparison_mode = True
    st.session_state.selected_simulations = {
        'primary': current,
        'secondary': None
    }

def switch_to_single_mode():
    """Disable comparison mode, keeping primary selection"""
    primary = st.session_state.selected_simulations.get('primary')
    st.session_state.comparison_mode = False
    if primary:
        set_active_simulation(primary['sim_id'])
```

## Future Extensions

### Multi-way Comparison (3+ simulations)
- Extend `selected_simulations` dict with more slots
- UI becomes a grid selector
- Visualizations adapt to show n-way comparisons

### Comparison Templates
- Save comparison setups (which sims, which views)
- Quick-load common comparisons
- Export comparison reports

## Action Items
1. [ ] Get feedback on proposed architecture
2. [ ] Create feature branch for comparison work
3. [ ] Implement Phase 1 state refactoring
4. [ ] Design comparison UI mockups
5. [ ] Plan visualization updates