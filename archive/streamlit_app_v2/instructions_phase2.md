# 📋 PHASE 2 IMPLEMENTATION INSTRUCTIONS

**IMPORTANT**: This is the active implementation plan for Phase 2 - Simple State Management Fix

## 🎯 Current Phase: State Management Bug Fixes

### Overview
Fix three specific bugs in state management and add basic multi-simulation support. No architectural changes, just targeted fixes.

**Timeline**: 2-3 days  
**Complexity**: Low - ~300 lines of changes  
**Risk**: Minimal - backward compatible patches

## 🐛 Bugs to Fix

1. **Duplicate audit_trail** - Exists in two places, causes sync issues
2. **KeyError 'spec'** - Protocol specification not loading properly  
3. **No multi-simulation support** - Can't compare simulations

## 📍 Pre-Implementation Checklist

- [ ] Current work merged to main branch
- [ ] New branch created: `feature/simple-state-fix`
- [ ] All tests passing on main
- [ ] Backup of current working state

## 🛠️ Day 1: Core Fixes (4-6 hours)

### Task 1.1: Remove Duplicate audit_trail (30 min)
**File**: `pages/2_Simulations.py`  
**Line**: 403  
**Action**: DELETE the line `st.session_state.audit_trail = runner.audit_log`

```python
# BEFORE (line 403):
st.session_state.audit_trail = runner.audit_log  # DELETE THIS LINE

# AFTER:
# Line removed - audit_trail only stored in simulation_results['audit_trail']
```

**Test**: Run simulation, check audit trail displays correctly

### Task 1.2: Fix Protocol Spec Loading (2 hours)
**File**: `utils/simulation_loader.py`  
**Lines**: 58-89  
**Issue**: Trying to use `from_yaml()` on dict data

**Replace with**:
```python
# Load protocol specification if available
protocol_yaml_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id / "protocol.yaml"
if protocol_yaml_path.exists():
    try:
        import yaml
        with open(protocol_yaml_path) as f:
            protocol_data = yaml.safe_load(f)
        
        # Create ProtocolSpecification from the saved dict
        from protocols.v2.protocol_spec import ProtocolSpecification
        protocol_spec = ProtocolSpecification.from_dict(protocol_data)
        protocol_info['spec'] = protocol_spec
        logger.info(f"Loaded full protocol specification for {sim_id}")
        
    except Exception as e:
        logger.error(f"Failed to load protocol spec: {e}")
        # For pre-beta, fail fast - no graceful degradation
        raise ValueError(f"Could not load protocol specification: {e}")
else:
    # No protocol.yaml - this simulation is missing data
    raise ValueError(f"No protocol specification found for {sim_id}")
```

**Test**: Load existing simulation, verify no KeyError on treatment patterns tab

### Task 1.3: Add Registry Support (2 hours)
**File**: `utils/simulation_loader.py`  
**Location**: After line 111, before setting `simulation_results`

**Add**:
```python
# Initialize registry if needed
if 'simulation_registry' not in st.session_state:
    st.session_state.simulation_registry = {}

# Add to registry (with simple 5-simulation limit)
st.session_state.simulation_registry[sim_id] = {
    'results': results,
    'protocol': protocol_info,
    'parameters': parameters,
    'audit_trail': audit_trail
}

# Simple memory management - keep only last 5
if len(st.session_state.simulation_registry) > 5:
    # Remove oldest (FIFO)
    oldest_sim = list(st.session_state.simulation_registry.keys())[0]
    del st.session_state.simulation_registry[oldest_sim]
    logger.info(f"Evicted oldest simulation from registry: {oldest_sim}")

# Set as active simulation
st.session_state.active_sim_id = sim_id

# Backward compatibility - keep old keys working
st.session_state.simulation_results = st.session_state.simulation_registry[sim_id]
st.session_state.current_sim_id = sim_id
```

**Test**: Load 6 simulations, verify oldest is removed

## 🛠️ Day 2: Helper Functions & UI Updates (4-6 hours)

### Task 2.1: Create State Helpers (2 hours)
**New File**: `utils/state_helpers.py`

```python
"""
Simple state management helpers for multi-simulation support.
No services, no complexity - just functions.
"""

import streamlit as st
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_active_simulation() -> Optional[Dict[str, Any]]:
    """Get the currently active simulation data."""
    if 'active_sim_id' not in st.session_state:
        return None
    
    sim_id = st.session_state.active_sim_id
    registry = st.session_state.get('simulation_registry', {})
    return registry.get(sim_id)

def set_active_simulation(sim_id: str) -> bool:
    """Set a simulation as active (must already be loaded)."""
    registry = st.session_state.get('simulation_registry', {})
    
    if sim_id not in registry:
        logger.error(f"Simulation {sim_id} not in registry")
        return False
    
    st.session_state.active_sim_id = sim_id
    # Backward compatibility
    st.session_state.simulation_results = registry[sim_id]
    st.session_state.current_sim_id = sim_id
    
    return True

def get_simulation_list() -> list:
    """Get list of loaded simulations with basic info."""
    registry = st.session_state.get('simulation_registry', {})
    
    sim_list = []
    for sim_id, data in registry.items():
        sim_list.append({
            'id': sim_id,
            'name': data['protocol']['name'],
            'patients': data['parameters']['n_patients'],
            'duration': data['parameters']['duration_years'],
            'is_active': sim_id == st.session_state.get('active_sim_id')
        })
    
    return sim_list

def clear_inactive_simulations(keep_active: bool = True):
    """Clear all simulations except the active one."""
    if 'simulation_registry' not in st.session_state:
        return
    
    active_id = st.session_state.get('active_sim_id')
    registry = st.session_state.simulation_registry
    
    if keep_active and active_id and active_id in registry:
        # Keep only the active simulation
        st.session_state.simulation_registry = {
            active_id: registry[active_id]
        }
    else:
        # Clear all
        st.session_state.simulation_registry = {}
        st.session_state.active_sim_id = None
        st.session_state.simulation_results = None
        st.session_state.current_sim_id = None
```

### Task 2.2: Update Analysis Overview (30 min)
**File**: `pages/3_Analysis_Overview.py`  
**Location**: Top of file and main content area

**Add import**:
```python
from utils.state_helpers import get_active_simulation
```

**Replace simulation check**:
```python
# OLD:
if 'simulation_results' not in st.session_state or st.session_state.simulation_results is None:

# NEW:
simulation_data = get_active_simulation()
if not simulation_data:
    st.warning("No simulation selected. Please run or load a simulation first.")
    if st.button("Go to Simulations"):
        st.switch_page("pages/2_Simulations.py")
    return

# Use simulation_data components
results = simulation_data['results']
protocol = simulation_data['protocol']
parameters = simulation_data['parameters']
audit_trail = simulation_data['audit_trail']
```

### Task 2.3: Add Simulation Selector (1.5 hours)
**File**: `pages/2_Simulations.py`  
**Location**: After "Recent Simulations" section

**Add**:
```python
# Multi-simulation selector (if multiple loaded)
from utils.state_helpers import get_simulation_list, set_active_simulation

sim_list = get_simulation_list()
if len(sim_list) > 1:
    st.subheader("📊 Loaded Simulations")
    
    # Create a simple table of loaded simulations
    for sim in sim_list:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            if sim['is_active']:
                st.write(f"**➤ {sim['name']}** - {sim['patients']:,} patients, {sim['duration']} years")
            else:
                st.write(f"{sim['name']} - {sim['patients']:,} patients, {sim['duration']} years")
        
        with col2:
            st.caption(sim['id'][:20] + "...")
            
        with col3:
            if sim['is_active']:
                st.success("Active")
            else:
                if st.button("Select", key=f"select_{sim['id']}"):
                    set_active_simulation(sim['id'])
                    st.rerun()
        
        with col4:
            # Placeholder for future compare checkbox
            st.empty()
    
    # Memory usage indicator
    st.caption(f"Memory: {len(sim_list)}/5 simulations loaded")
```

## 🛠️ Day 3: Testing & Polish (4 hours)

### Task 3.1: Comprehensive Testing (2 hours)

**Test Checklist**:
- [ ] Run new simulation → Verify added to registry
- [ ] Load existing simulation → Verify protocol spec loads
- [ ] Switch between simulations → Verify all parameters update
- [ ] Import simulation → Verify added to registry and set active
- [ ] Load 6+ simulations → Verify memory limit works
- [ ] Check audit trail → Verify shows correct simulation
- [ ] Restart app → Verify session state cleared properly

### Task 3.2: Edge Case Fixes (1 hour)

**Handle missing protocol.yaml**:
```python
# Add to simulation_loader.py protocol loading section
if not protocol_yaml_path.exists():
    # Check if this is an old simulation without saved protocol
    if metadata.get('created_date', '') < '2024-06-01':
        logger.warning(f"Old simulation {sim_id} missing protocol.yaml")
        protocol_info['spec'] = None  # Will need to handle in UI
    else:
        raise ValueError(f"Protocol specification required but not found for {sim_id}")
```

### Task 3.3: Run Full Test Suite (1 hour)
```bash
# Ensure no regressions
python scripts/run_tests.py --all

# Run specific state tests
python -m pytest tests/integration/test_simulation_selection_sync.py -v

# UI smoke test
streamlit run APE.py
```

## ✅ Definition of Done

### Functionality
- [ ] No KeyError 'spec' when viewing treatment patterns
- [ ] Audit trail shows correct simulation data
- [ ] Can switch between loaded simulations
- [ ] Parameters update when switching simulations
- [ ] Import adds to registry and sets active
- [ ] Memory limit (5 simulations) enforced

### Code Quality
- [ ] No duplicate state keys
- [ ] All changes backward compatible
- [ ] Helper functions have docstrings
- [ ] Logging added for debugging
- [ ] No new dependencies added

### Testing
- [ ] All existing tests pass
- [ ] Manual testing checklist complete
- [ ] No console errors in browser
- [ ] Performance acceptable (< 1s to switch)

## 📝 Commit Strategy

Make atomic commits for each fix:
```bash
git add pages/2_Simulations.py
git commit -m "fix: Remove duplicate audit_trail assignment"

git add utils/simulation_loader.py
git commit -m "fix: Protocol spec loading from saved YAML"

git add utils/simulation_loader.py
git commit -m "feat: Add simulation registry for multi-sim support"

git add utils/state_helpers.py
git commit -m "feat: Add state helper functions"

git add pages/3_Analysis_Overview.py pages/2_Simulations.py
git commit -m "feat: Update UI to use simulation registry"
```

## 🚀 Deployment

1. Create PR: `gh pr create --title "Fix state management bugs and add multi-simulation support"`
2. Include test results in PR description
3. Link to this implementation plan
4. Request review
5. Merge to main after approval

## 📊 Success Metrics

- **Bug fixes**: 3/3 bugs resolved
- **Code changes**: < 400 lines modified/added
- **Test coverage**: Maintained or improved
- **Performance**: No degradation
- **Timeline**: Completed in 2-3 days

---

**Remember**: Keep it simple! No over-engineering, just fix the bugs and add basic multi-sim support.