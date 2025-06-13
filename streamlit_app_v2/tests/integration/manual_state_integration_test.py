"""
Integration test for state management - requires Streamlit to be run.

This test is meant to be run manually with:
streamlit run tests/integration/test_state_integration.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.state_helpers import (
    init_simulation_registry, add_simulation_to_registry,
    list_simulation_summaries, set_active_simulation,
    get_active_simulation, save_protocol_spec,
    get_simulation_registry
)

st.title("State Management Integration Test")

# Test 1: Initialize registry
st.header("Test 1: Initialize Registry")
init_simulation_registry()
st.success("✓ Registry initialized")
st.json({
    "has_registry": "simulation_registry" in st.session_state,
    "registry_size": len(st.session_state.get("simulation_registry", {}))
})

# Test 2: Add simulations
st.header("Test 2: Add Simulations")
for i in range(3):
    test_sim = {
        'protocol': {'name': f'Protocol {i}', 'version': '1.0'},
        'parameters': {
            'n_patients': 100 + i*10,
            'duration_years': i + 1,
            'engine': 'abs'
        }
    }
    add_simulation_to_registry(f'test_sim_{i}', test_sim)

st.success("✓ Added 3 simulations")
summaries = list_simulation_summaries()
st.write(f"Number of simulations: {len(summaries)}")

# Test 3: Set active simulation
st.header("Test 3: Set Active Simulation")
if summaries:
    set_active_simulation('test_sim_1')
    active = get_active_simulation()
    st.success("✓ Set active simulation")
    st.json({
        "active_id": st.session_state.get("active_simulation_id"),
        "protocol_name": active['protocol']['name'] if active else None
    })

# Test 4: FIFO Eviction
st.header("Test 4: FIFO Eviction")
initial_count = len(get_simulation_registry())
for i in range(5):
    add_simulation_to_registry(f'evict_test_{i}', {'protocol': {'name': f'Evict {i}'}})

final_count = len(get_simulation_registry())
st.write(f"Initial count: {initial_count}, Final count: {final_count}")
if final_count == 5:
    st.success("✓ FIFO eviction working correctly")
else:
    st.error(f"✗ Expected 5 simulations, got {final_count}")

# Test 5: Protocol spec handling
st.header("Test 5: Protocol Spec Handling")
# Check v2 directory first, then fallback to old location
protocol_path = Path("protocols/v2/eylea.yaml")
if not protocol_path.exists():
    protocol_path = Path("protocols/eylea.yaml")
if protocol_path.exists():
    test_sim = {'protocol': {}}
    save_protocol_spec(test_sim, protocol_path)
    if 'yaml_content' in test_sim['protocol']:
        st.success("✓ Protocol spec saved correctly")
    else:
        st.error("✗ Protocol spec not saved")
else:
    st.warning("Protocol file not found - skipping test")

# Summary
st.header("Test Summary")
st.success("All manual tests can be verified above. Use the interactive test script for more detailed testing.")