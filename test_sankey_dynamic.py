#!/usr/bin/env python3
"""Test dynamic Sankey positioning by extracting and testing the function."""

import pandas as pd
import plotly.graph_objects as go

# Mock the color function
def get_treatment_state_colors():
    return {
        'Initial Treatment': '#3498db',
        'Intensive Treatment': '#e74c3c',
        'Regular Treatment': '#f39c12',
        'Extended Treatment': '#9b59b6',
        'Maximum Treatment': '#1abc9c'
    }

# Extract the create_dual_stream_sankey function from the file
with open('pages/4_Simulation_Comparison.py', 'r') as f:
    content = f.read()
    
# Find the function definition
start = content.find('def create_dual_stream_sankey(')
end = content.find('\n\n# First, load both datasets', start)
func_code = content[start:end]

# Replace the import statement
func_code = func_code.replace(
    'from ape.components.treatment_patterns.pattern_analyzer import get_treatment_state_colors',
    '# Using local mock function'
)

# Execute the function definition
exec(func_code)

# Create test data
def create_test_data(num_terminal_states):
    """Create test transition data."""
    transitions = []
    
    # Base flow
    transitions.extend([
        {'from_state': 'Initial Treatment', 'to_state': 'Intensive Treatment'} for _ in range(100)
    ])
    
    # Some go to No Further Visits
    transitions.extend([
        {'from_state': 'Intensive Treatment', 'to_state': 'No Further Visits'} for _ in range(20)
    ])
    
    # Others continue
    transitions.extend([
        {'from_state': 'Intensive Treatment', 'to_state': 'Regular Treatment'} for _ in range(80)
    ])
    
    # Create different terminal states based on num_terminal_states
    if num_terminal_states >= 1:
        transitions.extend([
            {'from_state': 'Regular Treatment', 'to_state': 'Still in Regular Treatment'} for _ in range(30)
        ])
    
    if num_terminal_states >= 2:
        transitions.extend([
            {'from_state': 'Regular Treatment', 'to_state': 'Extended Treatment'} for _ in range(50)
        ])
        transitions.extend([
            {'from_state': 'Extended Treatment', 'to_state': 'Still in Extended Treatment'} for _ in range(25)
        ])
    
    if num_terminal_states >= 3:
        transitions.extend([
            {'from_state': 'Extended Treatment', 'to_state': 'Maximum Treatment'} for _ in range(25)
        ])
        transitions.extend([
            {'from_state': 'Maximum Treatment', 'to_state': 'Still in Maximum Treatment'} for _ in range(25)
        ])
    
    if num_terminal_states >= 4:
        transitions.extend([
            {'from_state': 'Initial Treatment', 'to_state': 'Still in Initial Treatment'} for _ in range(5)
        ])
    
    if num_terminal_states >= 5:
        transitions.extend([
            {'from_state': 'Intensive Treatment', 'to_state': 'Still in Intensive Treatment'} for _ in range(10)
        ])
    
    return pd.DataFrame(transitions)

# Test cases
print("Testing dynamic Sankey positioning...")

test_cases = [
    ("Single terminal", 1, 1),
    ("Multiple terminals", 3, 3),
    ("Asymmetric terminals", 5, 2),
    ("Many terminals", 5, 5)
]

for test_name, terminals_a, terminals_b in test_cases:
    print(f"\nTest: {test_name} (A: {terminals_a} terminals, B: {terminals_b} terminals)")
    
    # Create test data
    df_a = create_test_data(terminals_a)
    df_b = create_test_data(terminals_b)
    
    # Count actual terminal states
    terminal_states_a = [s for s in df_a['to_state'].unique() if 'Still in' in s]
    terminal_states_b = [s for s in df_b['to_state'].unique() if 'Still in' in s]
    
    print(f"  A stream 'Still in' states: {sorted(terminal_states_a)}")
    print(f"  B stream 'Still in' states: {sorted(terminal_states_b)}")
    
    try:
        # Create the diagram
        fig = create_dual_stream_sankey(df_a, df_b, f"Test A ({terminals_a})", f"Test B ({terminals_b})")
        
        # Save to file
        output_file = f"output/debug/sankey_test_{test_name.replace(' ', '_')}.html"
        import os
        os.makedirs('output/debug', exist_ok=True)
        fig.write_html(output_file)
        print(f"  ✓ Saved to: {output_file}")
        
        # Extract node positions to verify spacing
        node_data = fig.data[0].node
        y_positions = node_data.y
        
        # Find terminal node positions
        all_states = []
        for i, (x, y) in enumerate(zip(node_data.x, node_data.y)):
            if x == 0.95:  # Terminal nodes are at x=0.95
                all_states.append((i, y))
        
        print(f"  Terminal node Y positions: {[f'{y:.3f}' for _, y in sorted(all_states, key=lambda x: x[1])]}")
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

print("\nTest complete! Check output/debug/ for the generated HTML files.")