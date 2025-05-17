# Puppeteer Automation for AMD Protocol Explorer

This document describes the complete Puppeteer integration for the AMD Protocol Explorer Streamlit app, designed to enable both automated testing and AI assistant interaction.

## Files

The Puppeteer integration consists of the following files:

1. `puppeteer_helpers.py` - Helper functions for adding Puppeteer support to Streamlit
2. `test_puppeteer_integration.js` - Test script that demonstrates Puppeteer integration
3. `puppeteer_integration_guide.md` - Comprehensive guide for integrating Puppeteer
4. `claude_puppeteer_test.js` - Example script for Claude AI assistant
5. `puppeteer_example.py` - Example Streamlit app with Puppeteer integration
6. `add_puppeteer_markers.py` - Script to add missing Puppeteer markers to the app

## Setup

### Install Dependencies

```bash
# Install Puppeteer
npm install puppeteer

# Install Streamlit (if not already installed)
pip install streamlit
```

### Run the Streamlit App

```bash
# Start the Streamlit app on port 8502
cd /Users/rose/Code/CC
streamlit run streamlit_app/app.py --server.port 8502
```

### Run the Test Script

```bash
# Run the Puppeteer test script
cd /Users/rose/Code/CC/streamlit_app
node test_puppeteer_integration.js
```

## Marker System

The app uses a marker-based system for component identification:

1. **Marker Elements**: HTML div elements with `data-test-id` attributes placed before hard-to-select components
2. **Component Keys**: Unique keys for all Streamlit components
3. **Helper Functions**: JavaScript functions for finding and interacting with marked elements

### Marker Naming Convention

All markers follow a consistent naming pattern:

- `component-type-marker` - For marker elements (e.g., `main-navigation-marker`)
- `component-type-btn` - For buttons (e.g., `run-simulation-btn-marker`)
- `component-type-N-marker` - For indexed items (e.g., `patient-expander-0-marker`)

## Implementation Details

### Puppeteer Helpers

The `puppeteer_helpers.py` module provides:

1. `add_puppeteer_support()` - Adds JavaScript helpers to the page
2. `selectable_button()`, `selectable_radio()`, `selectable_selectbox()` - Wrapper functions for Streamlit components
3. `wrap_element()` - Wraps content in an element with a test ID
4. `debug_puppeteer_helpers()` - Shows debug information

### Marker System

The marker system uses HTML elements with `data-test-id` attributes to make components easy to find:

```python
# Add a marker for the navigation
st.sidebar.markdown('<div data-test-id="main-navigation-marker"></div>', unsafe_allow_html=True)

# Add a marker for a button
st.markdown('<div data-test-id="run-simulation-btn-marker"></div>', unsafe_allow_html=True)
```

### JavaScript Helpers

The app injects JavaScript helpers for Puppeteer interaction:

```javascript
// Get element by test ID
window.puppeteerHelpers.getElementByTestId('test-id');

// Get all elements with test IDs
window.puppeteerHelpers.getAllElements();

// Click an element by test ID
window.puppeteerHelpers.clickElement('test-id');
```

## AI Assistant Integration

The integration is specifically designed to work well with AI assistants like Claude:

1. **Descriptive Markers**: Markers use clear, descriptive names
2. **Fallback Selectors**: Multiple selector approaches for resilience
3. **Console Helpers**: JavaScript functions for debugging
4. **Error Handling**: Graceful failure and error reporting

## Best Practices

1. **Always Add Markers Before Components**:
   ```python
   st.markdown('<div data-test-id="my-component-marker"></div>', unsafe_allow_html=True)
   my_component = st.button("Click Me")
   ```

2. **Use Unique Keys for All Components**:
   ```python
   st.button("Submit", key="unique_submit_button")
   ```

3. **Add Test IDs for Everything That Needs Interaction**:
   - Navigation elements
   - Buttons
   - Dropdown selectors
   - Expanders
   - Form elements

4. **Handle Timing Issues**:
   - Add wait time between interactions
   - Use appropriate timeouts
   - Check for element visibility

5. **Take Screenshots to Debug**:
   ```javascript
   await page.screenshot({ path: 'debug.png' });
   ```

## Troubleshooting

### Common Issues

1. **Element Not Found**
   - Check if the marker is added before the component
   - Try using standard Streamlit selectors as fallback
   - Increase wait time for dynamic content

2. **Click Not Working**
   - Check if the element is visible (not hidden by CSS)
   - Try clicking the parent or child element
   - Use JavaScript click via `page.evaluate()`

3. **Streamlit-Specific Issues**
   - Expandable sections must be clicked on their summary element
   - Dropdown options may need time to appear before clicking
   - Form submission may reload the page, requiring re-navigation

## Examples

### Basic Navigation

```javascript
// Navigate to the app
await page.goto('http://localhost:8502');

// Wait for page to load
await page.waitForTimeout(2000);

// Click on Run Simulation in navigation
await page.click('[data-testid="stRadio"] label:nth-child(2)');
```

### Running a Simulation

```javascript
// Click the Run Simulation button
await page.waitForSelector('[data-test-id="run-simulation-btn-marker"]');
await page.click('.stButton button[kind="primary"]');

// Wait for simulation to complete
await page.waitForSelector('.stSuccess', { timeout: 60000 });
```

### Working with Expandable Sections

```javascript
// Find all expandable sections
const expanders = await page.$$('details');

// Click the first expander
if (expanders.length > 0) {
  await expanders[0].click();
}
```

## Further Enhancements

Future enhancements to the Puppeteer integration could include:

1. **End-to-End Test Suite**: Create a comprehensive test suite covering all app functionality
2. **Performance Testing**: Add performance metrics collection
3. **Visual Regression Testing**: Compare screenshots to detect UI changes
4. **Accessibility Testing**: Add accessibility audit helpers
5. **Custom Commands**: Create higher-level commands for common interactions

## Contact

For questions or issues with the Puppeteer integration, contact:

[Your Contact Information]