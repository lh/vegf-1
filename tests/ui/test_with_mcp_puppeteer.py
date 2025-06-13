"""
Example of using MCP Puppeteer server for Streamlit testing.

This shows how to use the MCP tools directly for UI testing.
"""

import time


def test_streamlit_with_mcp():
    """Example test using MCP Puppeteer tools."""
    
    # Note: This is a template for when running in an environment
    # with MCP tools available
    
    print("MCP Puppeteer Test Example")
    print("==========================")
    print()
    print("To run this test:")
    print("1. Start your Streamlit app: streamlit run APE.py")
    print("2. In Claude, use the MCP tools:")
    print()
    print("Example MCP commands:")
    print("- mcp__puppeteer__puppeteer_navigate('http://localhost:8501')")
    print("- mcp__puppeteer__puppeteer_screenshot('homepage')")
    print("- mcp__puppeteer__puppeteer_click('button')")
    print("- mcp__puppeteer__puppeteer_fill('input[name=patients]', '1000')")
    print()
    print("Example test flow:")
    print("""
# Navigate to app
mcp__puppeteer__puppeteer_navigate(url='http://localhost:8501')

# Take screenshot of homepage
mcp__puppeteer__puppeteer_screenshot(name='homepage')

# Click Protocol Manager
mcp__puppeteer__puppeteer_click(selector='button:has-text("Protocol Manager")')

# Take screenshot of Protocol Manager
mcp__puppeteer__puppeteer_screenshot(name='protocol_manager')

# Select a protocol (if available)
mcp__puppeteer__puppeteer_click(selector='div[data-testid="stSelectbox"]')
mcp__puppeteer__puppeteer_click(selector='li[role="option"]:first-child')

# Navigate to simulation
mcp__puppeteer__puppeteer_click(selector='button:has-text("Next: Simulation")')

# Fill in simulation parameters
mcp__puppeteer__puppeteer_fill(selector='input[aria-label="Number of Patients"]', value='1000')

# Run simulation
mcp__puppeteer__puppeteer_click(selector='button:has-text("Run Simulation")')

# Wait and take screenshot of results
time.sleep(5)
mcp__puppeteer__puppeteer_screenshot(name='simulation_results')
""")


def test_memory_monitoring_ui():
    """Test memory monitoring UI elements."""
    
    print("Memory Monitoring UI Test")
    print("=========================")
    print()
    print("MCP commands to test memory UI:")
    print("""
# Check for memory indicator in sidebar
mcp__puppeteer__puppeteer_evaluate(
    script='document.querySelector(".memory-indicator") !== null'
)

# Check memory warning appears for large simulation
mcp__puppeteer__puppeteer_fill(selector='input[aria-label="Number of Patients"]', value='10000')

# Should see warning
mcp__puppeteer__puppeteer_evaluate(
    script='Array.from(document.querySelectorAll("*")).some(el => el.textContent.includes("memory"))'
)
""")


if __name__ == "__main__":
    test_streamlit_with_mcp()
    print()
    test_memory_monitoring_ui()