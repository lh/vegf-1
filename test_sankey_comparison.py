#!/usr/bin/env python3
"""Test script to verify Sankey diagram fixes in comparison page."""

import streamlit as st

st.set_page_config(page_title="Sankey Test Instructions", layout="wide")

st.title("Testing Sankey Diagram Fixes")

st.markdown("""
## Instructions for Testing

### 1. Check the Comparison Page
1. Run the Streamlit app: `streamlit run Home.py`
2. Navigate to **Simulation Comparison** page
3. Select two simulations to compare
4. Scroll down to **Patient Journey Flow** section
5. **Enable Debug Mode** checkbox

### 2. What to Look For

#### Data Fix Verification:
- In debug mode, you should see terminal states distribution
- States should include: `Intensive`, `Regular`, `Extended`, `Maximum Extension`, `Discontinued`
- NOT all patients should be in `Discontinued`

#### Display Fix Verification:
- Both Sankey diagrams should be fully visible
- Right diagram (Sankey B) should NOT be truncated
- Check that you can see all nodes and connections

### 3. Debug Information
When debug mode is enabled:
- Terminal states distribution will be shown
- Debug files will be saved to `debug/` directory
- You can download a zip file with all debug data

### 4. Compare with Analysis Page
1. Navigate to **Analysis** page
2. Select the same simulation
3. Go to **Patient Journey** tab
4. Compare the Sankey diagram with the one in Comparison page
5. They should show similar patient flow patterns

### 5. Feedback Needed
Please let me know:
1. Are patients still all showing as Discontinued?
2. Is Sankey B still truncated?
3. Do the terminal states look correct in debug mode?
4. Any error messages?

### Next Steps
Based on your feedback, I will:
- If data issue persists: investigate further data processing
- If display issue persists: try alternative layout approaches
- If both fixed: clean up debug code and finalize
""")

st.info("Please run the main app and follow the instructions above to test the fixes.")