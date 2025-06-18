#!/usr/bin/env python3
"""Debug test for Sankey positioning."""

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

# Extract and modify the create_dual_stream_sankey function with debug output
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

# Add debug prints
func_code = func_code.replace(
    '# Collect terminal states for each stream to calculate dynamic positioning',
    '''# Collect terminal states for each stream to calculate dynamic positioning
    print(f"\\nDEBUG: Processing states...")
    print(f"  States A: {sorted([s for s in states_a if 'Still in' in s or 'No Further' in s])}")
    print(f"  States B: {sorted([s for s in states_b if 'Still in' in s or 'No Further' in s])}")'''
)

func_code = func_code.replace(
    'still_in_y_positions_a[state] = y_start_a + i * y_step_a',
    '''still_in_y_positions_a[state] = y_start_a + i * y_step_a
                print(f"    A: {state} -> y={y_start_a + i * y_step_a:.3f}")'''
)

func_code = func_code.replace(
    'still_in_y_positions_b[state] = y_start_b + i * y_step_b',
    '''still_in_y_positions_b[state] = y_start_b + i * y_step_b
                print(f"    B: {state} -> y={y_start_b + i * y_step_b:.3f}")'''
)

func_code = func_code.replace(
    '# Use dynamically calculated position\n                y = still_in_y_positions_a.get(state, 0.77)',
    '''# Use dynamically calculated position
                y = still_in_y_positions_a.get(state, 0.77)
                if 'Still in' in base_state:
                    print(f"  Using position for {state}: {y:.3f}")'''
)

# Execute the function definition
exec(func_code)

# Create simple test data
df_a = pd.DataFrame([
    {'from_state': 'Initial Treatment', 'to_state': 'Regular Treatment'},
    {'from_state': 'Regular Treatment', 'to_state': 'Still in Regular Treatment'},
    {'from_state': 'Regular Treatment', 'to_state': 'Extended Treatment'},
    {'from_state': 'Extended Treatment', 'to_state': 'Still in Extended Treatment'},
    {'from_state': 'Extended Treatment', 'to_state': 'Maximum Treatment'},
    {'from_state': 'Maximum Treatment', 'to_state': 'Still in Maximum Treatment'},
    {'from_state': 'Initial Treatment', 'to_state': 'No Further Visits'},
])

df_b = pd.DataFrame([
    {'from_state': 'Initial Treatment', 'to_state': 'Regular Treatment'},
    {'from_state': 'Regular Treatment', 'to_state': 'Still in Regular Treatment'},
    {'from_state': 'Initial Treatment', 'to_state': 'No Further Visits'},
])

print("Creating Sankey diagram with debug output...")
fig = create_dual_stream_sankey(df_a, df_b, "Test A", "Test B")

# Save the result
import os
os.makedirs('output/debug', exist_ok=True)
fig.write_html('output/debug/sankey_debug_test.html')
print("\nSaved to output/debug/sankey_debug_test.html")