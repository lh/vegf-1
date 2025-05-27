"""
Pytest fixtures for UI tests with automatic server management.
"""

import pytest
import subprocess
import time
import socket
import os
import signal
from pathlib import Path
from playwright.sync_api import sync_playwright


def is_port_open(port=8501, host='localhost'):
    """Check if a port is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False


@pytest.fixture(scope="session")
def streamlit_server():
    """
    Start Streamlit server for the test session and stop it afterwards.
    
    This fixture:
    1. Checks if server is already running
    2. Starts it if needed
    3. Waits for it to be ready
    4. Cleans up after tests
    """
    port = 8501
    server_process = None
    
    # Check if server is already running
    if is_port_open(port):
        print(f"✓ Streamlit server already running on port {port}")
        yield f"http://localhost:{port}"
        return
    
    # Start the server
    print(f"Starting Streamlit server on port {port}...")
    
    # Find the APE.py file
    app_path = Path(__file__).parent.parent.parent / "APE.py"
    if not app_path.exists():
        raise FileNotFoundError(f"APE.py not found at {app_path}")
    
    # Start streamlit with specific settings for testing
    env = os.environ.copy()
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'  # Run headless
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'  # Disable telemetry
    
    server_process = subprocess.Popen(
        [
            'streamlit', 'run', str(app_path),
            '--server.port', str(port),
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--logger.level', 'error',  # Reduce noise
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if os.name != 'nt' else None
    )
    
    # Wait for server to start
    max_wait = 30  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if is_port_open(port):
            print(f"✓ Streamlit server started successfully on port {port}")
            break
        time.sleep(0.5)
    else:
        # Timeout - kill process and fail
        if server_process:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        raise TimeoutError(f"Streamlit server failed to start within {max_wait} seconds")
    
    # Give it a bit more time to fully initialize
    time.sleep(2)
    
    yield f"http://localhost:{port}"
    
    # Cleanup
    if server_process:
        print("Stopping Streamlit server...")
        try:
            # Kill the process group to ensure all child processes are terminated
            if os.name != 'nt':
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            else:
                server_process.terminate()
            
            # Wait for graceful shutdown
            server_process.wait(timeout=5)
        except:
            # Force kill if graceful shutdown fails
            if os.name != 'nt':
                os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
            else:
                server_process.kill()
        
        print("✓ Streamlit server stopped")


@pytest.fixture(scope="session")
def browser():
    """Create browser instance for testing."""
    with sync_playwright() as p:
        # Use Chromium for consistency
        browser = p.chromium.launch(
            headless=True,  # Set to False to see the browser
            args=['--no-sandbox']  # Needed for some environments
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser, streamlit_server):
    """Create a page with the Streamlit server URL."""
    context = browser.new_context()
    page = context.new_page()
    
    # Set default timeout
    page.set_default_timeout(10000)  # 10 seconds
    
    yield page
    
    context.close()


# Configure pytest-playwright
def pytest_configure(config):
    """Configure pytest-playwright settings."""
    config.option.headed = False  # Run headless by default
    config.option.slowmo = 0  # No artificial delays
    config.option.screenshot = "only-on-failure"  # Take screenshots on failure