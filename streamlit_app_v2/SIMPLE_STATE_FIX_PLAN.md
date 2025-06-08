# Simple State Management Fix Plan

## 🎯 Goal: Fix State Bugs & Enable Multi-Simulation Support

**Timeline**: 2-3 days  
**Approach**: Minimal patches to existing system  
**Risk**: Low - no architectural changes

## 📋 Executive Summary

The current state management has 3 fixable bugs:
1. Duplicate `audit_trail` key
2. Protocol spec not loading properly  
3. No support for multiple simulations

We can fix these with ~300 lines of targeted changes, no refactoring needed.

## 🔧 Implementation Plan

### Day 1: Fix State Loading (4-6 hours)

#### 1.1 Remove Duplicate audit_trail (30 min)
```python
# File: pages/2_Simulations.py
# Line 403 - DELETE this line:
st.session_state.audit_trail = runner.audit_log  # DELETE THIS

# Audit trail is already saved in simulation_results['audit_trail']
```

#### 1.2 Fix Protocol Spec Loading (2 hours)
```python
# File: utils/simulation_loader.py
# Update load_simulation_results() to properly reconstruct protocol spec

# Current issue: Lines 66-84 expect wrong format
# Fix: Use ProtocolSpecification.from_dict() instead of from_yaml()

# Replace lines 58-89 with:
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
        # For pre-beta, fail fast
        raise ValueError(f"Could not load protocol specification: {e}")
```

#### 1.3 Add Simple Registry Support (2 hours)
```python
# File: utils/simulation_loader.py
# Add after line 111 (before setting session_state.simulation_results):

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

# Keep only last 5 simulations in memory
if len(st.session_state.simulation_registry) > 5:
    # Remove oldest (simple FIFO)
    oldest_sim = list(st.session_state.simulation_registry.keys())[0]
    del st.session_state.simulation_registry[oldest_sim]
    logger.info(f"Evicted oldest simulation from registry: {oldest_sim}")

# Set as active simulation
st.session_state.active_sim_id = sim_id

# Keep backward compatibility
st.session_state.simulation_results = st.session_state.simulation_registry[sim_id]
st.session_state.current_sim_id = sim_id
```

### Day 2: Add Helper Functions & Update Pages (4-6 hours)

#### 2.1 Create Simple State Helpers (2 hours)
```python
# New file: utils/state_helpers.py
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

#### 2.2 Update Pages to Use Helpers (2 hours)

**Analysis Overview** (pages/3_Analysis_Overview.py):
```python
# Add at top
from utils.state_helpers import get_active_simulation

# Replace simulation loading logic with:
simulation_data = get_active_simulation()
if not simulation_data:
    st.warning("No simulation selected. Please run or load a simulation first.")
    if st.button("Go to Simulations"):
        st.switch_page("pages/2_Simulations.py")
    return

# Use simulation_data instead of st.session_state.simulation_results
results = simulation_data['results']
protocol = simulation_data['protocol']
parameters = simulation_data['parameters']
audit_trail = simulation_data['audit_trail']
```

**Simulations Page** (pages/2_Simulations.py):
```python
# Add simulation selector if multiple loaded
from utils.state_helpers import get_simulation_list, set_active_simulation

sim_list = get_simulation_list()
if len(sim_list) > 1:
    st.subheader("Loaded Simulations")
    
    # Simple selection UI
    for sim in sim_list:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{sim['name']}** - {sim['patients']} patients, {sim['duration']} years")
        with col2:
            if sim['is_active']:
                st.success("Active")
            else:
                if st.button("Select", key=f"select_{sim['id']}"):
                    set_active_simulation(sim['id'])
                    st.rerun()
        with col3:
            # Future: Add compare checkbox
            st.empty()
```

### Day 3: Testing & Edge Cases (4 hours)

#### 3.1 Test All Workflows (2 hours)
- [ ] Run simulation → Check registry has entry
- [ ] Switch between simulations → Check parameters update
- [ ] Import simulation → Check it's added to registry
- [ ] Load 6+ simulations → Check oldest is evicted
- [ ] Refresh page → Check state persists

#### 3.2 Fix Edge Cases (2 hours)
- [ ] Handle missing protocol.yaml gracefully
- [ ] Handle corrupted session state
- [ ] Test with both ABS and DES engines
- [ ] Verify audit trail displays correctly

## 📁 Files to Modify

1. **utils/simulation_loader.py** (~50 lines changed)
   - Fix protocol loading
   - Add registry support
   - Remove audit_trail duplication

2. **utils/state_helpers.py** (new file, ~100 lines)
   - Simple helper functions
   - No classes or services

3. **pages/2_Simulations.py** (~20 lines changed)
   - Remove duplicate audit_trail assignment
   - Add simulation selector UI

4. **pages/3_Analysis_Overview.py** (~10 lines changed)
   - Use get_active_simulation()
   - Handle no simulation case

## ✅ Success Criteria

1. **No more KeyError 'spec'** - Protocol loads correctly
2. **No duplicate state** - audit_trail only in one place
3. **Parameters update** - Switching simulations updates all UI
4. **Registry works** - Can hold 5 simulations
5. **Backward compatible** - Old code still works
6. **Tests pass** - All existing tests still green

## 🚫 What We're NOT Doing

- ❌ No service classes
- ❌ No event systems
- ❌ No complex architecture
- ❌ No database or caching
- ❌ No async operations
- ❌ No migration scripts

## 🎉 Benefits

- **Fixes all current bugs** with minimal changes
- **Enables comparison feature** (registry supports multiple sims)
- **Maintains simplicity** (just functions and dicts)
- **Works on Streamlit** (no external dependencies)
- **Ships this week** (not next month)

## 🔄 Future Extensions (If Needed)

Once this works, we can later add:
- Simple 2-simulation comparison view
- Session state persistence (pickle to disk)
- Better memory management
- Search/filter (if we get to 50+ simulations)

But for now, **KISS** - Keep It Simple, Streamlit!