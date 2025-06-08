"""
Test script for state management fixes.

Run with: streamlit run test_state_fix.py
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.state_helpers import (
    init_simulation_registry, add_simulation_to_registry,
    list_simulation_summaries, set_active_simulation,
    get_active_simulation, save_protocol_spec
)

st.title("State Management Test")

# Initialize registry
init_simulation_registry()

# Show current state
st.header("Session State Contents")
st.json({
    "has_simulation_registry": "simulation_registry" in st.session_state,
    "registry_size": len(st.session_state.get("simulation_registry", {})),
    "active_simulation_id": st.session_state.get("active_simulation_id"),
    "has_simulation_results": "simulation_results" in st.session_state,
    "has_audit_trail": "audit_trail" in st.session_state
})

# Test adding simulations
if st.button("Add Test Simulation"):
    test_sim = {
        'protocol': {'name': 'Test Protocol', 'version': '1.0'},
        'parameters': {
            'n_patients': 100,
            'duration_years': 2,
            'engine': 'abs',
            'seed': 42
        },
        'timestamp': '2025-01-06T10:00:00',
        'audit_trail': [
            {'event': 'test_event', 'timestamp': '2025-01-06T10:00:00'}
        ]
    }
    
    # Save protocol spec
    protocol_path = Path("protocols/eylea.yaml")
    if protocol_path.exists():
        save_protocol_spec(test_sim, protocol_path)
    
    # Add to registry
    import uuid
    sim_id = f"test_{uuid.uuid4().hex[:8]}"
    add_simulation_to_registry(sim_id, test_sim)
    st.success(f"Added simulation: {sim_id}")
    st.rerun()

# Show simulations
st.header("Simulations in Registry")
summaries = list_simulation_summaries()
if summaries:
    for sim in summaries:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.text(f"{sim['sim_id']} - {sim['protocol_name']}")
        col2.text(f"{sim['n_patients']} patients")
        if col3.button("Set Active", key=f"active_{sim['sim_id']}"):
            set_active_simulation(sim['sim_id'])
            st.success(f"Set {sim['sim_id']} as active")
            st.rerun()
else:
    st.info("No simulations in registry")

# Show active simulation
st.header("Active Simulation")
active_sim = get_active_simulation()
if active_sim:
    st.json({
        'protocol': active_sim.get('protocol', {}).get('name'),
        'parameters': active_sim.get('parameters'),
        'has_yaml': 'yaml_content' in active_sim.get('protocol', {}),
        'has_audit_trail': 'audit_trail' in active_sim
    })
else:
    st.info("No active simulation")

# Test eviction
st.header("Test FIFO Eviction")
if st.button("Add 10 Simulations"):
    for i in range(10):
        test_sim = {
            'protocol': {'name': f'Protocol {i}', 'version': '1.0'},
            'parameters': {'n_patients': 100 + i*10, 'duration_years': 1, 'engine': 'abs'}
        }
        add_simulation_to_registry(f"evict_test_{i}", test_sim)
    st.success("Added 10 simulations - should only keep last 5")
    st.rerun()

if st.button("Clear All"):
    from utils.state_helpers import clear_simulation_registry
    clear_simulation_registry()
    st.success("Cleared all simulations")
    st.rerun()