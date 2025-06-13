# Pragmatic State Refactoring Plan

## Reality Check
- **Platform**: Streamlit Community Cloud (free tier)
- **Users**: Few dozen at most
- **Status**: Pre-beta, not in production
- **Constraints**: No persistent storage, no databases, session-only state

## What We DON'T Need
❌ SQLite or any database
❌ Event bus or async operations  
❌ Persistent caching
❌ Complex memory management
❌ Multi-user coordination
❌ Performance monitoring at scale
❌ Schema versioning/migrations
❌ Enterprise features

## What We ACTUALLY Need

### 1. Fix Current Bugs (1-2 days)
```python
# Problems:
- KeyError 'spec' when loading simulations
- Parameters not updating when switching simulations
- Audit trail showing wrong simulation
- State not properly synced

# Solution:
- Fix load_simulation_results() to load ALL data
- Ensure protocol['spec'] is always included
- Clear session state before loading new simulation
```

### 2. Simple Multi-Simulation Support (2-3 days)
```python
# In session state:
st.session_state = {
    # Simple registry - just a dict
    'simulation_registry': {
        'sim_id_1': {
            'results': SimulationResults,
            'protocol': dict with spec,
            'parameters': dict,
            'audit_trail': list
        },
        'sim_id_2': {...}
    },
    'active_sim_id': 'sim_id_1',
    'comparison_sim_ids': []  # For future comparison
}
```

### 3. Clean Helper Functions (1 day)
```python
# utils/state_manager.py - Simple functions, not a service

def load_simulation(sim_id: str, set_active=True):
    """Load simulation and add to registry"""
    # Load from disk
    data = load_from_disk(sim_id)
    
    # Add to registry
    if 'simulation_registry' not in st.session_state:
        st.session_state.simulation_registry = {}
    
    st.session_state.simulation_registry[sim_id] = data
    
    if set_active:
        st.session_state.active_sim_id = sim_id
        # For backward compatibility
        st.session_state.simulation_results = data

def get_active_simulation():
    """Get currently active simulation"""
    if 'active_sim_id' not in st.session_state:
        return None
    
    sim_id = st.session_state.active_sim_id
    return st.session_state.simulation_registry.get(sim_id)

def clear_old_simulations(keep_n=5):
    """Simple memory management - keep last N simulations"""
    registry = st.session_state.get('simulation_registry', {})
    if len(registry) > keep_n:
        # Remove oldest (simple FIFO)
        sim_ids = list(registry.keys())
        for sim_id in sim_ids[:-keep_n]:
            del registry[sim_id]
```

## Implementation Steps

### Step 1: Merge Current Work
```bash
git add .
git commit -m "fix: Complete simulation export/import functionality"
git push
gh pr create --title "Fix simulation state management issues"
# After review/merge
git checkout main
git pull
```

### Step 2: Create Feature Branch
```bash
git checkout -b feature/simple-state-refactor
```

### Step 3: Fix Immediate Issues (Day 1)
1. Fix `load_simulation_results()` in `utils/simulation_loader.py`
2. Ensure protocol['spec'] is loaded from saved protocol.yaml
3. Test that switching simulations updates all state

### Step 4: Add Registry Support (Day 2)
1. Create `utils/state_manager.py` with simple functions
2. Update pages to use `get_active_simulation()`
3. Add registry with 5-simulation limit

### Step 5: Update UI (Day 3)
1. Update Simulations page to show active marker
2. Update Analysis to use active simulation
3. Add simple "Compare" button (future feature)

### Step 6: Test and Merge (Day 4)
1. Test all workflows
2. Update any broken tests
3. Create PR and merge

## What This Achieves

✅ Fixes all current bugs
✅ Supports multiple simulations in memory
✅ Sets foundation for comparison feature
✅ Keeps it SIMPLE
✅ Works within Streamlit constraints
✅ Can be done in less than a week

## What We Defer

- Complex comparison UI (do simple 2-way first)
- Search/filtering (not needed for dozens of simulations)
- Performance optimization (not needed at this scale)
- Advanced features (YAGNI - You Aren't Gonna Need It)

## Code Example - Complete Fix

```python
# utils/simulation_loader.py - Fixed version
def load_simulation_results(sim_id: str) -> bool:
    """Load simulation results into session state registry"""
    try:
        # Load results
        results_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
        results = ResultsFactory.load_results(results_path)
        
        # Load protocol with spec
        protocol_path = results_path / "protocol.yaml"
        if protocol_path.exists():
            import yaml
            with open(protocol_path) as f:
                protocol_data = yaml.safe_load(f)
                
            # Create protocol spec from saved data
            from protocols.v2.protocol_spec import ProtocolSpecification
            protocol_spec = ProtocolSpecification.from_dict(protocol_data)
        else:
            protocol_spec = None
        
        # Load audit trail
        audit_path = results_path / "audit_log.json"
        if audit_path.exists():
            with open(audit_path) as f:
                audit_trail = json.load(f)
        else:
            audit_trail = []
        
        # Build complete simulation data
        sim_data = {
            'results': results,
            'protocol': {
                'name': results.metadata.protocol_name,
                'version': results.metadata.protocol_version,
                'path': str(results.metadata.protocol_path),
                'spec': protocol_spec  # Now included!
            },
            'parameters': {
                'engine': results.metadata.engine_type,
                'n_patients': results.metadata.n_patients,
                'duration_years': results.metadata.duration_years,
                'seed': results.metadata.random_seed
            },
            'audit_trail': audit_trail
        }
        
        # Initialize registry if needed
        if 'simulation_registry' not in st.session_state:
            st.session_state.simulation_registry = {}
            
        # Add to registry
        st.session_state.simulation_registry[sim_id] = sim_data
        st.session_state.active_sim_id = sim_id
        
        # Backward compatibility
        st.session_state.simulation_results = sim_data
        st.session_state.current_sim_id = sim_id
        
        # Clear old simulations if too many
        if len(st.session_state.simulation_registry) > 5:
            oldest = min(st.session_state.simulation_registry.keys())
            if oldest != sim_id:
                del st.session_state.simulation_registry[oldest]
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to load simulation {sim_id}: {e}")
        return False
```

## Success Criteria

1. ✅ No more KeyError 'spec'
2. ✅ Selecting simulation updates all parameters
3. ✅ Audit trail shows correct simulation
4. ✅ Can hold 5 simulations in memory
5. ✅ Foundation for comparison feature
6. ✅ Less than 500 lines of new code
7. ✅ Completed in under a week