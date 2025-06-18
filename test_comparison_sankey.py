#!/usr/bin/env python3
"""Test Sankey positioning in the comparison page context."""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Test Sankey Positioning", layout="wide")

st.title("Test Dynamic Sankey Positioning")

# Import the function from the comparison page
exec(open('pages/4_Simulation_Comparison.py').read(), globals())

# Create test transition data with varying numbers of terminal states
def create_test_transitions(num_terminal_states, seed=42):
    """Create realistic test transition data."""
    np.random.seed(seed)
    transitions = []
    
    # Start with 100 patients in Initial Treatment
    patient_ids = [f'p{i}' for i in range(100)]
    current_states = {pid: 'Initial Treatment' for pid in patient_ids}
    
    # Transition some to Intensive
    for pid in patient_ids[:80]:
        transitions.append({
            'from_state': current_states[pid],
            'to_state': 'Intensive Treatment',
            'patient_id': pid
        })
        current_states[pid] = 'Intensive Treatment'
    
    # Some discontinue early
    for pid in patient_ids[80:100]:
        transitions.append({
            'from_state': current_states[pid],
            'to_state': 'No Further Visits',
            'patient_id': pid
        })
        current_states[pid] = 'No Further Visits'
    
    # From Intensive, some go to Regular
    intensive_patients = [pid for pid, state in current_states.items() if state == 'Intensive Treatment']
    for pid in intensive_patients[:60]:
        transitions.append({
            'from_state': current_states[pid],
            'to_state': 'Regular Treatment',
            'patient_id': pid
        })
        current_states[pid] = 'Regular Treatment'
    
    # Create terminal states based on num_terminal_states
    if num_terminal_states >= 1:
        # Some stay in Intensive
        for pid in intensive_patients[60:70]:
            transitions.append({
                'from_state': current_states[pid],
                'to_state': 'Still in Intensive Treatment',
                'patient_id': pid
            })
            current_states[pid] = 'Still in Intensive Treatment'
    
    if num_terminal_states >= 2:
        # Some Regular patients stay
        regular_patients = [pid for pid, state in current_states.items() if state == 'Regular Treatment']
        for pid in regular_patients[:20]:
            transitions.append({
                'from_state': current_states[pid],
                'to_state': 'Still in Regular Treatment',
                'patient_id': pid
            })
            current_states[pid] = 'Still in Regular Treatment'
        
        # Others go to Extended
        for pid in regular_patients[20:40]:
            transitions.append({
                'from_state': current_states[pid],
                'to_state': 'Extended Treatment',
                'patient_id': pid
            })
            current_states[pid] = 'Extended Treatment'
    
    if num_terminal_states >= 3:
        # Some stay in Extended
        extended_patients = [pid for pid, state in current_states.items() if state == 'Extended Treatment']
        for pid in extended_patients[:10]:
            transitions.append({
                'from_state': current_states[pid],
                'to_state': 'Still in Extended Treatment',
                'patient_id': pid
            })
            current_states[pid] = 'Still in Extended Treatment'
    
    if num_terminal_states >= 4:
        # Some go to Maximum
        extended_remaining = [pid for pid, state in current_states.items() 
                            if state == 'Extended Treatment' and pid not in transitions[-10:]]
        for pid in extended_remaining[:5]:
            transitions.append({
                'from_state': current_states[pid],
                'to_state': 'Maximum Treatment',
                'patient_id': pid
            })
            current_states[pid] = 'Maximum Treatment'
    
    if num_terminal_states >= 5:
        # Some stay in Maximum
        max_patients = [pid for pid, state in current_states.items() if state == 'Maximum Treatment']
        for pid in max_patients:
            transitions.append({
                'from_state': current_states[pid],
                'to_state': 'Still in Maximum Treatment',
                'patient_id': pid
            })
            current_states[pid] = 'Still in Maximum Treatment'
    
    return pd.DataFrame(transitions)

# Test configuration
col1, col2 = st.columns(2)

with col1:
    num_terminal_a = st.slider("Number of terminal states for A", 1, 5, 3)
    
with col2:
    num_terminal_b = st.slider("Number of terminal states for B", 1, 5, 2)

# Create test data
df_a = create_test_transitions(num_terminal_a, seed=42)
df_b = create_test_transitions(num_terminal_b, seed=123)

# Show terminal state counts
col1, col2 = st.columns(2)

with col1:
    terminal_a = sorted([s for s in df_a['to_state'].unique() if 'Still in' in s])
    st.info(f"Stream A has {len(terminal_a)} 'Still in' states:")
    for state in terminal_a:
        count = len(df_a[df_a['to_state'] == state])
        st.write(f"- {state}: {count} patients")

with col2:
    terminal_b = sorted([s for s in df_b['to_state'].unique() if 'Still in' in s])
    st.info(f"Stream B has {len(terminal_b)} 'Still in' states:")
    for state in terminal_b:
        count = len(df_b[df_b['to_state'] == state])
        st.write(f"- {state}: {count} patients")

# Create and display the dual-stream Sankey
st.subheader("Patient Journey Flow Comparison")

try:
    fig = create_dual_stream_sankey(df_a, df_b, f"Simulation A ({num_terminal_a} terminals)", f"Simulation B ({num_terminal_b} terminals)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Save to file for inspection
    output_file = f"output/debug/sankey_streamlit_test_A{num_terminal_a}_B{num_terminal_b}.html"
    import os
    os.makedirs('output/debug', exist_ok=True)
    fig.write_html(output_file)
    st.success(f"Diagram saved to: {output_file}")
    
except Exception as e:
    st.error(f"Error creating Sankey: {str(e)}")
    st.exception(e)

# Instructions
st.markdown("---")
st.markdown("""
### Dynamic Positioning Test

This test demonstrates the dynamic positioning of terminal states in the dual-stream Sankey diagram:

- **"No Further Visits"** nodes are fixed at y=0.60 (A) and y=0.10 (B)
- **"Still in"** states are dynamically distributed:
  - Stream A: Between y=0.65 and y=0.90
  - Stream B: Between y=0.15 and y=0.40
- States are sorted alphabetically for consistent ordering
- Spacing adjusts automatically based on the number of terminal states

Try different combinations to see how the positioning adapts!
""")