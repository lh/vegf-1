# Puppeteer Integration Guide for AMD Protocol Explorer

This comprehensive guide shows how to integrate Puppeteer with the AMD Protocol Explorer Streamlit app for testing, automation, and AI assistant interaction.

## Overview

The AMD Protocol Explorer has been enhanced to support Puppeteer integration through:

1. HTML marker elements with `data-test-id` attributes
2. JavaScript helper functions for element detection
3. Robust fallback mechanisms for component selection
4. Resilient selectors that work with Streamlit's dynamic content

## Quick Start

### Running the Test Script

1. Ensure the Streamlit app is running:
   ```bash
   cd /Users/rose/Code/CC
   streamlit run streamlit_app/app.py
   ```

2. Install Puppeteer if needed:
   ```bash
   npm install puppeteer
   ```

3. Run the test script:
   ```bash
   cd /Users/rose/Code/CC/streamlit_app
   node test_puppeteer_integration.js
   ```

The test script will:
- Navigate through all major sections of the app
- Take screenshots of each page
- Run a sample simulation
- Test interaction with patient data

## Puppeteer Helper Functions

The app provides several JavaScript helper functions accessible from the browser console:

```javascript
// Get element by test ID
window.puppeteerHelpers.getElementByTestId('test-id');

// Get all elements with test IDs
window.puppeteerHelpers.getAllElements();

// Click an element by test ID
window.puppeteerHelpers.clickElement('test-id');
```

## Key Markers and Selectors

The following elements have dedicated markers to make them easier to find:

| Component | Marker/Selector | Description |
|-----------|-----------------|-------------|
| Main Navigation | `[data-test-id="main-navigation-marker"]` | Navigation radio buttons |
| Simulation Type | `[data-test-id="simulation-type-select-marker"]` | Simulation type dropdown |
| Run Simulation Button | `[data-test-id="run-simulation-btn-marker"]` | Primary button to start simulation |
| Advanced Options | `[data-test-id="advanced-options-marker"]` | Expandable advanced options section |
| Error Details | `[data-test-id="error-details-marker"]` | Error details expander if simulation fails |

## AI Assistant Integration

For AI assistants like Claude, the enhanced app provides:

1. Marker elements to identify key UI components
2. Consistent attribute naming for reliable selection
3. Fallback selectors when markers aren't found
4. Browser console helpers for debugging

Example Puppeteer code for Claude:

```javascript
// Navigate to the app
await puppeteer.navigate('http://localhost:8502');

// Wait for page to load
await new Promise(resolve => setTimeout(resolve, 2000));

// Navigate to Run Simulation page
await puppeteer.click('[data-testid="stRadio"] label:nth-child(2)');

// Wait for page to load
await new Promise(resolve => setTimeout(resolve, 1000));

// Click Run Simulation button
await puppeteer.click('.stButton button[kind="primary"]');

// Wait for simulation to complete
await new Promise(resolve => setTimeout(resolve, 5000));

// Take a screenshot of the results
await puppeteer.screenshot({
  name: 'simulation_results',
  width: 1920,
  height: 2000
});
```

## Troubleshooting

### Common Issues

1. **Selectors Not Working**
   - Streamlit's component hierarchy can change between versions
   - Solution: Use multiple selector approaches with fallbacks

2. **Timing Issues**
   - Streamlit components may take time to load and render
   - Solution: Use adequate timeouts and `sleep()` functions between interactions

3. **Component Changes**
   - Streamlit components don't support direct `id` attributes
   - Solution: Use marker elements and more stable CSS selectors

4. **Non-Interactive Elements**
   - Some Streamlit components use custom rendering that may not respond to direct clicks
   - Solution: Use wrapper elements and look for buttons that contain the text you need

5. **Expanded Elements Not Visible**
   - Streamlit's `st.expander()` creates collapsed content by default
   - Solution: Target the expander's summary element to click it open

### Debugging Tips

1. Take frequent screenshots to see the state of the UI
2. Use browser console to explore available test IDs:
   ```javascript
   Array.from(document.querySelectorAll('[data-test-id]'))
     .map(el => el.getAttribute('data-test-id'))
   ```
3. Check Streamlit's component hierarchy using browser inspector
4. Add more wait time between actions when components are slow to render

## Adding New Test IDs

When enhancing the app with new components:

1. Add marker elements before components that don't support ID attributes:
   ```python
   st.markdown('<div data-test-id="my-component-marker"></div>', unsafe_allow_html=True)
   ```

2. Add unique keys to all Streamlit components:
   ```python
   st.button("Run", key="unique_button_key")
   ```

3. Keep selector names consistent across the app:
   - Use suffixes like `-marker`, `-btn`, `-select` consistently
   - Use kebab-case for all test IDs

## Running with Claude

When using Claude Anthropic's AI assistant:

1. Make sure the app is running on port 8502
2. Claude can use the browser tools to interact with the app
3. Claude can take screenshots to verify the app state
4. Share screenshots with Claude to help it understand the UI

Use this template for Claude instructions:

```
Please help me test the AMD Protocol Explorer app running on http://localhost:8502.

I want you to:
1. Navigate to the app
2. Go to the "Run Simulation" page
3. Set the population size to 500
4. Run a simulation
5. Take screenshots along the way

Use the Puppeteer tools to interact with the app.
```

This approach lets Claude effectively navigate and interact with the enhanced Streamlit app using the accessibility improvements we've added.