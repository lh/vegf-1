# Fix Strategy for Export/Import Integration Issues

## Root Cause Summary

The app uses two separate session state variables:
1. `current_sim_id` - The ID of the selected simulation
2. `simulation_results` - The actual loaded results object

**Problem**: Only running a NEW simulation sets both. Selecting or importing only sets `current_sim_id`.

## Fix Implementation Plan

### Fix 1: Create a Unified Loading Function

Add a function that loads simulation results whenever `current_sim_id` changes:

```python
def load_simulation_results(sim_id: str) -> bool:
    """Load simulation results into session state."""
    try:
        # Load results from disk
        results = ResultsFactory.load_results(sim_id)
        
        # Load metadata to get protocol info
        metadata_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Set session state
        st.session_state.simulation_results = {
            'results': results,
            'protocol': {
                'name': metadata.get('protocol_name', 'Unknown'),
                'version': metadata.get('protocol_version', '1.0'),
                'path': metadata.get('protocol_path', '')
            },
            'parameters': {
                'engine': metadata.get('engine_type', 'abs'),
                'n_patients': metadata.get('n_patients', 0),
                'duration_years': metadata.get('duration_years', 0),
                'seed': metadata.get('seed', 42),
                'runtime': metadata.get('runtime_seconds', 0)
            },
            'audit_trail': metadata.get('audit_trail', [])
        }
        return True
    except Exception as e:
        st.error(f"Failed to load simulation {sim_id}: {e}")
        return False
```

### Fix 2: Update Selection Logic

In `pages/2_Simulations.py`, when selecting a simulation:

```python
if ape_button(...):
    st.session_state.current_sim_id = sim['id']
    load_simulation_results(sim['id'])  # Add this line
    st.rerun()
```

### Fix 3: Update Import Logic

In `components/import_component.py`, after successful import:

```python
# Set session state
st.session_state.current_sim_id = sim_id
load_simulation_results(sim_id)  # Add this line
st.session_state.imported_simulation = True
```

### Fix 4: Update Analysis Overview

Add a check at the start to ensure results are loaded:

```python
# Check if results are available
if not st.session_state.get('simulation_results'):
    # Try to load from current_sim_id
    if st.session_state.get('current_sim_id'):
        if not load_simulation_results(st.session_state.current_sim_id):
            # Failed to load
            st.error("Failed to load simulation data")
            # Show navigation button...
    else:
        # No simulation selected
        # Show navigation button...
```

### Fix 5: Manage Button Visibility

Change line 130 in `pages/2_Simulations.py`:

```python
# From:
if st.session_state.get('current_sim_id'):

# To:
if simulations or st.session_state.get('current_sim_id'):
```

### Fix 6: Add IMPORTED Badge

The logic is already there (line 110-111), but we need to ensure `imported_simulations` persists properly.

## Implementation Order

1. **First**: Create the `load_simulation_results` function
2. **Second**: Update selection logic to use it
3. **Third**: Update import logic to use it
4. **Fourth**: Update Analysis Overview to check and load
5. **Fifth**: Fix Manage button visibility
6. **Sixth**: Verify IMPORTED badge works

## Testing After Each Fix

1. Select different simulations → Verify Analysis Overview updates
2. Import a simulation → Verify it becomes current and Analysis shows it
3. Start fresh (no simulations) → Import → Verify it works
4. Verify Manage button always visible
5. Verify IMPORTED badges show correctly

## Expected Outcome

- Selecting any simulation (recent or imported) will load its data
- Analysis Overview will always show the current simulation
- Import will properly set the imported simulation as current
- Manage button will be accessible even before running simulations
- Visual indicators (Selected ✓, IMPORTED) will work correctly