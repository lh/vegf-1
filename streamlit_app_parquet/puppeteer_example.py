"""
Puppeteer Support Example for Streamlit

This example shows how to use the puppeteer_helpers module to make a Streamlit app
more accessible to Puppeteer automation.

Run this example with:
    streamlit run puppeteer_example.py
"""

import streamlit as st
from puppeteer_helpers import (
    add_puppeteer_support,
    selectable_button,
    selectable_radio,
    selectable_selectbox,
    debug_puppeteer_helpers
)

# Add basic Puppeteer support
add_puppeteer_support()

st.title("Puppeteer Support Example")
st.write("""
This example demonstrates how to make Streamlit components easily accessible
to Puppeteer automation. It adds special data attributes and helper functions
that make it easier to interact with Streamlit components.
""")

# Create sections
st.header("Basic Selectable Elements")
col1, col2 = st.columns(2)

with col1:
    # Create a button that's easy to select with Puppeteer
    if selectable_button("Click Me", test_id="example-button"):
        st.success("Button clicked!")
        
    # Create a radio group
    option = selectable_radio(
        "Select an option",
        ["Option 1", "Option 2", "Option 3"],
        test_id="example-radio"
    )
    st.write(f"You selected: {option}")

with col2:
    # Create a selectbox
    fruit = selectable_selectbox(
        "Select a fruit",
        ["Apple", "Banana", "Cherry", "Durian"],
        test_id="example-selectbox"
    )
    st.write(f"You selected: {fruit}")

# Create a form example
st.header("Form Example")
with st.form("puppeteer_test_form", clear_on_submit=False):
    st.write("This form can be easily automated with Puppeteer")
    
    # Form elements
    name = st.text_input("Name", key="name_input")
    age = st.number_input("Age", min_value=0, max_value=120, key="age_input")
    submit = st.form_submit_button("Submit Form", key="submit_button")
    
    # We can't directly use selectable_button in a form,
    # but we can add a marker div before the form
    st.markdown('<div data-test-id="form-submit-marker"></div>', unsafe_allow_html=True)
    
    if submit:
        st.success(f"Form submitted! Name: {name}, Age: {age}")

# Add a debug section that shows all testable elements
if st.checkbox("Show Debug Information", key="show_debug"):
    debug_puppeteer_helpers()

# Add Puppeteer code example
st.header("Puppeteer Code Example")
st.code("""
// Connect to the Streamlit app using Puppeteer
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8501');
  
  // Wait for the Puppeteer helpers to initialize
  await page.waitForFunction('window.puppeteerReady === true');
  
  // Get all testable elements
  const elements = await page.evaluate(() => {
    return window.puppeteerHelpers.getAllElements();
  });
  console.log('Available elements:', elements);
  
  // Click a button by its test ID
  await page.evaluate(() => {
    return window.puppeteerHelpers.clickElement('example-button');
  });
  
  // Wait for success message to appear
  await page.waitForSelector('.stSuccess');
  
  // Take a screenshot
  await page.screenshot({ path: 'streamlit-automation.png' });
  
  await browser.close();
})();
""")