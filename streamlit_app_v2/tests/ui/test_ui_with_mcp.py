"""
Direct UI testing using MCP Puppeteer tools.
Run this with the Streamlit app on port 8503.
"""

def test_homepage():
    """Test homepage elements."""
    print("Testing APE V2 Homepage...")
    
    # These would be run through MCP in Claude:
    tests = [
        "mcp__puppeteer__puppeteer_navigate(url='http://localhost:8503')",
        "mcp__puppeteer__puppeteer_screenshot(name='homepage')",
        
        # Check for title
        """mcp__puppeteer__puppeteer_evaluate(
            script='document.querySelector("h1").textContent'
        )""",
        
        # Check for navigation buttons
        """mcp__puppeteer__puppeteer_evaluate(
            script='Array.from(document.querySelectorAll("button")).filter(b => b.textContent.includes("Protocol Manager")).length'
        )""",
        
        # Click Protocol Manager
        """mcp__puppeteer__puppeteer_click(
            selector='button:has-text("Protocol Manager")'
        )""",
    ]
    
    return tests


def test_navigation():
    """Test navigation between pages."""
    tests = [
        # Start at home
        "mcp__puppeteer__puppeteer_navigate(url='http://localhost:8503')",
        
        # Click Protocol Manager
        """mcp__puppeteer__puppeteer_evaluate(
            script='document.querySelector("button").click(); // First button with Protocol Manager text'
        )""",
        
        # Take screenshot
        "mcp__puppeteer__puppeteer_screenshot(name='protocol_manager_page')",
        
        # Check we're on Protocol Manager page
        """mcp__puppeteer__puppeteer_evaluate(
            script='window.location.pathname'
        )""",
    ]
    
    return tests


if __name__ == "__main__":
    print("MCP UI Test Commands")
    print("====================")
    print("\nHomepage Tests:")
    for test in test_homepage():
        print(f"\n{test}")
    
    print("\n\nNavigation Tests:")
    for test in test_navigation():
        print(f"\n{test}")