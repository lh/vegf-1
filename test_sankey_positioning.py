#!/usr/bin/env python3
"""Test script to verify dynamic positioning in Sankey diagram."""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Create test data with different numbers of terminal states
def create_test_transitions(num_still_in_states=3):
    """Create test transition data with configurable number of terminal states."""
    
    # Base transitions
    transitions = []
    
    # Initial -> Intensive
    for i in range(100):
        transitions.append({
            'from_state': 'Initial Treatment',
            'to_state': 'Intensive Treatment',
            'patient_id': f'p{i}'
        })
    
    # Intensive -> Regular (80%)
    for i in range(80):
        transitions.append({
            'from_state': 'Intensive Treatment',
            'to_state': 'Regular Treatment',
            'patient_id': f'p{i}'
        })
    
    # Intensive -> No Further Visits (20%)
    for i in range(80, 100):
        transitions.append({
            'from_state': 'Intensive Treatment',
            'to_state': 'No Further Visits',
            'patient_id': f'p{i}'
        })
    
    # Regular -> Extended (50%)
    for i in range(40):
        transitions.append({
            'from_state': 'Regular Treatment',
            'to_state': 'Extended Treatment',
            'patient_id': f'p{i}'
        })
    
    # Regular -> Still in Regular (30%)
    for i in range(40, 70):
        transitions.append({
            'from_state': 'Regular Treatment',
            'to_state': 'Still in Regular Treatment',
            'patient_id': f'p{i}'
        })
    
    # Extended -> Maximum (if num_still_in_states > 1)
    if num_still_in_states > 1:
        for i in range(20):
            transitions.append({
                'from_state': 'Extended Treatment',
                'to_state': 'Maximum Treatment',
                'patient_id': f'p{i}'
            })
        
        # Extended -> Still in Extended
        for i in range(20, 40):
            transitions.append({
                'from_state': 'Extended Treatment',
                'to_state': 'Still in Extended Treatment',
                'patient_id': f'p{i}'
            })
    
    # Maximum -> Still in Maximum (if num_still_in_states > 2)
    if num_still_in_states > 2:
        for i in range(20):
            transitions.append({
                'from_state': 'Maximum Treatment',
                'to_state': 'Still in Maximum Treatment',
                'patient_id': f'p{i}'
            })
    
    return pd.DataFrame(transitions)

# Test the function
if __name__ == "__main__":
    print("Testing dynamic Sankey positioning...")
    
    # Import the comparison page module
    # Since we can't import from pages directly, let's copy the function here
    exec(open('pages/4_Simulation_Comparison.py').read(), globals())
    
    # Create test data with different numbers of terminal states
    test_cases = [
        ("1 terminal state each", 1),
        ("3 terminal states each", 3),
        ("5 terminal states in A, 2 in B", None)  # Custom case
    ]
    
    for test_name, num_states in test_cases:
        print(f"\nTest case: {test_name}")
        
        if num_states is None:
            # Custom case
            df_a = create_test_transitions(5)
            df_b = create_test_transitions(2)
        else:
            df_a = create_test_transitions(num_states)
            df_b = create_test_transitions(num_states)
        
        # Count unique terminal states
        terminal_a = [s for s in df_a['to_state'].unique() if 'Still in' in s]
        terminal_b = [s for s in df_b['to_state'].unique() if 'Still in' in s]
        
        print(f"  Stream A terminal states: {len(terminal_a)} - {terminal_a}")
        print(f"  Stream B terminal states: {len(terminal_b)} - {terminal_b}")
        
        # Create the diagram
        try:
            fig = create_dual_stream_sankey(df_a, df_b, "Test A", "Test B")
            
            # Save to file
            output_file = f"test_sankey_{test_name.replace(' ', '_')}.html"
            fig.write_html(output_file)
            print(f"  ✓ Successfully created diagram: {output_file}")
            
            # Extract Y positions for terminal states
            node_data = fig.data[0].node
            print(f"  Node count: {len(node_data.x)}")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    print("\nTest complete!")