# Puppeteer Integration Guide for AMD Protocol Explorer

This guide shows how to integrate the Puppeteer helpers with the AMD Protocol Explorer Streamlit app.

## Overview

The `puppeteer_helpers.py` module provides:

1. Data attributes for easy element selection
2. JavaScript helpers for Puppeteer interaction
3. Wrapper functions for Streamlit components
4. Debug utilities for testing

## Basic Integration

To add Puppeteer support to the AMD Protocol Explorer, follow these steps:

### 1. Add basic support at the beginning of app.py

```python
import streamlit as st
from puppeteer_helpers import add_puppeteer_support

# Add basic puppeteer support
add_puppeteer_support()

# Rest of your existing app code
...
```

### 2. Replace key interactive components

Update important interactive components to be selectable by Puppeteer:

```python
from puppeteer_helpers import selectable_button, selectable_radio, selectable_selectbox

# Replace your existing navigation radio
page = selectable_radio(
    "Navigate to",
    ["Dashboard", "Run Simulation", "Patient Explorer", "Reports", "About"],
    key="navigation",
    test_id="main-navigation"
)

# Replace run simulation button
if selectable_button("Run Simulation", type="primary", key="run_simulation_button", test_id="run-simulation-btn"):
    # Existing simulation code...
    pass
```

### 3. Make panels selectable

To ensure expandable sections are selectable for testing, wrap them with special IDs:

```python
from puppeteer_helpers import wrap_element

# For expandable sections, add a marker div before the expander
st.markdown(wrap_element("", "advanced-options-marker"), unsafe_allow_html=True)
with st.expander("Advanced Options"):
    # Expander content...
    pass
```

## Claude Puppeteer Code Example

Here's how to interact with the enhanced app using Claude's Puppeteer tools:

```javascript
// Navigate to the app
await page.goto('http://localhost:8502');

// Wait for Puppeteer support to initialize
await page.waitForFunction('window.puppeteerReady === true');

// Get all testable elements 
const elements = await page.evaluate(() => {
  return window.puppeteerHelpers.getAllElements();
});

// Click on the Run Simulation navigation item
await page.evaluate(() => {
  return window.puppeteerHelpers.clickElement('main-navigation');
});

// Click the Run Simulation button
await page.evaluate(() => {
  return window.puppeteerHelpers.clickElement('run-simulation-btn');
});

// Take a screenshot of the results
await page.screenshot({ path: 'simulation-results.png' });
```

## Implementation Example for app.py

Here's how to modify the beginning of your `app.py` file:

```python
"""
APE: AMD Protocol Explorer

This application provides an interactive dashboard for exploring and visualizing
AMD treatment protocols using Discrete Event Simulation (DES) and Agent-Based Simulation (ABS),
including detailed modeling of treatment discontinuation patterns.
"""

import os
import sys
import json
import subprocess
import platform
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path

# Import Puppeteer helpers
from puppeteer_helpers import add_puppeteer_support, selectable_radio, selectable_button

# Add basic puppeteer support
add_puppeteer_support()

# Rest of your imports and initialization code...

# Navigation with Puppeteer support
page = selectable_radio(
    "Navigate to",
    ["Dashboard", "Run Simulation", "Patient Explorer", "Reports", "About"],
    key="navigation",
    test_id="main-navigation"
)
```

## Testing the Integration

1. Run your Streamlit app with the changes
2. Open the browser console to confirm "Puppeteer helpers initialized" message
3. Try using the Claude Puppeteer tools with the data-test-id attributes
4. Use `.css-[hash]` selectors as a fallback when needed