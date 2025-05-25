"""
Puppeteer Helpers for Streamlit

This module provides helper functions to make Streamlit apps more accessible
to Puppeteer automation. It adds special data attributes and helper functions
that make it easier to interact with Streamlit components through Puppeteer.

Usage:
    import streamlit as st
    from streamlit_app.puppeteer_helpers import add_puppeteer_support, make_selectable

    # Add basic Puppeteer support to the app
    add_puppeteer_support()

    # Make a button easily selectable by Puppeteer
    button = make_selectable(st.button, "Run Simulation", test_id="run-simulation-btn")
"""

import streamlit as st
import uuid
import functools
import json


def add_puppeteer_support():
    """
    Add basic Puppeteer support to a Streamlit app.

    This function should be called AFTER st.set_page_config() in your Streamlit app
    to add various helpers for Puppeteer automation.
    """
    try:
        # Check if we've already added support to avoid duplication
        if 'puppeteer_support_enabled' in st.session_state:
            return

        # Add debug console methods (minimal JS to avoid issues)
        st.markdown("""
        <script>
        window.puppeteerReady = true;
        console.log('Puppeteer helpers initialized');

        // Provide helper functions for puppeteer
        window.puppeteerHelpers = {
            getElementByTestId: function(testId) {
                return document.querySelector(`[data-test-id="${testId}"]`);
            },
            getAllElements: function() {
                return Array.from(document.querySelectorAll('[data-test-id]'))
                    .map(el => ({
                        testId: el.getAttribute('data-test-id'),
                        text: el.textContent,
                        visible: el.offsetParent !== null
                    }));
            },
            clickElement: function(testId) {
                const el = this.getElementByTestId(testId);
                if (el) {
                    el.click();
                    return true;
                }
                return false;
            }
        };
        </script>
        """, unsafe_allow_html=True)

        # Store in session state that puppeteer support is enabled
        st.session_state['puppeteer_support_enabled'] = True
    except Exception as e:
        # Silently handle errors
        pass


def wrap_element(content, test_id, element_type="div"):
    """Wrap content in an element with a test ID."""
    return f"""
    <{element_type} class="puppeteer-selectable" data-test-id="{test_id}">
        {content}
    </{element_type}>
    """


def make_selectable(streamlit_func, *args, test_id=None, element_type="div", **kwargs):
    """
    Make a Streamlit component easily selectable by Puppeteer.
    
    Parameters
    ----------
    streamlit_func : callable
        The Streamlit function to wrap (e.g., st.button, st.slider)
    *args
        Arguments to pass to the Streamlit function
    test_id : str, optional
        A unique test ID for Puppeteer selection. If not provided, 
        a test ID will be generated based on the args.
    element_type : str, optional
        HTML element type to use for wrapping. Default is "div".
    **kwargs
        Keyword arguments to pass to the Streamlit function
        
    Returns
    -------
    Any
        The return value from the Streamlit function
    """
    # Generate a test ID if none is provided
    if test_id is None:
        if args and isinstance(args[0], str):
            # Use the first string argument to generate a test ID
            test_id = args[0].lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
        else:
            test_id = f"element-{str(uuid.uuid4())[:8]}"
    
    # Store in session state
    if 'puppeteer_test_ids' not in st.session_state:
        st.session_state.puppeteer_test_ids = {}
    
    st.session_state.puppeteer_test_ids[test_id] = {
        "func": streamlit_func.__name__ if hasattr(streamlit_func, "__name__") else str(streamlit_func),
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in kwargs.items()}
    }
    
    # Add the container with a data-test-id attribute
    st.markdown(f'<div class="puppeteer-selectable" data-test-id="{test_id}"></div>', 
                unsafe_allow_html=True)
    
    # Call the original function
    return streamlit_func(*args, **kwargs)


def selectable_button(label, test_id=None, **kwargs):
    """Create a button that's easy to select with Puppeteer."""
    if test_id is None:
        test_id = f"button-{label.lower().replace(' ', '-')}"
    
    # Set a key if not provided to make the button uniquely identifiable
    if 'key' not in kwargs:
        kwargs['key'] = f"key-{test_id}"
        
    return make_selectable(st.button, label, test_id=test_id, **kwargs)


def selectable_radio(label, options, test_id=None, **kwargs):
    """Create a radio button group that's easy to select with Puppeteer."""
    if test_id is None:
        test_id = f"radio-{label.lower().replace(' ', '-')}"
        
    # Set a key if not provided
    if 'key' not in kwargs:
        kwargs['key'] = f"key-{test_id}"
        
    return make_selectable(st.radio, label, options, test_id=test_id, **kwargs)


def selectable_selectbox(label, options, test_id=None, **kwargs):
    """Create a selectbox that's easy to select with Puppeteer."""
    if test_id is None:
        test_id = f"select-{label.lower().replace(' ', '-')}"
        
    # Set a key if not provided
    if 'key' not in kwargs:
        kwargs['key'] = f"key-{test_id}"
        
    return make_selectable(st.selectbox, label, options, test_id=test_id, **kwargs)


def get_testable_elements():
    """Get a list of all testable elements for debugging."""
    if 'puppeteer_test_ids' not in st.session_state:
        return []
    
    return st.session_state.puppeteer_test_ids


def debug_puppeteer_helpers():
    """Display debug information about Puppeteer helpers."""
    st.write("## Puppeteer Debug Information")
    
    if 'puppeteer_support_enabled' not in st.session_state:
        st.error("Puppeteer support is not enabled. Call add_puppeteer_support() first.")
        return
    
    st.success("Puppeteer support is enabled")
    
    st.write("### Testable Elements")
    st.json(get_testable_elements())
    
    st.write("### How to use with Puppeteer")
    st.code("""
// Example Puppeteer code to interact with this app:
await page.evaluate(() => {
    return window.puppeteerHelpers.getAllElements();
});

// To click an element:
await page.evaluate(() => {
    return window.puppeteerHelpers.clickElement('button-run-simulation');
});
    """)