"""
Debug script to run directly from Streamlit to test retreatment visualization.
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

st.title("Retreatment Visualization Debug")
st.write("This script checks which implementation of the retreatment chart is being used.")

# Try to import from clean_nested_bar_chart
import_success = False
chart_source = "Unknown"

try:
    # Try to import from the clean nested bar chart implementation
    from visualization.clean_nested_bar_chart import create_discontinuation_retreatment_chart
    chart_source = "clean_nested_bar_chart"
    import_success = True
    st.success("Successfully imported from clean_nested_bar_chart")
except ImportError:
    st.error("Failed to import from clean_nested_bar_chart")
    try:
        # Fall back to the nested bar chart if clean version isn't available
        from visualization.nested_bar_chart import create_nested_discontinuation_chart as create_discontinuation_retreatment_chart
        chart_source = "nested_bar_chart"
        import_success = True
        st.success("Falling back to nested_bar_chart")
    except ImportError:
        st.error("Failed to import any chart implementation")

if import_success:
    # Create sample data for discontinuation and retreatment
    data = [
        {'reason': 'Premature', 'retreated': True, 'count': 455},
        {'reason': 'Premature', 'retreated': False, 'count': 93},
        {'reason': 'Planned', 'retreated': True, 'count': 60},
        {'reason': 'Planned', 'retreated': False, 'count': 89},
        {'reason': 'Not Renewed', 'retreated': True, 'count': 6},
        {'reason': 'Not Renewed', 'retreated': False, 'count': 119},
        {'reason': 'Administrative', 'retreated': True, 'count': 2},
        {'reason': 'Administrative', 'retreated': False, 'count': 10},
    ]

    df = pd.DataFrame(data)
    
    st.write(f"Using chart from: {chart_source}")
    
    # Display Python version and path
    st.write(f"Python version: {sys.version}")
    st.write(f"Python executable: {sys.executable}")
    st.write(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Display module details
    visualizations = []
    for name, module in sys.modules.items():
        if 'nested_bar_chart' in name or 'clean_nested_bar_chart' in name:
            mod_path = getattr(module, '__file__', 'Unknown')
            visualizations.append(f"{name}: {mod_path}")
    
    st.write("Visualization modules found:")
    for viz in visualizations:
        st.write(viz)
    
    # Create the chart
    fig, ax = create_discontinuation_retreatment_chart(
        data=df,
        title=f"Streamlit Test ({chart_source})",
        figsize=(10, 6),
        use_log_scale=True,
        sort_by_total=True,
        small_sample_threshold=15
    )
    
    # Display the figure in Streamlit
    st.pyplot(fig)
    
    # List visualization files
    st.write("Checking visualization directory:")
    import glob
    viz_files = glob.glob("visualization/*.py")
    for file in viz_files:
        st.write(file)
        
    # Last modified time for the visualization files
    st.write("File modification times:")
    for file in ['visualization/clean_nested_bar_chart.py', 'visualization/nested_bar_chart.py']:
        try:
            mtime = os.path.getmtime(file)
            st.write(f"{file}: {pd.to_datetime(mtime, unit='s')}")
        except FileNotFoundError:
            st.write(f"{file}: Not found")
else:
    st.error("Cannot run visualization test - imports failed")