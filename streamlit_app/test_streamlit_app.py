"""
test_streamlit_app.py - Simple Streamlit app for testing Playwright
Run with: streamlit run test_streamlit_app.py --server.port 8503
"""

import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Test Streamlit App", page_icon="🧪")

st.title("🧪 Test Streamlit App for Playwright")
st.markdown("This is a test app running on a different port to avoid interfering with your main app.")

# Sidebar
with st.sidebar:
    st.header("Test Controls")
    test_type = st.selectbox("Select Test Type", ["Basic", "Interactive", "Data", "Charts"])
    
    if st.button("Run Test"):
        st.success("Test button clicked!")

# Main content based on selection
if test_type == "Basic":
    st.header("Basic Elements")
    st.text("This is plain text")
    st.markdown("This is **markdown** text")
    st.code("print('Hello from code block')")
    
elif test_type == "Interactive":
    st.header("Interactive Elements")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Enter your name")
        if name:
            st.write(f"Hello, {name}!")
    
    with col2:
        number = st.number_input("Pick a number", 0, 100)
        st.write(f"You picked: {number}")
    
    if st.button("Click me!"):
        st.balloons()
        st.success("Button was clicked!")
        
elif test_type == "Data":
    st.header("Data Display")
    
    # Create sample dataframe
    df = pd.DataFrame({
        'Column A': np.random.randn(10),
        'Column B': np.random.randn(10),
        'Column C': np.random.choice(['X', 'Y', 'Z'], 10)
    })
    
    st.dataframe(df)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Metric 1", "70 °F", "1.2 °F")
    col2.metric("Metric 2", "100", "-5")
    col3.metric("Metric 3", "50%", "10%")
    
elif test_type == "Charts":
    st.header("Charts")
    
    # Line chart
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['a', 'b', 'c']
    )
    st.line_chart(chart_data)
    
    # Bar chart
    st.bar_chart(chart_data)

# Footer
st.markdown("---")
st.caption(f"Test app running on port specified at launch · Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}")